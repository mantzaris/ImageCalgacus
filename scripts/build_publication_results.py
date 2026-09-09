"""Publication exports from accepted public evidence only; never runs a model.

Run from any directory: python -B scripts/build_publication_results.py
Existing intervals are read, not refitted. New arithmetic/memory summaries are
descriptive. Writes only artifacts/publication_results/ (plus temporary TeX files).
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import textwrap

os.environ.setdefault("MPLCONFIGDIR", "/tmp/imagecalgacus-publication-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Pure accepted helpers; do not call analyze(), which writes the old review packet.
from analyze_v2 import auc, clopper_pearson
from imagecalgacus.runtime import budget_state

OUT = ROOT / "artifacts/publication_results"
V2 = ROOT / "artifacts/v2_review"
GPU = ROOT / "artifacts/gpu_performance_review"
V1 = ROOT / "artifacts/v1_qualification_review"
METHODS = ("fixed", "gated", "arithmetic")
DIRECTIONS = ("image-to-text", "text-to-image")
NAMES = {"fixed": "Fixed rank", "gated": "Entropy gated", "arithmetic": "Arithmetic A1"}
SHORT = {"fixed": "Fixed", "gated": "Gated", "arithmetic": "A1"}
COLORS = {"fixed": "#0072B2", "gated": "#009E73", "arithmetic": "#D55E00"}
MARKERS = {"fixed": "o", "gated": "s", "arithmetic": "^"}
MODE_COLORS = {"reference": "#666666", "cuda_graph": "#0072B2"}
MODE_NAMES = {"reference": "Reference", "cuda_graph": "CUDA graph"}
SOURCES = {}
FIGURES = []
TABLES = []
CHECKS = []


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path, kind="json"):
    path = Path(path)
    SOURCES[str(path.relative_to(ROOT))] = digest(path)
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw) if kind == "json" else ([json.loads(x) for x in raw.splitlines()] if kind == "jsonl" else raw)


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    CHECKS.append(name)


def close(a, b):
    # Reporting arithmetic agreement, not a relaxation of model equivalence.
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def protected_snapshot():
    paths = []
    for folder in sorted((ROOT / "artifacts").iterdir()):
        if folder.is_dir() and folder != OUT:
            paths.extend(p for p in folder.rglob("*") if p.is_file())
    for folder in ("plan", "configs", "data/qualification_v1", "imagecalgacus"):
        paths.extend(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    paths.extend(ROOT / "notes" / f for f in ("v2_results.md", "gpu_performance.md", "v1_qualification_results.md"))
    paths.extend(p for p in (ROOT / ".runtime").glob("**/gpu_budget.jsonl"))
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths))}


def aggregate_hash(mapping):
    return hashlib.sha256(json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
        "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": .7,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"})


def panel(ax, label, title):
    ax.set_title(f"{label}  {title}", loc="left", fontweight="bold", pad=12)


def save_figure(fig, stem, title, caption, finding, sources):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    undrawn_ticks = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if not lo <= tick.get_loc() <= hi:
                    undrawn_ticks.update((id(tick.label1), id(tick.label2)))
    # Explicit bounds check for all drawn text; skip auto ticks outside the view.
    for item in fig.findobj(matplotlib.text.Text):
        if item.get_visible() and item.get_text() and id(item) not in undrawn_ticks:
            b = item.get_window_extent(renderer)
            if b.width and b.height and (b.x0 < -1 or b.y0 < -1 or b.x1 > canvas.x1 + 1 or b.y1 > canvas.y1 + 1):
                raise ValueError(f"Text outside figure canvas: {stem}: {item.get_text()!r}")
    for extension in ("pdf", "svg", "png"):
        kwargs = {"dpi": 450} if extension == "png" else {}
        if extension == "pdf":
            kwargs["metadata"] = {"Title": title, "Creator": "ImageCalgacus CPU publication builder", "CreationDate": None, "ModDate": None}
        elif extension == "svg":
            kwargs["metadata"] = {"Title": title, "Date": None}
        fig.savefig(OUT / "figures" / f"{stem}.{extension}", **kwargs)
    FIGURES.append(dict(id=stem, title=title, caption=caption, finding=finding, sources=sources))
    plt.close(fig)


def tex_escape(text):
    substitutions = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "→": r"$\rightarrow$", "×": r"$\times$", "–": "--", "—": "---", "−": "$-$", "±": r"$\pm$",
        "≤": r"$\leq$", "≥": r"$\geq$"}
    return "".join(substitutions.get(c, c) for c in str(text)).replace("\n", r"\newline ")


def make_table(stem, title, headers, display_rows, numeric_rows, caption, widths, sources):
    write_csv(OUT / "tables" / f"{stem}.csv", numeric_rows)
    md = f"# {title}\n\n" + "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n"
    md += "\n".join("| " + " | ".join(str(c).replace("\n", "<br>").replace("|", "\\|") for c in row) + " |" for row in display_rows)
    md += f"\n\n{caption}\n"
    (OUT / "tables" / f"{stem}.md").write_text(md, encoding="utf-8")
    # Fixed fractional column widths sum to one; tab separation is subtracted first.
    columns = "@{}" + "".join(r">{\raggedright\arraybackslash}p{" + f"{w:.3f}" + r"\pubtablewidth}" for w in widths) + "@{}"
    body = r"\begin{tabular}{" + columns + "}\n\\toprule\n"
    body += " & ".join(r"\textbf{" + tex_escape(c) + "}" for c in headers) + r" \\" + "\n\\midrule\n"
    body += "\n".join(" & ".join(tex_escape(c) for c in row) + r" \\[4pt]" for row in display_rows)
    body += "\n\\bottomrule\n\\end{tabular}\n"
    snippet = "% Requires booktabs,array; full-precision numerical values are in the adjacent CSV.\n"
    snippet += "\\begin{table*}[t]\n\\centering\n\\small\n\\setlength{\\tabcolsep}{3pt}\n"
    snippet += r"\newlength{\pubtablewidth}" + "\n" if not TABLES else "% Define \\pubtablewidth once in your manuscript preamble.\n"
    snippet += r"\setlength{\pubtablewidth}{\dimexpr\linewidth-" + str(6 * (len(headers)-1)) + r"pt\relax}" + "\n"
    snippet += body + "\\caption{" + tex_escape(title + ". " + caption) + "}\n"
    snippet += "\\label{tab:" + stem + "}\n\\end{table*}\n"
    # Every snippet can also be included independently.
    snippet = snippet.replace(r"\newlength{\pubtablewidth}", r"\ifdefined\pubtablewidth\else\newlength{\pubtablewidth}\fi")
    snippet = snippet.replace("% Define \\pubtablewidth once in your manuscript preamble.", r"\ifdefined\pubtablewidth\else\newlength{\pubtablewidth}\fi")
    (OUT / "tables" / f"{stem}.tex").write_text(snippet, encoding="utf-8")
    # Compile each actual manuscript table for review, without scaling text to fit.
    document = r"""\documentclass[10pt]{article}
