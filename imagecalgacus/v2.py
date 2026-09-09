"""Bounded prospective V2 only: 40 frozen payload groups, three methods, shared controls.
Reuses V1 transport/terminal/accounting helpers; no new coder or model behavior.
"""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from .runtime import (ROOT,atomic_json,canonical_hash,sha256_file,source_hash,read_profile,
                      budget_state,phase_limit,apply_v2_allowance,reconcile_interrupted)
from .qualification import (read_json,verify_binding,completed_records,recover_terminal_events,
    execute_case,execute_trace,job_limit,verify_gpu_report,validate_receiver_inbox,sender_state)
from .evaluate import evaluate_case,validate_allocation
from .packet import NewRun
from .sender import read_source

MANIFEST=ROOT/"configs/v2_prospective.json"
SOURCES=ROOT/"data/qualification_v1/manifest.json"
PRIOR=ROOT/"artifacts/v1_qualification_review"
METHODS=("fixed","gated","arithmetic")
DIRECTIONS=("image-to-text","text-to-image")
ANALYSIS={
    "questions":["artifact exact recovery","gating rate/overhead/distortion tradeoff","comparison with framed A1 including failures"],
    "independent_unit":"payload/context group; 20 per direction, not 60 methods",
    "bootstrap_replicates":2000,"confidence":0.95,"bootstrap_seed":2026090901,
    "bootstrap":"percentile; resample whole groups within image class or UTF-8 length band; carry methods and owned shared controls together",
    "recovery_interval":"two-sided Clopper-Pearson exact binomial, including 0/n and n/n; Bernoulli working-model interval for a small fixed stratified sample",
    "paired_binary_boundary_bound":"difference of 97.5% marginal Clopper-Pearson intervals (Bonferroni conservative); also retain paired grouped bootstrap",
    "paired_metrics":["exact_complete","exact_goodput_bits_per_symbol","charged_pair_seconds","whole_surprisal_bits","whole_log_rank"],
    "paired_order":[["gated","fixed"],["arithmetic","fixed"],["arithmetic","gated"]],
    "goodput":"incomplete or unauthenticated transmissions have zero exact goodput; packet-prefix progress is separate",
    "scores":{"surprisal_bits_mean":"higher means stego","log_rank_mean":"higher means stego"},
    "score_scope":"whole delivered carrier; model/context-aware observer; no packet-boundary features or extra scoring passes",
    "auc":"empirical pairwise wins plus half ties; matched ordinary controls; include failed delivered carriers when scorable",
    "duplicates":"deduplicate identical control artifact hashes within each direction/method cell; lowest frozen group ordinal owns it; retain other links without extra negatives; repeated bootstrap draws retain owner multiplicity",
    "unscorable":"explicit missing carrier/control/whole score; never replace or infer scores",
    "plots":["six-cell recovery with boundary-aware intervals","whole-carrier score AUC with grouped intervals"],
    "no_label_selected_score_direction":True,"no_detector_training":True,"lossless_replays_already_satisfied":20,
}


