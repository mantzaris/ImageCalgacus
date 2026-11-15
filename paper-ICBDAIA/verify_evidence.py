#!/usr/bin/env python3
"""Verify manuscript numbers using saved records only; no research modules imported.

Run from any directory with Python 3. Standard library only. This checks counts,
means, AUC point estimates, saved equality evidence and timing boundaries. It
does not regenerate confidence intervals or repeat authentication/model decoding.
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {}


def read(path):
    raw = (ROOT / path).read_bytes()
    SOURCES[path] = hashlib.sha256(raw).hexdigest()
    return raw.decode("utf-8")


def js(path):
    return json.loads(read(path))


def jl(path):
    return [json.loads(line) for line in read(path).splitlines() if line]


def table(path):
    return list(csv.DictReader(read(path).splitlines()))


def close(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-11), (a, b)


def auc(positive, negative):
    return sum((a > b) + 0.5 * (a == b) for a in positive for b in negative) / (len(positive) * len(negative))


v2 = jl("artifacts/v2_review/results.jsonl")
controls = js("artifacts/v2_review/controls.json")
manifest = js("artifacts/v2_review/manifest.json")
analysis = js("artifacts/v2_review/analysis.json")
jobs = js("artifacts/v2_review/gpu_jobs.json")
outcomes = table("artifacts/publication_results/tables/table2_v2_outcomes.csv")
assert len(v2) == len({r["case"] for r in v2}) == 120
assert {r["case"] for r in v2} == {r["id"] for r in manifest["cases"]}
assert len(controls) == len({r["id"] for r in controls}) == 40
assert len({r["payload_group"] for r in controls}) == 40
assert sum(r["exact_recovery"] for r in v2) == 100
assert sum(c["modality"] == "text" for c in controls) == 20
assert sum(c["modality"] == "image" for c in controls) == 20
groups = defaultdict(list)
for r in v2:
    groups[(r["direction"], r["method"])].append(r)
    assert r["packet_bytes"] == 292
    assert r["framing_bytes"] == 36
    if r["exact_recovery"]:
        assert r["source_sha256"] == r["recovered_sha256"]
        assert r["authenticated"] and r["packet_complete"]
    if r["direction"] == "image-to-text":
        assert r["source_bytes"] == 256
        assert not r["serialization"]["tokenization_drift"]
    else:
        assert r["channels"] == 2976 and r["pixels"] == 992

verified_cells = []
for row in outcomes:
    key = row["direction"], row["method"]
    rows = groups[key]
    assert len(rows) == int(row["attempted"]) == 20
    assert sum(r["exact_recovery"] for r in rows) == int(row["exact"])
    goodput = [8 * r["source_bytes"] / (r["tokens"] or r["channels"]) if r["exact_recovery"] else 0 for r in rows]
    close(mean(goodput), row["goodput_mean"])
    close(mean(r["encode_seconds"] for r in rows), row["encode_phase_seconds"])
    close(mean(r["decode_seconds"] for r in rows), row["decode_phase_seconds"])
    pair_times = []
    for r in rows:
        pair = [j for j in jobs if j["id"].endswith("-prospective-" + r["case"] + "-encode") or j["id"].endswith("-prospective-" + r["case"] + "-decode")]
        assert len(pair) == 2
        pair_times.append(sum(j["charged_seconds"] for j in pair))
    close(mean(pair_times), row["charged_pair_seconds"])
    verified_cells.append({"direction": key[0], "method": key[1], "attempted": len(rows), "exact": sum(r["exact_recovery"] for r in rows), "mean_goodput": mean(goodput), "mean_charged_pair_seconds": mean(pair_times)})

audits = js("artifacts/v2_review/arithmetic_audits.json")
assert len(audits) == 40 and all(all(a["checks"].values()) for a in audits)
text_audits = [a for a in audits if a["case"].startswith("HI")]
assert all(a["positions"] == 2048 and not a["termination_reached"] for a in text_audits)
assert min(a["bits_recovered"] for a in text_audits) == 581
assert max(a["bits_recovered"] for a in text_audits) == 2216
close(mean(a["bits_recovered"] for a in text_audits), 1456.85)
assert all(r["failure_stage"] == "capacity" and r["exact_goodput_bits_per_symbol"] == 0 for r in groups[("image-to-text", "arithmetic")])

observations = table("artifacts/publication_results/data/detectability_observations.csv")
detector_table = table("artifacts/publication_results/tables/table3_detectability.csv")
verified_aucs = []
for row in detector_table:
    obs = [o for o in observations if all(o[k] == row[k] for k in ("direction", "method", "score"))]
    assert len(obs) == len({o["trace_id"] for o in obs}) == 20
    value = auc([float(o["stego"]) for o in obs], [float(o["ordinary"]) for o in obs])
    close(value, row["auc"])
    verified_aucs.append({k: row[k] for k in ("direction", "method", "score", "auc")})

context = jl("artifacts/png_context_detection_review/results.jsonl")
context_table = table("artifacts/png_context_detection_review/comparison.csv")
assert len(context) == len({r["artifact_id"] for r in context}) == 80
assert all(r["scorable"] and r["scored_channels"] == 2976 for r in context)
assert len({r["payload_group"] for r in context}) == 20
neg = [r for r in context if r["kind"] == "control"]
assert len(neg) == 20
for row in context_table:
    pos = [r for r in context if r["kind"] == "stego" and r["method"] == row["method"]]
    assert len(pos) == 20
    for condition, column in [("correct_scores", "correct_auc"), ("mismatch_scores", "mismatch_auc")]:
        value = auc([r[condition][row["score"]] for r in pos], [r[condition][row["score"]] for r in neg])
        close(value, row[column])
    close(float(row["mismatch_auc"]) - float(row["correct_auc"]), row["difference"])

gpu = jl("artifacts/gpu_performance_review/results.jsonl")
timings = js("artifacts/gpu_performance_review/timings.json")
assert len(gpu) == 22 and all(r["evaluation"]["exact_recovery"] for r in gpu)
by_comparison = defaultdict(dict)
for r in gpu:
    by_comparison[r["case"]["id"].rsplit("-", 1)[0]][r["mode"]] = r
assert len(by_comparison) == 11
for pair in by_comparison.values():
    a, b = pair["reference"], pair["cuda_graph"]
    assert a["distribution_digest"] == b["distribution_digest"]
    assert a["evaluation"]["carrier_sha256"] == b["evaluation"]["carrier_sha256"]
    assert a["evaluation"]["recovered_sha256"] == b["evaluation"]["recovered_sha256"]
gpu_means = {}
for mode in ("reference", "cuda_graph"):
    rows = [r for r in gpu if r["mode"] == mode and r["case"]["method"] == "fixed"]
    assert len(rows) == 9 and len({r["case"]["payload_id"] for r in rows}) == 3
    gpu_means[mode] = mean(r["charged_pair_seconds"] for r in rows)
    close(gpu_means[mode], timings["fixed_aggregate"][mode]["mean_charged_pair_seconds"])
    close(sum(r["case"]["bytes"] for r in rows) / sum(r["charged_pair_seconds"] for r in rows), timings["fixed_aggregate"][mode]["exact_payload_bytes_per_second"])
speedup = gpu_means["reference"] / gpu_means["cuda_graph"]
close(speedup, timings["fixed_aggregate"]["pair_speedup"])

photo = jl("artifacts/cover_rank_v1_review/results.jsonl")
photo_table = table("artifacts/cover_rank_v1_review/summary.csv")
assert len(photo) == 52 and all(r["exact_recovery"] and r["authenticated"] for r in photo)
assert len({r["group"] for r in photo if r["split"] == "heldout"}) == 20
for row in photo_table:
    rows = [r for r in photo if r["split"] == row["split"] and r["arm"] == row["arm"]]
    assert len(rows) == int(row["attempted"]) == int(row["exact"])
    for metric in ("psnr_db", "ssim", "changed_pixel_fraction", "changed_channel_fraction", "png_bytes", "source_bytes", "sender_seconds", "receiver_seconds", "pair_seconds"):
        close(mean(r[metric] for r in rows), row["mean_" + metric])
    assert max(r["max_channel_change"] for r in rows) == int(row["maximum_channel_change"])
report = {
    "scope": "Saved-record arithmetic/identity verification only; no model inference, new experiment, timing benchmark, authentication replay, interval refit or detector training.",
    "status": "passed",
    "v2_outcomes": 120, "v2_independent_controls": 40,
    "v2_cells": verified_cells, "v2_auc_point_estimates": verified_aucs,
    "arithmetic_text_prefix": {"min": 581, "max": 2216, "mean": 1456.85},
    "png_context_artifacts": 80, "png_context_independent_groups": 20,
    "gpu_comparisons": 11, "gpu_exact_recoveries": 22,
    "gpu_fixed_pairs_per_mode": 9, "gpu_fixed_charged_pair_means": gpu_means,
    "gpu_fixed_pooled_speedup": speedup,
    "photo_heldout_groups": 20, "photo_exact_heldout_recoveries_per_arm": 20,
    "uncertainty": "Read and retained accepted analysis.json confidence intervals; no resampling performed.",
    "source_sha256": SOURCES,
}
(HERE / "evidence_audit.json").write_text(json.dumps(report, indent=2) + "\n")
print("Saved-evidence checks passed; wrote paper-ICBDAIA/evidence_audit.json")
