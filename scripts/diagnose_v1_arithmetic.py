"""CPU-only audit of private receiver traces. Never called/imported by a receiver.

Use the existing independent Fraction/half-interval oracle, not coder roundtrips.
Only compact statistics/booleans leave .runtime; packet bits and bounds stay private.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from test_v1_coders import fractional_step
from imagecalgacus.runtime import json_write, sha256_file


def scalar_partition(row):
    """Independent scalar check of A1's specified partition (no production calls)."""
    width = row["upper"] - row["lower"]
    probabilities = dict(zip(row["ids"], row["q"]))
    selected = [symbol for rank, symbol in enumerate(row["order"])
                if rank < min(2, len(probabilities), width) or probabilities[symbol] >= 1 / width]
    mass = math.fsum(probabilities[symbol] for symbol in selected)
    bins = []
    total = 0
    for symbol in selected:
        size = round(probabilities[symbol] / mass * width)
        if total + size > width:
            break
        bins.append([symbol, size])
        total += size
    bins[0][1] += width - total
    symbols, cdf = [], [0]
    for symbol, size in bins:
        if size:
            symbols.append(symbol)
            cdf.append(cdf[-1] + size)
    return symbols, cdf


def analyze(rows, source_bits=None):
    bound = 1 << 32
    lo, hi, bits = Fraction(0), Fraction(1), ""
    surprisal = entropy = quantized_surprisal = 0.0
    zero_run = unchanged_run = maximum_unchanged = 0
    longest_zero = {"length": 0}
    unchanged = collapsed = narrowed = zero_narrowed = 0
    widths, supports, retained = [], [], []
    checks = {"fractional_interval_and_bit_oracle": True, "scalar_partition_oracle": True,
              "prefix_chain": True, "source_prefix_equal": source_bits is not None,
              "source_window_selects_observed_symbol": source_bits is not None}
    checkpoints = []
    for index, row in enumerate(rows, 1):
        width = row["upper"] - row["lower"]
        checks["prefix_chain"] &= (row["position"] == index and row["bits_before"] == len(bits)
                                    and (row["lower"], row["upper"]) == (int(lo * bound), int(hi * bound)))
        symbols, cdf = scalar_partition(row)
        checks["scalar_partition_oracle"] &= (symbols == row["symbols"] and cdf == row["cdf"])
        bucket = row["symbols"].index(row["symbol"])
        low_offset, high_offset = row["cdf"][bucket:bucket+2]
        bin_width = high_offset - low_offset
        if source_bits is not None:
            point = int(source_bits[len(bits):len(bits)+32].ljust(32, "0"), 2)
            checks["source_window_selects_observed_symbol"] &= (
                row["lower"] + low_offset <= point < row["lower"] + high_offset)
        lo, hi, emitted = fractional_step(lo, hi, low_offset, high_offset, width)
        checks["fractional_interval_and_bit_oracle"] &= (
            emitted == row["emitted"] and (int(lo*bound), int(hi*bound)) == (row["next_lower"], row["next_upper"]))
        bits += emitted
        if source_bits is not None:
            checks["source_prefix_equal"] &= bits == source_bits[:len(bits)].ljust(len(bits), "0")
        probability = row["q"][row["ids"].index(row["symbol"])]
        surprisal += -math.log2(probability)
        entropy += math.fsum(-p*math.log2(p) for p in row["q"])
        quantized_surprisal += -math.log2(bin_width / width)
        widths.append(width)
        supports.append(len(row["symbols"]))
        retained.append(row["partition_diagnostic"]["retained_mass"])
        did_narrow = bin_width < width  # BEFORE common-prefix rescaling!
        did_not_change = (row["lower"], row["upper"]) == (row["next_lower"], row["next_upper"])
        narrowed += did_narrow
        zero_narrowed += not emitted and did_narrow
        unchanged += did_not_change and not emitted
        collapsed += len(row["symbols"]) == 1 and len(row["ids"]) > 1
        unchanged_run = unchanged_run + 1 if did_not_change and not emitted else 0
        maximum_unchanged = max(maximum_unchanged, unchanged_run)
        zero_run = zero_run + 1 if not emitted else 0
        if zero_run > longest_zero["length"]:
            longest_zero = {"length": zero_run, "start_position": index-zero_run+1, "end_position": index}
        if index % 128 == 0 or index == len(rows):
            checkpoints.append({"position": index, "recovered_bits": len(bits),
                "cumulative_eligible_surprisal_bits": surprisal, "cumulative_eligible_entropy_bits": entropy,
                "cumulative_quantized_selected_surprisal_bits": quantized_surprisal,
                "interval_width_after_rescaling": row["next_upper"]-row["next_lower"],
                "quantized_support": len(row["symbols"]), "retained_mass": retained[-1],
                "selected_quantized_probability": bin_width / width})
    final_width = rows[-1]["next_upper"] - rows[-1]["next_lower"]
    pending_information = math.log2(bound / final_width)
    return {"positions": len(rows), "bits_recovered": len(bits), "target_bits": 2336,
        "eligible_surprisal_bits": surprisal, "eligible_entropy_bits": entropy,
        "quantized_selected_surprisal_bits": quantized_surprisal,
        "quantized_minus_eligible_surprisal_bits": quantized_surprisal-surprisal,
        "final_interval_width": final_width, "minimum_interval_width": min(widths+[final_width]),
        "maximum_interval_width": max(widths), "pending_interval_information_bits": pending_information,
        "information_identity_error_bits": quantized_surprisal-len(bits)-pending_information,
        "quantized_support_min": min(supports), "quantized_support_max": max(supports),
        "minimum_retained_mass": min(retained), "single_bin_from_multiple_eligible_positions": collapsed,
        "narrowing_positions_before_rescaling": narrowed, "zero_bit_narrowing_positions": zero_narrowed,
        "zero_bit_positions": sum(not r["emitted"] for r in rows), "longest_zero_bit_run": longest_zero,
        "unchanged_interval_zero_bit_positions": unchanged, "longest_unchanged_interval_run": maximum_unchanged,
        "zero_extension_reached": any(r["lookahead_zero_bits"] for r in rows),
        "termination_reached": any(r["done"] for r in rows),
        "checks": checks, "checkpoints_128_positions": checkpoints}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cases = []
    for case, run, packets in (("I1", "v1-pilot-001", "v1-packets-001"),
                               ("I5", "v1-pilot-002", "v1-packets-002")):
        directory = ROOT / ".runtime/v1_1/diagnostics" / case
        rows = [json.loads(line) for line in (directory/"trace.jsonl").read_text().splitlines()]
        # Evaluator-only original packet. Never an input of either receiver process.
        packet = (ROOT/"runs"/packets/(case+".packet")).read_bytes()
        assert len(packet) == 292
        summary = analyze(rows, "".join(format(byte, "08b") for byte in packet))
        old = ROOT/"runs"/run/(case+"-arithmetic")
        original = json.loads((old/"receiver.json").read_text())
        sender = json.loads((old/"sender.json").read_text())
        replay = json.loads((directory/"receiver.json").read_text())
        summary["checks"].update({
            "original_progress_reproduced": original["packet_bits_recovered"] == sender["packet_bits_recovered"] == summary["bits_recovered"] == replay["packet_bits_recovered"],
            "original_aggregate_diagnostics_reproduced": original["diagnostics"] == replay["diagnostics"] and original["coder_diagnostics"] == replay["coder_diagnostics"],
            "profile_and_model_unchanged": all(original[k] == replay[k] for k in ("profile_id", "model_id")),
            "fresh_receiver_process": original["gpu_evidence"]["device"]["pid"] != replay["gpu_evidence"]["device"]["pid"],
            "four_permitted_inputs_only": replay["input_roles"] == ["carrier", "profile", "context", "key"] and len(list((old/"inbox").iterdir())) == 4})
        summary.update({"case": case+"-arithmetic", "diagnostic_not_new_observation": True,
            "original_public_carrier": "../v1_review/cases/"+case+"-arithmetic/carrier.txt",
            "carrier_sha256": sha256_file(old/"inbox/carrier.txt"),
            "private_trace": str((directory/"trace.jsonl").relative_to(ROOT)),
            "private_trace_sha256": sha256_file(directory/"trace.jsonl"),
            "receiver_report": "diagnostics/"+case+"/receiver.json",
            "packet_complete": replay["packet_complete"], "carrier_complete": replay["carrier_complete"],
            "authenticated": replay["authenticated"], "failure_stage": replay["failure_stage"]})
        cases.append(summary)
    result = {"cases": cases, "all_checks_passed": all(all(c["checks"].values()) for c in cases),
              "scope": "CPU audit of two diagnostic replays; no new stego units and no full payload recovery claim"}
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    json_write(output, result)
    print(json.dumps({"all_checks_passed": result["all_checks_passed"], "cases": [
        {k:v for k,v in c.items() if k not in {"checkpoints_128_positions", "private_trace_sha256"}} for c in cases]}, indent=2))
    return int(not result["all_checks_passed"])


if __name__ == "__main__":
    raise SystemExit(main())
