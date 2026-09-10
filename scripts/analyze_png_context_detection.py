"""CPU-only paired AUC analysis and compact public export of frozen PNG scores."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import atomic_json,sha256_file,budget_state,phase_limit,DEFAULT_PHASE_LIMITS
from imagecalgacus.png_context_detection import REVIEW,MANIFEST,STAGE,METHODS,SCORES,read,jobs
from analyze_v2 import group_draws,auc,interval
from collect_gpu_performance import compact_job


def paired_auc(correct_stego,correct_control,mismatch_stego,mismatch_control,draws):
    """One frozen set of group weights for both observer conditions."""
    arrays=[np.asarray(a,dtype=np.float64) for a in
            (correct_stego,correct_control,mismatch_stego,mismatch_control)]
    valid=np.all(np.isfinite(arrays),axis=0)
    indices=np.flatnonzero(valid)
    selected=[a[valid] for a in arrays]
    sampled=[[],[],[]]
    for draw in draws:
        weights=np.bincount(draw,minlength=len(valid))[indices]
        old=auc(selected[0],selected[1],weights,weights)
        new=auc(selected[2],selected[3],weights,weights)
        sampled[0].append(np.nan if old is None else old)
        sampled[1].append(np.nan if new is None else new)
        sampled[2].append(np.nan if old is None or new is None else new-old)
    old=auc(selected[0],selected[1]);new=auc(selected[2],selected[3])
    return dict(correct_auc_paired=old,mismatch_auc=new,
        difference=None if old is None or new is None else new-old,
        correct_paired_95_interval=interval(sampled[0]),mismatch_95_interval=interval(sampled[1]),
        difference_95_interval=interval(sampled[2]),scorable_stego=len(indices),
        unique_controls=len(indices),excluded_group_indices=np.flatnonzero(~valid).tolist(),
        valid_bootstrap_replicates=[int(np.isfinite(a).sum()) for a in sampled])


def write_csv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def summarize(manifest,rows):
    lookup={r["artifact_id"]:r for r in rows}
    accepted=read(ROOT/"artifacts/v2_review/analysis.json")["detectability"]
    draws=group_draws(manifest["groups"],manifest["analysis"]["bootstrap_replicates"],manifest["analysis"]["seed"])
    cells=[]
    for method in METHODS:
        for score in SCORES:
            arrays=[[],[],[],[]]
            for group in manifest["groups"]:
                stego=lookup[group["id"]+"-"+method];control=lookup[stego["control_id"]]
                for values,row,condition in zip(arrays,[stego,control,stego,control],
                                                ["correct_scores"]*2+["mismatch_scores"]*2):
                    item=row.get(condition) or {}
                    values.append(item.get(score,np.nan))
            result=paired_auc(*arrays,draws)
            old=next(c for c in accepted if c["direction"]=="text-to-image" and c["method"]==method and c["score"]==score)
            # Independently reproduce accepted row1 endpoints without any new inference.
            original=paired_auc(arrays[0],arrays[1],arrays[0],arrays[1],draws)
            if original["correct_auc_paired"]!=old["auc"] or original["correct_paired_95_interval"]!=old["grouped_95_interval"]:
                raise ValueError("accepted AUC/interval definitions did not reproduce")
            cells.append(dict(method=method,score=score,correct_auc=old["auc"],
                correct_95_interval=old["grouped_95_interval"],correct_stego_count=old["n_stego"],
                correct_unique_controls=old["n_unique_control_artifacts"],**result))
    return dict(specification=manifest["analysis"],score_orientation="higher means stego",
        independent_payload_groups=20,independent_controls=20,cells=cells,
        interpretation="one context mismatch, exact model known; exploratory paired repeated measurements, no score reversal or threshold selection",
        retained_correct_context_results="artifacts/v2_review/analysis.json")


def make_table(analysis):
    rows=[]
    for c in analysis["cells"]:
        row={k:c[k] for k in ("method","score","correct_auc","mismatch_auc","difference",
                              "scorable_stego","unique_controls")}
        for stem,key in (("correct","correct_95_interval"),("mismatch","mismatch_95_interval"),("difference","difference_95_interval")):
            ci=c[key] or [None,None];row[stem+"_ci_low"],row[stem+"_ci_high"]=ci
        rows.append(row)
    write_csv(REVIEW/"comparison.csv",rows)
    def entry(value,ci):
        return "unscorable" if value is None else f"{value:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"
    lines=["| Method | Score | Row1 AUC [95% CI] | Row2 AUC [95% CI] | Paired difference [95% CI] | Stego / unique controls |",
           "|---|---|---|---|---|---|"]
    latex=[r"\begin{tabular}{llcccc}",r"\hline",
           r"Method & Score & Row1 AUC (95\% CI) & Row2 AUC (95\% CI) & Difference (95\% CI) & $n_s/n_c$ \\",r"\hline"]
    for c in analysis["cells"]:
        fields=[{"fixed":"Fixed rank","gated":"Entropy gated","arithmetic":"Arithmetic A1"}[c["method"]],
            "Mean surprisal" if c["score"]==SCORES[0] else "Mean log2 rank",
            entry(c["correct_auc"],c["correct_95_interval"]),
            entry(c["mismatch_auc"],c["mismatch_95_interval"]),
            entry(c["difference"],c["difference_95_interval"]),
            str(c["scorable_stego"])+" / "+str(c["unique_controls"])]
        lines.append("| "+" | ".join(fields)+" |")
        latex.append(" & ".join(fields)+r" \\")
    lines+=["","Difference = row2 minus row1. Higher scores always indicate stego. Paired length-stratified payload-group bootstrap, 2,000 replicates; 20 groups, not 60 independent controls. Row1 values and intervals are reused from accepted V2 evidence. No classification threshold is fitted."]
    latex += [r"\hline",r"\end{tabular}"]
    (REVIEW/"comparison.md").write_text("\n".join(lines)+"\n")
    (REVIEW/"comparison.tex").write_text("\n".join(latex)+"\n")


def make_figure(analysis):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,
        "axes.spines.right":False,"svg.fonttype":"none","pdf.fonttype":42,
        "figure.facecolor":"white","axes.facecolor":"white"})
    cells=[c for c in analysis["cells"] if c["score"]==SCORES[0]]
    fig,(a,b)=plt.subplots(1,2,figsize=(7.2,3.25),gridspec_kw={"width_ratios":[1.8,1]})
    colors=["#0072B2","#D55E00"]
    for index,c in enumerate(cells):
        y=2-index
        for j,(key,ci_key,label) in enumerate((("correct_auc","correct_95_interval","Correct context (row1)"),
                                               ("mismatch_auc","mismatch_95_interval","Mismatched context (row2)"))):
            value=c[key];ci=c[ci_key]
            if value is not None:
                a.errorbar(value,y+(.12 if j==0 else -.12),xerr=[[value-ci[0]],[ci[1]-value]],
                    color=colors[j],marker=["o","D"][j],ms=5,capsize=3,lw=1.3,label=label if index==0 else None)
        value=c["difference"];ci=c["difference_95_interval"]
        if value is not None:
            b.errorbar(value,y,xerr=[[value-ci[0]],[ci[1]-value]],color="#333333",marker="s",ms=5,capsize=3,lw=1.3)
            b.text(.98,y+.22,f"{value:+.3f}",transform=b.get_yaxis_transform(),ha="right",fontsize=8)
    a.set(yticks=[2,1,0],yticklabels=["Fixed rank","Entropy gated","Arithmetic A1"],
        xlim=(0,1),ylim=(-.45,2.55),xlabel="AUC (higher score = stego)",title="A   Observer context")
    b.set(yticks=[2,1,0],yticklabels=[],ylim=(-.45,2.55),xlabel="AUC difference (row2 − row1)",
        title="B   Paired change")
    extent=max(.15,max(abs(v) for c in cells for v in (c["difference_95_interval"] or [0])))
    extent=math.ceil(extent*10)/10
    b.set_xlim(-extent,extent)
    a.axvline(.5,color=".65",ls=":",lw=1,zorder=0);b.axvline(0,color=".65",ls=":",lw=1,zorder=0)
    for ax in (a,b): ax.grid(axis="x",alpha=.15);ax.set_axisbelow(True)
    handles,labels=a.get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.53,.105),ncol=2,frameon=False,fontsize=8.5)
    fig.text(.52,.035,"Same 80 PNGs; 20 payload groups; mean surprisal; paired 95% grouped intervals",
             ha="center",fontsize=8)
    fig.subplots_adjust(left=.16,right=.98,top=.87,bottom=.32,wspace=.28)
    for suffix in ("pdf","svg","png"):
        fig.savefig(REVIEW/("context_auc."+suffix),dpi=400,facecolor="white")
    plt.close(fig)


def collect():
    manifest=read(MANIFEST);rows=[]
    for item in manifest["artifacts"]:
        terminal=read(REVIEW/"terminals"/(item["observer_id"]+".json"))
        report=read(REVIEW/terminal["report"])
        rows.append({**item,"mismatch_scores":report["scores"],"scorable":report["passed"],
            "scored_channels":report["scored_channels"],"failure_stage":report["failure_stage"],
            "failure_reason":report["failure_reason"],"observer_report":terminal["report"],
            "observer_report_sha256":terminal["report_sha256"],"job_id":terminal["job_id"],
            "charged_seconds":terminal["charged_seconds"],"scoring_seconds":report.get("scoring_seconds"),
            "cold_load_seconds":report.get("cold_load_seconds"),"source_hash":report["source_hash"],
            "observer_profile_id":report["profile_id"],"context_sha256":report["context_sha256"],
            "model_sha256":report["model_id"],"gpu_device":report["gpu_evidence"]["device"]["uuid"]})
    (REVIEW/"results.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False,allow_nan=False)+"\n" for r in rows))
    analysis=summarize(manifest,rows)
    atomic_json(REVIEW/"analysis.json",analysis,replace=True)
    make_table(analysis);make_figure(analysis)
    compact=[compact_job(j) for j in jobs()]
    atomic_json(REVIEW/"gpu_jobs.json",compact,replace=True)
    usage={s:budget_state(s)[0] for s in DEFAULT_PHASE_LIMITS}
    accounting=dict(charged_seconds_by_stage=usage,new_charged_seconds=usage[STAGE],
        cumulative_seconds=sum(usage.values()),extension_limit_seconds=phase_limit(STAGE),
        extension_remaining_seconds=phase_limit(STAGE)-usage[STAGE],
        whole_project_limit_seconds=144000,whole_project_remaining_seconds=144000-sum(usage.values()),
        model_jobs=len(compact),validation_seconds=sum(j["charged_seconds"] for j in compact if "validation-" in j["id"]),
        heldout_scoring_seconds=sum(j["charged_seconds"] for j in compact if "score-" in j["id"]),
        convention="occupied child time includes imports, hashing, loading, graph setup, CPU probability bookkeeping, scoring and teardown; CUDA and phase times nested, not added",
        reserve="one 50% forward margin in preflight; no reserve counted as spent")
    atomic_json(REVIEW/"accounting.json",accounting,replace=True)
    coverage=dict(expected_artifacts=80,terminal_artifacts=len(rows),
        unique_artifact_hashes=len({r["carrier_sha256"] for r in rows}),
        independent_payload_groups=len({r["payload_group"] for r in rows}),
        independent_controls=sum(r["kind"]=="control" for r in rows),
        scorable_artifacts=sum(r["scorable"] for r in rows),
        failure_artifacts=[r["artifact_id"] for r in rows if not r["scorable"]],
        allocation_complete=len(rows)==80)
    atomic_json(REVIEW/"coverage.json",coverage,replace=True)
    verify()


def verify():
    """Saved-evidence checks only. No keys, private run directory or GPU access."""
    manifest=read(MANIFEST)
    rows=list(map(json.loads,(REVIEW/"results.jsonl").read_text().splitlines()))
    expected={r["artifact_id"]:r for r in manifest["artifacts"]}
    if len(rows)!=80 or len({r["artifact_id"] for r in rows})!=80 or {r["artifact_id"] for r in rows}!=set(expected):
        raise ValueError("missing, duplicate or unexpected allocation identity")
    job_lookup={j["id"]:j for j in read(REVIEW/"gpu_jobs.json")}
    for r in rows:
        item=expected[r["artifact_id"]]
        for key in item:
            if r[key]!=item[key]:raise ValueError("manifest association changed: "+key)
        if sha256_file(ROOT/r["carrier"])!=r["carrier_sha256"]:
            raise ValueError("accepted PNG bytes changed")
        if sha256_file(REVIEW/r["observer_report"])!=r["observer_report_sha256"]:
            raise ValueError("observer report changed")
        report=read(REVIEW/r["observer_report"]);job=job_lookup[r["job_id"]]
        if report["scores"]!=r["mismatch_scores"] or report["context_sha256"]!=manifest["contexts"]["row2"]["sha256"]:
            raise ValueError("score/context mismatch")
        if r["scorable"] and (report["scored_channels"]!=2976 or report["model_calls"]!=992):
            raise ValueError("incomplete scorable PNG")
        if not job["positive_process_activity"] or report["gpu_evidence"]["execution_mode"]!="cuda_graph":
            raise ValueError("missing CUDA graph execution evidence")
    if summarize(manifest,rows)!=read(REVIEW/"analysis.json"):
        raise ValueError("paired analysis not reproducible")
    public_files=list(REVIEW.rglob("*"))
    forbidden=[str(p) for p in public_files if p.is_file() and
               (p.suffix in (".key",".packet",".pth",".pt",".gguf") or p.name in ("row.rgb","run.key"))]
    if forbidden:raise ValueError("unexpected private/model material in public review")
    result=dict(passed=True,scope="public saved evidence + paired CPU analysis; no fresh inference or private files",
        verified_artifacts=80,unique_controls=20,paired_groups=20,
        row1_analysis_reproduced=True,forbidden_files=forbidden)
    atomic_json(REVIEW/"public_verification.json",result,replace=True)
    print(json.dumps(result),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    (verify if args.verify else collect)()
