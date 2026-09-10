# Descriptive PNG score-shift addendum

One supplementary figure and a descriptive table from **all 80 retained PNG observations**, with 20 artifacts in each category and 20 shared payload groups. No new inference, observations, contexts, tests of hypotheses or confidence intervals.

![Descriptive within-artifact score changes](score_shifts.png)

[PDF](score_shifts.pdf) · [SVG](score_shifts.svg) · [450-dpi PNG](score_shifts.png) · [Caption](caption.md)

| Category | Artifacts | Row1 mean | Row2 mean | Mean change | Median change |
|---|---:|---:|---:|---:|---:|
| Ordinary controls | 20 | 3.684 | 4.294 | +0.610 | +0.621 |
| Fixed rank | 20 | 4.191 | 4.525 | +0.334 | +0.286 |
| Entropy gated | 20 | 4.074 | 4.588 | +0.513 | +0.555 |
| Arithmetic A1 | 20 | 3.770 | 4.399 | +0.629 | +0.636 |

Units: bits per delivered RGB channel value. The paired mean fixed-rank-minus-control gap narrows from **0.507624** to **0.231119** (change **-0.276505**). Higher control score increases are consistent with this narrowing; descriptive mean shifts do not independently explain why AUC changed, which depends on full score rankings.

## Data, provenance and integration

- [All 80 observations, original group/control links and paired gaps](score_shift_observations.csv)
- [Summary CSV](score_shift_summary.csv), [Markdown](score_shift_summary.md)
- [Input/script/output identities and focused checks](provenance.json)
- [Manuscript results index](../../paper/results/README.md), [Methods/Results/limitations component](../../paper/results/png_context_detection.md)
- Main Figure 5 reuses the [accepted context-AUC figure](../png_context_detection_review/context_auc.pdf) unchanged. Supplementary Figure S3 is this score-shift figure; supplementary Table S2 reuses the [full accepted primary/secondary AUC table](../png_context_detection_review/comparison.md). Numbering is provisional because no manuscript existed.

The fixed-rank primary AUC reduction remains the accepted finding, with its mismatched interval only narrowly excluding chance. Its secondary rank-score interval includes chance. Uncertain gated/A1 changes do not establish a difference in methods' sensitivities. Row1 was generated-image conditioning; row2 was the previously frozen random-RGB row. This single mismatch does not isolate correctness from every difference in row statistics, establish a causal mechanism, or demonstrate secrecy or broad resistance to detection.

## Public reproduction

```sh
python -B scripts/build_png_context_addendum.py
```

Run from the public repository using Python with NumPy and Matplotlib (the existing host interpreter is `/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python`). The builder reads public scores, metadata and accepted publication assets only. It does not import model/application code or require model weights, raw contexts, private keys/packets or execution ledgers. It validates all 80 IDs, 20-per-category coverage, source/control pairing, complete score units, arithmetic and exported CSVs, and checks accepted public evidence remains byte-identical.

The PDF is 7.2 × 3.8 inches; SVG text remains editable and PNG is 450 dpi. Horizontal offsets are deterministic functions of frozen group order, not scores. Every category has 20 individual points plus one distinguishable mean diamond. Means/medians are calculated before display rounding. Existing AUCs and intervals are read unchanged for integration, never recomputed by this builder.

New GPU usage: **0 seconds**. No manuscript source existed, so Markdown integration components were created rather than a full paper. Figure PDF rendering/visual inspection and link/number checks are recorded in [inspection.md](inspection.md).
