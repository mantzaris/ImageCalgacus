# Final PDF visual inspection

Inspected 14 November 2026. Final PDF SHA-256:

`31875bcf4dd3481f20878e7cd13e6aec342cdfa2b159a7eb4e8cc920729bb79a`

All ten A4 pages were rendered at a 1,600-pixel long edge and visually inspected. Independent formatting and figure reviews are retained in `../inspection/format_review.md` and `../inspection/figure_review.md`. No human author approval is asserted.

| Page | Inspection |
|---|---|
| 1 | Conference header, title, “Anonymous Authors” with no identifying affiliation or email, 207-word abstract, keywords, and introduction are legible and contained within the template. |
| 2 | Introduction, focused related work and shared protocol flow without clipping. Numeric citations resolve. |
| 3 | Actual carrier overview is readable at 122 mm width. Dimension labels were moved below image edges; saved pixels and literal bytes are unchanged. The caption and serialization equation fit. |
| 4 | Pixel conditionals, three coder descriptions, capacity rules and photograph introduction are legible; equations and mathematical symbols render correctly. |
| 5 | Photograph method, grouping/uncertainty and the observer score definition fit without clipping. |
| 6 | Observer discussion, timing definitions and recovery results flow correctly. Original timings remain distinct from the development benchmark. |
| 7 | Recovery/goodput figure has readable labels, distinct token/channel units and saved uncertainty. The arithmetic failures and text detector separation remain explicit. |
| 8 | Context plot labels, paired-change direction and intervals are legible. The two-panel extension table is compact but readable, with no overlap. Header/body sizes remain class defaults. |
| 9 | Photograph limitations, discussion, conclusion and opening references fit. The direct identifying repository footnote is omitted. |
| 10 | Remaining references are readable and all links remain in the text area. The version-pinned PyTorch URL wraps its final `rst` onto a short line; its underfull warning is cosmetic, with no clipping. |

There are no overfull boxes, missing citations or unresolved reference labels. All fonts are embedded. The official 122 × 193 mm text area, body/caption/reference sizes, heading spacing and line spacing are retained. No negative-space commands, reduced fonts or compressed spacing were introduced to meet the limit. Normal paragraph/page breaks and float placement remain; pagination was achieved through substantive editing.

Three figure descriptions are exported through the official class into `DescriptionTexts.txt`. This does not imply full PDF tagging. The title page shows “Anonymous Authors”; names, affiliations and emails remain commented in the editable source. PDF author metadata is blank and the direct identifying repository link is commented out. Accurate third-person prior-work citations are retained. Final declarations remain the decisions recorded in `README.md`.
