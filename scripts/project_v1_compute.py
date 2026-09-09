"""CPU-only method-specific projection from actual pilot jobs; never allocates work."""
import argparse,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import budget_state,json_write,phase_limit

def average(values): return statistics.mean(values)
def main():
    start=time.perf_counter()
    parser=argparse.ArgumentParser()
    parser.add_argument("--payloads",type=int,default=20,help="per direction; prospective V1.1 default")
    parser.add_argument("--contexts",type=int,choices=[1,2],default=1,help="2 is a projection sensitivity only")
    parser.add_argument("--output",required=True,help="new output file; accepted reports are never overwritten")
    parser.add_argument("--qualification-results",type=Path,help="new V1.2 terminal observations; diagnostics excluded")
    parser.add_argument("--qualification-allocation",type=Path,default=ROOT/"configs/v1_qualification.json")
    args=parser.parse_args()
    if args.payloads<=0: parser.error("positive payload allocation required")
    output=Path(args.output).resolve()
    if output.exists() or output.is_relative_to(ROOT/"artifacts/v1_review") or output.is_relative_to(ROOT/"artifacts/v0_review"):
        parser.error("choose a new output outside accepted V0/V1 review packets")
    if args.qualification_results:
        return project_qualification(args, output)
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
        "authorized_v1_remaining_seconds":phase_limit("v1")-used,"fits_remaining_v1":1.25*dev_remaining<=phase_limit("v1")-used,
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

