#!/usr/bin/env python3
"""Compile the canonical submission directly; BibTeX is only for the companion."""
import argparse
from pathlib import Path
import os
import shutil
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("all", "main", "supplement"), default="all")
    args = parser.parse_args()
    build = HERE / "build"
    build.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["TEXINPUTS"] = str(HERE / "template") + os.pathsep + str(HERE) + os.pathsep
    env["BSTINPUTS"] = str(HERE / "template") + os.pathsep
    for stem, target in (("main", "ICAART2027_submission.pdf"), ("supplement", "ICAART2027_supplement.pdf")):
        if args.target not in ("all", stem):
            continue
        command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-output-directory=build", stem + ".tex"]
        with (build / (stem + "_build.txt")).open("w") as log:
            subprocess.run(command, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            if stem == "supplement":
                subprocess.run(["bibtex", "build/" + stem], cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            subprocess.run(command, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            subprocess.run(command, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        shutil.copyfile(build / (stem + ".pdf"), HERE / target)
        print(target)


if __name__ == "__main__":
    main()
