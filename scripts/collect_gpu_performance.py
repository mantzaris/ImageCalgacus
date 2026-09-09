"""Compact CPU-only benchmark export, timings and saved-evidence verification."""
import argparse
import csv
import io
import json
from pathlib import Path
import shutil
import statistics
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import atomic_json,sha256_file,budget_state,phase_limit,canonical_hash
from imagecalgacus.qualification import read_json,verify_gpu_report,validate_receiver_inbox,verify_binding
from imagecalgacus.evaluate import evaluate_case
from imagecalgacus.gpu_performance import STAGE,MANIFEST,REVIEW,completed_jobs,compare_records


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if sha256_file(source)!=sha256_file(target):raise ValueError("refusing changed export: "+str(target))
    else:shutil.copyfile(source,target)


def save(path,value):
    atomic_json(path,value,replace=path.exists())


def compact_job(job):
    samples=[]
    for row in job["pmon_samples"]:
        fields=row["pmon"].split()
        if len(fields)>9 and fields[3].isdigit():
            samples.append({"elapsed_seconds":row["elapsed"],"physical_gpu_index":int(fields[0]),
                "pid":int(fields[1]),"sm_percent":int(fields[3]),
                "fb_memory_mib":int(fields[9]) if fields[9].isdigit() else None})
    intervals=[b["elapsed_seconds"]-a["elapsed_seconds"] for a,b in zip(samples,samples[1:])]
    return {"id":job["id"],"pid":job["pid"],"utc":job["utc"],"command":job["command"],
        "returncode":job["returncode"],"failure":job["failure"],"charged_seconds":job["elapsed_seconds"],
        "logs_retained_locally":job["logs"],"samples":samples,"sample_count":len(samples),
        "positive_process_activity":any(s["sm_percent"]>0 for s in samples),
        "sampled_mean_sm_percent":statistics.mean(s["sm_percent"] for s in samples) if samples else None,
        "sampled_max_sm_percent":max((s["sm_percent"] for s in samples),default=None),
        "sampled_peak_memory_mib":max((s["fb_memory_mib"] or 0 for s in samples),default=None),
        "median_sampling_interval_seconds":statistics.median(intervals) if intervals else None}


