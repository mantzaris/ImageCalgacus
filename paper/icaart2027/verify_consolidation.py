#!/usr/bin/env python3
"""Verify source-only consolidation against a fresh build of the starting commit.

Uses Git, the installed TeX toolchain, Poppler and Pillow. No models, private
runtime files or experimental generators are used. The main-only build receives
exactly one TeX source, three unchanged official files and four figure PDFs.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STARTING_COMMIT = "0c7296327c0131201b3372a9c5bab70eddba4f0d"
MAIN_FILES = (
    "main.tex", "template/article.cls", "template/SCITEPRESS.sty",
    "template/apalike.sty", "figures/figure1_transport_submission.pdf",
    "figures/cover_transport_submission.pdf", "figures/figure2_recovery_rate.pdf",
    "figures/context_auc.pdf",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pdf_text(path):
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"])


def metadata(path):
    info = subprocess.check_output(["pdfinfo", str(path)], text=True)
    result = dict(line.split(":", 1) for line in info.splitlines() if ":" in line)
    # These reflect packaging, not visible content or the document identity.
    return {key: value.strip() for key, value in result.items()
            if key not in ("CreationDate", "ModDate", "File size")}


def aux_signature(path):
    return [line for line in path.read_text().splitlines()
            if re.match(r"\\(?:newlabel|bibcite|citation|@writefile)\b", line)]


def check_log(path):
    text = path.read_text()
    assert "Overfull" not in text and "undefined" not in text.lower(), path


def compare_pdfs(baseline, revised, temporary, stem):
    original_text, revised_text = pdf_text(baseline), pdf_text(revised)
    assert original_text == revised_text, stem + ": extracted text changed"
    old_metadata, new_metadata = metadata(baseline), metadata(revised)
    assert old_metadata == new_metadata, stem + ": document metadata changed"
    render = HERE / "build/consolidation_render"
    render.mkdir(parents=True, exist_ok=True)
    prefixes = [temporary / (stem + "-baseline"), render / stem]
    for path, prefix in zip((baseline, revised), prefixes):
        subprocess.run(["pdftoppm", "-r", "144", "-png", str(path), str(prefix)], check=True)
    pages = []
    for old in sorted(temporary.glob(stem + "-baseline-*.png")):
        suffix = old.name.removeprefix(stem + "-baseline-")
        new = render / (stem + "-" + suffix)
        with Image.open(old) as old_image, Image.open(new) as new_image:
            a, b = old_image.convert("RGB"), new_image.convert("RGB")
            assert a.size == b.size and a.tobytes() == b.tobytes(), (stem, suffix)
            assert ImageChops.difference(a, b).getbbox() is None
            pages.append({"page": int(suffix.removesuffix(".png")),
                          "size_pixels": list(a.size), "rgb_sha256": sha(a.tobytes()),
                          "changed_pixels": 0})
    assert len(pages) == int(new_metadata["Pages"])
    return {"pages": len(pages), "extracted_text_identical": True,
            "extracted_text_sha256": sha(revised_text),
            "extracted_nonwhitespace_characters": len(re.sub(r"\s", "", revised_text.decode())),
            "stable_metadata_identical": True, "metadata": new_metadata,
            "raster_dpi": 144, "all_rendered_pixels_identical": True,
            "page_comparisons": pages, "pdf_sha256": sha(revised.read_bytes())}


def main():
    source = (HERE / "main.tex").read_text()
    assert not re.search(r"\\(?:input|include|subfile|bibliography|bibliographystyle)\s*\{", source)
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", source)
    assert sorted(figures) == sorted(p for p in MAIN_FILES if p.startswith("figures/"))
    with tempfile.TemporaryDirectory(prefix="icaart-consolidation-") as temp:
        temporary = Path(temp)
        # Rebuild the actual starting source, including its later abstract edit.
        # The previously committed PDF was stale relative to that source edit.
        archive = subprocess.check_output(
            ["git", "archive", STARTING_COMMIT, "paper/icaart2027"], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as packed:
            for member in packed.getmembers():
                assert not member.issym() and not member.islnk()
                assert (temporary / member.name).resolve().is_relative_to(temporary)
            packed.extractall(temporary)
        original = temporary / "paper/icaart2027"
        subprocess.run([sys.executable, "-B", "build.py"], cwd=original, check=True)
        original_bbl = (original / "build/main.bbl").read_text()
        inline_bbl = source.split("% BEGIN INLINE main.bbl (apalike output from starting revision)\n", 1)[1].split("% END INLINE main.bbl", 1)[0]
        assert original_bbl == inline_bbl

        isolated = temporary / "single-file-only"
        for name in MAIN_FILES:
            target = isolated / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(HERE / name, target)
            if name != "main.tex":
                assert (original / name).read_bytes() == target.read_bytes(), name
        assert sorted(str(p.relative_to(isolated)) for p in isolated.rglob("*") if p.is_file()) == sorted(MAIN_FILES)
        env = os.environ.copy()
        env["TEXINPUTS"] = str(isolated / "template") + os.pathsep + str(isolated) + os.pathsep
        command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-recorder", "main.tex"]
        with (isolated / "compile.txt").open("w") as output:
            for _ in range(3):
                subprocess.run(command, cwd=isolated, env=env, stdout=output, stderr=subprocess.STDOUT, check=True)
        check_log(isolated / "main.log")
        dependencies = (isolated / "main.fls").read_text()
        for forbidden in (".bib", ".bbl", "preamble.tex", "/sections/", "/tables/", str(HERE)):
            assert forbidden not in dependencies, forbidden
        assert aux_signature(original / "build/main.aux") == aux_signature(isolated / "main.aux")
        report = {"passed": True, "starting_commit": STARTING_COMMIT,
                  "scope": "Source organization only; unchanged text, bibliography, labels, graphics, layout and stable metadata",
                  "baseline": "Fresh compilation of starting Git source, not its stale committed PDF",
                  "main_only_files": {name: sha((HERE / name).read_bytes()) for name in MAIN_FILES},
                  "main_only_pdflatex_runs": 3, "main_only_bibtex_runs": 0,
                  "recorder_confirms_no_fragment_or_bibliography_source_reads": True,
                  "inlined_bibliography_matches_generated_bbl": True,
                  "bibliography_entries": len(re.findall(r"\\bibitem\[", inline_bbl)),
                  "labels_citations_and_table_figure_lists_identical": True,
                  "verification_script_sha256": sha(Path(__file__).read_bytes()),
                  "new_gpu_seconds": 0}
        report["main"] = compare_pdfs(original / "ICAART2027_submission.pdf", isolated / "main.pdf", temporary, "main")
        # Establish that the delivered PDF, not just the test build, is the same.
        assert pdf_text(isolated / "main.pdf") == pdf_text(HERE / "ICAART2027_submission.pdf")
        assert aux_signature(isolated / "main.aux") == aux_signature(HERE / "build/main.aux")
        report["delivered_main_pdf_sha256"] = sha((HERE / "ICAART2027_submission.pdf").read_bytes())
        report["supplement"] = compare_pdfs(original / "ICAART2027_supplement.pdf", HERE / "ICAART2027_supplement.pdf", temporary, "supplement")
        assert aux_signature(original / "build/supplement.aux") == aux_signature(HERE / "build/supplement.aux")
        check_log(HERE / "build/main.log")
        check_log(HERE / "build/supplement.log")
    (HERE / "consolidation_verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "main_pages": report["main"]["pages"],
                      "main_rendered_pixel_differences": 0, "supplement_pages": report["supplement"]["pages"],
                      "formatted_bibliography_entries": report["bibliography_entries"], "new_gpu_seconds": 0}, indent=2))


if __name__ == "__main__":
    main()
