"""Ten preselected V0 fixtures and a simple serial demonstration, not a scheduler."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image
from .runtime import ROOT, read_profile, json_write, source_hash, run_budgeted, budget_state, GPU_LIMIT_SECONDS

TEXTS = [
    "Meet me beside the old oak tree.",
    "Bring the blue notebook to our meeting tomorrow.",
    "Le café est ouvert; retrouvons-nous près du vieux pont à midi",
    "The river is quiet tonight. Please leave the blue notebook beside the window before you go home.",
    "We will meet after the rain has stopped. Bring a notebook, two pencils, and the small map showing the paths through the forests.",
]
PROMPT = b"Write a calm field-journal entry about a walk through a temperate forest. Use continuous prose."


def prepare():
    folder = ROOT / "artifacts/v0_review/fixtures"
    folder.mkdir(parents=True, exist_ok=False)
    r, c = np.indices((16, 16))
    arrays = [(17 * c).astype(np.uint8), (255 * ((r + c) % 2)).astype(np.uint8),
              np.floor(255 * (r + c) / 30).astype(np.uint8),
              (255 * ((r >= 4) & (r <= 11) & (c >= 4) & (c <= 11))).astype(np.uint8),
              np.random.Generator(np.random.PCG64(20260907)).integers(0, 256, (16, 16), dtype=np.uint8)]
    cases = []
    for i, pixels in enumerate(arrays, 1):
        file = folder / ("I%d.png" % i)
        Image.fromarray(pixels).save(file)
        cases.append({"id": "I%d" % i, "direction": "image-to-text", "source": str(file.relative_to(ROOT)),
                      "bytes": 256, "source_sha256": hashlib.sha256(pixels.tobytes()).hexdigest()})
    for i, (text, count) in enumerate(zip(TEXTS, [32, 48, 64, 96, 128]), 1):
        raw = text.encode("utf-8")
        if len(raw) != count:
            raise ValueError("fixture byte length changed")
        file = folder / ("T%d.txt" % i)
        file.write_bytes(raw)
        cases.append({"id": "T%d" % i, "direction": "text-to-image", "source": str(file.relative_to(ROOT)),
                      "bytes": count, "source_sha256": hashlib.sha256(raw).hexdigest()})
    json_write(ROOT / "configs/v0_cases.json", {"fixtures_frozen_before_generation": True,
               "numpy": np.__version__, "noise_generator": "PCG64 integers(0,256,(16,16),dtype=uint8), seed=20260907",
               "cases": cases})
    contexts = ROOT / "artifacts/v0_review/contexts"
    contexts.mkdir(parents=True, exist_ok=True)
    (contexts / "prompt.txt").write_bytes(PROMPT)
    print(json.dumps({"prepared": [c["id"] for c in cases], "text_byte_lengths": [32, 48, 64, 96, 128]}))


def execute(args):
    profile = read_profile(args.profile)
    manifest = json.loads(Path(args.cases).read_text())
    cases = [case for case in manifest["cases"] if args.mode == "ten" or case["id"] in ("I1", "T1")]
    projection = None
    if args.mode == "ten":
        if not args.pilot:
            raise ValueError("--pilot with successful preliminary results is required before ten cases")
        pilot = Path(args.pilot)
        rows = [json.loads(line) for line in (pilot / "results.jsonl").read_text().splitlines()]
        if len(rows) != 2 or not all(r["exact_recovery"] and r["carrier_complete"] for r in rows):
            raise ValueError("both preliminary artifact recoveries must pass")
        used, ledger = budget_state()
        measured = {}
        for row in rows:
            costs = []
            for stage in ("encode", "decode"):
                match = [r["elapsed_seconds"] for r in ledger if r["event"] == "finished"
                         and r["id"].endswith(pilot.name + "-" + row["case"] + "-" + stage)]
                if not match:
                    raise ValueError("missing measured pilot cost")
                costs.append(max(match))
            measured[row["direction"]] = sum(costs)
        projected = 1.25 * (used + 5 * sum(measured.values()))
        projection = {"used_seconds": used, "measured_pair_seconds": measured,
                      "remaining_pairs_each_direction": 5, "reserve_multiplier": 1.25,
                      "projected_total_seconds": projected, "ceiling_seconds": GPU_LIMIT_SECONDS}
        print(json.dumps(projection), flush=True)
        if projected > GPU_LIMIT_SECONDS:
            raise RuntimeError("measured V0 projection exceeds the two-hour allowance")
    outer = Path(args.new_run)
    outer.mkdir(parents=True, exist_ok=False, mode=0o700)
    json_write(outer / "references.json", {"cases": cases})
    if projection is not None:
        json_write(outer / "compute_projection.json", projection)
    json_write(outer / "implementation.json", {"source_hash": source_hash(), "profile": profile})
    for case in cases:
        modality = "text" if case["direction"] == "image-to-text" else "image"
        case_dir = outer / case["id"]
        context = ROOT / "artifacts/v0_review/contexts" / ("prompt.txt" if modality == "text" else "row.rgb")
        command = [profile[modality]["interpreter"], "-B", "-m", "imagecalgacus.sender", case["direction"],
                   "--source", str(ROOT / case["source"]), "--profile", str(Path(args.profile).resolve()),
                   "--context", str(context), "--new-run", str(case_dir)]
        result = run_budgeted(command, outer.name + "-" + case["id"] + "-encode")
        if result == 0:
            inbox = case_dir / "inbox"
            command = [profile[modality]["interpreter"], "-B", "-m", "imagecalgacus.receiver", case["direction"],
                       "--carrier", str(inbox / ("carrier.txt" if modality == "text" else "carrier.png")),
                       "--profile", str(inbox / "profile.json"),
                       "--context", str(inbox / ("prompt.txt" if modality == "text" else "row.rgb")),
                       "--key", str(inbox / "run.key"),
                       "--output", str(case_dir / ("recovered.gray" if modality == "text" else "recovered.txt")),
                       "--report", str(case_dir / "receiver.json")]
            result = run_budgeted(command, outer.name + "-" + case["id"] + "-decode")
        evaluation = subprocess.run([sys.executable, "-B", "-m", "imagecalgacus.evaluate",
                        "--run", str(outer), "--references", str(outer / "references.json"), "--mode", "progress"], check=False)
        print("case %s process status %d" % (case["id"], result), flush=True)
        if result != 0 or evaluation.returncode != 0:
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--mode", choices=["preliminary", "ten"], default="ten")
    parser.add_argument("--cases", default="configs/v0_cases.json")
    parser.add_argument("--profile", default="configs/v0.json")
    parser.add_argument("--new-run")
    parser.add_argument("--pilot", help="successful preliminary run used for measured compute projection")
    args = parser.parse_args()
    if args.prepare:
        prepare()
        return 0
    if not args.new_run:
        parser.error("--new-run required")
    return execute(args)


if __name__ == "__main__":
    raise SystemExit(main())
