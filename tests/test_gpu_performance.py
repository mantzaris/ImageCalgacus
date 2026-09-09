"""Focused CPU guards for the optional GPU benchmark, not a model substitute."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from imagecalgacus import runtime
from imagecalgacus.image_backend import DistributionDigest, ImageBackend
from imagecalgacus.gpu_performance import select_payloads, compare_records


class GPUPerformance(unittest.TestCase):
    def test_absolute_separate_allowance_is_idempotent(self):
        original={s:runtime.phase_limit(s) for s in ("v0","v1","v2")}
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/"authorization.json"
            self.assertEqual(runtime.phase_limit("gpu_performance",path),0)
            self.assertTrue(runtime.apply_performance_allowance(path))
            before=path.read_bytes()
            self.assertFalse(runtime.apply_performance_allowance(path))
            self.assertEqual(before,path.read_bytes())
            self.assertEqual(runtime.phase_limit("gpu_performance",path),7200)
            self.assertEqual({s:runtime.phase_limit(s) for s in original},original)
            value=json.loads(before);value["absolute_seconds"]+=7200
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):runtime.apply_performance_allowance(path)
            with self.assertRaises(ValueError):runtime.phase_limit("gpu_performance",path)

    def test_performance_phase_and_whole_caps_prevent_launch(self):
        for costs in ((0,0,0,7200),(3163,39995,100842,0)):
            with self.subTest(costs=costs), tempfile.TemporaryDirectory() as name, patch.object(runtime,"ROOT",Path(name)):
                runtime.apply_performance_allowance()
                original={}
                for stage,cost in zip(("v0","v1","v2","gpu_performance"),costs):
                    folder=runtime.budget_root(stage);folder.mkdir(parents=True,exist_ok=True)
                    ledger=folder/"gpu_budget.jsonl"
                    ledger.write_text(json.dumps(dict(event="started",id=stage))+"\n"+
                                      json.dumps(dict(event="finished",id=stage,elapsed_seconds=cost))+"\n")
                    original[ledger]=ledger.read_bytes()
                with patch.object(runtime.subprocess,"Popen") as launch:
                    with self.assertRaises(RuntimeError):
                        runtime.run_budgeted(["unused"],"must-not-launch",stage="gpu_performance")
                    launch.assert_not_called()
                for path,data in original.items():self.assertEqual(path.read_bytes(),data)

    def test_exact_stream_digest_detects_one_ulp_membership_order_and_length(self):
        ids=np.array([1,7,9]);q=np.array([0.5,0.3,0.2]);order=ids.copy()
        def digest(a,b,c,twice=False):
            h=DistributionDigest();h.observe(a,b,c)
            if twice:h.observe(a,b,c)
            return h.summary()
        original=digest(ids,q,order)
        self.assertEqual(original,digest(ids.copy(),q.copy(),order.copy()))
        changed=q.copy();changed[0]=np.nextafter(changed[0],1.0)
        self.assertNotEqual(original,digest(ids,changed,order))
        self.assertNotEqual(original,digest(ids+1,q,order))
        self.assertNotEqual(original,digest(ids,q,order[::-1]))
        self.assertNotEqual(original,digest(ids,q,order,True))

    def test_case_selection_ignores_outcomes_and_heldout(self):
        items=[dict(id="T"+str(i),bytes=b,split="development",direction="text-to-image",outcome=False)
               for i,b in [(5,128),(4,96),(1,32),(2,48),(3,64)]]
        items.append(dict(id="T0",bytes=32,split="heldout",direction="text-to-image",outcome=True))
        self.assertEqual([x["id"] for x in select_payloads({"payloads":items})],["T1","T4","T5"])

    def test_mode_is_explicit_and_invalid_mode_never_loads_model(self):
        with self.assertRaisesRegex(ValueError,"no fallback"):
            ImageBackend({},execution_mode="cpu")

    def test_comparison_rejects_even_one_probability_stream_difference(self):
        row=dict(evaluation=dict(carrier_sha256="carrier",recovered_sha256="source",exact_recovery=True),
                 distribution_digest={"steps":2976,"probabilities_sha256":"exact"},charged_pair_seconds=20.)
        records={"reference":copy.deepcopy(row),"cuda_graph":copy.deepcopy(row)}
        self.assertTrue(compare_records(records)["equivalent"])
        records["cuda_graph"]["distribution_digest"]["probabilities_sha256"]="different"
        self.assertFalse(compare_records(records)["equivalent"])


if __name__=="__main__":unittest.main()
