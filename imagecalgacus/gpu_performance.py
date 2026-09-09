"""One development-only GPU benchmark; existing packet/evaluator/accounting helpers.

No encryption, qualification credits, held-out work or receiver diagnostic inputs.
The manifest is frozen before the first charged microcheck. Terminal files allow
receiver-only continuation, never automatic retries of an experimental failure.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time
import traceback

from .runtime import (ROOT, atomic_json, canonical_hash, sha256_file, source_hash,
                      read_profile, budget_state, phase_limit, run_budgeted,
                      reconcile_interrupted, apply_performance_allowance)
from .qualification import (read_json, verify_binding, sender_state,
                            validate_receiver_inbox, verify_gpu_report,
                            receiver_command)
from .evaluate import evaluate_case

STAGE = "gpu_performance"
MANIFEST = ROOT/"configs/gpu_performance.json"
REVIEW = ROOT/"artifacts/gpu_performance_review"
METHODS = ("fixed", "gated", "arithmetic")
MODES = ("reference", "cuda_graph")
JOB_LIMIT = 140


def history_files():
    files = []
    for base in (ROOT/"artifacts", ROOT/"runs", ROOT/".runtime"):
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink(): continue
            relative = path.relative_to(ROOT)
            if any(part.startswith("gpu-performance") or part.startswith("gpu_performance") for part in relative.parts): continue
            if relative.as_posix() == ".runtime/gpu.lock": continue
            files.append(path)
    return {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(files)}


def select_payloads(manifest):
    selected = []
    for lower, upper in ((32, 64), (65, 96), (97, 128)):
        available = [p for p in manifest["payloads"] if p["split"] == "development"
                     and p["direction"] == "text-to-image" and lower <= p["bytes"] <= upper]
        selected.append(min(available, key=lambda p: int(p["id"][1:])))
    return selected


def prepare(directory):
    apply_performance_allowance()
    directory = Path(directory).resolve()
    if (directory/"execution_identity.json").exists():
        identity = read_json(directory/"execution_identity.json")
        if identity["manifest_sha256"] != sha256_file(MANIFEST):
            raise ValueError("frozen benchmark manifest changed")
        return identity
    if MANIFEST.exists(): raise ValueError("manifest exists without this run identity; inspect before proceeding")
    sources = ROOT/"data/qualification_v1/manifest.json"
    payloads = select_payloads(read_json(sources))
    allocation = read_json(ROOT/"configs/v1_qualification.json")
    bindings = read_json(ROOT/"runs/v1-qualification-complete/packet_bindings.json")
    cases = []
    retained = {}
    for payload in payloads:
        original = next(c for c in allocation["cases"] if c["payload_id"] == payload["id"]
                        and c["context_id"] == "row1" and c["method"] == "fixed")
        binding = bindings[original["pair_id"]]
        verify_binding(binding, original)
        retained[original["pair_id"]] = binding
        cases.append({**original, "bytes": payload["bytes"], "packet_sha256": binding["packet_sha256"],
                      "historical_work_id": original["work_id"]})
    comparisons = []
    for repetition in range(3):
        for case in cases:
            methods = METHODS if repetition == 0 and case == cases[0] else ("fixed",)
            for method in methods:
                pair = case["payload_id"]+"-"+method+"-r"+str(repetition)
                order = list(MODES if len(comparisons) % 2 == 0 else reversed(MODES))
                # Explicit alternation for the same fixed pair across timing repeats.
                if repetition:
                    initial = next(x for x in comparisons if x["payload_id"] == case["payload_id"]
                                   and x["method"] == "fixed" and x["repetition"] == 0)
                    order = list(reversed(initial["mode_order"])) if repetition == 1 else initial["mode_order"].copy()
                comparisons.append({"id": pair, "payload_id": case["payload_id"], "method": method,
                                    "repetition": repetition, "mode_order": order})
    manifest = {"schema": "imagecalgacus-development-gpu-benchmark-1", "stage": STAGE,
        "starting_revision": subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "scientific_observations_added": 0, "heldout_execution": False,
        "selection_rule": "lowest numeric development text ID in each byte band 32-64,65-96,97-128; row1 only; no outcome selection",
        "source_manifest_sha256": sha256_file(sources), "cases": cases,
        "profiles": {m: {"path": "configs/v1_"+m+".json", "sha256": sha256_file(ROOT/("configs/v1_"+m+".json")),
                           "profile_id": canonical_hash(read_profile(ROOT/("configs/v1_"+m+".json")))} for m in METHODS},
        "candidates": [{"mode": "cuda_graph", "change": "capture/replay unchanged forward, persistent input/output and timing events; same normalization and synchronization",
                        "warmup_forwards": 3, "fallback": "none; retain reference on capture/equivalence/benefit failure"}],
        "probe": {"canvases": "row1 + zero suffix, row1 + uint8 ascending ramp suffix, row1 + descending ramp suffix",
                  "forwards_per_mode": 9, "order": list(MODES), "timeout_seconds": 180,
                  "full_output_comparison": "exact float32 bytes; all 100x32x32 outputs, no tolerance",
                  "minimum_forward_speedup_to_continue": 1.05},
        "comparisons": comparisons, "processes_per_comparison": 4, "job_timeout_seconds": JOB_LIMIT,
        "initial_conservative_bound_seconds": 180 + len(comparisons)*4*JOB_LIMIT,
        "initial_basis": "V2 PNG processes average about 89 seconds; 140-second job bound includes graph setup, hashing and teardown; 180-second short probe",
        "acceptance": ["same immutable packet/profile/context/seed", "fresh artifact-only receiver after sender exits",
            "2976 identical per-position eligible IDs, float64 coder probabilities and stable ordering (length-framed SHA256 streams)",
            "identical delivered PNG bytes, recovered source bytes and completion/authentication/outcome fields",
            "strict CUDA weights/input/output, eval/inference mode, positive process-specific GPU activity",
            "stop on unresolved discrepancy, infrastructure failure or inability to fit a complete comparison"],
        "timing_repeats": "at most two extra fixed repeats; only after all five initial comparisons pass and mean occupied-pair speedup >=1.05",
        "measurements": ["charged fresh encode/decode process latency", "payload bytes per charged encode+decode second",
            "phase encode/decode seconds", "cold model load", "execution setup", "CUDA-event forward interval",
            "peak allocated/reserved CUDA bytes", "process pmon samples"],
        "sampling_caveat": "nvidia-smi pmon -c1 -s um repeated by wrapper (~1s); PID matched; sampled utilization is not sustained utilization",
        "repetition_interpretation": "timing repeats of three development payloads, not new independent research observations",
        "precision_or_protocol_change": False, "created_utc": datetime.now(timezone.utc).isoformat()}
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    atomic_json(directory/"packet_bindings.json",retained)
    atomic_json(directory/"protected_history.json",history_files())
    atomic_json(MANIFEST,manifest)
    files = {str(p.relative_to(ROOT)):sha256_file(p) for p in sorted((ROOT/"imagecalgacus").rglob("*.py"))}
    for path in [MANIFEST, sources, ROOT/"configs/gpu_performance_authorization.json"] + [ROOT/v["path"] for v in manifest["profiles"].values()] + [ROOT/c["context"] for c in cases] + [ROOT/c["source"] for c in cases]:
        files[str(path.relative_to(ROOT))] = sha256_file(path)
    identity = {"source_revision":manifest["starting_revision"],"execution_source_hash":source_hash(),
        "manifest_sha256":sha256_file(MANIFEST),"files":files,
        "historical_usage_seconds":{s:budget_state(s)[0] for s in ("v0","v1","v2")},
        "new_stage_limit_seconds":phase_limit(STAGE),"created_utc":manifest["created_utc"],
        "protocol_changed":False,"reference_implementation_revision":"5178dab"}
    atomic_json(directory/"execution_identity.json",identity)
    print(json.dumps({"prepared":str(directory),"payloads":[p["payload_id"] for p in cases],
                      "comparisons":len(comparisons),"conservative_seconds":manifest["initial_conservative_bound_seconds"]}),flush=True)
    return identity


def probe(directory):
    import numpy as np
    from .image_backend import ImageBackend
    manifest = read_json(MANIFEST)
    profile = read_profile(ROOT/manifest["profiles"]["fixed"]["path"])
    row = np.frombuffer((ROOT/manifest["cases"][0]["context"]).read_bytes(),dtype=np.uint8).reshape(32,3)
    ramp = np.arange(3072,dtype=np.uint16).astype(np.uint8).reshape(32,32,3)
    canvases = [np.zeros_like(ramp),ramp,255-ramp]
    for canvas in canvases: canvas[0]=row
    reference=[]; result={"modes":{},"output_bytes_equal":True,"failure":None}
    model=None
    try:
        for mode in MODES:
            model=ImageBackend(profile,execution_mode=mode)
            times=[]; hashes=[]; equal=[]
            for index in range(9):
                started=time.monotonic()
                output=model.forward(canvases[index%3]).detach().cpu().numpy().copy()
                times.append(time.monotonic()-started)
                hashes.append(hashlib.sha256(output.tobytes()).hexdigest())
                if mode=="reference": reference.append(output)
                else: equal.append(output.tobytes()==reference[index].tobytes())
            model.close()
            result["modes"][mode]={"forward_seconds":times,"mean_forward_seconds":statistics.mean(times),
                "output_hashes":hashes,"exact_outputs":equal,"cold_load_seconds":model.load_seconds,
                "gpu_evidence":model.evidence}
            if equal and not all(equal):
                result["output_bytes_equal"]=False
                raise RuntimeError("exact full-output discrepancy; no tolerance or silent fallback")
            model=None
        result["forward_speedup"]=result["modes"]["reference"]["mean_forward_seconds"]/result["modes"]["cuda_graph"]["mean_forward_seconds"]
        result["continue"]=result["forward_speedup"]>=manifest["probe"]["minimum_forward_speedup_to_continue"]
    except Exception as exc:
        result["failure"]=type(exc).__name__+": "+str(exc);result["continue"]=False
        traceback.print_exc()
    finally:
        atomic_json(directory/"probe.json",result)
    print(json.dumps(result),flush=True)
    return 0 if result["continue"] else 2


def completed_jobs():
    _,rows=budget_state(STAGE)
    starts={r["id"]:r for r in rows if r["event"]=="started"}
    return [{**starts[r["id"]],**r} for r in rows if r["event"]=="finished"]


def job_for_report(report):
    pid=report["gpu_evidence"]["device"]["pid"]
    matched=[j for j in completed_jobs() if j.get("pid")==pid]
    # Also require the command's output location at collection time; no old stage PIDs.
    if len(matched)!=1: raise ValueError("ambiguous or missing benchmark process identity")
    job=matched[0]
    active=[s for s in job["pmon_samples"] if len(s["pmon"].split())>=4 and s["pmon"].split()[3].isdigit() and int(s["pmon"].split()[3])>0]
    if not active or job["returncode"]!=0 or job["failure"]:
        raise ValueError("GPU activity or successful occupied-process evidence missing")
    return job


def execute_case(directory,case,binding,mode):
    packet,key=verify_binding(binding,case)
    folder=directory/"cases"/case["id"]
    state=sender_state(folder,case,binding)
    profile=read_profile(ROOT/case["profile"])
    extra=["--image-execution",mode,"--image-distribution-audit"]
    if state=="unstarted":
        command=[profile["image"]["interpreter"],"-B","-m","imagecalgacus.sender","text-to-image",
            "--source",str(ROOT/case["source"]),"--profile",str(ROOT/case["profile"]),
            "--context",str(ROOT/case["context"]),"--prepared-packet",str(packet),"--key",str(key),
            "--new-run",str(folder)]+extra
        if run_budgeted(command,case["id"]+"-encode",stage=STAGE,max_seconds=JOB_LIMIT)!=0:
            raise RuntimeError("benchmark sender failed; preserve without retry")
        state=sender_state(folder,case,binding)
    if state=="receiver_pending":
        output=folder/"recovered.txt"
        if output.exists(): raise RuntimeError("interrupted receiver output exists; inspect, do not overwrite")
        command=receiver_command(case,folder/"inbox",output,folder/"receiver.json")+extra
        if run_budgeted(command,case["id"]+"-decode",stage=STAGE,max_seconds=JOB_LIMIT)!=0:
            raise RuntimeError("benchmark receiver failed; preserve without retry")
    elif state!="evaluate_pending": raise RuntimeError("invalid or interrupted carrier; no reroll")
    sender,receiver=read_json(folder/"sender.json"),read_json(folder/"receiver.json")
    validate_receiver_inbox(folder/"inbox",case,key)
    for report in (sender,receiver):
        verify_gpu_report(report,"image",profile)
        if report["gpu_evidence"].get("execution_mode")!=mode: raise ValueError("wrong execution mode")
    sj,rj=job_for_report(sender),job_for_report(receiver)
    if sj["pid"]==rj["pid"]: raise ValueError("receiver is not a fresh process")
    row=evaluate_case(case,folder,write=True)
    digest=sender["gpu_evidence"].get("distribution_digest")
    if not (row["evidence_valid"] and row["exact_recovery"] and row["carrier_complete"] and
            digest and digest["steps"]==2976 and digest==receiver["gpu_evidence"].get("distribution_digest")):
        raise ValueError("benchmark recovery or exact sender/receiver distribution mismatch")
    return {"case":case,"evaluation":row,"mode":mode,"folder":str(folder),
            "encode_job":sj["id"],"decode_job":rj["id"],
            "charged_encode_seconds":sj["elapsed_seconds"],"charged_decode_seconds":rj["elapsed_seconds"],
            "charged_pair_seconds":sj["elapsed_seconds"]+rj["elapsed_seconds"],
            "distribution_digest":digest}


def compare_records(records):
    reference=records["reference"];candidate=records["cuda_graph"]
    fields=("carrier_sha256","recovered_sha256","source_sha256","packet_complete","sender_carrier_complete",
            "receiver_packet_complete","authenticated","receiver_carrier_complete","exact_recovery",
            "packet_stop","completion_symbols","prepared_packet_sha256","failure_stage","failure_reason")
    checks={k:reference["evaluation"].get(k)==candidate["evaluation"].get(k) for k in fields}
    checks["exact_distribution_streams"]=reference["distribution_digest"]==candidate["distribution_digest"]
    return {"checks":checks,"equivalent":all(checks.values()),
        "charged_pair_speedup":reference["charged_pair_seconds"]/candidate["charged_pair_seconds"]}


def remaining():
    usage={s:budget_state(s)[0] for s in ("v0","v1","v2",STAGE)}
    return min(phase_limit(STAGE)-usage[STAGE],144000-sum(usage.values()))


def run(directory,prepare_only=False):
    directory=Path(directory).resolve()
    identity=prepare(directory)
    if prepare_only:return
    for name,digest in identity["files"].items():
        if sha256_file(ROOT/name)!=digest: raise ValueError("frozen benchmark execution file changed: "+name)
    reconcile_interrupted(STAGE)
    manifest=read_json(MANIFEST)
    if not (directory/"probe.json").exists():
        if remaining()<manifest["initial_conservative_bound_seconds"]: raise RuntimeError("full conservative benchmark bound exceeds remaining allowance")
        python=read_profile(ROOT/manifest["profiles"]["fixed"]["path"])["image"]["interpreter"]
        status=run_budgeted([python,"-B","-m","imagecalgacus.gpu_performance","--run",str(directory),"--probe"],
                            "cuda-graph-probe",stage=STAGE,max_seconds=180)
        if status not in (0,2): raise RuntimeError("probe infrastructure failure")
    micro=read_json(directory/"probe.json")
    if not micro.get("continue"): print("Probe did not qualify candidate; no full benchmark.",flush=True);return
    # Probe also must establish actual GPU activity before accepting its speed.
    for value in micro["modes"].values(): job_for_report(value)
    bindings=read_json(directory/"packet_bindings.json")
    by_payload={c["payload_id"]:c for c in manifest["cases"]}
    for comparison in manifest["comparisons"]:
        path=directory/"comparisons"/(comparison["id"]+".json")
        if path.exists():
            if not read_json(path)["equivalence"]["equivalent"]: raise RuntimeError("retained equivalence failure")
            continue
        if comparison["repetition"]:
            initial=[read_json(p) for p in (directory/"comparisons").glob("*-r0.json")]
            if len(initial)!=5 or not all(x["equivalence"]["equivalent"] for x in initial):
                raise RuntimeError("initial correctness allocation incomplete")
            fixed=[x for x in initial if x["comparison"]["method"]=="fixed"]
            speed=sum(x["records"]["reference"]["charged_pair_seconds"] for x in fixed)/sum(x["records"]["cuda_graph"]["charged_pair_seconds"] for x in fixed)
            if speed<1.05: print("No clear end-to-end benefit; timing repetitions not launched.",flush=True);break
        if remaining()<4*JOB_LIMIT: raise RuntimeError("complete comparison cannot fit conservative remaining allowance")
        records={}
        base=by_payload[comparison["payload_id"]];method=comparison["method"]
        profile=manifest["profiles"][method]
        for mode in comparison["mode_order"]:
            case={**base,"id":comparison["id"]+"-"+mode,"method":method,"profile":profile["path"],
                  "profile_id":profile["profile_id"],"source_hash":identity["execution_source_hash"]}
            records[mode]=execute_case(directory,case,bindings[case["pair_id"]],mode)
        equivalence=compare_records(records)
        atomic_json(path,{"comparison":comparison,"records":records,"equivalence":equivalence})
        print(json.dumps({"comparison":comparison["id"],**equivalence,"remaining_seconds":remaining()}),flush=True)
        if not equivalence["equivalent"]: raise ValueError("unresolved exact equivalence discrepancy; stop")
    print(json.dumps({"benchmark_finished":True,"remaining_seconds":remaining()}),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",default="runs/gpu-performance-001")
    parser.add_argument("--prepare-only",action="store_true")
    parser.add_argument("--probe",action="store_true")
    args=parser.parse_args()
    if args.probe: raise SystemExit(probe(Path(args.run)))
    run(args.run,args.prepare_only)


if __name__=="__main__": main()
