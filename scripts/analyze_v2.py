"""CPU-only frozen V2 analysis: grouped intervals, paired metrics and two inline scores.
No model imports, key reads, detector training, threshold selection or extra scoring.
"""
import argparse
from collections import Counter,defaultdict
import csv
import html
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import atomic_json,canonical_hash,sha256_file
from imagecalgacus.v2 import METHODS,DIRECTIONS


def clopper_pearson(successes,n,confidence=.95):
    if not 0<=successes<=n or n<1:raise ValueError("binomial counts required")
    alpha=1-confidence
    def probability(p,first,last):
        return math.fsum(math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(first,last+1))
    def root(first,last,increasing):
        lo,hi=0.,1.
        for _ in range(80):
            middle=(lo+hi)/2;value=probability(middle,first,last)
            if (value<alpha/2)==increasing:lo=middle
            else:hi=middle
        return (lo+hi)/2
    return [0. if successes==0 else root(successes,n,True),
            1. if successes==n else root(0,successes,False)]


def group_draws(groups,replicates,seed):
    rng=np.random.Generator(np.random.PCG64(seed))
    strata=defaultdict(list)
    for index,g in enumerate(groups):strata[g["stratum"]].append(index)
    return np.hstack([rng.choice(members,size=(replicates,len(members)),replace=True)
                      for _,members in sorted(strata.items())])


def interval(values):
    valid=np.asarray(values,dtype=np.float64)
    valid=valid[np.isfinite(valid)]
    return np.quantile(valid,[.025,.975]).tolist() if len(valid) else None


def mean_interval(values,draws):
    a=np.asarray([np.nan if x is None else float(x) for x in values],dtype=np.float64)
    valid=np.isfinite(a)
    sampled=a[draws];count=np.isfinite(sampled).sum(axis=1)
    averages=np.divide(np.nansum(sampled,axis=1),count,out=np.full(len(draws),np.nan),where=count>0)
    return dict(n=int(valid.sum()),mean=float(a[valid].mean()) if valid.any() else None,
                grouped_95_interval=interval(averages),valid_bootstrap_replicates=int(np.isfinite(averages).sum()))


def auc(positive,negative,positive_weights=None,negative_weights=None):
    p=np.asarray(positive,dtype=np.float64);n=np.asarray(negative,dtype=np.float64)
    wp=np.ones(len(p)) if positive_weights is None else np.asarray(positive_weights,dtype=np.float64)
    wn=np.ones(len(n)) if negative_weights is None else np.asarray(negative_weights,dtype=np.float64)
    if not len(p) or not len(n) or not wp.sum() or not wn.sum():return None
    wins=(p[:,None]>n[None,:]).astype(np.float64)+.5*(p[:,None]==n[None,:])
    return float((wins*wp[:,None]*wn[None,:]).sum()/(wp.sum()*wn.sum()))


