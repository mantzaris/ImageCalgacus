"""CPU-only final evidence namespace reconciliation; no private state needed."""
import contextlib
import io
import json
import runpy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
helpers=runpy.run_path(str(ROOT/"scripts/finalize_v1_qualification.py"))
validate=helpers["validate_record_identities"]
verify_public=helpers["verify_public"]


class FinalCompletionIdentity(unittest.TestCase):
    def test_unexpected_lossless_or_wrong_kind_cannot_hide_in_complete_report(self):
        allocation={"cases":[{"id":"c","work_id":"s"}],"traces":[{"id":"t","work_id":"t"}]}
        lossless=[{"id":"l","work_id":"l"}]
        valid={"s":{"work_id":"s","kind":"stego","case":"c"},
               "t":{"work_id":"t","kind":"trace","id":"t"},
               "l":{"work_id":"l","kind":"lossless","id":"l"}}
        validate(valid,allocation,lossless)
        with self.assertRaises(ValueError):
            validate(dict(valid,extra={"work_id":"extra","kind":"lossless","id":"extra"}),allocation,lossless)
        with self.assertRaises(ValueError):
            validate(dict(valid,l={"work_id":"l","kind":"trace","id":"l"}),allocation,lossless)
        with self.assertRaises(ValueError):
            validate(dict(valid,l={"work_id":"l","kind":"lossless","id":"wrong"}),allocation,lossless)

    def test_public_references_do_not_hide_partial_or_duplicate_coverage(self):
        cases=[{"id":"a","work_id":"wa"},{"id":"b","work_id":"wb"}]
        def observed(case,folder):
            return dict(case=case["id"],work_id=case["work_id"],attempted=True,terminal=True,
                evidence_valid=True,carrier_complete=True,exact_recovery=True,authenticated=True,
                source_equal=True,packet_complete=True)
        rows=[dict(observed(c,None),evidence_directory="unused") for c in cases]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); allocation=root/"allocation.json"
            allocation.write_text(json.dumps({"cases":cases}))
            results=root/"results.jsonl"
            def write(values):
                results.write_text("".join(json.dumps(r)+"\n" for r in values))
            with patch.dict(verify_public.__globals__,{"ALLOCATION":allocation,"evaluate_case":observed}),contextlib.redirect_stdout(io.StringIO()):
                write(rows[:1]);self.assertEqual(verify_public(root),2)
                write(rows);self.assertEqual(verify_public(root),0)
                write(rows+rows[:1]);self.assertEqual(verify_public(root),2)
                write([dict(rows[0],case="wrong"),rows[1]])
                with self.assertRaises(ValueError):verify_public(root)
                write([dict(rows[0],source_equal=False),rows[1]])
                with self.assertRaises(ValueError):verify_public(root)