def build_manifest():
    sources=read_json(SOURCES)
    contexts={c["id"]:c for c in sources["contexts"]}
    payloads={p["id"]:p for p in sources["payloads"] if p["split"]=="heldout"}
    profiles={m:read_profile(ROOT/("configs/v1_"+m+".json")) for m in METHODS}
    source_identity=source_hash();cases=[];controls=[];groups=[]
    for index in range(1,21):
        for prefix,direction,context,modality in (("HI","image-to-text","prompt1","text"),("HT","text-to-image","row1","image")):
            p=payloads[prefix+str(index)];ctx=contexts[context];pair=p["id"]+"-"+context
            source="data/qualification_v1/"+p["source"]
            if sha256_file(ROOT/source)!=p["file_sha256"]:raise ValueError("frozen source file changed")
            raw=read_source(ROOT/source,direction).data
            if hashlib.sha256(raw).hexdigest()!=p["source_sha256"]:raise ValueError("frozen payload changed")
            if sha256_file(SOURCES.parent/ctx["path"])!=ctx["sha256"]:raise ValueError("frozen context changed")
            stratum="class-"+str(p["provenance"]["class"]) if modality=="text" else "32-64" if p["bytes"]<=64 else "65-128"
            members=[]
            for method in METHODS:
                profile=profiles[method]
                definition=dict(split="heldout",payload_id=p["id"],direction=direction,context_sha256=ctx["sha256"],
                    source_sha256=p["source_sha256"],method=method,profile_id=canonical_hash(profile),replicate=0,
                    text_filter_arm="sequence" if modality=="text" else None)
                case=dict(definition,id=pair+"-"+method,work_id=canonical_hash(definition),pair_id=pair,
                    source=source,source_file_sha256=p["file_sha256"],source_bytes=p["bytes"],context_id=context,
                    context="data/qualification_v1/"+ctx["path"],profile="configs/v1_"+method+".json",
                    model_id=profile[modality]["model_sha256"],source_hash=source_identity,
                    sampling_seed=profile["completion_seed"],stratum=stratum,status="pending")
                cases.append(case);members.append(case["work_id"])
            seed_definition=dict(allocation_seed=2026090900,split="heldout",direction=direction,
                payload_id=p["id"],context_sha256=ctx["sha256"],purpose="control")
            seed=int(canonical_hash(seed_definition)[:16],16)
            definition=dict(split="heldout",purpose="control",modality=modality,payload_group=pair,
                context_sha256=ctx["sha256"],seed=seed,profile_id=canonical_hash(profiles["fixed"]),
                symbols_rule="maximum realized delivered text length" if modality=="text" else "full 2976 channel values")
            control=dict(definition,id="control-"+pair,work_id=canonical_hash(definition),context_id=context,
                context="data/qualification_v1/"+ctx["path"],profile="configs/v1_fixed.json",
                symbols=2048 if modality=="text" else 2976,status="pending",
                purpose_detail="one ordinary trace; matched prefixes shared by methods, not independent replicates",
                seed_definition=seed_definition)
            controls.append(control)
            groups.append(dict(id=pair,ordinal=len(groups),payload_id=p["id"],direction=direction,stratum=stratum,
                work_ids=members,control_work_id=control["work_id"]))
    result=dict(schema="bounded-prospective-v2",source_manifest=str(SOURCES.relative_to(ROOT)),
        source_manifest_sha256=sha256_file(SOURCES),source_hash=source_identity,
        accepted_qualification_revision="29d2ca2ff7e0cdf6f3a6c000d1ad7948ac8a7bc3",
        cases=cases,controls=controls,groups=groups,analysis=ANALYSIS,
        order_rule="HI1/prompt1 then HT1/row1, then ascending numeric index alternating directions; fixed/gated/arithmetic followed by shared control",
        sampling_policy="unchanged profile completion_seed=3001 for stego; independent control seed from recorded purpose/group hash; cryptography uses OS randomness only",
        packet_policy="one fresh key and one immutable sealed packet per group, shared across all three methods; no re-encryption on resume",
        failure_policy="capacity is terminal; unexpected fixed recovery/identity/infrastructure failures pause; no rerolls or replacement sources",
        text_controls_rule="one trace to longest realized delivered carrier length; all required method prefixes retained inline",
        units=dict(stego=120,independent_control_traces=40,payload_groups_per_direction=20,extra_lossless_replays=0))
    validate_manifest(result)
    return result


