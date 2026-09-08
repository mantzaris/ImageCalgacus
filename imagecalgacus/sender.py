"""Single fresh-key encoding run. No neural inference on CPU."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import traceback
import numpy as np
from PIL import Image
from .packet import NewRun, Payload, TEXT, GRAYSCALE
from .fixed_rank import packet_ranks, choose_rank, ordinary_sample
from .runtime import read_profile, json_write, canonical_hash, source_hash, sha256_file


def read_source(path, direction):
    path = Path(path)
    if direction == "image-to-text":
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode != "L" or image.size != (16, 16):
                raise ValueError("source must be a canonical 16x16 8-bit grayscale PNG")
            data = np.asarray(image, dtype=np.uint8).tobytes()
        return Payload(GRAYSCALE, data, 16, 16).validate()
    return Payload(TEXT, path.read_bytes()).validate()


def encode(args):
    profile = read_profile(args.profile)
    payload = read_source(args.source, args.direction)
    context = Path(args.context).read_bytes()
    run = NewRun(args.new_run)
    inbox = run.directory / "inbox"
    inbox.mkdir(mode=0o700)
    ranks = packet_ranks(run.encrypt(payload))
    shutil.copy2(run.directory / "run.key", inbox / "run.key")
    json_write(inbox / "profile.json", profile)
    context_name = "prompt.txt" if args.direction == "image-to-text" else "row.rgb"
    (inbox / context_name).write_bytes(context)
    source_name = "source.png" if args.direction == "image-to-text" else "source.txt"
    shutil.copyfile(args.source, run.directory / source_name)
    json_write(run.directory / "reference.json", {"kind": payload.kind, "bytes": len(payload.data),
               "sha256": hashlib.sha256(payload.data).hexdigest(),
               "source": source_name, "width": payload.width, "height": payload.height})
    modality = "text" if args.direction == "image-to-text" else "image"
    result = {"stage": "encode", "direction": args.direction, "profile_id": canonical_hash(profile),
              "source_hash": source_hash(), "model_id": profile[modality]["model_sha256"],
              "packet_complete": False, "carrier_complete": False, "packet_bytes": 292,
              "failure_stage": None, "failure_reason": None}
    model = None
    start = time.monotonic()
    phase, emitted = "backend", 0
    try:
        if modality == "text":
            from .text_backend import TextBackend
            model = TextBackend(profile)
            carrier, limit = inbox / "carrier.txt", 616
        else:
            from .image_backend import ImageBackend
            model = ImageBackend(profile)
            carrier, limit = inbox / "carrier.png", 2976
        result["cold_load_seconds"] = model.load_seconds
        generation_start = time.monotonic()
        model.start(context)
        phase = "generation"
        rng = np.random.Generator(np.random.PCG64(profile["completion_seed"]))
        support_minimum = 1000000
        for position in range(limit):
            ids, q, order = model.distribution()
            support_minimum = min(support_minimum, len(order))
            symbol = choose_rank(order, ranks[position]) if position < 584 else ordinary_sample(ids, q, rng)
            model.observe(symbol)
            emitted += 1
            if emitted == 584:
                result["packet_complete"] = True
            if emitted % 128 == 0:
                print("generated %d/%d symbols" % (emitted, limit), flush=True)
        phase = "serialization"
        if modality == "text":
            carrier.write_bytes(model.serialize())
            result.update({"tokens": emitted, "filter_seconds": model.filter_seconds})
        else:
            from .image_backend import write_png
            write_png(carrier, model.canvas[1:])
            result.update({"pixels": 992, "channels": 2976,
                           "pixel_sha256": hashlib.sha256(model.canvas[1:].tobytes()).hexdigest()})
        result.update({"carrier": str(carrier), "carrier_bytes": carrier.stat().st_size,
                       "carrier_sha256": sha256_file(carrier), "carrier_complete": True,
                       "encode_seconds": time.monotonic() - generation_start,
                       "packet_stop": 584, "completion_symbols": limit - 584,
                       "support_minimum": support_minimum, "model_calls": model.calls})
    except Exception as exc:
        result.update({"failure_stage": phase, "failure_reason": type(exc).__name__ + ": " + str(exc)})
        traceback.print_exc()
        if model is not None:
            if modality == "text":
                try:
                    (run.directory / "failed-prefix.txt").write_bytes(model.serialize())
                except Exception:
                    pass
            else:
                np.save(run.directory / "failed-prefix.npy", model.canvas.reshape(-1)[:model.position])
    finally:
        if model is not None:
            result["gpu_evidence"] = model.evidence
            model.close()
        result["emitted_symbols"] = emitted
        result["total_seconds"] = time.monotonic() - start
        json_write(run.directory / "sender.json", result)
        print(json.dumps(result), flush=True)
    return 0 if result["carrier_complete"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("direction", choices=["image-to-text", "text-to-image"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--new-run", required=True)
    raise SystemExit(encode(parser.parse_args()))


if __name__ == "__main__":
    main()
