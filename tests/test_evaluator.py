"""Negative evaluator checks: authentication is not source-byte equality."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from imagecalgacus.evaluate import evaluate_case


class IndependentEquality(unittest.TestCase):
    def test_authenticated_output_must_still_equal_frozen_source(self):
        source = b"Meet me beside the old oak tree."
        case = {"id": "T1", "direction": "text-to-image",
                "source_sha256": hashlib.sha256(source).hexdigest()}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.txt").write_bytes(source)
            (root / "sender.json").write_text(json.dumps({
                "profile_id": "same", "packet_complete": True, "carrier_complete": True}))
            (root / "receiver.json").write_text(json.dumps({
                "profile_id": "same", "authenticated": True, "carrier_complete": True,
                "width": 0, "height": 0}))
            # A successful authentication flag cannot make changed bytes equal.
            (root / "recovered.txt").write_bytes(source[:-1] + b"!")
            result = evaluate_case(case, root)
            self.assertTrue(result["authenticated"])
            self.assertFalse(result["source_equal"])
            self.assertFalse(result["exact_recovery"])
            # Matching bytes must also refer to the originally frozen fixture.
            (root / "source.txt").write_bytes(source[:-1] + b"!")
            result = evaluate_case(case, root)
            self.assertTrue(result["source_equal"])
            self.assertFalse(result["fixture_matches_frozen_reference"])
            self.assertFalse(result["exact_recovery"])
            (root / "source.txt").write_bytes(source)
            (root / "recovered.txt").write_bytes(source)
            self.assertTrue(evaluate_case(case, root)["exact_recovery"])


if __name__ == "__main__":
    unittest.main()
