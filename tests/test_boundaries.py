"""Focused receiver data-flow and GPU-default checks; no model execution."""
import ast
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from imagecalgacus.runtime import ROOT, read_profile
from imagecalgacus.receiver import receive


class Boundaries(unittest.TestCase):
    def test_gpu_profile_rejects_cpu_and_sidecars(self):
        base = json.loads((ROOT / "configs/v0.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            for change in ["cpu", "partial", "payload_sidecar"]:
                profile = json.loads(json.dumps(base))
                if change == "payload_sidecar":
                    profile["source_digest"] = "not permitted"
                else:
                    profile["text"]["n_gpu_layers"] = 0 if change == "cpu" else 8
                path.write_text(json.dumps(profile))
                with self.assertRaises(ValueError):
                    read_profile(path)

    def test_receiver_rejects_extra_inputs_before_model_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ["carrier.txt", "profile.json", "prompt.txt", "run.key", "source_digest.txt"]:
                (folder / name).write_bytes(b"")
            args = SimpleNamespace(carrier=folder / "carrier.txt", profile=folder / "profile.json",
                                   context=folder / "prompt.txt", key=folder / "run.key",
                                   output=folder / "output", report=folder / "report",
                                   direction="image-to-text")
            with self.assertRaisesRegex(ValueError, "undeclared inputs"):
                receive(args)

    def test_receiver_does_not_import_reference_pipeline(self):
        tree = ast.parse((ROOT / "imagecalgacus/receiver.py").read_text())
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertTrue(imports.isdisjoint({"sender", "demo", "evaluate"}))
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("source_hash", calls)  # no reading fixture-bearing modules for hashing


if __name__ == "__main__":
    unittest.main()
