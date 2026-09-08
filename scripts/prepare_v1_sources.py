"""CPU-only deterministic sources/contexts, not a carrier-generation command.

First acquisition pins hashes in --lock; every subsequent preparation requires
those exact bytes. Raw archives stay in the ignored cache. No outcome inputs.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import urllib.request
import numpy as np
from PIL import Image, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from imagecalgacus.runtime import json_write, sha256_file, canonical_hash
from imagecalgacus.sender import read_source

FASHION_REVISION = "b2617bb6d3ffa2e429640350f613e3291e10b141"
BASE = "https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/" + FASHION_REVISION + "/"
MD5 = {"train-images-idx3-ubyte.gz": "8d4fb7e6c68d591d4c3dfef9ec88bf0d",
       "train-labels-idx1-ubyte.gz": "25c81989df183df01b3e8a0aad5dffbe",
       "t10k-images-idx3-ubyte.gz": "bef4ecab320f06d8554ea6380940ec79",
       "t10k-labels-idx1-ubyte.gz": "bb300cfdad3c16e7a12a480ee83cd310"}
URLS = {name: BASE + "data/fashion/" + name for name in MD5}
URLS.update({"FASHION_LICENSE.txt": BASE + "LICENSE"})
URLS.update({"pg%d.txt" % book: "https://www.gutenberg.org/cache/epub/%d/pg%d.txt" % (book, book)
             for book in (11, 84, 1342, 1661)})
BOOKS = {11: ["Lewis Carroll", "Alice's Adventures in Wonderland"],
         84: ["Mary Wollstonecraft Shelley", "Frankenstein; or, the Modern Prometheus"],
         1342: ["Jane Austen", "Pride and Prejudice"],
         1661: ["Arthur Conan Doyle", "The Adventures of Sherlock Holmes"]}


def acquire(cache, lock_path, allow_new):
    cache.mkdir(parents=True, exist_ok=True)
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else None
    if lock is None and not allow_new:
        raise ValueError("first acquisition requires --acquire; later runs must use the frozen lock")
    records = {}
    for name, url in URLS.items():
        path = cache / name
        if not path.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "ImageCalgacus-research-source-preparation/1.2"})
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            if lock and hashlib.sha256(raw).hexdigest() != lock["sources"][name]["sha256"]:
                raise ValueError("upstream changed; restore pinned source cache: " + name)
            with path.open("xb") as stream:
                stream.write(raw)
        raw = path.read_bytes()
        if name in MD5 and hashlib.md5(raw).hexdigest() != MD5[name]:
            raise ValueError("official Fashion-MNIST MD5 mismatch: " + name)
        record = {"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if name in MD5:
            record.update({"official_md5": MD5[name], "repository_revision": FASHION_REVISION})
        if name.startswith("pg"):
            header = raw[:raw.find(b"*** START OF")].decode("utf-8-sig", errors="strict")
            record["edition_header"] = [line for line in header.splitlines() if line.startswith(("Title:", "Author:", "Release date:", "Most recently updated:", "Language:", "Credits:"))]
        if lock and lock["sources"][name] != record:
            raise ValueError("frozen source identity mismatch: " + name)
        records[name] = record
    if lock is None:
        json_write(lock_path, {"sources": records, "fashion_revision": FASHION_REVISION,
                              "fetch_date": "2026-09-08", "hash_policy": "fail on upstream changes; no silent new editions"})
    return records


def read_idx(cache, split):
    stem, count = ("train", 60000) if split == "development" else ("t10k", 10000)
    image_bytes = gzip.decompress((cache / (stem + "-images-idx3-ubyte.gz")).read_bytes())
    label_bytes = gzip.decompress((cache / (stem + "-labels-idx1-ubyte.gz")).read_bytes())
    if struct.unpack(">IIII", image_bytes[:16]) != (2051, count, 28, 28) or len(image_bytes) != 16+count*784:
        raise ValueError("invalid image IDX header/length")
    if struct.unpack(">II", label_bytes[:8]) != (2049, count) or len(label_bytes) != 8+count:
        raise ValueError("invalid label IDX header/length")
    labels = np.frombuffer(label_bytes, dtype=np.uint8, offset=8)
    if np.any(labels > 9):
        raise ValueError("invalid class label")
    return np.frombuffer(image_bytes, dtype=np.uint8, offset=16).reshape(count, 28, 28), labels


NARRATIVE_STARTS = {11: b"Alice was beginning to get very tired",
                    84: b"You will rejoice to hear that no disaster",
                    1342: b"It is a truth universally acknowledged",
                    1661: b"To Sherlock Holmes she is always"}


def text_candidates(raw, lower, upper, book=None):
    """Literal contiguous body spans; byte offsets remain offsets in downloaded file."""
    raw.decode("utf-8-sig", errors="strict")
    start = re.search(br"\*\*\* START OF .*?\*\*\*", raw)
    end = re.search(br"\*\*\* END OF .*?\*\*\*", raw)
    if not start or not end or start.end() >= end.start():
        raise ValueError("missing or invalid Gutenberg body markers")
    body_start, body_end = start.end(), end.start()
    if book is not None:
        anchor = raw.find(NARRATIVE_STARTS[book], body_start, body_end)
        if anchor < 0:
            raise ValueError("missing pinned narrative start")
        body_start = anchor
    # Paragraphs, not title/contents/credit lists: prose requires >=128 bytes,
    # >=20 ASCII words, a lowercase majority among ASCII letters, no branding.
    for match in re.finditer(br"[^\r\n]+(?:\r?\n(?!\r?\n)[^\r\n]+)*", raw[body_start:body_end]):
        paragraph = match.group()
        letters = re.findall(br"[A-Za-z]", paragraph)
        if len(paragraph) < 128 or len(re.findall(br"[A-Za-z]+", paragraph)) < 20:
            continue
        if sum(b"a" <= char <= b"z" for char in letters) < .6*len(letters):
            continue
        if any(word in paragraph.lower() for word in (b"gutenberg", b"contents", b"illustration", b"transcriber", b"copyright")):
            continue
        # First whole-word start; longest valid whole-word/codepoint ending in band.
        first = re.search(br"[A-Za-z]", paragraph)
        if first is None:
            continue
        begin = body_start + match.start() + first.start()
        endings = [begin+i for i in range(lower, upper+1)
                   if begin+i <= body_end and (begin+i == len(raw) or raw[begin+i:begin+i+1].isspace())]
        for finish in reversed(endings):
            candidate = raw[begin:finish]
            try:
                candidate.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                continue
            yield begin, finish, candidate, [body_start, body_end]
            break


def prepare(output, cache, lock_path, allow_new=False):
    if output.exists():
        raise FileExistsError("source output must be new; freeze rather than overwrite")
    sources = acquire(cache, lock_path, allow_new)
    if np.__version__ != "2.2.6" or pillow_version != "12.3.0":
        raise ValueError("source preparation requires pinned NumPy 2.2.6 and Pillow 12.3.0")
    output.mkdir(parents=True)
    for split in ("development", "heldout"):
        (output / split).mkdir()
    payloads, exclusions = [], []
    original_hashes, canonical_hashes = set(), set()

    def register(case_id, split, direction, source_path, provenance):
        payload = read_source(source_path, direction)
        digest = hashlib.sha256(payload.data).hexdigest()
        if digest in canonical_hashes:
            raise ValueError("unexpected duplicate canonical payload")
        canonical_hashes.add(digest)
        item = {"id": case_id, "split": split, "direction": direction,
                "source": str(source_path.relative_to(output)), "bytes": len(payload.data),
                "source_sha256": digest, "file_sha256": sha256_file(source_path),
                "width": payload.width, "height": payload.height, "provenance": provenance}
        if direction == "text-to-image":
            item["length_band"] = "32-64" if len(payload.data) <= 64 else "65-128"
        payloads.append(item)

    for fixture in json.loads((ROOT/"configs/v0_cases.json").read_text())["cases"]:
        original = ROOT / fixture["source"]
        target = output/"development"/original.name
        shutil.copyfile(original, target)
        register(fixture["id"], "development", fixture["direction"], target,
                 {"type": "accepted_fixture", "original_path": fixture["source"], "original_file_sha256": sha256_file(original)})
        if payloads[-1]["source_sha256"] != fixture["source_sha256"]:
            raise ValueError("fixture bytes changed")
        original_hashes.add(payloads[-1]["source_sha256"])
    for split, labels_wanted in (("development", list(range(10))+list(range(5))), ("heldout", list(range(10))*2)):
        images, labels = read_idx(cache, split)
        used = set()
        for number, label in enumerate(labels_wanted, 6 if split == "development" else 1):
            for index in np.flatnonzero(labels == label):
                index = int(index)
                if index in used:
                    continue
                original = images[index].tobytes()
                original_digest = hashlib.sha256(original).hexdigest()
                image = Image.fromarray(images[index]).resize((16, 16), Image.Resampling.BOX)
                canonical_digest = hashlib.sha256(image.tobytes()).hexdigest()
                if original_digest in original_hashes or canonical_digest in canonical_hashes:
                    exclusions.append({"split": split, "index": index, "reason": "duplicate_original_or_canonical"})
                    used.add(index)
                    continue
                case_id = ("I" if split == "development" else "HI") + str(number)
                target = output/split/(case_id+".png")
                image.save(target, format="PNG", compress_level=6)
                register(case_id, split, "image-to-text", target,
                         {"type": "fashion_mnist", "archive": ("train" if split == "development" else "t10k")+"-images-idx3-ubyte.gz",
                          "original_index": index, "class": label, "original_sha256": original_digest,
                          "original_shape": [28, 28], "mode": "L", "preprocessing": "Pillow BOX 28x28 to 16x16, no inversion/normalization"})
                original_hashes.add(original_digest); used.add(index)
                break
            else:
                raise ValueError("not enough nonduplicate Fashion-MNIST sources")
    used_spans = {book: [] for book in BOOKS}
    for split, books, bands, first_id in (("development", (11, 84), [(32,64)]*7+[(65,128)]*8, 6),
                                         ("heldout", (1342,1661), [(32,64)]*10+[(65,128)]*10, 1)):
        for offset, band in enumerate(bands):
            book = books[offset % 2]
            raw = (cache/("pg%d.txt" % book)).read_bytes()
            for begin, finish, candidate, body in text_candidates(raw, *band, book=book):
                if any(begin < b and a < finish for a,b in used_spans[book]):
                    continue
                digest = hashlib.sha256(candidate).hexdigest()
                if digest in canonical_hashes:
                    exclusions.append({"book": book, "begin": begin, "end": finish, "reason": "duplicate_literal_text"})
                    continue
                case_id = ("T" if split == "development" else "HT") + str(first_id+offset)
                target = output/split/(case_id+".txt")
                target.write_bytes(candidate)
                register(case_id, split, "text-to-image", target,
                         {"type": "gutenberg", "book": book, "author": BOOKS[book][0], "title": BOOKS[book][1],
                          "archive": "pg%d.txt" % book, "byte_start": begin, "byte_end_exclusive": finish,
                          "body_byte_bounds": body, "narrative_start": NARRATIVE_STARTS[book].decode("ascii"), "preprocessing": "unchanged literal UTF-8 span, no normalization or newline conversion"})
                used_spans[book].append((begin, finish))
                break
            else:
                raise ValueError("not enough qualifying text: no corpus substitution")
    contexts_dir = output/"contexts"; contexts_dir.mkdir()
    contexts = []
    for name, modality, original in (("prompt1.txt", "text", ROOT/"artifacts/v0_review/contexts/prompt.txt"),
                                     ("row1.rgb", "image", ROOT/"artifacts/v0_review/contexts/row.rgb")):
        shutil.copyfile(original, contexts_dir/name)
        contexts.append({"id": name.split('.')[0], "modality": modality, "path": "contexts/"+name,
                         "sha256": sha256_file(original), "construction": "unchanged accepted V0 first context"})
    prompt2 = b"Explain how a home cook prepares a simple vegetable soup. Use continuous prose."
    (contexts_dir/"prompt2.txt").write_bytes(prompt2)
    row2 = np.random.Generator(np.random.PCG64(2002)).integers(0,256,96,dtype=np.uint8).tobytes()
    (contexts_dir/"row2.rgb").write_bytes(row2)
    contexts += [{"id":"prompt2","modality":"text","path":"contexts/prompt2.txt","sha256":hashlib.sha256(prompt2).hexdigest(),"construction":"verbatim planned prompt, no newline"},
                 {"id":"row2","modality":"image","path":"contexts/row2.rgb","sha256":hashlib.sha256(row2).hexdigest(),"construction":"independent uniform RGB8 row: NumPy PCG64(2002).integers(0,256,96,dtype=uint8), raster RGB; no model/payload dependence"}]
    counts = Counter((p["split"],p["direction"]) for p in payloads)
    bands = Counter((p["split"],p.get("length_band")) for p in payloads if p["direction"]=="text-to-image")
    assert set(counts.values()) == {20} and len(counts)==4
    assert set(bands.values()) == {10} and len(bands)==4
    assert Counter(p["provenance"]["class"] for p in payloads if p["split"]=="heldout" and p["direction"]=="image-to-text") == Counter({i:2 for i in range(10)})
    terms = output/"terms"; terms.mkdir()
    shutil.copyfile(cache/"FASHION_LICENSE.txt", terms/"FASHION_LICENSE.txt")
    text11 = (cache/"pg11.txt").read_bytes()
    marker = text11.find(b"START: FULL LICENSE")
    if marker < 0: raise ValueError("cannot retain Gutenberg license")
    (terms/"GUTENBERG_LICENSE.txt").write_bytes(text11[marker:])
    result = {"schema":"qualification-sources-v1.2","sources_lock_sha256":sha256_file(lock_path),
              "numpy":np.__version__,"pillow":pillow_version,"sources":sources,"payloads":payloads,"contexts":contexts,
              "selection":"images: class round-robin, smallest unused IDX index after duplicate exclusions; text: alternating specified books, first unused prose paragraph, longest whole-word UTF-8 span in band",
              "exclusions":exclusions,"selection_uses_carrier_outcomes":False,"heldout_carrier_generation":False,
              "checks":{"20_per_split_direction":True,"10_per_text_band_split":True,"heldout_images_two_per_class":True,
                        "canonical_and_original_duplicates_excluded":True,"splits_disjoint":True,"literal_nonoverlapping_utf8":True,"existing_fixtures_byte_preserved":True}}
    json_write(output/"manifest.json", result)
    print(json.dumps({"manifest_sha256":sha256_file(output/"manifest.json"),"payloads":len(payloads),"contexts":len(contexts),"exclusions":len(exclusions)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=ROOT/".runtime/source_cache")
    parser.add_argument("--lock", type=Path, default=ROOT/"configs/v1_sources.json")
    parser.add_argument("--acquire", action="store_true")
    args = parser.parse_args()
    prepare(args.output, args.cache, args.lock, args.acquire)
