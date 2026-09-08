"""CPU-only method-specific projection from actual pilot jobs; never allocates work."""
import argparse,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import budget_state,json_write

def average(values): return statistics.mean(values)
def main():
    start=time.perf_counter()
    parser=argparse.ArgumentParser()
    parser.add_argument("--payloads",type=int,default=20,help="per direction; prospective V1.1 default")
    parser.add_argument("--contexts",type=int,choices=[1,2],default=1,help="2 is a projection sensitivity only")
    parser.add_argument("--output",required=True,help="new output file; accepted reports are never overwritten")
    args=parser.parse_args()
    if args.payloads<=0: parser.error("positive payload allocation required")
    output=Path(args.output).resolve()
    if output.exists() or output.is_relative_to(ROOT/"artifacts/v1_review") or output.is_relative_to(ROOT/"artifacts/v0_review"):
        parser.error("choose a new output outside accepted V0/V1 review packets")
    review=ROOT/"artifacts/v1_review"
    rows=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    used,ledger=budget_state("v1");v0,_=budget_state("v0")
    jobs={r["id"]:r for r in ledger if r["event"]=="finished"}
    methods={}
    for direction in ("image-to-text","text-to-image"):
        for method in ("fixed","gated","arithmetic"):
            group=[r for r in rows if r["direction"]==direction and r["method"]==method]
            observations=[]
            for r in group:
                label=r["run"]+"-"+r["case"]
                enc=next(j["elapsed_seconds"] for ident,j in jobs.items() if ident.endswith(label+"-encode"))
                dec=next(j["elapsed_seconds"] for ident,j in jobs.items() if ident.endswith(label+"-decode"))
                operations=r["encode_seconds"]+r["decode_seconds"]
                loads=r["sender_load_seconds"]+r["receiver_load_seconds"]
                observations.append({"case":r["case"],"encode_seconds":r["encode_seconds"],
                    "decode_seconds":r["decode_seconds"],"cold_load_seconds":loads,
                    "other_process_setup_teardown_seconds":enc+dec-operations-loads,
                    "charged_encode_seconds":enc,"charged_decode_seconds":dec,
                    "charged_pair_seconds":enc+dec,"carrier_complete":r["carrier_complete"],
                    "exact_recovery":r["exact_recovery"],"tokens":r["tokens"],"channels":r["channels"]})
            fields=("encode_seconds","decode_seconds","cold_load_seconds","other_process_setup_teardown_seconds",
                    "charged_encode_seconds","charged_decode_seconds","charged_pair_seconds")
            methods[direction+"/"+method]={"n":len(group),"observations":observations,
                "mean":{k:average([r[k] for r in observations]) for k in fields},
                "maximum":{k:max(r[k] for r in observations) for k in fields},
                "exact_count":sum(r["exact_recovery"] for r in group)}
    controls={}
    for modality,seed in (("text",4301),("image",4302)):
        data=json.loads((ROOT/(".runtime/v1/controls/%s-%d/result.json"%(modality,seed))).read_text())
        cost=next(j["elapsed_seconds"] for ident,j in jobs.items() if ident.endswith("control-"+modality+"-"+str(seed)))
        overhead=cost-data["generation_seconds"]
        controls[modality]={"measured_charged_seconds":cost,"generation_seconds":data["generation_seconds"],
            "cold_load_seconds":data["cold_load_seconds"],"other_setup_seconds":overhead-data["cold_load_seconds"],
            "symbols":data["symbols"],"prefix_estimates":{}}
        for count,details in data.get("prefix_diagnostics",{}).items():
            controls[modality]["prefix_estimates"][count]=details["generation_seconds"]+overhead
    matching={}
    for key,m in methods.items():
        matching[key]=average([controls["text"]["prefix_estimates"][str(r["tokens"])] for r in m["observations"]]) if key.startswith("image-to-text") else controls["image"]["measured_charged_seconds"]
    # Credit only this pilot (2 cases per cell), not V0 repeats or duplicated controls.
    remaining_counts={"image-to-text/fixed":38,"text-to-image/fixed":38,
                      "image-to-text/gated":6,"image-to-text/arithmetic":6,
                      "text-to-image/gated":6,"text-to-image/arithmetic":6}
    known_remaining=sum(n*methods[k]["mean"]["charged_pair_seconds"] for k,n in remaining_counts.items())
    static_proxy=40*methods["image-to-text/fixed"]["maximum"]["charged_pair_seconds"]
    calibration_jobs=[j["elapsed_seconds"] for ident,j in jobs.items() if "calibration-text" in ident]
    image_calibration_jobs=[j["elapsed_seconds"] for ident,j in jobs.items() if "calibration-image" in ident]
    calibration_remaining=6*average(calibration_jobs)+6*average(image_calibration_jobs)
    controls_remaining=23*(controls["text"]["measured_charged_seconds"]+controls["image"]["measured_charged_seconds"])
    dev_remaining=known_remaining+static_proxy+calibration_remaining+controls_remaining
    development={"remaining_stego_units":140,"counts_by_measured_cell":remaining_counts,
        "static_mask_units_unmeasured":40,"measured_cell_projection_seconds":known_remaining,
        "static_mask_sequence_cost_proxy_seconds":static_proxy,
        "remaining_calibration_traces":12,"calibration_projection_seconds":calibration_remaining,
        "additional_controls_upper_count":46,"control_projection_seconds":controls_remaining,
        "additional_point_projection_seconds":dev_remaining,"with_25_percent_reserve_seconds":1.25*dev_remaining,
        "authorized_v1_remaining_seconds":7200-used,"fits_remaining_v1":1.25*dev_remaining<=7200-used,
        "assumptions":["152 planned stego units minus 12 pilot units; eight gated/arithmetic timing cases per modality/method before credits",
          "40 singleton/static-mask arms are unmeasured: maximum measured sequence-check pair cost is an explicit proxy, not a benchmark or guaranteed bound",
          "up to 48 controls provisionally balanced 24 per modality, crediting the two actually shared pilot controls once",
          "16 ordinary traces provisionally balanced eight per modality, crediting four calibration traces; second-context behavior not measured",
          "all estimates conditional on these profiles and local timings; unfinished corpus/second-context checks are not qualified by this projection"]}
    historical=json.loads((review/"budget.json").read_text())
    scenarios=[]
    for contexts in (args.contexts,):
        encode=args.payloads*contexts*sum(m["mean"]["encode_seconds"] for m in methods.values())
        decode=args.payloads*contexts*sum(m["mean"]["decode_seconds"] for m in methods.values())
        cold=args.payloads*contexts*sum(m["mean"]["cold_load_seconds"] for m in methods.values())
        other=args.payloads*contexts*sum(m["mean"]["other_process_setup_teardown_seconds"] for m in methods.values())
        for sharing in ("one_control_trace_per_payload_context",):
            control=args.payloads*contexts*(sum(matching.values()) if sharing=="one_control_per_method" else
                                  controls["text"]["measured_charged_seconds"]+controls["image"]["measured_charged_seconds"])
            resave=20*average([methods["text-to-image/"+m]["mean"]["charged_decode_seconds"] for m in ("fixed","gated","arithmetic")])
            total=v0+used+dev_remaining+encode+decode+cold+other+control+resave
            scenarios.append({"payloads_per_direction":args.payloads,"contexts":contexts,"stego_units":6*args.payloads*contexts,"control_policy":sharing,
                "control_generation_jobs":6*args.payloads*contexts if sharing=="one_control_per_method" else 2*args.payloads*contexts,
                "stego_generation_seconds":encode,"receiver_replay_seconds":decode,
                "cold_load_seconds":cold,"other_process_setup_seconds":other,
                "control_generation_including_setup_seconds":control,"additional_gpu_scoring_seconds":0,
                "lossless_image_replay_20_seconds":resave,"development_spent_seconds":v0+used,
                "v0_historical_seconds":v0,"v1_historical_seconds":historical["v1_charged_seconds"],
                "post_v1_checkpoint_diagnostic_seconds":used-historical["v1_charged_seconds"],
                "remaining_development_seconds":dev_remaining,"subtotal_seconds":total,
                "reserve_seconds":.25*total,"total_with_reserve_gpu_hours":1.25*total/3600,
                "fits_40_gpu_hours":1.25*total<=144000,
                "unreserved_main_stego_only_gpu_hours":(encode+decode+cold+other)/3600})
    result={"scope":"V1.1 prospective allocation projection only; no V2 execution or extra GPU authority","method_timings":methods,
        "controls":controls,"matched_control_cost_estimates":matching,"remaining_v1_qualification":development,
        "full_study_scenarios":scenarios,
        "caveats":["Only two development payload groups per direction and one context were measured; no confidence intervals or unseen-context throughput claim",
          "Capacity failures consume full actual generation/replay costs and remain in per-method averages",
          "Control prefix costs reuse measured checkpoints plus measured setup; fresh independent controls may vary",
          "Shared controls reduce jobs, not the number of independent observations; all shared dependencies stay in their payload groups",
          "Likelihood/rank scoring is already charged inline; CPU JSON aggregation adds no neural replay",
          "V1.1 authorized 20 held-out payloads/direction, one existing context, all methods and up to 40 shared controls; no held-out generation",
          "Historical jobs and diagnostics enter spent cost once; diagnostic replays are not credited against the unchanged 140 remaining development units",
          "One 25% planning reserve is applied to the unreserved subtotal, conservatively including spent history; it is not an extra actual charge or permission",
          "Twenty additional lossless PNG fresh-process replays remain required; UTF-8 byte roundtrips and PNG rewrites/equality are CPU work outside GPU occupancy",
          "The static-mask and remaining-development allocation estimates require measurement/confirmation before any larger authorization"],
        "cpu_aggregation_seconds":time.perf_counter()-start}
    json_write(output,result)
    print(json.dumps({"remaining_v1_with_reserve_hours":1.25*dev_remaining/3600,"full_study":scenarios},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
