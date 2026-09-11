#!/usr/bin/env python3
"""Focused manuscript audit of retained numbers, PDFs and unchanged evidence.

Run from the repository with its existing CPU analysis environment. No model is
loaded. This is not a new experiment or private-key decoding verification.
"""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def same(a, b):
    # Only aggregate rounding comparisons. Model stream equality is checked
    # exactly by the existing benchmark verifier, without this tolerance.
    assert math.isclose(float(a), float(b), abs_tol=1e-12, rel_tol=1e-12), (a, b)


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pdf_text(path):
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def nonspace(text):
    return len(re.sub(r"\s", "", text))


def main():
    checks = {}
    baseline = read(HERE / "preservation_baseline.json")
    for path, digest in baseline["public_files"].items():
        assert sha(ROOT / path) == digest, path
    checks["unchanged_accepted_files"] = len(baseline["public_files"])
    available_ledgers = [ROOT / p for p in baseline["ledgers"]]
    if all(p.exists() for p in available_ledgers):
        charges = {}
        for path, digest in baseline["ledgers"].items():
            assert sha(ROOT / path) == digest, path
            events = [json.loads(line) for line in (ROOT / path).read_text().splitlines()]
            finished = [e for e in events if e["event"] == "finished"]
            assert len(finished) == len({e["id"] for e in finished})
            assert {e["id"] for e in finished} == {e["id"] for e in events if e["event"] == "started"}
            charges[path] = sum(e["elapsed_seconds"] for e in finished)
            assert charges[path] > 0
            same(charges[path], finished[-1]["cumulative_seconds"])
        checks["unchanged_ledgers"] = len(charges)
        checks["historical_charged_seconds"] = charges
        checks["cumulative_gpu_seconds"] = sum(charges.values())
    else:
        checks["private_ledger_check"] = "not run; execution ledgers unavailable"
    checks["new_gpu_seconds"] = 0
    for item in read(HERE / "data/asset_provenance.json")["inputs"]:
        assert sha(ROOT / item["source"]) == sha(HERE / item["manuscript_copy"]) == item["sha256"]
    for name, digest in read(HERE / "template/provenance.json")["unmodified_files"].items():
        assert sha(HERE / "template" / name) == digest
    checks["template_and_copied_assets_unchanged"] = True

    analysis = read(ROOT / "artifacts/v2_review/analysis.json")
    cells = {(r["direction"], r["method"]): r for r in analysis["cells"]}
    outcomes = rows(HERE / "data/table2_v2_outcomes.csv")
    for r in outcomes:
        c = cells[r["direction"], r["method"]]
        assert int(r["exact"]) == c["exact_recovery_count"]
        assert int(r["attempted"]) == c["n_attempted"] == 20
        same(r["recovery_ci_low"], c["recovery_95_interval"][0])
        same(r["recovery_ci_high"], c["recovery_95_interval"][1])
        for col, metric in (("goodput_mean", "exact_goodput_bits_per_symbol"),
                            ("encode_phase_seconds", "encode_seconds"),
                            ("decode_phase_seconds", "decode_seconds"),
                            ("charged_pair_seconds", "charged_pair_seconds")):
            same(r[col], c["metrics"][metric]["mean"])
        for col, i in (("goodput_ci_low", 0), ("goodput_ci_high", 1)):
            same(r[col], c["metrics"]["exact_goodput_bits_per_symbol"]["grouped_95_interval"][i])
    checks["six_recovery_cells"] = [int(r["exact"]) for r in outcomes]
    assert checks["six_recovery_cells"] == [20, 20, 0, 20, 20, 20]
    detectors = {(r["direction"], r["method"], r["score"]): r for r in analysis["detectability"]}
    for r in rows(HERE / "data/table3_detectability.csv"):
        c = detectors[r["direction"], r["method"], r["score"]]
        same(r["auc"], c["auc"])
        same(r["auc_ci_low"], c["grouped_95_interval"][0])
        same(r["auc_ci_high"], c["grouped_95_interval"][1])
    context = read(ROOT / "artifacts/png_context_detection_review/analysis.json")
    context_cells = {(r["method"], r["score"]): r for r in context["cells"]}
    for r in rows(HERE / "data/context_comparison.csv"):
        c = context_cells[r["method"], r["score"]]
        for field in ("correct_auc", "mismatch_auc", "difference"):
            same(r[field], c[field])
        for prefix in ("correct", "mismatch", "difference"):
            same(r[prefix + "_ci_low"], c[prefix + "_95_interval"][0])
            same(r[prefix + "_ci_high"], c[prefix + "_95_interval"][1])
    checks["accepted_auc_cells_checked"] = 18

    shifts = rows(HERE / "data/score_shift_observations.csv")
    assert len(shifts) == len({r["artifact_id"] for r in shifts}) == 80
    assert len({r["payload_group"] for r in shifts}) == 20
    controls = {r["artifact_id"]: r for r in shifts if r["category"] == "ordinary"}
    for r in shifts:
        same(r["score_change"], float(r["row2_mean_surprisal"]) - float(r["row1_mean_surprisal"]))
        assert r["units"] == "bits per delivered RGB channel value"
        assert controls[r["matched_control_id"]]["payload_group"] == r["payload_group"]
    for summary in rows(HERE / "data/score_shift_summary.csv"):
        selected = [r for r in shifts if r["category"] == summary["category"]]
        assert len(selected) == int(summary["n_artifacts"]) == 20
        for col, field in (("mean_row1", "row1_mean_surprisal"), ("mean_row2", "row2_mean_surprisal"),
                           ("mean_score_change", "score_change")):
            same(summary[col], statistics.mean(float(r[field]) for r in selected))
        same(summary["median_score_change"], statistics.median(float(r["score_change"]) for r in selected))
    checks["fixed_control_gaps"] = {row: statistics.mean(
        float(r[row + "_mean_surprisal"]) - float(controls[r["matched_control_id"]][row + "_mean_surprisal"])
        for r in shifts if r["category"] == "fixed") for row in ("row1", "row2")}
    checks["score_shift_artifacts"] = 80

    timing = read(ROOT / "artifacts/gpu_performance_review/timings.json")
    assert len(timing["individual"]) == 22
    for mode in ("reference", "cuda_graph"):
        selected = [r for r in timing["individual"] if r["method"] == "fixed" and r["mode"] == mode]
        assert len(selected) == 9 and all(r["exact_recovery"] and r["equivalent"] for r in selected)
        aggregate = timing["fixed_aggregate"][mode]
        for field in ("charged_encode_seconds", "charged_decode_seconds", "charged_pair_seconds"):
            same(aggregate["mean_" + field], statistics.mean(r[field] for r in selected))
        same(aggregate["exact_payload_bytes_per_second"], sum(r["payload_bytes"] for r in selected) / sum(r["charged_pair_seconds"] for r in selected))
    same(timing["fixed_aggregate"]["pair_speedup"], timing["fixed_aggregate"]["reference"]["mean_charged_pair_seconds"] / timing["fixed_aggregate"]["cuda_graph"]["mean_charged_pair_seconds"])
    checks["fixed_gpu_headline"] = timing["fixed_aggregate"]

    # Existing public verifiers, with stdout and any verifier report redirected
    # into this new manuscript-only record, never an accepted review packet.
    with contextlib.redirect_stdout(io.StringIO()):
        checks["public_v2"] = module("collect_v2_review").verify_public(ROOT / "artifacts/v2_review")
        checks["public_benchmark"] = module("collect_gpu_performance").verify_public(ROOT / "artifacts/gpu_performance_review")
        checks["public_qualification_exit"] = module("finalize_v1_qualification").verify_public(ROOT / "artifacts/v1_qualification_review")
        observer = module("analyze_png_context_detection")
        reports = []
        observer.atomic_json = lambda path, result, **kwargs: reports.append(result)
        observer.verify()
        checks["public_context"] = reports[-1]
    assert checks["public_qualification_exit"] == 0
    assert checks["public_v2"]["study_allocation_complete"]
    assert checks["public_benchmark"]["exact_recoveries"] == 22
    assert checks["public_context"]["passed"]

    pdfs = {}
    for stem, name in (("main", "ICAART2027_submission.pdf"), ("supplement", "ICAART2027_supplement.pdf")):
        path = HERE / name
        extracted = pdf_text(path)
        info = subprocess.check_output(["pdfinfo", str(path)], text=True)
        assert not re.search(r"^Author:[ \t]*[^\s]", info, re.MULTILINE)
        for forbidden in ("/home/meow", "GPU-10d1f16f", "github.com/mantzaris/ImageCalgacus", "@gmail", "@ucf"):
            assert forbidden not in extracted + info, forbidden
        log = (HERE / "build" / (stem + ".log")).read_text()
        assert "Overfull" not in log and "undefined" not in log.lower()
        pages = int(re.search(r"Pages:\s*(\d+)", info)[1])
        pdfs[stem] = {"file": name, "sha256": sha(path), "pages": pages, "extracted_nonwhitespace_characters": nonspace(extracted), "empty_author_metadata": True}
    figures = ("figure2_recovery_rate.pdf", "context_auc.pdf", "figure4_gpu_performance.pdf")
    extra = sum(nonspace(pdf_text(HERE / "figures" / name)) for name in figures)
    # All figure text is vector and is already present in extracted main text.
    # Double-count it anyway, count all method-diagram source including syntax,
    # then add 1,000 characters for possible ligature/math extraction loss.
    diagram_allowance = nonspace((HERE / "figures/method_diagram.tex").read_text())
    conservative = pdfs["main"]["extracted_nonwhitespace_characters"] + extra + diagram_allowance + 1000
    assert 10000 <= conservative <= 50000
    abstract = re.search(r"\\abstract\{(.*?)\}\s*\\onecolumn", (HERE / "main.tex").read_text(), re.S)[1]
    abstract_words = len(abstract.split())
    assert 70 <= abstract_words <= 200
    checks["pdfs"] = pdfs
    checks["character_count"] = {"abstract_words_whitespace_method": abstract_words,
        "main_extracted_including_figures_tables_references": pdfs["main"]["extracted_nonwhitespace_characters"],
        "duplicated_external_figure_text_allowance": extra, "whole_diagram_source_allowance": diagram_allowance,
        "additional_extraction_allowance": 1000, "conservative_main_nonwhitespace_estimate": conservative,
        "official_regular_paper_range": [10000, 50000],
        "caveat": "Conservative estimate, not an official portal count. No official graph-to-character conversion was specified. All visible figure text was also visually inspected."}
    for category in ("public_files", "ledgers"):
        for path, digest in baseline[category].items():
            if (ROOT / path).exists():
                assert sha(ROOT / path) == digest, path
    checks["passed"] = True
    checks["source_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    checks["verification_script_sha256"] = sha(Path(__file__))
    (HERE / "verification.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps({key: checks[key] for key in ("passed", "unchanged_accepted_files", "new_gpu_seconds", "six_recovery_cells", "character_count")}, indent=2))


if __name__ == "__main__":
    main()