def detection_cell(groups,method,score,rows,links,draws):
    positives=[];positive_groups=[];negative_by_hash={};excluded=[];duplicates=[]
    for index,g in enumerate(groups):
        row=rows.get((g["id"],method));link=links.get(row["work_id"]) if row else None
        value=row.get("diagnostics",{}).get("whole",{}).get(score) if row else None
        ordinary=link.get("scores",{}).get(score) if link else None
        if not row or not row.get("artifact_saved") or not row.get("evidence_valid") or value is None or not math.isfinite(value):
            excluded.append(dict(group=g["id"],reason="missing or unscorable delivered stego"));continue
        if not link or not link.get("available") or ordinary is None or not math.isfinite(ordinary):
            excluded.append(dict(group=g["id"],reason="missing matched control or inline score"));continue
        positives.append(float(value));positive_groups.append(index)
        digest=link["matched_sha256"]
        if digest in negative_by_hash:
            owner=negative_by_hash[digest]
            if owner["score"]!=ordinary:raise ValueError("identical control artifact has inconsistent inline score")
            duplicates.append(dict(group=g["id"],owner_group=groups[owner["group"]]["id"],sha256=digest))
        else:negative_by_hash[digest]=dict(group=index,score=float(ordinary),trace_id=link["trace_id"])
    negative=list(negative_by_hash.values())
    samples=[]
    for draw in draws:
        weights=np.bincount(draw,minlength=len(groups))
        value=auc(positives,[r["score"] for r in negative],weights[positive_groups],
                  [weights[r["group"]] for r in negative])
        samples.append(np.nan if value is None else value)
    return dict(method=method,score=score,direction=groups[0]["direction"],
        score_direction="higher means stego, frozen before outcomes",
        auc=auc(positives,[r["score"] for r in negative]),grouped_95_interval=interval(samples),
        n_stego=len(positives),n_unique_control_artifacts=len(negative),
        n_independent_trace_ids=len({r["trace_id"] for r in negative}),
        failed_deliveries_included=sum(not rows[g["id"],method]["exact_complete"] for g in groups
            if (g["id"],method) in rows and groups.index(g) in positive_groups),
        excluded=excluded,control_duplicates=duplicates,
        valid_bootstrap_replicates=sum(math.isfinite(x) for x in samples))


def csv_write(path,rows,fields):
    with path.open("w",newline="",encoding="utf-8") as out:
        writer=csv.DictWriter(out,fieldnames=fields,extrasaction="ignore");writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k)
                             for k in fields})


def interval_plot(path,title,items,chance=None):
    width=860;left=340;span=400;top=65;step=30;height=top+step*len(items)+55
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="16" y="25" font-family="sans-serif" font-size="17">{html.escape(title)}</text>']
    for tick in (0,.25,.5,.75,1):
        x=left+span*tick
        parts += [f'<line x1="{x}" y1="{top-18}" x2="{x}" y2="{height-35}" stroke="#e3e7eb"/>',
                  f'<text x="{x}" y="{height-13}" text-anchor="middle" font-family="sans-serif" font-size="11">{tick:g}</text>']
    if chance is not None:
        x=left+span*chance
        parts.append(f'<line x1="{x}" y1="{top-18}" x2="{x}" y2="{height-35}" stroke="#777" stroke-dasharray="4,4"/>')
    for index,(label,value,bounds,method) in enumerate(items):
        y=top+step*index;color={"fixed":"#167339","gated":"#0969da","arithmetic":"#8250df"}[method]
        parts.append(f'<text x="16" y="{y+4}" font-family="sans-serif" font-size="12">{html.escape(label)}</text>')
        if value is not None:
            x=left+span*value
            if bounds:
                parts.append(f'<line x1="{left+span*bounds[0]}" x2="{left+span*bounds[1]}" y1="{y}" y2="{y}" stroke="{color}" stroke-width="2"/>')
            parts += [f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>',
                      f'<text x="{left+span+12}" y="{y+4}" font-family="sans-serif" font-size="12">{value:.3f}</text>']
    parts.append("</svg>")
    path.write_text("\n".join(parts)+"\n",encoding="utf-8")


