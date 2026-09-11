# Final manuscript visual inspection

Completed 10 September 2026. Every final main page and every companion page was inspected from its 130-dpi A4 raster render, with vector PDFs retained for manuscript use. This is a human-readable inspection record by the manuscript-preparation assistant, not an independent scientific review.

Final PDF SHA-256 identities:

- Main, 12 pages: `63debfdfea6d71e68b4b58f562b216e35ba1289c7dedd9b18151a570549219a4`.
- Companion, 8 pages: `95fcf5616f19fc482fd965129f880e5bedb1785167411db0891b9ea0db6b1676`.

## Main paper

| Page | Content inspected | Final outcome |
|---|---|---|
| 1 | Two-line title, anonymous author area, 176-word abstract, introduction | Legible. Official title-block spacing retained. No author identity. |
| 2 | Related work, citation forms and prior-method distinctions | No duplicated author-text citation phrasing or overflow. |
| 3 | Packet/header, authentication, text reconstruction equation and model interface | Packet-size equation fits. Literal identifier and UTF-8 conventions readable. |
| 4 | Vector method diagram, RGB posterior equations, entropy gate and A1 partition | Labels/arrows readable. Entropy minus sign and conditional notation checked against TeX and implementation. |
| 5 | A1 finite-message rule, stopping/completion, source allocation | All mathematical symbols and prose within columns. |
| 6 | Table 1, actual hardware/runtime, score definitions and group intervals | Table and two score equations fit; units and LLM/image-model distinction clear. |
| 7 | Prospective outcomes, rate/overhead interpretation and text capacity | Footnote no longer splits into the opposite column. All six outcome claims remain consistent. |
| 8 | Table 2, capacity interpretation, original and mismatched AUCs | Original prospective times and failure cell readable; no clipped numeric intervals. |
| 9 | Figure 2, GPU narrative, beginning of discussion | Separate rate units and boundary-aware recovery whiskers readable. |
| 10 | Figure 3 and discussion | Paired AUC difference, fixed orientation and shared sample clear. |
| 11 | Figure 4, conclusion, AI disclosure | All nine fixed timing pairs and distinct memory measures readable. No overlap or duplicated timing charges. |
| 12 | Disclosure continuation and all 15 references | References use template 9-point size. No unresolved citations, missing glyphs or clipped URLs. Natural final-reference-page whitespace retained. |

## Companion

| Page | Content inspected | Final outcome |
|---|---|---|
| 1 | Title, companion-status abstract, examples/table interpretation | Anonymous; no representation that supplementary upload is authorized. |
| 2 | Figure S1 and A1 equations | Real pixels, correct aspect ratios, verbatim excerpt and explicit complete-carrier path readable. |
| 3 | Figure S2, correct-context score distributions | All six panels, individual scores, AUCs and intervals readable. Failed text carriers labeled. |
| 4 | Tables S1–S2 and development evidence | Both complete numerical tables fit at 9-point size; failures/control counts retained. |
| 5 | Figure S3 and Table S3 | Observed capacity checkpoints and target distinct; overhead categories readable without adding overlapping termination diagnostics. |
| 6 | Figure S4 and performance details | Paired 20-payload/two-context outcomes and development-only status clear. |
| 7 | Table S4, Figure S5 and Table S5 | Both score comparisons and all 80 descriptive shifts readable; shared-control and post hoc qualifications preserved. |
| 8 | Table S6, compact reproducibility, AI disclosure and references | Five GPU combinations fit; checkpoint hashes wrap intact; bibliography completes on the page with no orphan lines. |

## Corrections and final checks

Initial drafts were shortened by removing repetition, not by changing template margins, fonts or line spacing. Packet and score equations were broken at natural mathematical boundaries. A long checkpoint filename received permissible break points. References were set to the official 9-point convention. An unnecessarily long drafting footnote was shortened. Supplementary floats use standard `[!t]` placement, and repeated reproducibility prose was condensed so the tables no longer form a widely spaced terminal float page and the bibliography no longer leaves two orphan lines. No numerical content was changed for layout.

Both final logs have no overfull boxes, undefined references or unresolved citations. Empty author metadata was checked with `pdfinfo`. The source ZIP was compiled in an isolated temporary directory; both extracted PDF texts match the local build exactly. See `source_archive_verification.json` and `verification.json` for machine-readable checks. Raster inspection files are ignored build outputs, not accepted experimental artifacts or source-ZIP contents.

Render again, if needed:

```sh
pdftoppm -r 130 -png paper/icaart2027/ICAART2027_submission.pdf paper/icaart2027/inspection/main
pdftoppm -r 130 -png paper/icaart2027/ICAART2027_supplement.pdf paper/icaart2027/inspection/supplement
```

The current PDF page count is authoritative. Older ignored render files from draft pagination are not part of the final document.
