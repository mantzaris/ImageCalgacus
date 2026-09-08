"""Bounded 12-unit V1 development pilot. Fresh packet preparation; no scheduling framework."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from .packet import NewRun
from .sender import read_source
from .runtime import ROOT,read_profile,run_budgeted,budget_state,json_write,canonical_hash,source_hash,sha256_file

METHODS=("fixed","gated","arithmetic")
PAYLOADS=("I1","T1","I5","T3")


def projected_remainder(run, index, cases):
    used,ledger=budget_state("v1")
    measured={}
    for case in cases[:index]:
        label=run.name+"-"+case["id"]
        cost=sum(r["elapsed_seconds"] for r in ledger if r["event"]=="finished" and r["id"].endswith((label+"-encode",label+"-decode")))
        measured[(case["direction"],case["method"])]=cost
    calibration=[json.loads(p.read_text()) for p in (ROOT/".runtime/v1/calibration").glob("*/result.json")]
    text_control=max(r["total_seconds"] for r in calibration if r["modality"]=="text") * 4
    image_control=max(r["total_seconds"] for r in calibration if r["modality"]=="image")
    cost=0.0
    details=[]
    for case in cases[index:]:
        actual=measured[(case["direction"],case["method"])]
        # Constant fixed-rank text length; for variable text conservatively allow
        # cap-length quadratic prefix work using the measured ordinary 1024 trace.
        upper=actual
        if case["direction"]=="image-to-text" and case["method"]!="fixed":
            upper=max(upper,2*text_control)
        details.append({"case":case["id"],"measured_first_pair_seconds":actual,"remaining_pair_upper_seconds":upper})
        cost+=upper
    estimate=1.25*(used+cost+text_control+image_control)
    return {"used_seconds":used,"remaining_pairs":details,"control_seconds_upper":{"text":text_control,"image":image_control},
            "reserve_multiplier":1.25,"projected_v1_total_seconds":estimate,"ceiling_seconds":7200,
            "note":"variable-length text uses a conservative N-squared cap envelope; no new methods inferred from fixed timings"}


def execute(args):
    review=ROOT/"artifacts/v1_review"
    settings_path=ROOT/"configs/v1_calibration.json"
    settings=json.loads(settings_path.read_text())
    equivalent=json.loads((ROOT/"runs/v1-text-equivalence-001/result.json").read_text())
    if not equivalent["passed"]: raise RuntimeError("text behavior regression not passed")
    base=read_profile(ROOT/"configs/v0.json")
    manifest=json.loads((ROOT/"configs/v0_cases.json").read_text())
    byid={c["id"]:c for c in manifest["cases"]}
    directory=Path(args.new_run); directory.mkdir(parents=True,exist_ok=False,mode=0o700)
    packet_run=NewRun(args.packet_run)
    fixtures=review/"fixtures"; fixtures.mkdir(parents=True,exist_ok=False)
    contexts=review/"contexts"; contexts.mkdir(exist_ok=False)
    for name in ("prompt.txt","row.rgb"):
        shutil.copyfile(ROOT/"artifacts/v0_review/contexts"/name,contexts/name)
    profiles={}
    for method in METHODS:
        profile=json.loads(json.dumps(base))
        profile["protocol"]="imagecalgacus-v1-three-methods"
        profile["coder"]={"method":method,"precision":32,"framing":"A1",
                          "calibration_sha256":sha256_file(settings_path),
                          "thresholds":{m:{"value":v["threshold_bits"],"hex":v["threshold_hex"]} for m,v in settings["modalities"].items()}}
        profile_path=ROOT/"configs"/("v1_"+method+".json")
        if profile_path.exists(): raise FileExistsError("pilot profile already frozen")
        json_write(profile_path,profile); profiles[method]=(profile_path,profile)
    cases=[]; pairs=[]; frozen_source=source_hash()
    for payload_id in PAYLOADS:
        source=byid[payload_id]
        original=ROOT/source["source"]
        target=fixtures/original.name
        shutil.copyfile(original,target)
        payload=read_source(target,source["direction"])
        packet=packet_run.encrypt(payload)
        packet_path=packet_run.directory/(payload_id+".packet")
        packet_path.write_bytes(packet)
        context=contexts/("prompt.txt" if source["direction"]=="image-to-text" else "row.rgb")
        pair={"payload_id":payload_id,"direction":source["direction"],"source_sha256":source["source_sha256"],
              "source_bytes":len(payload.data),"context_sha256":sha256_file(context),
              "prepared_packet_sha256":hashlib.sha256(packet).hexdigest()}
        pairs.append(pair)
        modality="text" if source["direction"]=="image-to-text" else "image"
        for method in METHODS:
            path,profile=profiles[method]
            work=canonical_hash({"source_hash":frozen_source,"payload_id":payload_id,"context":pair["context_sha256"],
                                 "profile":canonical_hash(profile),"replicate":0,"split":"v1_development"})
            cases.append({"id":payload_id+"-"+method,"work_id":work,"payload_id":payload_id,"method":method,
                          "direction":source["direction"],"source_sha256":source["source_sha256"],"source":str(target),
                          "profile_id":canonical_hash(profile),"model_id":profile[modality]["model_sha256"],
                          "profile":str(path),"context":str(context),"pair_id":payload_id+"-context1"})
    json_write(directory/"references.json",{"cases":cases})
    json_write(directory/"implementation.json",{"source_hash":frozen_source,"source_revision":args.revision,
               "calibration_sha256":sha256_file(settings_path),"pairing":"one immutable packet per payload/context, shared by three methods"})
    json_write(review/"pilot_manifest.json",{"payload_order":list(PAYLOADS),"methods":list(METHODS),
               "preselected_before_outputs":True,"independent_payload_groups":4,"pairs":pairs,
               "cases":cases,"controls":{"text_seed":4301,"image_seed":4302,"shared_within_this_pilot":True}})
    for index,case in enumerate(cases):
        if index==6:
            projection=projected_remainder(directory,index,cases)
            json_write(directory/"midpilot_projection.json",projection)
            print(json.dumps(projection),flush=True)
            if projection["projected_v1_total_seconds"]>7200:
                print("STOP: measured reserved remainder exceeds initial V1 allocation",flush=True)
                return 3
        if source_hash()!=frozen_source:
            raise RuntimeError("pilot application source changed; stop instead of mixing implementations")
        modality="text" if case["direction"]=="image-to-text" else "image"
        profile=profiles[case["method"]][1]
        case_dir=directory/case["id"]
        label=directory.name+"-"+case["id"]
        command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.sender",case["direction"],
                 "--source",case["source"],"--profile",case["profile"],"--context",case["context"],
                 "--prepared-packet",str(packet_run.directory/(case["payload_id"]+".packet")),
                 "--key",str(packet_run.directory/"run.key"),"--new-run",str(case_dir)]
        sent=run_budgeted(command,label+"-encode",stage="v1")
        carrier=case_dir/"inbox"/("carrier.txt" if modality=="text" else "carrier.png")
        received=None
        if sent in (0,2) and carrier.exists():
            inbox=case_dir/"inbox"
            command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.receiver",case["direction"],
                     "--carrier",str(carrier),"--profile",str(inbox/"profile.json"),
                     "--context",str(inbox/("prompt.txt" if modality=="text" else "row.rgb")),
                     "--key",str(inbox/"run.key"),
                     "--output",str(case_dir/("recovered.gray" if modality=="text" else "recovered.txt")),
                     "--report",str(case_dir/"receiver.json")]
            received=run_budgeted(command,label+"-decode",stage="v1")
        evaluated=subprocess.run([sys.executable,"-B","-m","imagecalgacus.evaluate","--run",str(directory),
                    "--references",str(directory/"references.json"),"--mode","progress"],cwd=ROOT,check=False)
        print(json.dumps({"case":case["id"],"sender_exit":sent,"receiver_exit":received,"evaluation_exit":evaluated.returncode}),flush=True)
        if sent not in (0,2) or received not in (None,0,2) or evaluated.returncode:
            print("STOP: implementation/execution failure; preserve attempt for diagnosis",flush=True)
            return 1
    final=subprocess.run([sys.executable,"-B","-m","imagecalgacus.evaluate","--run",str(directory),
               "--references",str(directory/"references.json"),"--output",str(directory/"final_validation.json"),
               "--allow-failures"],cwd=ROOT,check=False)
    return final.returncode


def execute_qualification(args):
    """One frozen six-unit batch; no resumption, extra units, or new allowance."""
    from .evaluate import evaluate_case, validate_allocation
    batch_path=Path(args.qualification_batch)
    batch=json.loads(batch_path.read_text())
    cases=batch["cases"]
    if len(cases)>6 or not batch["preselected_before_carriers"]:
        raise ValueError("not the authorized bounded batch")
    if source_hash()!=batch["source_hash"]:
        raise ValueError("source changed after batch freeze")
    allocation=json.loads((ROOT/"configs/v1_qualification.json").read_text())
    if sha256_file(ROOT/"configs/v1_qualification.json")!=batch["allocation_sha256"]:
        raise ValueError("allocation changed")
    if sha256_file(ROOT/allocation["source_manifest"])!=allocation["source_manifest_sha256"]:
        raise ValueError("source manifest changed")
    directory=Path(args.new_run); directory.mkdir(parents=True,exist_ok=False,mode=0o700)
    packets=NewRun(args.packet_run)
    json_write(directory/"references.json",{"cases":cases})
    json_write(directory/"freeze.json",batch)
    rows=[]; byid={c["id"]:c for c in cases}
    for group in batch["ordered_groups"]:
        group_cases=[byid[k] for k in group]
        bound=sum(2*c["job_timeout_seconds"] for c in group_cases)
        used,_=budget_state("v1")
        if bound+20>7200-used:
            print("STOP: complete group plus teardown headroom no longer fits",flush=True); break
        first=group_cases[0]
        if any(c["pair_id"]!=first["pair_id"] for c in group_cases):
            raise ValueError("group is not an intact payload/context pair")
        packet=packets.encrypt(read_source(ROOT/first["source"],first["direction"]))
        packet_path=packets.directory/(first["pair_id"]+".packet")
        packet_path.write_bytes(packet)
        for case in group_cases:
            if source_hash()!=batch["source_hash"]: raise RuntimeError("frozen source changed")
            profile=read_profile(ROOT/case["profile"])
            if canonical_hash(profile)!=case["profile_id"] or sha256_file(ROOT/case["context"])!=case["context_sha256"]:
                raise ValueError("frozen profile/context changed")
            if hashlib.sha256(read_source(ROOT/case["source"],case["direction"]).data).hexdigest()!=case["source_sha256"]:
                raise ValueError("frozen payload changed")
            modality="text" if case["direction"]=="image-to-text" else "image"
            case_dir=directory/case["id"]; inbox=case_dir/"inbox"
            label=directory.name+"-"+case["id"]
            command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.sender",case["direction"],
                     "--source",str(ROOT/case["source"]),"--profile",str(ROOT/case["profile"]),
                     "--context",str(ROOT/case["context"]),"--prepared-packet",str(packet_path),
                     "--key",str(packets.directory/"run.key"),"--new-run",str(case_dir)]
            sent=run_budgeted(command,label+"-encode",stage="v1",max_seconds=case["job_timeout_seconds"])
            carrier=inbox/("carrier.txt" if modality=="text" else "carrier.png")
            received=None
            if carrier.exists() and sent in (0,2):
                command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.receiver",case["direction"],
                         "--carrier",str(carrier),"--profile",str(inbox/"profile.json"),
                         "--context",str(inbox/("prompt.txt" if modality=="text" else "row.rgb")),
                         "--key",str(inbox/"run.key"),"--output",str(case_dir/("recovered.gray" if modality=="text" else "recovered.txt")),
                         "--report",str(case_dir/"receiver.json")]
                received=run_budgeted(command,label+"-decode",stage="v1",max_seconds=case["job_timeout_seconds"])
            row=evaluate_case(case,case_dir,write=True)
            row.update(run=directory.name,context_id=case["context_id"],pair_id=case["pair_id"],
                       sender_exit=sent,receiver_exit=received,phase="v1.2")
            with (directory/"results.jsonl").open("a") as stream:
                stream.write(json.dumps(row,ensure_ascii=False)+"\n")
            rows.append(row)
            print(json.dumps({k:row.get(k) for k in ("case","outcome_class","exact_recovery","failure_stage","failure_reason")}),flush=True)
            allowed=row["evidence_valid"] and row["outcome_class"] in {"exact_recovery","static_tokenization_drift_failure"}
            if not allowed:
                json_write(directory/"coverage.json",validate_allocation(cases,rows))
                print("STOP: unexpected recovery/infrastructure failure; no automatic retry",flush=True)
                return 1
    summary=validate_allocation(cases,rows)
    summary["v1_qualified"]=False
    json_write(directory/"coverage.json",summary)
    return 0 if summary["allocation_complete"] else 3


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--new-run",required=True)
    parser.add_argument("--packet-run",required=True)
    parser.add_argument("--revision")
    parser.add_argument("--qualification-batch",help="frozen V1.2 six-case manifest, no extra allowance")
    args=parser.parse_args()
    if args.qualification_batch:
        raise SystemExit(execute_qualification(args))
    if not args.revision: parser.error("--revision required for the original pilot")
    raise SystemExit(execute(args))


if __name__=="__main__":
    main()
