# Single-PDF final visual inspection

All **12 main-paper pages** were rendered at 120 dpi and inspected after the final prose/layout edits. The two changed figures were also inspected separately. A final punctuation-only pass changed pixels on pages 2, 6, 7 and 8; those pages were rendered and reinspected. The other eight final pages are pixel-identical to the inspected renders. This record concerns editorial finalization from `79fd48c`, not new experimental evidence.

Main SHA256: `ffedfbb0c05512d67f861ce4d50862563a48ff9c277091e3044e73d1f83277a6`.

Companion SHA256: `5f9d0046fc43a4b420dd047333fae3cb59b2b3f9d056191952ace3243a267ca2`.

Archive hashes and independent-build results are in [source_archive_verification.json](source_archive_verification.json).

## Main-page inspection

| Pages | Observations |
|---|---|
| 1–2 | Title and 173-word abstract fit the unchanged official format. Introduction gives the three-stage progression. Related-work attribution is readable. Exact header/packet fields fit without clipping. |
| 3–4 | Figure 1A–B shows actual canonical pixels, the verbatim text excerpt, generated PNG and complete source/recovered messages. The full size is stated without an unavailable link. No text/figure overlap. RGB conditioning, filtering, fixed/gated/A1 rules and equations remain legible. |
| 5–6 | Invariant-context construction, keyed placement and distortion bound are readable. Equation 4's number is on its normal separate line, without overlap. Figure 2A–C compares the same cover/stego at equal scale and ×32 absolute differences. The complete message and analytic-difference label are legible. Sparse low-amplitude differences remain faint, as expected from the actual pixels. GPU runtime identifiers fit. |
| 7–8 | Table 1 has readable columns. Source allocation, paired groups, uncertainty and timing boundaries are explicit. Photograph design is separate from the original allocation. Arithmetic capacity failures retain their own section and incomplete-prefix interpretation. |
| 9–10 | Table 2 preserves all six outcomes and original timings. Both detection scores and paired row changes appear in the main. GPU throughput, timings and overlapping memory measures are readable. Figure 3 shows 0/20 A1 text explicitly. Photograph results state the parity baseline's better fidelity/cost. |
| 11–12 | Figure 4 and Table 3 are readable without clipping or overlap. Discussion retains the text-filtering bottleneck and material limitations. Conclusion, anonymous AI disclosure and all references fit. Cross-page continuation is grammatical and bibliography text is not truncated. |

Main figures are 1–4 and tables 1–3. Original transports are **Figure 1A–B on page 3**. Photograph transport is **Figure 2 on page 6**. Four figure PDFs have extractable text, including annotations. There are no local-file access promises, companion dependencies, unresolved references, author metadata or internal drafting placeholders in the main PDF.

## Companion and source package

The 11-page companion was rebuilt without source or scientific-asset changes. Its extracted text is byte-identical to the starting PDF (`e8441d01e1a1a4dcc994633f5a6204f5a4943b1149aa14fdf35de5863fff0a38` SHA256 of layout extraction). Its previous full-page visual record remains in Git history. The current operation does not claim a new companion experiment or supplementary submission route.

Both PDFs compile from the allowlisted source ZIP in an isolated temporary directory and reproduce local extracted text. Unused old figure copies are not duplicated in the ZIP, while all required assets are present. The official template download was rechecked on 12 September 2026 and all retained files match. No font, margin, line spacing or negative-spacing workaround was introduced.

## Counts and checks

The main has **41,519 extracted non-whitespace characters**, **44,154 conservatively estimated characters** and **173 abstract words**. The conservative count adds all four figures' extracted text again (1,635) plus 1,000 for extraction uncertainty. The companion has 30,057 extracted characters. Both build logs have no overfull boxes or undefined references/citations.

Saved-evidence checks preserve all six prospective outcomes, benchmark equivalence, AUCs, photograph metrics and coverage. Two regeneration runs produced identical PDF/SVG/PNG figure bytes. All six local compute ledgers remain hash-identical to the starting state. **Zero GPU seconds** were added.

```sh
pdftoppm -r 120 -png paper/icaart2027/ICAART2027_submission.pdf paper/icaart2027/build/single_pdf_render/main
```

Render files are ignored build products, not experimental carriers. Rights, disclosure-placement and public-history questions remain in [AUTHOR_REVIEW.md](AUTHOR_REVIEW.md), outside the scientific narrative.
