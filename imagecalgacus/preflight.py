"""Bounded GPU feasibility checks; outputs contain no payload reference data."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np

from .fixed_rank import ordinary_sample
from .runtime import read_profile, json_write, canonical_hash, source_hash


def run(args):
    profile = read_profile(args.profile)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    record = {"stage": "preflight", "backend": args.backend, "profile_id": canonical_hash(profile),
              "source_hash": source_hash(), "passed": False}
    model = None
    started = time.monotonic()
    try:
        if args.backend == "text":
            from .text_backend import TextBackend
            model = TextBackend(profile)
            context = b"Write a calm field-journal entry about a walk through a temperate forest. Use continuous prose."
            traces = []
            for _ in range(2):
                model.start(context)
                trace = []
                for step in range(8):
                    ids, q, order = model.distribution()
                    if len(order) < 16:
                        raise ValueError("preflight text support below 16")
                    trace.append(order[:16].tolist())
                    model.observe(int(order[step % 16]))
                traces.append(trace)
            if traces[0] != traces[1]:
                raise ValueError("GPU text reset/replay rank divergence")
            record["rank_replay_equal"] = True
            record["rank_signature"] = canonical_hash(traces[0])
            record["model_calls"] = model.calls
        else:
            from .image_backend import ImageBackend, write_png, read_png
            model = ImageBackend(profile)
            model.probe()
            # Initial step timing permits an early cap projection without a full canvas.
            model.start(None)
            rng = np.random.Generator(np.random.PCG64(profile["context_seed"]))
            generated_ranks = []
            begin = time.monotonic()
            for position in range(3072):
                ids, q, order = model.distribution()
                symbol = ordinary_sample(ids, q, rng)
                generated_ranks.append(int(np.flatnonzero(order == symbol)[0]) + 1)
                model.observe(symbol)
                if position == 95:
                    projected = (time.monotonic() - begin) * 32
                    print(json.dumps({"first_row_seconds": time.monotonic() - begin,
                                      "full_canvas_projected_seconds": projected}), flush=True)
                    if projected * 2 > 1200:
                        raise RuntimeError("ordinary generation/replay projection exceeds feasibility slice")
            record["ordinary_generation_seconds"] = time.monotonic() - begin
            write_png(output / "ordinary.png", model.canvas)
            (output / "row.rgb").write_bytes(model.canvas[0].tobytes())
            pixels = read_png(output / "ordinary.png", (32, 32, 3))
            record["ordinary_pixel_sha256"] = hashlib.sha256(pixels.tobytes()).hexdigest()
            model.start(None)
            begin = time.monotonic()
            recovered_ranks = []
            for symbol in pixels.reshape(-1):
                ids, q, order = model.distribution()
                recovered_ranks.append(int(np.flatnonzero(order == symbol)[0]) + 1)
                model.observe(int(symbol))
            record["ordinary_replay_seconds"] = time.monotonic() - begin
            if generated_ranks != recovered_ranks:
                raise ValueError("ordinary PNG rank replay differs")
            record["rank_replay_equal"] = True
            record["model_calls"] = model.calls
        record["gpu_evidence"] = model.evidence
        record["cold_load_seconds"] = model.load_seconds
        record["passed"] = True
    except Exception as exc:
        record["failure"] = type(exc).__name__ + ": " + str(exc)
        traceback.print_exc()
    finally:
        if model is not None:
            record["gpu_evidence"] = model.evidence
            model.close()
        record["total_seconds"] = time.monotonic() - started
        json_write(output / "result.json", record)
        print(json.dumps(record), flush=True)
    return 0 if record["passed"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--backend", choices=["text", "image"], required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