def validate_manifest(manifest):
    if manifest["units"]!=dict(stego=120,independent_control_traces=40,payload_groups_per_direction=20,extra_lossless_replays=0):
        raise ValueError("not the bounded prospective allocation")
    cases=manifest["cases"];controls=manifest["controls"];groups=manifest["groups"]
    source_manifest=read_json(ROOT/manifest["source_manifest"])
    if sha256_file(ROOT/manifest["source_manifest"])!=manifest["source_manifest_sha256"]:
        raise ValueError("source selection identity changed")
    payloads={(p["id"],p["direction"]):p for p in source_manifest["payloads"] if p["split"]=="heldout"}
    contexts={c["id"]:c for c in source_manifest["contexts"]}
    for case in cases:
        p=payloads.get((case["payload_id"],case["direction"]))
        context="prompt1" if case["direction"]=="image-to-text" else "row1"
        if not p or case["source_sha256"]!=p["source_sha256"] or case["source"]!="data/qualification_v1/"+p["source"]:
            raise ValueError("case not in frozen held-out selection")
        if case["context_id"]!=context or case["context_sha256"]!=contexts[context]["sha256"]:
            raise ValueError("prospective context changed")
        definition={key:case[key] for key in ("split","payload_id","direction","context_sha256",
            "source_sha256","method","profile_id","replicate","text_filter_arm")}
        if canonical_hash(definition)!=case["work_id"]:raise ValueError("unstable scientific work identifier")
        if case["replicate"]!=0:raise ValueError("extra replicate")
        profile=read_profile(ROOT/case["profile"])
        modality="text" if case["direction"]=="image-to-text" else "image"
        if canonical_hash(profile)!=case["profile_id"] or profile["coder"]["method"]!=case["method"] or profile[modality]["model_sha256"]!=case["model_id"]:
            raise ValueError("prospective profile/model identity")
        if sha256_file(ROOT/case["context"])!=case["context_sha256"] or sha256_file(ROOT/case["source"])!=case["source_file_sha256"]:
            raise ValueError("prospective source/context bytes changed")
    if len(cases)!=120 or len(controls)!=40 or len(groups)!=40:raise ValueError("wrong allocation size")
    expected={c["work_id"]:c for c in cases}
    if len(expected)!=120 or len({c["id"] for c in cases})!=120:raise ValueError("duplicate scientific unit")
    trace_ids={t["work_id"] for t in controls}
    if len(trace_ids)!=40 or trace_ids&set(expected):raise ValueError("duplicate control identity")
    covered=[];linked=[]
    for group in groups:
        members=[expected[w] for w in group["work_ids"]]
        if len(members)!=3 or {c["method"] for c in members}!=set(METHODS):raise ValueError("incomplete method pairing")
        for field in ("pair_id","source_sha256","context_sha256","direction","payload_id"):
            if len({c[field] for c in members})!=1:raise ValueError("mismatched group pairing")
        if members[0]["pair_id"]!=group["id"]:raise ValueError("wrong group")
        if any(c["split"]!="heldout" or c["text_filter_arm"]=="static" for c in members):raise ValueError("out-of-scope arm/split")
        covered+=group["work_ids"];linked.append(group["control_work_id"])
    if len(set(covered))!=120 or set(covered)!=set(expected) or set(linked)!=trace_ids or len(set(linked))!=40:
        raise ValueError("duplicate or missing group/control coverage")
    if Counter(c["direction"] for c in cases)!=Counter({d:60 for d in DIRECTIONS}):raise ValueError("direction allocation")
    if len({t["seed"] for t in controls})!=40:raise ValueError("control seed collision")


def pending_group(group,records):
    return [w for w in group["work_ids"]+[group["control_work_id"]] if w not in records]


def realized_control(item,group,records):
    members=[records[w]["evaluation"] for w in group["work_ids"]]
    if any(not r["terminal"] or not r["evidence_valid"] for r in members):raise ValueError("control before valid terminal group")
    if item["modality"]=="text":
        lengths=[r["delivered_tokens"] for r in members if r["artifact_saved"]]
        if not lengths:raise ValueError("no carrier to match; record unavailable rather than invent control")
        return dict(item,symbols=max(lengths))
    return dict(item)


