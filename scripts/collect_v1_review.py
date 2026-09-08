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
    args=parser.parse_args()
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


if __name__=="__main__":
    raise SystemExit(main())
