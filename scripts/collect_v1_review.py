"""Allowlisted CPU-only V1 evidence packaging; never runs a neural model."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import json_write,sha256_file,source_hash,budget_state
from imagecalgacus.evaluate import evaluate_run,validate_allocation
from collect_v0_review import compact_gpu


def copy(source,target):
    source,target=Path(source),Path(target)
    if source.suffix in {".key",".packet",".bin",".pth",".gguf",".so",".pstats"}:
        raise ValueError("forbidden public file")
    if source.is_file():
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",type=Path,nargs="+",required=True)
    parser.add_argument("--qualification",action="store_true",help="collect only the new bounded V1.2 batch")
    args=parser.parse_args()
    if args.qualification:
        if len(args.run)!=1: parser.error("one bounded qualification run required")
        return collect_qualification(args.run[0])
    review=ROOT/"artifacts/v1_review"
    expected=json.loads((review/"pilot_manifest.json").read_text())["cases"]
    public_rows=[]; rows=[]; copied_rows=[]; run_checks={}; seen_cases=set()
    for run in args.run:
        manifest=json.loads((run/"references.json").read_text())
        part,check=evaluate_run(run,manifest["cases"],"final",
            [json.loads(line) for line in (run/"results.jsonl").read_text().splitlines()])
        run_checks[run.name]=check
        rows.extend(part)
        for row in part:
            case_dir=run/row["case"]
            if row["case"] in seen_cases: raise ValueError("duplicate case cannot overwrite public evidence")
            seen_cases.add(row["case"])
            public=review/"cases"/row["case"]
            for name in ("source.png","source.txt","recovered.gray","recovered.png","recovered.txt",
                         "sender.json","receiver.json","evaluation.json","attempt.json","failed-prefix.txt"):
                copy(case_dir/name,public/name)
            for name in ("carrier.txt","carrier.png","profile.json"):
                copy(case_dir/"inbox"/name,public/name)
            row=dict(row,run=run.name,independent_payload_group=row["case"].split("-")[0])
            for field in ("source","carrier","recovered","sender_gpu_evidence","receiver_gpu_evidence"):
                if row.get(field):
                    row[field]=str((public/Path(row[field]).name).relative_to(review))
            public_rows.append(row)
        for name in ("implementation.json","midpilot_projection.json","final_validation.json"):
            copy(run/name,review/run.name/name)
    coverage=validate_allocation(expected,rows)
    copied_rows,copied_coverage=evaluate_run(review/"cases",expected,"final",rows)
    copied_coverage.pop("recorded_result_reconciliation",None)
    json_write(review/"coverage.json",coverage)
    json_write(review/"run_coverage.json",run_checks)
    public_manifest=[]
    for c in expected:
        c=dict(c,source=str((review/"fixtures"/Path(c["source"]).name).relative_to(ROOT)),
               profile=str((review/"profiles"/Path(c["profile"]).name).relative_to(ROOT)),
               context=str((review/"contexts"/Path(c["context"]).name).relative_to(ROOT)))
        public_manifest.append(c)
    json_write(review/"references.json",{"cases":public_manifest})
    with (review/"results.jsonl").open("w") as stream:
        for row in public_rows: stream.write(json.dumps(row,ensure_ascii=False)+"\n")
    for name in ("LICENSE","THIRD_PARTY.md"):
        copy(ROOT/name,review/name)
    copy(ROOT/"artifacts/v0_review/environment.json",review/"reused_environment.json")
    for source in (ROOT/"configs").glob("v1*.json"):
        copy(source,review/"profiles"/source.name)
    for category in ("calibration","controls"):
        for directory in sorted((ROOT/".runtime/v1"/category).glob("*")):
            for name in ("result.json","carrier.txt","carrier.png"):
                copy(directory/name,review/category/directory.name/name)
            for source in directory.glob("prefix-*.txt"):
                copy(source,review/category/directory.name/source.name)
    for name in ("result.json","reference.txt","optimized.txt"):
        copy(ROOT/"runs/v1-text-equivalence-001"/name,review/"text_equivalence"/name)
    copy(ROOT/".runtime/v1/profile-reference/result.json",review/"text_equivalence/profile_reference.json")
    used,ledger=budget_state("v1"); v0,_=budget_state("v0")
    jobs=compact_gpu(ledger)
    for job in jobs:
        record=next(r for r in ledger if r["event"]=="finished" and r["id"]==job["id"])
        fields=[s["pmon"].split() for s in record.get("pmon_samples",[])]
        job["sampled_max_process_fb_mb"]=max((int(f[9]) for f in fields if len(f)>9 and f[9].isdigit()),default=None)
        job["memory_measurement"]="nvidia-smi pmon FB column, reported MB; sampled maximum, not guaranteed allocator peak"
    json_write(review/"gpu_jobs.json",jobs)
    json_write(review/"budget.json",{"v0_historical_seconds":v0,"v1_charged_seconds":used,
        "v1_limit_seconds":7200,"v1_remaining_seconds":7200-used,"cumulative_seconds":v0+used,
        "overall_ceiling_seconds":144000,"overall_remaining_not_automatically_authorized":144000-v0-used,
        "charged_rule":"full process wall time: loading, filtering, GPU inference, serialization and teardown",
        "all_jobs_observed_process_gpu_activity":all(j["max_process_sm_percent"]>0 for j in jobs)})
    # Exact model initialization evidence, without full stderr/large activity dumps.
    evidence=[]
    for job in jobs:
        log=ROOT/job["logs_retained_locally"]/"stderr.log"
        if log.exists():
            lines=[line for line in log.read_text(errors="replace").splitlines()
                   if any(term in line for term in ("offloaded ","CUDA0 model buffer","CUDA0 KV buffer","CUDA0 compute buffer"))]
            evidence.append({"job":job["id"],"stderr_sha256":sha256_file(log),"initialization_lines":lines})
    json_write(review/"backend_initialization.json",evidence)
    test=subprocess.run([sys.executable,"-B","-m","unittest","discover","-s","tests","-v"],
                        cwd=ROOT,text=True,capture_output=True)
    (review/"cpu_tests.txt").write_text(test.stdout+test.stderr)
    json_write(review/"cpu_tests.json",{"exit_code":test.returncode,"command":[sys.executable,"-B","-m","unittest","discover","-s","tests","-v"]})
    source_files={}
    for folder in ("imagecalgacus","tests","scripts"):
        source_files.update({str(p.relative_to(ROOT)):sha256_file(p) for p in (ROOT/folder).rglob("*.py")})
    for p in (ROOT/"configs").glob("*.json"): source_files[str(p.relative_to(ROOT))]=sha256_file(p)
    for name in ("requirements.txt","THIRD_PARTY.md","LICENSE"):
        if (ROOT/name).exists(): source_files[name]=sha256_file(ROOT/name)
    json_write(review/"source_manifest.json",{"package_source_hash":source_hash(),"files":source_files})
    # Recheck every public artifact's equality/identity from the copied files.
    json_write(review/"public_artifact_validation.json",copied_coverage)
    print(json.dumps({"coverage":coverage,"public_validation":copied_coverage,"cpu_exit":test.returncode,"v1_seconds":used}))
    return int(test.returncode!=0 or coverage!=copied_coverage)


def collect_qualification(run):
    """Allowlisted checkpoint, explicit credits; no copy of historical packets."""
    import hashlib
    from collections import Counter
    review=ROOT/"artifacts/v1_2_review"
    if (review/"cases").exists(): raise FileExistsError("V1.2 cases already collected")
    references=json.loads((run/"references.json").read_text())
    recorded=[json.loads(line) for line in (run/"results.jsonl").read_text().splitlines()]
    rows,coverage=evaluate_run(run,references["cases"],"final",recorded)
    public_rows=[]
    for row in rows:
        directory=run/row["case"]; public=review/"cases"/row["case"]
        for name in ("source.png","source.txt","recovered.gray","recovered.png","recovered.txt",
                     "sender.json","receiver.json","evaluation.json","attempt.json","failed-prefix.txt"):
            copy(directory/name,public/name)
        for name in ("carrier.txt","carrier.png","profile.json","prompt.txt","row.rgb"):
            copy(directory/"inbox"/name,public/name)
        original=next(r for r in recorded if r["work_id"]==row["work_id"])
        row.update({k:original[k] for k in ("run","phase","context_id","pair_id","sender_exit","receiver_exit")})
        for field in ("source","carrier","recovered","sender_gpu_evidence","receiver_gpu_evidence"):
            if row.get(field): row[field]=str((public/Path(row[field]).name).relative_to(review))
        public_rows.append(row)
    json_write(review/"references.json",references)
    with (review/"results.jsonl").open("x") as stream:
        for row in public_rows: stream.write(json.dumps(row,ensure_ascii=False)+"\n")
    _,public_validation=evaluate_run(review/"cases",references["cases"],"final",recorded)
    json_write(review/"batch_coverage.json",coverage)
    json_write(review/"public_artifact_validation.json",public_validation)
    allocation=json.loads((ROOT/"configs/v1_qualification.json").read_text())
    credited_new={r["work_id"] for r in rows if r["evidence_valid"] and r["outcome_class"] in {"exact_recovery","static_tokenization_drift_failure"}}
    events=[]
    for case in allocation["cases"]:
        if case["status"]=="credited":
            events.append({"work_id":case["work_id"],"case":case["id"],"event":"accepted_pilot_credit",
                           "evidence":"artifacts/v1_review/cases/"+case["id"]+"/evaluation.json"})
        elif case["work_id"] in credited_new:
            result=next(r for r in rows if r["work_id"]==case["work_id"])
            events.append({"work_id":case["work_id"],"case":case["id"],"event":"qualification_outcome",
                           "outcome_class":result["outcome_class"],"evidence":"cases/"+case["id"]+"/evaluation.json"})
    with (review/"qualification_events.jsonl").open("x") as stream:
        for event in events: stream.write(json.dumps(event)+"\n")
    pending=[c for c in allocation["cases"] if c["status"]=="pending" and c["work_id"] not in credited_new]
    coverage_table=Counter((c["direction"],c["method"],c["text_filter_arm"]) for c in pending)
    json_write(review/"qualification_coverage.json",{
        "stego_allocated":152,"prior_credits":12,"new_outcome_credits":len(credited_new),"pending_stego":len(pending),
        "pending_by_arm":[{"direction":d,"method":m,"arm":a,"count":n} for (d,m,a),n in sorted(coverage_table.items(),key=str)],
        "pending_work_ids":[c["work_id"] for c in pending],
        "ordinary_credited":4,"ordinary_pending":12,"controls_credited":2,"controls_pending_upper":46,
        "diagnostic_replay_credits":0,"v1_qualified":False,"batch_unique_payloads":2,"batch_payload_context_groups":4})
    used,ledger=budget_state("v1");v0,_=budget_state("v0")
    records=[r for r in ledger if "-"+run.name+"-" in r["id"]]
    jobs=compact_gpu(records)
    json_write(review/"gpu_jobs.json",jobs)
    initialization=[]
    for job in jobs:
        log=ROOT/job["logs_retained_locally"]/"stderr.log"
        initialization.append({"job":job["id"],"stderr_sha256":sha256_file(log),
            "initialization_lines":[l for l in log.read_text(errors="replace").splitlines()
               if any(t in l for t in ("offloaded ","CUDA0 model buffer","CUDA0 KV buffer","CUDA0 compute buffer"))]})
    json_write(review/"backend_initialization.json",initialization)
    baseline=json.loads((ROOT/".runtime/v1_2/baseline.json").read_text())
    changed=[p for p,h in baseline["protected_files"].items() if not (ROOT/p).is_file() or sha256_file(ROOT/p)!=h]
    prefix=(ROOT/".runtime/v1/gpu_budget.jsonl").read_bytes()[:baseline["v1_ledger_bytes"]]
    prefix_ok=hashlib.sha256(prefix).hexdigest()==baseline["v1_ledger_sha256"]
    json_write(review/"preservation.json",{"protected_files":len(baseline["protected_files"]),"changed":changed,
        "original_v1_ledger_prefix_unchanged":prefix_ok,"v0_seconds_unchanged":v0==baseline["v0_seconds"],
        "accepted_evidence_preserved":not changed and prefix_ok})
    json_write(review/"budget.json",{"checkpoint_seconds":used-baseline["v1_seconds"],"v1_charged_seconds":used,
        "v1_remaining_seconds":7200-used,"v1_limit_seconds":7200,"v0_seconds":v0,"cumulative_seconds":used+v0,
        "gpu_jobs":len(jobs),"all_jobs_have_process_gpu_activity":all(j["max_process_sm_percent"]>0 for j in jobs),
        "full_child_wall_time_charged":True,"no_new_phase_allowance":True})
    for name in ("v0_revalidation_correct_phase.json","v1_revalidation.json"):
        item=json.loads((ROOT/".runtime/v1_2"/name).read_text());item.pop("results",None)
        json_write(review/name,item)
    copy(ROOT/"configs/v1_2_batch.json",review/"batch_manifest.json")
    copy(ROOT/"configs/v1_fixed_static.json",review/"static_profile.json")
    json_write(review/"source_manifest.json",{"package_source_hash":source_hash(),
        "source_preparation_sha256":sha256_file(ROOT/"data/qualification_v1/manifest.json"),
        "allocation_sha256":sha256_file(ROOT/"configs/v1_qualification.json"),
        "files":{str(p.relative_to(ROOT)):sha256_file(p) for folder in ("imagecalgacus","scripts","tests")
                 for p in sorted((ROOT/folder).rglob("*.py"))}})
    print(json.dumps({"batch":coverage,"qualified_new":len(credited_new),"pending":len(pending),"gpu_seconds":used-baseline["v1_seconds"],
                      "remaining_v1":7200-used,"preserved":not changed and prefix_ok}))
    return int(bool(changed) or not prefix_ok or not public_validation["allocation_complete"])


if __name__=="__main__":
    raise SystemExit(main())
