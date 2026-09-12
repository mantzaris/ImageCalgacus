# Final visual inspection

All twelve main-paper pages and all eleven companion pages were rendered at 120 dpi and visually inspected after the photograph extension was integrated. This record supersedes the previous draft's layout measurements, not its experimental evidence.

- Main PDF SHA256: `00a94e6995d918ecfea6518e6dbbf3d79ae474eadfc47e27db2cc8bcfb45a727`.
- Companion PDF SHA256: `6398769132013ec8b16de76fdf5f36251ae02877ad771680218bd3eda7daefb2`.
- Isolated-build source ZIP SHA256: `529dcc19486d8d3a0342c851546ed54c793aa0290df9dec6be39bee6186715e4`.

## Main paper

| Pages | Inspection |
|---|---|
| 1–2 | Title, 184-word abstract, introduction and new related-work paragraph fit the authentic layout. No author block or clipped text. The earlier orphaned word was removed through prose editing. |
| 3–4 | Packet and conditional equations are legible. Figure 1A–B preserves both actual historical examples, complete source/recovered texts and the explicitly incomplete carrier excerpt. Caption does not claim reviewer access to local paths. |
| 5–6 | Coarse-context rank protocol and joint RGB equation are readable. Equation 4's number occupies a separate normal line without overlap. Figure 2 on page 6 shows the complete literal message and actual photograph at readable final size. Source and recovered words match. No photograph enhancement. |
| 7–8 | Table 1, model/GPU setup, grouped uncertainty, observer assumptions, bounded photograph allocation and all six prospective recovery outcomes are readable. Distinct timing and statistical units remain explicit. |
| 9–10 | Table 2 preserves original prospective timings and arithmetic failures. Figure 3's rates/intervals are legible. GPU speedup and new paired fidelity findings remain in the main text. No learned-partition advantage is implied. |
| 11–12 | Figure 4, Table 3, limitations, conclusion, AI disclosure and all references fit. Table 3 matches unrounded source records after stated rounding. Cross-page conclusion continuation is grammatical. No missing citations, clipped bibliography or oversized final whitespace. |

Main figures are 1–4 and tables 1–3. The old worked examples are Figure 1A–B on page 4; the new complete photograph example is Figure 2 on page 6. Both are in the first half. The detailed historical GPU plot is now in the companion, with its main numerical findings preserved.

## Companion

| Pages | Inspection |
|---|---|
| 1–2 | Title/abstract, process diagram Figure S1, expanded Table S1 and relocated packet/mixture detail are clear. No duplicate worked-example figure. |
| 3–4 | Six-panel detection Figure S2 and full-score/overhead Tables S2–S3 are legible, without clipping or overlapping rows. Original values and failed-carrier inclusion remain. |
| 5–6 | Arithmetic Figure S3 and paired sequence/static Figure S4 preserve observed checkpoints and payload identities. New extension identifiers appear in S7, separate from historical allocations. |
| 7–8 | Context Table S4, descriptive Figure S5/Table S5, full benchmark Table S6 and new placement/scoring details are readable. Long profile identifier and equations fit. |
| 9–10 | Historical GPU Figure S6, new failure/fidelity/accounting detail, reproducibility and references are readable. Old benchmark memory measures remain distinct. |
| 11 | Figure S7 shows the first three frozen covers, actual carriers and differences ×32. All labels/caption fit. Differences are sparse and faint by design, not enhanced for effect or presented as no changes. Natural image aspect ratios and pixels are retained. |

Companion figures are S1–S7 and tables S1–S6. The new figure PDFs are exact copies of the review exports. Standalone new PDF/PNG previews were also inspected. The four-row summary Markdown and LaTeX values agree with their source CSV, and the manuscript's two-row variant is readable.

## Build and numerical checks

Both logs are free of overfull boxes, unresolved references and undefined citations. Normal float placement resolved an initial companion overflow. No official template file, margin, font size, line spacing or negative-spacing workaround was introduced. The final main count is **42,189 extracted non-whitespace characters**, **44,842 conservatively estimated**, with **184 abstract words**. The companion is eleven pages and 30,057 extracted characters. The source ZIP compiles in an isolated directory and reproduces both PDF texts exactly. Empty author metadata is verified.

Reproduce inspection renders after building:

```sh
pdftoppm -r 120 -png paper/icaart2027/ICAART2027_submission.pdf paper/icaart2027/build/main-inspect
pdftoppm -r 120 -png paper/icaart2027/ICAART2027_supplement.pdf paper/icaart2027/build/supp-inspect
```

Raster previews are ignored build outputs, not manuscript assets. Experimental carriers are not rewritten by rendering. Compilation and inspection add zero GPU time. The separately authorized extension's 429.149258 charged seconds remain in its own ledger. Photograph publication rights, AI-disclosure placement and a Regular Paper supplementary route remain author-review issues.
