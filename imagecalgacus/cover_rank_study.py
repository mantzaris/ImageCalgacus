"""Small serial runner for the frozen cover_rank_v1 allocation.
No source or binding records are imported by the separately launched receiver.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from PIL import Image
import numpy as np
from .cover_rank import SHAPE
from .image_backend import read_png
from .packet import open_packet,TEXT
from .runtime import (ROOT,atomic_json,sha256_file,source_hash,run_budgeted,
    budget_state,phase_limit,DEFAULT_PHASE_LIMITS,reconcile_interrupted)

STAGE="cover_rank_v1"
REVIEW=ROOT/"artifacts/cover_rank_v1_review"
RUN=ROOT/"runs/cover-rank-v1-001"
STATE=ROOT/".runtime/cover_rank_v1"

def identity():
    paths=list((ROOT/"imagecalgacus").rglob("*.py"))
    paths += [ROOT/"scripts/prepare_cover_rank_v1.py",ROOT/"plan/cover_rank_v1.md",
              REVIEW/"manifest.json",REVIEW/"profile.json"]
    return {str(p.relative_to(ROOT)):sha256_file(p) for p in sorted(paths)}

def validate_gpu(report,job):
    evidence=report.get("gpu",{})
    positive=[x for x in job["pmon_samples"] if x["pmon"].split()[3].isdigit() and int(x["pmon"].split()[3])>0]
    if not positive or not evidence.get("strict_loading") or evidence.get("parameter_devices")!=["cuda:0"] or evidence.get("input_device")!="cuda:0" or not evidence.get("inference_mode"):
        raise RuntimeError("GPU execution evidence incomplete")
    if evidence.get("model_sha256")!=json.loads((REVIEW/"profile.json").read_text())["image"]["model_sha256"]:
        raise RuntimeError("model identity mismatch")

def remaining():
    used=budget_state(STAGE)[0]
    whole=sum(budget_state(s)[0] for s in DEFAULT_PHASE_LIMITS)
    return min(phase_limit(STAGE)-used,144000-whole)

def job(name,arguments,neural=True,expected_failure=False):
    record_path=STATE/"jobs"/(name+".json")
    report_path=RUN/"reports"/(name+".json")
    report_path.parent.mkdir(parents=True,exist_ok=True)
    profile=json.loads((REVIEW/"profile.json").read_text())
    command=[profile["image"]["interpreter"],"-B","-m","imagecalgacus.cover_rank",*map(str,arguments),
             "--report",str(report_path)]
    if record_path.exists():
        saved=json.loads(record_path.read_text())
        if saved["command"]!=command: raise RuntimeError("continuation command changed")
        result=saved["job"]
    else:
        # Recover a finished interrupted orchestration without repeating a model job.
        records=budget_state(STAGE)[1]
        starts=[r for r in records if r["event"]=="started" and r["command"]==command]
        if starts:
            if len(starts)!=1: raise RuntimeError("duplicate job attempt requires explicit reconciliation")
            result=next(r for r in records if r["event"]=="finished" and r["id"]==starts[0]["id"])
        else:
            run_budgeted(command,name,stage=STAGE,max_seconds=120 if name=="probe" else 90 if neural else 20)
            result=budget_state(STAGE)[1][-1]
        atomic_json(record_path,{"command":command,"job":result})
    if not report_path.exists(): raise RuntimeError("missing terminal report, retain job and stop")
    report=json.loads(report_path.read_text())
    expected=2 if expected_failure else 0
    if result["returncode"]!=expected or result["failure"]:
        raise RuntimeError("unexpected process outcome: "+name+" "+str(report.get("failure_reason")))
    if expected_failure and (report.get("failure_stage")!="authentication" or not report.get("failure_reason","").startswith("InvalidTag")):
        raise RuntimeError("failure was not the expected authentication rejection")
    if neural: validate_gpu(report,result)
    public_job={k:v for k,v in result.items() if k!="pmon_samples"}
    samples=result["pmon_samples"]
    public_job["gpu_activity"]={"samples":len(samples),
        "positive_samples":sum(x["pmon"].split()[3].isdigit() and int(x["pmon"].split()[3])>0 for x in samples),
        "sampling":"nvidia-smi pmon matched child PID, serial, approximately 0.2 seconds; not sustained utilization inference",
        "peak_sm_percent":max([int(x["pmon"].split()[3]) for x in samples if x["pmon"].split()[3].isdigit()] or [0])}
    public_job["neural_inference"]=neural
    public_job["command"]=command
    public_job["report"]=report
    public_path=REVIEW/"jobs"/(name+".json")
    if not public_path.exists():atomic_json(public_path,public_job)
    return report,public_job

def inbox(name,carrier,key,profile):
    folder=RUN/"receivers"/name
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    for src,dest in ((carrier,"carrier.png"),(key,"run.key"),(profile,"profile.json")):
        p=folder/dest
        if p.exists():
            if sha256_file(p)!=sha256_file(src):raise RuntimeError("receiver input changed")
        else:shutil.copyfile(src,p)
        if dest=="run.key":p.chmod(0o600)
    if {p.name for p in folder.iterdir()}!={"carrier.png","run.key","profile.json"}:
        raise RuntimeError("forbidden extra receiver input")
    return folder

def check_binding(group,bindings):
    binding=bindings[group["id"]]
    packet=ROOT/binding["packet"];key=ROOT/binding["key"]
    source=REVIEW/group["source"];cover=REVIEW/group["cover"]
    if sha256_file(packet)!=binding["packet_sha256"] or sha256_file(source)!=group["source_sha256"] or sha256_file(cover)!=group["cover_sha256"]:
        raise RuntimeError("frozen input or packet binding changed")
    if open_packet(packet.read_bytes(),key.read_bytes(),TEXT).data!=source.read_bytes():
        raise RuntimeError("packet is not bound to frozen source")
    return packet,key,cover,source

def execute_group(group,bindings):
    packet,key,cover,source=check_binding(group,bindings)
    for arm in group["arms"]:
        name=group["id"]+"-"+arm;folder=REVIEW/"outcomes"/name
        folder.mkdir(parents=True,exist_ok=True)
        terminal=folder/"result.json"
        if terminal.exists():
            result=json.loads(terminal.read_text())
            if result["work_id"]!=name or sha256_file(folder/"carrier.png")!=result["carrier_sha256"] or sha256_file(folder/"recovered.txt")!=group["source_sha256"]:
                raise RuntimeError("existing outcome changed")
            continue
        verify=RUN/"checks"/arm
        args=["encode","--arm",arm,"--cover",cover,"--prepared-packet",packet,"--key",key,
              "--profile",REVIEW/"profile.json","--output",folder/"carrier.png"]
        if group["id"]==json.loads((REVIEW/"manifest.json").read_text())["groups"][0]["id"]:
            args+=["--verification-directory",verify]
        sender,sjob=job(name+"-sender",args,arm=="model_rank")
        box=inbox(name,folder/"carrier.png",key,REVIEW/"profile.json")
        receiver,rjob=job(name+"-receiver",["decode","--arm",arm,"--carrier",box/"carrier.png",
            "--key",box/"run.key","--profile",box/"profile.json","--output",folder/"recovered.txt"],arm=="model_rank")
        same=(folder/"recovered.txt").read_bytes()==source.read_bytes()
        if not same or sender.get("digests")!=receiver.get("digests") or sender["coarse_sha256"]!=receiver["coarse_sha256"]:
            raise RuntimeError("unexpected source equality or fresh-process rank discrepancy")
        a=read_png(cover,SHAPE);b=read_png(folder/"carrier.png",SHAPE)
        if not np.array_equal(a//4,b//4) or np.max(np.abs(a.astype(int)-b.astype(int)))>3:
            raise RuntimeError("distortion contract violation")
        result={"work_id":name,"group":group["id"],"split":group["split"],"arm":arm,
            "source_sha256":group["source_sha256"],"source_bytes":group["source_bytes"],
            "cover_sha256":group["cover_sha256"],"carrier_sha256":sha256_file(folder/"carrier.png"),
            "recovered_sha256":sha256_file(folder/"recovered.txt"),"exact_recovery":same,
            "packet_complete":sender["packet_complete"],"carrier_complete":sender["carrier_complete"],
            "authenticated":receiver["authenticated"],"rank_streams_equal":sender.get("digests")==receiver.get("digests"),
            "sender_job":sjob["id"],"receiver_job":rjob["id"],
            "sender_seconds":sjob["elapsed_seconds"],"receiver_seconds":rjob["elapsed_seconds"],
            "sender_phase_seconds":sender["phase_seconds"],"receiver_phase_seconds":receiver["phase_seconds"],
            "packet_pairing_verified":True,"failure":None}
        atomic_json(terminal,result)
        print(json.dumps({"completed":name,"exact":same,"seconds":result["sender_seconds"]+result["receiver_seconds"]}),flush=True)

def development_checks(group,bindings):
    _,key,_,source=check_binding(group,bindings)
    wrong=RUN/"checks/wrong.key"
    if not wrong.exists():
        wrong.write_bytes(os.urandom(32));wrong.chmod(0o600)
    results=[]
    for arm in group["arms"]:
        name=group["id"]+"-"+arm;carrier=REVIEW/"outcomes"/name/"carrier.png"
        rewritten=RUN/"checks"/arm/"lossless.png"
        if not rewritten.exists():
            Image.fromarray(read_png(carrier,SHAPE)).save(rewritten,format="PNG",compress_level=9)
        if not np.array_equal(read_png(carrier,SHAPE),read_png(rewritten,SHAPE)):
            raise RuntimeError("lossless rewrite changed pixels")
        for check,input_file,input_key in (("wrong-key",carrier,wrong),
                                          ("changed-bit",RUN/"checks"/arm/"changed_bit.png",key),
                                          ("lossless",rewritten,key)):
            label=name+"-"+check
            box=inbox(label,input_file,input_key,REVIEW/"profile.json")
            output=RUN/"checks"/arm/(check+".txt")
            report,j=job(label,["decode","--arm",arm,"--carrier",box/"carrier.png",
                "--profile",box/"profile.json","--key",box/"run.key","--output",output],
                arm=="model_rank",check!="lossless")
            if check=="lossless" and output.read_bytes()!=source.read_bytes():raise RuntimeError("lossless source mismatch")
            if check!="lossless" and output.exists():raise RuntimeError("plaintext produced on auth failure")
            results.append({"arm":arm,"check":check,"passed":True,"job_id":j["id"],
                "pixel_equality":True if check=="lossless" else None})
    if not (REVIEW/"development_checks.json").exists():
        atomic_json(REVIEW/"development_checks.json",results)

def forecast():
    records=[r for r in budget_state(STAGE)[1] if r["event"]=="finished"]
    jobs=list((REVIEW/"jobs").glob("*.json")) if (REVIEW/"jobs").exists() else []
    neural=[json.loads(p.read_text())["elapsed_seconds"] for p in jobs if json.loads(p.read_text()).get("neural_inference") and p.stem!="probe"]
    plain=[json.loads(p.read_text())["elapsed_seconds"] for p in jobs if not json.loads(p.read_text()).get("neural_inference")]
    n_bound=max(30.,1.5*max(neural,default=30.))
    p_bound=max(5.,1.5*max(plain,default=5.))
    pending=52-len(list((REVIEW/"outcomes").glob("*/result.json"))) if (REVIEW/"outcomes").exists() else 52
    projected=pending*(n_bound+p_bound) # equal numbers of two-process arms
    return {"charged_seconds":sum(r["elapsed_seconds"] for r in records),
            "pending_carriers":pending,"remaining_projected_seconds":projected,
            "conservative_neural_process_bound":n_bound,"parity_process_bound":p_bound,
            "remaining_allowance_seconds":remaining()}

def main():
    p=argparse.ArgumentParser();p.add_argument("--through",choices=("probe","development","all"),default="all")
    args=p.parse_args()
    reconcile_interrupted(STAGE)
    manifest=json.loads((REVIEW/"manifest.json").read_text())
    bindings=json.loads((RUN/"bindings.json").read_text())
    freeze=REVIEW/"execution_freeze.json"
    if freeze.exists():
        if json.loads(freeze.read_text())["files"]!=identity():raise RuntimeError("execution freeze changed")
    else:atomic_json(freeze,{"files":identity(),"starting_revision":manifest["starting_revision"]})
    for g in manifest["groups"]:check_binding(g,bindings)
    job("probe",["probe","--cover",REVIEW/manifest["groups"][0]["cover"],
                 "--profile",REVIEW/"profile.json"])
    if args.through=="probe":return
    for split in ("development","heldout"):
        if split=="heldout":
            development_checks(manifest["groups"][0],bindings)
            projection=forecast()
            if not (REVIEW/"heldout_freeze.json").exists():
                atomic_json(REVIEW/"heldout_freeze.json",{"files":identity(),"forecast":projection,
                    "development_exact":len(list((REVIEW/"outcomes").glob("development-*/result.json")))})
            if args.through=="development":return
            if projection["remaining_projected_seconds"]>projection["remaining_allowance_seconds"]-120:
                raise RuntimeError("complete held-out allocation does not fit conservative forecast")
        for group in [g for g in manifest["groups"] if g["split"]==split]:
            if all((REVIEW/"outcomes"/w/"result.json").exists() for w in group["work_ids"]):continue
            if remaining()<220:raise RuntimeError("insufficient complete pair headroom")
            execute_group(group,bindings)
            print(json.dumps({"checkpoint":group["id"],**forecast()}),flush=True)

if __name__=="__main__":main()
