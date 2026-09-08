"""Artifact-only fresh-process receiver. No sender, demo or evaluator imports.
Only carrier/profile/context/key are read as message inputs. Reference comparison
and conversion of recovered grayscale bytes to PNG are separate evaluator work.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback
from .packet import open_packet, TEXT, GRAYSCALE
from .fixed_rank import recover_rank, decode_bounded_ranks_to_bytes
from .runtime import read_profile, json_write, canonical_hash


def receive(args):
    inputs = [Path(p).resolve() for p in (args.carrier, args.profile, args.context, args.key)]
    if len(set(inputs)) != 4 or len({p.parent for p in inputs}) != 1:
        raise ValueError("stage four distinct permitted inputs in one receiver directory")
    if {p.resolve() for p in inputs[0].parent.iterdir()} != set(inputs):
        raise ValueError("receiver directory contains undeclared inputs")
    if Path(args.output).resolve().parent == inputs[0].parent or Path(args.report).resolve().parent == inputs[0].parent:
        raise ValueError("outputs must be outside receiver input directory")
    if Path(args.output).exists() or Path(args.report).exists():
        raise FileExistsError("refusing to overwrite recovered output/report")
    profile = read_profile(args.profile)
    context, key = Path(args.context).read_bytes(), Path(args.key).read_bytes()
    if len(key) != 32:
        raise ValueError("wrong key length")
    modality = "text" if args.direction == "image-to-text" else "image"
    record = {"stage": "decode", "direction": args.direction, "profile_id": canonical_hash(profile),
              "model_id": profile[modality]["model_sha256"],
              "carrier": str(Path(args.carrier)), "output": str(Path(args.output)),
              "input_roles": ["carrier", "profile", "context", "key"],
              "input_files": [p.name for p in inputs],
              "packet_complete": False, "authenticated": False, "carrier_complete": False,
              "failure_stage": None, "failure_reason": None}
    model, ranks = None, []
    started = time.monotonic()
    phase = "backend"
    try:
        if modality == "text":
            from .text_backend import TextBackend
            model = TextBackend(profile)
            symbols = model.reconstruct(Path(args.carrier).read_bytes())
            expected_total, expected_kind = 616, GRAYSCALE
        else:
            from .image_backend import ImageBackend, read_png
            pixels = read_png(args.carrier)
            symbols = pixels.reshape(-1).tolist()
            record["pixel_sha256"] = hashlib.sha256(pixels.tobytes()).hexdigest()
            model = ImageBackend(profile)
            expected_total, expected_kind = 2976, TEXT
        record["cold_load_seconds"] = model.load_seconds
        begin = time.monotonic()
        model.start(context)
        phase = "replay"
        for position, symbol in enumerate(symbols):
            ids, q, order = model.distribution()
            if int(symbol) not in ids:
                raise ValueError("ineligible carrier symbol at position " + str(position))
            if position < 584:
                ranks.append(recover_rank(order, int(symbol)))
            model.observe(int(symbol))
            if len(ranks) == 584 and not record["packet_complete"]:
                record["packet_complete"] = True
                phase = "authentication_and_parsing"
                payload = open_packet(decode_bounded_ranks_to_bytes(ranks), key, expected_kind)
                record.update({"authenticated": True, "payload_bytes": len(payload.data),
                               "width": payload.width, "height": payload.height})
                output = Path(args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as stream:
                    stream.write(payload.data)
                record["recovered_sha256"] = hashlib.sha256(payload.data).hexdigest()
                phase = "completion_conformance"
            if (position + 1) % 128 == 0:
                print("replayed %d/%d symbols" % (position + 1, len(symbols)), flush=True)
        if not record["packet_complete"]:
            raise ValueError("capacity exhausted before 584 packet symbols")
        if len(symbols) != expected_total:
            raise ValueError("incorrect fixed carrier completion length")
        record.update({"carrier_complete": True, "packet_stop": 584,
                       "completion_symbols": expected_total - 584, "model_calls": model.calls,
                       "decode_seconds": time.monotonic() - begin})
        if modality == "text":
            record.update({"tokens": len(symbols), "filter_seconds": model.filter_seconds})
        else:
            record.update({"pixels": 992, "channels": len(symbols)})
    except Exception as exc:
        record.update({"failure_stage": phase, "failure_reason": type(exc).__name__ + ": " + str(exc)})
        traceback.print_exc()
    finally:
        if model is not None:
            record["gpu_evidence"] = model.evidence
            model.close()
        record["total_seconds"] = time.monotonic() - started
        json_write(args.report, record)
        print(json.dumps(record), flush=True)
    return 0 if record["authenticated"] and record["carrier_complete"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("direction", choices=["image-to-text", "text-to-image"])
    parser.add_argument("--carrier", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    raise SystemExit(receive(parser.parse_args()))


if __name__ == "__main__":
    main()
