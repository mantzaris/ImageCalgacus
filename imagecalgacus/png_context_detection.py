"""Frozen, serial saved-PNG observer extension; reuses the occupied-job wrapper."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from .runtime import (ROOT, DEFAULT_PHASE_LIMITS, atomic_json, canonical_hash,
    sha256_file, source_hash, read_profile, budget_state, phase_limit, run_budgeted,
    reconcile_interrupted, apply_png_context_allowance)
from .qualification import verify_gpu_report

STAGE = "png_context_detection"
REVIEW = ROOT/"artifacts/png_context_detection_review"
MANIFEST = REVIEW/"manifest.json"
RUN = ROOT/"runs/png-context-detection-001"
V2 = ROOT/"artifacts/v2_review"
PROFILE = ROOT/"configs/v1_fixed.json"
METHODS = ("fixed", "gated", "arithmetic")
SCORES = ("surprisal_bits_mean", "log_rank_mean")


def read(path):
    return json.loads(Path(path).read_text())


def remaining():
    usage = {s:budget_state(s)[0] for s in DEFAULT_PHASE_LIMITS}
    return min(phase_limit(STAGE)-usage[STAGE], 144000-sum(usage.values()))


def protected_files():
    # Old public evidence, private keys/packets/reports, and all historical ledgers.
    files = []
    for folder in (ROOT/"artifacts", ROOT/"runs"):
        files.extend(p for p in folder.rglob("*") if p.is_file()
                     and REVIEW not in p.parents and RUN not in p.parents)
    files.extend(p for p in (ROOT/".runtime").rglob("*") if p.is_file()
                 and STAGE not in p.parts and p.name != "gpu.lock")
    files.extend(p for folder in ("data/qualification_v1","configs","notes","plan")
                 for p in (ROOT/folder).rglob("*") if p.is_file()
                 and not p.name.startswith("png_context"))
    return {str(p.relative_to(ROOT)):sha256_file(p) for p in sorted(set(files))}


def build_manifest():
    accepted = read(V2/"manifest.json")
    groups = [g for g in accepted["groups"] if g["direction"]=="text-to-image"]
    rows = {r["case"]:r for r in map(json.loads,(V2/"results.jsonl").read_text().splitlines())}
    links = {r["case"]:r for r in read(V2/"control_links.json")}
    contexts = {c["id"]:c for c in read(ROOT/"data/qualification_v1/manifest.json")["contexts"]
                if c["modality"]=="image"}
    for c in contexts.values():
        c["path"] = "data/qualification_v1/"+c["path"]
        if sha256_file(ROOT/c["path"]) != c["sha256"] or (ROOT/c["path"]).stat().st_size != 96:
            raise ValueError("frozen conditioning row changed")
    profile = read_profile(PROFILE)
    items = []
    for group in groups:
        group_links = []
        for method in METHODS:
            r = rows[group["id"]+"-"+method]; link = links[r["case"]]
            if not r["evidence_valid"] or r["channels"]!=2976 or r["context_id"]!="row1":
                raise ValueError("incompatible accepted PNG evidence")
            original_profile = read(V2/"cases"/r["case"]/"profile.json")
            if original_profile["image"]!=profile["image"] or original_profile["gpu_uuid"]!=profile["gpu_uuid"]:
                raise ValueError("observer model settings differ from accepted image model")
            items.append(dict(artifact_id=r["case"], kind="stego", method=method,
                payload_group=group["id"], stratum=group["stratum"], original_work_id=r["work_id"],
                control_id=link["trace_id"], carrier="artifacts/v2_review/"+r["carrier"],
                carrier_sha256=r["carrier_sha256"], correct_scores=r["diagnostics"]["whole"],
                original_profile_id=r["profile_id"], original_exact_recovery=r["exact_recovery"]))
            group_links.append(link)
        first = group_links[0]
        if not all(l["available"] and l["symbols"]==2976 and
                   all(l[k]==first[k] for k in ("trace_id","matched_artifact","matched_sha256","scores"))
                   for l in group_links):
            raise ValueError("missing or inconsistent shared control")
        items.append(dict(artifact_id=first["trace_id"], kind="control", method=None,
            payload_group=group["id"], stratum=group["stratum"], original_work_id=first["trace_work_id"],
            control_id=first["trace_id"], carrier="artifacts/v2_review/"+first["matched_artifact"],
            carrier_sha256=first["matched_sha256"], correct_scores=first["scores"],
            original_profile_id=None, original_exact_recovery=None))
    if len(groups)!=20 or len(items)!=80 or len({r["carrier_sha256"] for r in items})!=80:
        raise ValueError("expected exactly 80 unique PNGs in 20 groups")
    if len({r["control_id"] for r in items})!=20:
        raise ValueError("control links are not 20 independent traces")
    for i,item in enumerate(items):
        if sha256_file(ROOT/item["carrier"])!=item["carrier_sha256"]:
            raise ValueError("accepted carrier changed")
        if item["correct_scores"]["positions"]!=2976:
            raise ValueError("whole-carrier correct-context score required")
        item.update(observer_id="score-%03d"%(i+1), observer_context="row2")
    development = []
    for case in ("T1-fixed-r0-reference", "T1-arithmetic-r0-reference"):
        folder = ROOT/"artifacts/gpu_performance_review/cases"/case
        report = read(folder/"sender.json")
        development.append(dict(artifact_id=case, carrier=str((folder/"carrier.png").relative_to(ROOT)),
            retained_report=str((folder/"sender.json").relative_to(ROOT)),
            correct_scores=report["diagnostics"]["whole"],
            distribution_digest=report["gpu_evidence"]["distribution_digest"]))
    folder = ROOT/"artifacts/v1_qualification_review/traces/control-image-5202"
    report = read(folder/"result.json")
    if report["context_sha256"]!=contexts["row1"]["sha256"]:
        raise ValueError("development ordinary context mismatch")
    development.append(dict(artifact_id=folder.name, carrier=str((folder/"carrier.png").relative_to(ROOT)),
        retained_report=str((folder/"result.json").relative_to(ROOT)),
        correct_scores=report["diagnostics"]["whole"], distribution_digest=None))
    for i,item in enumerate(development):
        item.update(observer_id="validation-%02d"%(i+1), observer_context="row1",
            carrier_sha256=sha256_file(ROOT/item["carrier"]),
            retained_report_sha256=sha256_file(ROOT/item["retained_report"]))
    return dict(schema="png-context-extension-v1", starting_revision=subprocess.check_output(
        ["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(), source_hash=source_hash(),
        profile=str(PROFILE.relative_to(ROOT)), profile_sha256=sha256_file(PROFILE),
        profile_id=canonical_hash(profile), model_sha256=profile["image"]["model_sha256"],
        contexts=contexts, groups=groups, artifacts=items, development_validation=development,
        order_rule="V2 frozen PNG group order; fixed, gated, arithmetic, then its one control; no outcome selection",
        development_rule="first GPU benchmark payload fixed/arithmetic reference carriers, then first row1 ordinary control retained in qualification review",
        observer_inputs=["saved RGB8 PNG","common fixed profile (coder unused)","specified 96-byte row"],
        observer_exclusions=["labels","group/control associations","keys","sources","packets","sender caches"],
        scoring=dict(primary=SCORES[0],secondary=SCORES[1],positions=2976,
            orientation="higher means stego",precision="unchanged float32 network / float64 conditional probabilities",
            definition="V2 Trace.whole sequential means over every delivered raster RGB channel; row excluded",
            invalid="no extra clipping; zero/invalid observed probability is an explicit unscorable outcome; partial means excluded",
            execution_mode="cuda_graph"),
        analysis=dict(bootstrap_replicates=2000,seed=2026090902,
            seed_reason="accepted V2 seed 2026090901 plus PNG direction offset 1",
            resampling="accepted PCG64 length-stratified payload-group draws; identical draws across both contexts, all methods and shared controls",
            difference="mismatched minus correct; paired percentile 95% intervals",
            missing="retain failures; method/score paired complete-group AUCs and explicit exclusions; accepted full row1 result also retained",
            duplicates="accepted lowest frozen group owns an identical control hash; verified none in this allocation",
            score_direction="never reverse; no threshold selection; exploratory, one alternate row"),
        budget=dict(stage=STAGE,absolute_seconds=7200,whole_project_seconds=144000,
            per_job_hard_seconds=60,forecast="remaining jobs * max(30, 1.5 * maximum measured development charged seconds); one 50% time margin, no second reserve",
            stop="no full 80-artifact launch unless conservative batch projection fits both caps; pause on infrastructure, identity or validation discrepancy"),
        accepted_sources={str(p.relative_to(ROOT)):sha256_file(p) for p in
            (V2/"manifest.json",V2/"results.jsonl",V2/"control_links.json",V2/"analysis.json",
             ROOT/"data/qualification_v1/manifest.json")})


def prepare():
    apply_png_context_allowance()
    if MANIFEST.exists():
        verify_freeze()
        return
    RUN.mkdir(parents=True,exist_ok=True)
    manifest = build_manifest()
    protected = protected_files()
    atomic_json(RUN/"protected_history.json", protected)
    atomic_json(MANIFEST, manifest)
    files = [*sorted((ROOT/"imagecalgacus").rglob("*.py")),
             ROOT/"scripts/analyze_png_context_detection.py",
             ROOT/"scripts/analyze_v2.py", ROOT/"tests/test_png_observer.py",
             PROFILE,ROOT/"configs/png_context_authorization.json",MANIFEST]
    atomic_json(REVIEW/"execution_freeze.json",dict(starting_revision=manifest["starting_revision"],
        package_source_hash=source_hash(),files={str(p.relative_to(ROOT)):sha256_file(p) for p in files},
        starting_usage={s:budget_state(s)[0] for s in DEFAULT_PHASE_LIMITS},
        protected_history_count=len(protected), protected_history_identity=canonical_hash(protected),
        rankcloak_inspected_revision="ce853d42d6ba64065cb63c6bdfc0d825c62734cd",
        scope="new likelihood-only observations, not new transmissions or V2 replacement"))
    print("frozen",len(manifest["artifacts"]),"artifacts",flush=True)


def verify_freeze():
    for path,digest in read(REVIEW/"execution_freeze.json")["files"].items():
        if sha256_file(ROOT/path)!=digest:
            raise ValueError("execution freeze changed: "+path)
    for path,digest in read(MANIFEST)["accepted_sources"].items():
        if sha256_file(ROOT/path)!=digest: raise ValueError("accepted source changed: "+path)


def jobs():
    _,records=budget_state(STAGE)
    starts={r["id"]:r for r in records if r["event"]=="started"}
    return [{**starts[r["id"]],**r} for r in records if r["event"]=="finished"]


def execute(item,manifest):
    ident=item["observer_id"]
    terminal=REVIEW/"terminals"/(ident+".json")
    if terminal.exists():
        value=read(terminal)
        if value["input_identity"]!=canonical_hash(item): raise ValueError("changed completed work")
        if value["report_sha256"]!=sha256_file(REVIEW/value["report"]): raise ValueError("changed report")
        return value
    folder=RUN/"inputs"/ident
    folder.mkdir(parents=True,exist_ok=True)
    inputs={"carrier.png":ROOT/item["carrier"],"profile.json":PROFILE,
            "row.rgb":ROOT/manifest["contexts"][item["observer_context"]]["path"]}
    for name,path in inputs.items():
        destination=folder/name
        if destination.exists():
            if sha256_file(destination)!=sha256_file(path): raise ValueError("changed observer inbox")
        else: shutil.copyfile(path,destination)
    if set(p.name for p in folder.iterdir())!=set(inputs):
        raise ValueError("undeclared observer input")
    report=REVIEW/"reports"/(ident+".json")
    command=[read_profile(PROFILE)["image"]["interpreter"],"-B","-m","imagecalgacus.png_observer",
        "--carrier",str(folder/"carrier.png"),"--profile",str(folder/"profile.json"),
        "--context",str(folder/"row.rgb"),"--report",str(report)]
    matching=[j for j in jobs() if j["command"]==command]
    if not matching:
        if report.exists(): raise ValueError("orphan report without ledger evidence")
        if remaining()<60: raise RuntimeError("insufficient inclusive per-job reserve")
        run_budgeted(command,ident,stage=STAGE,max_seconds=60)
        matching=[j for j in jobs() if j["command"]==command]
    if len(matching)!=1: raise ValueError("duplicate execution attempt; reconcile explicitly")
    job=matching[0]
    if not report.exists():
        raise RuntimeError("interrupted or missing observer report; preserve job and stop")
    result=read(report)
    if result["carrier_sha256"]!=item["carrier_sha256"] or result["context_sha256"]!=manifest["contexts"][item["observer_context"]]["sha256"]:
        raise ValueError("observer identity mismatch")
    if result["profile_id"]!=manifest["profile_id"] or result["source_hash"]!=manifest["source_hash"]:
        raise ValueError("observer profile/source mismatch")
    verify_gpu_report(result,"image",read_profile(PROFILE))
    positive=any(len((f:=r["pmon"].split()))>3 and f[3].isdigit() and int(f[3])>0 for r in job["pmon_samples"])
    if not positive or result["gpu_evidence"].get("cuda_model_milliseconds",0)<=0:
        raise RuntimeError("positive process-specific GPU activity not established")
    if job["failure"] or job["returncode"] not in (0,2):
        raise RuntimeError("infrastructure failure; inspect retained job")
    value=dict(observer_id=ident,input_identity=canonical_hash(item),job_id=job["id"],
        report=str(report.relative_to(REVIEW)),report_sha256=sha256_file(report),
        passed=result["passed"],charged_seconds=job["elapsed_seconds"],positive_gpu_activity=positive,
        failure_stage=result["failure_stage"],failure_reason=result["failure_reason"])
    atomic_json(terminal,value)
    return value


def run():
    prepare(); reconcile_interrupted(STAGE); verify_freeze()
    manifest=read(MANIFEST); checks=[]
    for item in manifest["development_validation"]:
        outcome=execute(item,manifest);report=read(REVIEW/outcome["report"])
        check=dict(artifact_id=item["artifact_id"],observer_id=item["observer_id"],
            scores_exact=report["scores"]==item["correct_scores"],
            digest_available=item["distribution_digest"] is not None,
            digest_exact=(report["gpu_evidence"]["distribution_digest"]==item["distribution_digest"]
                          if item["distribution_digest"] is not None else None),
            charged_seconds=outcome["charged_seconds"])
        checks.append(check)
        if not outcome["passed"] or not check["scores_exact"] or check["digest_exact"] is False:
            atomic_json(REVIEW/"validation.json",dict(passed=False,checks=checks),replace=True)
            raise RuntimeError("development score reproduction discrepancy; no held-out scoring")
    atomic_json(REVIEW/"validation.json",dict(passed=True,checks=checks),replace=True)
    per_job=max(30.,1.5*max(r["charged_seconds"] for r in checks))
    pending=[r for r in manifest["artifacts"] if not (REVIEW/"terminals"/(r["observer_id"]+".json")).exists()]
    forecast=dict(pending_jobs=len(pending),conservative_seconds_per_job=per_job,
        remaining_projected_seconds=len(pending)*per_job,available_seconds=remaining(),
        fits=len(pending)*per_job<=remaining(),margin="one 50% margin with 30s/job floor")
    atomic_json(REVIEW/"preflight_forecast.json",forecast,replace=True)
    print("measured full-batch forecast",json.dumps(forecast),flush=True)
    if not forecast["fits"]: raise RuntimeError("complete balanced batch cannot fit")
    for i,item in enumerate(manifest["artifacts"]):
        verify_freeze()
        left=sum(not (REVIEW/"terminals"/(r["observer_id"]+".json")).exists()
                 for r in manifest["artifacts"][i:])
        if left*per_job>remaining(): raise RuntimeError("remaining full allocation no longer fits")
        outcome=execute(item,manifest)
        per_job=max(per_job,1.5*outcome["charged_seconds"])
        print("completed",i+1,"/80",item["observer_id"],"scorable",outcome["passed"],flush=True)
        if (i+1)%4==0:
            atomic_json(REVIEW/"progress.json",dict(terminal_artifacts=i+1,
                remaining_gpu_seconds=remaining(),remaining_forecast_seconds=(79-i)*per_job),replace=True)
    baseline=read(RUN/"protected_history.json")
    changed=[p for p,h in baseline.items() if not (ROOT/p).exists() or sha256_file(ROOT/p)!=h]
    atomic_json(REVIEW/"preservation.json",dict(checked_files=len(baseline),changed=changed,
        passed=not changed,private_contents_not_exported=True),replace=True)
    if changed: raise ValueError("accepted history changed")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["prepare","run"])
    args=parser.parse_args()
    (prepare if args.action=="prepare" else run)()


if __name__=="__main__":main()
