"""Focused non-model checks for the new saved-PNG observer and paired analysis."""
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from imagecalgacus import runtime
from imagecalgacus.coders import Trace
from imagecalgacus.image_backend import read_png,write_png
from imagecalgacus.png_observer import score_pixels
from imagecalgacus.png_context_detection import build_manifest
sys.path.insert(0,str(runtime.ROOT/"scripts"))
from analyze_png_context_detection import paired_auc
from analyze_v2 import group_draws


class SyntheticBackend:
    def start(self,context):
        self.context=context;self.observed=[]
    def distribution(self):
        return np.array([0,1]),np.array([.75,.25]),np.array([0,1])
    def observe(self,value):
        self.observed.append(value)


class PNGObserverTests(unittest.TestCase):
    def test_saved_pixels_complete_accounting_and_literal_context(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"carrier.png"
            pixels=np.zeros((31,32,3),dtype=np.uint8)
            pixels.reshape(-1)[::2]=1
            write_png(path,pixels)
            model=SyntheticBackend();trace=Trace();context=bytes(range(96))
            scores=score_pixels(model,read_png(path),context,trace)
            self.assertEqual(model.context,context)
            self.assertEqual(model.observed,pixels.reshape(-1).tolist())
            self.assertEqual(scores["positions"],2976)
            self.assertAlmostEqual(scores["surprisal_bits_mean"],(2-math.log2(.75))/2,places=12)
            self.assertEqual(scores["log_rank_mean"],.5)
            with self.assertRaises(ValueError):score_pixels(model,pixels,context[:-1],Trace())

    def test_zero_support_is_failure_not_clipping(self):
        pixels=np.zeros((31,32,3),dtype=np.uint8);pixels[0,0,0]=2
        with self.assertRaisesRegex(ValueError,"outside eligible"):
            score_pixels(SyntheticBackend(),pixels,bytes(96),Trace())

    def test_manifest_full_unique_control_links_and_frozen_rows(self):
        manifest=build_manifest();items=manifest["artifacts"]
        self.assertEqual(len(items),80)
        self.assertEqual(sum(i["kind"]=="control" for i in items),20)
        self.assertEqual(len({i["carrier_sha256"] for i in items}),80)
        self.assertNotEqual(manifest["contexts"]["row1"]["sha256"],manifest["contexts"]["row2"]["sha256"])
        for group in manifest["groups"]:
            members=[i for i in items if i["payload_group"]==group["id"]]
            self.assertEqual(len(members),4)
            self.assertEqual(len({i["control_id"] for i in members}),1)

    def test_stage_absolute_idempotent_and_old_caps_preserved(self):
        original={s:runtime.phase_limit(s) for s in ("v0","v1","v2","gpu_performance")}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"authorization.json"
            self.assertEqual(runtime.phase_limit("png_context_detection",path),0)
            self.assertTrue(runtime.apply_png_context_allowance(path))
            before=path.read_bytes()
            self.assertFalse(runtime.apply_png_context_allowance(path))
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(runtime.phase_limit("png_context_detection",path),7200)
            self.assertEqual({s:runtime.phase_limit(s) for s in original},original)
            value=json.loads(before);value["absolute_seconds"]+=1;path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):runtime.phase_limit("png_context_detection",path)

    def test_whole_project_cap_includes_new_stage(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(runtime,"ROOT",Path(directory)):
            runtime.apply_png_context_allowance()
            folder=runtime.budget_root("v0");folder.mkdir(parents=True,exist_ok=True)
            (folder/"gpu_budget.jsonl").write_text(json.dumps(dict(event="started",id="old"))+"\n"+
                json.dumps(dict(event="finished",id="old",elapsed_seconds=144000))+"\n")
            with patch.object(runtime.subprocess,"Popen") as launch:
                with self.assertRaises(RuntimeError):
                    runtime.run_budgeted(["not-run"],"cap",stage="png_context_detection",max_seconds=60)
                launch.assert_not_called()

    def test_paired_context_draws_retain_zero_difference_and_orientation(self):
        draws=group_draws([{"stratum":"a"}]*4,2000,2026090902)
        result=paired_auc([0,1,2,3],[4,5,6,7],[0,1,2,3],[4,5,6,7],draws)
        self.assertEqual(result["correct_auc_paired"],0)
        self.assertEqual(result["mismatch_auc"],0)
        self.assertEqual(result["difference_95_interval"],[0,0])
        self.assertEqual(result["valid_bootstrap_replicates"],[2000]*3)


if __name__=="__main__":unittest.main()