def project_qualification(args, output):
    """Method/context cells from charged jobs; unchanged 120-unit main allocation."""
    from collections import Counter
    review=ROOT/"artifacts/v1_review"
    old=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    new=[json.loads(line) for line in args.qualification_results.read_text().splitlines()]
    allocation=json.loads(args.qualification_allocation.read_text())
    used,ledger=budget_state("v1");v0,_=budget_state("v0")
    jobs={r["id"]:r for r in ledger if r["event"]=="finished"}
    observations=[]
    for row in old+new:
        label=row["run"]+"-"+row["case"]
        enc=next(j["elapsed_seconds"] for ident,j in jobs.items() if ident.endswith(label+"-encode"))
        dec=next(j["elapsed_seconds"] for ident,j in jobs.items() if ident.endswith(label+"-decode"))
        generation=row["encode_seconds"]; replay=row["decode_seconds"] or 0.0
        loads=(row["sender_load_seconds"] or 0.)+(row["receiver_load_seconds"] or 0.)
        context=row.get("context_id","prompt1" if row["direction"]=="image-to-text" else "row1")
        arm=row.get("text_filter_arm","sequence") if row["direction"]=="image-to-text" else None
        observations.append(dict(case=row["case"],work_id=row["work_id"],direction=row["direction"],method=row["method"],
            context=context,arm=arm,encode_seconds=generation,decode_seconds=replay,cold_load_seconds=loads,
            other_process_seconds=enc+dec-generation-replay-loads,charged_encode_seconds=enc,
            charged_decode_seconds=dec,charged_pair_seconds=enc+dec,
            exact_recovery=row["exact_recovery"],outcome_class=row.get("outcome_class","accepted_pilot"),
            carrier_complete=row["carrier_complete"]))
    fields=("encode_seconds","decode_seconds","cold_load_seconds","other_process_seconds","charged_encode_seconds","charged_decode_seconds","charged_pair_seconds")
    def cell(direction,method,context,arm):
        measured=[r for r in observations if (r["direction"],r["method"],r["context"],r["arm"])==(direction,method,context,arm)]
        fallback=None
        if not measured:
            first="prompt1" if direction=="image-to-text" else "row1"
            measured=[r for r in observations if (r["direction"],r["method"],r["context"],r["arm"])==(direction,method,first,arm)]
            fallback="unmeasured second-context cell uses first context of SAME method"
        if not measured and arm=="static":
            measured=[r for r in observations if r["direction"]==direction and r["method"]==method and r["arm"]=="sequence"]
            fallback="static unmeasured: sequence maximum cost proxy"
        if not measured: raise ValueError("missing method-specific cost evidence")
        means={f:average([r[f] for r in measured]) for f in fields}
        if fallback and arm=="static":
            means={f:max(r[f] for r in measured) for f in fields}
        return dict(n=len(measured),cases=[r["case"] for r in measured],mean=means,assumption=fallback,
                    full_carrier_replays_observed=sum(r["carrier_complete"] for r in measured),
                    uncertainty="one observed case" if len(measured)==1 else "small development sample")
    # Credits require correct implementation/evidence; a legitimate static drift failure is an outcome.
    credited={r["work_id"] for r in new if r["evidence_valid"] and r.get("outcome_class") in {"exact_recovery","static_tokenization_drift_failure"}}
    pending=[c for c in allocation["cases"] if c["status"]=="pending" and c["work_id"] not in credited]
    groups=Counter((c["direction"],c["method"],c["context_id"],c["text_filter_arm"]) for c in pending)
    details=[]; remaining_stego=0.; observed_point_stego=0.
    for (direction,method,context,arm),count in sorted(groups.items(),key=str):
        estimate=cell(direction,method,context,arm)
        point=estimate["mean"]["charged_pair_seconds"]
        per=point
        if arm=="static":
            # An early receiver failure cannot establish the price of a full future replay.
            full_static=[r["charged_decode_seconds"] for r in observations if r["arm"]=="static" and r["carrier_complete"]]
            per=estimate["mean"]["charged_encode_seconds"]+max(estimate["mean"]["charged_decode_seconds"],
                estimate["mean"]["charged_encode_seconds"] if not estimate["full_carrier_replays_observed"] else 0.,
                average(full_static) if full_static and not estimate["full_carrier_replays_observed"] else 0.)
        details.append(dict(direction=direction,method=method,context=context,arm=arm,pending=count,
            timing=estimate,observed_pair_point_seconds=point,planning_pair_seconds=per,total_seconds=count*per,
            static_replay_assumption=("observed full replay in this cell" if estimate["full_carrier_replays_observed"] else
                "max of early decode, same-context encode, and observed full static replay in another context") if arm=="static" else None))
        remaining_stego+=count*per;observed_point_stego+=count*point
    trace_costs={};trace_details=[]; ordinary=controls_remaining=0.
    for trace in allocation["traces"]:
        if trace["status"]!="pending": continue
        purpose,modality=trace["purpose"],trace["modality"]
        matches=[j["elapsed_seconds"] for ident,j in jobs.items() if
                 ("calibration-"+modality in ident if purpose=="ordinary" else ident.endswith("control-"+modality+"-"+str(4301 if modality=="text" else 4302)))]
        estimate=average(matches)
        trace_costs[purpose,modality]=estimate
        trace_details.append({"id":trace["id"],"context":trace["context_id"],"seconds":estimate,
                              "assumption":"existing same-modality ordinary trace cost; second contexts unmeasured"})
        if purpose=="ordinary": ordinary+=estimate
        else: controls_remaining+=estimate
    main_cells={direction+"/"+method:cell(direction,method,"prompt1" if direction=="image-to-text" else "row1",
                    "sequence" if direction=="image-to-text" else None)
                for direction in ("image-to-text","text-to-image") for method in ("fixed","gated","arithmetic")}
    n=args.payloads*args.contexts
    generation=n*sum(c["mean"]["encode_seconds"] for c in main_cells.values())
    replay=n*sum(c["mean"]["decode_seconds"] for c in main_cells.values())
    loads=n*sum(c["mean"]["cold_load_seconds"] for c in main_cells.values())
    process=n*sum(c["mean"]["other_process_seconds"] for c in main_cells.values())
    main_controls=n*(trace_costs["control","text"]+trace_costs["control","image"])
    lossless=20*average([main_cells["text-to-image/"+m]["mean"]["charged_decode_seconds"] for m in ("fixed","gated","arithmetic")])
    remaining_dev=remaining_stego+ordinary+controls_remaining
    total=v0+used+remaining_dev+generation+replay+loads+process+main_controls+lossless
    baseline=json.loads((ROOT/".runtime/v1_2/baseline.json").read_text())
    history_v1=json.loads((review/"budget.json").read_text())["v1_charged_seconds"]
    result={"scope":"V1.2 measured forecast only; V1 unqualified, no held-out execution or extra authorization",
        "observations":observations,"main_context_method_timings":main_cells,
        "remaining_qualification":{"stego_pending":len(pending),"batch_credited":len(credited),"by_cell":details,
            "ordinary_pending":sum(t["purpose"]=="ordinary" and t["status"]=="pending" for t in allocation["traces"]),
            "controls_pending_upper":sum(t["purpose"]=="control" and t["status"]=="pending" for t in allocation["traces"]),
            "remaining_stego_seconds":remaining_stego,"naive_observed_static_point_stego_seconds":observed_point_stego,
            "ordinary_seconds":ordinary,"controls_upper_seconds":controls_remaining,"trace_estimates":trace_details,
            "unreserved_seconds":remaining_dev,"unreserved_hours":remaining_dev/3600,
            "standalone_with_25_percent_headroom_hours":1.25*remaining_dev/3600,
            "additional_to_remaining_phase_unreserved_seconds":max(0,remaining_dev-(phase_limit("v1")-used))},
        "history":{"v0_seconds":v0,"v1_original_checkpoint_seconds":history_v1,
                   "v1_1_seconds":baseline["v1_seconds"]-history_v1,"v1_2_seconds":used-baseline["v1_seconds"],
                   "v1_total_seconds":used,"remaining_v1_seconds":phase_limit("v1")-used,"cumulative_seconds":v0+used},
        "whole_project":{"payloads_per_direction":args.payloads,"contexts":args.contexts,"main_stego_units":6*n,"shared_controls_upper":2*n,
            "history_seconds":v0+used,"remaining_qualification_seconds":remaining_dev,
            "main_generation_seconds":generation,"main_receiver_seconds":replay,"main_loading_seconds":loads,
            "main_other_occupied_process_seconds":process,"main_controls_seconds":main_controls,
            "additional_lossless_png_replays":20,"lossless_replay_seconds":lossless,"additional_neural_scoring_seconds":0,
            "subtotal_seconds":total,"reserve_once_seconds":.25*total,"total_with_reserve_hours":1.25*total/3600,
            "overall_ceiling_hours":40,"forecast_fits_ceiling":1.25*total<=144000},
        "assumptions":["No diagnostic replay is an observation or credit. Failed arithmetic attempts remain in method means.",
          "Second-context fixed cells and each static cell have at most one new observation. Other second-context methods/ordinary traces are unmeasured.",
          "Static cells with only early failures use a sender-length/full-other-context replay floor, not an assumption that all future receivers fail early.",
          "All per-child costs include model checks/loading, CPU filtering/bookkeeping during occupancy, serialization and teardown.",
          "One 25% reserve applies to the whole unreserved subtotal, conservatively including history; the standalone development headroom is NOT added again.",
          "Shared ordinary prefixes are not independent method-specific controls. Inline likelihood scoring already costs GPU occupancy; standalone JSON and lossless file rewrite checks use CPU.",
          "Remaining 20 lossless PNG replays are additional jobs, not credited by current exact recovery or V1.1 diagnostics.",
          "No claim of statistical power or future throughput guarantee follows from this small sample."]}
    json_write(output,result)
    print(json.dumps({"pending":len(pending),"remaining_development_hours":remaining_dev/3600,
                      "whole_project_with_reserve_hours":1.25*total/3600,"v1_remaining_seconds":phase_limit("v1")-used}))
    return 0



