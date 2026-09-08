"""Small GPU preconditions, hashes and a serial two-hour accounting wrapper.
No payload/reference loading occurs here. Full child wall time is charged,
conservatively including imports/hash checks before allocation and process teardown.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
CUDA_SETTINGS = {
    "CUDA_LAUNCH_BLOCKING": "1",
    "GGML_CUDA_DISABLE_GRAPHS": "1",
    "GGML_CUDA_DISABLE_FUSION": "1",
    "GGML_CUDA_FORCE_CUBLAS_COMPUTE_32F": "1",
    "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
    "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
}
GPU_LIMIT_SECONDS = 7200


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def source_hash():
    return canonical_hash({str(p.relative_to(ROOT)): sha256_file(p)
                           for p in sorted((ROOT / "imagecalgacus").rglob("*.py"))})


def read_profile(path):
    profile = json.loads(Path(path).read_text())
    if profile.get("protocol") not in {"imagecalgacus-v0-fixed16", "imagecalgacus-v1-three-methods"} or profile.get("packet_bytes") != 292:
        raise ValueError("unsupported V0 protocol")
    allowed = {"protocol", "packet_bytes", "gpu_uuid", "text", "image", "completion_seed", "context_seed"}
    if profile["protocol"] == "imagecalgacus-v1-three-methods":
        allowed.add("coder")
        coder = profile.get("coder", {})
        if set(coder) != {"method","thresholds","calibration_sha256","precision","framing"}:
            raise ValueError("undeclared coder profile fields")
        if coder["method"] not in {"fixed","gated","arithmetic"} or coder["precision"] != 32 or coder["framing"] != "A1":
            raise ValueError("unsupported method/finite-stream profile")
        if set(coder["thresholds"]) != {"text","image"}:
            raise ValueError("separate frozen modality thresholds required")
        for item in coder["thresholds"].values():
            if set(item) != {"value","hex"} or float.fromhex(item["hex"]) != item["value"] or not 0 <= item["value"] < 100:
                raise ValueError("invalid frozen float64 threshold")
    if set(profile) != allowed:
        raise ValueError("undeclared protocol fields; payload sidecars are forbidden")
    schemas = {
        "text": {"interpreter", "model_path", "model_sha256", "n_gpu_layers", "logits_all", "n_batch", "n_ubatch", "n_ctx", "n_threads", "minimum_free_mib"},
        "image": {"interpreter", "model_path", "model_sha256", "nr_resnet", "nr_filters", "nr_logistic_mix", "minimum_free_mib"},
    }
    if any(set(profile[name]) != fields for name, fields in schemas.items()):
        raise ValueError("undeclared backend configuration fields")
    text = profile["text"]
    required = {"n_gpu_layers": -1, "logits_all": True, "n_batch": 1, "n_ubatch": 1, "n_ctx": 4096}
    if any(text.get(k) != v for k, v in required.items()):
        raise ValueError("profile is not approved full-GPU serial text inference")
    return profile


def configure_gpu(profile, modality):
    if not os.environ.get("IMAGECALGACUS_BUDGETED"):
        raise RuntimeError("launch model commands through python -m imagecalgacus.runtime to enforce the V0 allowance")
    selected = profile["gpu_uuid"]
    if not selected.startswith("GPU-"):
        raise ValueError("physical GPU UUID required")
    settings = {**CUDA_SETTINGS, "CUDA_VISIBLE_DEVICES": selected}
    for name, required in settings.items():
        value = os.environ.get(name)
        if value is not None and value != required:
            raise RuntimeError("conflicting GPU setting: " + name)
        os.environ[name] = required
    query = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=uuid,pci.bus_id,name,memory.total,memory.free,driver_version",
         "--format=csv,noheader,nounits"], text=True)
    matches = [line.split(", ") for line in query.strip().splitlines() if line.startswith(selected + ",")]
    if len(matches) != 1:
        raise RuntimeError("selected physical GPU unavailable")
    uuid, bus, name, total, free, driver = matches[0]
    if int(free) < profile[modality]["minimum_free_mib"]:
        raise RuntimeError("insufficient free VRAM; no CPU/partial-offload fallback")
    return {"uuid": uuid, "pci_bus_id": bus, "name": name, "total_mib": int(total),
            "free_mib_before": int(free), "driver": driver, "logical_device": 0,
            "effective_environment": settings, "pid": os.getpid()}


def allocation_snapshot():
    result = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid,gpu_uuid,used_gpu_memory",
         "--format=csv,noheader,nounits"], text=True)
    return [line.strip() for line in result.splitlines()
            if line.split(",")[0].strip() == str(os.getpid())]


def verified_model(profile, modality):
    item = profile[modality]
    path = Path(item["model_path"])
    actual = sha256_file(path)
    if actual != item["model_sha256"]:
        raise ValueError("model hash mismatch: " + modality)
    return path


def budget_root(stage):
    if stage not in {"v0", "v1"}:
        raise ValueError("unknown budget stage")
    return ROOT / (".runtime" if stage == "v0" else ".runtime/v1")


def budget_state(stage="v0"):
    path = budget_root(stage) / "gpu_budget.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    starts = {r["id"] for r in records if r["event"] == "started"}
    ends = {r["id"] for r in records if r["event"] == "finished"}
    if starts != ends:
        raise RuntimeError("unclosed GPU accounting record; stop and reconcile before more GPU work")
    return sum(r["elapsed_seconds"] for r in records if r["event"] == "finished"), records


def run_budgeted(command, label, stage="v0", max_seconds=None):
    directory = budget_root(stage)
    directory.mkdir(parents=True, exist_ok=True)
    with (ROOT / ".runtime/gpu.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        used, records = budget_state(stage)
        other_used, _ = budget_state("v0" if stage == "v1" else "v1")
        remaining = min(GPU_LIMIT_SECONDS - used, 40 * 3600 - used - other_used)
        if max_seconds is not None:
            remaining = min(remaining, float(max_seconds))
        if remaining <= 0:
            raise RuntimeError("authorized phase GPU allowance exhausted")
        ident = (stage + "-" if stage == "v1" else "") + "%03d-%s" % (len(records) // 2 + 1, label)
        logdir = directory / "logs" / ident
        logdir.mkdir(parents=True, exist_ok=False)
        ledger = directory / "gpu_budget.jsonl"
        def append(value):
            with ledger.open("a") as stream:
                stream.write(json.dumps(value) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        started = time.monotonic()
        append({"event": "started", "id": ident, "utc": datetime.now(timezone.utc).isoformat(),
                "command": command, "remaining_seconds": remaining, "budget_stage": stage})
        env = os.environ.copy()
        env["IMAGECALGACUS_BUDGETED"] = ident
        # Project-local missing text dependency only, not sibling source imports.
        env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / ".deps-text")])
        stop = threading.Event()
        samples = []
        def monitor(pid):
            while not stop.is_set():
                try:
                    output = subprocess.check_output(["nvidia-smi", "pmon", "-c", "1", "-s", "um"],
                                                     text=True, stderr=subprocess.STDOUT, timeout=4)
                    for line in output.splitlines():
                        fields = line.split()
                        if len(fields) >= 4 and fields[1] == str(pid):
                            samples.append({"elapsed": time.monotonic() - started, "pmon": line.strip()})
                except (subprocess.SubprocessError, OSError):
                    pass
                stop.wait(0.1)
        status, failure = -1, None
        proc = None
        with (logdir / "stdout.log").open("w") as stdout, (logdir / "stderr.log").open("w") as stderr:
            try:
                proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                        start_new_session=True)
                worker = threading.Thread(target=monitor, args=(proc.pid,), daemon=True)
                worker.start()
                status = proc.wait(timeout=max(0.1, remaining - (time.monotonic() - started)))
            except subprocess.TimeoutExpired:
                failure = "gpu_budget_timeout"
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                status = 124
            except BaseException as exc:
                failure = type(exc).__name__
                if proc is not None and proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                raise
            finally:
                elapsed = time.monotonic() - started
                stop.set()
                if proc is not None:
                    worker.join(timeout=5)
                result = {"event": "finished", "id": ident, "elapsed_seconds": elapsed,
                          "returncode": status, "failure": failure, "logs": str(logdir.relative_to(ROOT)),
                          "pid": proc.pid if proc else None, "pmon_samples": samples,
                          "cumulative_seconds": used + elapsed}
                append(result)
                print(json.dumps({**{k: v for k, v in result.items() if k != "pmon_samples"},
                                  "pmon_sample_count": len(samples)}), flush=True)
        return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--stage", choices=["v0", "v1"], default="v0")
    parser.add_argument("--max-seconds", type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.status:
        path = budget_root(args.stage) / "gpu_budget.jsonl"
        records = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        ended = {r["id"] for r in records if r["event"] == "finished"}
        active = [r for r in records if r["event"] == "started" and r["id"] not in ended]
        used = sum(r["elapsed_seconds"] for r in records if r["event"] == "finished")
        active_seconds = sum((datetime.now(timezone.utc) - datetime.fromisoformat(r["utc"])).total_seconds() for r in active)
        print(json.dumps({"stage": args.stage, "completed_seconds": used, "active_elapsed_seconds": active_seconds,
                          "other_stage_seconds": budget_state("v0" if args.stage == "v1" else "v1")[0],
                          "remaining_seconds": GPU_LIMIT_SECONDS - used - active_seconds,
                          "active_jobs": [r["id"] for r in active], "completed_jobs": len(ended)}))
        return
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not args.label:
        parser.error("--label and a command after -- are required")
    sys.exit(run_budgeted(command, args.label, stage=args.stage, max_seconds=args.max_seconds))


if __name__ == "__main__":
    main()
