# Anonymous ICAART 2027 manuscript sources

Build both PDFs with Python 3 and a standard TeX Live installation containing
pdfLaTeX, BibTeX, Times/PSLaTeX, TikZ, algorithm2e, subcaption, footmisc,
booktabs, tabularx and hyperref:

```sh
python -B build.py
```

The outputs are `ICAART2027_submission.pdf` and
`ICAART2027_supplement.pdf`. Compilation uses the supplied, unchanged
SCITEPRESS article class and bibliography/style files in `template/`.
The authentic template was retrieved on 10 September 2026 from
https://www.scitepress.org/documents/SCITEPRESS_Conference_Latex.zip,
linked by https://icaart.scitevents.org/Templates.aspx.
`template/provenance.json` records the original archive and file hashes.
Its example sources are intentionally not redistributed in this compilation
archive because they are not needed to build the submission.

This archive is compilation-only. Numerical evidence, complete carrier
examples, author decisions and saved-evidence verification commands accompany
the draft in the repository's manuscript index. The source archive has no
keys, private conditioning rows, prepared packets, models, runtime directories,
execution ledgers or build caches. No network or neural inference is used to
compile it. Experimental assets are included as retained vector figure PDFs.

The main paper is anonymous and independently assessable. Regular Paper
supplementary-upload permission is unconfirmed. The supplement is prepared as
a companion artifact, not represented as accepted supplementary submission
material. The AI-disclosure/anonymity policy conflict is noted for author
review outside this compilation-only archive.
