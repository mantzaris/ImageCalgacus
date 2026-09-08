"""Read-only model-backed profile of the accepted text carrier; no payload/key inputs."""
import argparse
import cProfile
import io
import json
from pathlib import Path
import pstats
import time
from imagecalgacus.runtime import read_profile, json_write, source_hash
from imagecalgacus.text_backend import TextBackend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--carrier", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    model = TextBackend(read_profile(args.profile))
    record = {"source_hash": source_hash(), "purpose": "pre-optimization cProfile of full accepted carrier replay"}
    profile = cProfile.Profile()
    try:
        ids = model.reconstruct(Path(args.carrier).read_bytes())
        started = time.monotonic()
        model.start(Path(args.context).read_bytes())
        profile.enable()
        for i, token in enumerate(ids):
            eligible, q, order = model.distribution()
            if token not in eligible:
                raise ValueError("accepted carrier no longer eligible")
            model.observe(token)
            if i % 128 == 0:
                print("profiled", i, flush=True)
        profile.disable()
        record.update({"tokens":len(ids), "wall_seconds":time.monotonic()-started,
                       "filter_seconds":model.filter_seconds, "cold_load_seconds":model.load_seconds,
                       "gpu_evidence":model.evidence, "completed":True})
        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream).sort_stats("cumulative")
        stats.print_stats(30)
        record["cprofile_summary"] = stream.getvalue()
        profile.dump_stats(str(args.output / "reference.pstats"))
        json_write(args.output / "result.json", record)
        print(json.dumps({k:v for k,v in record.items() if k!="gpu_evidence"}))
    finally:
        model.close()


if __name__ == "__main__":
    main()
