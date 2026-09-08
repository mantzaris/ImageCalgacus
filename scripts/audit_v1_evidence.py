"""Focused CPU evidence audit: inputs, paired ciphertext, identities and controls."""
import ast,json,stat,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import json_write,sha256_file,canonical_hash,budget_state

def main():
    review=ROOT/"artifacts/v1_review"
    rows=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    _,ledger=budget_state("v1")
    starts=[j for j in ledger if j["event"]=="started"]
    cases=[];pairs={};packet_directories=set();control_links=[]
    pilot_hash=json.loads((review/"pilot_source_manifest.json").read_text())["package_source_hash"]
    for row in rows:
        directory=ROOT/"runs"/row["run"]/row["case"]
        inbox=directory/"inbox"
        expected={"profile.json","run.key","carrier.txt","prompt.txt"} if row["direction"]=="image-to-text" else {"profile.json","run.key","carrier.png","row.rgb"}
        send=json.loads((directory/"sender.json").read_text())
        receive=json.loads((directory/"receiver.json").read_text())
        job=next(j for j in starts if j["id"].endswith(row["run"]+"-"+row["case"]+"-encode"))
        command=job["command"]
        packet=Path(command[command.index("--prepared-packet")+1])
        key=Path(command[command.index("--key")+1])
        packet_directories.add(packet.parent)
        profile=json.loads((inbox/"profile.json").read_text())
        checks={"case":row["case"],"only_four_receiver_inputs":{p.name for p in inbox.iterdir()}==expected,
            "retained_key_matches":(inbox/"run.key").read_bytes()==key.read_bytes(),
            "key_permissions_private":stat.S_IMODE(key.stat().st_mode)==0o600,
            "packet_sha_matches":sha256_file(packet)==row["prepared_packet_sha256"],
            "profile_identity_matches":canonical_hash(profile)==row["profile_id"],
            "pilot_source_matches":send["source_hash"]==pilot_hash,
            "fresh_processes":send["gpu_evidence"]["device"]["pid"]!=receive["gpu_evidence"]["device"]["pid"],
            "independent_coder_progress":row["coder_progress_matches"]}
        cases.append(checks)
        pairs.setdefault(row["independent_payload_group"],set()).add(row["prepared_packet_sha256"])
        modality="text" if row["direction"]=="image-to-text" else "image"
        seed=4301 if modality=="text" else 4302
        control=json.loads((ROOT/(".runtime/v1/controls/%s-%d/result.json"%(modality,seed))).read_text())
        length=row["tokens"] if modality=="text" else 2976
        detail=control["prefix_diagnostics"][str(length)]["diagnostics"] if modality=="text" else control["diagnostics"]
        path="controls/text-4301/prefix-%d.txt"%length if modality=="text" else "controls/image-4302/carrier.png"
        control_links.append({"work_id":row["work_id"],"case":row["case"],"control_id":modality+"-"+str(seed),
            "matched_symbols":length,"carrier":path,"shared_not_independent":True,
            "stego_mean_surprisal_bits":row["diagnostics"]["whole"]["surprisal_bits_mean"],
            "control_mean_surprisal_bits":detail["whole"]["surprisal_bits_mean"],
            "stego_mean_log_rank":row["diagnostics"]["whole"]["log_rank_mean"],
            "control_mean_log_rank":detail["whole"]["log_rank_mean"]})
    nonce_checks=[]
    for directory in sorted(packet_directories):
        packets=list(directory.glob("*.packet"))
        nonces=[p.read_bytes()[:12] for p in packets]
        nonce_checks.append({"private_namespace":str(directory),"prepared_count":len(packets),
            "unique_nonce_count":len(set(nonces)),"all_packet_sizes_292":all(p.stat().st_size==292 for p in packets)})
    imports=[n.module for n in ast.walk(ast.parse((ROOT/"imagecalgacus/receiver.py").read_text())) if isinstance(n,ast.ImportFrom)]
    no_evaluator=not any(n and n.split(".")[0] in {"sender","evaluate","demo","v1_pilot"} for n in imports)
    paired=all(len(digests)==1 for digests in pairs.values())
    passed=all(all(v for k,v in c.items() if k!="case") for c in cases) and paired and no_evaluator
    passed &= all(n["prepared_count"]==n["unique_nonce_count"] and n["all_packet_sizes_292"] for n in nonce_checks)
    json_write(review/"receiver_pairing_audit.json",{"passed":passed,"cases":cases,
        "one_ciphertext_per_three_method_pair":paired,"independent_payload_groups":len(pairs),
        "receiver_direct_imports_exclude_sender_evaluator":no_evaluator,"nonce_checks":nonce_checks,
        "separation":"fresh processes, explicit four-file data flow; not an adversarial OS sandbox"})
    json_write(review/"control_links.json",{"unique_ordinary_controls":2,"independent_control_samples":2,
        "pilot_payload_groups":4,"comparisons":control_links,"statistical_inference_performed":False,
        "gpu_scoring":"diagnostics computed inline during already-charged generation/replay; no extra neural scoring pass"})
    print(json.dumps({"audit_passed":passed,"cases":len(cases),"payload_groups":len(pairs),"unique_controls":2}))
    return int(not passed)

if __name__=="__main__": raise SystemExit(main())
