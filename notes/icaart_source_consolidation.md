# ICAART single-file source consolidation

## Starting point and scope

Starting revision was `0c7296327c0131201b3372a9c5bab70eddba4f0d` on `main`,
with a clean working tree and matching remote main. That commit contains a later
abstract edit relative to the preceding editorial finalization. It is preserved
verbatim. The committed PDF predated that edit, so the comparison baseline was
a fresh compilation of the actual starting sources, not the stale PDF binary.

This operation changes source organization only. No wording, result, equation,
citation, caption, table, graphic, model setting or experimental evidence is
revised. No experiment, carrier generation or neural inference ran. No figure
generator was needed. Existing rights and venue-policy questions remain in
`paper/icaart2027/AUTHOR_REVIEW.md` without a new policy determination.

## Canonical source and retained dependencies

`paper/icaart2027/main.tex` now contains its preamble and custom macros, title,
keywords, abstract, ten formerly external section fragments, all three complete
tables, equations, figure environments, disclosure and twenty formatted
bibliography entries. The two formerly external main table bodies are included
at their original positions. The exact starting `main.bbl` output is inside the
original small-font bibliography group. Comments identify each inlined origin.

The main reads no manuscript fragment, `.bib` or `.bbl`. Its external local
dependencies are three official files (`article.cls`, `SCITEPRESS.sty`,
`apalike.sty`) and four existing figure PDFs. Standard installed LaTeX packages
remain required. Figures and official implementation files were not inlined or
modified. No appendix or companion content was added to the submission.

The ten main-only section files and `tables/main_outcomes.tex` and
`tables/cover_main.tex` were removed after verification. Their content is fully
present in the canonical main and recoverable from Git history. `preamble.tex`,
`sections/cover_supplement.tex`, the TikZ diagram and six companion table
fragments remain for the separate supplement. `references.bib` and `apalike.bst`
remain for its compilation and reference maintenance, not main compilation.

`build.py --target main` compiles the canonical file directly in three pdfLaTeX
passes without BibTeX. `--target supplement` and the default both-document build
preserve the companion workflow. `build_tables.py` now writes companion tables
only. No build stage reconstructs or overwrites edits in `main.tex`.

## Equivalence verification

The first naive inline build exposed trailing-space differences at former file
boundaries. Explicit `\space` tokens retain those original spaces. This restores
the original paragraph wrapping and table placement without changing fonts,
margins, line spacing, template files or manuscript prose.

`verify_consolidation.py` reconstructs the starting Git source in a temporary
directory and compiles the comparison PDFs. In a different temporary directory,
it copies exactly eight files: `main.tex`, three official files and four figure
PDFs. No old preamble, section, table or bibliography source is present in that
main-only directory. Three pdfLaTeX passes complete without BibTeX. The recorder
confirms no fragment or bibliography-source reads.

Results recorded in `paper/icaart2027/consolidation_verification.json`:

- Main PDF remains 12 pages. Layout text is byte-identical to the fresh baseline.
- All 12 page renders at 144 dpi have zero differing RGB pixels.
- All twenty formatted bibliography entries match the original generated `.bbl`
  byte-for-byte. Citations, labels and figure/table-list records are identical.
- Stable metadata matches, including empty author, title, subject, keywords,
  creator, producer, A4 dimensions and PDF version. Timestamps and file sizes
  are excluded from metadata equivalence because rebuilding can change them.
- The separate 11-page companion remains text- and pixel-identical.
- Every main page was visually inspected, including all four figures and three
  tables. Figure 1 remains on page 3 and Figure 2 on page 6. No clipping,
  unresolved references or layout regressions were observed.
- The source ZIP compiles both PDFs independently and reproduces local extracted
  text. It contains no obsolete main section/table fragments or private material.

The unchanged fresh-baseline counts are 41,500 extracted non-whitespace
characters, 44,135 conservatively estimated characters and 180 abstract words.
The conservative calculation duplicates the four figure PDFs' 1,635 extracted
characters and adds 1,000 for extraction uncertainty. This leaves a 5,865-character
margin below the previously verified 50,000 limit. The older count differences
come from the abstract edit already in the starting commit, not this task.

Existing saved-evidence verification passed, including 3,700 protected public
files, six original recovery cells, paired GPU benchmark and context scores,
and all six unchanged local ledgers. Cumulative historical usage remains
89,404.217194 charged seconds. This source task adds **zero GPU seconds**.

## Commands and records

From the repository root:

```sh
python -B paper/icaart2027/build.py
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify_consolidation.py
../llm-rankcloak/.venv/bin/python -B paper/icaart2027/verify.py
python -B paper/icaart2027/package_source.py
```

The existing interpreter supplies Pillow and the retained analysis dependencies;
no sibling source imports or model inference are used for consolidation. The
compile-only ZIP requires standard TeX packages and Python for its optional
wrapper. `BUILD_README.md` also provides a direct pdfLaTeX command.

The updated PDFs and `ICAART2027_source.zip`, consolidation record, archive
verification, manuscript verification and visual-inspection record are all in
`paper/icaart2027/`. The README and results index identify the single editable
source and preserve the separate companion's purpose. The authorized change
set is confined to manuscript organization, verification and documentation.
