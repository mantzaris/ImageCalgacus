#!/usr/bin/env python3
"""Build only this manuscript; never run research or regenerate measurements."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def run(command, destination=None):
    env = os.environ.copy()
    for variable in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS"):
        env.pop(variable, None)
    result = subprocess.run(command, cwd=HERE, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if destination:
        destination.write_text(result.stdout)
    if result.returncode:
        raise SystemExit(result.stdout)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="render all pages with pdftoppm")
    args = parser.parse_args()
    inspection = HERE / "inspection"
    verification = HERE / "verification"
    inspection.mkdir(exist_ok=True)
    verification.mkdir(exist_ok=True)
    latex = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    run(latex, inspection / "compile-first.txt")
    biblog = run(["bibtex", "main"], inspection / "bibtex.txt")
    run(latex, inspection / "compile-second.txt")
    run(latex, inspection / "compile-final.txt")
    log = (HERE / "main.log").read_text()
    forbidden = [r"undefined", r"multiply defined", r"Overfull ",
                 r"Rerun to get", r"Label\(s\) may have changed"]
    if any(re.search(pattern, log, re.I) for pattern in forbidden):
        raise SystemExit("Resolve citations/references or overfull boxes; see main.log")
    if "Warning--" in biblog:
        raise SystemExit("Resolve BibTeX warnings; see inspection/bibtex.txt")
    info = run(["pdfinfo", "main.pdf"], inspection / "pdfinfo.txt")
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    if not 8 <= pages <= 10:
        raise SystemExit("Paper must have 8–10 total pages; got %d" % pages)
    run(["pdftotext", "-layout", "main.pdf", "inspection/main-layout.txt"])
    fonts = run(["pdffonts", "main.pdf"], inspection / "fonts.txt")
    source = (HERE / "main.tex").read_text()
    abstract = source.split(r"\begin{abstract}", 1)[1].split(r"\keywords", 1)[0]
    abstract_words = len(abstract.split())
    if not 180 <= abstract_words <= 220:
        raise SystemExit("Abstract outside requested 180–220 words")
    if re.search(r"TODO|TBD|FIXME|XXX", source):
        raise SystemExit("Unresolved editorial placeholder found")
    if args.render:
        run(["pdftoppm", "-scale-to", "1600", "-png", "main.pdf", "inspection/page"],
            inspection / "render.log")
    names = ["main.tex", "main.pdf", "main.bbl", "references.bib", "llncs.cls",
             "splncs04.bst", "preamble-conf.tex"]
    names += [str(p.relative_to(HERE)) for p in sorted((HERE / "figures").glob("*.pdf"))]
    report = {
        "total_pages": pages,
        "abstract_words_whitespace_count": abstract_words,
        "missing_citations_references": False,
        "overfull_boxes": False,
        "remaining_log_diagnostics": [line for line in log.splitlines()
                                      if "Warning" in line or "Underfull" in line],
        "anonymous_review_version": r"\author{Anonymous Authors}" in source,
        "pdf_author": re.search(r"^Author:[ \t]*(.*)$", info, re.M).group(1) if re.search(r"^Author:[ \t]*(.*)$", info, re.M) else "",
        "identified_author_block_retained_in_comments": "% \\author{Alexander V. Mantzaris" in source,
        "rendered_all_pages": args.render,
        "research_execution": "None; compilation and PDF presentation checks only",
        "sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in names},
    }
    (verification / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Built main.pdf: %d total pages; %d-word abstract; no missing references or overfull boxes."
          % (pages, abstract_words))


if __name__ == "__main__":
    main()