\usepackage[paperwidth=8in,paperheight=9in,margin=.45in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,booktabs,array,caption}
\captionsetup{font=small,labelformat=empty}
\pagestyle{empty}
\begin{document}
""" + snippet.replace("[t]", "[!ht]") + "\n\\end{document}\n"
    with tempfile.TemporaryDirectory(prefix="imagecalgacus-publication-tex-") as folder:
        temporary = Path(folder)
        (temporary / "table.tex").write_text(document, encoding="utf-8")
        p = subprocess.run(["pdflatex", "-halt-on-error", "-interaction=nonstopmode", "table.tex"], cwd=temporary, capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(f"LaTeX failed for {stem}: {p.stdout[-3500:]}")
        log = (temporary / "table.log").read_text()
        if "Overfull" in log or "Output written on table.pdf (1 page" not in log:
            raise ValueError(f"Table layout needs attention ({stem}): " + "\n".join(x for x in log.splitlines() if "Overfull" in x or "Output written" in x))
        shutil.copyfile(temporary / "table.pdf", OUT / "tables" / f"{stem}.pdf")
        subprocess.run(["pdftoppm", "-singlefile", "-scale-to", "2000", "-png", str(temporary / "table.pdf"), str(OUT / "tables" / stem)], check=True, capture_output=True)
    TABLES.append(dict(id=stem, title=title, caption=caption, sources=sources, latex_overfull_boxes=0, latex_pages=1))


def load_evidence():
    analysis = read(V2 / "analysis.json")
    manifest = read(V2 / "manifest.json")
    rows = read(V2 / "results.jsonl", "jsonl")
    links = read(V2 / "control_links.json")
    costs = read(V2 / "compute_projection.json")
    cost_by_id = {r["work_id"]: r for r in costs["observations"]}
    for r in rows:
        r.update(cost_by_id[r["work_id"]])
        r["exact_complete"] = bool(r["exact_recovery"] and r["carrier_complete"] and r["evidence_valid"])
        r["delivered_symbols"] = r["delivered_tokens"] if r["direction"] == DIRECTIONS[0] else r["channels"]
        r["recovered_goodput"] = 8*r["source_bytes"]/r["delivered_symbols"] if r["exact_complete"] else 0.
    timings = read(GPU / "timings.json")
    records = read(GPU / "results.jsonl", "jsonl")
    jobs = read(GPU / "gpu_jobs.json")
    job_by_id = {j["id"]: j for j in jobs}
    record_by_id = {r["benchmark_execution_id"]: r for r in records}
    for t in timings["individual"]:
        r = record_by_id[t["comparison"] + "-" + t["mode"]]
        t["sampled_process_peak_mib"] = max(job_by_id[r[k]]["sampled_peak_memory_mib"] for k in ("encode_job", "decode_job"))
    audits = read(V2 / "arithmetic_audits.json")
    static = read(V1 / "static_pairs.json")
    source = read(ROOT / "data/qualification_v1/manifest.json")
    profile = read(V2 / "cases" / manifest["cases"][0]["id"] / "profile.json")
    check("120 unique V2 outcomes equal frozen work IDs", len(rows) == len({r['work_id'] for r in rows}) == 120 and {r['work_id'] for r in rows} == {r['work_id'] for r in manifest['cases']})
    check("40 independent controls, 120 matched links", len(links) == 120 and len({l['trace_id'] for l in links}) == len(manifest['controls']) == 40)
    for cell, expected in zip(analysis["cells"], (20, 20, 0, 20, 20, 20)):
        selected = [r for r in rows if (r['direction'], r['method']) == (cell['direction'], cell['method'])]
        check(f"V2 counts {cell['direction']} {cell['method']}", len(selected) == cell['n_attempted'] == 20 and sum(r['exact_complete'] for r in selected) == cell['exact_recovery_count'] == expected)
        check(f"Boundary interval {cell['direction']} {cell['method']}", cell['recovery_95_interval'] == clopper_pearson(expected, 20))
        for field, raw in (("exact_goodput_bits_per_symbol", "recovered_goodput"), ("charged_pair_seconds", "charged_pair_seconds"), ("encode_seconds", "encode_seconds"), ("decode_seconds", "decode_seconds")):
            check(f"Unrounded cell mean {cell['direction']} {cell['method']} {field}", close(statistics.mean(r[raw] for r in selected), cell['metrics'][field]['mean']))
    by_work = {r['work_id']: r for r in rows}
    score_rows = []
    for link in links:
        r = by_work[link['work_id']]
        for score in analysis['specification']['scores']:
            score_rows.append(dict(case=r['case'], group=r['pair_id'], work_id=r['work_id'], direction=r['direction'], method=r['method'], score=score,
                stego=r['diagnostics']['whole'][score], ordinary=link['scores'][score], exact_recovery=r['exact_complete'], failed_transmission=not r['exact_complete'],
                trace_id=link['trace_id'], matched_sha256=link['matched_sha256'], matched_artifact=link['matched_artifact']))
    for c in analysis['detectability']:
        selected = [r for r in score_rows if (r['direction'], r['method'], r['score']) == (c['direction'], c['method'], c['score'])]
        check(f"AUC/counts {c['direction']} {c['method']} {c['score']}", len(selected) == c['n_stego'] == 20 and len({r['matched_sha256'] for r in selected}) == c['n_unique_control_artifacts'] == 20 and close(auc([r['stego'] for r in selected], [r['ordinary'] for r in selected]), c['auc']) and sum(r['failed_transmission'] for r in selected) == c['failed_deliveries_included'] and not c['control_duplicates'] and not c['excluded'])
    comparisons = [read(p) for p in sorted((GPU/'comparisons').glob('*.json'))]
    check("11 exact stream/carrier comparisons; 22 exact recoveries", len(comparisons) == 11 and all(c['equivalence']['equivalent'] and all(c['equivalence']['checks'].values()) for c in comparisons) and len(records) == 22 and all(r['evaluation']['exact_recovery'] for r in records))
    for comparison in comparisons:
        pair_records = comparison['records']
        a, b = pair_records['reference'], pair_records['cuda_graph']
        folder_a, folder_b = (GPU/'cases'/r['case']['id'] for r in (a,b))
        check('Actual cross-mode carrier/probability equality '+comparison['comparison']['id'],
              a['distribution_digest'] == b['distribution_digest'] and
              (folder_a/'carrier.png').read_bytes() == (folder_b/'carrier.png').read_bytes() and
              (folder_a/'recovered.txt').read_bytes() == (folder_b/'recovered.txt').read_bytes())
    for t in timings['individual']:
        r = record_by_id[t['comparison'] + '-' + t['mode']]
        folder = GPU/'cases'/r['benchmark_execution_id']
        check('Benchmark saved bytes and timing '+r['benchmark_execution_id'], (folder/'source.txt').read_bytes() == (folder/'recovered.txt').read_bytes() and len((folder/'source.txt').read_bytes()) == t['payload_bytes'] and digest(folder/'carrier.png') == r['evaluation']['carrier_sha256'] and close(t['charged_pair_seconds'], t['charged_encode_seconds']+t['charged_decode_seconds']) and close(t['exact_payload_bytes_per_second'], t['payload_bytes']/t['charged_pair_seconds']))
    fixed = timings['fixed_aggregate']
    for mode in MODE_NAMES:
        selected = [t for t in timings['individual'] if t['method']=='fixed' and t['mode']==mode]
        check('Nine fixed timings and aggregate '+mode, len(selected)==9 and len({t['payload'] for t in selected})==3 and close(statistics.mean(t['charged_pair_seconds'] for t in selected), fixed[mode]['mean_charged_pair_seconds']) and close(sum(t['payload_bytes'] for t in selected)/sum(t['charged_pair_seconds'] for t in selected),fixed[mode]['exact_payload_bytes_per_second']))
    check('40 arithmetic audits and independent checks',len(audits)==40 and all(all(a['checks'].values()) for a in audits))
    check('40 paired V1 outcomes; 20 distinct payloads',len(static)==40 and len({p['pair_id'].split('-')[0] for p in static})==20 and sum(p['sequence']['exact_recovery'] for p in static)==40 and sum(p['static']['exact_recovery'] for p in static)==22)
    for pair in static:
        check('V1 original pairing '+pair['pair_id'],
              pair['sequence']['prepared_packet_sha256'] == pair['static']['prepared_packet_sha256'] == pair['paired_packet_sha256'] and
              pair['sequence']['source_sha256'] == pair['static']['source_sha256'])
    filtering = []
    for method in METHODS:
        selected = [r for r in rows if r['direction']==DIRECTIONS[0] and r['method']==method]
        reports = [read(V2/r['sender_gpu_evidence']) for r in selected]
        filtering.append(dict(method=method,n=len(reports),
            aggregate_filter_fraction=sum(r['filter_seconds'] for r in reports)/sum(r['encode_seconds'] for r in reports),
            fraction_definition='sum candidate-filter seconds / sum encoding-phase seconds; retained V2, not new timing'))
    write_json(OUT/'data/text_filtering_limitation.json',filtering)
    for r in rows:
        # Positive, skipped, zero-bit and completion positions are disjoint;
        # A1 termination is already included among positive positions.
        check('Position accounting '+r['case'], sum(r[k] for k in ('packet_positions','skipped_positions','zero_bit_positions','completion_symbols')) == r['delivered_symbols'])
    write_csv(OUT/'data/v2_plot_observations.csv', [{k:r[k] for k in ('case','pair_id','work_id','direction','method','source_bytes','delivered_symbols','exact_complete','recovered_goodput','encode_seconds','decode_seconds','charged_pair_seconds','packet_bits_recovered','packet_positions','skipped_positions','zero_bit_positions','completion_symbols','failure_stage')} for r in rows])
    write_csv(OUT/'data/detectability_observations.csv',score_rows)
    write_csv(OUT/'data/gpu_timing_observations.csv',timings['individual'])
    write_json(OUT/'data/accepted_analysis_specification.json',analysis['specification'])
    write_json(OUT/'data/accepted_paired_differences.json',analysis['paired_differences'])
    return analysis, manifest, rows, score_rows, timings, records, audits, static, source, profile


def figures(analysis, manifest, rows, scores, timings, audits, static):
    by_case = {r['case']:r for r in rows}
    examples = [next(c for c in manifest['cases'] if c['direction']==d and c['method']=='fixed') for d in DIRECTIONS]
    first_image, first_text = (V2/'cases'/c['id'] for c in examples)
    for folder in (first_image,first_text):
        for name in ('source.png','source.txt','carrier.txt','carrier.png','recovered.png','recovered.txt','recovered.gray'):
            p=folder/name
            if p.exists():SOURCES[str(p.relative_to(ROOT))]=digest(p)
    source_image = np.array(Image.open(first_image/'source.png'))
    recovered_image = np.array(Image.open(first_image/'recovered.png'))
    carrier_image = np.array(Image.open(first_text/'carrier.png'))
    message = (first_text/'source.txt').read_bytes()
    carrier = (first_image/'carrier.txt').read_text(encoding='utf-8')
    # End at the last whole word before character 250, without rewriting any bytes.
    end = carrier.rfind(' ',0,250)
    excerpt = carrier[:end]
    check('First ordered examples and literal pixels/text',source_image.shape==(16,16) and np.array_equal(source_image,recovered_image) and source_image.tobytes()==(first_image/'recovered.gray').read_bytes() and carrier_image.shape==(31,32,3) and message==(first_text/'recovered.txt').read_bytes())
    (OUT/'data/figure1_carrier_excerpt.txt').write_bytes(excerpt.encode('utf-8'))
    write_json(OUT/'data/figure1_examples.json',dict(selection='first manifest-ordered fixed case per direction',cases=examples,excerpt_start_byte=0,excerpt_end_byte=len(excerpt.encode()),excerpt_is_literal_prefix=True,display_wrapping_only=True,source_text_bytes=len(message)))
    fig=plt.figure(figsize=(7.2,5.7))
    fig.text(.035,.956,'A  Image → saved UTF-8 → canonical image',weight='bold',size=11)
    upper=fig.add_gridspec(1,3,left=.04,right=.96,bottom=.52,top=.88,width_ratios=[1,2.4,1],wspace=.25)
    for col,data,label in ((0,source_image,'Source'),(2,recovered_image,'Recovery')):
        ax=fig.add_subplot(upper[0,col]);ax.imshow(data,cmap='gray',vmin=0,vmax=255,interpolation='nearest',aspect='equal');ax.set_axis_off()
        ax.set_title(label,fontsize=10,pad=8)
        ax.text(.5,-.09,'16 × 16 grayscale\n256 canonical bytes',transform=ax.transAxes,ha='center',va='top',fontsize=8)
    ax=fig.add_subplot(upper[0,1]);ax.set_axis_off();ax.set_title('Delivered text — verbatim excerpt',fontsize=10,pad=8)
    wrapped='\n'.join(textwrap.fill(p,width=46,replace_whitespace=False,drop_whitespace=False) for p in excerpt.split('\n'))
    ax.text(0,.98,wrapped,ha='left',va='top',fontsize=9,linespacing=1.38)
    ax.text(0,-.015,f"Excerpt ends here; full file linked in caption.\n{by_case[examples[0]['id']]['delivered_tokens']} tokens; {by_case[examples[0]['id']]['carrier_bytes']:,} UTF-8 bytes.",fontsize=8,va='top')
    fig.text(.035,.425,'B  Literal text → saved PNG → literal text',weight='bold',size=11)
    lower=fig.add_gridspec(1,3,left=.055,right=.96,bottom=.12,top=.35,width_ratios=[1.3,1,1.3],wspace=.35)
    for col,label in ((0,'Source text'),(2,'Recovered text')):
        ax=fig.add_subplot(lower[0,col]);ax.set_axis_off();ax.set_title(label,fontsize=10,pad=7)
        ax.text(0,.84,textwrap.fill(message.decode(),width=24),va='top',fontsize=10,linespacing=1.4)
        ax.text(0,.06,f'{len(message)} literal UTF-8 bytes',va='bottom',fontsize=8)
    ax=fig.add_subplot(lower[0,1]);ax.imshow(carrier_image,interpolation='nearest',aspect='equal');ax.set_axis_off();ax.set_title('Delivered PNG',fontsize=10,pad=8)
    ax.text(.5,-.1,'32 × 31 RGB8\n992 pixels · 2,976 channels',ha='center',va='top',transform=ax.transAxes,fontsize=8)
    fig.text(.5,.025,'Fixed rank · first frozen V2 case in each direction · both sources recovered byte-for-byte',ha='center',fontsize=8.5)
    save_figure(fig,'figure1_transport','Actual bidirectional artifact transport',
        f"First manifest-ordered fixed-rank V2 examples, {examples[0]['id']} and {examples[1]['id']}; selection did not use appearance. Images show unchanged saved pixels enlarged with nearest-neighbor interpolation and correct aspect ratios. A transports the canonical 16 × 16 grayscale array (256 bytes), not arbitrary original image-file bytes. Its literal leading text excerpt has display line wrapping only; the complete carrier is ../v2_review/cases/{examples[0]['id']}/carrier.txt. B transports all {len(message)} literal UTF-8 bytes through a 32 × 31 RGB8 PNG; the native model canvas is 32 × 32, with the shared 1 × 32 RGB row withheld. Fresh receivers used only their own saved carrier, pinned profile/model, shared prompt1 or row1, and retained encryption key. Sources and their byte comparison were evaluator-only. Row1 is 96 shared context bytes, not transmitted payload. The full examples and exact source/recovery paths are linked in the index.",
        'Exact canonical source bytes survived both delivered-file paths on these two predetermined examples.', ['artifacts/v2_review/manifest.json','artifacts/v2_review/results.jsonl']+[str(p.relative_to(ROOT)) for p in (first_image,first_text)])

    fig,axes=plt.subplots(2,2,figsize=(7.2,4.6),gridspec_kw={'width_ratios':[1,1.05]})
    fig.subplots_adjust(left=.15,right=.97,top=.88,bottom=.12,wspace=.42,hspace=.7)
    for row,d in enumerate(DIRECTIONS):
        for col in range(2):
            ax=axes[row,col];ax.set_yticks([2,1,0], [NAMES[m] if col==0 else SHORT[m] for m in METHODS]);ax.set_ylim(-.42,2.6);ax.grid(axis='x',color='#e6e6e6',lw=.6);ax.set_axisbelow(True)
        for j,m in enumerate(METHODS):
            c=next(c for c in analysis['cells'] if c['direction']==d and c['method']==m);y=2-j
            value=100*c['exact_rate'];lo,hi=np.array(c['recovery_95_interval'])*100
            axes[row,0].errorbar(value,y,xerr=[[value-lo],[hi-value]],fmt=MARKERS[m],color=COLORS[m],capsize=3,markersize=5)
            axes[row,0].text(50,y+.15,f"{c['exact_recovery_count']}/{c['n_attempted']} ({value:.0f}%)",ha='center',fontsize=8)
            metric=c['metrics']['exact_goodput_bits_per_symbol'];value=metric['mean'];lo,hi=metric['grouped_95_interval']
            axes[row,1].errorbar(value,y,xerr=[[value-lo],[hi-value]],fmt=MARKERS[m],color=COLORS[m],capsize=3,markersize=5)
            axes[row,1].text(value,y+.2,f'{value:.3f}',ha='center',fontsize=8)
        axes[row,0].set_xlim(-4,104);axes[row,0].set_xticks([0,25,50,75,100]);axes[row,0].set_xlabel('Exact recovery (%)')
        axes[row,1].set_xlim(-.1,3.8) if row==0 else axes[row,1].set_xlim(-.01,.31)
        axes[row,1].set_xlabel('Recovered payload bits / token' if row==0 else 'Recovered payload bits / channel value')
        panel(axes[row,0],('A','C')[row],('Text carrier','PNG carrier')[row]+' · recovery')
        panel(axes[row,1],('B','D')[row],('Text carrier','PNG carrier')[row]+' · useful rate')
    save_figure(fig,'figure2_recovery_rate','Held-out recovery and exact useful rate',
        'All six V2 cells, 20 held-out payload groups per direction. Recovery whiskers are the accepted two-sided 95% Clopper–Pearson intervals (Bernoulli working model); rate whiskers are the accepted 2,000-draw, stratified payload-group percentile intervals. These preserve class/length strata and paired methods. Points show cell means. Goodput is 8 × source bytes divided by every delivered symbol only when the complete carrier authenticates and exactly recovers; otherwise it is zero. All 20 A1 text failures remain in the denominator at zero goodput. Recovered packet prefixes are not useful delivery (Figure S1). Text axes use bits/token; PNG axes use bits/channel value, not bits/pixel (multiply the PNG rates by three). Zero-width rate intervals reflect identical observed rates, not universal reliability. The canonical-image and fixed-slot formats constrain these small-sample results.',
        'Fixed and gated methods recovered 20/20 in both directions; A1 recovered 20/20 through PNGs but 0/20 through text.', ['artifacts/v2_review/analysis.json','artifacts/v2_review/results.jsonl'])

    fig,axes=plt.subplots(2,3,figsize=(7.2,5.9))
    fig.subplots_adjust(left=.085,right=.98,top=.89,bottom=.1,wspace=.36,hspace=.52)
    for r,d in enumerate(DIRECTIONS):
        for col,m in enumerate(METHODS):
            ax=axes[r,col];selected=[s for s in scores if s['direction']==d and s['method']==m and s['score']=='surprisal_bits_mean']
            c=next(c for c in analysis['detectability'] if c['direction']==d and c['method']==m and c['score']=='surprisal_bits_mean')
            offsets=np.linspace(-.14,.14,len(selected))
            for offset,s in zip(offsets,selected):
                ax.plot([offset,1+offset],[s['ordinary'],s['stego']],color='#cccccc',lw=.5,zorder=1)
            ax.scatter(offsets,[s['ordinary'] for s in selected],marker='s',facecolors='white',edgecolors='#666666',s=18,linewidths=.8,zorder=3)
            ax.scatter(1+offsets,[s['stego'] for s in selected],marker='x' if (r==0 and m=='arithmetic') else MARKERS[m],color=COLORS[m],s=22,linewidths=.9,zorder=3)
            maxval=max(max(s['ordinary'],s['stego']) for s in selected)
            ax.set_ylim(0,maxval*1.38);ax.set_xlim(-.35,1.35);ax.set_xticks([0,1],['Ordinary','Stego' if not (r==0 and col==2) else 'Stego (failed)']);ax.grid(axis='y',color='#e8e8e8',lw=.5);ax.set_axisbelow(True)
            unit='token' if r==0 else 'channel value';ax.set_ylabel(f'Mean surprisal (bits/{unit})',fontsize=8)
            lo,hi=c['grouped_95_interval'];ax.text(.5,.96,f"AUC {c['auc']:.4f}\n95% [{lo:.4f}, {hi:.4f}]",transform=ax.transAxes,ha='center',va='top',fontsize=8)
            panel(ax,chr(65+3*r+col),SHORT[m]+' · '+('text' if r==0 else 'PNG'))
    fig.text(.5,.975,'Known-model / known-context observer · frozen higher-is-stego score',ha='center',fontsize=10)
    save_figure(fig,'figure3_detectability','Exploratory whole-carrier surprisal distributions',
        'Each point is a saved V2 carrier or its matched ordinary control (20 of each per panel). Light connectors preserve payload-group pairing; horizontal offsets follow frozen group order only. Square open markers are ordinary controls; filled/colored symbols are stego, with crosses for failed A1 text transmissions. Scores are whole-carrier mean eligible-distribution surprisal under an observer who knows the exact model and shared context, without the encryption key. Each group owns one independent control trace; text methods reuse length-matched prefixes and PNG methods share the full ordinary PNG. Thus 120 method-specific links are only 40 independent traces across the study. No duplicate or unscorable V2 artifacts occurred. Annotations are the accepted higher-is-stego AUCs and 95% grouped intervals, never flipped when below 0.5. All failed delivered A1 text carriers remain scorable. Panel y-scales differ. Complete empirical separation in the small fixed/gated text sample, including its collapsed bootstrap interval, does not establish perfect population detection. AUC near 0.5 does not establish security against this or other observers.',
        'Rank-coded text separates strongly from ordinary text under this tested observer; PNG and failed A1 text show different, uncertain score distributions.', ['artifacts/v2_review/analysis.json','artifacts/v2_review/control_links.json','artifacts/v2_review/results.jsonl'])

    fixed=[t for t in timings['individual'] if t['method']=='fixed'];payloads=sorted({t['payload'] for t in fixed},key=lambda x:int(x[1:]));aggregate=timings['fixed_aggregate']
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.9));fig.subplots_adjust(left=.09,right=.98,top=.86,bottom=.105,wspace=.3,hspace=.68)
    labels=[p+f"\n{next(t['payload_bytes'] for t in fixed if t['payload']==p)} B" for p in payloads]
    for col,field in enumerate(('charged_encode_seconds','charged_decode_seconds')):
        ax=axes[0,col]
        for i,p in enumerate(payloads):
            for rep,offset in enumerate((-.065,0,.065)):
                a,b=[next(t for t in fixed if t['payload']==p and t['repetition']==rep and t['mode']==mode) for mode in MODE_NAMES]
                ax.plot([i-.19+offset,i+.19+offset],[a[field],b[field]],lw=.7,color='#bbbbbb')
                for t,x in ((a,i-.19+offset),(b,i+.19+offset)):
                    ax.scatter(x,t[field],marker=('o','s','^')[rep],color=MODE_COLORS[t['mode']],s=27,zorder=3)
        ax.set_xticks(range(3),labels);ax.set_ylim(0,103);ax.set_ylabel('Charged fresh-process latency (s)');ax.grid(axis='y',color='#e6e6e6',lw=.6)
        panel(ax,('A','B')[col],('Encode','Decode')[col]+' · three repetitions each')
    ax=axes[1,0]
    for i,p in enumerate(payloads):
        for rep,offset in enumerate((-.065,0,.065)):
            for mode,dx in (('reference',-.19),('cuda_graph',.19)):
                t=next(t for t in fixed if t['payload']==p and t['repetition']==rep and t['mode']==mode)
                ax.scatter(i+dx+offset,t['exact_payload_bytes_per_second'],color=MODE_COLORS[mode],marker=('o','s','^')[rep],s=27)
    ax.set_xticks(range(3),labels);ax.set_ylim(0,4.15);ax.set_ylabel('Recovered source bytes / pair-second');ax.grid(axis='y',color='#e6e6e6',lw=.6)
    panel(ax,'C','Useful throughput · encode + decode')
    ax=axes[1,1];memory_fields=('peak_cuda_allocated_mib','peak_cuda_reserved_mib','sampled_process_peak_mib')
    for j,mode in enumerate(MODE_NAMES):
        values=[max(t[f] for t in fixed if t['mode']==mode) for f in memory_fields]
        bars=ax.bar(np.arange(3)+(j-.5)*.34,values,width=.31,color=MODE_COLORS[mode],label=MODE_NAMES[mode])
        for bar,value in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,value+25,f'{value:.0f}',ha='center',fontsize=7)
    ax.set_xticks(range(3),['PyTorch\nallocated','PyTorch\nreserved','Sampled\nprocess']);ax.set_ylim(0,1370);ax.set_ylabel('Peak GPU memory (MiB)');ax.grid(axis='y',color='#e6e6e6',lw=.6);ax.set_axisbelow(True);panel(ax,'D','GPU memory · distinct measures')
    handles=[Line2D([],[],marker='o',ls='',color=MODE_COLORS[m],label=MODE_NAMES[m]) for m in MODE_NAMES]
    handles += [Line2D([],[],marker=s,ls='',color='#333333',label=f'Repetition {i+1}') for i,s in enumerate(('o','s','^'))]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.947),ncol=5,frameon=False,columnspacing=1.2)
    fig.text(.5,.986,f"CUDA graph replay: {aggregate['pair_speedup']:.2f}× faster · {aggregate['reference']['exact_payload_bytes_per_second']:.3f} → {aggregate['cuda_graph']['exact_payload_bytes_per_second']:.3f} recovered B/s",ha='center',va='top',fontsize=11,weight='bold')
    save_figure(fig,'figure4_gpu_performance','Behavior-preserving CUDA graph improvement',
        f"Development engineering benchmark, not V2: T1/T4/T5 contain 32/96/128 source bytes, all under row1. Fixed rank has three alternating-order matched timing repetitions per payload (nine comparisons). Colors identify execution mode and shapes repetitions; connectors in A/B join matched packets. Headline {aggregate['pair_speedup']:.3f}× speedup is the ratio of mean charged reference and graph encode-plus-decode time on the pinned RTX 5000 Ada / PyTorch 2.5.1+cu124 configuration. Charged fresh processes include imports, model hashing/loading, graph setup, CPU bookkeeping, serialization and teardown. Throughput is exactly recovered source bytes divided by both charged processes; the headline pools bytes and time across all nine repetitions, while C shows individual ratios. These are three development payloads, not nine independent research observations. All 11 benchmark comparisons (including single-payload gated/A1 in Table 4) had identical exact ID/order/probability stream hashes, delivered PNG bytes and recovered source bytes; all 22 recoveries passed. D shows maxima across fixed jobs separately for allocated tensors, reserved allocator storage and sampled process memory; they overlap and must not be added. Process memory is sampled, not a guaranteed true peak. No broad statistical speed claim or equivalence on other stacks is established; reference execution remains available.",
        'CUDA graph replay reduces matched end-to-end latency by about 5.13× without changing checked probability streams or carrier bytes, at greater reserved/process memory.', ['artifacts/gpu_performance_review/timings.json','artifacts/gpu_performance_review/gpu_jobs.json','artifacts/gpu_performance_review/comparisons/'])

    trajectory=[];endpoints=[]
    for audit in audits:
        d=by_case[audit['case']]['direction']
        for point in audit['checkpoints_128_positions']:
            trajectory.append(dict(case=audit['case'],direction=d,position=point['position'],useful_packet_prefix_bits=min(point['recovered_bits'],audit['target_bits']),emitted_including_suffix_bits=point['recovered_bits'],eligible_surprisal_bits=point['cumulative_eligible_surprisal_bits'],eligible_entropy_bits=point['cumulative_eligible_entropy_bits'],is_endpoint=point['position']==audit['positions']))
        endpoints.append({k:audit[k] for k in ('case','positions','bits_recovered','target_bits','eligible_surprisal_bits','quantized_minus_eligible_surprisal_bits','unchanged_interval_zero_bit_positions','longest_unchanged_interval_run','zero_extension_reached','termination_reached')})
    write_csv(OUT/'data/arithmetic_observed_checkpoints.csv',trajectory);write_csv(OUT/'data/arithmetic_endpoints.csv',endpoints)
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.9));fig.subplots_adjust(left=.09,right=.98,top=.78,bottom=.19,wspace=.24)
    for j,d in enumerate(DIRECTIONS):
        ax=axes[j]
        for audit in [a for a in audits if by_case[a['case']]['direction']==d]:
            points=[p for p in trajectory if p['case']==audit['case']];x=[p['position'] for p in points];y=[p['useful_packet_prefix_bits'] for p in points]
            ax.plot(x,y,color=COLORS['arithmetic'] if j==0 else COLORS['fixed'],lw=.6,alpha=.48,marker='o',ms=2)
        ax.axhline(2336,color='#111111',ls='--',lw=1);ax.text(.97,.985,'Packet target: 2,336 bits',transform=ax.transAxes,ha='right',va='top',fontsize=8)
        ax.set_ylim(0,2520);ax.set_xlim(0,2100 if j==0 else 3000);ax.set_yticks([0,584,1168,1752,2336]);ax.set_xlabel('Consumed text tokens' if j==0 else 'Consumed channel values');ax.grid(color='#eeeeee',lw=.5);ax.set_axisbelow(True)
        ax.set_ylabel('Recovered packet-prefix bits' if j==0 else '')
        cap=2048 if j==0 else 2976;ax.axvline(cap,ls=':',color='#555555',lw=1)
        ax.text(.98,.05,f'Carrier cap: {cap:,}',transform=ax.transAxes,ha='right',fontsize=8)
        panel(ax,('A','B')[j],('Text: 0/20 packets complete','PNG: 20/20 packets complete')[j])
    fig.text(.5,.945,'All V2 arithmetic cases · observed checkpoints every 128 positions + endpoint',ha='center',fontsize=9)
    fig.text(.5,.055,'Dots are recorded observations; connecting lines are visual guides, not intermediate measurements.',ha='center',fontsize=8)
    text_audits = [a for a in audits if by_case[a['case']]['direction']==DIRECTIONS[0]]
    prefix_min, prefix_max = min(a['bits_recovered'] for a in text_audits), max(a['bits_recovered'] for a in text_audits)
    save_figure(fig,'figureS1_arithmetic_capacity','Arithmetic information accumulation and carrier capacity',
        f'All 20 V2 A1 text and 20 A1 PNG cases, using retained audit observations every 128 consumed symbols and the final recorded endpoint. Dots are measured checkpoints; connecting segments are guides, not measured intermediate values. Axes have different carrier units and caps. Text stops at 2,048 tokens with {prefix_min:,}–{prefix_max:,} of the required 2,336 bits and never reaches zero-extension/termination; packet prefixes are not authenticated source delivery. PNGs reach the packet target before completing the remaining full 2,976-channel carrier. Curves stop at the packet endpoint; they do not extrapolate into ordinary completion. Useful packet-prefix bits are capped at 2,336; emitted zero suffix bits beyond that are kept separately in the supporting endpoint CSV and Table S1. Eligible surprisal and entropy checkpoint values are also in the data CSV, not invented from line segments. Isolated unchanged-interval steps in HI5/HI16 (failed text) and HT19 (successful PNG) were transient, longest run one; they do not establish sustained stagnation as the text-failure cause. Low accumulated information under the fixed cap remains the accepted explanation. A1 retains its separate, previously documented finite-precision stagnation limitation.',
        'The directional A1 completion difference is visible in actual prefix progress and unchanged carrier budgets, without treating partial information as successful delivery.', ['artifacts/v2_review/arithmetic_audits.json','artifacts/v2_review/results.jsonl'])

    pairs=sorted(static,key=lambda p:(p['pair_id'].split('-')[1],int(p['pair_id'].split('-')[0][1:])))
    static_rows=[]
    fig,axes=plt.subplots(2,1,figsize=(7.2,3.9));fig.subplots_adjust(left=.155,right=.98,top=.81,bottom=.17,hspace=.85)
    for j,context in enumerate(('prompt1','prompt2')):
        selected=[p for p in pairs if p['pair_id'].endswith(context)];ax=axes[j]
        for arm,y in (('sequence',1),('static',0)):
            for i,p in enumerate(selected):
                success=p[arm]['exact_recovery'];ax.scatter(i+1,y,marker='s' if success else 'x',color=COLORS['fixed'] if success else COLORS['arithmetic'],s=75 if success else 65,linewidths=1.8)
                static_rows.append(dict(payload=p['pair_id'].split('-')[0],context=context,arm=arm,case=p[arm]['case'],exact_recovery=success,authenticated=p[arm]['authenticated'],failure_stage=p[arm]['failure_stage'],outcome_class=p[arm]['outcome_class'],carrier=p[arm]['carrier']))
        successes=sum(p['static']['exact_recovery'] for p in selected)
        panel(ax,('A','B')[j],f"{context}: {'forest' if j==0 else 'soup'} · sequence 20/20, static {successes}/20")
        ax.set_yticks([1,0],['Sequence','Static']);ax.set_ylim(-.55,1.55);ax.set_xlim(.4,20.6);ax.set_xticks(range(1,21),[f'I{i}' for i in range(1,21)],fontsize=7);ax.tick_params(length=0);ax.spines['left'].set_visible(False);ax.spines['bottom'].set_visible(False)
        for x in range(1,21):ax.axvline(x,color='#eeeeee',lw=.7,zorder=0)
    fig.legend(handles=[Line2D([],[],marker='s',ls='',color=COLORS['fixed'],label='Exact saved-file recovery'),Line2D([],[],marker='x',ls='',color=COLORS['arithmetic'],label='Retained tokenization-drift failure')],loc='upper center',bbox_to_anchor=(.5,.99),ncol=2,frameon=False)
    fig.text(.5,.06,'Development only · 20 distinct image payloads × 2 frozen prompts · paired immutable packets',ha='center',fontsize=9)
    write_csv(OUT/'data/static_sequence_pairs.csv',static_rows)
    save_figure(fig,'figureS2_text_consistency','Saved-text tokenization consistency: paired development evidence',
        'V1 development comparison, separate from V2. Each column preserves one of 20 distinct canonical image payloads under both frozen prompts; 40 context-specific pairs are not 40 independent payloads. Within each pair, fixed-rank sequence and static arms transport the same immutable packet. Sequence eligibility checks the complete generated carrier prefix; static eligibility checks singleton tokens only, with the other filtering/coding rules held fixed. Static carriers were saved literally even when retokenization drifted; no repair, saved IDs or sender state reached receivers. Sequence recovered 20/20 under each prompt; static recovered 8/20 (forest) and 14/20 (soup), with 18 retained drift/replay failures. This motivates the tested main method’s saved-artifact consistency requirement, not a theorem that singleton filtering must always fail. The historical unavailable static matched-control prefix remains unavailable and is not scored or regenerated here.',
        'Complete-prefix filtering passed all 40 development artifact recoveries; singleton-only filtering did not reliably preserve the saved-text decoding path.', ['artifacts/v1_qualification_review/static_pairs.json'])


def tables(analysis, rows, timings, source, profile):
    development=[p for p in source['payloads'] if p['split']=='development'];heldout=[p for p in source['payloads'] if p['split']=='heldout']
    counts=lambda items,d:sum(p['direction']==d for p in items)
    text_lengths=[p['bytes'] for p in heldout if p['direction']==DIRECTIONS[1]]
    specification=[
        ('Canonical payload','16 × 16 grayscale (L8), row-major; 256 raw pixel bytes',f'Literal strict UTF-8; allowed 32–128 B (held out: {min(text_lengths)}–{max(text_lengths)} B)'),
        ('Delivered carrier','UTF-8 file; at most 2,048 carrier tokens','Lossless PNG, 32 × 31 RGB8; 992 pixels / 2,976 channel values'),
        ('Model / checkpoint',f"Llama 3 8B Instruct LLM; QuantFactory Q4_K_M GGUF; {profile['text']['model_sha256'][:12]}",f"CIFAR-10 pretrained PixelCNN++ autoregressive image model; {profile['image']['nr_resnet']} residual blocks, {profile['image']['nr_filters']} filters, {profile['image']['nr_logistic_mix']} logistic mixtures; {profile['image']['model_sha256'][:12]}"),
        ('Inference profile','llama-cpp-python 0.3.23; full 33/33 eligible layers on CUDA; float64 probability bookkeeping','PyTorch 2.5.1+cu124; float32 CUDA forward; float64 discrete RGB conditional/mixture posterior probabilities'),
        ('Shared context','Frozen prompt1: temperate-forest field journal; prompt tokenization separate from carrier','Frozen row1: 1 × 32 RGB8 (96 B), prepended privately to a 32 × 32 model canvas'),
        ('Packet and framing','292 B = 12 B nonce + encrypted (8 B header + 256 B slot) + 16 B tag; AES-256-GCM; zero slot padding','Same 292 B / 2,336-bit packet; one sealed packet shared across methods in each payload/context group'),
        ('Coding','Fixed radix 16; entropy-gated radix 16; finite-precision arithmetic A1 (32 bits)','Same three methods; RGB channel alphabet; raster order, then R/G/B'),
        ('Eligibility / gate',f'Top 256 before complete-prefix filtering; strict H > {profile["coder"]["thresholds"]["text"]["value"]:.6f} bits',f'Observable values 0–255; strict H > {profile["coder"]["thresholds"]["image"]["value"]:.6f} bits'),
        ('Stopping / completion','Known 2,336-bit target; exactly 32 ordinary tail tokens after packet completion, within cap','Known packet target; ordinary completion through all 2,976 delivered channels'),
        ('Exact recovery','Fresh receiver reconstructs tokens from saved UTF-8; authenticated parsing plus independent equality of all canonical pixels','Fresh receiver reconstructs symbols from saved PNG pixels; authenticated parsing plus independent literal source-byte equality'),
        ('Distinct payloads',f'Development {counts(development,DIRECTIONS[0])} × 2 prompts; held out {counts(heldout,DIRECTIONS[0])} × prompt1',f'Development {counts(development,DIRECTIONS[1])} × 2 rows; held out {counts(heldout,DIRECTIONS[1])} × row1'),
        ('V2 allocation','60 stego units; 20 independent control traces with matched prefixes shared across methods','60 stego units; 20 independent full-PNG controls shared across methods'),
    ]
    make_table('table1_specification','Experimental specification',['Property','Image → text carrier','Text → PNG carrier'],specification,[dict(property=k,image_to_text=a,text_to_image=b) for k,a,b in specification],
        'Frozen scientific profiles, not the later optional GPU graph execution mode. Development uses 20 distinct payloads per direction; fixed-arm cross-context tests do not imply that every development payload had every method. V2 has 20 groups per direction, three paired methods and one context. Checkpoint hashes are abbreviated to 12 hexadecimal characters; gate values are rounded here only. Exact float64 thresholds, checkpoint hashes, contexts, runtime identities and source provenance are in data/protocol_identities.json. The 36 framing bytes and slot padding are different overheads. Text and image neural models are different autoregressive backends. Exactness concerns canonical source bytes, not pre-resize images or arbitrary source containers.', [.18,.41,.41],['plan/implementation_plan.md','data/qualification_v1/manifest.json','artifacts/v2_review/manifest.json','configs/v1_fixed.json'])
    numeric=[];display=[]
    for c in analysis['cells']:
        m=c['metrics'];rate=m['exact_goodput_bits_per_symbol'];d=c['direction'];method=c['method'];lo,hi=c['recovery_95_interval']
        row=dict(direction=d,method=method,attempted=c['n_attempted'],exact=c['exact_recovery_count'],recovery_rate=c['exact_rate'],recovery_ci_low=lo,recovery_ci_high=hi,goodput_mean=rate['mean'],goodput_ci_low=rate['grouped_95_interval'][0],goodput_ci_high=rate['grouped_95_interval'][1],goodput_unit=c['rate_unit'],encode_phase_seconds=m['encode_seconds']['mean'],decode_phase_seconds=m['decode_seconds']['mean'],charged_pair_seconds=m['charged_pair_seconds']['mean'],charged_encode_seconds=m['charged_encode_seconds']['mean'],charged_decode_seconds=m['charged_decode_seconds']['mean'],failure_category='capacity: 2,048-token cap before packet completion' if c['failures'] else 'none')
        numeric.append(row)
        display.append([('UTF-8' if d==DIRECTIONS[0] else 'PNG')+' / '+SHORT[method],f"{row['exact']}/{row['attempted']}\n[{100*lo:.2f}, {100*hi:.2f}]%",f"{rate['mean']:.4f}\n[{rate['grouped_95_interval'][0]:.4f}, {rate['grouped_95_interval'][1]:.4f}]",f"{row['encode_phase_seconds']:.2f}",f"{row['decode_phase_seconds']:.2f}",f"{row['charged_pair_seconds']:.2f}",'Token-cap capacity' if c['failures'] else 'None'])
    make_table('table2_v2_outcomes','V2 recovery, useful rate and original runtime',['Carrier / method','Exact / attempted; 95% interval','Exact goodput; 95% interval','Encode phase (s)','Decode phase (s)','Charged pair (s)','Failure'],display,numeric,
        'Original held-out V2 timings, including unsuccessful attempts; later graph timings are not substituted. Goodput units are bits/token for UTF-8 and bits/channel value for PNG; PNG rates multiply by three to obtain bits/pixel. Recovery uses accepted 95% Clopper–Pearson bounds; goodput uses accepted 2,000-draw stratified payload-group percentile intervals, n = 20 groups per direction. Incomplete/unauthenticated outcomes have zero exact goodput. Encode/decode phases exclude cold loading and other occupied time; the charged pair includes both full fresh processes, loading and teardown. These nested measurements are not additive charges. All 20 failures are A1 text capacity outcomes, with no authenticated payload.', [.13,.18,.21,.105,.105,.12,.15],['artifacts/v2_review/analysis.json','artifacts/v2_review/compute_projection.json','artifacts/v2_review/results.jsonl'])
    numeric=[];display=[]
    for d in DIRECTIONS:
        for method in METHODS:
            for score in ('surprisal_bits_mean','log_rank_mean'):
                c=next(c for c in analysis['detectability'] if (c['direction'],c['method'],c['score'])==(d,method,score));lo,hi=c['grouped_95_interval']
                numeric.append(dict(direction=d,method=method,score=score,auc=c['auc'],auc_ci_low=lo,auc_ci_high=hi,scorable_stego=c['n_stego'],unique_matched_controls=c['n_unique_control_artifacts'],independent_trace_ids=c['n_independent_trace_ids'],failed_transmissions_included=c['failed_deliveries_included'],unscorable=len(c['excluded']),duplicates=len(c['control_duplicates'])))
                display.append([('UTF-8' if d==DIRECTIONS[0] else 'PNG')+' / '+SHORT[method],'Mean surprisal' if score.startswith('surprisal') else 'Mean log2 rank',f"{c['auc']:.4f} [{lo:.4f}, {hi:.4f}]",str(c['n_stego']),str(c['n_unique_control_artifacts']),str(c['failed_deliveries_included'])])
    make_table('table3_detectability','Exploratory known-model/context detectability',['Carrier / method','Frozen score','AUC [grouped 95% interval]','Scorable stego','Unique matched controls','Failed stego included'],display,numeric,
        'Both frozen whole-carrier scores use higher-is-stego direction, including AUCs below 0.5. Intervals reuse the accepted 2,000-draw payload-group bootstrap with class/length strata and shared controls. There are 40 independent ordinary traces overall, not 120 per-method control replicates or 240 per-score observations. Each cell has 20 unique matched artifacts; no V2 duplicates or unscorable carriers were dropped. All 20 failed A1 text carriers are included. Small empirical perfect separation and a [1,1] bootstrap interval do not prove perfect population detection; near-chance scores do not prove security.', [.16,.20,.25,.12,.145,.125],['artifacts/v2_review/analysis.json','artifacts/v2_review/control_links.json'])
    numeric=[];display=[]
    for s in sorted(timings['summaries'],key=lambda r:(int(r['payload'][1:]),METHODS.index(r['method']))):
        a,b=[s['modes'][mode] for mode in MODE_NAMES]
        record=dict(payload=s['payload'],method=s['method'],payload_bytes=s['payload_bytes'],timing_repetitions=s['timing_repetitions'],pair_speedup=s['pair_speedup'],exact_equivalence=True)
        for mode in MODE_NAMES:
            part=s['modes'][mode]
            for field in ('charged_encode_seconds','charged_decode_seconds','charged_pair_seconds','exact_payload_bytes_per_second','cold_load_pair_seconds','execution_setup_pair_seconds','cuda_event_pair_seconds','peak_cuda_allocated_mib','peak_cuda_reserved_mib'):
                record[mode+'_'+field]=part[field]
            selected=[t for t in timings['individual'] if t['payload']==s['payload'] and t['method']==s['method'] and t['mode']==mode]
            record[mode+'_sampled_process_peak_mib']=max(t['sampled_process_peak_mib'] for t in selected)
        numeric.append(record)
        display.append([s['payload']+' / '+SHORT[s['method']],f"{s['payload_bytes']} / {s['timing_repetitions']}",f"{a['charged_encode_seconds']:.2f} / {a['charged_decode_seconds']:.2f}",f"{b['charged_encode_seconds']:.2f} / {b['charged_decode_seconds']:.2f}",f"{s['pair_speedup']:.2f}×",f"{a['exact_payload_bytes_per_second']:.3f} → {b['exact_payload_bytes_per_second']:.3f}",'Exact'])
    peaks = {mode:{field:max(t[field] for t in timings['individual'] if t['mode']==mode)
             for field in ('peak_cuda_allocated_mib','peak_cuda_reserved_mib','sampled_process_peak_mib')}
             for mode in MODE_NAMES}
    memory_caption = (f"Peak PyTorch allocated memory: {peaks['reference']['peak_cuda_allocated_mib']:.3f} → {peaks['cuda_graph']['peak_cuda_allocated_mib']:.3f} MiB; "
        f"reserved: {peaks['reference']['peak_cuda_reserved_mib']:.0f} → {peaks['cuda_graph']['peak_cuda_reserved_mib']:.0f} MiB; "
        f"sampled process maximum: {peaks['reference']['sampled_process_peak_mib']:,.0f} → {peaks['cuda_graph']['sampled_process_peak_mib']:,.0f} MiB.")
    make_table('table4_gpu_benchmark','Matched reference versus CUDA graph benchmark',['Payload / method','Bytes / repeats','Reference encode / decode (s)','Graph encode / decode (s)','Pair speedup','Recovered B/s reference → graph','Equivalence'],display,numeric,
        'Three development payloads, row1; timing repetitions are not new independent research observations. Fixed has three matched repetitions per payload; gated/A1 each have one T1 comparison. Latencies are means of full charged fresh processes, including loading, graph setup and teardown. Speedup is the ratio of matched mean charged pair times; per-row throughput is the accepted mean of individual exact-source-bytes/pair-second ratios (the Figure 4 pooled headline instead divides summed bytes by summed times). All 11 comparisons/22 recoveries match exact ID/order/probability stream hashes, PNG file bytes and recovered source bytes. ' + memory_caption + ' These are distinct, overlapping measures, not additive; per-combination measurements and nested CUDA-event/loading times are in the full-precision CSV. Tested RTX 5000 Ada, PyTorch 2.5.1+cu124 and unchanged checkpoint/float32 precision; no cross-hardware performance claim.', [.14,.10,.18,.18,.10,.18,.12],['artifacts/gpu_performance_review/timings.json','artifacts/gpu_performance_review/gpu_jobs.json','artifacts/gpu_performance_review/comparisons/'])
    numeric=[];display=[]
    for c in analysis['cells']:
        fields=('framing_bytes','slot_padding_bytes','packet_positions','skipped_positions','zero_bit_positions','termination_positions','termination_suffix_bits','lookahead_zero_bits','completion_symbols','packet_transport_bits_per_symbol','serialized_expansion')
        r=dict(direction=c['direction'],method=c['method'],**{f:c['metrics'][f]['mean'] for f in fields})
        selected=[x for x in rows if (x['direction'],x['method'])==(c['direction'],c['method'])]
        r['mean_delivered_symbols']=statistics.mean(x['delivered_symbols'] for x in selected)
        r['mean_complete_packet_bits_per_delivered_symbol']=statistics.mean(2336/x['delivered_symbols'] for x in selected) if all(x['packet_complete'] for x in selected) else None
        numeric.append(r)
        display.append([('UTF-8' if c['direction']==DIRECTIONS[0] else 'PNG')+' / '+SHORT[c['method']],f"{r['slot_padding_bytes']:.1f}",f"{r['packet_positions']:.2f}",f"{r['skipped_positions']:.2f}",f"{r['zero_bit_positions']:.2f}",f"{r['completion_symbols']:.2f}",'—' if r['packet_transport_bits_per_symbol'] is None else f"{r['packet_transport_bits_per_symbol']:.3f}",f"{r['termination_suffix_bits']:.1f}"])
    a1_image = next(c for c in analysis['cells'] if c['direction']==DIRECTIONS[1] and c['method']=='arithmetic')
    suffix_mean = a1_image['metrics']['termination_suffix_bits']['mean']
    lookahead_mean = a1_image['metrics']['lookahead_zero_bits']['mean']
    make_table('tableS1_overhead','Framing, padding and carrier-position overhead',['Carrier / method','Slot pad (B)','Packet-positive positions','Skipped positions','Zero-bit positions','Completion positions','Packet bits / span symbol','Suffix bits'],display,numeric,
        f'Descriptive cell means over 20 held-out attempts. Every packet is 292 B: 36 B framing/encryption plus the 256 B payload slot. Rank alignment adds zero padding bits. The four position columns partition delivered symbols: packet-positive + skipped + zero-bit + completion. A1’s one successful termination position is already among packet-positive positions, never another position to add. Packet-span transport is 2,336 / packet stopping position (including skips/zero-bit steps), undefined for unfinished A1 text. Whole-carrier packet rates and file expansion are in the CSV. A1 PNG suffix bits (mean {suffix_mean:.1f}) are discarded zero-extension emissions, not useful packet bits; lookahead zeros (mean {lookahead_mean:.1f}, CSV) overlap that diagnostic and must not be summed with it. A1 text reaches neither suffix processing nor completion.', [.14,.10,.16,.12,.12,.13,.14,.09],['artifacts/v2_review/analysis.json','artifacts/v2_review/results.jsonl'])
    write_json(OUT/'data/protocol_identities.json',dict(source_manifest_sha256=digest(ROOT/'data/qualification_v1/manifest.json'),profile=profile,contexts=source['contexts'],source_provenance=source['sources'],specification_source='plan/implementation_plan.md'))


def documentation(analysis, timings, preservation, usage, source_revision):
    reference=timings['fixed_aggregate']['reference'];graph=timings['fixed_aggregate']['cuda_graph']
    caption_lines=['# Publication captions\n']
    for f in FIGURES:caption_lines += [f"## {f['id']}: {f['title']}\n",f['caption']+'\n']
    for t in TABLES:caption_lines += [f"## {t['id']}: {t['title']}\n",t['caption']+'\n']
    (OUT/'captions.md').write_text('\n'.join(caption_lines),encoding='utf-8')
    (OUT/'captions.tex').write_text('\n\n'.join('% '+r['id']+'\n'+r'\caption{'+tex_escape(r['caption'])+'}\n'+r'\label{fig:'+r['id']+'}' for r in FIGURES)+'\n',encoding='utf-8')
    claims=[
        ('Bidirectional exact artifact recovery','Supported for the tested canonical payloads, pinned models and unchanged artifact symbols: fixed/gated 20/20 per direction; A1 PNG 20/20.','Figures 1–2; Table 2; V2 source/carrier/recovered artifacts','Not arbitrary original-image container recovery, general reliability, lossy robustness or security.'),
        ('Complete-prefix consistency in the main text path','Supported design requirement for this evaluated implementation: sequence 40/40; singleton static 22/40 in paired V1 development.','Figure S2; V1 static_pairs.json','Not a universal impossibility theorem for other serializers; 20 payloads, not 40 independent payloads.'),
        ('Arithmetic text capacity limitation','Observed 0/20 V2 packets by the fixed cap; low-information trajectories are the accepted diagnosis.','Figure S1; Table 2; V2 arithmetic audits','Partial packet information is not payload delivery; no universal termination guarantee for A1; no full text success established.'),
        ('Observed detectability differences','Supported only for the frozen model/context-aware mean-surprisal and log-rank observer.','Figure 3; Table 3; accepted grouped intervals','Neither perfect population detection nor imperceptibility, unknown-detector resistance or secrecy is established.'),
        ('Behavior-preserving GPU speedup',f"Matched fixed-rank charged latency improves {timings['fixed_aggregate']['pair_speedup']:.3f}×; 11 exact stream/carrier comparisons and 22 exact recoveries.",'Figure 4; Table 4; exact stream comparison records','Three development payloads and pinned hardware/runtime; timing repeats are not extra independent study observations.'),
    ]
    write_csv(OUT/'data/claim_to_evidence.csv',[dict(claim=c,supported=s,evidence=e,unestablished=u) for c,s,e,u in claims])
    lines=['# Publication results: figures and tables\n',
        'CPU-only presentation of accepted evidence. **Four main figures, four main tables, two supplementary figures and one supplementary overhead table.** No new model inference, study-source selection, scoring pass or statistical fit. V1 development, V2 held-out outcomes and development GPU timing repetitions remain separate.\n',
        f"Built from checkout `{source_revision}` (reviewed benchmark `5e08a8b`; no subsequent commit at start). New reporting code identities are separate from historical execution identities. [Captions](captions.md) · [LaTeX figure captions](captions.tex) · [Provenance and exact source hashes](data/provenance.json) · [Numerical checks/preservation](data/verification.json) · [Saved-evidence verification](data/public_evidence_verification.json).\n",
        '## Main figures\n']
    for f in FIGURES:
        if f['id'].startswith('figureS'):continue
        stem=f['id'];lines += [f"### {f['title']}\n",f"[PDF](figures/{stem}.pdf) · [SVG](figures/{stem}.svg) · [450-dpi PNG](figures/{stem}.png)\n",f['finding']+'\n',f['caption']+'\n']
    lines += ['## Supplementary figures\n']
    for f in FIGURES:
        if not f['id'].startswith('figureS'):continue
        stem=f['id'];lines += [f"### {f['title']}\n",f"[PDF](figures/{stem}.pdf) · [SVG](figures/{stem}.svg) · [450-dpi PNG](figures/{stem}.png)\n",f['caption']+'\n']
    lines += ['## Tables\n','Each CSV retains unrounded numerical fields. Each LaTeX table is independently includable with `booktabs` and `array`; compiled PDFs/previews show the actual typeset layout at 7.1-inch table width, without shrinking text to fit.\n','| Item | Quick review | Manuscript | Numerical source |\n|---|---|---|---|']
    for t in TABLES:
        s=t['id'];lines.append(f"| {t['title']} | [Markdown](tables/{s}.md), [preview](tables/{s}.png) | [LaTeX](tables/{s}.tex), [PDF](tables/{s}.pdf) | [CSV](tables/{s}.csv) |")
    lines += ['\n## Complete saved examples behind Figure 1\n',
        '| Direction | Source | Complete delivered carrier | Recovery |\n|---|---|---|---|',
        '| HI1 / prompt1 / fixed | [canonical PNG](../v2_review/cases/HI1-prompt1-fixed/source.png) | [complete UTF-8](../v2_review/cases/HI1-prompt1-fixed/carrier.txt) | [PNG](../v2_review/cases/HI1-prompt1-fixed/recovered.png), [raw pixels](../v2_review/cases/HI1-prompt1-fixed/recovered.gray) |',
        '| HT1 / row1 / fixed | [literal UTF-8](../v2_review/cases/HT1-row1-fixed/source.txt) | [complete PNG](../v2_review/cases/HT1-row1-fixed/carrier.png) | [literal UTF-8](../v2_review/cases/HT1-row1-fixed/recovered.txt) |\n',
        'The excerpt byte range and exact prefix are retained in [figure1_examples.json](data/figure1_examples.json) and [figure1_carrier_excerpt.txt](data/figure1_carrier_excerpt.txt). Display wrapping is not serialization. Public review folders contain source truth and are not receiver inboxes.\n',
        '## Numerical definitions and limitations\n',
        'All recovery/rate/AUC intervals are read unchanged from accepted V2 `analysis.json`. Recovery uses boundary-aware Clopper–Pearson; rate/AUC/paired continuous intervals use 2,000 PCG64 draws (seed 2026090901 plus direction offset), resampling whole payload groups within class/length strata. Methods and shared controls remain together. Twenty groups per direction are not a representative population sample. No additional significance test, sign selection or threshold fit is performed.\n',
        'V2 has 120 outcomes and 40 independent ordinary controls, with 20 scorable stego and 20 unique matched controls per score cell. Failed A1 text carriers remain included. No V2 exact-control duplicates occur. The V1 unavailable historical static prefix remains unavailable; Figure S2 uses recovery only. [Full-precision plotted score pairs](data/detectability_observations.csv) and [accepted paired differences](data/accepted_paired_differences.json) retain dependencies.\n',
        f"GPU headline uses nine fixed comparisons per mode: {reference['mean_charged_pair_seconds']:.6f} → {graph['mean_charged_pair_seconds']:.6f} mean charged pair seconds; summed recovered bytes / summed pair times = {reference['exact_payload_bytes_per_second']:.6f} → {graph['exact_payload_bytes_per_second']:.6f} B/s. Table 4 uses the accepted mean individual throughput per payload/method; these estimands differ slightly before rounding. Full [timing rows](data/gpu_timing_observations.csv) preserve cold load, graph setup and nested CUDA events. CUDA events overlap phase/process time and are not extra charges or profiler-summed active kernel durations. Sampled process memory is not allocator reservation; none of the memory measures is additive.\n",
        'The existing benchmark used repeated PID-matched `nvidia-smi pmon -c 1 -s um` observations (roughly 0.19 s polling). Driver windows, correlated samples and observation gaps prevent claims of sustained utilization. No fresh GPU queries or runs are needed for these exports. Text filtering remains a separate bottleneck; [fractions recomputed from retained V2 reports](data/text_filtering_limitation.json) are supporting timing evidence, not new benchmarks. Faster image inference does not correct arithmetic text information deficits.\n',
        'New endpoint/memory displays are descriptive views of retained records, not new inference or statistical analyses. Arithmetic trajectories use only actual 128-position checkpoints and endpoints; packet bits are capped before suffix diagnostics. All six requested figures were supported by retained evidence.\n',
        '## Claim-to-evidence limits\n','| Claim | Supported evidence | Not established |\n|---|---|---|']
    for c,s,e,u in claims:lines.append(f'| {c} | {s} {e}. | {u} |')
    lines += ['\n## Reproduction and provenance\n',
        'From the repository root, using Python with NumPy, Pillow and Matplotlib plus `pdflatex` (`booktabs`, `array`, `lmodern`, `caption`) and `pdftoppm`:\n',
        '```sh\npython -B scripts/build_publication_results.py\n```\n',
        'The existing compatible interpreter on this host is `/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python`. No dependency installation is part of this task. The entry point reads public saved evidence, performs focused numerical/identity assertions and the three public evidence verifiers, writes only this new output directory, compiles table previews, and checks that accepted artifacts and ledgers are unchanged. Private keys, prepared packets, weights, raw audit traces and environments are never inputs. If local ledgers exist, their balances/hashes are checked read-only; a public checkout instead reports the accepted historical accounting without claiming a local ledger audit.\n',
        'Saved-evidence verifiers (CPU-only, no authentication replay):\n',
        '```sh\npython -B scripts/collect_v2_review.py --verify-public artifacts/v2_review\npython -B scripts/collect_gpu_performance.py --verify-public\npython -B scripts/finalize_v1_qualification.py --verify-public artifacts/v1_qualification_review\n```\n',
        f"Preservation: {preservation['protected_file_count']:,} existing files verified byte-identical. No new GPU time charged: 0 s. Cumulative recorded use remains {sum(usage.values()):,.6f} s; historical stage balances are in [verification.json](data/verification.json). No accepted V2/benchmark analysis or execution identity was overwritten.\n",
        'Evidence roots: [V2](../v2_review/README.md), [GPU benchmark](../gpu_performance_review/README.md), [V1 qualification](../v1_qualification_review/README.md). Model/code/corpus attribution remains in [THIRD_PARTY.md](../../THIRD_PARTY.md) and the frozen source provenance. No generated substitute image, new dataset or model result is used. Supporting verification notes and visual review are in [notes/publication_results.md](../../notes/publication_results.md).\n']
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    write_json(OUT/'data/item_sources.json',dict(figures=FIGURES,tables=TABLES))


def main():
    for sub in ('figures','tables','data'):(OUT/sub).mkdir(parents=True,exist_ok=True)
    initial=protected_snapshot()
    accounting=read(GPU/'accounting.json')
    stages=tuple(accounting['usage_seconds'])
    ledgers_present=all((ROOT/'.runtime'/('gpu_budget.jsonl' if s=='v0' else s+'/gpu_budget.jsonl')).exists() for s in stages)
    usage={s:budget_state(s)[0] for s in stages} if ledgers_present else accounting['usage_seconds']
    check('Current/accepted accounting agreement',all(close(usage[s],accounting['usage_seconds'][s]) for s in stages))
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    style()
    analysis,manifest,rows,scores,timings,records,audits,static,source,profile=load_evidence()
    figures(analysis,manifest,rows,scores,timings,audits,static)
    tables(analysis,rows,timings,source,profile)
    public_checks = {}
    commands = {
        'V2':['scripts/collect_v2_review.py','--verify-public','artifacts/v2_review'],
        'GPU':['scripts/collect_gpu_performance.py','--verify-public'],
        'V1':['scripts/finalize_v1_qualification.py','--verify-public','artifacts/v1_qualification_review'],
    }
    for label, arguments in commands.items():
        process = subprocess.run([sys.executable,'-B']+arguments,cwd=ROOT,capture_output=True,text=True,check=True)
        public_checks[label] = dict(command='python -B '+' '.join(arguments),exit_code=process.returncode,result=json.loads(process.stdout))
        check('Accepted public evidence verifier '+label,process.returncode==0)
    write_json(OUT/'data/public_evidence_verification.json',public_checks)
    final=protected_snapshot()
    check('All accepted evidence/configuration/ledger bytes unchanged',initial==final)
    final_usage={s:budget_state(s)[0] for s in stages} if ledgers_present else accounting['usage_seconds']
    check('Zero new GPU charges',usage==final_usage)
    preservation=dict(protected_file_count=len(initial),before_sha256=aggregate_hash(initial),after_sha256=aggregate_hash(final),all_unchanged=True)
    documentation(analysis,timings,preservation,usage,revision)
    identities = {}
    for name, path in (('V2',V2/'execution_freeze.json'),('GPU',GPU/'execution_identity.json'),('V1',V1/'protocol_compute_freeze.json')):
        frozen = read(path)
        identities[name] = {k:v for k,v in frozen.items() if k in ('source_revision','execution_source_hash','manifest_sha256','execution_package_hash','historical_revision','source_context_manifest_sha256','allocation_sha256')}
    write_json(OUT/'data/historical_execution_identities.json',identities)
    provenance=dict(reporting_revision=revision,reporting_script='scripts/build_publication_results.py',reporting_script_sha256=digest(__file__),sources=SOURCES,
        versions=dict(python=sys.version.split()[0],numpy=np.__version__,matplotlib=matplotlib.__version__),statistical_content_sha256=analysis['statistical_content_sha256'],intervals_reused_without_refitting=True,
        evidence_sets=dict(V1='development qualification',V2='held-out prospective',GPU='development engineering timing repetitions'),private_payload_or_key_material_read=False,new_model_inference=False)
    write_json(OUT/'data/provenance.json',provenance)
    check('Bounded output count',len(FIGURES)==6 and len(TABLES)==5)
    write_json(OUT/'data/verification.json',dict(checks_passed=len(CHECKS),checks=CHECKS,preservation=preservation,local_ledgers_checked=ledgers_present,usage_seconds=usage,new_gpu_seconds=0,cumulative_seconds=sum(usage.values()),whole_ceiling_seconds=144000,whole_remaining_seconds=144000-sum(usage.values()),figures=len(FIGURES),tables=len(TABLES),latex_overfull_boxes=0,visual_review='See notes/publication_results.md; rendered outputs are inspected after generation.'))
    outputs={str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and p.name!='output_hashes.json'}
    write_json(OUT/'data/output_hashes.json',outputs)
    print(json.dumps(dict(index=str((OUT/'README.md').relative_to(ROOT)),figures=len(FIGURES),tables=len(TABLES),numerical_checks=len(CHECKS),preservation=preservation,new_gpu_seconds=0)))


if __name__=='__main__':
    main()
