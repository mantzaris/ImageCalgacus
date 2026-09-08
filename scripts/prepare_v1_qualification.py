"""Freeze the existing V1 allocation; no model jobs and no outcome-based selection."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import canonical_hash,sha256_file,source_hash,json_write,read_profile,budget_state

def freeze(output):
    if output.exists(): raise FileExistsError("allocation must be new")
    source_root=ROOT/"data/qualification_v1"
    manifest=json.loads((source_root/"manifest.json").read_text())
    payloads={p["id"]:p for p in manifest["payloads"] if p["split"]=="development"}
    contexts={c["id"]:c for c in manifest["contexts"]}
    pilot=json.loads((ROOT/"artifacts/v1_review/pilot_manifest.json").read_text())
    legacy={(c["payload_id"],c["method"]):c for c in pilot["cases"]}
    static_path=ROOT/"configs/v1_fixed_static.json"
    static=read_profile(ROOT/"configs/v1_fixed.json")
    static["development_text_filter"]="static"
    if static_path.exists():
        if json.loads(static_path.read_text())!=static: raise ValueError("static profile changed")
    else: json_write(static_path,static)
    frozen=source_hash(); cases=[]
    def add(pid,context_id,method,arm,reason):
        payload=payloads[pid]; context=contexts[context_id]
        profile_path=static_path if arm=="static" else ROOT/("configs/v1_"+method+".json")
        profile=read_profile(profile_path)
        modality="text" if pid.startswith("I") else "image"
        definition={"split":"development","payload_id":pid,"source_sha256":payload["source_sha256"],
                    "context_sha256":context["sha256"],"method":method,"text_filter_arm":arm,
                    "profile_id":canonical_hash(profile),"replicate":0}
        ident=pid+"-"+context_id+"-"+method+("-"+arm if arm else "")
        item=dict(definition,id=ident,definition_id=canonical_hash(definition),
                  work_id=canonical_hash(dict(definition,source_hash=frozen)),
                  direction=payload["direction"],source=str((source_root/payload["source"]).relative_to(ROOT)),
                  context=str((source_root/context["path"]).relative_to(ROOT)),context_id=context_id,
                  profile=str(profile_path.relative_to(ROOT)),model_id=profile[modality]["model_sha256"],
                  source_hash=frozen,pair_id=pid+"-"+context_id,reason=reason,status="pending")
        if context_id.endswith("1") and arm!="static" and (pid,method) in legacy:
            old=legacy[(pid,method)]
            if old["profile_id"]!=item["profile_id"] or old["source_sha256"]!=item["source_sha256"] or sha256_file(old["context"])!=context["sha256"]:
                raise ValueError("pilot credit identity mismatch")
            item.update(id=old["id"],work_id=old["work_id"],status="credited",
                        credit={"manifest":"artifacts/v1_review/pilot_manifest.json","case":old["id"],
                                "work_id":old["work_id"],"kind":"accepted pilot observation, including capacity failures",
                                "original_source_hash":json.loads((ROOT/"artifacts/v1_review/cases"/old["id"]/"sender.json").read_text())["source_hash"]})
        cases.append(item)
    for i in range(1,21):
        for ctx in ("prompt1","prompt2"):
            for arm in ("sequence","static"): add("I"+str(i),ctx,"fixed",arm,"paired singleton vs complete-prefix; 40 sequence recoveries required")
    for i in range(1,21):
        for ctx in ("row1","row2"): add("T"+str(i),ctx,"fixed",None,"fixed PNG independent artifact recovery across both rows")
    for ids,ctxs,arm in ((("I1","I5","I6","I7"),("prompt1","prompt2"),"sequence"),
                         (("T1","T3","T6","T7"),("row1","row2"),None)):
        for pid in ids:
            for ctx in ctxs:
                for method in ("gated","arithmetic"): add(pid,ctx,method,arm,"method-specific timing/capacity/replay qualification; four preselected payloads per modality")
    traces=[]; base=read_profile(ROOT/"configs/v0.json")
    for modality,ctxbase,prefix in (("text","prompt","I"),("image","row","T")):
        for ctxnum in (1,2):
            ctx=contexts[ctxbase+str(ctxnum)]
            for purpose,count in (("ordinary",4),("control",12)):
                for index in range(count):
                    if purpose=="ordinary": seed=(4100 if modality=="text" else 4200)+(ctxnum-1)*10+index+1
                    else: seed=(4301 if modality=="text" else 4302) if ctxnum==1 and index==0 else (5100 if modality=="text" else 5200)+100*(ctxnum-1)+index+1
                    # Ordinary seed ranges and control ranges are separate; RNG is not crypto.
                    name=purpose+"-"+modality+"-"+str(seed)
                    trace_profile="configs/v0.json" if purpose=="ordinary" else "configs/v1_fixed.json"
                    identity={"purpose":purpose,"modality":modality,"context_sha256":ctx["sha256"],"seed":seed,"profile_id":canonical_hash(read_profile(ROOT/trace_profile))}
                    trace=dict(identity,id=name,work_id=canonical_hash(identity),status="pending",
                               context_id=ctx["id"],context=str((source_root/ctx["path"]).relative_to(ROOT)),
                               profile=trace_profile,symbols=1024 if modality=="text" and purpose=="ordinary" else 2048 if modality=="text" else 2976,
                               purpose_detail="frozen-threshold audit, not recalibration" if purpose=="ordinary" else "shared ordinary trace, matched prefixes reused without extra independent replicates",
                               payload_group=None if purpose=="ordinary" else prefix+str(index+1)+"-"+ctx["id"])
                    old=ROOT/".runtime/v1"/("calibration" if purpose=="ordinary" else "controls")/(modality+"-"+str(seed))/"result.json"
                    if old.exists():
                        evidence=json.loads(old.read_text())
                        if evidence["context_sha256"]!=ctx["sha256"] or evidence["profile_id"]!=identity["profile_id"]: raise ValueError("trace credit identity mismatch")
                        trace.update(status="credited",credit={"report":str(old.relative_to(ROOT)),"sha256":sha256_file(old),
                            "original_source_hash":evidence["source_hash"],"counted_once":True})
                    traces.append(trace)
    assert len(cases)==152 and len({c["work_id"] for c in cases})==152
    assert Counter(c["status"] for c in cases)=={"pending":140,"credited":12}
    assert Counter((t["purpose"],t["status"]) for t in traces)=={("ordinary","pending"):12,("ordinary","credited"):4,("control","pending"):46,("control","credited"):2}
    allocation={"schema":"v1-qualification-v1.2","source_hash":frozen,"source_manifest":"data/qualification_v1/manifest.json",
        "source_manifest_sha256":sha256_file(source_root/"manifest.json"),"cases":cases,"traces":traces,
        "counts":{"stego_total":152,"stego_credited":12,"stego_pending":140,"ordinary_total":16,"ordinary_pending":12,"controls_upper_total":48,"controls_pending":46},
        "credit_policy":"old case/work IDs retained exactly; explicit definition_id includes arm and context. No V0 repeats or diagnostic replay credits.",
        "packet_policy":"one immutable ciphertext per payload/context across methods and text arms. Legacy groups retain original sealed packet identity; never encrypt new plaintext with an old key. New groups get fresh run keys.",
        "pair_credit_note":"I1/I5 sequence credits remain paired with pending static arms only using their already sealed sender-private pilot packet, not a new encryption; retained keys remain receiver-only apart from sender validation.",
        "sampling_policy":"completion_seed remains profile-pinned; ordinary seeds above are not encryption keys/nonces",
        "qualification_conditions":["40/40 sequence fixed text recoveries","40/40 fixed PNG recoveries","40 static comparison outcomes","32 gated/arithmetic timing outcomes, legitimate capacity failures retained","16 ordinary traces, thresholds unchanged","up to 48 declared shared controls","existing independent A1 checks and full lossless checks remain required before final study freeze"],
        "no_heldout_generation":True}
    json_write(output,allocation)
    wanted=["I6-prompt1-fixed-sequence","I6-prompt1-fixed-static","I6-prompt2-fixed-sequence","I6-prompt2-fixed-static","T6-row1-fixed","T6-row2-fixed"]
    batch=[next(c for c in cases if c["id"]==ident) for ident in wanted]
    limits=[110,130,130,150,110,110] # per child, including receiver
    for c,limit in zip(batch,limits):
        c["job_timeout_seconds"]=limit
        c["expected_outcome"]="retained artifact and exact recovery or correctly attributed drift failure" if c["text_filter_arm"]=="static" else "complete authenticated exact recovery"
    used,_=budget_state("v1")
    forecast={"source_revision":"aea21e0179b7c3a5cc5ba3ece73e2d585e058495","source_hash":frozen,
              "allocation_sha256":sha256_file(output),"cases":batch,
              "ordered_groups":[wanted[:2],wanted[2:4],wanted[4:5],wanted[5:]],
              "starting_v1_seconds":used,"remaining_v1_seconds":7200-used,
              "sum_child_hard_limits_seconds":2*sum(limits),"fits":2*sum(limits)<7200-used,
              "forecast_basis":"measured fixed text max pair 132.733s, PNG mean 175.870s; 220s pair base bounds, extra static/c2 bounds 260/300s cover lazy singleton construction and context uncertainty. Full child occupancy charged, no extra jobs.",
              "preselected_before_carriers":True,"same_packet_per_pair":True,
              "files_sha256":{str(p.relative_to(ROOT)):sha256_file(p) for p in sorted((ROOT/"imagecalgacus").glob("*.py"))}}
    json_write(output.with_name("v1_2_batch.json"),forecast)
    print(json.dumps({"allocation":str(output),"counts":allocation["counts"],"batch_bound_seconds":2*sum(limits),"balance_seconds":7200-used}))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"configs/v1_qualification.json")
    freeze(parser.parse_args().output)