def analysis(review,records):
    comparisons=[read_json(p) for p in sorted((review/"comparisons").glob("*.json"))]
    individual=[]
    for pair in comparisons:
        definition=pair["comparison"]
        for mode in definition["mode_order"]:
            record=pair["records"][mode];case=record["case"];row=record["evaluation"]
            folder=review/"cases"/case["id"]
            sender,receiver=read_json(folder/"sender.json"),read_json(folder/"receiver.json")
            cuda=sum(r["gpu_evidence"]["cuda_model_milliseconds"]/1000 for r in (sender,receiver))
            phase=sender["encode_seconds"]+receiver["decode_seconds"]
            cold=sum(r["cold_load_seconds"] for r in (sender,receiver))
            setup=sum(r["gpu_evidence"]["execution_setup_seconds"] for r in (sender,receiver))
            occupied=record["charged_pair_seconds"]
            item={"comparison":definition["id"],"payload":definition["payload_id"],"method":definition["method"],
                "repetition":definition["repetition"],"mode":mode,"payload_bytes":row["source_bytes"],
                "encode_seconds":sender["encode_seconds"],"decode_seconds":receiver["decode_seconds"],
                "charged_encode_seconds":record["charged_encode_seconds"],"charged_decode_seconds":record["charged_decode_seconds"],
                "charged_pair_seconds":occupied,"exact_payload_bytes_per_second":row["source_bytes"]/occupied if row["exact_recovery"] else 0,
                "cold_load_pair_seconds":cold,"execution_setup_pair_seconds":setup,
                "cuda_event_pair_seconds":cuda,"phase_non_cuda_interval_seconds":phase-cuda,
                "other_occupied_seconds":occupied-phase-cold-setup,
                "cuda_event_encode_seconds":sender["gpu_evidence"]["cuda_model_milliseconds"]/1000,
                "cuda_event_decode_seconds":receiver["gpu_evidence"]["cuda_model_milliseconds"]/1000,
                "peak_cuda_allocated_mib":max(r["gpu_evidence"]["peak_cuda_allocated_bytes"] for r in (sender,receiver))/2**20,
                "peak_cuda_reserved_mib":max(r["gpu_evidence"]["peak_cuda_reserved_bytes"] for r in (sender,receiver))/2**20,
                "carrier_bytes":row["carrier_bytes"],"pixels":row["pixels"],"channels":row["channels"],
                "model_calls_per_process":sender["model_calls"],"exact_recovery":row["exact_recovery"],
                "equivalent":pair["equivalence"]["equivalent"]}
            individual.append(item)
    summaries=[]
    for payload,method in sorted({(r["payload"],r["method"]) for r in individual}):
        selected=[r for r in individual if r["payload"]==payload and r["method"]==method]
        modes={mode:[r for r in selected if r["mode"]==mode] for mode in ("reference","cuda_graph")}
        summary={"payload":payload,"method":method,"payload_bytes":selected[0]["payload_bytes"],
                 "timing_repetitions":len(modes["reference"]),"independent_research_observations":0,"modes":{}}
        for mode,rows in modes.items():
            keys=[k for k in rows[0] if isinstance(rows[0][k],(int,float)) and not isinstance(rows[0][k],bool)]
            summary["modes"][mode]={k:statistics.mean(r[k] for r in rows) for k in keys}
            summary["modes"][mode]["process_pair_range_seconds"]=[min(r["charged_pair_seconds"] for r in rows),max(r["charged_pair_seconds"] for r in rows)]
        a,b=(summary["modes"][mode] for mode in ("reference","cuda_graph"))
        summary.update(pair_speedup=a["charged_pair_seconds"]/b["charged_pair_seconds"],
            encode_speedup=a["charged_encode_seconds"]/b["charged_encode_seconds"],
            decode_speedup=a["charged_decode_seconds"]/b["charged_decode_seconds"])
        summaries.append(summary)
    fixed={mode:[r for r in individual if r["method"]=="fixed" and r["mode"]==mode] for mode in ("reference","cuda_graph")}
    aggregate={}
    for mode,rows in fixed.items():
        if rows:
            aggregate[mode]={"pairs":len(rows),"mean_charged_encode_seconds":statistics.mean(r["charged_encode_seconds"] for r in rows),
                "mean_charged_decode_seconds":statistics.mean(r["charged_decode_seconds"] for r in rows),
                "mean_charged_pair_seconds":statistics.mean(r["charged_pair_seconds"] for r in rows),
                "exact_payload_bytes_per_second":sum(r["payload_bytes"] for r in rows)/sum(r["charged_pair_seconds"] for r in rows),
                "mean_encode_phase_seconds":statistics.mean(r["encode_seconds"] for r in rows),
                "mean_decode_phase_seconds":statistics.mean(r["decode_seconds"] for r in rows)}
    if len(aggregate)==2:aggregate["pair_speedup"]=aggregate["reference"]["mean_charged_pair_seconds"]/aggregate["cuda_graph"]["mean_charged_pair_seconds"]
    result={"analysis_code_sha256":sha256_file(__file__),"individual":individual,"summaries":summaries,"fixed_aggregate":aggregate,
        "latency_definition":"charged fresh child process, including imports/loading/setup/serialization/teardown; monitor join is wrapper overhead outside charge",
        "throughput_definition":"exact source bytes divided by charged encoder+receiver time, not packet bytes or carrier bytes",
        "cuda_caveat":"CUDA events bracket forwards and are synchronized before reading; reference intervals include device-idle gaps between host kernel launches, not a profiler sum of active kernel times",
        "nested_measurements":"CUDA intervals are inside phases; phases, model load and execution setup are inside occupied processes. Do not add them to charges again.",
        "sample_size_caveat":"three development payloads; timing repetitions are not independent observations; no inferential performance intervals"}
    save(review/"timings.json",result)
    stream=io.StringIO()
    if individual:
        writer=csv.DictWriter(stream,fieldnames=list(individual[0]));writer.writeheader();writer.writerows(individual)
    (review/"timings.csv").write_text(stream.getvalue())
    lines=["| Payload / method | Repeats | Ref encode / decode (s) | Graph encode / decode (s) | Pair speedup | Ref → graph payload B/s |",
           "|---|---:|---:|---:|---:|---:|"]
    for row in summaries:
        a,b=(row["modes"][mode] for mode in ("reference","cuda_graph"))
        lines.append(f"| {row['payload']} / {row['method']} ({row['payload_bytes']} B) | {row['timing_repetitions']} | {a['charged_encode_seconds']:.2f} / {a['charged_decode_seconds']:.2f} | {b['charged_encode_seconds']:.2f} / {b['charged_decode_seconds']:.2f} | {row['pair_speedup']:.2f}× | {a['exact_payload_bytes_per_second']:.3f} → {b['exact_payload_bytes_per_second']:.3f} |")
    (review/"comparison_table.md").write_text("\n".join(lines)+"\n")
    return result


