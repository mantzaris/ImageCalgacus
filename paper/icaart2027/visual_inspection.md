# Single-PDF final visual inspection

All **12 main-paper pages** were rendered at 144 dpi and inspected after source consolidation from `0c7296327c0131201b3372a9c5bab70eddba4f0d`. The reference is a fresh build of that commit's source, preserving its latest abstract. All 12 pages have **zero differing RGB pixels**, exact layout-text equality and identical stable PDF metadata. Figure/table labels and citations also match. [Consolidation verification](consolidation_verification.json) records per-page hashes and the main-only eight-file build.

Main SHA256: `defe4d75c8acde581e1cd2f88f5467b02cff33b059e39037217343c3c0b67855`.

Companion SHA256: `094ea206525c25ae11b262affe043faa4e3836f07059d74c21a2bb1bb764d4af`.

Archive hashes and independent-build results are in [source_archive_verification.json](source_archive_verification.json).

## Main-page inspection

| Pages | Observations |
|---|---|
| 1–2 | Title and 180-word abstract fit the unchanged official format. Introduction gives the three-stage progression. Related-work attribution is readable. Exact header/packet fields fit without clipping. |
| 3–4 | Figure 1A–B shows actual canonical pixels, the verbatim text excerpt, generated PNG and complete source/recovered messages. The full size is stated without an unavailable link. No text/figure overlap. RGB conditioning, filtering, fixed/gated/A1 rules and equations remain legible. |
| 5–6 | Invariant-context construction, keyed placement and distortion bound are readable. Equation 4's number is on its normal separate line, without overlap. Figure 2A–C compares the same cover/stego at equal scale and ×32 absolute differences. The complete message and analytic-difference label are legible. Sparse low-amplitude differences remain faint, as expected from the actual pixels. GPU runtime identifiers fit. |
| 7–8 | Table 1 has readable columns. Source allocation, paired groups, uncertainty and timing boundaries are explicit. Photograph design is separate from the original allocation. Arithmetic capacity failures retain their own section and incomplete-prefix interpretation. |
| 9–10 | Table 2 preserves all six outcomes and original timings. Both detection scores and paired row changes appear in the main. GPU throughput, timings and overlapping memory measures are readable. Figure 3 shows 0/20 A1 text explicitly. Photograph results state the parity baseline's better fidelity/cost. |
| 11–12 | Figure 4 and Table 3 are readable without clipping or overlap. Discussion retains the text-filtering bottleneck and material limitations. Conclusion, anonymous AI disclosure and all references fit. Cross-page continuation is grammatical and bibliography text is not truncated. |

Main figures are 1–4 and tables 1–3. Original transports are **Figure 1A–B on page 3**. Photograph transport is **Figure 2 on page 6**. Four figure PDFs have extractable text, including annotations. There are no local-file access promises, companion dependencies, unresolved references, author metadata or internal drafting placeholders in the main PDF.

## Companion and source package

The 11-page companion was rebuilt without source or scientific-asset changes. Its extracted text and all 11 pages rendered at 144 dpi are identical to a fresh build of the starting source. Its previous full-page visual record remains in Git history. The current operation does not claim a new companion experiment or supplementary submission route.

The main compiles in an isolated directory containing only `main.tex`, three official files and four figure PDFs, with no BibTeX run or fragments. The formatted twenty-entry bibliography is byte-identical to the generated starting `.bbl`. Both PDFs also compile from the allowlisted source ZIP in an isolated temporary directory and reproduce local extracted text. Unused old figure copies are not duplicated in the ZIP, while all required assets are present. The official template download was rechecked on 12 September 2026 and all retained files match. No font, margin, line spacing or negative-spacing workaround was introduced.

## Counts and checks

The main has **41,500 extracted non-whitespace characters**, **44,135 conservatively estimated characters** and **180 abstract words**. The conservative count adds all four figures' extracted text again (1,635) plus 1,000 for extraction uncertainty. The companion has 30,057 extracted characters. Both build logs have no overfull boxes or undefined references/citations.

Saved-evidence checks preserve all six prospective outcomes, benchmark equivalence, AUCs, photograph metrics and coverage. No figures or experimental carriers were regenerated in this source-only task. All six local compute ledgers remain hash-identical to the starting state. **Zero GPU seconds** were added.

```sh
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify_consolidation.py
```

Render files are ignored build products, not experimental carriers. Rights, disclosure-placement and public-history questions remain in [AUTHOR_REVIEW.md](AUTHOR_REVIEW.md), outside the scientific narrative.