def prepare(directory):
    directory=Path(directory).resolve()
    apply_v2_allowance()
    if not read_json(PRIOR/"acceptance.json")["v1_qualified"]:raise ValueError("V1 not accepted")
    old=read_json(PRIOR/"protocol_compute_freeze.json")
    if sha256_file(SOURCES)!=old["source_context_manifest_sha256"]:raise ValueError("source/context manifest changed")
    for name,digest in old["protected_protocol_modules"].items():
        if sha256_file(ROOT/"imagecalgacus"/name)!=digest:raise ValueError("protocol computation changed before V2")
    for name,digest in old["profiles"].items():
        if sha256_file(ROOT/name)!=digest:raise ValueError("frozen profile changed")
    if not MANIFEST.exists():atomic_json(MANIFEST,build_manifest())
    manifest=read_json(MANIFEST);validate_manifest(manifest)
    if (directory/"freeze.json").exists():
        freeze=read_json(directory/"freeze.json")
        if sha256_file(MANIFEST)!=freeze["manifest_sha256"]:raise ValueError("prospective manifest changed")
        bindings=read_json(directory/"packet_bindings.json")
        for c in manifest["cases"]:verify_binding(bindings[c["pair_id"]],c)
        return manifest,freeze
    if directory.exists() and any(directory.iterdir()):raise RuntimeError("incomplete CPU preparation: preserve and inspect, no resealing")
    # Historical evidence and private keys/packets: hash, never copy to public output.
    protected={}
    for folder in ("artifacts","data/qualification_v1","runs"):
        for p in (ROOT/folder).rglob("*"):
            if p.is_file() and not p.is_relative_to(directory) and "v2_review" not in p.parts:
                protected[str(p.relative_to(ROOT))]=sha256_file(p)
    for p in (ROOT/"notes").glob("v[01]*.md"):
        if p.name!="v1_test_portability.md":protected[str(p.relative_to(ROOT))]=sha256_file(p)
    for stage in ("v0","v1"):
        from .runtime import budget_root
        p=budget_root(stage)/"gpu_budget.jsonl"
        protected[str(p.relative_to(ROOT))]=sha256_file(p)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    for name in ("cases","traces","groups","terminals","checkpoints"):(directory/name).mkdir()
    bindings={};case_by_work={c["work_id"]:c for c in manifest["cases"]}
    for group in manifest["groups"]:
        c=case_by_work[group["work_ids"][0]];folder=directory/"groups"/group["id"]
        new=NewRun(folder);packet=folder/"sealed.packet"
        with packet.open("xb") as stream:
            stream.write(new.encrypt(read_source(ROOT/c["source"],c["direction"])));stream.flush();os.fsync(stream.fileno())
        bindings[group["id"]]=dict(packet=str(packet),key=str(folder/"run.key"),packet_sha256=sha256_file(packet),
            source_sha256=c["source_sha256"],context_sha256=c["context_sha256"])
        verify_binding(bindings[group["id"]],c)
    atomic_json(directory/"packet_bindings.json",bindings)
    files=[MANIFEST,SOURCES,ROOT/"configs/v2_gpu_authorization.json",ROOT/"pyproject.toml"]
    files += [ROOT/c[f] for c in manifest["cases"] for f in ("profile","context","source")]
    files += [p for folder in ("imagecalgacus","scripts","tests") for p in (ROOT/folder).rglob("*.py")]
    freeze=dict(source_revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        execution_source_hash=source_hash(),manifest_sha256=sha256_file(MANIFEST),analysis_sha256=canonical_hash(manifest["analysis"]),
        files={str(p.relative_to(ROOT)):sha256_file(p) for p in sorted(set(files))},
        initial_usage={s:budget_state(s)[0] for s in ("v0","v1","v2")},
        protected_history=protected,order=[g["id"] for g in manifest["groups"]],
        protocol_change=False,first_checkpoint_groups=[g["id"] for g in manifest["groups"][:2]],
        created_utc=datetime.now(timezone.utc).isoformat())
    atomic_json(directory/"freeze.json",freeze)
    return manifest,freeze


