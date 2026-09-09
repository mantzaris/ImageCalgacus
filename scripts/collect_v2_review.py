"""CPU-only V2 evidence reconciliation/export and public verification.
Allowlisted artifacts only; private packets, keys and detailed audits never copied.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import runpy
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from imagecalgacus.runtime import atomic_json,sha256_file,canonical_hash,source_hash,budget_state,phase_limit
from imagecalgacus.qualification import read_json,completed_records,verify_binding,validate_receiver_inbox,verify_gpu_report
from imagecalgacus.evaluate import evaluate_case,validate_allocation
from imagecalgacus.v2 import MANIFEST,PRIOR,validate_manifest,reconcile_evidence,forecast
from collect_v1_review import copy
from collect_v0_review import compact_gpu


def verify_public(review,write=False):
    review=review.resolve();manifest=read_json(review/"manifest.json");validate_manifest(manifest)
    freeze=read_json(review/"execution_freeze.json")
    if sha256_file(review/"manifest.json")!=freeze["manifest_sha256"]:raise ValueError("manifest identity changed")
    if canonical_hash(manifest["analysis"])!=freeze["analysis_sha256"]:raise ValueError("analysis rules changed")
    index=read_json(review/"artifact_hashes.json")
    for name,digest in index.items():
        path=(review/name).resolve()
        if not path.is_relative_to(review) or sha256_file(path)!=digest:raise ValueError("public artifact changed: "+name)
    by_work={c["work_id"]:c for c in manifest["cases"]}
    saved=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    rows=[];packets={};boundary=[]
    for row in saved:
        c=by_work.get(row["work_id"])
        if c is None or c["id"]!=row["case"]:raise ValueError("unexpected case/work identity")
        folder=review/"cases"/c["id"];checked=evaluate_case(c,folder)
        for field in ("exact_recovery","evidence_valid","carrier_complete","source_equal","authenticated","carrier_sha256"):
            if checked[field]!=row[field]:raise ValueError("public evidence differs: "+c["id"]+"/"+field)
        if checked["artifact_saved"]:
            if sha256_file(folder/("prompt.txt" if c["direction"]=="image-to-text" else "row.rgb"))!=c["context_sha256"]:
                raise ValueError("public context changed")
            profile=read_json(folder/"profile.json")
            for name in ("sender.json","receiver.json"):
                if (folder/name).exists():verify_gpu_report(read_json(folder/name),"text" if c["direction"]=="image-to-text" else "image",profile)
        digest=checked.get("prepared_packet_sha256")
        if digest:
            if c["pair_id"] in packets and packets[c["pair_id"]]!=digest:raise ValueError("unpaired ciphertexts")
            packets[c["pair_id"]]=digest
        rows.append(checked)
    actual=[p.name for p in (review/"cases").iterdir() if p.is_dir()] if (review/"cases").exists() else []
    coverage=validate_allocation(manifest["cases"],rows,actual)
    traces=read_json(review/"controls.json")
    expected={t["work_id"]:t for t in manifest["controls"]}
    ids=[t["work_id"] for t in traces];valid=True
    for t in traces:
        definition=expected.get(t["work_id"])
        if not definition:valid=False;continue
        valid &= t["profile_id"]==definition["profile_id"] and t["context_sha256"]==definition["context_sha256"] and t["seed"]==definition["seed"] and t["passed"]
        members=[r for r in saved if by_work[r["work_id"]]["pair_id"]==definition["payload_group"]]
        lengths=[r["delivered_tokens"] for r in members if r["artifact_saved"]] if t["modality"]=="text" else [2976]
        if not lengths or t["symbols"]!=max(lengths):raise ValueError("control length is not the frozen realized-length rule")
        path=(review/t["carrier"]).resolve()
        valid &= path.is_relative_to(review) and sha256_file(path)==t["carrier_sha256"]
    links=read_json(review/"control_links.json")
    if len({l["work_id"] for l in links})!=len(links):raise ValueError("duplicate matched link")
    trace_lookup={t["work_id"]:t for t in traces}
    for link in links:
        if link["work_id"] not in by_work:raise ValueError("unexpected linked work")
        c=by_work[link["work_id"]]
        t=trace_lookup[link["trace_work_id"]]
        if expected[link["trace_work_id"]]["payload_group"]!=c["pair_id"]:raise ValueError("wrong shared control group")
        if link["available"]:
            path=(review/link["matched_artifact"]).resolve()
            if not path.is_relative_to(review) or sha256_file(path)!=link["matched_sha256"]:raise ValueError("control prefix changed")
            scores=(t["prefix_diagnostics"][str(link["symbols"])]["diagnostics"]["whole"]
                    if t["modality"]=="text" else t["diagnostics"]["whole"])
            if link["scores"]!=scores:raise ValueError("control score differs from inline report")
    controls_complete=valid and len(ids)==40 and set(ids)==set(expected) and len(set(ids))==len(ids)
    if controls_complete and coverage["allocation_complete"]:
        if len(links)!=120:raise ValueError("missing matched control association")
        rows_by_work={r["work_id"]:r for r in rows}
        for link in links:
            if rows_by_work[link["work_id"]]["artifact_saved"] and (not link["available"] or not link["scores"]):
                raise ValueError("new delivered carrier lacks its allocated matched control evidence")
    coverage.update(controls_completed=len(set(ids)),controls_allocation_complete=controls_complete,
        study_allocation_complete=coverage["allocation_complete"] and controls_complete,
        verification_scope="CPU public saved-source equality, identities, pairing digests, hashes, shared controls and complete allocation; not private-key GPU replay")
    if write:atomic_json(review/"public_verification.json",coverage,replace=True)
    print(json.dumps(coverage))
    return coverage


def collect(directory):
    directory=directory.resolve();review=ROOT/"artifacts/v2_review";review.mkdir(parents=True,exist_ok=True)
    manifest=read_json(MANIFEST);freeze=read_json(directory/"freeze.json")
    records=completed_records(directory,{})
    bindings=read_json(directory/"packet_bindings.json")
    reconcile_evidence(manifest,records,bindings)
    events=[json.loads(line) for line in (directory/"qualification_events.jsonl").read_text().splitlines()] if (directory/"qualification_events.jsonl").exists() else []
    if len({e["work_id"] for e in events})!=len(events) or {e["work_id"] for e in events}!=set(records):
        raise ValueError("event/terminal reconciliation mismatch")
    for event in events:
        if sha256_file(directory/event["record"])!=event["record_sha256"]:raise ValueError("terminal record changed")
    def save(name,value):atomic_json(review/name,value,replace=True)
    copy(MANIFEST,review/"manifest.json")
    public_freeze={k:v for k,v in freeze.items() if k!="protected_history"}
    public_freeze.update(private_freeze_sha256=sha256_file(directory/"freeze.json"),
        protected_history_count=len(freeze["protected_history"]))
    save("execution_freeze.json",public_freeze)
    rows=[];boundaries=[];arithmetic=[]
    for c in manifest["cases"]:
        folder=directory/"cases"/c["id"]
        if not folder.exists():continue
        row=evaluate_case(c,folder)
        if c["work_id"] in records:
            accepted=records[c["work_id"]]["evaluation"]
            for field in ("exact_recovery","evidence_valid","authenticated","carrier_complete"):
                if row[field]!=accepted[field]:raise ValueError("terminal evaluation changed")
            row.update(outcome_class=accepted["outcome_class"],private_prefix_equal=accepted["private_prefix_equal"])
            if records[c["work_id"]].get("arithmetic_audit"):
                arithmetic.append(dict(case=c["id"],**records[c["work_id"]]["arithmetic_audit"]))
        target=review/"cases"/c["id"]
        for name in ("source.png","source.txt","recovered.gray","recovered.png","recovered.txt","sender.json",
                     "receiver.json","evaluation.json","attempt.json","unexpected_failure.json"):
            copy(folder/name,target/name)
        for name in ("carrier.txt","carrier.png","profile.json","prompt.txt","row.rgb"):copy(folder/"inbox"/name,target/name)
        row.update(pair_id=c["pair_id"],context_id=c["context_id"],stratum=c["stratum"],
            execution_source_hash=records.get(c["work_id"],{}).get("execution_source_hash"),
            allocation_source_hash=c["source_hash"],evidence_directory=str(target.relative_to(review)))
        for field in ("source","carrier","recovered","sender_gpu_evidence","receiver_gpu_evidence"):
            if row.get(field):row[field]=str((target/Path(row[field]).name).relative_to(review))
        rows.append(row)
        if (folder/"receiver.json").exists():
            packet,key=verify_binding(bindings[c["pair_id"]],c)
            validate_receiver_inbox(folder/"inbox",c,key)
            receiver=read_json(folder/"receiver.json");sender=read_json(folder/"sender.json")
            boundaries.append(dict(case=c["id"],source_bound_packet=True,packet_sha256=sha256_file(packet),
                receiver_inputs=receiver["input_roles"],input_files=receiver["input_files"],
                fresh_process=receiver["gpu_evidence"]["device"]["pid"]!=sender["gpu_evidence"]["device"]["pid"],
                execution_source_hash=sender["source_hash"],
                receiver_source_identity_basis="frozen controller/group plus sender hash and fresh command/PID; no native receiver source-hash field"))
    with (review/"results.jsonl").open("w") as out:
        for row in rows:out.write(json.dumps(row,ensure_ascii=False)+"\n")
    save("failures.json",[r for r in rows if not (r["exact_recovery"] and r["carrier_complete"])])
    save("receiver_boundaries.json",boundaries);save("arithmetic_audits.json",arithmetic)
    traces=[];links=[];lookup={r["work_id"]:r for r in rows}
    for item in manifest["controls"]:
        if item["work_id"] not in records:continue
        record=records[item["work_id"]];data=record["result"]
        source=Path(record["result_path"]).parent;target=review/"controls"/item["id"]
        for name in ("carrier.txt","carrier.png"):copy(source/name,target/name)
        for path in source.glob("prefix-*.txt"):copy(path,target/path.name)
        public={k:v for k,v in data.items() if k!="entropies_bits"}
        public.update(work_id=item["work_id"],id=item["id"],payload_group=item["payload_group"],
            carrier=str((target/Path(data["carrier"]).name).relative_to(review)),
            original_report_sha256=sha256_file(record["result_path"]))
        save(str((target/"result.json").relative_to(review)),public);traces.append(public)
        members=[c for c in manifest["cases"] if c["pair_id"]==item["payload_group"]]
        for c in members:
            row=lookup.get(c["work_id"])
            count=(row.get("delivered_tokens") if item["modality"]=="text" else 2976) if row else None
            name="prefix-"+str(count)+".txt" if item["modality"]=="text" else "carrier.png"
            path=target/name;available=bool(row and row["artifact_saved"] and path.exists())
            scores=(public.get("prefix_diagnostics",{}).get(str(count),{}).get("diagnostics",{}).get("whole",{})
                    if item["modality"]=="text" else public["diagnostics"]["whole"])
            links.append(dict(work_id=c["work_id"],case=c["id"],payload_group=c["pair_id"],
                trace_id=item["id"],trace_work_id=item["work_id"],symbols=count,
                available=available,reason=None if available else "no delivered/scorable matched artifact",
                matched_artifact=str(path.relative_to(review)) if available else None,
                matched_sha256=sha256_file(path) if available else None,scores=scores if available else {},
                independent_control_replicates=0,shared_trace_counted_once=True))
    save("controls.json",traces);save("control_links.json",links)
    copy(directory/"qualification_events.jsonl",review/"completion_events.jsonl")
    copy(ROOT/"configs/v2_gpu_authorization.json",review/"v2_gpu_authorization.json")
    projection=forecast(manifest,records,directory);save("compute_projection.json",projection)
    usage=projection["usage_seconds"]
    save("budget.json",dict(usage_seconds=usage,cumulative_seconds=sum(usage.values()),
        phase_limits={s:phase_limit(s) for s in usage},v2_remaining_seconds=phase_limit("v2")-usage["v2"],
        cumulative_remaining_seconds=144000-sum(usage.values()),authorization_is_not_cost=True))
    jobs=compact_gpu(budget_state("v2")[1]);save("gpu_jobs.json",jobs)
    initialization=[]
    for job in jobs:
        path=ROOT/job["logs_retained_locally"]/"stderr.log"
        initialization.append(dict(job=job["id"],stderr_sha256=sha256_file(path),lines=[
            line for line in path.read_text(errors="replace").splitlines()
            if any(term in line for term in ("offloaded ","CUDA0 model buffer","CUDA0 KV buffer","CUDA0 compute buffer"))]))
    save("backend_initialization.json",initialization)
    preserved={p:sha256_file(ROOT/p)==h for p,h in freeze["protected_history"].items()}
    save("preservation.json",dict(protected_files=len(preserved),all_preserved=all(preserved.values()),
        changed=[p for p,ok in preserved.items() if not ok],historical_usage_unchanged=all(
            usage[s]==freeze["initial_usage"][s] for s in ("v0","v1"))))
    index={str(p.relative_to(review)):sha256_file(p) for folder in ("cases","controls") for p in (review/folder).rglob("*") if p.is_file()}
    for name in ("manifest.json","execution_freeze.json","results.jsonl","controls.json","control_links.json","gpu_jobs.json","receiver_boundaries.json"):
        index[name]=sha256_file(review/name)
    save("artifact_hashes.json",index)
    coverage=verify_public(review,write=True);save("coverage.json",coverage)
    analysis=runpy.run_path(str(ROOT/"scripts/analyze_v2.py"))["analyze"](review)
    save("acceptance.json",dict(allocation_complete=coverage["study_allocation_complete"],
        all_recovered=coverage["all_recovered"],historical_evidence_preserved=all(preserved.values()),
        protocol_code_unchanged=all(sha256_file(ROOT/"imagecalgacus"/p)==h for p,h in read_json(PRIOR/"protocol_compute_freeze.json")["protected_protocol_modules"].items()),
        execution_source_frozen=source_hash()==freeze["execution_source_hash"],
        gpu_activity_all_jobs=all(j["max_process_sm_percent"]>0 for j in jobs),
        within_v2_limit=usage["v2"]<=phase_limit("v2"),within_whole_limit=sum(usage.values())<=144000,
        frozen_analysis=manifest["analysis"]==analysis["specification"],
        no_additional_matrix=True,no_new_lossless_replays=True))
    secrets={p.read_bytes() for pattern in ("*.key","*.packet") for p in (ROOT/"runs").rglob(pattern)}
    for path in review.rglob("*"):
        if not path.is_file():continue
        raw=path.read_bytes()
        if path.suffix in {".key",".packet",".gguf",".pth",".so",".pstats"} or any(s and s in raw for s in secrets):
            raise ValueError("private material in public packet")
    print(json.dumps(dict(review=str(review),allocation_complete=coverage["study_allocation_complete"],
                          gpu_seconds=usage["v2"],whole_reserved_hours=projection["reserved_whole_hours"])))
    return 0 if coverage["study_allocation_complete"] else 2


if __name__=="__main__":
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run",type=Path);group.add_argument("--verify-public",type=Path)
    args=parser.parse_args()
    if args.run:raise SystemExit(collect(args.run))
    result=verify_public(args.verify_public)
    raise SystemExit(0 if result["study_allocation_complete"] else 2)
