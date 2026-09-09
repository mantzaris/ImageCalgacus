"""Frozen V1 continuation, not a general scheduler. No held-out model inputs."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import time
from .runtime import (ROOT, atomic_json, canonical_hash, source_hash, sha256_file,
                      read_profile, budget_state, phase_limit, run_budgeted,
                      reconcile_interrupted)
from .packet import NewRun, open_packet
from .sender import read_source
from .evaluate import evaluate_case, validate_allocation

ALLOCATION = ROOT/"configs/v1_qualification.json"
PRIOR_EVENTS = ROOT/"artifacts/v1_2_review/qualification_events.jsonl"
CONTRACT_FILES = ("packet.py","fixed_rank.py","entropy_coding.py","arithmetic_coding.py",
                  "coders.py","text_backend.py","image_backend.py")


def read_json(path):
    return json.loads(Path(path).read_text())


def prior_cases(allocation):
    by_work={c["work_id"]:c for c in allocation["cases"]}
    events=[json.loads(line) for line in PRIOR_EVENTS.read_text().splitlines()]
    if len({e["work_id"] for e in events})!=len(events):
        raise ValueError("duplicate historical credit")
    records={}
    for event in events:
        case=by_work[event["work_id"]]
        evidence=Path(event["evidence"])
        if not evidence.exists(): evidence=ROOT/"artifacts/v1_2_review"/evidence
        evaluation=read_json(evidence)
        public=evidence.parent
        sender=read_json(public/"sender.json")
        private=Path(sender["carrier"]).parent.parent
        checked=evaluate_case(case,private)
        # Preserve the historical work identity, not a relabeled rerun.
        if not checked["evidence_valid"] or not checked["terminal"]:
            raise ValueError("invalid prior credit: "+case["id"])
        if checked["exact_recovery"]!=evaluation["exact_recovery"]:
            raise ValueError("historical equality changed")
        records[case["work_id"]]={"kind":"stego","work_id":case["work_id"],"case":case["id"],
            "case_dir":str(private),"historical_evidence":str(evidence),
            "evaluation":checked,"execution_source_hash":sender["source_hash"],
            "historical":True}
    return records


def verify_binding(binding, case):
    packet,key=Path(binding["packet"]),Path(binding["key"])
    if not packet.is_file() or not key.is_file():
        raise ValueError("missing original packet/key for "+case["pair_id"])
    if sha256_file(packet)!=binding["packet_sha256"]:
        raise ValueError("packet binding mismatch for "+case["pair_id"])
    payload=read_source(ROOT/case["source"],case["direction"])
    if hashlib.sha256(payload.data).hexdigest()!=case["source_sha256"]:
        raise ValueError("source payload changed")
    if binding["source_sha256"]!=case["source_sha256"] or binding["context_sha256"]!=case["context_sha256"]:
        raise ValueError("packet bound to wrong payload/context group")
    if open_packet(packet.read_bytes(),key.read_bytes(),payload.kind)!=payload:
        raise ValueError("packet/key/source authentication mismatch")
    return packet,key


def completed_records(directory, prior):
    records=dict(prior)
    for path in sorted((directory/"terminals").glob("*.json")):
        record=read_json(path)
        if path.stem!=record["work_id"]: raise ValueError("terminal filename/work mismatch")
        if record["work_id"] in records:
            raise ValueError("duplicate terminal or prior observation")
        records[record["work_id"]]=record
    return records


def pending_work(allocation, records):
    return [c for c in allocation["cases"] if c["work_id"] not in records]


def terminal(directory, record):
    path=directory/"terminals"/(record["work_id"]+".json")
    if path.exists():
        if read_json(path)!=record: raise ValueError("conflicting completion record")
        return False
    atomic_json(path,record)
    # Authoritative immutable terminal files recover a crash before this append.
    append_event(directory,record)
    return True


def append_event(directory, record):
    path=directory/"qualification_events.jsonl"
    entries=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if any(e["work_id"]==record["work_id"] for e in entries): return
    event={"work_id":record["work_id"],"kind":record["kind"],"event":"terminal",
           "record":"terminals/"+record["work_id"]+".json","record_sha256":sha256_file(directory/"terminals"/(record["work_id"]+".json"))}
    with path.open("a") as stream:
        stream.write(json.dumps(event)+"\n");stream.flush();os.fsync(stream.fileno())


def recover_terminal_events(directory):
    for path in sorted((directory/"terminals").glob("*.json")):
        append_event(directory,read_json(path))


def classify(case,row,sender,receiver,prefix_matches):
    if not row["evidence_valid"]: return "infrastructure_or_identity_error"
    if row["exact_recovery"] and row["carrier_complete"] and prefix_matches: return "exact_recovery"
    if row.get("outcome_class")=="static_tokenization_drift_failure":
        return "static_tokenization_drift_failure"
    if case["method"] in {"gated","arithmetic"} and sender.get("failure_stage")=="capacity" and receiver.get("failure_stage")=="capacity":
        if (prefix_matches and row["coder_progress_matches"] and
                sender["diagnostics"]==receiver["diagnostics"] and
                sender["coder_diagnostics"]==receiver["coder_diagnostics"]):
            return "verified_capacity_failure"
    return "unexpected_experimental_or_infrastructure_failure"


def sender_state(case_dir, case, binding):
    """Only a saved artifact with a complete, matching sender report can resume."""
    report=case_dir/"sender.json"
    if not report.exists(): return "unstarted" if not case_dir.exists() else "interrupted_sender"
    sender=read_json(report)
    carrier=case_dir/"inbox"/("carrier.txt" if case["direction"]=="image-to-text" else "carrier.png")
    if sender.get("profile_id")!=case["profile_id"] or sender.get("prepared_packet_sha256")!=binding["packet_sha256"]:
        raise ValueError("started sender identity mismatch")
    if not carrier.exists() or sha256_file(carrier)!=sender.get("carrier_sha256"):
        return "invalid_or_interrupted_sender"

    validate_receiver_inbox(case_dir/"inbox",case,Path(binding["key"]))
    return "receiver_pending" if not (case_dir/"receiver.json").exists() else "evaluate_pending"


def validate_receiver_inbox(inbox, case, original_key):
    names={"carrier.txt","prompt.txt","profile.json","run.key"} if case["direction"]=="image-to-text" else {"carrier.png","row.rgb","profile.json","run.key"}
    if {p.name for p in inbox.iterdir()}!=names: raise ValueError("receiver inbox has undeclared or missing inputs")
    if canonical_hash(read_profile(inbox/"profile.json"))!=case["profile_id"]:
        raise ValueError("receiver profile does not match frozen work")
    context=inbox/("prompt.txt" if case["direction"]=="image-to-text" else "row.rgb")
    if sha256_file(context)!=case["context_sha256"] or (inbox/"run.key").read_bytes()!=original_key.read_bytes():
        raise ValueError("receiver context/key not the original group binding")


def verify_gpu_report(result, modality, profile):
    gpu=result.get("gpu_evidence",{}); device=gpu.get("device",{})
    if (device.get("uuid")!=profile["gpu_uuid"] or not device.get("pid") or not gpu.get("gpu_allocation") or
        gpu.get("model_sha256")!=profile[modality]["model_sha256"]):
        raise ValueError("missing or incompatible GPU allocation evidence")
    if modality=="text":
        if gpu.get("offloaded_layers")!=[33,33]: raise ValueError("full eligible-layer offload not established")
    elif not (gpu.get("parameter_devices")==["cuda:0"] and gpu.get("input_device")=="cuda:0" and
              gpu.get("strict_loading") and gpu.get("inference_mode")):
        raise ValueError("strict CUDA image inference not established")


def prepare(directory):
    directory=Path(directory).resolve()
    allocation=read_json(ALLOCATION)
    prior=prior_cases(allocation)
    if len(prior)!=18: raise ValueError("unexpected starting credit count")
    baseline=read_json(ROOT/".runtime/v1_qualification/baseline.json")
    bindings=baseline["legacy_packet_bindings"]
    groups=defaultdict(list)
    for case in allocation["cases"]: groups[case["pair_id"]].append(case)
    # Check all historical bindings before preparing any new packet or GPU work.
    for group,binding in bindings.items():
        for case in groups[group]: verify_binding(binding,case)
        for record in prior.values():
            if record["work_id"] in {c["work_id"] for c in groups[group]} and record["evaluation"]["prepared_packet_sha256"]!=binding["packet_sha256"]:
                raise ValueError("historical group contains different ciphertexts")
    if (directory/"freeze.json").exists():
        freeze=read_json(directory/"freeze.json")
        if freeze["allocation_sha256"]!=sha256_file(ALLOCATION):
            raise ValueError("frozen allocation changed")
        for group,binding in read_json(directory/"packet_bindings.json").items():
            verify_binding(binding,groups[group][0])
        return freeze
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    for name in ("cases","traces","lossless","terminals","checkpoints"):
        (directory/name).mkdir(exist_ok=True)
    # Packet generation is CPU-only. Every genuinely new group has a new key.
    for group,members in groups.items():
        if group in bindings: continue
        folder=directory/"groups"/group
        packet_path=folder/"sealed.packet"
        if packet_path.exists():
            binding={"packet":str(packet_path),"key":str(folder/"run.key"),
                     "packet_sha256":sha256_file(packet_path),"source_sha256":members[0]["source_sha256"],
                     "context_sha256":members[0]["context_sha256"],"legacy":False}
            verify_binding(binding,members[0]);bindings[group]=binding;continue
        if folder.exists():
            raise RuntimeError("interrupted unsealed new group; preserve and inspect before new encryption: "+group)
        run=NewRun(folder); payload=read_source(ROOT/members[0]["source"],members[0]["direction"])
        packet=run.encrypt(payload)
        with packet_path.open("xb") as stream: stream.write(packet);stream.flush();os.fsync(stream.fileno())
        bindings[group]={"packet":str(packet_path),"key":str(folder/"run.key"),
                         "packet_sha256":sha256_file(packet_path),"source_sha256":members[0]["source_sha256"],
                         "context_sha256":members[0]["context_sha256"],"legacy":False}
    atomic_json(directory/"packet_bindings.json",bindings)
    cases=allocation["cases"]; byid={c["id"]:c for c in cases}
    pending={c["work_id"] for c in pending_work(allocation,prior)}
    queue=[]; queued=set()
    def add_cases(group, methods=None, first=False):
        selected=[c for c in groups[group] if c["work_id"] in pending and c["work_id"] not in queued and (methods is None or c["method"] in methods)]
        if not selected:return
        selected.sort(key=lambda c:({"fixed":0,"gated":1,"arithmetic":2}[c["method"]],c["text_filter_arm"]=="static"))
        queue.append({"kind":"stego_group","id":group+("-first-pair" if first else ""),
                      "work_ids":[c["work_id"] for c in selected],"first_pair":first})
        queued.update(c["work_id"] for c in selected)
    traces={t["id"]:t for t in allocation["traces"] if t["status"]=="pending"}
    trace_seen=set()
    def add_trace(name):
        if name in traces and name not in trace_seen:
            queue.append({"kind":"trace","id":name,"work_ids":[traces[name]["work_id"]]});trace_seen.add(name)
    add_cases("I7-prompt1",{"fixed"},first=True)
    add_trace("ordinary-text-4111");add_trace("ordinary-image-4211")
    add_cases("I6-prompt2");add_cases("T6-row2")
    add_trace("control-text-5206");add_trace("control-image-5306")
    # Cover all timing cells early, preserving pending arms within each group.
    for group in ("I7-prompt1","I1-prompt2","T1-row2","I5-prompt2","T3-row2",
                  "I6-prompt1","T6-row1","I7-prompt2","T7-row2","T7-row1"):
        add_cases(group)
        for t in allocation["traces"]:
            if t.get("payload_group")==group:add_trace(t["id"])
    for t in allocation["traces"]:
        if t["purpose"]=="ordinary":add_trace(t["id"])
    # Remaining fixed groups, numeric source order, row/prompt1 then 2.
    for i in range(1,21):
        for prefix,context in (("I","prompt"),("T","row")):
            for number in (1,2):
                group=prefix+str(i)+"-"+context+str(number)
                add_cases(group)
                for t in allocation["traces"]:
                    if t.get("payload_group")==group:add_trace(t["id"])
    for t in allocation["traces"]:add_trace(t["id"])
    lossless=[]
    for i in range(1,11):
        for context in ("row1","row2"):
            case=next(c for c in cases if c["payload_id"]=="T"+str(i) and c["context_id"]==context and c["method"]=="fixed")
            item={"id":"lossless-"+case["id"],"parent_work_id":case["work_id"],"kind":"lossless",
                  "compression_level":9,"remove_ancillary":True}
            item["work_id"]=canonical_hash(item);lossless.append(item)
            queue.append({"kind":"lossless","id":item["id"],"work_ids":[item["work_id"]]})
    assert queued==pending and len(pending)==134 and len(trace_seen)==58
    files=[ALLOCATION,ROOT/"data/qualification_v1/manifest.json",ROOT/"configs/v1_gpu_authorization.json"]
    files += [ROOT/c["profile"] for c in cases]+[ROOT/c["context"] for c in cases]
    files += [ROOT/t["profile"] for t in allocation["traces"]]
    files += [ROOT/c["source"] for c in cases]
    files += [p for folder in ("imagecalgacus","scripts","tests") for p in (ROOT/folder).rglob("*.py")]
    freeze={"source_revision":baseline["revision"],"execution_source_hash":source_hash(),
            "allocation_sha256":sha256_file(ALLOCATION),"prior_event_sha256":sha256_file(PRIOR_EVENTS),
            "queue":queue,"lossless":lossless,"initial_pending":134,"initial_traces_pending":58,
            "initial_lossless_pending":20,"initial_v1_seconds":budget_state("v1")[0],
            "v1_absolute_limit":phase_limit("v1"),"files":{str(p.relative_to(ROOT)):sha256_file(p) for p in set(files)},
            "order_rule":"first I7/prompt1 fixed pair; second-context audits and timing early; remaining groups numeric; controls after their group; T1-T10 both rows lossless last",
            "protocol_change":False,"receiver_audit_output_only":True,
            "protected_contract_files":{n:sha256_file(ROOT/"imagecalgacus"/n) for n in CONTRACT_FILES}}
    atomic_json(directory/"freeze.json",freeze)
    print(json.dumps({"prepared":str(directory),"pending":134,"traces":58,"lossless":20,"original_groups":8,"new_groups":72}),flush=True)
    return freeze


def job_limit(case, first=False):
    if case["direction"]=="text-to-image": return 130
    if case["method"]!="fixed": return 900
    if case["text_filter_arm"]=="static": return 50 if first else 70
    return 90 if first else 110


def receiver_command(case,inbox,output,report):
    modality="text" if case["direction"]=="image-to-text" else "image"
    profile=read_profile(inbox/"profile.json")
    return [profile[modality]["interpreter"],"-B","-m","imagecalgacus.receiver",case["direction"],
        "--carrier",str(inbox/("carrier.txt" if modality=="text" else "carrier.png")),
        "--profile",str(inbox/"profile.json"),"--context",str(inbox/("prompt.txt" if modality=="text" else "row.rgb")),
        "--key",str(inbox/"run.key"),"--output",str(output),"--report",str(report)]


def execute_case(directory,case,binding,first=False,stage="v1"):
    packet,key=verify_binding(binding,case)
    case_dir=directory/"cases"/case["id"]; state=sender_state(case_dir,case,binding)
    limit=job_limit(case,first)
    modality="text" if case["direction"]=="image-to-text" else "image"
    profile=read_profile(ROOT/case["profile"])
    label=("prospective-" if stage=="v2" else "qualification-")+case["id"]
    if state=="unstarted":
        command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.sender",case["direction"],
            "--source",str(ROOT/case["source"]),"--profile",str(ROOT/case["profile"]),
            "--context",str(ROOT/case["context"]),"--prepared-packet",str(packet),"--key",str(key),
            "--new-run",str(case_dir)]
        status=run_budgeted(command,label+"-encode",stage=stage,max_seconds=limit)
        if status not in (0,2): raise RuntimeError("sender execution failure; inspect retained attempt: "+case["id"])
        state=sender_state(case_dir,case,binding)
    if state not in {"receiver_pending","evaluate_pending"}:
        raise RuntimeError("interrupted/invalid sender preserved, no automatic reroll: "+case["id"])
    audit=ROOT/(".runtime/v2/audits" if stage=="v2" else ".runtime/v1_qualification/audits")/case["id"]
    if state=="receiver_pending":
        # Interrupted receiver outputs are preserved, never used as receiver inputs.
        for path in (case_dir/"recovered.gray",case_dir/"recovered.txt",audit/"bits.txt",audit/"arithmetic.jsonl"):
            if path.exists():
                archive=case_dir/"interrupted-receiver"/(path.name+"."+str(time.time_ns()))
                archive.parent.mkdir(exist_ok=True);shutil.move(str(path),archive)
        output=case_dir/("recovered.gray" if modality=="text" else "recovered.txt")
        command=receiver_command(case,case_dir/"inbox",output,case_dir/"receiver.json")
        command+=["--private-recovered-bits",str(audit/"bits.txt")]
        if case["method"]=="arithmetic":
            command+=["--private-arithmetic-trace",str(audit/"arithmetic.jsonl")]
        status=run_budgeted(command,label+"-decode",stage=stage,max_seconds=limit)
        if status not in (0,1,2):raise RuntimeError("receiver execution interruption: "+case["id"])
    sender,receiver=read_json(case_dir/"sender.json"),read_json(case_dir/"receiver.json")
    row=evaluate_case(case,case_dir,write=True)
    bits=(audit/"bits.txt").read_text()
    original="".join(format(b,"08b") for b in packet.read_bytes())
    prefix_equal=bits==original[:len(bits)].ljust(len(bits),"0")
    classification=classify(case,row,sender,receiver,prefix_equal)
    arithmetic=None
    if case["method"]=="arithmetic":
        analyze=runpy.run_path(str(ROOT/"scripts/diagnose_v1_arithmetic.py"))["analyze"]
        trace=[json.loads(line) for line in (audit/"arithmetic.jsonl").read_text().splitlines()]
        arithmetic=analyze(trace,original)
        atomic_json(audit/"summary.json",arithmetic,replace=True)
        if not all(arithmetic["checks"].values()):
            raise RuntimeError("independent arithmetic audit failed: "+case["id"])
        if classification=="verified_capacity_failure" and arithmetic["unchanged_interval_zero_bit_positions"]:
            classification="verified_A1_stagnation_capacity"
    row.update(run=directory.name,context_id=case["context_id"],pair_id=case["pair_id"],
               outcome_class=classification,private_prefix_equal=prefix_equal,
               execution_source_hash=sender["source_hash"],allocation_source_hash=case["source_hash"])
    if classification not in {"exact_recovery","static_tokenization_drift_failure","verified_capacity_failure","verified_A1_stagnation_capacity"}:
        atomic_json(case_dir/"unexpected_failure.json",row,replace=True)
        raise RuntimeError("unexpected recovery or identity failure; pause: "+case["id"])
    record={"kind":"stego","work_id":case["work_id"],"case":case["id"],"case_dir":str(case_dir),
        "execution_source_hash":sender["source_hash"],"allocation_source_hash":case["source_hash"],
        "evaluation":row,"arithmetic_audit":arithmetic,"historical":False}
    terminal(directory,record)
    print(json.dumps({"case":case["id"],"outcome":classification,"packet":row["packet_complete"],
                      "authenticated":row["authenticated"],"exact":row["exact_recovery"]}),flush=True)
    return record


def execute_trace(directory,item,case_records,stage="v1"):
    target=directory/"traces"/item["id"]
    result_path=target/"result.json"
    if not result_path.exists():
        if target.exists(): raise RuntimeError("interrupted ordinary trace; retain and inspect: "+item["id"])
        profile=read_profile(ROOT/item["profile"])
        command=[profile[item["modality"]]["interpreter"],"-B","-m","imagecalgacus.ordinary",
            "--modality",item["modality"],"--profile",str(ROOT/item["profile"]),"--context",str(ROOT/item["context"]),
            "--seed",str(item["seed"]),"--symbols",str(item["symbols"]),
            "--purpose","control" if item["purpose"]=="control" else "calibration","--output",str(target)]
        if item["purpose"]=="control" and item["modality"]=="text":
            lengths={r["evaluation"].get("delivered_tokens") or r["evaluation"].get("tokens")
                     for r in case_records.values() if r["kind"]=="stego" and
                     r["evaluation"].get("pair_id")==item["payload_group"] and r["evaluation"].get("artifact_saved")}
            # Legacy rows have pair identity supplied by the frozen allocation in run().
            lengths={n for n in lengths if n is not None}
            if not lengths: raise ValueError("no realized carrier lengths for control group")
            command+=["--prefix-lengths",",".join(map(str,sorted(lengths)))]
        limit=900 if item["modality"]=="text" and item["symbols"]==2048 else 320 if item["modality"]=="text" else 130
        status=run_budgeted(command,("prospective-" if stage=="v2" else "qualification-")+item["id"],stage=stage,max_seconds=limit)
        if status:raise RuntimeError("ordinary/control execution failure: "+item["id"])
    result=read_json(result_path)
    if not result["passed"] or result["profile_id"]!=item["profile_id"] or result["context_sha256"]!=item["context_sha256"] or result["seed"]!=item["seed"] or result["symbols"]!=item["symbols"]:
        raise ValueError("ordinary/control identity or completion failure")

    if sha256_file(result["carrier"])!=result["carrier_sha256"]: raise ValueError("ordinary artifact changed")
    verify_gpu_report(result,item["modality"],read_profile(ROOT/item["profile"]))
    prefix_files={p.name:sha256_file(p) for p in target.glob("prefix-*.txt")}
    if item["purpose"]=="control" and item["modality"]=="text":
        for count in result.get("prefix_diagnostics",{}):
            if "prefix-"+count+".txt" not in prefix_files: raise ValueError("missing declared matched prefix")
    record={"kind":"trace","work_id":item["work_id"],"id":item["id"],"result_path":str(result_path),
            "execution_source_hash":result["source_hash"],"result":result,"prefix_files":prefix_files,"historical":False}
    terminal(directory,record);return record


def execute_lossless(directory,item,parent,case):
    from PIL import Image
    from .image_backend import read_png
    target=directory/"lossless"/item["id"];inbox=target/"inbox"
    original=Path(parent["case_dir"])/"inbox"/"carrier.png"
    if not parent["evaluation"]["exact_recovery"] or not parent["evaluation"]["carrier_complete"]:
        raise ValueError("selected lossless parent is not an exact fixed PNG; no replacement")
    pixels=read_png(original);raw=pixels.tobytes()
    if not inbox.exists():
        inbox.mkdir(parents=True,mode=0o700)
        Image.frombytes("RGB",(32,31),raw).save(inbox/"carrier.png",format="PNG",compress_level=9)
        for name in ("profile.json","row.rgb","run.key"):
            shutil.copyfile(original.parent/name,inbox/name)
        os.chmod(inbox/"run.key",0o600)
    with Image.open(inbox/"carrier.png") as im:
        preserved=im.mode=="RGB" and im.size==(32,31) and im.tobytes()==raw and not im.info
    if not preserved: raise ValueError("lossless CPU pixel/metadata check failed")
    validate_receiver_inbox(inbox,case,original.parent/"run.key")
    report=target/"receiver.json";output=target/"recovered.txt"
    if not report.exists():
        if output.exists():shutil.move(str(output),str(target/("interrupted-recovered-"+str(time.time_ns())+".txt")))
        status=run_budgeted(receiver_command(case,inbox,output,report),
            "qualification-"+item["id"]+"-decode",stage="v1",max_seconds=130)
        if status:raise RuntimeError("selected lossless replay failed; no replacement")
    receiver=read_json(report)
    verify_gpu_report(receiver,"image",read_profile(inbox/"profile.json"))
    expected=read_source(ROOT/case["source"],case["direction"]).data
    passed=receiver["authenticated"] and receiver["carrier_complete"] and output.read_bytes()==expected
    if not passed:raise ValueError("lossless source equality or receiver conformance failed")
    record={"kind":"lossless","work_id":item["work_id"],"id":item["id"],"parent_work_id":item["parent_work_id"],
            "original":str(original),"rewritten":str(inbox/"carrier.png"),"recovered":str(output),
            "source":case["source"],"report":str(report),"original_file_sha256":sha256_file(original),
            "rewritten_file_sha256":sha256_file(inbox/"carrier.png"),"pixel_sha256":hashlib.sha256(raw).hexdigest(),
            "pixels_preserved":preserved,"compression_level":9,"ancillary_metadata_removed":True,"exact_recovery":passed,
            "execution_source_hash":source_hash(),"receiver":receiver}
    terminal(directory,record);return record


def trace_credits(allocation):
    result={}
    for item in allocation["traces"]:
        if item["status"]!="credited":continue
        path=ROOT/item["credit"]["report"]
        if sha256_file(path)!=item["credit"]["sha256"]:raise ValueError("historical trace changed")
        data=read_json(path)
        if not data["passed"] or data["profile_id"]!=item["profile_id"] or data["context_sha256"]!=item["context_sha256"]:
            raise ValueError("historical trace identity mismatch")
        result[item["work_id"]]={"kind":"trace","work_id":item["work_id"],"id":item["id"],
                                 "result_path":str(path),"result":data,"historical":True,
                                 "execution_source_hash":data["source_hash"]}
    return result


def snapshot(directory,allocation,freeze,records,reason,permanent=False):
    case_rows=[r["evaluation"] for r in records.values() if r["kind"]=="stego"]
    coverage=validate_allocation(allocation["cases"],case_rows)
    forecast=runpy.run_path(str(ROOT/"scripts/project_v1_compute.py"))["completion_forecast"](directory,allocation,freeze,records)
    coverage.update(trace_completed=sum(r["kind"]=="trace" for r in records.values()),
                    lossless_completed=sum(r["kind"]=="lossless" for r in records.values()),
                    reason=reason,v1_qualified=False)
    result={"coverage":coverage,"forecast":forecast,"utc":datetime.now(timezone.utc).isoformat()}
    atomic_json(directory/"progress.json",result,replace=True)
    if permanent:
        path=directory/"checkpoints"/("%04d.json"%(len(list((directory/"checkpoints").glob("*.json")))+1))
        atomic_json(path,result)
    print(json.dumps({"checkpoint":reason,"stego":len(case_rows),"traces":coverage["trace_completed"],
                      "lossless":coverage["lossless_completed"],"v1_seconds":forecast["v1_seconds"],
                      "remaining_projection_seconds":forecast["remaining_qualification_seconds"],
                      "whole_project_reserved_hours":forecast["whole_project_reserved_hours"]}),flush=True)
    return result


def run(directory,prepare_only=False):
    directory=Path(directory).resolve()
    reconcile_interrupted("v1")
    freeze=prepare(directory)
    if prepare_only:return 0
    for name,digest in freeze["files"].items():
        if sha256_file(ROOT/name)!=digest:raise ValueError("execution freeze changed: "+name)
    allocation=read_json(ALLOCATION);by_work={c["work_id"]:c for c in allocation["cases"]}
    traces={t["work_id"]:t for t in allocation["traces"]}
    lossless={t["work_id"]:t for t in freeze["lossless"]}
    prior=prior_cases(allocation);prior.update(trace_credits(allocation))
    recover_terminal_events(directory)
    records=completed_records(directory,prior)
    for work,record in records.items():
        if record["kind"]=="stego":
            c=by_work[work];record["evaluation"].update(pair_id=c["pair_id"],context_id=c["context_id"],
                text_filter_arm=c["text_filter_arm"])
    bindings=read_json(directory/"packet_bindings.json")
    current=snapshot(directory,allocation,freeze,records,"start/resume",permanent=True)
    last_checkpoint=budget_state("v1")[0]
    try:
        for group in freeze["queue"]:
            pending=[w for w in group["work_ids"] if w not in records]
            if not pending:continue
            if not current["forecast"]["fits_phase_with_reserve"] or not current["forecast"]["fits_whole_project"]:
                raise RuntimeError("measured remaining-work forecast exceeds an authorized ceiling")
            if source_hash()!=freeze["execution_source_hash"]:raise RuntimeError("execution source changed during run")
            if group["kind"]=="stego_group":
                bound=sum(2*job_limit(by_work[w],group["first_pair"]) for w in pending)+20
            elif group["kind"]=="trace":
                item=traces[pending[0]]
                bound=(900 if item["modality"]=="text" and item["symbols"]==2048 else 320 if item["modality"]=="text" else 130)+20
            else:bound=150
            used,_=budget_state("v1")
            if bound>phase_limit("v1")-used:raise RuntimeError("complete group and receiver headroom cannot fit remaining phase")
            for work in pending:
                if group["kind"]=="stego_group":
                    case=by_work[work]
                    record=execute_case(directory,case,bindings[case["pair_id"]],group["first_pair"])
                elif group["kind"]=="trace":
                    record=execute_trace(directory,traces[work],records)
                else:
                    item=lossless[work]
                    record=execute_lossless(directory,item,records[item["parent_work_id"]],by_work[item["parent_work_id"]])
                records[work]=record
            used,_=budget_state("v1")
            checkpoint=bool(group.get("first_pair")) or used-last_checkpoint>=1800
            current=snapshot(directory,allocation,freeze,records,group["id"],permanent=checkpoint)
            if checkpoint:last_checkpoint=used
        snapshot(directory,allocation,freeze,records,"allocation execution finished",permanent=True)
        return 0
    except BaseException as exc:
        snapshot(directory,allocation,freeze,records,"STOP: "+type(exc).__name__+": "+str(exc),permanent=True)
        raise
