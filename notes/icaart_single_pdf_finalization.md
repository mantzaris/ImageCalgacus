# ICAART single-PDF editorial finalization

Starting revision **79fd48c8b531f1eaeea28f2fc45457beac51b3ef**, branch `main`, with a clean working tree and matching remote main. This operation is manuscript preparation from retained evidence. It adds no carriers, datasets, model inference or GPU charge.

## Completed changes

The submission artifact is `paper/icaart2027/ICAART2027_submission.pdf` alone. Main-paper prose no longer depends on a companion, review packet, local example path or unavailable attachment. It now includes the exact header fields and ordering, padding/AAD contract, A1 framing and separate stagnation limitation, keyed photograph placement, development allocation, model/checkpoint and GPU settings, secondary detection results, score shifts, packet/completion overhead and benchmark memory boundary.

Introduction and related work present the progression from canonical image transport through generated text, to literal text through generated PNGs, to bounded photograph changes. Repeated attribution/qualification and implementation-history detail were condensed. Material limitations remain. The photograph result explicitly preserves parity's equal recovery, better mean fidelity and substantially lower runtime. Generated-PNG AUCs are not assigned to photographs.

Manuscript-only figure variants were regenerated through `paper/icaart2027/build_submission_figures.py`. Figure 1 retains `HI1-prompt1-fixed` and `HT1-row1-fixed`, including the verbatim 249-byte excerpt. Its complete carrier is identified as 616 tokens and 2,827 UTF-8 bytes, without promising an external file. Figure 2 retains `heldout-2018-model_rank` and shows the original cover, actual carrier and `32 * abs(stego - cover)` per RGB channel. Cover/stego have equal display scale. The entire 63-byte source/recovered text remains visible. No pixels or carrier files were changed. PDF/SVG/PNG outputs and their source hashes are recorded separately from accepted exports.

## Final package and verification

- Main: **12 pages**, **41,519 extracted non-whitespace characters**, **44,154 conservative estimate**, **173 abstract words**. The conservative allowance counts 1,635 figure-text characters twice and adds 1,000 for extraction uncertainty, leaving 5,846 below the official maximum.
- Original examples: **Figure 1A–B, page 3**. Photograph example: **Figure 2A–C, page 6**. Recovery Figure 3 is on page 10, context Figure 4 and photograph Table 3 on page 11.
- Companion: 11 pages, rebuilt, with extracted text identical to the starting version. It is optional supporting material, not required review input.
- Both PDFs compile. The source ZIP compiles in an isolated directory and reproduces both local extracted PDF texts. Its allowlist excludes keys, sealed packets, model weights, private contexts, environments, ledgers and caches.
- All twelve final main pages and the two changed figures were visually inspected. Figures, captions, table widths, equations, references and page breaks are readable. Logs contain no overfull boxes, undefined citations or unresolved references. Fonts are embedded and author metadata is empty.
- The current official template archive was downloaded again on 12 September 2026. All six retained template/example files match; no layout settings were altered.
- Two figure-generation runs reproduced all six output files byte-for-byte. Public qualification, V2, GPU benchmark and context verifiers pass. The separate photograph verifier recomputes saved fidelity/equality/coverage and confirms all 52 original outcomes. Accepted counts, AUCs, intervals and timings are unchanged.
- All tracked scientific evidence/configuration/application paths are unchanged from the starting revision. All six private execution ledgers remain hash-identical. Historical cumulative use remains **89,404.217194 seconds**, with **0 new GPU seconds**.

Executed commands:

```sh
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/build_submission_figures.py
python -B paper/icaart2027/build.py
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify.py
../llm-rankcloak/.venv/bin/python -B scripts/analyze_cover_rank_v1.py --verify-only
python -B paper/icaart2027/package_source.py
pdftoppm -r 120 -png paper/icaart2027/ICAART2027_submission.pdf paper/icaart2027/build/single_pdf_render/main
```

Detailed records are `paper/icaart2027/verification.json`, `source_archive_verification.json`, `visual_inspection.md`, `data/figure_variants.json`, `data/single_pdf_start.json` and `data/single_pdf_policy.json`. Build/render intermediates remain ignored. Historical execution identities are not rewritten as this editorial source revision.

## Remaining author decisions

The technical package is complete, but unconditional submission readiness is not claimed. `paper/icaart2027/AUTHOR_REVIEW.md` records precise questions about (1) republication of BSDS photographs and derivatives, separate from research-download terms and citation; (2) anonymous AI-disclosure placement; (3) eligibility and handling of the already-public manuscript history; and (4) authorship, overlap and source-term declarations. The official posting restriction covers the period beginning at submission; the pages do not expressly resolve pre-existing public versions. Metadata cleanup does not erase public history.

Git delivery is limited to the authorized manuscript, figure-source, verification and documentation changes on `origin/main`, without force-pushing or rewriting history. The companion need not be uploaded. No venue submission, organizer contact, visibility change or experiment was performed.
