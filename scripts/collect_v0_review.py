"""Build the small V0 review packet from actual execution, with an explicit allowlist.
No inference, key copying, model copying or external writes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from imagecalgacus.runtime import json_write, canonical_hash, sha256_file, source_hash


def copy_allowed(source, destination):
    source, destination = Path(source), Path(destination)
    if source.name.endswith(".key") or source.suffix in {".pth", ".gguf", ".so"}:
        raise ValueError("forbidden review file")
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def compact_gpu(records):
    jobs = []
    for record in records:
        if record["event"] != "finished":
            continue
        samples = record.get("pmon_samples", [])
        parsed = []
        for sample in samples:
            fields = sample["pmon"].split()
            if len(fields) > 3 and fields[3].isdigit():
                parsed.append((int(fields[3]), sample["pmon"]))
        peak = max(parsed, default=(0, None))
        start = next(r for r in records if r["event"] == "started" and r["id"] == record["id"])
        jobs.append({"id": record["id"], "pid": record["pid"], "utc": start["utc"],
                     "command": start["command"], "returncode": record["returncode"],
                     "charged_seconds": record["elapsed_seconds"],
                     "pmon_samples": len(samples), "max_process_sm_percent": peak[0],
                     "peak_activity_line": peak[1], "logs_retained_locally": record["logs"]})
    return jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--preliminary", type=Path, required=True)
    args = parser.parse_args()
    review = ROOT / "artifacts/v0_review"
    review.mkdir(parents=True, exist_ok=True)
    all_results = []
    # Include every extant encoding run, not only the requested final one.
    candidates = sorted((ROOT / "runs").glob("*/references.json"))
    for references in candidates:
        run = references.parent
        manifest = json.loads(references.read_text())
        if not (run / "results.jsonl").exists():
            continue
        rows = [json.loads(line) for line in (run / "results.jsonl").read_text().splitlines()]
        for row in rows:
            case_dir = run / row["case"]
            public = review / run.name / row["case"]
            names = ["source.png", "source.txt", "recovered.gray", "recovered.png", "recovered.txt",
                     "sender.json", "receiver.json", "evaluation.json", "failed-prefix.txt", "failed-prefix.npy"]
            for name in names:
                copy_allowed(case_dir / name, public / name)
            for name in ["carrier.txt", "carrier.png"]:
                copy_allowed(case_dir / "inbox" / name, public / name)
            row = dict(row, run=run.name, phase="ten" if run.resolve() == args.run.resolve() else ("earlier_ten_attempt" if len(manifest["cases"]) == 10 else "preliminary"))
            for field in ["source", "carrier", "recovered", "sender_gpu_evidence", "receiver_gpu_evidence"]:
                original = row.get(field)
                if original:
                    row[field] = str((public / Path(original).name).relative_to(review))
            all_results.append(row)
        copy_allowed(run / "compute_projection.json", review / run.name / "compute_projection.json")
        copy_allowed(run / "implementation.json", review / run.name / "implementation.json")

    preflights = {}
    for modality in ["text", "image"]:
        path = ROOT / (".runtime/%s-preflight-1/result.json" % modality)
        if path.exists():
            preflights[modality] = json.loads(path.read_text())
            copy_allowed(path, review / "preflight" / (modality + ".json"))
    text_log = ROOT / ".runtime/logs/001-text-preflight-1/stderr.log"
    if text_log.exists():
        patterns = ["offload", "buffer size", "n_ctx", "n_batch", "n_ubatch", "CUDA devices", "Device 0"]
        excerpt = [line for line in text_log.read_text().splitlines()
                   if any(pattern in line for pattern in patterns)]
        (review / "preflight/text_initialization_excerpt.txt").write_text(
            "Source: .runtime/logs/001-text-preflight-1/stderr.log\n"
            + "Full log SHA-256: " + sha256_file(text_log) + "\n\n" + "\n".join(excerpt) + "\n")

    copy_allowed(ROOT / ".runtime/image-preflight-1/ordinary.png", review / "preflight/ordinary.png")
    copy_allowed(ROOT / "configs/v0.json", review / "profile.json")
    copy_allowed(ROOT / "configs/v0_cases.json", review / "fixtures/cases.json")
    copy_allowed(ROOT / "models/pixelcnn_pp_cifar10.provenance.json", review / "preflight/image_acquisition.json")

    profile = json.loads((ROOT / "configs/v0.json").read_text())
    environment = {}
    for modality in ["text", "image"]:
        packages = ["numpy", "cryptography", "Pillow"] + (
            ["llama-cpp-python", "nvidia-cuda-runtime-cu12", "nvidia-cublas-cu12"]
            if modality == "text" else ["torch"])
        code = ("import importlib.metadata as m, json, sys; "
                "print(json.dumps({'python':sys.version, 'executable':sys.executable, "
                "'packages':{p:m.version(p) for p in " + repr(packages) + "}}))")
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT / ".deps-text")]))
        environment[modality] = json.loads(subprocess.check_output(
            [profile[modality]["interpreter"], "-B", "-c", code], cwd=ROOT, env=env, text=True))
    json_write(review / "environment.json", environment)

    records = [json.loads(line) for line in (ROOT / ".runtime/gpu_budget.jsonl").read_text().splitlines()]
    jobs = compact_gpu(records)
    if len(jobs) * 2 != len(records):
        raise RuntimeError("model job still active or accounting incomplete")
    json_write(review / "gpu_evidence.json", {"accounting": "complete child process wall time, conservatively including imports/hash/load/teardown",
               "ceiling_seconds": 7200, "used_seconds": sum(j["charged_seconds"] for j in jobs), "jobs": jobs})
    with (review / "results.jsonl").open("w") as stream:
        for row in all_results:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=ROOT, text=True, capture_output=True)
    json_write(review / "focused_tests.json", {"command": [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
               "returncode": tests.returncode, "stdout": tests.stdout, "stderr": tests.stderr})
    json_write(review / "source_manifest.json", {"package_source_hash": source_hash(),
               "project_files": {name: sha256_file(ROOT / name) for name in ["pyproject.toml", ".gitignore", "README.md", "THIRD_PARTY.md", "LICENSE"]},
               "files": {str(p.relative_to(ROOT)): sha256_file(p)
                         for folder in ["imagecalgacus", "configs", "tests", "scripts"]
                         for p in sorted((ROOT / folder).rglob("*"))
                         if p.is_file() and "__pycache__" not in p.parts}})
    ten = [r for r in all_results if r["phase"] == "ten"]
    input_checks = []
    for row in ten:
        inbox = args.run / row["case"] / "inbox"
        text = row["direction"] == "image-to-text"
        carrier_name = "carrier.txt" if text else "carrier.png"
        context_name = "prompt.txt" if text else "row.rgb"
        names = sorted(p.name for p in inbox.iterdir())
        receiver = json.loads((args.run / row["case"] / "receiver.json").read_text())
        passed = set(names) == {carrier_name, context_name, "profile.json", "run.key"}
        passed &= (inbox / context_name).read_bytes() == (review / "contexts" / context_name).read_bytes()
        passed &= canonical_hash(json.loads((inbox / "profile.json").read_text())) == row["profile_id"]
        passed &= set(receiver["input_files"]) == set(names)
        passed &= receiver["input_roles"] == ["carrier", "profile", "context", "key"]
        input_checks.append({"case": row["case"], "files": names, "passed": bool(passed)})
    boundary_passed = len(input_checks) == 10 and all(r["passed"] for r in input_checks)
    json_write(review / "receiver_input_checks.json", {
        "claim": "four-file data-flow separation, not an operating-system sandbox",
        "passed": boundary_passed, "cases": input_checks})
    expected_source_hash = json.loads((args.run / "implementation.json").read_text())["source_hash"]
    frozen = source_hash() == expected_source_hash and all(
        json.loads((args.run / row["case"] / "sender.json").read_text())["source_hash"] == expected_source_hash for row in ten)
    acceptance = frozen and len(ten) == 10 and all(r["exact_recovery"] and r["carrier_complete"] and r["sender_profile_matches_receiver"] for r in ten)
    acceptance &= boundary_passed
    acceptance &= tests.returncode == 0 and all(p.get("passed") for p in preflights.values()) and len(preflights) == 2
    acceptance &= all(j["returncode"] == 0 and j["max_process_sm_percent"] > 0 for j in jobs)
    used = sum(j["charged_seconds"] for j in jobs)
    acceptance &= used <= 7200
    json_write(review / "acceptance.json", {"v0_acceptance": bool(acceptance), "application_source_frozen": frozen, "receiver_input_checks_passed": boundary_passed, "ten_attempted": len(ten),
               "ten_exact": sum(r["exact_recovery"] for r in ten), "all_stego_attempts": len(all_results),
               "all_stego_failures": sum(not (r["exact_recovery"] and r["carrier_complete"]) for r in all_results),
               "model_jobs": len(jobs), "charged_seconds": used, "budget_remaining_seconds": 7200 - used})
    # A final byte-level key exclusion check is local only; key bytes are never logged.
    keys = [p.read_bytes() for p in (ROOT / "runs").rglob("*.key")]
    for file in review.rglob("*"):
        if file.is_file():
            data = file.read_bytes()
            if file.suffix == ".key" or any(key and key in data for key in keys):
                raise ValueError("secret material detected in review packet")
    print(json.dumps({"review": str(review), "acceptance": bool(acceptance), "used_seconds": used,
                      "files": sum(p.is_file() for p in review.rglob("*"))}))


if __name__ == "__main__":
    main()
