"""Finish only wholly unstarted pilot payload pairs in a NEW key/run namespace.
This is a bounded one-off pilot continuation, not an interrupted-encoding resumer.
"""
import argparse,json
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import read_profile,source_hash,run_budgeted,json_write,budget_state,sha256_file
from imagecalgacus.sender import read_source
from imagecalgacus.packet import NewRun


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--first-run",type=Path,required=True)
    p.add_argument("--new-run",type=Path,required=True)
    p.add_argument("--new-packets",type=Path,required=True)
    args=p.parse_args()
    original=json.loads((args.first_run/"references.json").read_text())["cases"]
    old=json.loads((args.first_run/"implementation.json").read_text())
    proposal=json.loads((args.first_run/"midpilot_projection.json").read_text())
    if source_hash()!=old["source_hash"]: raise RuntimeError("pilot scientific implementation changed")
    remaining=[c for c in original if not (args.first_run/c["id"]).exists()]
    groups={c["payload_id"] for c in remaining}
    if not remaining or any(sum(c["payload_id"]==g for c in remaining)!=3 for g in groups):
        raise RuntimeError("only wholly unstarted three-method pairs can start here")
    used,_=budget_state("v1")
    future=sum(r["remaining_pair_upper_seconds"] for r in proposal["remaining_pairs"])
    future+=sum(proposal["control_seconds_upper"].values())
    estimate=used+1.25*future
    revised={"spent_seconds":used,"future_upper_seconds":future,"future_failure_reserve_seconds":.25*future,
             "projected_total_seconds":estimate,"initial_ceiling_seconds":7200,
             "reason":"retain measured conservative cap envelopes; reserve applies to future work, not already spent jobs",
             "original_projection":str(args.first_run/"midpilot_projection.json")}
    if estimate>7200: print(json.dumps(revised)); return 3
    args.new_run.mkdir(parents=True,exist_ok=False,mode=0o700)
    packets=NewRun(args.new_packets)
    pairs=[]
    for group in sorted(groups):
        case=next(c for c in remaining if c["payload_id"]==group)
        raw=packets.encrypt(read_source(case["source"],case["direction"]))
        target=packets.directory/(group+".packet"); target.write_bytes(raw)
        pairs.append({"payload_id":group,"prepared_packet_sha256":sha256_file(target),
                      "new_key_namespace":str(packets.directory),
                      "lineage":"replaces never-encoded preparation only; no previous carrier or outcome for this pair"})
    json_write(args.new_run/"references.json",{"cases":remaining})
    json_write(args.new_run/"implementation.json",dict(old,continuation_of=str(args.first_run),
               prepared_pairs=pairs,prospective_budget=revised))
    json_write(ROOT/"artifacts/v1_review/continuation_manifest.json",
               {"cases":remaining,"prepared_pairs":pairs,"budget":revised,
                "allocation_unchanged":True,"previously_attempted_units_retried":0})
    print(json.dumps(revised),flush=True)
    for case in remaining:
        if source_hash()!=old["source_hash"]: raise RuntimeError("pilot source changed")
        modality="text" if case["direction"]=="image-to-text" else "image"
        profile=read_profile(case["profile"]); python=profile[modality]["interpreter"]
        directory=args.new_run/case["id"]; inbox=directory/"inbox"
        label=args.new_run.name+"-"+case["id"]
        sent=run_budgeted([python,"-B","-m","imagecalgacus.sender",case["direction"],
             "--source",case["source"],"--profile",case["profile"],"--context",case["context"],
             "--prepared-packet",str(packets.directory/(case["payload_id"]+".packet")),
             "--key",str(packets.directory/"run.key"),"--new-run",str(directory)],label+"-encode",stage="v1")
        received=None
        carrier=inbox/("carrier.txt" if modality=="text" else "carrier.png")
        if sent in (0,2) and carrier.exists():
            received=run_budgeted([python,"-B","-m","imagecalgacus.receiver",case["direction"],
              "--carrier",str(carrier),"--profile",str(inbox/"profile.json"),
              "--context",str(inbox/("prompt.txt" if modality=="text" else "row.rgb")),
              "--key",str(inbox/"run.key"),
              "--output",str(directory/("recovered.gray" if modality=="text" else "recovered.txt")),
              "--report",str(directory/"receiver.json")],label+"-decode",stage="v1")
        checked=subprocess.run([sys.executable,"-B","-m","imagecalgacus.evaluate","--run",str(args.new_run),
                 "--references",str(args.new_run/"references.json"),"--mode","progress"],cwd=ROOT).returncode
        print(json.dumps({"case":case["id"],"sender_exit":sent,"receiver_exit":received}),flush=True)
        if sent not in (0,2) or received not in (0,2) or checked: return 1
    return subprocess.run([sys.executable,"-B","-m","imagecalgacus.evaluate","--run",str(args.new_run),
               "--references",str(args.new_run/"references.json"),"--output",str(args.new_run/"final_validation.json"),
               "--allow-failures"],cwd=ROOT).returncode


if __name__=="__main__":
    raise SystemExit(main())
