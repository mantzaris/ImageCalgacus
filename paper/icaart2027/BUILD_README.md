# Anonymous ICAART 2027 manuscript sources

## Canonical submission

Edit `main.tex` directly. This is the sole editable main manuscript, including
its preamble, macros, sections, equations, captions, complete tables, disclosure
and formatted `thebibliography` environment. Compilation never assembles or
overwrites this file from fragments. The explicit boundary spaces preserve the
original file-loading whitespace and verified layout.

From this directory, with Python 3 and the standard TeX packages installed:

```sh
python -B build.py --target main
```

The output is `ICAART2027_submission.pdf`. The main build runs pdfLaTeX three
times and does not run BibTeX. Its only local dependencies are:

- `template/article.cls`, `template/SCITEPRESS.sty`, `template/apalike.sty`.
- `figures/figure1_transport_submission.pdf`.
- `figures/cover_transport_submission.pdf`.
- `figures/figure2_recovery_rate.pdf`.
- `figures/context_auc.pdf`.

The direct equivalent, producing `main.pdf` without the Python wrapper, is:

```sh
for tex_pass in 1 2 3; do
  TEXINPUTS="template/:" pdflatex -interaction=nonstopmode -halt-on-error main.tex
done
```

Standard system dependencies include pdfLaTeX, Times/PSLaTeX, TikZ, algorithm2e,
subcaption, footmisc, booktabs, tabularx and hyperref. Neither a bibliography
database nor an external `.bbl`, preamble, section or table fragment is required
for the submission. The class, style files and normal packages remain external.

## Separate companion and reference maintenance

```sh
python -B build.py --target supplement
python -B build.py
```

The first command builds only `ICAART2027_supplement.pdf`. The second builds
both PDFs. The companion still uses BibTeX and its retained `preamble.tex`,
`sections/cover_supplement.tex`, `figures/method_diagram.tex`, six table fragments,
figure PDFs, `references.bib` and `template/apalike.bst`. These fragments are not
an alternative source of the main paper. Nothing from the companion is merged
into the main.

`references.bib` is retained for the companion and future reference maintenance.
The main's inline bibliography is the exact existing apalike-formatted output.
Updating the database alone will not update it. Future reference edits must
explicitly update the authoritative bibliography in `main.tex`; if BibTeX is
used to prepare replacement entries, do that in a scratch document and review
the replacement rather than making the ordinary build regenerate `main.tex`.

## Template and archive scope

Compilation uses the unchanged supplied SCITEPRESS files in `template/`.
The authentic template was retrieved on 10 September 2026 from
https://www.scitepress.org/documents/SCITEPRESS_Conference_Latex.zip,
linked by https://icaart.scitevents.org/Templates.aspx.
`template/provenance.json` records the original archive and file hashes.
Its example sources are intentionally not redistributed in this compilation
archive because they are not needed to build either document.

This archive is compilation-only. Numerical evidence, complete carrier
examples, author decisions and saved-evidence verification commands accompany
the draft in the repository's manuscript index. The archive has no keys,
private conditioning rows, prepared packets, models, runtime directories,
execution ledgers or build caches. No network or neural inference is used.
Figures are retained vector PDFs, not regenerated experimental carriers.

The main paper is anonymous and independently assessable. Regular Paper
supplementary-upload permission is unconfirmed. The companion is not
represented as accepted supplementary submission material. The unresolved
AI-disclosure/anonymity and photograph-permission questions remain in the
author review record outside this compilation-only archive.