def collect(directory,review):
    review.mkdir(parents=True,exist_ok=True)
    manifest=read_json(MANIFEST);identity=read_json(directory/"execution_identity.json")
    for source,name in ((MANIFEST,"manifest.json"),(directory/"execution_identity.json","execution_identity.json"),
                        (directory/"probe.json","probe.json"),(ROOT/"configs/gpu_performance_authorization.json","authorization.json")):
        if source.exists():copy(source,review/name)
    bindings=read_json(directory/"packet_bindings.json")
    records=[];boundaries=[];historical=[]
    for path in sorted((directory/"comparisons").glob("*.json")):
        comparison=read_json(path)
        copy(path,review/"comparisons"/path.name)
        pair_records=comparison["records"]
        left,right=(Path(pair_records[mode]["folder"]) for mode in ("reference","cuda_graph"))
        for name in ("inbox/carrier.png","recovered.txt"):
            if (left/name).read_bytes()!=(right/name).read_bytes():
                raise ValueError("direct matched saved bytes differ")
        if comparison["comparison"]["repetition"]==0:
            payload=comparison["comparison"]["payload_id"];method=comparison["comparison"]["method"]
            locations=[ROOT/"artifacts/v1_qualification_review/cases"/(payload+"-row1-"+method),
                       ROOT/"artifacts/v1_review/cases"/(payload+"-"+method)]
            original=next((p for p in locations if (p/"carrier.png").exists()),None)
            if original is None:raise ValueError("missing accepted development reference")
            same=(left/"inbox/carrier.png").read_bytes()==(original/"carrier.png").read_bytes()
            if not same:raise ValueError("reference changed versus accepted development carrier")
            historical.append({"comparison":comparison["comparison"]["id"],"accepted_carrier":str(original/"carrier.png"),
                               "accepted_carrier_sha256":sha256_file(original/"carrier.png"),"byte_equal":same,
                               "historical_execution_source_hash":read_json(original/"sender.json")["source_hash"]})
        for mode,record in comparison["records"].items():
            case=record["case"];folder=Path(record["folder"]);target=review/"cases"/case["id"]
            _,key=verify_binding(bindings[case["pair_id"]],case)
            validate_receiver_inbox(folder/"inbox",case,key)
            boundaries.append({"case":case["id"],"input_roles":["carrier","profile","context","key"],
                "actual_names":sorted(p.name for p in (folder/"inbox").iterdir()),"passed":True,
                "mode_is_explicit_execution_configuration":mode})
            for name in ("source.txt","recovered.txt","sender.json","receiver.json","evaluation.json"):
                if (folder/name).exists():copy(folder/name,target/name)
            for name in ("carrier.png","profile.json","row.rgb"):
                copy(folder/"inbox"/name,target/name)
            records.append({**record,"benchmark_execution_id":case["id"],"new_scientific_credit":False})
    jobs=[compact_job(job) for job in completed_jobs()]
    save(review/"gpu_jobs.json",jobs);save(review/"receiver_boundaries.json",boundaries)
    save(review/"historical_reference_equivalence.json",historical)
    (review/"results.jsonl").write_text("".join(json.dumps(r,allow_nan=False)+"\n" for r in records))
    usage={s:budget_state(s)[0] for s in ("v0","v1","v2",STAGE)}
    if any(usage[s]!=identity["historical_usage_seconds"][s] for s in ("v0","v1","v2")):
        raise ValueError("historical charged usage changed")
    spent=sum(usage.values());performance=usage[STAGE]
    accounting={"usage_seconds":usage,"phase_limits_seconds":{s:phase_limit(s) for s in usage},
        "new_charged_seconds":performance,"cumulative_charged_seconds":spent,
        "benchmark_remaining_seconds":phase_limit(STAGE)-performance,"whole_remaining_seconds":144000-spent,
        "whole_ceiling_seconds":144000,"allowance_is_not_spend":True,
        "reserve_fraction":0.25,"forecast_with_one_reserve_seconds":1.25*spent,
        "future_authorized_research_work_seconds":0,"reserve_is_unused_planning_cushion":True}
    save(review/"accounting.json",accounting)
    protected=read_json(directory/"protected_history.json")
    changed=[p for p,h in protected.items() if not (ROOT/p).exists() or sha256_file(ROOT/p)!=h]
    save(review/"preservation.json",{"historical_files_checked":len(protected),"changed":changed,
        "passed":not changed,"private_hash_index_retained":str(directory/"protected_history.json")})
    if changed:raise ValueError("historical evidence changed")
    current={name:sha256_file(ROOT/name)==digest for name,digest in identity["files"].items()}
    save(review/"execution_identity_check.json",{"passed":all(current.values()),"files":current})
    analysis(review,records)
    public_files=[p for p in review.rglob("*") if p.is_file()]
    # Allowlisted export + direct raw/hex/base64 material checks; never print secrets.
    import base64
    secrets=[]
    for binding in bindings.values():
        for field in ("packet","key"):
            raw=Path(binding[field]).read_bytes();secrets.extend((raw,raw.hex().encode(),base64.b64encode(raw)))
    for path in public_files:
        if path.is_symlink() or path.suffix in {".key",".packet",".pth",".gguf"}:raise ValueError("private file in public review")
        data=path.read_bytes()
        if any(value in data for value in secrets):raise ValueError("private material in export")
    save(review/"privacy.json",{"allowlisted_export":True,"private_material_scan_passed":True,
        "excluded":["keys","sealed packets","weights","private environments","raw packet/interval traces"],
        "public_reports_contain_only_exact_distribution_hashes":True})
    save(review/"artifact_hashes.json",{str(p.relative_to(review)):sha256_file(p) for p in sorted(review.rglob("*"))
         if p.is_file() and p.name not in {"artifact_hashes.json","public_verification.json","README.md"}})
    return verify_public(review,write=True)


