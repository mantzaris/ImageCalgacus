#!/usr/bin/env python3
"""Copy retained publication assets and verify headline data. Never runs models."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    publication = ROOT / "artifacts/publication_results"
    for folder in ("figures", "tables", "data"):
        (HERE / folder).mkdir(exist_ok=True)
    copies = {}
    for path in sorted((publication / "figures").glob("*.pdf")):
        copies[path] = HERE / "figures" / path.name
    for path in sorted((publication / "tables").glob("*.csv")):
        copies[path] = HERE / "data" / path.name
    for path in sorted((publication / "tables").glob("*.tex")):
        copies[path] = HERE / "tables" / ("retained_" + path.name)
    for name in ("protocol_identities.json", "accepted_paired_differences.json",
                 "gpu_timing_observations.csv", "v2_plot_observations.csv",
                 "arithmetic_endpoints.csv", "static_sequence_pairs.csv",
                 "text_filtering_limitation.json"):
        copies[publication / "data" / name] = HERE / "data" / name
    context = ROOT / "artifacts/png_context_detection_review"
    copies[context / "context_auc.pdf"] = HERE / "figures/context_auc.pdf"
    copies[context / "comparison.csv"] = HERE / "data/context_comparison.csv"
    copies[context / "analysis.json"] = HERE / "data/context_analysis.json"
    addendum = ROOT / "artifacts/png_context_detection_addendum"
    copies[addendum / "score_shifts.pdf"] = HERE / "figures/score_shifts.pdf"
    for name in ("score_shift_observations.csv", "score_shift_summary.csv"):
        copies[addendum / name] = HERE / "data" / name
    copies[ROOT / "artifacts/gpu_performance_review/timings.json"] = HERE / "data/benchmark_timings.json"
    copies[ROOT / "artifacts/v2_review/analysis.json"] = HERE / "data/v2_analysis.json"
    example_files = {
        "HI1-prompt1-fixed": ("source.png", "carrier.txt", "recovered.gray", "recovered.png"),
        "HT1-row1-fixed": ("source.txt", "carrier.png", "recovered.txt"),
    }
    for case, names in example_files.items():
        for name in names:
            copies[ROOT / "artifacts/v2_review/cases" / case / name] = HERE / "examples" / case / name
    for source, destination in copies.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    outcomes = rows(publication / "tables/table2_v2_outcomes.csv")
    assert len(outcomes) == 6 and sum(int(r["attempted"]) for r in outcomes) == 120
    assert [int(r["exact"]) for r in outcomes] == [20, 20, 0, 20, 20, 20]
    benchmark = rows(publication / "tables/table4_gpu_benchmark.csv")
    assert sum(int(r["timing_repetitions"]) for r in benchmark) == 11
    assert all(r["exact_equivalence"] == "True" for r in benchmark)
    shifts = rows(addendum / "score_shift_observations.csv")
    assert len(shifts) == 80
    provenance = {
        "preparation_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "new_gpu_seconds": 0,
        "scope": "Manuscript-only copies of retained evidence; no statistical reanalysis or model imports",
        "inputs": [{"source": str(s.relative_to(ROOT)), "manuscript_copy": str(d.relative_to(HERE)),
                    "sha256": sha(s)} for s, d in copies.items()],
        "checks": {"prospective_outcomes": 120, "exact_recovery_counts": [20,20,0,20,20,20],
                   "benchmark_comparisons": 11, "benchmark_exact_recoveries": 22,
                   "score_shift_artifacts": 80},
    }
    (HERE / "data/asset_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance["checks"], indent=2))


if __name__ == "__main__":
    main()

