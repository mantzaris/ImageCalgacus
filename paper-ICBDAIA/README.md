# ICBDAIA 2027 manuscript draft

**Hiding Images in Text and Text in Images with Generative AI**

- [Manuscript PDF](main.pdf): **10 total pages**, including all figures, tables and references; **207-word abstract**.
- [Editable LaTeX](main.tex), [bibliography](references.bib), and [self-contained source bundle](ImageCalgacus_ICBDAIA2027_source.zip).
- [Formatting and template provenance](FORMAT_NOTES.md), [claim-to-evidence map](CLAIM_EVIDENCE.md), [asset notices](ASSET_NOTICES.md), and [figure provenance](FIGURE_NOTES.md).
- [Build checks](verification/build.json), [saved-record numerical audit](evidence_audit.json), [visual review](verification/visual_inspection.md), and [isolated source-bundle verification](verification/source_bundle.json).

This is the anonymous PDF version for review. Author names, affiliations and emails are commented out in `main.tex` for later restoration; the PDF author metadata is empty and the direct link to this paper's identifying repository is also commented out. **Use `main.pdf` for the anonymous submission: the editable sources and source ZIP deliberately retain identities.** Ordinary third-person citations to prior work retain accurate attribution.

This is a complete new venue-adapted draft. The direct title and opening example explain what is sent and recovered before introducing coding terminology. The abstract distinguishes recovery from concealment, and the argument follows saved-file recovery, capacity, detector knowledge and execution cost. Unfavorable results remain explicit. Three figures use actual saved carriers and retained numerical intervals; a combined table keeps the GPU and photograph extensions compact. Sixteen cited references fit within the page limit.

## Build

From the repository root:

```sh
python3 paper-ICBDAIA/build.py --render
```

Inside an extracted source bundle:

```sh
python3 build.py --render
```

The build uses Python 3's standard library, pdfLaTeX, BibTeX and Poppler (`pdfinfo`, `pdftotext`, `pdffonts`, and optionally `pdftoppm`). Required standard TeX packages include `newtxtext`, `newtxmath`, `fontenc`, `inputenc`, `geometry`, `fancyhdr`, `etoolbox`, `graphicx`, `booktabs`, `array`, `tabularx`, `url` and `hyperref`. The unchanged official `llncs.cls` and `splncs04.bst` are local. No repository research module, model, key, GPU or network connection is needed to compile.

Direct compilation is also supported:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

`main.tex` uses the local `references.bib`. The original ICAART manuscript has its own **inline bibliography** and remains unchanged; this new bibliography does not modify it. The build checks the total page count, abstract length, missing references and overfull boxes. One harmless underfull line remains where the version-pinned PyTorch reference URL wraps; it is readable and contained in the text area. All PDF fonts are embedded. Figure descriptions are supplied through the official class's `\Description` facility and exported to `DescriptionTexts.txt`; this is not a claim that the PDF is fully tagged.

Optional figure regeneration uses only bundled saved inputs:

```sh
python3 paper-ICBDAIA/build_figures.py
```

This requires Matplotlib, NumPy and Pillow. Existing figure PDFs are sufficient for the manuscript build. Original source paths/hashes, literal example bytes, saved intervals and rendering package versions are recorded under `data/`. No statistical interval is refitted by this plotting step.

The source bundle is produced and rebuilt in isolation with:

```sh
python3 paper-ICBDAIA/package_source.py
```

The bundle contains the manuscript, local styles, bibliography, figure PDFs and editable SVGs, plotting script and all its saved inputs, notices and build instructions. The full conference template download and inspection material remain in `template/` in the repository; they are not required for compilation. The archive excludes model weights, private packets/keys, execution environments, historical raw research artifacts and build caches. Its isolated build is checked for identical extracted text and all ten rendered page images; PDF metadata timestamps may differ.

## Completed verification and preservation

All ten rendered pages were inspected. Figure 1's dimension labels were separated from the image edges; headings, captions, equation flow, references, table alignment and final-size figure labels were reviewed. There are no missing citations/references, overfull boxes or unresolved scientific placeholders. The PDF displays “Anonymous Authors” with no affiliation. The supplied identities remain only in commented source and author-side notes; this is intentional for later restoration.

`verify_evidence.py` checks saved counts, goodput, AUC point estimates, timing ratios and historical equivalence records using the standard library. It requires the full research checkout, unlike compilation and figure plotting. It does **not** repeat neural decoding, authentication, timing measurements, detector training or experiments. Accepted intervals are reused. The audit reconciles misleading arithmetic failure labels, offered-versus-recovered rates, timing boundaries and reused controls in `CLAIM_EVIDENCE.md`.

All new manuscript work is inside this directory. The preservation check hashes **4,320 pre-existing tracked files** and confirms no changes to the original manuscript, code, artifacts or experimental declarations. No new experiments, inference, parameter sweeps, training or timing benchmarks were run. No paper was submitted and no organizer was contacted.

## Remaining author decisions

1. **Restoring author information.** The full supplied author, numbered-affiliation and email block remains commented in `main.tex`, together with a commented `pdfauthor` setting. To restore the identified version, remove the active anonymous `\author`, `\authorrunning` and empty `\institute` lines, then uncomment the retained block and rebuild. The identifying repository footnote is retained as a separate comment. The sources intentionally remain identifiable; the PDF is the review artifact.
2. **Human review and declarations.** Review the scientific text, references, contribution attribution, funding/conflicts and originality/overlap with the existing public manuscript. Confirm venue eligibility and publishing declarations. No approval or endorsement is invented. The author will add the final disclosure text manually.
3. **Source terms and photographs.** Fashion-MNIST/Gutenberg notices are retained. This draft reproduces no BSDS photograph; it reports the saved photograph comparison numerically. Specific republication rights for photographs and derivatives in the old manuscript remain unresolved, and would need review before adding those assets here. This revision does not clear old publication-permission questions.
4. **Camera-ready Word delivery.** Initial submission is PDF. The conference separately requests a camera-ready PDF and Word/DOC; an actual macro-free Word conversion or an explicit exemption remains to be arranged after acceptance. The linked template is technically DOCM, despite the reference manuscript's older DOCX label. See `FORMAT_NOTES.md` for the inspected package identity and official LaTeX support. No supplementary PDF submission is assumed.
