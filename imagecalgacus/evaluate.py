"""Separate source-equality evaluator; never imported by the receiver."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .runtime import json_write


def evaluate_case(case, case_dir):
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
    if gray and recovered is not None and len(recovered) == 256:
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
    json_write(case_dir / "evaluation.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    args = parser.parse_args()
    cases = json.loads(args.references.read_text())["cases"]
    results = [evaluate_case(case, args.run / case["id"]) for case in cases if (args.run / case["id"]).exists()]
    with (args.run / "results.jsonl").open("w") as stream:
        for result in results:
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(json.dumps({"evaluated": len(results), "exact": sum(r["exact_recovery"] for r in results),
                      "complete_and_exact": sum(r["exact_recovery"] and r["carrier_complete"] for r in results)}))
    return 0 if results and all(r["exact_recovery"] and r["carrier_complete"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
