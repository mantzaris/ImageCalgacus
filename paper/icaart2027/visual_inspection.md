# Revised manuscript visual inspection

Completed 11 September 2026 after the editorial revision from `9f91143`. Every final main-paper page and all eight companion pages were rendered at 130 dpi on A4 and inspected. Figure 1 was inspected at its final full manuscript width, not only as a standalone enlarged asset. This is an assistant inspection record, not an independent scientific review.

Final PDF SHA-256 identities:

- Main, 12 pages: `75b17949332a9062b9661a0477faeb04da6cfa221eb8cc86380386baaef8b912`.
- Companion, 8 pages: `c63445b96f1f9ff39e2827aacf3f7b5b53e6d5791159f338e911f54f7e372691`.

## Main paper

| Page | Content inspected | Findings |
|---|---|---|
| 1 | Title, unchanged 176-word abstract, shortened Introduction, start of Related Work | Anonymous title block, readable body, complete contribution and headline results. Shorter drafting footnote fits on one line and retains its citation. |
| 2 | Related Work and Method 3.1 | Attribution retained, both Figure 1 directions explicitly introduced, canonical payload and header readable. |
| 3 | **Figure 1A and 1B**, packet and authentication contract | Both actual examples are clear. Canonical source/recovered pixels use unchanged nearest-neighbor views. Excerpt is verbatim and explicitly incomplete. Complete 63-byte text is visible in source and recovery. Caption explains dimensions, receiver inputs, withheld row and the original local full-file note without implying reviewer access. |
| 4 | Probability rules, complete-prefix equation, RGB mixture posteriors, rank and gate rules | Equations, minus signs, subscripts and strict entropy comparison readable. No clipping. |
| 5 | A1 framing, termination, recovery conditions, source allocation | Essential protocol and finite-capacity limitations remain in the main paper. |
| 6 | Table 1, GPU configuration, timing, grouping and observer definition | Two model types distinguished, 33/33 offload and CUDA configuration retained, table and units fit. |
| 7 | Observer extension, matched benchmark design, recovery/rate results | Repeated PNG rescoring distinct from transmissions; timing repetitions and grouping clearly specified. |
| 8 | Table 2, arithmetic failures, correct-context and mismatch findings | All six cells, including 0/20 arithmetic text, remain. Rates, original times and uncertainty agree with retained evidence. |
| 9 | Figure 2, GPU results, start of Discussion | Recovery/rate axes and boundary-aware intervals readable. Charged timing and throughput denominators explicit. |
| 10 | Figure 3, Discussion, start of Conclusion | Fixed paired AUC decrease and uncertain other changes preserved. Text-filtering bottleneck, scope and security limitations remain. |
| 11 | Figure 4, conclusion, AI disclosure, start of references | Three-payload matched benchmark, 5.13-fold headline, memory distinctions and actual timing repetitions readable. Full AI disclosure unchanged. |
| 12 | Remaining references | All 15 records complete, URLs/identifiers wrap without clipping. Ordinary final-page reference whitespace retained rather than altering the template. |

## Companion

| Page | Content inspected | Findings |
|---|---|---|
| 1 | Revised abstract and Sections S1–S3 | Points to main Figure 1; no duplicate example or relative example-path access claim. |
| 2 | **Figure S1 process diagram**, Table S1 and A1 equations | Standard float placement resolved the initial overflow. Diagram inputs/arrows and expanded rates/times readable. |
| 3 | Figure S2 and development serialization text | Six detection panels retain all observations and failed text carriers; labels and caption readable. |
| 4 | Table S2 and Figure S3 | Both score tables and arithmetic capacity trajectories readable. Observed checkpoints and target remain distinct. |
| 5 | Table S3 and Figure S4 | Overhead accounting and paired 20-payload/two-context outcomes fit, with no altered measurements. |
| 6 | Descriptive shifts, benchmark details and reproducibility | Hashes and checkpoint name wrap intact; timing boundaries and private-data exclusions preserved. |
| 7 | Table S4, Figure S5 and Table S5 | Context intervals and all 80 score shifts readable; shared controls and post hoc status clear. |
| 8 | Table S6, disclosure ending and references | Five benchmark combinations and complete references fit. Normal final-page whitespace remains. |

## Corrections and verification

The examples moved into the main paper without changing their PDF or underlying files. The process diagram moved to the companion. Repetitive attribution and observer/performance qualifications were consolidated, while every material limitation remains. A repeated drafting-footnote pointer was shortened, keeping the section-level tool citation and full disclosure.

The initial companion build packed the relocated diagram and a large plot too tightly. Restoring standard `[t]` placement for those two floats and shortening the diagram caption removed the overflow. No margins, font sizes, line spacing, negative spacing or official template files were changed.

Both final logs have no overfull boxes, unresolved references or citations. Main figures remain 1–4 and tables 1–2. Companion figures remain S1–S5 and tables S1–S6. The main worked examples are Figure 1A–B on page 3; there is no duplicate in the companion.

The main has 39,713 extracted non-whitespace characters and a conservative 42,596 estimate, including a second count of all four figure texts plus a 1,000-character extraction allowance. See `verification.json`. The source ZIP was compiled in an isolated temporary directory, reproducing both local PDF texts exactly. Empty author metadata and unchanged accepted evidence/ledgers were checked.

Reproduce the page renders:

```sh
pdftoppm -r 130 -png paper/icaart2027/ICAART2027_submission.pdf paper/icaart2027/inspection/main
pdftoppm -r 130 -png paper/icaart2027/ICAART2027_supplement.pdf paper/icaart2027/inspection/supplement
```

Raster files are ignored inspection outputs. The PDF hashes above identify the inspected documents. No model inference or GPU time was used.
