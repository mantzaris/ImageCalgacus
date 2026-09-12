#!/usr/bin/env python3
"""Two submission-only figure variants from unchanged retained artifacts.
No model execution, key access, statistical refitting or accepted-export writes.
Layout and rendering reuse the established publication builder.
"""
import hashlib
import json
from pathlib import Path
import sys
import textwrap

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_publication_results as publication
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

INPUTS = {}


def read_bytes(path):
    data = path.read_bytes()
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return data


def read_json(path):
    return json.loads(read_bytes(path))


def pixels(path):
    read_bytes(path)
    with Image.open(path) as image:
        return np.asarray(image).copy()


def original_directions():
    v2 = ROOT / "artifacts/v2_review"
    manifest = read_json(v2 / "manifest.json")
    rows = {r["case"]: r for r in map(json.loads, read_bytes(v2 / "results.jsonl").decode().splitlines())}
    examples = [next(c for c in manifest["cases"] if c["direction"] == direction and c["method"] == "fixed")
                for direction in publication.DIRECTIONS]
    first_image, first_text = (v2 / "cases" / c["id"] for c in examples)
    source_image = pixels(first_image / "source.png")
    recovered_image = pixels(first_image / "recovered.png")
    carrier_image = pixels(first_text / "carrier.png")
    message = read_bytes(first_text / "source.txt")
    assert message == read_bytes(first_text / "recovered.txt")
    carrier_bytes = read_bytes(first_image / "carrier.txt")
    excerpt_bytes = read_bytes(ROOT / "artifacts/publication_results/data/figure1_carrier_excerpt.txt")
    assert carrier_bytes.startswith(excerpt_bytes)
    assert source_image.shape == (16, 16) and carrier_image.shape == (31, 32, 3)
    assert np.array_equal(source_image, recovered_image)
    assert source_image.tobytes() == read_bytes(first_image / "recovered.gray")
    row = rows[examples[0]["id"]]
    assert len(carrier_bytes) == row["carrier_bytes"]
    excerpt = excerpt_bytes.decode("utf-8", errors="strict")

    # Adapt the original publication Figure 1 layout, not the experimental data.
    fig = plt.figure(figsize=(7.2, 5.7))
    fig.text(.035, .956, "A  Image → saved UTF-8 → canonical image", weight="bold", size=11)
    upper = fig.add_gridspec(1, 3, left=.04, right=.96, bottom=.52, top=.88,
                            width_ratios=[1, 2.4, 1], wspace=.25)
    for col, data, label in ((0, source_image, "Source"), (2, recovered_image, "Recovery")):
        ax = fig.add_subplot(upper[0, col])
        ax.imshow(data, cmap="gray", vmin=0, vmax=255, interpolation="nearest", aspect="equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_axis_off()
        ax.set_title(label, fontsize=10, pad=8)
        ax.text(.5, -.09, "16 × 16 grayscale\n256 canonical bytes", transform=ax.transAxes,
                ha="center", va="top", fontsize=8)
    ax = fig.add_subplot(upper[0, 1])
    ax.set_axis_off()
    ax.set_title("Delivered text (verbatim excerpt)", fontsize=10, pad=8)
    wrapped = "\n".join(textwrap.fill(p, width=46, replace_whitespace=False, drop_whitespace=False)
                        for p in excerpt.split("\n"))
    ax.text(0, .98, wrapped, ha="left", va="top", fontsize=9, linespacing=1.38)
    ax.text(0, -.015, f"Displayed excerpt ends here.\nComplete carrier: {row['delivered_tokens']} tokens,\n"
            f"{len(carrier_bytes):,} UTF-8 bytes.", fontsize=8, va="top")
    fig.text(.035, .425, "B  Literal text → saved PNG → literal text", weight="bold", size=11)
    lower = fig.add_gridspec(1, 3, left=.055, right=.96, bottom=.12, top=.35,
                            width_ratios=[1.3, 1, 1.3], wspace=.35)
    for col, label in ((0, "Source text"), (2, "Recovered text")):
        ax = fig.add_subplot(lower[0, col])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_axis_off()
        ax.set_title(label, fontsize=10, pad=7)
        ax.text(0, .84, textwrap.fill(message.decode("utf-8"), width=24), va="top", fontsize=10, linespacing=1.4)
        ax.text(0, .06, f"{len(message)} literal UTF-8 bytes", va="bottom", fontsize=8)
    ax = fig.add_subplot(lower[0, 1])
    ax.imshow(carrier_image, interpolation="nearest", aspect="equal")
    ax.set_axis_off()
    ax.set_title("Delivered PNG", fontsize=10, pad=8)
    ax.text(.5, -.1, "32 × 31 RGB8\n992 pixels · 2,976 channels", ha="center",
            va="top", transform=ax.transAxes, fontsize=8)
    fig.text(.5, .025, "Fixed rank · first frozen case in each direction · both sources recovered byte-for-byte",
             ha="center", fontsize=8.5)
    publication.save_figure(fig, "figure1_transport_submission", "Actual bidirectional transport",
                            "", "", [])
    return {"cases": [c["id"] for c in examples], "selection": "first manifest-ordered fixed case per direction",
            "carrier_bytes": len(carrier_bytes), "delivered_tokens": row["delivered_tokens"],
            "excerpt_bytes": len(excerpt_bytes), "literal_prefix_verified": True,
            "source_and_recovered_bytes_equal": True}


def photograph():
    review = ROOT / "artifacts/cover_rank_v1_review"
    manifest = read_json(review / "manifest.json")
    group = next(g for g in manifest["groups"] if g["split"] == "heldout")
    assert group["bsds_id"] == "2018"  # Previously used main example, not a new selection.
    cover_path = review / group["cover"]
    outcome = review / "outcomes" / (group["id"] + "-model_rank")
    cover, stego = pixels(cover_path), pixels(outcome / "carrier.png")
    source = read_bytes(review / group["source"])
    assert source == read_bytes(outcome / "recovered.txt")
    result = read_json(outcome / "result.json")
    assert result["exact_recovery"] and result["authenticated"]
    assert hashlib.sha256(cover_path.read_bytes()).hexdigest() == group["cover_sha256"]
    assert hashlib.sha256((outcome / "carrier.png").read_bytes()).hexdigest() == result["carrier_sha256"]
    assert cover.dtype == stego.dtype == np.uint8 and cover.shape == stego.shape == (256, 256, 3)
    delta = np.abs(stego.astype(np.int16) - cover.astype(np.int16))
    assert np.max(delta) <= 3 and np.array_equal(cover // 4, stego // 4)
    difference = (32 * delta).astype(np.uint8)  # No clipping occurs, since 32*3 < 256.
    fig = plt.figure(figsize=(7.2, 3.6))
    grid = fig.add_gridspec(1, 3, left=.035, right=.965, bottom=.31, top=.89, wspace=.07)
    for index, (data, title) in enumerate(zip(
            (cover, stego, difference),
            ("A  Canonical cover", "B  Delivered stego", "C  Absolute difference ×32"))):
        ax = fig.add_subplot(grid[0, index])
        ax.imshow(data, interpolation="nearest", aspect="equal", vmin=0, vmax=255)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_axis_off()
        ax.set_title(title, fontsize=10, pad=9, fontweight="bold")
        if index == 2:
            ax.text(.5, -.055, "Analytical visualization", ha="center", va="top",
                    transform=ax.transAxes, fontsize=8)
    fig.text(.5, .20, f"Complete source = recovered message ({len(source)} UTF-8 bytes)",
             ha="center", fontsize=9, fontweight="bold")
    fig.text(.5, .135, source.decode("utf-8", errors="strict"), ha="center", fontsize=9)
    fig.text(.5, .055, "BSDS 2018 · 256 × 256 RGB8 · authenticated saved-PNG recovery in a fresh GPU process",
             ha="center", fontsize=8)
    publication.save_figure(fig, "cover_transport_submission", "Photograph transport and exact recovery",
                            "", "", [])
    return {"case": group["id"], "arm": "model_rank", "source_bytes": len(source),
            "selection": "same first frozen held-out example used before finalization",
            "source_recovered_equal": True, "coarse_invariant": True,
            "maximum_channel_change": int(delta.max()),
            "difference": "32 * abs(stego.astype(int16) - cover.astype(int16)), per RGB channel",
            "display": "equal image axes, nearest-neighbor, no modifications to source or carrier files"}


def main():
    read_bytes(ROOT / "scripts/build_publication_results.py")
    publication.OUT = HERE  # Only manuscript variants, never accepted review outputs.
    publication.style()
    plt.rcParams["svg.hashsalt"] = "icaart2027-single-pdf"
    (HERE / "figures").mkdir(exist_ok=True)
    evidence = {"original": original_directions(), "photograph": photograph(),
                "new_gpu_seconds": 0, "inputs": INPUTS,
                "plotting_versions": {"matplotlib": plt.matplotlib.__version__,
                                      "numpy": np.__version__, "Pillow": Image.__version__},
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    # Matplotlib emits trailing spaces in SVG path lines. Normalize only that
    # generated XML whitespace; geometry, text and embedded image bytes are unchanged.
    for stem in ("figure1_transport_submission", "cover_transport_submission"):
        svg = HERE / "figures" / (stem + ".svg")
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    evidence["outputs"] = {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for stem in ("figure1_transport_submission", "cover_transport_submission")
                           for p in sorted((HERE / "figures").glob(stem + ".*"))}
    (HERE / "data/figure_variants.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({k: v for k, v in evidence.items() if k not in ("inputs", "outputs")}, indent=2))


if __name__ == "__main__":
    main()
