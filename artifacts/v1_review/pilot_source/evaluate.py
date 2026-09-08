"""Separate source-equality evaluator; never imported by the receiver."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .runtime import json_write, canonical_hash, sha256_file


def evaluate_case(case, case_dir, write=False):
    case_dir = Path(case_dir)
    sender = json.loads((case_dir / "sender.json").read_text()) if (case_dir / "sender.json").exists() else {}
    receiver = json.loads((case_dir / "receiver.json").read_text()) if (case_dir / "receiver.json").exists() else {}
    gray = case["direction"] == "image-to-text"
    source = case_dir / ("source.png" if gray else "source.txt")
    if gray and source.exists():
        with Image.open(source) as im:
            expected = np.asarray(im, dtype=np.uint8).tobytes()
    else:
        expected = source.read_bytes() if source.exists() else None
    output = case_dir / ("recovered.gray" if gray else "recovered.txt")
    recovered = output.read_bytes() if output.exists() else None
    equal = expected is not None and recovered is not None and expected == recovered
    frozen = expected is not None and hashlib.sha256(expected).hexdigest() == case["source_sha256"]
    dimensions = (receiver.get("width"), receiver.get("height")) == ((16, 16) if gray else (0, 0))
    exact = bool(equal and frozen and dimensions and receiver.get("authenticated"))
    if write and gray and recovered is not None and len(recovered) == 256:
        Image.fromarray(np.frombuffer(recovered, dtype=np.uint8).reshape(16, 16)).save(case_dir / "recovered.png")
    result = {"case": case["id"], "direction": case["direction"], "source_equal": equal,
              "fixture_matches_frozen_reference": frozen, "exact_recovery": exact,
              "authenticated": receiver.get("authenticated", False),
              "packet_complete": sender.get("packet_complete", False),
              "carrier_complete": bool(sender.get("carrier_complete") and receiver.get("carrier_complete")),
              "profile_id": sender.get("profile_id"), "model_id": sender.get("model_id"),
              "sender_profile_matches_receiver": bool(receiver) and sender.get("profile_id") == receiver.get("profile_id"),
              "gpu_device": sender.get("gpu_evidence", {}).get("device", {}).get("uuid"),
              "sender_gpu_evidence": str(case_dir / "sender.json"),
              "receiver_gpu_evidence": str(case_dir / "receiver.json"),
              "source": str(source), "carrier": sender.get("carrier"), "recovered": str(output),
              "encode_seconds": sender.get("encode_seconds"), "decode_seconds": receiver.get("decode_seconds"),
              "sender_total_seconds": sender.get("total_seconds"), "receiver_total_seconds": receiver.get("total_seconds"),
              "sender_load_seconds": sender.get("cold_load_seconds"), "receiver_load_seconds": receiver.get("cold_load_seconds"),
              "carrier_bytes": sender.get("carrier_bytes"), "carrier_sha256": sender.get("carrier_sha256"),
              "tokens": sender.get("tokens"), "pixels": sender.get("pixels"), "channels": sender.get("channels"),
              "packet_stop": sender.get("packet_stop"), "completion_symbols": sender.get("completion_symbols"),
              "source_bytes": len(expected) if expected is not None else None,
              "source_sha256": hashlib.sha256(expected).hexdigest() if expected is not None else None,
              "recovered_sha256": hashlib.sha256(recovered).hexdigest() if recovered is not None else None,
              "failure_stage": sender.get("failure_stage") or receiver.get("failure_stage"),
              "failure_reason": sender.get("failure_reason") or receiver.get("failure_reason")}
    declared = case.get("profile_id")
    model_id = case.get("model_id")
    identity = bool(sender.get("profile_id") and sender.get("model_id"))
    identity &= declared is None or sender.get("profile_id") == declared
    identity &= model_id is None or sender.get("model_id") == model_id
    identity &= sender.get("method", "fixed") == case.get("method", "fixed")
    if receiver:
        identity &= receiver.get("method", "fixed") == case.get("method", "fixed")
        identity &= sender.get("profile_id") == receiver.get("profile_id")
        identity &= sender.get("model_id") == receiver.get("model_id")
        identity &= sender.get("direction") == receiver.get("direction") == case["direction"]
    carrier_name = "carrier.txt" if gray else "carrier.png"
    carrier = case_dir / "inbox" / carrier_name
    if not carrier.exists():
        carrier = case_dir / carrier_name  # public review layout
    terminal_failure = bool(result["failure_stage"] and result["failure_reason"])
    attempted = bool(sender) or (case_dir / "attempt.json").exists()
    terminal = bool(sender) and (bool(receiver) or terminal_failure)
    complete = bool(result["carrier_complete"])
    evidence = bool(identity)
    if complete:
        evidence &= bool(receiver.get("packet_complete") and sender.get("packet_complete"))
        evidence &= carrier.is_file() and sender.get("carrier_sha256") == sha256_file(carrier)
        for report in (sender, receiver):
            gpu = report.get("gpu_evidence", {})
            device = gpu.get("device", {})
            evidence &= bool(device.get("uuid") and device.get("pid"))
            if gray:
                layers = gpu.get("offloaded_layers", [])
                evidence &= len(layers) == 2 and layers[0] == layers[1] and layers[0] > 0
            else:
                evidence &= gpu.get("parameter_devices") == ["cuda:0"] and gpu.get("input_device") == "cuda:0"
                evidence &= bool(gpu.get("inference_mode") and gpu.get("strict_loading"))
        evidence &= sender.get("gpu_evidence", {}).get("device", {}).get("uuid") == receiver.get("gpu_evidence", {}).get("device", {}).get("uuid")
    else:
        evidence &= terminal_failure
    progress_fields = ("packet_stop","packet_positions","skipped_positions","zero_bit_positions","packet_bits_recovered")
    progress_matches = not receiver or all(sender.get(k) == receiver.get(k) for k in progress_fields if k in sender)
    if receiver and not progress_matches:
        evidence = False
    result.update({"coder_progress_matches":progress_matches,"prepared_packet_sha256":sender.get("prepared_packet_sha256")})
    count = sender.get("tokens") if gray else sender.get("channels")
    delivered = count if carrier.exists() else None
    payload_bits = 8*len(expected) if expected is not None else None
    rate = payload_bits/delivered if delivered and payload_bits is not None else None
    result.update({"packet_bytes":292,"framing_bytes":36,"slot_padding_bytes":256-len(expected) if expected is not None else None,
                   "useful_bits_per_token":rate if gray else None,
                   "useful_bits_per_channel":rate if not gray else None,
                   "useful_bits_per_pixel":payload_bits/sender["pixels"] if not gray and delivered else None,
                   "exact_goodput_bits_per_symbol":rate if exact and complete else 0.0 if delivered else None,
                   "packet_transport_bits_per_symbol":2336/sender["packet_stop"] if sender.get("packet_stop") else None,
                   "serialized_expansion":sender.get("carrier_bytes",0)/len(expected) if delivered and expected else None,
                   "sender_model_calls":sender.get("model_calls"),"receiver_model_calls":receiver.get("model_calls"),
                   "sender_peak_rss_kib":sender.get("peak_rss_kib"),"receiver_peak_rss_kib":receiver.get("peak_rss_kib")})
    result.update({"work_id": case.get("work_id", case["id"]), "method": case.get("method", "fixed"),
                   "attempted": attempted, "terminal": terminal, "evidence_valid": bool(evidence),
                   "identity_consistent": bool(identity), "carrier": str(carrier) if carrier.exists() else None})
    for field in ("packet_positions", "skipped_positions", "zero_bit_positions", "termination_positions",
                  "termination_suffix_bits", "lookahead_zero_bits", "diagnostics", "coder_diagnostics",
                  "peak_rss_kib", "packet_bits_recovered"):
        if field in sender:
            result[field] = sender[field]
    if write:
        json_write(case_dir / "evaluation.json", result)
    return result



def validate_allocation(cases, rows, actual_ids=None):
    """Report coverage separately from success. Duplicate IDs never add trials."""
    expected = [case.get("work_id", case["id"]) for case in cases]
    observed = [row.get("work_id", row["case"]) for row in rows]
    expected_counts, observed_counts = Counter(expected), Counter(observed)
    duplicate_expected = sorted(k for k, n in expected_counts.items() if n > 1)
    duplicate_results = sorted(k for k, n in observed_counts.items() if n > 1)
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    if actual_ids is not None:
        unexpected = sorted(set(unexpected) | (set(actual_ids) - {c["id"] for c in cases}))
    unique = {row.get("work_id", row["case"]): row for row in rows}
    selected = [unique[k] for k in dict.fromkeys(expected) if k in unique]
    unstarted = [r.get("work_id", r["case"]) for r in selected if not r.get("attempted")]
    unfinished = [r.get("work_id", r["case"]) for r in selected if not r.get("terminal")]
    invalid = [r.get("work_id", r["case"]) for r in selected if not r.get("evidence_valid")]
    complete = bool(expected) and not any((duplicate_expected, duplicate_results, missing, unexpected,
                                          unstarted, unfinished, invalid))
    attempted = sum(bool(r.get("attempted")) for r in selected)
    completed = sum(bool(r.get("carrier_complete") and r.get("evidence_valid")) for r in selected)
    exact = sum(bool(r.get("exact_recovery") and r.get("evidence_valid")) for r in selected)
    return {"allocation_complete": complete, "expected_count": len(set(expected)),
            "attempted_count": attempted, "completed_count": completed,
            "packet_completed_count":sum(bool(r.get("packet_complete")) for r in selected),
            "authenticated_count":sum(bool(r.get("authenticated")) for r in selected),
            "exact_recovery_count": exact, "all_recovered": bool(complete and completed == len(expected) and exact == len(expected)),
            "recorded_failure_count": sum(bool(r.get("terminal") and not (r.get("carrier_complete") and r.get("exact_recovery"))) for r in selected),
            "missing_identifiers": missing, "unexpected_identifiers": unexpected,
            "duplicate_expected_identifiers": duplicate_expected, "duplicate_result_identifiers": duplicate_results,
            "unstarted_identifiers": unstarted, "unfinished_identifiers": unfinished, "invalid_evidence_identifiers": invalid}


def evaluate_run(run, cases, mode="final", recorded_rows=None):
    run = Path(run)
    actual = sorted(p.name for p in run.iterdir() if p.is_dir()) if run.exists() else []
    rows = [evaluate_case(case, run / case["id"], write=mode == "progress")
            for case in cases if (run / case["id"]).is_dir()]
    summary = validate_allocation(cases, rows, actual_ids=actual)
    if recorded_rows is not None:
        ids = [r.get("work_id", r["case"]) for r in recorded_rows]
        expected = {c.get("work_id", c["id"]) for c in cases}
        duplicates = sorted(k for k, n in Counter(ids).items() if n > 1)
        missing, unexpected = sorted(expected - set(ids)), sorted(set(ids) - expected)
        summary["recorded_result_reconciliation"] = {"missing": missing, "unexpected": unexpected, "duplicates": duplicates}
        if duplicates or unexpected or (missing and mode == "final"):
            summary["allocation_complete"] = summary["all_recovered"] = False
    return rows, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--mode", choices=["progress", "final"], default="final")
    parser.add_argument("--results", type=Path, help="existing results to reconcile; defaults to RUN/results.jsonl")
    parser.add_argument("--phase", help="explicit phase filter for combined historical review results")
    parser.add_argument("--output", type=Path, help="new summary path; final validation never rewrites historical results")
    parser.add_argument("--allow-failures", action="store_true", help="final exit success means complete allocation, not all-recovered")
    args = parser.parse_args()
    cases = json.loads(args.references.read_text())["cases"]
    records_path = args.results or args.run / "results.jsonl"
    recorded = [json.loads(line) for line in records_path.read_text().splitlines()] if records_path.exists() else None
    if recorded is not None and args.phase:
        recorded = [row for row in recorded if row.get("phase") == args.phase]
    if args.mode == "progress" and ("v0_review" in args.run.parts or args.run.name in {"ten-001", "preliminary-001"}):
        raise ValueError("accepted V0 evidence is read-only; use final validation with a separate output")
    rows, summary = evaluate_run(args.run, cases, args.mode, recorded)
    summary["mode"] = args.mode
    summary["exit_requires_all_recovered"] = not args.allow_failures
    if args.mode == "progress":
        with (args.run / "results.jsonl").open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    if args.output:
        if args.output.exists():
            raise FileExistsError("refusing to overwrite validation report")
        json_write(args.output, dict(summary, results=rows))
    print(json.dumps(summary))
    if args.mode == "progress":
        return int(bool(summary["duplicate_expected_identifiers"] or summary["duplicate_result_identifiers"] or summary["unexpected_identifiers"]))
    return 0 if summary["allocation_complete"] and (args.allow_failures or summary["all_recovered"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
