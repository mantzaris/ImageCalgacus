# Manuscript results integration index

The complete first ICAART 2027 Regular Paper draft now incorporates these results components. Start with the [manuscript index](../icaart2027/README.md), [main PDF](../icaart2027/ICAART2027_submission.pdf), [companion PDF](../icaart2027/ICAART2027_supplement.pdf), or [author decisions](../icaart2027/AUTHOR_REVIEW.md).

The earlier manuscript-ready material below is preserved and incorporated, not replaced by an outline. Figure/table numbering now follows the compiled draft and stable LaTeX labels.

| Placement | Final item | Source / integration |
|---|---|---|
| Main paper | Figures 1–4, Tables 1–2 | [Complete manuscript and evidence mapping](../icaart2027/README.md) |
| Main Results | Figure 3, PNG context-AUC comparison | [Detection component](png_context_detection.md#fig-png-context-auc); `fig:png-context-auc` |
| Companion | Figure S5, descriptive within-PNG score shifts | [Figure and caption](png_context_detection.md#fig-png-score-shifts); `fig:png-score-shifts` |
| Companion | Table S4, full primary/secondary AUC comparison | [Table and caption](png_context_detection.md#tab-png-context-scores); `tab:png-context-scores` |
| Companion | Table S5, descriptive category means | [Accepted unrounded summary](../../artifacts/png_context_detection_addendum/score_shift_summary.csv) |
| Original publication exports | Original Figures 1–4, S1–S2 and Tables 1–4, S1 | [Accepted publication index](../../artifacts/publication_results/README.md), unchanged |

[Methods, Results and limitations](png_context_detection.md) · [Descriptive addition and provenance](../../artifacts/png_context_detection_addendum/README.md).

Build the complete manuscript locally:

```sh
python -B paper/icaart2027/build.py
```

The retained-score generator remains `python -B scripts/build_png_context_addendum.py`. It uses public scores and plotting dependencies, not models or private contexts/keys. Its older generated integration text predates the full manuscript, so rerunning it would restore provisional numbering in this directory. Do not use it to build the paper. No accepted numerical export was changed for manuscript preparation.

Both manuscript PDFs have been compiled and visually inspected. The source ZIP has been compiled independently. Separate ICAART Regular Paper supplementary-upload permission is unconfirmed, so the companion is not represented as accepted supplementary submission material. New GPU use for manuscript preparation is zero.
