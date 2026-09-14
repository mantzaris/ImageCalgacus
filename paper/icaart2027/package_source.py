#!/usr/bin/env python3
"""Package only required sources, then compile the ZIP in an isolated directory."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_text(path):
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def main():
    files = [HERE / name for name in ("main.tex", "supplement.tex", "preamble.tex", "references.bib", "build.py", "BUILD_README.md", "ASSET_NOTICES.md")]
    files += [HERE / "sections/cover_supplement.tex"]  # Companion-only content.
    # Only PDFs actually included by the two manuscripts. Old accepted copies
    # remain in the repository, but are not duplicate compilation dependencies.
    for name in ("figure1_transport_submission", "cover_transport_submission",
                 "figure2_recovery_rate", "context_auc", "figure3_detectability",
                 "figureS1_arithmetic_capacity", "figureS2_text_consistency",
                 "score_shifts", "figure4_gpu_performance", "cover_examples"):
        files.append(HERE / "figures" / (name + ".pdf"))
    files += [HERE / "figures/method_diagram.tex"]
    for name in ("context_comparison", "score_shifts", "supp_table2_v2_outcomes", "supp_table3_detectability", "supp_tableS1_overhead", "supp_table4_gpu_benchmark"):
        files.append(HERE / "tables" / (name + ".tex"))
    for name in ("article.cls", "SCITEPRESS.sty", "apalike.sty", "apalike.bst", "provenance.json"):
        files.append(HERE / "template" / name)
    # Exact official copies beside main.tex support ordinary editor/pdfLaTeX use.
    for name in ("article.cls", "SCITEPRESS.sty", "apalike.sty", "apalike.bst"):
        assert (HERE / name).read_bytes() == (HERE / "template" / name).read_bytes(), name
        files.append(HERE / name)
    names = [str(path.relative_to(HERE)) for path in files]
    assert len(names) == len(set(names))
    for path in files:
        assert path.is_file() and not path.is_symlink()
        if path.suffix in (".tex", ".bib", ".py", ".md", ".json"):
            text = path.read_text()
            for forbidden in ("/home/meow", "GPU-10d1f16f", "github.com/mantzaris/ImageCalgacus"):
                assert forbidden not in text, (path, forbidden)
    archive = HERE / "ICAART2027_source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for path in sorted(files):
            out.write(path, str(path.relative_to(HERE)))
    # A fresh filesystem location with only the allowlisted ZIP contents.
    # Exercise ordinary pdfLaTeX, without the wrapper's custom search paths.
    with tempfile.TemporaryDirectory(prefix="imagecalgacus-source-compile-") as temporary:
        target = Path(temporary)
        with zipfile.ZipFile(archive) as zipped:
            assert sorted(zipped.namelist()) == sorted(names)
            assert all((target / name).resolve().is_relative_to(target) for name in names)
            zipped.extractall(target)
        env = os.environ.copy()
        for variable in ("TEXINPUTS", "BSTINPUTS", "BIBINPUTS"):
            env.pop(variable, None)
        outputs = {}
        for stem, name in (("main", "ICAART2027_submission.pdf"), ("supplement", "ICAART2027_supplement.pdf")):
            command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                       "-file-line-error", "-recorder", stem + ".tex"]
            with (target / (stem + "_direct_build.txt")).open("w") as output:
                subprocess.run(command, cwd=target, env=env, stdout=output, stderr=subprocess.STDOUT, check=True)
                if stem == "supplement":
                    subprocess.run(["bibtex", stem], cwd=target, env=env, stdout=output, stderr=subprocess.STDOUT, check=True)
                for _ in range(2):
                    subprocess.run(command, cwd=target, env=env, stdout=output, stderr=subprocess.STDOUT, check=True)
            isolated = target / (stem + ".pdf")
            assert extract_text(isolated) == extract_text(HERE / name), name
            log = (target / (stem + ".log")).read_text()
            assert "Overfull" not in log and "undefined" not in log.lower()
            inputs = {(target / line[6:]).resolve() for line in
                      (target / (stem + ".fls")).read_text().splitlines()
                      if line.startswith("INPUT ")}
            for dependency in ("article.cls", "SCITEPRESS.sty", "apalike.sty"):
                assert (target / dependency).resolve() in inputs, dependency
            info = subprocess.check_output(["pdfinfo", str(isolated)], text=True)
            outputs[name] = {"pages": int(re.search(r"Pages:\s*(\d+)", info)[1]), "isolated_build_text_identical": True,
                             "direct_pdflatex_without_custom_search_paths": True,
                             "official_files_loaded_from_manuscript_directory": True}
    # Packaging remains usable after future direct manuscript edits. The
    # historical pixel-equivalence check is separate, not a content reset gate.
    main_source = (HERE / "main.tex").read_text()
    assert not re.search(r"\\(?:input|include|subfile|bibliography|bibliographystyle)\s*\{", main_source)
    assert r"\begin{thebibliography}" in main_source
    report = {"passed": True, "archive": archive.name, "archive_sha256": sha(archive),
              "canonical_main": "main.tex", "main_requires_bibtex_or_fragments": False,
              "main_only_verification": "consolidation_verification.json",
              "archive_bytes": archive.stat().st_size, "files": {name: sha(HERE / name) for name in sorted(names)},
              "isolated_compilation": outputs, "private_material_included": False, "new_gpu_seconds": 0,
              "scope": "Allowlisted compile-only sources, no repository/private runtime dependency; standard installed TeX packages required"}
    (HERE / "source_archive_verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
