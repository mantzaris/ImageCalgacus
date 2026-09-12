#!/usr/bin/env python3
"""Typeset companion-only tables; never overwrite the canonical main.tex."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
METHOD = {"fixed": "Fixed", "gated": "Gated", "arithmetic": "A1"}


def rows(name):
    with (HERE / "data" / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def table(name, spec, headings, data):
    lines = [r"\begin{tabular}{@{}" + spec + r"@{}}", r"\toprule",
             " & ".join(headings) + r" \\", r"\midrule"]
    lines += [" & ".join(row) + r" \\" for row in data]
    lines += [r"\bottomrule", r"\end{tabular}"]
    (HERE / "tables" / (name + ".tex")).write_text("\n".join(lines) + "\n")


def main():
    context_rows = rows("context_comparison.csv")
    def interval(r, prefix):
        return f'[{float(r[prefix+"_ci_low"]):.4f}, {float(r[prefix+"_ci_high"]):.4f}]'
    table("context_comparison", "llccc", ["Method", "Score", r"Row1 AUC [95\% CI]", r"Row2 AUC [95\% CI]", r"Change [95\% CI]"],
          [[METHOD[r["method"]], "Surprisal" if r["score"] == "surprisal_bits_mean" else r"$\log_2$ rank",
            f'{float(r["correct_auc"]):.4f} ' + interval(r,"correct"),
            f'{float(r["mismatch_auc"]):.4f} ' + interval(r,"mismatch"),
            f'{float(r["difference"]):+.4f} ' + interval(r,"difference")] for r in context_rows])
    table("score_shifts", "lrrrrr", ["Category", "Count", "Row1 mean", "Row2 mean", "Mean change", "Median change"],
          [[r["category_label"], r["n_artifacts"], f'{float(r["mean_row1"]):.6f}',
            f'{float(r["mean_row2"]):.6f}', f'{float(r["mean_score_change"]):+.6f}',
            f'{float(r["median_score_change"]):+.6f}'] for r in rows("score_shift_summary.csv")])

    # Reuse original table bodies, removing their outer floats and stylistic bold.
    # Layout-only copies. Accepted publication exports remain untouched.
    for name in ("table3_detectability", "table4_gpu_benchmark", "tableS1_overhead", "table2_v2_outcomes"):
        text = (HERE / "tables" / ("retained_" + name + ".tex")).read_text()
        start = text.index(r"\begin{tabular}")
        end = text.index(r"\end{tabular}") + len(r"\end{tabular}")
        body = text[start:end]
        import re
        body = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", body)
        # Column definitions total one pubtablewidth. The original body explicitly
        # expects 3pt tab separation, so retain that local table setting.
        columns = {"table3_detectability": 6, "table4_gpu_benchmark": 7,
                   "tableS1_overhead": 10, "table2_v2_outcomes": 7}[name]
        prefix = (r"\setlength{\tabcolsep}{3pt}" + "\n" +
                  r"\setlength{\pubtablewidth}{\dimexpr\linewidth-" + str(6 * (columns - 1)) + r"pt\relax}" + "\n")
        (HERE / "tables" / ("supp_" + name + ".tex")).write_text(prefix + body + "\n")


if __name__ == "__main__":
    main()
