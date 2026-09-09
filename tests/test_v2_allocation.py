"""Focused CPU-only prospective allocation/accounting/continuation checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from imagecalgacus import runtime,v2
from imagecalgacus.qualification import verify_binding,sender_state,terminal,completed_records
from test_qualification_continuation import synthetic_binding,synthetic_sender


class ProspectiveAllocation(unittest.TestCase):
    def test_frozen_sources_methods_contexts_and_control_ids(self):
        manifest=v2.build_manifest();v2.validate_manifest(manifest)
        self.assertEqual([g["id"] for g in manifest["groups"][:4]],
                         ["HI1-prompt1","HT1-row1","HI2-prompt1","HT2-row1"])
        self.assertEqual({c["context_id"] for c in manifest["cases"]},{"prompt1","row1"})
        self.assertEqual({c["split"] for c in manifest["cases"]},{"heldout"})
        self.assertEqual(len({t["seed"] for t in manifest["controls"]}),40)
        self.assertEqual({c["sampling_seed"] for c in manifest["cases"]},{3001})
        changed=copy.deepcopy(manifest);changed["cases"][1]["work_id"]=changed["cases"][0]["work_id"]
        with self.assertRaises(ValueError):v2.validate_manifest(changed)
        changed=copy.deepcopy(manifest);changed["cases"][1]["context_sha256"]="0"*64
        with self.assertRaises(ValueError):v2.validate_manifest(changed)
        changed=copy.deepcopy(manifest);changed["cases"][0]["text_filter_arm"]="static"
        with self.assertRaises(ValueError):v2.validate_manifest(changed)

    def test_pending_methods_reuse_original_packet_and_valid_carrier(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);case,binding=synthetic_binding(root)
            group=dict(work_ids=["fixed","gated","arithmetic"],control_work_id="control")
            terminal(root,dict(work_id="fixed",kind="stego",case="fixed"))
            records=completed_records(root,{})
            self.assertEqual(v2.pending_group(group,records),["gated","arithmetic","control"])
            original=Path(binding["packet"]).read_bytes()
            for method in ("gated","arithmetic"):
                self.assertEqual(verify_binding(binding,dict(case,method=method))[0].read_bytes(),original)
            folder=synthetic_sender(root,case,binding)
            self.assertEqual(sender_state(folder,case,binding),"receiver_pending")
            # Work accounting alone cannot cause another encryption or sender.
            self.assertEqual(Path(binding["packet"]).read_bytes(),original)
            self.assertFalse(terminal(root,records["fixed"]))
            self.assertEqual(v2.pending_group(group,completed_records(root,{})),["gated","arithmetic","control"])

    def test_control_matches_longest_failed_or_completed_carrier(self):
        group=dict(work_ids=["fixed","gated","arithmetic"])
        records={w:{"evaluation":dict(terminal=True,evidence_valid=True,artifact_saved=True,delivered_tokens=n)}
                 for w,n in zip(group["work_ids"],[616,730,2048])}
        item=dict(modality="text",symbols=2048,work_id="same")
        self.assertEqual(v2.realized_control(item,group,records)["symbols"],2048)
        records["arithmetic"]["evaluation"]["delivered_tokens"]=1200
        actual=v2.realized_control(item,group,records)
        self.assertEqual(actual["symbols"],1200);self.assertEqual(actual["work_id"],"same")
        records["gated"]["evaluation"]["terminal"]=False
        with self.assertRaises(ValueError):v2.realized_control(item,group,records)

    def test_v2_absolute_authorization_once_and_no_transfer(self):
        with tempfile.TemporaryDirectory() as name,patch.object(runtime,"ROOT",Path(name)):
            self.assertEqual(runtime.phase_limit("v2"),0)
            self.assertTrue(runtime.apply_v2_allowance())
            p=Path(name)/"configs/v2_gpu_authorization.json";before=p.read_bytes()
            self.assertFalse(runtime.apply_v2_allowance());self.assertEqual(p.read_bytes(),before)
            self.assertEqual(runtime.phase_limit("v2"),54000)
            self.assertEqual(runtime.phase_limit("v0"),7200)
            self.assertEqual(runtime.phase_limit("v1"),7200)
            runtime.apply_v1_allowance()
            self.assertEqual(runtime.phase_limit("v1"),50400)
            self.assertEqual(runtime.phase_limit("v2"),54000)
            bad=json.loads(before);bad["absolute_seconds"]*=2;p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):runtime.apply_v2_allowance()
            with self.assertRaises(ValueError):runtime.phase_limit("v2")

    def test_phase_and_whole_caps_block_launch_and_preserve_ledgers(self):
        for costs in ((1000,2000,54000),(80000,64000,0)):
            with self.subTest(costs=costs),tempfile.TemporaryDirectory() as name,patch.object(runtime,"ROOT",Path(name)):
                runtime.apply_v2_allowance();before={}
                for stage,cost in zip(("v0","v1","v2"),costs):
                    folder=runtime.budget_root(stage);folder.mkdir(parents=True,exist_ok=True)
                    ledger=folder/"gpu_budget.jsonl"
                    ledger.write_text(json.dumps(dict(event="started",id=stage))+"\n"+
                                      json.dumps(dict(event="finished",id=stage,elapsed_seconds=cost))+"\n")
                    before[ledger]=ledger.read_bytes()
                with patch.object(runtime.subprocess,"Popen") as launch:
                    with self.assertRaises(RuntimeError):runtime.run_budgeted(["unused"],"blocked",stage="v2")
                    launch.assert_not_called()
                for path,raw in before.items():self.assertEqual(path.read_bytes(),raw)


if __name__=="__main__":unittest.main()