def job_costs(records):
    _,ledger=budget_state("v2");finished=[r for r in ledger if r["event"]=="finished"]
    def cost(label):return sum(r["elapsed_seconds"] for r in finished if r["id"].endswith("-prospective-"+label))
    observations=[];controls=[]
    for record in records.values():
        if record["kind"]=="stego":
            r=record["evaluation"];enc=cost(r["case"]+"-encode");dec=cost(r["case"]+"-decode")
            if not enc or not dec:raise ValueError("missing charged sender/receiver")
            generation=r.get("encode_seconds") or 0.;replay=r.get("decode_seconds") or 0.
            loads=(r.get("sender_load_seconds") or 0.)+(r.get("receiver_load_seconds") or 0.)
            observations.append(dict(work_id=r["work_id"],case=r["case"],direction=r["direction"],method=r["method"],
                charged_encode_seconds=enc,charged_decode_seconds=dec,charged_pair_seconds=enc+dec,
                encode_seconds=generation,decode_seconds=replay,cold_load_seconds=loads,
                other_occupied_seconds=enc+dec-generation-replay-loads))
        elif record["kind"]=="trace":
            r=record["result"];charged=cost(record["id"])
            if not charged:raise ValueError("missing control charge")
            controls.append(dict(work_id=record["work_id"],id=record["id"],modality=r["modality"],
                symbols=r["symbols"],charged_seconds=charged,generation_seconds=r["generation_seconds"],
                cold_load_seconds=r["cold_load_seconds"],
                other_occupied_seconds=charged-r["generation_seconds"]-r["cold_load_seconds"]))
    return observations,controls


def forecast(manifest,records,directory=None):
    old=read_json(PRIOR/"compute_projection.json")
    observations,controls=job_costs(records);cells={};remaining=0.
    bindings=read_json(directory/"packet_bindings.json") if directory is not None else {}
    for direction in DIRECTIONS:
        for method in METHODS:
            measured=[r for r in observations if (r["direction"],r["method"])==(direction,method)]
            historical=old["main_method_context_cells"][direction+"/"+method]["mean"]
            fields=("charged_encode_seconds","charged_decode_seconds")
            # A single new group cannot optimistically lower the established estimate.
            means={f:(sum(r[f] for r in measured)/len(measured) if len(measured)>=2 else
                      max(historical[f],measured[0][f]) if measured else historical[f]) for f in fields}
            pending=[c for c in manifest["cases"] if c["work_id"] not in records and
                     (c["direction"],c["method"])==(direction,method)]
            roles={"encode":0,"decode":0}
            for c in pending:
                state=sender_state(directory/"cases"/c["id"],c,bindings[c["pair_id"]]) if directory is not None else "unstarted"
                if state not in {"receiver_pending","evaluate_pending"}:roles["encode"]+=1
                if state!="evaluate_pending":roles["decode"]+=1
            seconds=roles["encode"]*means["charged_encode_seconds"]+roles["decode"]*means["charged_decode_seconds"]
            remaining+=seconds
            cells[direction+"/"+method]=dict(new_n=len(measured),pending=len(pending),remaining_model_jobs=roles,mean=means,
                seconds=seconds,assumption="same-method/context V1 mean until >=2 prospective measurements; one-case increases retained")
    control_cells={}
    for modality,context in (("text","prompt1"),("image","row1")):
        measured=[r for r in controls if r["modality"]==modality]
        historical=[r["charged_seconds"] for r in old["trace_observations"] if
                    (r["purpose"],r["modality"],r["context"])==("control",modality,context)]
        prior=sum(historical)/len(historical)
        # Text cap remains a conservative proxy if a realized control was shorter.
        estimates=[r["charged_seconds"]*max(1.,(2048/r["symbols"])**2) if modality=="text" else r["charged_seconds"] for r in measured]
        mean=sum(estimates)/len(estimates) if len(estimates)>=2 else max([prior]+estimates)
        pending=sum(t["work_id"] not in records and t["modality"]==modality for t in manifest["controls"])
        remaining+=pending*mean
        control_cells[modality]=dict(new_n=len(measured),pending=pending,seconds=pending*mean,
            mean_inclusive_seconds=mean,assumption="text full-cap proxy; realized shorter controls use conservative squared-length extrapolation")
    usage={s:budget_state(s)[0] for s in ("v0","v1","v2")};spent=sum(usage.values())
    subtotal=spent+remaining;reserve=.25*subtotal
    return dict(usage_seconds=usage,v2_limit_seconds=phase_limit("v2"),v2_remaining_seconds=phase_limit("v2")-usage["v2"],
        whole_limit_seconds=144000,whole_actual_remaining_seconds=144000-spent,
        observations=observations,control_observations=controls,cells=cells,control_cells=control_cells,
        pending_stego=sum(c["work_id"] not in records for c in manifest["cases"]),
        pending_controls=sum(t["work_id"] not in records for t in manifest["controls"]),
        remaining_prospective_seconds=remaining,phase_headroom_seconds=.25*remaining,
        fits_phase=usage["v2"]+1.25*remaining<=phase_limit("v2"),
        subtotal_seconds=subtotal,reserve_once_seconds=reserve,reserved_whole_hours=(subtotal+reserve)/3600,
        fits_whole=subtotal+reserve<=144000,extra_scoring_seconds=0,extra_lossless_jobs=0,
        note="authorization is not cost; spent failures retained; one reserve, with phase headroom testing the same reserve")


