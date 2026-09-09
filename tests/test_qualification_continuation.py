"""CPU-only continuation, binding, budget and terminal-record regression checks."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from imagecalgacus import runtime
from imagecalgacus.qualification import (
    read_json, ALLOCATION, prior_cases, pending_work, verify_binding, sender_state,
    classify, terminal, completed_records, recover_terminal_events, validate_receiver_inbox)
from imagecalgacus.packet import NewRun
from imagecalgacus.sender import read_source


class QualificationContinuation(unittest.TestCase):
    def test_idempotent_v1_extension_preserves_v0(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/"authorization.json"
            self.assertEqual(runtime.phase_limit("v1",p),7200)
            self.assertTrue(runtime.apply_v1_allowance(p))
            before=p.read_bytes()
            self.assertFalse(runtime.apply_v1_allowance(p))
            self.assertEqual(p.read_bytes(),before)
            self.assertEqual(runtime.phase_limit("v1",p),50400)
            self.assertEqual(runtime.phase_limit("v0",p),7200)
            changed=json.loads(before);changed["absolute_seconds"]+=43200
            p.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):runtime.apply_v1_allowance(p)
            with self.assertRaises(ValueError):runtime.phase_limit("v1",p)

    def test_atomic_json_is_complete_and_exclusive(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/"terminal.json"
            runtime.atomic_json(p,{"unicode":"é","items":[1,2]})
            self.assertEqual(read_json(p),{"unicode":"é","items":[1,2]})
            with self.assertRaises(FileExistsError):runtime.atomic_json(p,{"different":1})
            self.assertEqual(read_json(p)["unicode"],"é")

    def test_skip_historical_credits_and_no_duplicate_terminal_credit(self):
        allocation=read_json(ALLOCATION); historical=prior_cases(allocation)
        self.assertEqual(len(historical),18)
        pending=pending_work(allocation,historical)
        self.assertEqual(len(pending),134)
        self.assertFalse(set(historical)&{c["work_id"] for c in pending})
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); record={"work_id":pending[0]["work_id"],"kind":"stego","case":pending[0]["id"]}
            self.assertTrue(terminal(root,record));self.assertFalse(terminal(root,record))
            current=completed_records(root,historical)
            self.assertEqual(len(current),19); self.assertEqual(len(pending_work(allocation,current)),133)
            self.assertEqual(len((root/"qualification_events.jsonl").read_text().splitlines()),1)
            with self.assertRaises(ValueError):
                terminal(root,dict(record,case="different"))
            with self.assertRaises(ValueError):
                completed_records(root,{record["work_id"]:record})

    def test_crash_after_atomic_terminal_before_event_is_recoverable(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); record={"work_id":"unique","kind":"stego","case":"case"}
            runtime.atomic_json(root/"terminals/unique.json",record)
            recover_terminal_events(root);recover_terminal_events(root)
            events=(root/"qualification_events.jsonl").read_text().splitlines()
            self.assertEqual(len(events),1)
            self.assertEqual(json.loads(events[0])["work_id"],"unique")
            self.assertIn("unique",completed_records(root,{}))

    def test_original_pair_packet_not_new_encryption(self):
        allocation=read_json(ALLOCATION)
        baseline=read_json(runtime.ROOT/".runtime/v1_qualification/baseline.json")
        for c in allocation["cases"]:
            if c["pair_id"] in baseline["legacy_packet_bindings"]:
                b=baseline["legacy_packet_bindings"][c["pair_id"]]
                p,k=verify_binding(b,c)
                self.assertEqual(runtime.sha256_file(p),b["packet_sha256"])
                self.assertEqual(len(k.read_bytes()),32)
        c=next(c for c in allocation["cases"] if c["pair_id"]=="I5-prompt1")
        b=baseline["legacy_packet_bindings"][c["pair_id"]]
        self.assertIn("v1-packets-002",str(verify_binding(b,c)[0]))
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            with self.assertRaises(ValueError):
                verify_binding(dict(b,packet=str(root/"missing.packet")),c)
            with self.assertRaises(ValueError):
                verify_binding(dict(b,packet_sha256="0"*64),c)
            with self.assertRaises(ValueError):
                verify_binding(dict(b,context_sha256="0"*64),c)
            fresh=NewRun(root/"new")
            replacement=fresh.encrypt(read_source(runtime.ROOT/c["source"],c["direction"]))
            (root/"replacement.packet").write_bytes(replacement)
            with self.assertRaises(ValueError):
                verify_binding(dict(b,packet=str(root/"replacement.packet")),c)
            with self.assertRaises(Exception):
                verify_binding(dict(b,key=str(root/"new/run.key")),c)

    def test_receiver_only_resume_and_reject_changed_inbox(self):
        allocation=read_json(ALLOCATION);historical=prior_cases(allocation)
        c=next(c for c in allocation["cases"] if c["id"]=="I1-fixed")
        old=Path(historical[c["work_id"]]["case_dir"])
        binding=read_json(runtime.ROOT/".runtime/v1_qualification/baseline.json")["legacy_packet_bindings"][c["pair_id"]]
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); target=root/"case"
            self.assertEqual(sender_state(target,c,binding),"unstarted")
            target.mkdir(); self.assertEqual(sender_state(target,c,binding),"interrupted_sender")
            shutil.copytree(old/"inbox",target/"inbox")
            shutil.copyfile(old/"sender.json",target/"sender.json")
            self.assertEqual(sender_state(target,c,binding),"receiver_pending")
            # Only the saved carrier/profile/context/key are needed for this state.
            self.assertFalse((target/"source.png").exists())
            shutil.copyfile(old/"receiver.json",target/"receiver.json")
            self.assertEqual(sender_state(target,c,binding),"evaluate_pending")
            (target/"inbox/extra.json").write_text("{}")
            with self.assertRaises(ValueError):sender_state(target,c,binding)

    def test_capacity_static_and_infrastructure_are_distinct(self):
        base=dict(evidence_valid=True,exact_recovery=False,carrier_complete=False,coder_progress_matches=True)
        s=dict(failure_stage="capacity",diagnostics={"x":1},coder_diagnostics={"bits":100})
        r=copy.deepcopy(s)
        self.assertEqual(classify({"method":"arithmetic"},base,s,r,True),"verified_capacity_failure")
        self.assertEqual(classify({"method":"gated"},base,s,r,False),"unexpected_experimental_or_infrastructure_failure")
        self.assertEqual(classify({"method":"fixed"},base,s,r,True),"unexpected_experimental_or_infrastructure_failure")
        static=dict(base,outcome_class="static_tokenization_drift_failure")
        self.assertEqual(classify({"method":"fixed"},static,s,r,False),"static_tokenization_drift_failure")
        self.assertEqual(classify({"method":"arithmetic"},dict(base,evidence_valid=False),s,r,True),"infrastructure_or_identity_error")
        success=dict(base,exact_recovery=True,carrier_complete=True)
        self.assertEqual(classify({"method":"fixed"},success,{}, {},True),"exact_recovery")
        self.assertNotEqual(classify({"method":"fixed"},success,{}, {},False),"exact_recovery")

    def test_interrupted_budget_is_charged_once_and_live_child_blocks(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); folder=root/".runtime/v1";folder.mkdir(parents=True)
            ledger=folder/"gpu_budget.jsonl"
            start={"event":"started","id":"test-interrupted","utc":(datetime.now(timezone.utc)-timedelta(seconds=10)).isoformat()}
            ledger.write_text(json.dumps(start)+"\n")
            with patch.object(runtime,"ROOT",root):
                log=folder/"logs/test-interrupted/process.json"
                runtime.atomic_json(log,{"pid":os.getpid(),"start_ticks":Path("/proc/self/stat").read_text().split()[21]})
                with self.assertRaises(RuntimeError):runtime.reconcile_interrupted("v1")
                log.unlink()
                result=runtime.reconcile_interrupted("v1")
                self.assertEqual(len(result),1);self.assertGreaterEqual(result[0]["elapsed_seconds"],10)
                self.assertEqual(runtime.reconcile_interrupted("v1"),[])
                used,events=runtime.budget_state("v1")
                self.assertEqual(len(events),2);self.assertGreaterEqual(used,10)

if __name__=="__main__":unittest.main()