def analyze(review):
    started=time.perf_counter();review=review.resolve()
    manifest=json.loads((review/"manifest.json").read_text())
    spec=manifest["analysis"];rows=[json.loads(line) for line in (review/"results.jsonl").read_text().splitlines()]
    costs=json.loads((review/"compute_projection.json").read_text())
    by_cost={r["work_id"]:r for r in costs["observations"]}
    for row in rows:
        row.update(by_cost.get(row["work_id"],{}))
        row["exact_complete"]=int(row["exact_recovery"] and row["carrier_complete"] and row["evidence_valid"])
        # Failures do not acquire goodput from offered source length or recovered prefix bits.
        symbols=row.get("delivered_tokens") if row["direction"]=="image-to-text" else row.get("channels")
        row["exact_goodput_bits_per_symbol"]=(8*row["source_bytes"]/symbols if row["exact_complete"] else 0.) if symbols else 0.
        row["whole_surprisal_bits"]=row.get("diagnostics",{}).get("whole",{}).get("surprisal_bits_mean")
        row["whole_log_rank"]=row.get("diagnostics",{}).get("whole",{}).get("log_rank_mean")
    by_pair={(r["pair_id"],r["method"]):r for r in rows}
    if len(by_pair)!=len(rows):raise ValueError("duplicate prospective observation")
    controls=json.loads((review/"control_links.json").read_text());by_link={r["work_id"]:r for r in controls}
    cells=[];pairs=[];detection=[]
    for number,direction in enumerate(DIRECTIONS):
        groups=[g for g in manifest["groups"] if g["direction"]==direction]
        draws=group_draws(groups,spec["bootstrap_replicates"],spec["bootstrap_seed"]+number)
        for method in METHODS:
            selected=[by_pair[g["id"],method] for g in groups if (g["id"],method) in by_pair]
            attempted=[r for r in selected if r["attempted"]]
            n=len(attempted);exact=sum(r["exact_complete"] for r in attempted)
            complete_packets=sum(r["packet_complete"] for r in attempted)
            fields=("exact_goodput_bits_per_symbol","charged_pair_seconds","encode_seconds","decode_seconds",
                    "charged_encode_seconds","charged_decode_seconds","cold_load_seconds","other_occupied_seconds",
                    "whole_surprisal_bits","whole_log_rank","useful_bits_per_token","useful_bits_per_channel",
                    "useful_bits_per_pixel","packet_transport_bits_per_symbol","serialized_expansion",
                    "framing_bytes","slot_padding_bytes","packet_positions","skipped_positions","zero_bit_positions",
                    "termination_positions","termination_suffix_bits","lookahead_zero_bits","completion_symbols")
            metrics={field:mean_interval([by_pair.get((g["id"],method),{}).get(field) for g in groups],draws) for field in fields}
            delivered=sum((r.get("delivered_tokens") or r.get("channels") or 0) for r in attempted)
            source_bits=sum(8*r["source_bytes"] for r in attempted)
            exact_bits=sum(8*r["source_bytes"] for r in attempted if r["exact_complete"])
            cell=dict(direction=direction,method=method,n_expected=20,n_attempted=n,exact_recovery_count=exact,
                authenticated_count=sum(r["authenticated"] for r in attempted),sender_packet_completed=complete_packets,
                sender_carrier_completed=sum(r["sender_carrier_complete"] for r in attempted),
                receiver_packet_completed=sum(r["receiver_packet_complete"] for r in attempted),
                receiver_carrier_conformant=sum(r["receiver_carrier_complete"] for r in attempted),
                authenticated_source_equal_count=sum(r["exact_recovery"] for r in attempted),
                exact_rate=exact/n if n else None,recovery_95_interval=clopper_pearson(exact,n) if n else None,
                exact_per_completed_packet=exact/complete_packets if complete_packets else None,
                failures=dict(Counter((r["failure_stage"] or r["outcome_class"]) for r in attempted if not r["exact_complete"])),
                rate_unit="bits/token" if direction=="image-to-text" else "bits/channel value",
                metrics=metrics,aggregate_offered_bits_per_symbol=source_bits/delivered if delivered else None,
                aggregate_exact_goodput_bits_per_symbol=exact_bits/delivered if delivered else None,
                aggregate_exact_goodput_bits_per_pixel=3*exact_bits/delivered if delivered and direction=="text-to-image" else None,
                charged_total_seconds=sum(r["charged_pair_seconds"] for r in attempted),
                packet_prefix_bits=[dict(case=r["case"],bits=r.get("packet_bits_recovered"),
                    packet_complete=r["packet_complete"],authenticated=r["authenticated"]) for r in attempted])
            cells.append(cell)
            for score in spec["scores"]:detection.append(detection_cell(groups,method,score,by_pair,by_link,draws))
        for a,b in spec["paired_order"]:
            for metric in spec["paired_metrics"]:
                values=[];a_flags=[];b_flags=[]
                for g in groups:
                    ra=by_pair.get((g["id"],a),{});rb=by_pair.get((g["id"],b),{})
                    va=ra.get(metric);vb=rb.get(metric)
                    values.append(va-vb if va is not None and vb is not None else None)
                    if va is not None and vb is not None:
                        a_flags.append(ra["exact_complete"]);b_flags.append(rb["exact_complete"])
                result=dict(direction=direction,method_a=a,method_b=b,metric=metric,**mean_interval(values,draws))
                if metric=="exact_complete" and a_flags:
                    ia=clopper_pearson(sum(a_flags),len(a_flags),.975)
                    ib=clopper_pearson(sum(b_flags),len(b_flags),.975)
                    result["boundary_aware_conservative_95_bound"]=[max(-1,ia[0]-ib[1]),min(1,ia[1]-ib[0])]
                pairs.append(result)
    analysis=dict(specification=spec,manifest_sha256=sha256_file(review/"manifest.json"),cells=cells,
        paired_differences=pairs,detectability=detection,bootstrap_dependencies_preserved=True,
        limitations=["20 frozen, stratified payload groups per direction; not a representative population or statistical-power claim",
          "Exact-binomial recovery bounds use a Bernoulli working model; group bootstrap preserves allocated class/length strata",
          "Collapsed paired bootstrap intervals describe observed data only; binary differences also have conservative boundary-aware bounds",
          "AUC uses frozen higher-is-stego scores, including values below .5; no sign/threshold chosen from held-out labels",
          "Inline mean surprisal/log2-rank under the known model/context are exploratory observers, not unknown-detector or human security"],
        statistical_content_sha256=canonical_hash(dict(cells=cells,paired=pairs,detection=detection)),
        reporting_source_sha256=sha256_file(__file__),cpu_seconds=time.perf_counter()-started)
    atomic_json(review/"analysis.json",analysis,replace=True)
    recovery=[dict(direction=c["direction"],method=c["method"],n=c["n_attempted"],exact=c["exact_recovery_count"],
                   rate=c["exact_rate"],interval=c["recovery_95_interval"],goodput=c["metrics"]["exact_goodput_bits_per_symbol"]["mean"],
                   unit=c["rate_unit"],charged_seconds=c["charged_total_seconds"],failures=c["failures"]) for c in cells]
    csv_write(review/"recovery_rates.csv",recovery,["direction","method","n","exact","rate","interval","goodput","unit","charged_seconds","failures"])
    csv_write(review/"paired_differences.csv",pairs,["direction","method_a","method_b","metric","n","mean","grouped_95_interval","boundary_aware_conservative_95_bound"])
    csv_write(review/"detectability.csv",detection,["direction","method","score","auc","grouped_95_interval","n_stego","n_unique_control_artifacts","failed_deliveries_included","valid_bootstrap_replicates","excluded","control_duplicates"])
    interval_plot(review/"recovery.svg","Exact completed artifact recovery — 95% Clopper-Pearson intervals",
        [(c["direction"]+" / "+c["method"]+f' ({c["exact_recovery_count"]}/{c["n_attempted"]})',c["exact_rate"],c["recovery_95_interval"],c["method"]) for c in cells])
    interval_plot(review/"detectability.svg","Exploratory whole-carrier AUC — 95% grouped bootstrap intervals",
        [(c["direction"]+" / "+c["method"]+" / "+("surprisal" if c["score"].startswith("surprisal") else "log2-rank"),
          c["auc"],c["grouped_95_interval"],c["method"]) for c in detection],chance=.5)
    print(json.dumps(dict(cells=[{k:c[k] for k in ("direction","method","n_attempted","exact_recovery_count","exact_rate")} for c in cells],
                          statistical_content_sha256=analysis["statistical_content_sha256"],cpu_seconds=analysis["cpu_seconds"])))
    return analysis


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--review",type=Path,required=True)
    args=parser.parse_args();analyze(args.review)