def reconcile_evidence(manifest,records,bindings):
    expected={c["work_id"]:c for c in manifest["cases"]}
    expected.update({t["work_id"]:t for t in manifest["controls"]})
    _,ledger=budget_state("v2")
    for work,r in records.items():
        if work not in expected or r.get("case",r.get("id"))!=expected[work]["id"]:raise ValueError("unexpected completed work")
        c=expected[work]
        reports=[]
        if r["kind"]=="stego":
            folder=Path(r["case_dir"]);checked=evaluate_case(c,folder)
            if not checked["evidence_valid"] or checked["exact_recovery"]!=r["evaluation"]["exact_recovery"]:
                raise ValueError("completed carrier evidence changed")
            packet,key=verify_binding(bindings[c["pair_id"]],c)
            if checked["prepared_packet_sha256"]!=sha256_file(packet):raise ValueError("wrong shared ciphertext")
            validate_receiver_inbox(folder/"inbox",c,key)
            sender=read_json(folder/"sender.json");receiver=read_json(folder/"receiver.json")
            if sender["source_hash"]!=r["execution_source_hash"]:raise ValueError("execution source mismatch")
            if receiver["input_roles"]!=["carrier","profile","context","key"]:raise ValueError("receiver inputs changed")
            if sender["gpu_evidence"]["device"]["pid"]==receiver["gpu_evidence"]["device"]["pid"]:
                raise ValueError("receiver not a fresh process")
            reports=[sender,receiver];modality="text" if c["direction"]=="image-to-text" else "image"
        elif r["kind"]=="trace":
            report=read_json(r["result_path"])
            if report!=r["result"] or sha256_file(report["carrier"])!=report["carrier_sha256"]:raise ValueError("control changed")
            for name,digest in r["prefix_files"].items():
                if sha256_file(Path(r["result_path"]).parent/name)!=digest:raise ValueError("control prefix changed")
            reports=[report];modality=c["modality"]
        else:raise ValueError("unexpected prospective record kind")
        for report in reports:
            verify_gpu_report(report,modality,read_profile(ROOT/c["profile"]))
            pid=report["gpu_evidence"]["device"]["pid"]
            matching=[j for j in ledger if j["event"]=="finished" and j["pid"]==pid]
            if len(matching)!=1:raise ValueError("GPU process/ledger identity mismatch")
            activity=[s["pmon"].split()[3] for s in matching[0]["pmon_samples"]]
            if not any(x.isdigit() and int(x)>0 for x in activity):raise ValueError("no positive GPU execution evidence")


def snapshot(directory,manifest,records,reason,permanent=False):
    rows=[r["evaluation"] for r in records.values() if r["kind"]=="stego"]
    coverage=validate_allocation(manifest["cases"],rows)
    coverage["controls_complete"]=sum(r["kind"]=="trace" for r in records.values())==40
    coverage["study_allocation_complete"]=coverage["allocation_complete"] and coverage["controls_complete"]
    projection=forecast(manifest,records,directory)
    data=dict(coverage=coverage,forecast=projection,reason=reason,utc=datetime.now(timezone.utc).isoformat())
    atomic_json(directory/"progress.json",data,replace=True)
    if permanent:
        atomic_json(directory/"checkpoints"/("%04d.json"%(len(list((directory/"checkpoints").glob("*.json")))+1)),data)
    print(json.dumps(dict(checkpoint=reason,stego=len(rows),controls=sum(r["kind"]=="trace" for r in records.values()),
        v2_seconds=projection["usage_seconds"]["v2"],remaining_seconds=projection["remaining_prospective_seconds"],
        reserved_whole_hours=projection["reserved_whole_hours"])),flush=True)
    return data


