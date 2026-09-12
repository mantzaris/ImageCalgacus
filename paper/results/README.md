# Manuscript results integration index

The [ICAART manuscript index](../icaart2027/README.md) is the consolidated starting point. The current [main PDF](../icaart2027/ICAART2027_submission.pdf) has 12 pages and the [companion](../icaart2027/ICAART2027_supplement.pdf) has 11. The bounded photograph extension is separate from accepted generated-carrier and repeated-score evidence.

| Location | Item | Evidence |
|---|---|---|
| Main page 4 | Figure 1A–B, actual historical bidirectional artifacts | Unchanged retained transport figure, `fig:examples` |
| Main page 6 | Figure 2, complete text-to-photograph example | [New review packet](../../artifacts/cover_rank_v1_review/README.md), `fig:cover-example` |
| Main Results | Figure 3, recovery/goodput, Table 2 | Accepted six prospective cells and original runtimes |
| Main page 11 | Figure 4, context-AUC comparison | [Detection component](png_context_detection.md#fig-png-context-auc), `fig:png-context-auc` |
| Main page 11 | Table 3, paired photograph outcomes | Model ranks and simple parity, twenty held-out groups |
| Main Section 5.5 | GPU speedup and timing boundary | Detailed plot now companion Figure S6; original values unchanged |
| Companion | Figure S1 process diagram, S2 detection, S3 capacity, S4 sequence/static | Accepted development/prospective evidence kept distinct |
| Companion | Figure S5 score shifts, Tables S4–S5 | [Retained context/addendum integration](png_context_detection.md) |
| Companion page 11 | Figure S7, covers/carriers/differences ×32 | First three frozen photograph test identifiers |
| Original publication package | Figures 1–4/S1–S2 and Tables 1–4/S1 | [Accepted exports](../../artifacts/publication_results/README.md), unchanged |

The earlier [PNG context Methods/Results/limitations](png_context_detection.md) remain incorporated, not replaced. Their original scores and analyses are unchanged. Local `examples/` links are author materials, not a claim of an approved reviewer-access route.

```sh
python -B paper/icaart2027/build.py
python -B paper/icaart2027/package_source.py
```

The old score-addendum generator uses public saved scores but would restore provisional integration numbering. Do not use it to reset this index or build the manuscript.

The extension's figure/table generator is `python -B scripts/analyze_cover_rank_v1.py`, using saved evidence only. Both PDFs and the source archive have been compiled and visually checked. Separate supplementary-upload permission, AI-disclosure placement and photograph republication rights remain explicit author-review issues. Manuscript preparation uses zero GPU time; the new experiment's 429.149258-second charge is recorded separately.
