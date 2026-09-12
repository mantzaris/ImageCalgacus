"""Public CPU evaluation and publication exports for retained cover_rank_v1.
No model loading, key access or generation. Private preservation/accounting audit
is separately requested with --private-audit.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import textwrap
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from imagecalgacus.image_backend import read_png
from imagecalgacus.cover_rank import SHAPE,BITS,coarse
from imagecalgacus.runtime import ROOT,sha256_file,atomic_json

REVIEW=ROOT/"artifacts/cover_rank_v1_review"
COLORS={"model_rank":"#0072B2","parity":"#D55E00"}

def metrics(cover,stego):
    delta=stego.astype(np.int32)-cover.astype(np.int32)
    mse=float(np.mean(delta.astype(np.float64)**2))
    a,b=cover.astype(np.float64),stego.astype(np.float64)
    scores=[]
    # Valid-center Gaussian SSIM, window 11, sigma1.5, population covariance.
    for c in range(3):
        x,y=a[:,:,c],b[:,:,c]
        f=lambda z:gaussian_filter(z,sigma=1.5,truncate=3.5,mode="reflect")
        ux,uy=f(x),f(y)
        vx,vy=f(x*x)-ux*ux,f(y*y)-uy*uy
        cov=f(x*y)-ux*uy
        s=((2*ux*uy+(.01*255)**2)*(2*cov+(.03*255)**2))/((ux*ux+uy*uy+(.01*255)**2)*(vx+vy+(.03*255)**2))
        scores.append(float(s[5:-5,5:-5].mean()))
    return {"mse":mse,"psnr_db":float(10*np.log10(255**2/mse)) if mse else None,
        "ssim":float(np.mean(scores)),"max_channel_change":int(np.max(np.abs(delta))),
        "changed_pixel_fraction":float(np.any(delta!=0,axis=2).mean()),
        "changed_channel_fraction":float((delta!=0).mean()),
        "coarse_invariant":bool(np.array_equal(coarse(cover),coarse(stego)))}

def write_csv(path,rows):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def save_figure(fig,stem):
    for suffix in ("pdf","svg","png"):
        fig.savefig(REVIEW/(stem+"."+suffix),dpi=400,facecolor="white",
            metadata={"Creator":"ImageCalgacus retained evidence"} if suffix=="pdf" else None)
    plt.close(fig)

def figures(manifest,rows):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"pdf.fonttype":42,"ps.fonttype":42,
                         "axes.titlesize":10,"svg.hashsalt":"cover-rank-v1"})
    groups=[g for g in manifest["groups"] if g["split"]=="heldout"][:3]
    fig,axes=plt.subplots(3,3,figsize=(7.05,7.1))
    for j,g in enumerate(groups):
        cover=read_png(REVIEW/g["cover"],SHAPE)
        stego=read_png(REVIEW/"outcomes"/(g["id"]+"-model_rank")/"carrier.png",SHAPE)
        difference=np.minimum(255,32*np.abs(stego.astype(int)-cover.astype(int))).astype(np.uint8)
        for k,pixels in enumerate((cover,stego,difference)):
            axes[j,k].imshow(pixels,interpolation="nearest");axes[j,k].set_xticks([]);axes[j,k].set_yticks([])
            for spine in axes[j,k].spines.values():spine.set_visible(False)
        axes[j,0].set_ylabel("BSDS "+g["bsds_id"],fontsize=9)
    for ax,title in zip(axes[0],("Canonical cover","Delivered model-rank PNG","Absolute difference ×32")):ax.set_title(title)
    fig.subplots_adjust(left=.075,right=.99,bottom=.02,top=.95,wspace=.05,hspace=.05)
    save_figure(fig,"cover_examples")
    g=groups[0];source=(REVIEW/g["source"]).read_text()
    recovered=(REVIEW/"outcomes"/(g["id"]+"-model_rank")/"recovered.txt").read_text()
    fig=plt.figure(figsize=(7.05,3.05))
    ax1=fig.add_axes([.025,.12,.29,.75]);ax2=fig.add_axes([.34,.10,.32,.78]);ax3=fig.add_axes([.685,.12,.29,.75])
    for ax in (ax1,ax3):ax.axis("off")
    ax1.set_title("A  Complete source text",loc="left",fontweight="bold")
    ax1.text(0,.78,textwrap.fill(source,width=24),va="top",fontsize=10,linespacing=1.5)
    ax1.text(0,.12,str(g["source_bytes"])+" literal UTF-8 bytes",fontsize=8)
    ax2.imshow(read_png(REVIEW/"outcomes"/(g["id"]+"-model_rank")/"carrier.png",SHAPE),interpolation="nearest")
    ax2.set_title("B  Delivered photograph",fontweight="bold");ax2.axis("off")
    ax3.set_title("C  Complete recovered text",loc="left",fontweight="bold")
    ax3.text(0,.78,textwrap.fill(recovered,width=24),va="top",fontsize=10,linespacing=1.5)
    ax3.text(0,.12,"Authenticated and byte-identical",fontsize=8)
    fig.text(.5,.035,"BSDS "+g["bsds_id"]+"  •  256 × 256 RGB8  •  saved PNG, fresh GPU receiver",ha="center",fontsize=8)
    save_figure(fig,"text_photo_example")

def summarize(rows):
    summary=[]
    for split,n in (("development",6),("heldout",20)):
        for arm in ("model_rank","parity"):
            selected=[r for r in rows if r["split"]==split and r["arm"]==arm]
            s={"split":split,"arm":arm,"attempted":len(selected),"expected":n,
               "exact":sum(r["exact_recovery"] for r in selected)}
            for field in ("psnr_db","ssim","changed_pixel_fraction","changed_channel_fraction","png_bytes",
                          "source_bytes","sender_seconds","receiver_seconds","pair_seconds","partition_disagreement"):
                values=[r[field] for r in selected if r[field] is not None]
                s["mean_"+field]=float(np.mean(values)) if values else None
                s["min_"+field]=float(np.min(values)) if values else None
                s["max_"+field]=float(np.max(values)) if values else None
            s["maximum_channel_change"]=max(r["max_channel_change"] for r in selected)
            summary.append(s)
    return summary

def table(summary):
    columns=["Split / arm","Exact","PSNR (dB)","SSIM","Changed pixels (%)","PNG bytes","Encode / decode (s)"]
    formatted=[]
    for r in summary:
        formatted.append([r["split"]+" / "+r["arm"].replace("_"," "),
            str(r["exact"])+"/"+str(r["attempted"]),f'{r["mean_psnr_db"]:.3f}',
            f'{r["mean_ssim"]:.7f}',f'{100*r["mean_changed_pixel_fraction"]:.3f}',
            f'{r["mean_png_bytes"]:.1f}',f'{r["mean_sender_seconds"]:.3f} / {r["mean_receiver_seconds"]:.3f}'])
    (REVIEW/"summary.md").write_text("| "+" | ".join(columns)+" |\n| "+" | ".join(["---"]*len(columns))+" |\n"+
        "\n".join("| "+" | ".join(row)+" |" for row in formatted)+"\n")
    (REVIEW/"summary.tex").write_text("\\begin{tabular}{llrrrrr}\n\\hline\n"+
        "Split / arm & Exact & PSNR & SSIM & Pixels (\\%) & PNG bytes & Enc. / dec. (s) \\\\\n\\hline\n"+
        "\n".join(" & ".join(row)+" \\\\" for row in formatted)+"\n\\hline\n\\end{tabular}\n")

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--private-audit",action="store_true")
    parser.add_argument("--verify-only",action="store_true");args=parser.parse_args()
    manifest=json.loads((REVIEW/"manifest.json").read_text())
    rows=[]
    expected=set(manifest["execution_order"])
    found={p.parent.name for p in (REVIEW/"outcomes").glob("*/result.json")}
    if found!=expected:raise ValueError("allocation incomplete or unexpected: "+str(expected^found))
    for g in manifest["groups"]:
        if sha256_file(REVIEW/g["cover"])!=g["cover_sha256"] or sha256_file(REVIEW/g["source"])!=g["source_sha256"]:
            raise ValueError("source changed")
        cover=read_png(REVIEW/g["cover"],SHAPE)
        for arm in g["arms"]:
            name=g["id"]+"-"+arm;folder=REVIEW/"outcomes"/name
            r=json.loads((folder/"result.json").read_text())
            if r["work_id"]!=name:raise ValueError("work identity mismatch")
            stego=read_png(folder/"carrier.png",SHAPE)
            if sha256_file(folder/"carrier.png")!=r["carrier_sha256"] or (folder/"recovered.txt").read_bytes()!=(REVIEW/g["source"]).read_bytes():
                raise ValueError("carrier or source equality mismatch")
            sender=json.loads((REVIEW/"jobs"/(name+"-sender.json")).read_text())
            receiver=json.loads((REVIEW/"jobs"/(name+"-receiver.json")).read_text())
            if not all(r[k] for k in ("packet_complete","carrier_complete","authenticated",
                                     "exact_recovery","rank_streams_equal","packet_pairing_verified")):
                raise ValueError("incomplete or unsuccessful saved outcome")
            if sender["returncode"]!=0 or receiver["returncode"]!=0 or not receiver["report"].get("authenticated"):
                raise ValueError("recorded receiver did not authenticate")
            if r["sender_job"]!=sender["id"] or r["receiver_job"]!=receiver["id"]:
                raise ValueError("job identity mismatch")
            if sender["report"]["model_calls"]!=(64 if arm=="model_rank" else 0) or receiver["report"]["model_calls"]!=(64 if arm=="model_rank" else 0):
                raise ValueError("unexpected forward count")
            if sender["report"].get("digests")!=receiver["report"].get("digests"):
                raise ValueError("rank stream mismatch")
            m=metrics(cover,stego)
            if not m["coarse_invariant"] or m["max_channel_change"]>3 or m["psnr_db"]<10*np.log10(255**2/(9*2336/65536))-1e-10:
                raise ValueError("distortion bound violation")
            rows.append({**r,**m,"png_bytes":(folder/"carrier.png").stat().st_size,
                "pair_seconds":r["sender_seconds"]+r["receiver_seconds"],
                "packet_bits_per_pixel":BITS/65536,"useful_bits_per_pixel":8*r["source_bytes"]/65536,
                "partition_disagreement":sender["report"].get("partition_disagreement_up_to_swap_mean"),
                "nonidentical_partitions":sender["report"].get("nonidentical_partitions"),
                "model_calls_sender":sender["report"]["model_calls"],
                "model_calls_receiver":receiver["report"]["model_calls"]})
    summary=summarize(rows)
    paired=[]
    for g in manifest["groups"]:
        a=next(r for r in rows if r["group"]==g["id"] and r["arm"]=="model_rank")
        b=next(r for r in rows if r["group"]==g["id"] and r["arm"]=="parity")
        paired.append({"group":g["id"],"split":g["split"],
            **{k+"_model_minus_parity":a[k]-b[k] for k in ("psnr_db","ssim","mse","changed_pixel_fraction","changed_channel_fraction","pair_seconds","png_bytes")},
            "carrier_bytes_differ":a["carrier_sha256"]!=b["carrier_sha256"]})
    jobs=[json.loads(p.read_text()) for p in (REVIEW/"jobs").glob("*.json")]
    if len({j["id"] for j in jobs})!=len(jobs):raise ValueError("duplicate charged job")
    budget={"stage":"cover_rank_v1","limit_seconds":7200,"charged_seconds":sum(j["elapsed_seconds"] for j in jobs),
        "neural_occupied_seconds":sum(j["elapsed_seconds"] for j in jobs if j["neural_inference"]),
        "model_free_child_seconds_charged_conservatively":sum(j["elapsed_seconds"] for j in jobs if not j["neural_inference"]),
        "jobs":len(jobs),"neural_jobs":sum(j["neural_inference"] for j in jobs),
        "history_seconds":manifest["history_seconds"]}
    budget["remaining_stage_seconds"]=7200-budget["charged_seconds"]
    budget["cumulative_seconds"]=sum(manifest["history_seconds"].values())+budget["charged_seconds"]
    budget["remaining_whole_project_seconds"]=144000-budget["cumulative_seconds"]
    if budget["remaining_stage_seconds"]<0 or budget["remaining_whole_project_seconds"]<0:raise ValueError("budget exceeded")
    if any(j["neural_inference"] and j["gpu_activity"]["positive_samples"]<=0 for j in jobs):raise ValueError("missing GPU activity")
    acceptance={"allocation_complete":True,"attempted":len(rows),"exact":sum(r["exact_recovery"] for r in rows),
        "development_exact":sum(r["exact_recovery"] for r in rows if r["split"]=="development"),
        "heldout_exact":sum(r["exact_recovery"] for r in rows if r["split"]=="heldout"),
        "focused_checks":json.loads((REVIEW/"development_checks.json").read_text()),
        "theoretical_psnr_lower_bound_db":float(10*np.log10(255**2/(9*2336/65536))),
        "public_verification":"saved evidence, hashes, equality and coverage; not fresh private-key decoding"}
    if args.private_audit:
        from imagecalgacus.runtime import budget_state
        baseline=json.loads((ROOT/".runtime/cover_rank_v1/preservation.json").read_text())
        changed=[p for p,h in baseline.items() if sha256_file(ROOT/p)!=h]
        if changed:raise ValueError("accepted evidence changed: "+str(changed[:5]))
        if abs(budget_state("cover_rank_v1")[0]-budget["charged_seconds"])>1e-8:raise ValueError("ledger mismatch")
        private={"unchanged_protected_files":len(baseline),"ledger_reconciled":True}
        # Scan public content for complete private key or packet representations.
        secrets=[p.read_bytes() for p in (ROOT/"runs/cover-rank-v1-001").glob("*.packet")]
        secrets+=[(ROOT/"runs/cover-rank-v1-001/run.key").read_bytes()]
        import base64
        patterns=[v for s in secrets for v in (s,s.hex().encode(),base64.b64encode(s))]
        for p in REVIEW.rglob("*"):
            if p.is_symlink() or p.suffix in (".key",".packet",".pth",".pt"):
                raise ValueError("forbidden public file "+str(p))
            if p.is_file() and any(s in p.read_bytes() for s in patterns):
                raise ValueError("private material in public file "+str(p))
        private["secret_scan_passed"]=True
        atomic_json(REVIEW/"private_preservation_check.json",private,replace=True)
    if args.verify_only:
        stored=json.loads((REVIEW/"acceptance.json").read_text())
        if stored!=acceptance:raise ValueError("saved acceptance summary disagrees")
        for filename,expected_rows in (("per_case.csv",rows),("summary.csv",summary),("paired.csv",paired)):
            with (REVIEW/filename).open(newline="") as stream:
                saved_rows=list(csv.DictReader(stream))
            expected_text=[{k:"" if v is None else str(v) for k,v in row.items()} for row in expected_rows]
            if saved_rows!=expected_text:raise ValueError("exported values disagree: "+filename)
        if [json.loads(line) for line in (REVIEW/"results.jsonl").read_text().splitlines()]!=rows:
            raise ValueError("JSONL results disagree")
        if json.loads((REVIEW/"budget.json").read_text())!=budget:
            raise ValueError("exported budget disagrees")
        print(json.dumps(acceptance));return
    write_csv(REVIEW/"per_case.csv",rows)
    write_csv(REVIEW/"summary.csv",summary)
    write_csv(REVIEW/"paired.csv",paired)
    (REVIEW/"results.jsonl").write_text("".join(json.dumps(r,allow_nan=False)+"\n" for r in rows))
    atomic_json(REVIEW/"acceptance.json",acceptance,replace=True)
    atomic_json(REVIEW/"budget.json",budget,replace=True)
    atomic_json(REVIEW/"paired_summary.json",{
        split:{k:float(np.mean([r[k] for r in paired if r["split"]==split]))
               for k in paired[0] if k.endswith("_model_minus_parity")}
        for split in ("development","heldout")},replace=True)
    table(summary);figures(manifest,rows)
    atomic_json(REVIEW/"output_provenance.json",{"script_sha256":sha256_file(__file__),
        "manifest_sha256":sha256_file(REVIEW/"manifest.json"),"numpy":np.__version__,
        "scipy":__import__("scipy").__version__,"pillow":Image.__version__,"matplotlib":matplotlib.__version__,
        "inputs":{str(p.relative_to(REVIEW)):sha256_file(p) for p in sorted((REVIEW/"outcomes").rglob("*")) if p.is_file()},
        "analysis_gpu_seconds":0,"descriptive_only":True},replace=True)
    print(json.dumps({"acceptance":acceptance,"budget":budget,"summary":summary},indent=2))
if __name__=="__main__":main()
