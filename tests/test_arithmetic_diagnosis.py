"""Concrete diagnostic gap: zero emission is not the same as no narrowing."""
import copy
import unittest
import numpy as np
from imagecalgacus.arithmetic_coding import ArithmeticCoder
from scripts.diagnose_v1_arithmetic import analyze


def make_rows(distributions):
    coder = ArithmeticCoder()
    rows = []
    for q, symbol in distributions:
        ids = np.arange(len(q))
        step = coder.prepare(ids, np.array(q), ids)
        lower, upper, before = coder.lower, coder.upper, len(coder.bits)
        coder.consume(step, symbol)
        rows.append({"position": coder.positions, "lower": lower, "upper": upper,
            "next_lower": coder.lower, "next_upper": coder.upper, "bits_before": before,
            "emitted": coder.bits[before:], "symbol": symbol,
            "lookahead_zero_bits": coder.lookahead_zero_bits, "done": coder.done,
            "termination_suffix_bits": coder.termination_suffix_bits,
            **{name: step[name].tolist() for name in ("ids", "q", "order", "symbols", "cdf")},
            "partition_diagnostic": step["diagnostic"]})
    return rows


class ArithmeticDiagnosis(unittest.TestCase):
    def test_zero_steps_narrow_and_eventually_emit(self):
        result = analyze(make_rows([([.6, .4], 0)] * 12), "0" * 2336)
        self.assertTrue(all(result["checks"].values()))
        self.assertGreater(result["zero_bit_positions"], 0)
        self.assertGreater(result["bits_recovered"], 0)
        self.assertEqual(result["zero_bit_positions"], result["zero_bit_narrowing_positions"])
        self.assertEqual(result["unchanged_interval_zero_bit_positions"], 0)
        self.assertAlmostEqual(result["information_identity_error_bits"], 0, places=12)

    def test_real_stagnation_after_two_narrowing_steps(self):
        half = 1 << 31
        distributions = [([(half+1)/(2*half), (half-1)/(2*half)], 0),
                         ([(half-2)/(half+1), 3/(half+1)], 1)]
        distributions += [([1/32] * 32, 0)] * 8
        result = analyze(make_rows(distributions), "0" + "1" * 2335)
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["minimum_interval_width"], 3)
        self.assertEqual(result["narrowing_positions_before_rescaling"], 2)
        self.assertEqual(result["single_bin_from_multiple_eligible_positions"], 8)
        self.assertEqual(result["longest_unchanged_interval_run"], 8)
        self.assertEqual(result["longest_zero_bit_run"]["length"], 10)
        self.assertFalse(result["termination_reached"])

    def test_independent_oracle_rejects_bad_record_and_source(self):
        rows = make_rows([([.6, .4], 0)] * 12)
        bad = copy.deepcopy(rows)
        bad[0]["emitted"] = "1"
        self.assertFalse(analyze(bad, "0" * 2336)["checks"]["fractional_interval_and_bit_oracle"])
        result = analyze(rows, "1" * 2336)
        self.assertFalse(result["checks"]["source_prefix_equal"])
        self.assertFalse(result["checks"]["source_window_selects_observed_symbol"])


if __name__ == "__main__":
    unittest.main()