def verify_public(review,write=False):
    manifest=read_json(review/"manifest.json");identity=read_json(review/"execution_identity.json")
    if sha256_file(review/"manifest.json")!=identity["manifest_sha256"]:raise ValueError("manifest changed")
    for name,digest in read_json(review/"artifact_hashes.json").items():
        path=(review/name).resolve()
        if not path.is_relative_to(review.resolve()) or sha256_file(path)!=digest:raise ValueError("public evidence changed: "+name)
    rows=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    if len({r["case"]["id"] for r in rows})!=len(rows):raise ValueError("duplicate timing observation")
    expected={c["id"]+"-"+mode for c in manifest["comparisons"] for mode in c["mode_order"]}
    actual={r["case"]["id"] for r in rows}
    if not actual.issubset(expected):raise ValueError("unexpected benchmark case")
    packets={};recoveries=0;repeat_identity={}
    for record in rows:
        case=record["case"];folder=review/"cases"/case["id"]
        checked=evaluate_case(case,folder)
        if not (checked["evidence_valid"] and checked["exact_recovery"] and checked["carrier_complete"]):raise ValueError("invalid saved-artifact outcome")
        if sha256_file(folder/"row.rgb")!=case["context_sha256"]:raise ValueError("wrong context")
        if canonical_hash(read_json(folder/"profile.json"))!=manifest["profiles"][case["method"]]["profile_id"]:raise ValueError("wrong profile")
        sender,receiver=read_json(folder/"sender.json"),read_json(folder/"receiver.json")
        for report in (sender,receiver):
            verify_gpu_report(report,"image",read_json(folder/"profile.json"))
            if report["gpu_evidence"]["execution_mode"]!=record["mode"]:raise ValueError("wrong execution mode")
            if report["gpu_evidence"]["distribution_digest"]!=record["distribution_digest"]:raise ValueError("distribution stream mismatch")
        if record["distribution_digest"]["steps"]!=2976:raise ValueError("incomplete distribution audit")
        packet=sender["prepared_packet_sha256"]
        if packet!=case["packet_sha256"] or packets.setdefault(case["pair_id"],packet)!=packet:raise ValueError("changed paired packet")
        fingerprint=(sender["carrier_sha256"],receiver["recovered_sha256"],record["distribution_digest"])
        repeat_key=(case["payload_id"],case["method"])
        if repeat_identity.setdefault(repeat_key,fingerprint)!=fingerprint:
            raise ValueError("timing repetition changed behavior")
        if record.get("benchmark_execution_id")!=case["id"] or record.get("new_scientific_credit") is not False:
            raise ValueError("benchmark identity/credit not explicit")
        recoveries+=1
    pairs=[]
    for path in (review/"comparisons").glob("*.json"):
        pair=read_json(path);checked=compare_records(pair["records"])
        if not checked["equivalent"] or checked!=pair["equivalence"]:raise ValueError("comparison not exact")
        left,right=(review/"cases"/pair["records"][mode]["case"]["id"] for mode in ("reference","cuda_graph"))
        for name in ("carrier.png","recovered.txt"):
            if (left/name).read_bytes()!=(right/name).read_bytes():raise ValueError("saved comparison bytes differ")
        pairs.append(pair["comparison"]["id"])
    if len(pairs)*2!=len(rows):raise ValueError("missing comparison member")
    jobs=read_json(review/"gpu_jobs.json")
    if not all(j["positive_process_activity"] and j["returncode"]==0 and not j["failure"] for j in jobs):raise ValueError("GPU process evidence failed")
    accounting=read_json(review/"accounting.json")
    if abs(sum(j["charged_seconds"] for j in jobs)-accounting["new_charged_seconds"])>1e-8:raise ValueError("charges not reconciled")
    if accounting["new_charged_seconds"]>7200 or accounting["cumulative_charged_seconds"]>144000:raise ValueError("allowance exceeded")
    if not read_json(review/"preservation.json")["passed"]:raise ValueError("history not preserved")
    result={"timing_cases_completed":len(rows),"exact_recoveries":recoveries,"matched_comparisons":len(pairs),
        "frozen_maximum_comparisons":len(manifest["comparisons"]),"all_frozen_comparisons_completed":actual==expected,
        "missing":sorted(expected-actual),"gpu_model_processes":len(jobs),"saved_evidence_valid":True,
        "verification_scope":"CPU saved source/carrier/report hashes and allocation; no private-key authentication or neural replay"}
    if write:save(review/"public_verification.json",result)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",default="runs/gpu-performance-001")
    parser.add_argument("--review",default=str(REVIEW))
    choices=parser.add_mutually_exclusive_group()
    choices.add_argument("--verify-public",action="store_true")
    choices.add_argument("--analyze-public",action="store_true")
    args=parser.parse_args();review=Path(args.review)
    if args.analyze_public:
        verify_public(review)
        result=analysis(review,None)["fixed_aggregate"]
    else:
        result=verify_public(review) if args.verify_public else collect(Path(args.run),review)
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
