# Focused verification and visual inspection

This checkpoint is a retained-evidence publication addition, not another experiment or portability campaign. The starting checkout was `c2effbb3c2f908851d39e399ef83b69ade87c287`, with no working changes, no existing addendum script/directory, no manuscript source and no applicable AGENTS.md files.

## Numerical and integration checks

The builder included all 80 unique manifest-identified PNG observations: 20 ordinary controls and 20 per coding method, retaining the original 20 payload groups/control associations and complete 2,976-channel scores. Controls are counted once. Exported CSVs were read back and checked for identity, exact saved-float subtraction, counts, means and medians. The paired fixed/control gap was computed using each fixed artifact's declared control, and checked against the algebraic category-mean difference.

One additional focused check recomputed the within-artifact differences, category means and medians using 40-digit Decimal arithmetic on the saved decimal scores. These agreed with the exported floating-point summaries within 1e-12 reporting precision; no model probability rule was altered. The four expected three-decimal summaries agree with the retained data without hardcoded result values in the builder.

Figure SVG annotations were checked against the unrounded summary means. Manuscript mean-change and gap values were checked against the exports, and local links and explicit figure/table anchors were resolved. The accepted AUC estimates and intervals are read from analysis.json and referenced unchanged; no new bootstrap, confidence interval, hypothesis test, classifier or threshold is introduced.

## Public-only reproduction

Executed successfully:

```sh
/home/meow/Documents/repos/llm-rankcloak/.venv/bin/python -B scripts/build_png_context_addendum.py
```

The same command also succeeded once in a temporary minimal public export containing only the script and its recorded public input files. The temporary export deliberately had **no imagecalgacus package, data/context directory, models, runs, keys or .runtime ledgers**. Both CSVs and PDF/SVG/PNG figure files were byte-identical to the main build. This specifically verifies the requested public-score-only reproduction path, not general CPU portability.

## Actual PDF inspection

The new score_shifts.pdf was rasterized with `pdftoppm -r 144 -png -singlefile` and viewed at its intended 7.2 × 3.8-inch proportions. The PDF reports 518.4 × 273.6 points; the PNG export is 3,240 × 1,710 pixels (450 dpi). All individual observations are plotted with deterministic group-order offsets, and separate open mean diamonds do not hide observations. The units, four mean annotations, category labels, zero line and legend are readable and unclipped.

The reused context_auc.pdf was also rasterized and visually inspected, without altering it. Its labels and intervals remain readable. The summary Markdown and generated manuscript-ready Methods, Results, limitations and captions were inspected for numerical consistency and scope.

No manuscript existed, so there were no manuscript pages to compile. The requested fallback files, paper/results/README.md and paper/results/png_context_detection.md, integrate the existing main AUC figure, new supplementary shift figure and full accepted supplementary comparison table. Figure 5 / Figure S3 / Table S2 are provisional numbering; stable labels are provided. Final typesetting awaits a manuscript, but no requested integration component is missing.

## Preservation and zero GPU usage

All **3,661 protected accepted public files** were byte-identical before and after generation, including the original publication package, PNG context-detection review packet and accepted notes. No application, model, protocol, source-data or test files were modified.

All five local GPU ledgers were separately read and hash-checked before and after reporting; the public builder itself never reads them:

| Ledger | Unchanged SHA-256 |
|---|---|
| V0 | `0309090a7ba12305c66cbb574c9f3f0617ad0b6a11496055dc67f0e7218f61d3` |
| V1 | `02e470af365426920fa68a31a64c139f78855af9958f53e8cdeb21941a12dce4` |
| V2 | `ad98825222680989b0d9d4cdc417327be4d137ebc61c0e8e8910ceb80c52b29f` |
| GPU performance | `f83b12e8c76f25150636ca4a08fad6c56c13cdc7f246c29629b1b3502bd7de8e` |
| PNG context detection | `2bc7982dac6063c6930cf6adfcbdf286936d0028e0fc0452c9bf7c22e7cb6d51` |

New GPU usage: **0 seconds**. Cumulative recorded usage remains 88,975.0679364727 seconds. No carrier generation, model inference, new context, training, additional experiment, dependency installation, commit, push, submission or publication occurred.