def run(directory,prepare_only=False):
    directory=Path(directory).resolve()
    for stage in ("v0","v1","v2"):reconcile_interrupted(stage)
    manifest,freeze=prepare(directory)
    if prepare_only:
        print(json.dumps(dict(prepared=True,manifest=str(MANIFEST),groups=40,stego=120,controls=40)))
        return 0
    for name,digest in freeze["files"].items():
        if sha256_file(ROOT/name)!=digest:raise ValueError("execution freeze changed: "+name)
    recover_terminal_events(directory);records=completed_records(directory,{})
    bindings=read_json(directory/"packet_bindings.json")
    # Recover finished outputs on CPU before projecting remaining GPU work.
    # Missing/malformed sender output blocks continuation; it is never re-encrypted.
    for c in manifest["cases"]:
        if c["work_id"] in records:continue
        state=sender_state(directory/"cases"/c["id"],c,bindings[c["pair_id"]])
        if state=="evaluate_pending":
            records[c["work_id"]]=execute_case(directory,c,bindings[c["pair_id"]],stage="v2")
        elif state not in {"unstarted","receiver_pending"}:
            raise RuntimeError("unresolved interrupted sender before continuation: "+c["id"])
    for group in manifest["groups"]:
        work=group["control_work_id"]
        if work not in records and (directory/"traces"/("control-"+group["id"])/"result.json").exists():
            item=next(t for t in manifest["controls"] if t["work_id"]==work)
            records[work]=execute_trace(directory,realized_control(item,group,records),records,stage="v2")
    reconcile_evidence(manifest,records,bindings)
    by_work={c["work_id"]:c for c in manifest["cases"]}
    controls={t["work_id"]:t for t in manifest["controls"]}
    state=snapshot(directory,manifest,records,"start/resume",True)
    last_checkpoint=budget_state("v2")[0]
    try:
        for index,group in enumerate(manifest["groups"]):
            pending=pending_group(group,records)
            if not pending:continue
            if not state["forecast"]["fits_phase"] or not state["forecast"]["fits_whole"]:
                raise RuntimeError("remaining forecast no longer fits an authorized ceiling")
            if source_hash()!=freeze["execution_source_hash"]:raise RuntimeError("execution source changed")
            bound=0
            for w in group["work_ids"]:
                if w in records:continue
                c=by_work[w];state=sender_state(directory/"cases"/c["id"],c,bindings[c["pair_id"]])
                bound+=(1 if state=="receiver_pending" else 0 if state=="evaluate_pending" else 2)*job_limit(c)
            if group["control_work_id"] not in records:bound+=900 if group["direction"]=="image-to-text" else 130
            remaining=min(phase_limit("v2")-budget_state("v2")[0],144000-sum(budget_state(s)[0] for s in ("v0","v1","v2")))
            if bound+20>remaining:raise RuntimeError("cannot reserve whole group including fresh recovery/control")
            for work in group["work_ids"]:
                if work in records:continue
                c=by_work[work];record=execute_case(directory,c,bindings[c["pair_id"]],stage="v2")
                records[work]=record
                reconcile_evidence(manifest,{work:record},bindings)
            work=group["control_work_id"]
            if work not in records:
                item=realized_control(controls[work],group,records)
                record=execute_trace(directory,item,records,stage="v2")
                records[work]=record
                reconcile_evidence(manifest,{work:record},bindings)
            used=budget_state("v2")[0];checkpoint=index<=1 or used-last_checkpoint>=1800
            state=snapshot(directory,manifest,records,group["id"],checkpoint)
            if checkpoint:last_checkpoint=used
        snapshot(directory,manifest,records,"bounded allocation executed",True)
        return 0
    except BaseException as exc:
        snapshot(directory,manifest,records,"STOP: "+type(exc).__name__+": "+str(exc),True)
        raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=Path,required=True)
    parser.add_argument("--prepare-only",action="store_true")
    args=parser.parse_args();raise SystemExit(run(args.run,args.prepare_only))


if __name__=="__main__":main()
