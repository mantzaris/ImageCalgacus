# ICBDAIA 2027 formatting and submission notes

Verified 14 November 2026. These notes concern ImageCalgacus only. The other manuscript named by the user was consulted for template provenance and its page-placement helper; none of its research material was imported.

## Current conference requirements

The [conference website](https://icbdaia.com/) and [official EasyChair call](https://easychair.org/cfp/ICBDAIA27) specify English full papers of 8–10 pages in the Springer template and announce publication in **Lecture Notes in Networks and Systems (LNNS)**. This draft applies the user's stricter explicit interpretation: **10 total pages maximum, including references**.

Initial submission is a **PDF uploaded to EasyChair**. The conference separately requests a camera-ready PDF and Word/DOC file after acceptance, together with publishing and registration documents. Springer's support for LaTeX does not override that conference requirement. A suitable macro-free Word version or an explicit organizer exemption remains a camera-ready decision. No paper was submitted and no organizer was contacted.

Neither checked public conference page specifies a single-blind or double-blind review policy. The template's author fields do not settle this question. At the author's request, the current PDF uses “Anonymous Authors”, an empty institute and blank PDF author metadata. The supplied two-author block, formatted with `\inst{1}`/`\inst{2}`, `\institute` and `\email`, is retained as comments for later restoration. The direct identifying repository footnote is also commented out. Ordinary third-person prior-work references remain accurately attributed. Editable sources and their ZIP intentionally retain identities; the current PDF is the anonymous review artifact. The ICAART review policy is not carried over.

## Downloaded conference template

The [actual conference-linked file](https://drive.google.com/file/d/1X67baiOAmfXYsMWcHocoHNuiSS75y24w/view) was freshly downloaded using its [download endpoint](https://drive.google.com/uc?export=download&id=1X67baiOAmfXYsMWcHocoHNuiSS75y24w). The unchanged file is retained as `template/conference-template.docm`, SHA-256:

`68e89eda8b4d1a8529c65e9dd7fdcf1c9264f62ca233537a6b5db0a6d936de12`

**Correction to the reference repository's notes:** this is a macro-enabled **DOCM**, not DOCX. The package content types declare `application/vnd.ms-word.document.macroEnabled.main+xml` and contain `word/vbaProject.bin`. Renaming the extension does not convert it to DOCX. Springer's author instructions expressly require macro-free DOCX for Word submissions. The original downloaded template is preserved for provenance, not offered as a completed manuscript or a file to submit.

The package XML, styles, page dimensions, margins and three header variants were inspected. Its content was extracted to `template/conference-template-text.txt`; LibreOffice rendered it to `template/conference-template.pdf`, and all three rendered pages were visually inspected. The last template page is blank apart from its page number; that is an artifact of the template sample, not a requirement for the paper.

The template specifies a **150–250-word abstract**, so the requested 180–220-word abstract fits. It uses A4 pages, approximately 44 mm left/right and 52 mm top/bottom margins, and a **122 × 193 mm text area**. The body uses Times at 10 points; title 14-point bold; first-level headings 12-point bold; second-level headings 10-point bold; abstract, captions and references 9 points. Only two heading levels are numbered. Tables have captions above, figures below. The reference example prefers bracketed numeric citations.

## Supported official LaTeX equivalent

The [Springer proceedings author page](https://www.springernature.com/gp/authors/publish-a-book/step-by-step-conference-proceedings) supplies the relevant resources. Its [Engineering/Physics/Mathematics author instructions](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/26362278/data/v2) expressly include LNNS and permit LaTeX or Word. The same page links the [official proceedings LaTeX package](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/26361882/data/v8). Its README states that it serves LNCS and other proceedings book series. Its dimensions and heading sizes match the conference template. This direct evidence supports the class choice; “Springer” alone would not.

The package was freshly downloaded and retained unchanged as `template/springer-proceedings-latex.zip`, with its full extracted contents in `template/springer-latex/`. The supplied **`llncs.cls` v2.25 (2026-09-03)** and **`splncs04.bst`** are copied unchanged into the manuscript directory. Their original copyright notices apply; the repository's license does not relicense them. The official sample uses T1 encoding, `newtxtext` and `newtxmath` with the `varvw` option. Those Times-compatible fonts also agree with the actual conference template. The general prose instructions still mention CMR, but the newer concrete sample selects these fonts.

Use `\documentclass[orivec]{llncs}` without `runningheads`, the official font packages, and `\input{preamble-conf}`. The supported `orivec` option retains the ordinary mathematical vector accent. `preamble-conf.tex` reproduces the conference's A4 page placement, unchanged 122 × 193 mm text area, first-page 8-point bold conference header and later 9-point outer page numbers. It derives from the [reference manuscript's helper](https://github.com/mantzaris/OverseeingManyLLMs/blob/main/paper-ICBDAIA/preamble-conf.tex), checked against the newly downloaded template. It changes no body font sizes, line spacing, heading spacing, caption spacing or bibliography formatting. No compression or negative-space adjustment is used.

The supplied alphabetically sorted `splncs04` style gives numbered citations consistent with the concrete conference sample; LNNS instructions also permit numbered references customary in the field. References remain inside the total page budget. The three-page `template/format-fixture.tex` compiled without warnings and verified a 347.12361 × 549.13818 TeX-point text block (122 × 193 mm), A4 output and correct first/even/odd headers. Its rendered pages were inspected. File hashes and inspection details are recorded in `template/provenance.json`.

## Remaining author decisions

The author will add the final disclosure text manually. Human review, publishing declarations, unresolved asset permissions, and camera-ready Word delivery remain author decisions. These issues do not prevent preparation of the requested editable draft. Supporting repository records are not an assumed supplementary PDF submission. Accessible descriptions for selected figures accompany the manuscript sources. Final page count and manuscript PDF checks are recorded in `README.md` and the manuscript's verification record rather than inferred from the template fixture.
