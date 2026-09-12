"""Small GPU preconditions, hashes and a serial stage-specific accounting wrapper.
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
DEFAULT_PHASE_LIMITS = {"v0": 7200, "v1": 7200, "v2": 0, "gpu_performance": 0, "png_context_detection": 0, "cover_rank_v1": 0}
V1_QUALIFICATION_AUTHORIZATION = {
    "authorization_id": "user-v1-qualification-additional-12h",
    "stage": "v1", "previous_seconds": 7200, "additional_seconds": 43200,
    "absolute_seconds": 50400, "v0_seconds": 7200, "whole_project_seconds": 144000,
    "scope": "complete frozen V1 qualification and 20 development PNG lossless replays; no V2 or held-out carriers",
    "reviewed_revision": "b5f2d1e3b9e901e5dfe6a181b6ca5d95dc35ac4b",
}


V2_PROSPECTIVE_AUTHORIZATION = {
    "authorization_id": "user-v2-bounded-prospective-15h",
    "stage": "v2", "absolute_seconds": 54000, "whole_project_seconds": 144000,
    "scope": "120 frozen held-out stego units, up to 40 shared controls and initial CPU analysis; no extra matrix or lossless replay allocation",
    "reviewed_revision": "29d2ca2ff7e0cdf6f3a6c000d1ad7948ac8a7bc3",
    "unused_other_phase_allowances_transfer": False,
}


GPU_PERFORMANCE_AUTHORIZATION = {
    "authorization_id": "user-post-v2-gpu-performance-2h",
    "stage": "gpu_performance", "absolute_seconds": 7200,
    "whole_project_seconds": 144000,
    "scope": "bounded matched development-only image GPU execution benchmark; no V2 reruns or new scientific allocation",
    "reviewed_revision": "5178dab",
    "unused_other_phase_allowances_transfer": False,
}



PNG_CONTEXT_AUTHORIZATION = {
    "authorization_id": "user-png-context-detection-2h",
    "stage": "png_context_detection", "absolute_seconds": 7200,
    "whole_project_seconds": 144000,
    "scope": "three predetermined development score checks and row2 scoring of the 80 existing V2 PNG artifacts; no carrier generation",
    "starting_revision": "cdff18c30a0492f242921d72fb369ef78a6a7f38",
    "unused_other_phase_allowances_transfer": False,
}


COVER_RANK_AUTHORIZATION = {
    "authorization_id": "user-cover-rank-v1-2h",
    "stage": "cover_rank_v1", "absolute_seconds": 7200,
    "whole_project_seconds": 144000,
    "scope": "six development and twenty held-out photographs, two paired arms, focused verification; no other matrix",
    "starting_revision": "e39c14cc858bb67f870916692384d0e97502aa63",
    "unused_other_phase_allowances_transfer": False,
}


def apply_cover_rank_allowance(path=None):
    path = Path(path) if path is not None else ROOT/"configs/cover_rank_authorization.json"
    if path.exists():
        if json.loads(path.read_text()) != COVER_RANK_AUTHORIZATION:
            raise ValueError("conflicting cover-rank authorization")
        return False
    atomic_json(path, COVER_RANK_AUTHORIZATION)
    return True


def apply_png_context_allowance(path=None):
    """A separate absolute cap, never an additive allowance on resumption."""
    path = Path(path) if path is not None else ROOT/"configs/png_context_authorization.json"
    if path.exists():
        if json.loads(path.read_text()) != PNG_CONTEXT_AUTHORIZATION:
            raise ValueError("conflicting PNG context authorization")
        return False
    atomic_json(path, PNG_CONTEXT_AUTHORIZATION)
    return True


def apply_performance_allowance(path=None):
    """Separate absolute cap; repeating the authorization never adds time."""
    path = Path(path) if path is not None else ROOT/"configs/gpu_performance_authorization.json"
    if path.exists():
        if json.loads(path.read_text()) != GPU_PERFORMANCE_AUTHORIZATION:
            raise ValueError("conflicting GPU performance authorization")
        return False
    atomic_json(path, GPU_PERFORMANCE_AUTHORIZATION)
    return True


def apply_v2_allowance(path=None):
    """One absolute V2 authorization; old ledgers/allowances are untouched."""
    path = Path(path) if path is not None else ROOT/"configs/v2_gpu_authorization.json"
    if path.exists():
        if json.loads(path.read_text()) != V2_PROSPECTIVE_AUTHORIZATION:
            raise ValueError("conflicting V2 authorization; do not add another allowance")
        return False
    atomic_json(path,V2_PROSPECTIVE_AUTHORIZATION)
    return True


def apply_v1_allowance(path=None):
    """Idempotent absolute authorization, never an increment on a current balance."""
    path = Path(path) if path is not None else ROOT/"configs/v1_gpu_authorization.json"
    if path.exists():
        if json.loads(path.read_text()) != V1_QUALIFICATION_AUTHORIZATION:
            raise ValueError("conflicting phase authorization; do not add the extension again")
        return False
    atomic_json(path, V1_QUALIFICATION_AUTHORIZATION, replace=False)
    return True


def phase_limit(stage, authorization_path=None):
    if stage not in DEFAULT_PHASE_LIMITS:
        raise ValueError("unknown budget stage")
    if stage == "cover_rank_v1":
        path = Path(authorization_path) if authorization_path is not None else ROOT/"configs/cover_rank_authorization.json"
        if not path.exists(): return 0
        if json.loads(path.read_text()) != COVER_RANK_AUTHORIZATION:
            raise ValueError("invalid cover-rank authorization")
        return COVER_RANK_AUTHORIZATION["absolute_seconds"]
    if stage == "png_context_detection":
        path = Path(authorization_path) if authorization_path is not None else ROOT/"configs/png_context_authorization.json"
        if not path.exists(): return 0
        if json.loads(path.read_text()) != PNG_CONTEXT_AUTHORIZATION:
            raise ValueError("invalid or altered PNG context authorization")
        return PNG_CONTEXT_AUTHORIZATION["absolute_seconds"]
    if stage == "gpu_performance":
        path = Path(authorization_path) if authorization_path is not None else ROOT/"configs/gpu_performance_authorization.json"
        if not path.exists(): return 0
        if json.loads(path.read_text()) != GPU_PERFORMANCE_AUTHORIZATION:
            raise ValueError("invalid or altered GPU performance authorization")
        return GPU_PERFORMANCE_AUTHORIZATION["absolute_seconds"]
    if stage == "v2":
        path = Path(authorization_path) if authorization_path is not None else ROOT/"configs/v2_gpu_authorization.json"
        if not path.exists(): return 0
        if json.loads(path.read_text()) != V2_PROSPECTIVE_AUTHORIZATION:
            raise ValueError("invalid or altered V2 allowance authorization")
        return V2_PROSPECTIVE_AUTHORIZATION["absolute_seconds"]
    path = Path(authorization_path) if authorization_path is not None else ROOT/"configs/v1_gpu_authorization.json"
    if path.exists():
        if json.loads(path.read_text()) != V1_QUALIFICATION_AUTHORIZATION:
            raise ValueError("invalid or altered V1 allowance authorization")
        if stage == "v1":
            return V1_QUALIFICATION_AUTHORIZATION["absolute_seconds"]
    return DEFAULT_PHASE_LIMITS[stage]


def atomic_json(path, value, replace=False):
    """Fsynced JSON + atomic rename/link; immutable terminal records never overwrite."""
    import tempfile
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    fd, temporary = tempfile.mkstemp(prefix="."+path.name+".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
        folder_fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(folder_fd)
        finally: os.close(folder_fd)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)



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
        if "development_text_filter" in profile:
            allowed.add("development_text_filter")
            if profile["development_text_filter"] not in {"sequence", "static"} or profile.get("coder", {}).get("method") != "fixed":
                raise ValueError("development text-filter arms require fixed coding")
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
        raise RuntimeError("launch model commands through python -m imagecalgacus.runtime to enforce the authorized stage allowance")
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
    if stage not in DEFAULT_PHASE_LIMITS:
        raise ValueError("unknown budget stage")
    return ROOT / (".runtime" if stage == "v0" else ".runtime/"+stage)


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
        other_used = sum(budget_state(other)[0] for other in DEFAULT_PHASE_LIMITS if other != stage)
        remaining = min(phase_limit(stage) - used, 40 * 3600 - used - other_used)
        if max_seconds is not None:
            remaining = min(remaining, float(max_seconds))
        if remaining <= 0:
            raise RuntimeError("authorized phase GPU allowance exhausted")
        ident = (stage + "-" if stage != "v0" else "") + "%03d-%s" % (len(records) // 2 + 1, label)
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
                "command": command, "remaining_seconds": remaining, "budget_stage": stage,
                "wrapper_pid": os.getpid(), "phase_limit_seconds": phase_limit(stage)})
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
        proc = None; worker = None
        with (logdir / "stdout.log").open("w") as stdout, (logdir / "stderr.log").open("w") as stderr:
            try:
                proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                        start_new_session=True)
                atomic_json(logdir/"process.json", {"pid":proc.pid,"start_ticks":Path("/proc/%d/stat"%proc.pid).read_text().split()[21]})
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
                if worker is not None:
                    worker.join(timeout=5)
                result = {"event": "finished", "id": ident, "elapsed_seconds": elapsed,
                          "returncode": status, "failure": failure, "logs": str(logdir.relative_to(ROOT)),
                          "pid": proc.pid if proc else None, "pmon_samples": samples,
                          "cumulative_seconds": used + elapsed}
                append(result)
                print(json.dumps({**{k: v for k, v in result.items() if k != "pmon_samples"},
                                  "pmon_sample_count": len(samples)}), flush=True)
        return status


def reconcile_interrupted(stage="v1"):
    """Only with the GPU lock free and no surviving budget-tagged child.
    Missing terminal timing is charged the wall-clock upper bound, never zero.
    """
    directory=budget_root(stage); ledger=directory/"gpu_budget.jsonl"
    (ROOT/".runtime").mkdir(exist_ok=True)
    with (ROOT/".runtime/gpu.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        records=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        ended={r["id"] for r in records if r["event"]=="finished"}
        active=[r for r in records if r["event"]=="started" and r["id"] not in ended]
        used=sum(r["elapsed_seconds"] for r in records if r["event"]=="finished")
        reconciled=[]
        for start in active:

            marker=("IMAGECALGACUS_BUDGETED="+start["id"]).encode()
            sidecar=directory/"logs"/start["id"]/"process.json"
            if sidecar.exists():
                child=json.loads(sidecar.read_text())
                stat=Path("/proc")/str(child["pid"])/"stat"
                if stat.exists() and stat.read_text().split()[21]==child["start_ticks"]:
                    raise RuntimeError("interrupted recorded child still alive; no new jobs")

            for process in Path("/proc").iterdir():
                if not process.name.isdigit(): continue
                try:
                    if process.stat().st_uid!=os.getuid(): continue
                    environment=(process/"environ").read_bytes()
                except (OSError,PermissionError): continue
                if marker in environment.split(b"\0"):
                    raise RuntimeError("interrupted model process still alive; preserve and wait: "+process.name)
            elapsed=max(0.,(datetime.now(timezone.utc)-datetime.fromisoformat(start["utc"])).total_seconds())
            used+=elapsed
            row={"event":"finished","id":start["id"],"elapsed_seconds":elapsed,"returncode":-1,
                 "failure":"interrupted_wall_clock_upper_bound","pid":None,"pmon_samples":[],
                 "logs":str((directory/"logs"/start["id"]).relative_to(ROOT)),
                 "cumulative_seconds":used,"timing_is_conservative_upper_bound":True}
            with ledger.open("a") as stream:
                stream.write(json.dumps(row)+"\n"); stream.flush(); os.fsync(stream.fileno())
            reconciled.append(row)
        return reconciled


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--stage", choices=list(DEFAULT_PHASE_LIMITS), default="v0")
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
                          "other_stage_seconds": sum(budget_state(s)[0] for s in DEFAULT_PHASE_LIMITS if s != args.stage),
                          "phase_limit_seconds": phase_limit(args.stage),
                          "remaining_seconds": phase_limit(args.stage) - used - active_seconds,
                          "active_jobs": [r["id"] for r in active], "completed_jobs": len(ended)}))
        return
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not args.label:
        parser.error("--label and a command after -- are required")
    sys.exit(run_budgeted(command, args.label, stage=args.stage, max_seconds=args.max_seconds))


if __name__ == "__main__":
    main()
