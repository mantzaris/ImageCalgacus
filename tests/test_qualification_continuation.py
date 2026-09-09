"""Portable CPU continuation tests; private history checks are explicitly opt-in."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from cryptography.exceptions import InvalidTag
from PIL import Image
from imagecalgacus import runtime, qualification
from imagecalgacus.qualification import (
    read_json, ALLOCATION, prior_cases, pending_work, verify_binding, sender_state,
    classify, terminal, completed_records, recover_terminal_events, validate_receiver_inbox)
from imagecalgacus.packet import NewRun
from imagecalgacus.sender import read_source


def synthetic_binding(root):
    """Real authenticated packet and source; no model or historical run dependency."""
    Image.frombytes("L",(16,16),bytes(range(256))).save(root/"source.png")
    (root/"prompt.txt").write_bytes(b"A synthetic shared context.")
    profile=read_json(runtime.ROOT/"configs/v1_fixed.json")
    for modality in ("text","image"):
        profile[modality]["interpreter"]=sys.executable
        profile[modality]["model_path"]=str(root/(modality+".unused-model"))
    runtime.atomic_json(root/"profile.json",profile)
    payload=read_source(root/"source.png","image-to-text")
    run=NewRun(root/"packet")
    packet=root/"packet/sealed.packet";packet.write_bytes(run.encrypt(payload))
    source_hash=__import__("hashlib").sha256(payload.data).hexdigest()
    case=dict(id="synthetic-fixed",work_id="synthetic-work",pair_id="synthetic-prompt",
        direction="image-to-text",method="fixed",text_filter_arm="sequence",
        source=str(root/"source.png"),source_sha256=source_hash,
        profile_id=runtime.canonical_hash(profile),context_sha256=runtime.sha256_file(root/"prompt.txt"))
    binding=dict(packet=str(packet),key=str(root/"packet/run.key"),packet_sha256=runtime.sha256_file(packet),
                 source_sha256=source_hash,context_sha256=case["context_sha256"])
    return case,binding


def synthetic_sender(root,case,binding):
    target=root/"case"; inbox=target/"inbox";inbox.mkdir(parents=True)
    (inbox/"carrier.txt").write_bytes(b"literal saved carrier")
    for source,name in ((root/"profile.json","profile.json"),(root/"prompt.txt","prompt.txt"),
                        (Path(binding["key"]),"run.key")):
        shutil.copyfile(source,inbox/name)
    runtime.atomic_json(target/"sender.json",dict(profile_id=case["profile_id"],
        prepared_packet_sha256=binding["packet_sha256"],carrier_sha256=runtime.sha256_file(inbox/"carrier.txt")))
    return target


def interrupted_ledger(root,ident="test-interrupted"):
    folder=root/".runtime/v1";folder.mkdir(parents=True)
    ledger=folder/"gpu_budget.jsonl"
    start=dict(event="started",id=ident,utc=(datetime.now(timezone.utc)-timedelta(seconds=10)).isoformat())
    ledger.write_text(json.dumps(start)+"\n")
    return folder,ledger


def fake_proc_entry(proc,pid,ticks,marker=b""):
    process=proc/str(pid);process.mkdir(parents=True,exist_ok=True)
    # Linux stat fields: pid, comm, state, fields4..21, starttime(field22).
    (process/"stat").write_text(str(pid)+" (python) S "+" ".join(["0"]*18)+" "+str(ticks)+" 0\n")
    (process/"environ").write_bytes(marker)


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

    def test_skip_credits_and_no_duplicate_terminal_credit(self):
        allocation={"cases":[dict(id="case-"+str(i),work_id="work-"+str(i)) for i in range(3)]}
        prior={"work-0":dict(work_id="work-0",kind="stego",case="case-0",historical=True)}
        pending=pending_work(allocation,prior)
        self.assertEqual([c["work_id"] for c in pending],["work-1","work-2"])
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);record=dict(work_id=pending[0]["work_id"],kind="stego",case=pending[0]["id"])
            self.assertTrue(terminal(root,record));self.assertFalse(terminal(root,record))
            current=completed_records(root,prior)
            self.assertEqual(len(current),2)
            self.assertEqual([c["work_id"] for c in pending_work(allocation,current)],["work-2"])
            self.assertEqual(len((root/"qualification_events.jsonl").read_text().splitlines()),1)
            with self.assertRaises(ValueError):terminal(root,dict(record,case="different"))
            with self.assertRaises(ValueError):completed_records(root,{record["work_id"]:record})

    def test_crash_after_atomic_terminal_before_event_is_recoverable(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);record={"work_id":"unique","kind":"stego","case":"case"}
            runtime.atomic_json(root/"terminals/unique.json",record)
            recover_terminal_events(root);recover_terminal_events(root)
            events=(root/"qualification_events.jsonl").read_text().splitlines()
            self.assertEqual(len(events),1)
            self.assertEqual(json.loads(events[0])["work_id"],"unique")
            self.assertIn("unique",completed_records(root,{}))

    def test_original_pair_packet_not_new_encryption(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);c,b=synthetic_binding(root)
            p,k=verify_binding(b,c)
            self.assertEqual(p.read_bytes(),Path(b["packet"]).read_bytes())
            for changed in (dict(b,packet=str(root/"missing.packet")),dict(b,packet_sha256="0"*64),
                            dict(b,context_sha256="0"*64),dict(b,source_sha256="0"*64)):
                with self.assertRaises(ValueError):verify_binding(changed,c)
            fresh=NewRun(root/"new")
            replacement=root/"replacement.packet"
            replacement.write_bytes(fresh.encrypt(read_source(root/"source.png",c["direction"])))
            with self.assertRaises(ValueError):verify_binding(dict(b,packet=str(replacement)),c)
            with self.assertRaises(InvalidTag):verify_binding(dict(b,key=str(root/"new/run.key")),c)
            Image.frombytes("L",(16,16),bytes(reversed(range(256)))).save(root/"source.png")
            with self.assertRaises(ValueError):verify_binding(b,c)

    def test_receiver_only_resume_and_reject_changed_inbox(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);c,b=synthetic_binding(root);target=root/"case"
            self.assertEqual(sender_state(target,c,b),"unstarted")
            target.mkdir();self.assertEqual(sender_state(target,c,b),"interrupted_sender")
            target.rmdir();target=synthetic_sender(root,c,b)
            self.assertEqual(sender_state(target,c,b),"receiver_pending")
            self.assertFalse((target/"source.png").exists())
            runtime.atomic_json(target/"receiver.json",{"synthetic_report":True})
            self.assertEqual(sender_state(target,c,b),"evaluate_pending")
            (target/"inbox/extra.json").write_text("{}")
            with self.assertRaises(ValueError):sender_state(target,c,b)
            (target/"inbox/extra.json").unlink()
            (target/"inbox/prompt.txt").write_bytes(b"wrong context")
            with self.assertRaises(ValueError):sender_state(target,c,b)
            shutil.copyfile(root/"prompt.txt",target/"inbox/prompt.txt")
            (target/"inbox/run.key").write_bytes(b"x"*32)
            with self.assertRaises(ValueError):sender_state(target,c,b)
            shutil.copyfile(b["key"],target/"inbox/run.key")
            (target/"inbox/carrier.txt").write_bytes(b"changed carrier")
            self.assertEqual(sender_state(target,c,b),"invalid_or_interrupted_sender")

    def test_capacity_static_and_infrastructure_are_distinct(self):
        base=dict(evidence_valid=True,exact_recovery=False,carrier_complete=False,coder_progress_matches=True)
        s=dict(failure_stage="capacity",diagnostics={"x":1},coder_diagnostics={"bits":100});r=copy.deepcopy(s)
        self.assertEqual(classify({"method":"arithmetic"},base,s,r,True),"verified_capacity_failure")
        self.assertEqual(classify({"method":"gated"},base,s,r,False),"unexpected_experimental_or_infrastructure_failure")
        self.assertEqual(classify({"method":"fixed"},base,s,r,True),"unexpected_experimental_or_infrastructure_failure")
        static=dict(base,outcome_class="static_tokenization_drift_failure")
        self.assertEqual(classify({"method":"fixed"},static,s,r,False),"static_tokenization_drift_failure")
        self.assertEqual(classify({"method":"arithmetic"},dict(base,evidence_valid=False),s,r,True),"infrastructure_or_identity_error")
        success=dict(base,exact_recovery=True,carrier_complete=True)
        self.assertEqual(classify({"method":"fixed"},success,{}, {},True),"exact_recovery")
        self.assertNotEqual(classify({"method":"fixed"},success,{}, {},False),"exact_recovery")

    def test_controlled_process_identities_and_conservative_accounting(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);folder,ledger=interrupted_ledger(root);proc=root/"proc";proc.mkdir()
            fake_proc_entry(proc,77,"101")
            sidecar=folder/"logs/test-interrupted/process.json"
            runtime.atomic_json(sidecar,{"pid":77,"start_ticks":"101"})
            real_path=Path
            def mapped_path(value):
                return proc if str(value)=="/proc" else real_path(value)
            with patch.object(runtime,"ROOT",root),patch.object(runtime,"Path",side_effect=mapped_path):
                with self.assertRaisesRegex(RuntimeError,"recorded child still alive"):
                    runtime.reconcile_interrupted("v1")
                # Reused PID (different start time) is not the original child.
                fake_proc_entry(proc,77,"202",b"IMAGECALGACUS_BUDGETED=test-interrupted\0")
                with self.assertRaisesRegex(RuntimeError,"model process still alive"):
                    runtime.reconcile_interrupted("v1")
                fake_proc_entry(proc,77,"202")
                result=runtime.reconcile_interrupted("v1")
                self.assertEqual(len(result),1);self.assertGreaterEqual(result[0]["elapsed_seconds"],10)
                self.assertEqual(runtime.reconcile_interrupted("v1"),[])
                used,events=runtime.budget_state("v1")
                self.assertEqual(len(events),2);self.assertGreaterEqual(used,10)


class ProcessPlatformIntegration(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux") and Path("/proc/self/stat").exists(),
                         "platform integration requires a coherent Linux /proc")
    def test_model_free_child_identity_and_marker_block_reconciliation(self):
        ident="model-free-portability-check"
        env=dict(os.environ,IMAGECALGACUS_BUDGETED=ident)
        child=subprocess.Popen([sys.executable,"-u","-c","import os,time; print(os.getpid()); time.sleep(30)"],
                               stdout=subprocess.PIPE,text=True,env=env)
        try:
            reported=int(child.stdout.readline())
            try:
                stat=Path("/proc/%d/stat"%child.pid).read_text().split()
                environment=Path("/proc/%d/environ"%child.pid).read_bytes()
                self_stat=Path("/proc/self/stat").read_text().split()
            except (FileNotFoundError,PermissionError) as exc:
                self.skipTest("platform integration cannot inspect child /proc: "+type(exc).__name__)
            if reported!=child.pid or int(stat[0])!=child.pid or int(self_stat[0])!=os.getpid():
                self.skipTest("platform integration: Python and /proc process IDs are incoherent")
            if ("IMAGECALGACUS_BUDGETED="+ident).encode() not in environment.split(b"\0"):
                self.skipTest("platform integration cannot observe the child's budget marker")
            with tempfile.TemporaryDirectory() as name:
                root=Path(name);folder,_=interrupted_ledger(root,ident)
                sidecar=folder/"logs"/ident/"process.json"
                runtime.atomic_json(sidecar,dict(pid=child.pid,start_ticks=stat[21]))
                with patch.object(runtime,"ROOT",root):
                    with self.assertRaisesRegex(RuntimeError,"recorded child still alive"):
                        runtime.reconcile_interrupted("v1")
                    runtime.atomic_json(sidecar,dict(pid=child.pid,start_ticks="mismatch"),replace=True)
                    with self.assertRaisesRegex(RuntimeError,"model process still alive"):
                        runtime.reconcile_interrupted("v1")
                    child.terminate();child.wait(timeout=5)
                    self.assertEqual(len(runtime.reconcile_interrupted("v1")),1)
                    self.assertEqual(runtime.reconcile_interrupted("v1"),[])
        finally:
            if child.poll() is None:child.terminate();child.wait(timeout=5)
            child.stdout.close()


@unittest.skipUnless(os.environ.get("IMAGECALGACUS_PRIVATE_TESTS")=="1",
                     "private integration: set IMAGECALGACUS_PRIVATE_TESTS=1 with original V1 run files/keys")
class HistoricalPrivateIntegration(unittest.TestCase):
    def test_original_credits_and_all_packet_bindings(self):
        baseline=runtime.ROOT/".runtime/v1_qualification/baseline.json"
        self.assertTrue(baseline.is_file(),"private integration requires original baseline and retained runs")
        allocation=read_json(ALLOCATION);history=prior_cases(allocation)
        self.assertEqual(len(history),18)
        self.assertEqual(len(pending_work(allocation,history)),134)
        bindings=read_json(baseline)["legacy_packet_bindings"]
        for c in allocation["cases"]:
            if c["pair_id"] in bindings:verify_binding(bindings[c["pair_id"]],c)
        c=next(c for c in allocation["cases"] if c["pair_id"]=="I5-prompt1")
        self.assertIn("v1-packets-002",str(verify_binding(bindings[c["pair_id"]],c)[0]))


if __name__=="__main__":unittest.main()
