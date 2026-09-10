"""Key-free saved-PNG likelihood observer, using the unchanged CUDA graph backend.

No labels, sources, packets, keys, or sender diagnostics are inputs. The retained
Trace whole-carrier accumulator preserves V2's summation and scoring precision.
"""
import argparse
import hashlib
import time
from pathlib import Path
import numpy as np
from .coders import Trace
from .image_backend import ImageBackend, read_png
from .runtime import atomic_json, canonical_hash, read_profile, sha256_file, source_hash


def score_pixels(model, pixels, context, trace):
    """Observe actual raster RGB symbols; do not decode or sample any symbols."""
    if pixels.shape != (31, 32, 3) or pixels.dtype != np.uint8:
        raise ValueError("exact 31x32 RGB8 delivered pixels required")
    if len(context) != 96:
        raise ValueError("conditioning row must have exactly 96 bytes")
    model.start(context)
    for symbol in pixels.reshape(-1):
        ids, probabilities, order = model.distribution()
        index = np.flatnonzero(ids == symbol)
        if len(index) != 1 or int(symbol) not in order:
            raise ValueError("observed symbol outside eligible numerical support")
        value = float(probabilities[index[0]])
        if not np.isfinite(value) or value <= 0:
            raise ValueError("zero or invalid observed-symbol probability; no clipping")
        # Only the 'whole' group is reported: no packet/completion role is inferred.
        trace.observe(ids, probabilities, order, int(symbol), "completion", 0, model)
        model.observe(int(symbol))
    return trace.summary()["whole"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("carrier", "context", "profile", "report"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("immutable observer report already exists")
    started = time.monotonic()
    profile = read_profile(args.profile)
    context = args.context.read_bytes()
    pixels = read_png(args.carrier)
    if len(context) != 96:
        raise ValueError("conditioning row must have exactly 96 bytes")
    result = dict(schema="png-observer-v1", purpose="likelihood-only",
        source_hash=source_hash(), profile_id=canonical_hash(profile),
        model_id=profile["image"]["model_sha256"], carrier_sha256=sha256_file(args.carrier),
        pixel_sha256=hashlib.sha256(pixels.tobytes()).hexdigest(),
        context_sha256=hashlib.sha256(context).hexdigest(),
        dimensions=[32,31], expected_channels=2976, scored_channels=0,
        passed=False, scores=None, failure_stage=None, failure_reason=None)
    model = None
    trace = Trace()
    stage = "model_loading"
    try:
        model = ImageBackend(profile, execution_mode="cuda_graph", audit=True)
        result["cold_load_seconds"] = model.load_seconds
        stage = "scoring"
        begin = time.monotonic()
        result["scores"] = score_pixels(model, pixels, context, trace)
        result["scoring_seconds"] = time.monotonic()-begin
        result["model_calls"] = model.calls
        if result["scores"]["positions"] != 2976 or model.calls != 992:
            raise ValueError("incomplete delivered-channel accounting")
        result["passed"] = True
    except Exception as exc:
        result.update(failure_stage=stage, failure_reason=type(exc).__name__+": "+str(exc), scores=None)
    finally:
        result["scored_channels"] = trace.summary()["whole"]["positions"]
        if model is not None:
            result["gpu_evidence"] = model.evidence
            model.close()
        result["total_seconds"] = time.monotonic()-started
        atomic_json(args.report, result)
    print("scored_channels", result["scored_channels"], "passed", result["passed"], flush=True)
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
