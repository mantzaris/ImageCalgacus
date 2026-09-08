"""Final coverage is not subset success; all checks here are CPU only."""
import unittest
from pathlib import Path
import tempfile
import shutil
from imagecalgacus.runtime import ROOT
from imagecalgacus.evaluate import evaluate_run
from imagecalgacus.evaluate import validate_allocation


def passing(name):
    return dict(case=name, attempted=True, terminal=True, evidence_valid=True,
                carrier_complete=True, exact_recovery=True)


class Allocation(unittest.TestCase):
    def setUp(self):
        self.cases = [{"id": str(i)} for i in range(10)]

    def test_partial_run(self):
        result = validate_allocation(self.cases, [passing("0")])
        self.assertFalse(result["allocation_complete"])
        self.assertFalse(result["all_recovered"])
        self.assertEqual(result["attempted_count"], 1)
        self.assertEqual(len(result["missing_identifiers"]), 9)

    def test_real_partial_directory_is_not_final_success(self):
        import json
        cases=json.loads((ROOT/"configs/v0_cases.json").read_text())["cases"]
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT/"artifacts/v0_review/ten-001/I1",Path(tmp)/"I1")
            rows,result=evaluate_run(tmp,cases,mode="final")
            self.assertFalse(result["allocation_complete"])
            self.assertEqual(result["attempted_count"],1)
            self.assertEqual(result["exact_recovery_count"],1)
            self.assertFalse((Path(tmp)/"results.jsonl").exists())

    def test_one_expected_case_missing(self):
        result = validate_allocation(self.cases, [passing(str(i)) for i in range(9)])
        self.assertEqual(result["missing_identifiers"], ["9"])
        self.assertFalse(result["allocation_complete"])

    def test_duplicate_and_unexpected_identifiers(self):
        rows = [passing(str(i)) for i in range(10)]
        for bad in (rows + [passing("0")], rows + [passing("X")]):
            self.assertFalse(validate_allocation(self.cases, bad)["allocation_complete"])
        self.assertFalse(validate_allocation(self.cases + [{"id":"0"}], rows)["allocation_complete"])

    def test_duplicate_case_names_with_different_work_ids(self):
        cases=[{"id":"same","work_id":"a"},{"id":"same","work_id":"b"}]
        rows=[dict(passing("same"),work_id=k) for k in ("a","b")]
        result=validate_allocation(cases,rows)
        self.assertFalse(result["allocation_complete"])
        self.assertEqual(result["duplicate_expected_case_identifiers"],["same"])

    def test_case_and_work_identifier_mapping_must_match(self):
        cases=[{"id":"right","work_id":"valid-work"}]
        rows=[dict(passing("wrong"),work_id="valid-work")]
        result=validate_allocation(cases,rows)
        self.assertFalse(result["allocation_complete"])
        self.assertEqual(result["case_work_mismatches"],["valid-work"])

    def test_terminal_receiver_backend_failure_is_complete_failed_allocation(self):
        import json
        cases=json.loads((ROOT/"configs/v0_cases.json").read_text())["cases"][:1]
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/cases[0]["id"]
            shutil.copytree(ROOT/"artifacts/v0_review/ten-001/I1",target)
            report=json.loads((target/"receiver.json").read_text())
            report.update(authenticated=False,carrier_complete=False,packet_complete=False,
                          failure_stage="backend",failure_reason="synthetic unavailable backend",
                          packet_stop=None,packet_bits_recovered=0,packet_positions=0)
            report.pop("gpu_evidence",None)
            (target/"receiver.json").write_text(json.dumps(report))
            (target/"recovered.gray").unlink()
            rows,result=evaluate_run(tmp,cases)
            self.assertTrue(result["allocation_complete"])
            self.assertFalse(result["all_recovered"])
            self.assertEqual(result["recorded_failure_count"],1)

    def test_actual_profile_change_invalidates_success_evidence(self):
        import json
        cases=json.loads((ROOT/"configs/v0_cases.json").read_text())["cases"][:1]
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/cases[0]["id"]
            shutil.copytree(ROOT/"artifacts/v0_review/ten-001/I1",target)
            profile=json.loads((ROOT/"configs/v0.json").read_text())
            profile["text"]["model_sha256"]="changed"
            (target/"profile.json").write_text(json.dumps(profile))
            _,result=evaluate_run(tmp,cases)
            self.assertFalse(result["allocation_complete"])

    def test_complete_allocation_can_contain_failure(self):
        rows = [passing(str(i)) for i in range(10)]
        rows[-1].update(carrier_complete=False, exact_recovery=False, failure_stage="capacity",
                        failure_reason="packet not complete at cap")
        result = validate_allocation(self.cases, rows)
        self.assertTrue(result["allocation_complete"])
        self.assertFalse(result["all_recovered"])
        self.assertEqual(result["recorded_failure_count"], 1)
        self.assertEqual((result["attempted_count"],result["completed_count"],result["exact_recovery_count"]), (10,9,9))

    def test_complete_passing_allocation(self):
        result = validate_allocation(self.cases, [passing(str(i)) for i in range(10)])
        self.assertTrue(result["allocation_complete"] and result["all_recovered"])

    def test_missing_evidence_or_profile_mismatch_is_not_success(self):
        rows = [passing(str(i)) for i in range(10)]
        rows[0]["evidence_valid"] = False
        self.assertFalse(validate_allocation(self.cases, rows)["allocation_complete"])


if __name__ == "__main__":
    unittest.main()
