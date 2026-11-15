#!/usr/bin/env python3
"""Package this manuscript and verify an isolated CPU-only source rebuild."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "ImageCalgacus_ICBDAIA2027_source.zip"
ISOLATED = HERE / "verification" / "source-bundle-build"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    names = ["main.tex", "main.pdf", "main.bbl", "references.bib", "llncs.cls",
             "splncs04.bst", "preamble-conf.tex", "build.py", "build_figures.py",
             "package_source.py", "verify_evidence.py", "README.md", "FORMAT_NOTES.md",
             "CLAIM_EVIDENCE.md", "FIGURE_NOTES.md", "ASSET_NOTICES.md",
             "DescriptionTexts.txt", "evidence_audit.json",
             "verification/build.json", "verification/visual_inspection.md",
             "template/provenance.json", "template/springer-latex/readme.txt"]
    files = [HERE / name for name in names]
    files += sorted((HERE / "figures").glob("*.pdf"))
    files += sorted((HERE / "figures").glob("*.svg"))
    files += sorted(p for p in (HERE / "data").rglob("*") if p.is_file())
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise SystemExit("Missing source files: " + ", ".join(missing))
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(HERE).as_posix())
    if ISOLATED.exists():
        shutil.rmtree(ISOLATED)
    ISOLATED.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as archive:
        archive.extractall(ISOLATED)
    subprocess.run([sys.executable, "build.py", "--render"], cwd=ISOLATED, check=True)
    local_text = (HERE / "inspection" / "main-layout.txt").read_text()
    rebuilt_text = (ISOLATED / "inspection" / "main-layout.txt").read_text()
    assert local_text == rebuilt_text, "Extracted text differs after isolated rebuild"
    original_pages = sorted((HERE / "inspection").glob("page-*.png"))
    rebuilt_pages = sorted((ISOLATED / "inspection").glob("page-*.png"))
    assert len(original_pages) == len(rebuilt_pages) == 10
    identical_pages = {original.name: sha(original) == sha(rebuilt)
                       for original, rebuilt in zip(original_pages, rebuilt_pages)}
    assert all(identical_pages.values()), "Rendered page differs after isolated rebuild"
    record = {"archive": ARCHIVE.name, "archive_sha256": sha(ARCHIVE),
              "files": len(files), "isolated_build_passed": True,
              "total_pages": 10, "extracted_text_identical": True,
              "rendered_pages_identical": identical_pages,
              "research_execution": "None; LaTeX compilation and PDF rasterization only",
              "source_sha256": {p.relative_to(HERE).as_posix(): sha(p) for p in files}}
    (HERE / "verification" / "source_bundle.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Source bundle verified: 10 pages, identical text and rendered pages.")


if __name__ == "__main__":
    main()
