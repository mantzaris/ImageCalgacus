"""CPU-only finalization of the frozen V1 allocation; no model jobs or V2 work.
Uses the existing evaluator, terminal records, GPU ledger and allowlisted copier.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from imagecalgacus.runtime import (atomic_json,sha256_file,source_hash,budget_state,phase_limit,read_profile)
from imagecalgacus.qualification import (ALLOCATION,read_json,prior_cases,trace_credits,completed_records,
    verify_binding,validate_receiver_inbox,verify_gpu_report)
from imagecalgacus.evaluate import evaluate_case,validate_allocation
from collect_v1_review import copy
from collect_v0_review import compact_gpu


def validate_record_identities(records, allocation, lossless):
    expected={}
    for kind,items in (("stego",allocation["cases"]),("trace",allocation["traces"]),("lossless",lossless)):
        for item in items:
            if item["work_id"] in expected:raise ValueError("duplicate frozen work identifier")
            expected[item["work_id"]]=(kind,item["id"])
    for work,record in records.items():
        if work not in expected or record["work_id"]!=work:
            raise ValueError("unexpected completion identifier")
        kind,name=expected[work]
        if record["kind"]!=kind or record.get("case",record.get("id"))!=name:
            raise ValueError("completion kind/name does not match frozen identity")


def collect(directory):
    directory=directory.resolve();review=ROOT/"artifacts/v1_qualification_review"
    review.mkdir(parents=True,exist_ok=True)
    allocation=read_json(ALLOCATION);freeze=read_json(directory/"freeze.json")
    baseline=read_json(ROOT/".runtime/v1_qualification/baseline.json")
    prior=prior_cases(allocation);prior.update(trace_credits(allocation))
    records=completed_records(directory,prior);bindings=read_json(directory/"packet_bindings.json")

    validate_record_identities(records,allocation,freeze["lossless"])
    events=[json.loads(line) for line in (directory/"qualification_events.jsonl").read_text().splitlines()]
    if len({e["work_id"] for e in events})!=len(events):raise ValueError("duplicate continuation events")
    expected_events={w for w,r in records.items() if not r.get("historical")}
    if {e["work_id"] for e in events}!=expected_events:raise ValueError("terminal/event reconciliation mismatch")
    for e in events:
        if sha256_file(directory/e["record"])!=e["record_sha256"]:
            raise ValueError("event terminal digest mismatch")
    cases={c["work_id"]:c for c in allocation["cases"]}
    trace_defs={t["work_id"]:t for t in allocation["traces"]}
    rows=[];public_dirs={};boundaries=[];pairs=defaultdict(list);arithmetic=[]
    def save(name,value):atomic_json(review/name,value,replace=True)
    def relative(path):return str(Path(path).resolve().relative_to(ROOT))
    for work,record in records.items():
        if record["kind"]!="stego":continue
        c=cases[work]; folder=Path(record["case_dir"]);checked=evaluate_case(c,folder)
        old=record["evaluation"]
        if (checked["exact_recovery"],checked["evidence_valid"])!=(old["exact_recovery"],old["evidence_valid"]):
            raise ValueError("terminal evidence changed")
        packet,key=verify_binding(bindings[c["pair_id"]],c)
        if checked["prepared_packet_sha256"]!=bindings[c["pair_id"]]["packet_sha256"]:
            raise ValueError("mismatched paired ciphertext")
        validate_receiver_inbox(folder/"inbox",c,key)
        receiver=read_json(folder/"receiver.json");sender=read_json(folder/"sender.json")
        declared_profile=read_profile(folder/"inbox/profile.json")
        for report in (sender,receiver):
            verify_gpu_report(report,"text" if c["direction"]=="image-to-text" else "image",declared_profile)
        if not record.get("historical") and not (
            sender["source_hash"]==record["execution_source_hash"]==freeze["execution_source_hash"]):
            raise ValueError("new group execution source differs from its freeze")
        permitted=receiver["input_roles"]==["carrier","profile","context","key"] and set(receiver["input_files"])=={p.name for p in (folder/"inbox").iterdir()}
        fresh=receiver["gpu_evidence"]["device"]["pid"]!=sender["gpu_evidence"]["device"]["pid"]
        boundaries.append(dict(case=c["id"],four_inputs=permitted,fresh_process=fresh,
            paired_packet_authenticated_against_source=True,execution_source_hash=record["execution_source_hash"],
            historical=record.get("historical",False),
            receiver_native_source_hash=receiver.get("source_hash"),
            receiver_source_identity_basis=(
                "original retained sender identity and original receiver/process/model evidence; not attributed to the new controller"
                if record.get("historical") else
                "frozen controller/group source check, recorded sender hash, fresh receiver command/PID; receiver report has no native source-hash field")))
        public=Path(record["historical_evidence"]).parent if record.get("historical") else review/"cases"/c["id"]
        if not public.exists() and record.get("historical"):public=ROOT/"artifacts/v1_2_review"/public
        if not record.get("historical"):
            for name in ("source.png","source.txt","recovered.gray","recovered.png","recovered.txt",
                         "sender.json","receiver.json","evaluation.json","attempt.json","unexpected_failure.json"):
                copy(folder/name,public/name)
            for name in ("carrier.txt","carrier.png","profile.json","prompt.txt","row.rgb"):
                copy(folder/"inbox"/name,public/name)
        public_dirs[work]=public.resolve()
        row=dict(checked,outcome_class=old.get("outcome_class",checked["outcome_class"]),
            pair_id=c["pair_id"],context_id=c["context_id"],text_filter_arm=c["text_filter_arm"],
            execution_source_hash=record["execution_source_hash"],allocation_source_hash=c["source_hash"],
            historical=record.get("historical",False),evidence_directory=relative(public))
        for field in ("source","carrier","recovered","sender_gpu_evidence","receiver_gpu_evidence"):
            if row.get(field):row[field]=relative(public/Path(row[field]).name)
        rows.append(row);pairs[c["pair_id"]].append(row)
        if record.get("arithmetic_audit"):arithmetic.append(dict(case=c["id"],**record["arithmetic_audit"]))
        if not record.get("historical"):
            public_checked=evaluate_case(c,public)
            if not public_checked["evidence_valid"] or public_checked["exact_recovery"]!=checked["exact_recovery"]:
                raise ValueError("copied public case failed revalidation")
    coverage=validate_allocation(allocation["cases"],rows)
    save("coverage.json",coverage);save("receiver_and_packet_checks.json",boundaries)
    with (review/"results.jsonl").open("w") as out:
        for row in rows:out.write(json.dumps(row,ensure_ascii=False)+"\n")
    save("failures.json",[r for r in rows if not (r["exact_recovery"] and r["carrier_complete"])])
    save("arithmetic_audits.json",dict(new_receiver_inline_audits=arithmetic,
        historical_diagnosis="artifacts/v1_1_review/arithmetic_diagnosis.json",
        diagnostic_passes_are_not_new_observations=True))
    static=[]
    for group,group_rows in sorted(pairs.items()):
        fixed={r["text_filter_arm"]:r for r in group_rows if r["direction"]=="image-to-text" and r["method"]=="fixed"}
        if fixed:
            static.append(dict(pair_id=group,paired_packet_sha256={r["prepared_packet_sha256"] for r in fixed.values()}.pop(),
                sequence=fixed.get("sequence"),static=fixed.get("static"),complete_pair=set(fixed)=={"sequence","static"}))
    save("static_pairs.json",static)
    trace_rows=[];control_links=[];threshold_audits=[]
    frozen_gate=read_profile(ROOT/"configs/v1_gated.json")["coder"]["thresholds"]
    for work,t in trace_defs.items():
        if work not in records:continue
        record=records[work];data=record["result"];folder=Path(record["result_path"]).parent
        if sha256_file(data["carrier"])!=data["carrier_sha256"]:raise ValueError("trace artifact changed")
        if read_json(record["result_path"])!=data:raise ValueError("trace report changed after terminal recording")
        for name,digest in record.get("prefix_files",{}).items():
            if sha256_file(folder/name)!=digest:raise ValueError("matched control prefix changed")
        verify_gpu_report(data,t["modality"],read_profile(ROOT/t["profile"]))
        if record.get("historical"):
            category="controls" if t["purpose"]=="control" else "calibration"
            public=ROOT/"artifacts/v1_review"/category/folder.name
        else:
            public=review/"traces"/t["id"]
            for name in ("carrier.txt","carrier.png"):copy(folder/name,public/name)
            for p in folder.glob("prefix-*.txt"):copy(p,public/p.name)
        compact={k:v for k,v in data.items() if k!="entropies_bits"}
        compact["carrier"]=relative(public/Path(data["carrier"]).name)
        compact.update(work_id=work,id=t["id"],context_id=t["context_id"],purpose_detail=t["purpose_detail"],
                       source_result_sha256=sha256_file(record["result_path"]),historical=record.get("historical",False))
        trace_rows.append(compact)
        if not record.get("historical"):atomic_json(public/"result.json",compact,replace=True)
        entropies=data["entropies_bits"];threshold=frozen_gate[t["modality"]]["value"]
        if t["purpose"]=="ordinary":
            threshold_audits.append(dict(id=t["id"],context=t["context_id"],modality=t["modality"],n=len(entropies),
                frozen_threshold=threshold,strictly_above=sum(e>threshold for e in entropies),
                mean_entropy_bits=sum(entropies)/len(entropies),threshold_unchanged=True,
                calibration_only_if_historical=record.get("historical",False)))
        else:
            targets=list(pairs.get(t["payload_group"],[]))
            # Preserve original cross-payload pilot associations, without adding controls.
            extra="I5-prompt1" if t["id"]=="control-text-4301" else "T3-row1" if t["id"]=="control-image-4302" else None
            if extra:targets += [r for r in pairs.get(extra,[]) if r["historical"]]
            for row in targets:
                n=row.get("delivered_tokens") if t["modality"]=="text" else 2976
                prefix=public/("prefix-"+str(n)+".txt" if t["modality"]=="text" else "carrier.png")
                # A full-length text control is itself the matched 2048-token prefix.
                if n==2048 and not prefix.exists():prefix=public/"carrier.txt"
                available=prefix.exists()
                if not available and not record.get("historical"):
                    raise ValueError("new allocated control is missing its matched prefix")
                reason=None if available else "historical trace did not retain this later arm's matched prefix; no extra model pass or invented score"
                control_links.append(dict(trace_id=t["id"],trace_work_id=work,work_id=row["work_id"],case=row["case"],
                    payload_group=row["pair_id"],symbols=n,matched_artifact=relative(prefix) if available else None,
                    matched_sha256=sha256_file(prefix) if available else None,available=available,reason=reason,
                    inline_score_available=t["modality"]=="image" or str(n) in data.get("prefix_diagnostics",{}),
                    independent_control_replicates=0,shared_trace_counted_once=True,
                    primary_frozen_association=t["payload_group"]==row["pair_id"]))
    save("ordinary_and_controls.json",trace_rows);save("control_links.json",control_links)
    allocated_control_groups={t["payload_group"] for t in trace_defs.values() if t["purpose"]=="control"}
    save("control_coverage.json",dict(independent_allocated_traces=48,
        completed_independent_traces=sum(r["purpose"]=="control" for r in trace_rows),
        unavailable_matched_prefixes=[r for r in control_links if not r["available"]],
        groups_outside_control_allocation=[dict(pair_id=g,reason="outside the frozen 12 control groups per modality/context; no additional control allocated")
            for g in sorted({c["pair_id"] for c in cases.values()}-allocated_control_groups)],
        historical_extra_associations_are_not_additional_replicates=True))
    save("threshold_audit.json",dict(frozen_thresholds=frozen_gate,traces=threshold_audits,recalibrated=False))
    lossless=[]
    for item in freeze["lossless"]:
        if item["work_id"] not in records:continue
        record=dict(records[item["work_id"]]);target=review/"lossless"/record["id"]
        # Recheck current files, not only the original terminal's booleans.
        from PIL import Image
        original=Path(record["original"]);rewritten=Path(record["rewritten"])
        case=cases[item["parent_work_id"]]
        if (sha256_file(original)!=record["original_file_sha256"] or
            sha256_file(rewritten)!=record["rewritten_file_sha256"]):
            raise ValueError("lossless artifact changed")
        with Image.open(original) as before,Image.open(rewritten) as after:
            pixels_ok=(before.mode==after.mode=="RGB" and before.size==after.size==(32,31)
                       and before.tobytes()==after.tobytes() and not after.info
                       and hashlib.sha256(after.tobytes()).hexdigest()==record["pixel_sha256"])
        receiver=read_json(record["report"])
        _,key=verify_binding(bindings[case["pair_id"]],case)
        validate_receiver_inbox(rewritten.parent,case,key)
        verify_gpu_report(receiver,"image",read_profile(rewritten.parent/"profile.json"))
        parent_receiver=read_json(Path(records[item["parent_work_id"]]["case_dir"])/"receiver.json")
        fresh=receiver["gpu_evidence"]["device"]["pid"]!=parent_receiver["gpu_evidence"]["device"]["pid"]
        equal=Path(record["recovered"]).read_bytes()==(ROOT/case["source"]).read_bytes()
        if not (pixels_ok and equal and fresh and receiver==record["receiver"] and
                receiver["packet_complete"] and receiver["authenticated"] and receiver["carrier_complete"]):
            raise ValueError("lossless CPU revalidation failed")
        record["final_cpu_revalidation"]=dict(pixels_equal=pixels_ok,source_equal=equal,
            receiver_report_unchanged=True,fresh_receiver_process=fresh,permitted_inputs_only=True)
        for field in ("rewritten","recovered","report"):
            source=Path(record[field]);copy(source,target/source.name);record[field]=relative(target/source.name)
        case=cases[item["parent_work_id"]]
        record["original"]=relative(public_dirs[item["parent_work_id"]]/"carrier.png")
        for name in ("profile.json","row.rgb"):
            copy(Path(records[item["work_id"]]["rewritten"]).parent/name,target/name)
        lossless.append(record)
    save("lossless_png.json",dict(selection=freeze["lossless"],results=lossless,
        not_additional_stego_observations=True,extra_main_study_lossless_jobs=0))
    # Strict literal UTF-8 file roundtrips, no tokenizer/model/normalization pass.
    utf8=[];roundtrips=directory/"utf8_roundtrips";roundtrips.mkdir(exist_ok=True)
    for row in rows:
        if row["direction"]!="image-to-text" or not row["artifact_saved"]:continue
        original=ROOT/row["carrier"];raw=original.read_bytes();raw.decode("utf-8",errors="strict")
        output=roundtrips/(row["work_id"]+".txt")
        if output.exists() and output.read_bytes()!=raw:raise ValueError("roundtrip output changed")
        if not output.exists():output.write_bytes(raw)
        utf8.append(dict(case=row["case"],work_id=row["work_id"],carrier=row["carrier"],
            sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),strict_utf8=True,save_load_equal=output.read_bytes()==raw,
            tokenization_drift=row["serialization"].get("tokenization_drift",False)))
    save("utf8_lossless.json",utf8)
    used,ledger=budget_state("v1");v0,_=budget_state("v0")
    ledger_path=ROOT/".runtime/v1/gpu_budget.jsonl"
    old_bytes=ledger_path.read_bytes()[:baseline["v1_ledger_bytes"]]
    ledger_preserved=hashlib.sha256(old_bytes).hexdigest()==baseline["v1_ledger_sha256"]
    baseline_ids={r["id"] for r in map(json.loads,old_bytes.splitlines())}
    jobs=compact_gpu(ledger);new_jobs=[j for j in jobs if j["id"] not in baseline_ids]
    save("gpu_jobs.json",new_jobs)
    init=[]
    for job in new_jobs:
        path=ROOT/job["logs_retained_locally"]/"stderr.log"
        init.append(dict(job=job["id"],stderr_sha256=sha256_file(path),initialization_lines=[
            line for line in path.read_text(errors="replace").splitlines()
            if any(term in line for term in ("offloaded ","CUDA0 model buffer","CUDA0 KV buffer","CUDA0 compute buffer"))]))
    save("backend_initialization.json",init)
    protected={name:sha256_file(ROOT/name)==digest for name,digest in baseline["protected_files"].items()}
    save("preservation.json",dict(protected_count=len(protected),all_preserved=all(protected.values()),
        changed=[n for n,p in protected.items() if not p],historical_v1_ledger_prefix_preserved=ledger_preserved,
        v0_seconds_unchanged=v0==baseline["v0_seconds"]))
    forecast=runpy.run_path(str(ROOT/"scripts/project_v1_compute.py"))["completion_forecast"](directory,allocation,freeze,records)
    save("compute_projection.json",forecast)
    cells=defaultdict(list)
    for observation in forecast["observations"]:
        cells[(observation["direction"],observation["method"],observation["context"],observation["arm"])].append(observation)
    row_by_work={r["work_id"]:r for r in rows}
    timing_summary=[]
    for key,items in sorted(cells.items(),key=str):
        details=[row_by_work[r["work_id"]] for r in items]
        metrics={}
        for field in ("charged_encode_seconds","charged_decode_seconds","charged_pair_seconds",
                      "encode_seconds","decode_seconds","cold_load_seconds","other_process_seconds"):
            values=[r[field] for r in items]
            metrics[field]=dict(mean=sum(values)/len(values),minimum=min(values),maximum=max(values))
        timing_summary.append(dict(direction=key[0],method=key[1],context=key[2],arm=key[3],n=len(items),
            outcomes=dict(Counter(r["outcome_class"] for r in details)),
            exact_recoveries=sum(r["exact_recovery"] for r in details),
            metrics=metrics,work_ids=[r["work_id"] for r in items],
            observed_packet_bits=[dict(case=r["case"],packet_bits_recovered=r.get("packet_bits_recovered"),
                packet_complete=r["packet_complete"],receiver_packet_complete=r.get("receiver_packet_complete"),
                carrier_complete=r["carrier_complete"],authenticated=r["authenticated"],
                failure_stage=r.get("failure_stage"),failure_reason=r.get("failure_reason")) for r in details]))
    save("method_context_summary.json",dict(cells=timing_summary,descriptive_only=True,
        failed_attempt_costs_included=True,payload_context_groups=80,unique_payloads=40,
        unique_payloads_per_direction=20,contexts_per_payload=2,stego_work_units=152,
        independence_note="Repeated contexts and coding arms are not independent payload replicates."))
    save("budget.json",dict(v0_seconds=v0,v1_seconds=used,checkpoint_seconds=used-freeze["initial_v1_seconds"],
        v0_limit_seconds=phase_limit("v0"),v1_limit_seconds=phase_limit("v1"),v1_remaining_seconds=phase_limit("v1")-used,
        cumulative_seconds=v0+used,whole_project_limit_seconds=144000,authorization_is_not_a_cost=True))
    copy(directory/"freeze.json",review/"execution_freeze.json")
    copy(ROOT/"configs/v1_gpu_authorization.json",review/"v1_gpu_authorization.json")
    copy(ROOT/".runtime/v1_qualification/accepted_revalidation.json",review/"accepted_revalidation.json")
    copy(directory/"qualification_events.jsonl",review/"qualification_events.jsonl")
    # Public terminal summaries exclude private directories and detailed audit traces.
    save("work_records.json",[dict(work_id=w,kind=r["kind"],case=r.get("case",r.get("id")),
        historical=r.get("historical",False),execution_source_hash=r["execution_source_hash"])
        for w,r in records.items()])
    tests=subprocess.run([sys.executable,"-B","-m","unittest","discover","-s","tests","-v"],cwd=ROOT,text=True,capture_output=True)
    (review/"cpu_tests.txt").write_text(tests.stdout+tests.stderr)
    save("cpu_tests.json",dict(command=[sys.executable,"-B","-m","unittest","discover","-s","tests","-v"],exit_code=tests.returncode))
    sequence=[r for r in rows if r["method"]=="fixed" and r["direction"]=="image-to-text" and r["text_filter_arm"]=="sequence"]
    png=[r for r in rows if r["method"]=="fixed" and r["direction"]=="text-to-image"]
    static_rows=[r for r in rows if r["text_filter_arm"]=="static"]
    timing=[r for r in rows if r["method"]!="fixed"]
    conditions=dict(allocation_complete=coverage["allocation_complete"],
        sequence_40_exact=len(sequence)==40 and all(r["exact_recovery"] and r["carrier_complete"] for r in sequence),
        fixed_png_40_exact=len(png)==40 and all(r["exact_recovery"] and r["carrier_complete"] for r in png),
        static_40_accounted=len(static_rows)==40 and all(r["outcome_class"] in {"exact_recovery","static_tokenization_drift_failure"} for r in static_rows),
        timing_32_accounted=len(timing)==32 and all(r["evidence_valid"] and r["terminal"] for r in timing),
        ordinary_16_complete=sum(r["purpose"]=="calibration" for r in trace_rows)==16,
        controls_48_complete=sum(r["purpose"]=="control" for r in trace_rows)==48,
        lossless_20_exact=len(lossless)==20 and all(r["pixels_preserved"] and r["exact_recovery"] for r in lossless),
        utf8_checks_complete=len(utf8)==sum(c["direction"]=="image-to-text" for c in allocation["cases"]) and all(r["save_load_equal"] for r in utf8),
        receiver_boundaries=all(r["four_inputs"] and r["fresh_process"] for r in boundaries),
        original_evidence_preserved=all(protected.values()) and ledger_preserved and v0==baseline["v0_seconds"],
        gpu_activity_all_new_jobs=bool(new_jobs) and all(j["max_process_sm_percent"]>0 for j in new_jobs),
        cpu_tests_pass=tests.returncode==0,execution_code_frozen=source_hash()==freeze["execution_source_hash"],
        stage_budget_respected=used<=phase_limit("v1"),whole_forecast_fits=forecast["fits_whole_project"])
    save("acceptance.json",dict(v1_qualified=all(conditions.values()),conditions=conditions,
        counts=dict(sequence=len(sequence),fixed_png=len(png),static=len(static_rows),timing=len(timing),
                    traces=len(trace_rows),lossless=len(lossless)),
        arithmetic_text_complete=sum(r["method"]=="arithmetic" and r["direction"]=="image-to-text" and r["exact_recovery"] and r["carrier_complete"] for r in rows),
        v2_authorized=False))
    save("protocol_compute_freeze.json",dict(execution_package_hash=freeze["execution_source_hash"],
        historical_revision=freeze["source_revision"],allocation_sha256=sha256_file(ALLOCATION),
        source_context_manifest_sha256=sha256_file(ROOT/"data/qualification_v1/manifest.json"),
        profiles={p:sha256_file(ROOT/p) for p in sorted({c["profile"] for c in allocation["cases"]})},
        protected_protocol_modules=freeze["protected_contract_files"],main_stego_units=120,main_shared_controls=40,
        one_context_per_direction=True,main_contexts={"image-to-text":"prompt1","text-to-image":"row1"},
        main_text_filter_arm="sequence",packet_bytes=292,text_carrier_cap_tokens=2048,
        text_completion_tokens=32,image_carrier={"width":32,"height":31,"mode":"RGB","channels_per_pixel":3,"pixels":992,"channel_values":2976},
        shared_image_prefix_rows=1,arithmetic_framing="A1",arithmetic_precision_bits=32,
        heldout_carriers_generated=False,thresholds=frozen_gate,
        remaining_condition_names=[k for k,v in conditions.items() if not v],
        reporting_only_script=str(Path(__file__).relative_to(ROOT)),reporting_script_sha256=sha256_file(__file__),
        prior_reviews=["artifacts/v0_review","artifacts/v1_review","artifacts/v1_1_review","artifacts/v1_2_review"]))
    # Byte-level secret exclusion; never print secrets or include raw arithmetic traces.
    secrets={p.read_bytes() for pattern in ("*.key","*.packet") for p in (ROOT/"runs").rglob(pattern)}
    for p in review.rglob("*"):
        if p.is_file():
            raw=p.read_bytes()
            if p.suffix in {".key",".packet",".gguf",".pth",".so"} or any(secret and secret in raw for secret in secrets):
                raise ValueError("forbidden private material in review output")
    progress=read_json(directory/"progress.json")
    progress["coverage"]["v1_qualified"]=all(conditions.values())
    progress["final_cpu_review"]=relative(review/"acceptance.json")
    atomic_json(directory/"progress.json",progress,replace=True)
    save("latest_internal_checkpoint.json",dict(progress,checkpoint_status="final_cpu_reconciled"))
    print(json.dumps(dict(review=str(review),v1_qualified=all(conditions.values()),
                         unmet=[k for k,v in conditions.items() if not v],v1_seconds=used)))
    return 0 if all(conditions.values()) else 2

def verify_public(review):
    """Recheck public source equality and coverage; no keys, models or private logs."""
    review=review.resolve();allocation=read_json(ALLOCATION)
    cases={c["work_id"]:c for c in allocation["cases"]}
    records=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    rows=[]
    for record in records:
        work=record["work_id"]
        if work not in cases or record["case"]!=cases[work]["id"]:
            raise ValueError("unexpected public work identity")
        checked=evaluate_case(cases[work],ROOT/record["evidence_directory"])
        for field in ("exact_recovery","evidence_valid","carrier_complete","authenticated","source_equal"):
            if checked[field]!=record[field]:raise ValueError("public evidence changed: "+record["case"])
        rows.append(checked)
    summary=validate_allocation(allocation["cases"],rows)
    summary["verification_scope"]="public CPU source equality and allocation; not key-dependent GPU replay"
    print(json.dumps(summary))
    return 0 if summary["allocation_complete"] else 2


if __name__=="__main__":
    p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--run",type=Path);group.add_argument("--verify-public",type=Path)
    args=p.parse_args()
    raise SystemExit(verify_public(args.verify_public) if args.verify_public else collect(args.run))