def completion_forecast(directory, allocation, freeze, records):
    """Live completion forecast from charged jobs, not another allocation."""
    from collections import Counter
    from imagecalgacus.runtime import phase_limit
    used, ledger = budget_state("v1"); v0, _ = budget_state("v0")
    jobs = [r for r in ledger if r["event"] == "finished"]
    cases = {c["work_id"]:c for c in allocation["cases"]}
    traces = {t["work_id"]:t for t in allocation["traces"]}
    observations=[]; trace_observations=[]
    fields=("encode_seconds","decode_seconds","cold_load_seconds","other_process_seconds",
            "charged_encode_seconds","charged_decode_seconds","charged_pair_seconds")
    def charged(label):
        matches=[r for r in jobs if r["id"].endswith("-"+label)]
        if not matches: raise ValueError("missing charged job: "+label)
        # Corrected/interrupted attempts consume budget and are never free.
        return sum(r["elapsed_seconds"] for r in matches)
    for work, record in records.items():
        if record["kind"]=="stego":
            c=cases[work]; row=record["evaluation"]
            folder=Path(record["case_dir"])
            label=(folder.parent.name+"-"+c["id"]) if record.get("historical") else "qualification-"+c["id"]
            enc,dec=charged(label+"-encode"),charged(label+"-decode")
            generation=row.get("encode_seconds") or 0.; replay=row.get("decode_seconds") or 0.
            loads=(row.get("sender_load_seconds") or 0.)+(row.get("receiver_load_seconds") or 0.)
            observations.append(dict(case=c["id"],work_id=work,direction=c["direction"],method=c["method"],
                context=c["context_id"],arm=c["text_filter_arm"],encode_seconds=generation,decode_seconds=replay,
                cold_load_seconds=loads,other_process_seconds=enc+dec-generation-replay-loads,
                charged_encode_seconds=enc,charged_decode_seconds=dec,charged_pair_seconds=enc+dec,
                exact_recovery=row["exact_recovery"],carrier_complete=row["carrier_complete"],
                outcome_class=row.get("outcome_class"),historical=record.get("historical",False)))
        elif record["kind"]=="trace":
            t=traces[work]; data=record["result"]
            label=(t["id"].replace("ordinary-","calibration-") if record.get("historical") else "qualification-"+t["id"])
            total=charged(label)
            trace_observations.append(dict(id=t["id"],purpose=t["purpose"],modality=t["modality"],
                context=t["context_id"],charged_seconds=total,generation_seconds=data["generation_seconds"],
                cold_load_seconds=data["cold_load_seconds"],
                other_process_seconds=total-data["generation_seconds"]-data["cold_load_seconds"]))
    def cell(direction,method,context,arm):
        exact=[r for r in observations if (r["direction"],r["method"],r["context"],r["arm"])==(direction,method,context,arm)]
        measured=exact or [r for r in observations if (r["direction"],r["method"],r["arm"])==(direction,method,arm)]
        if not measured: raise ValueError("no same-method timing evidence")
        means={f:average([r[f] for r in measured]) for f in fields}
        per=means["charged_pair_seconds"]
        replay_floor=None
        if arm=="static":
            # A failed early replay never predicts all future receivers failing early.
            full=[r["charged_decode_seconds"] for r in observations if r["arm"]=="static" and r["carrier_complete"]]
            replay_floor=max([means["charged_decode_seconds"],means["charged_encode_seconds"]]+full)
            per=means["charged_encode_seconds"]+replay_floor
        return dict(n=len(exact),evidence_cases=[r["case"] for r in measured],mean=means,planning_pair_seconds=per,
                    static_replay_floor_seconds=replay_floor,
                    assumption=None if exact else "unmeasured context: pooled SAME-method/arm measured contexts",
                    uncertainty="small development sample; trajectory and machine-load variation")
    def trace_cell(purpose,modality,context):
        exact=[r for r in trace_observations if (r["purpose"],r["modality"],r["context"])==(purpose,modality,context)]
        measured=exact or [r for r in trace_observations if (r["purpose"],r["modality"])==(purpose,modality)]
        if not measured: raise ValueError("missing ordinary/control cost evidence")
        return dict(n=len(exact),seconds=average([r["charged_seconds"] for r in measured]),
                    cases=[r["id"] for r in measured],assumption=None if exact else "unmeasured context: same-purpose/modality proxy")
    pending=[c for w,c in cases.items() if w not in records]
    by_cell=[]; stego=0.
    for key,count in sorted(Counter((c["direction"],c["method"],c["context_id"],c["text_filter_arm"]) for c in pending).items(),key=str):
        estimate=cell(*key); total=count*estimate["planning_pair_seconds"]; stego+=total
        by_cell.append(dict(direction=key[0],method=key[1],context=key[2],arm=key[3],
                            pending=count,timing=estimate,total_seconds=total))
    trace_details=[]; ordinary=controls=0.
    for w,t in traces.items():
        if w in records:continue
        estimate=trace_cell(t["purpose"],t["modality"],t["context_id"])
        trace_details.append(dict(id=t["id"],purpose=t["purpose"],context=t["context_id"],estimate=estimate))
        if t["purpose"]=="ordinary":ordinary+=estimate["seconds"]
        else:controls+=estimate["seconds"]
    lossless_details=[]
    for item in freeze["lossless"]:
        if item["work_id"] in records:continue
        c=cases[item["parent_work_id"]]
        observed=[r for r in records.values() if r["kind"]=="lossless" and
                  cases[r["parent_work_id"]]["context_id"]==c["context_id"]]
        costs=[charged("qualification-"+r["id"]+"-decode") for r in observed]
        per=average(costs) if costs else cell("text-to-image","fixed",c["context_id"],None)["mean"]["charged_decode_seconds"]
        lossless_details.append(dict(id=item["id"],context=c["context_id"],seconds=per,
            assumption=None if costs else "fixed-PNG fresh receiver, same row, including loading and occupied processing"))
    lossless=sum(r["seconds"] for r in lossless_details)
    remaining=stego+ordinary+controls+lossless
    main_cells={d+"/"+m:cell(d,m,"prompt1" if d=="image-to-text" else "row1","sequence" if d=="image-to-text" else None)
                for d in ("image-to-text","text-to-image") for m in ("fixed","gated","arithmetic")}
    main={f:20*sum(c["mean"][f] for c in main_cells.values()) for f in fields}
    main_controls=20*sum(trace_cell("control",m,ctx)["seconds"] for m,ctx in (("text","prompt1"),("image","row1")))
    subtotal=v0+used+remaining+main["charged_pair_seconds"]+main_controls
    limit=phase_limit("v1")
    return dict(v0_seconds=v0,v1_seconds=used,v1_limit_seconds=limit,v1_balance_seconds=limit-used,
        checkpoint_seconds=used-freeze["initial_v1_seconds"],observations=observations,trace_observations=trace_observations,
        remaining_stego=len(pending),remaining_ordinary=sum(t["purpose"]=="ordinary" for t in trace_details),
        remaining_controls=sum(t["purpose"]=="control" for t in trace_details),remaining_lossless=len(lossless_details),
        remaining_stego_seconds=stego,remaining_ordinary_seconds=ordinary,remaining_controls_seconds=controls,
        remaining_lossless_seconds=lossless,remaining_qualification_seconds=remaining,by_cell=by_cell,
        pending_trace_estimates=trace_details,pending_lossless_estimates=lossless_details,
        phase_planning_headroom_seconds=.25*remaining,fits_phase_with_reserve=1.25*remaining<=limit-used,
        main_stego_units=120,main_shared_controls=40,main_method_context_cells=main_cells,
        main_generation_seconds=main["encode_seconds"],main_receiver_seconds=main["decode_seconds"],
        main_cold_load_seconds=main["cold_load_seconds"],main_other_occupied_seconds=main["other_process_seconds"],
        main_stego_inclusive_seconds=main["charged_pair_seconds"],main_controls_seconds=main_controls,
        extra_main_lossless_jobs=0,additional_neural_scoring_seconds=0,
        whole_project_subtotal_seconds=subtotal,whole_project_reserve_once_seconds=.25*subtotal,
        whole_project_reserved_hours=1.25*subtotal/3600,fits_whole_project=1.25*subtotal<=144000,
        assumptions=[
          "Every charged attempt including diagnosed arithmetic failures, loading, imports, occupied CPU processing, serialization and teardown remains in spent history.",
          "Completed work is removed from remaining cost once. Diagnostic replays have no scientific work credits.",
          "Twenty fixed-PNG lossless checks are qualification receiver jobs; no duplicate 20-job main-study term.",
          "One 25% reserve applies to whole-project subtotal including history. Phase headroom is a feasibility check on the same reserve, not an added cost.",
          "The 43,200-second authorization amendment is permission, not a forecast expense.",
          "Main study stays 20 held-out payloads per direction, one existing context, all three methods; no held-out jobs launched.",
          "Controls are independent per allocated trace, with matched prefixes shared across methods, not replicated control observations.",
          "Threshold-audit traces do not recalibrate frozen thresholds. Inline scoring needs no added model pass.",
          "Only available method/context observations inform costs; small cells and unmeasured context proxies remain uncertain."])

if __name__=="__main__": raise SystemExit(main())
