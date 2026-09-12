"""cover_rank_v1. A separate invariant-cover rank map, not V2 likelihood.
Reuses the attributed PixelCNN++ backend and exact logistic bin definition.
Receiver entry point has no source, original cover, packet or evaluator input.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import struct
import time
import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from .image_backend import ImageBackend, read_png, write_png
from .packet import PACKET_BYTES, TEXT, open_packet
from .pixel_probabilities import RGBConditionals
from .runtime import atomic_json, canonical_hash, sha256_file, source_hash

SHAPE = (256, 256, 3)
BITS = PACKET_BYTES * 8
OFFSETS = np.array([(r,g,b) for r in range(4) for g in range(4) for b in range(4)], dtype=np.uint8)
PROTOCOL = {
    "name": "cover_rank_v1", "shape": [256,256,3], "tile": [32,32],
    "coarse": "4*floor(c/4)", "context": "B+2", "tile_order": "row-major",
    "candidate_order": "lexicographic RGB", "score": "joint RGB log bin probability float64",
    "bit": "zero-based rank parity", "distance": "squared RGB; lexicographic ties",
    "packet_bytes": 292, "bit_order": "MSB first", "positions": 2336,
    "placement": "HKDF-SHA256 then HMAC-SHA256 priority; v1",
    "model_sha256": "a5ed558f6d4098ce3cbfd47658b7e3be37fae77b71a90c8a56f46a6266ff833f",
    "execution": "cuda_graph; float32 network; float64 candidate scores",
}

def read_profile(path):
    p = json.loads(Path(path).read_text())
    if set(p) != {"protocol","gpu_uuid","image"} or p["protocol"] != PROTOCOL:
        raise ValueError("unrecognized cover profile")
    if p["image"]["model_sha256"] != PROTOCOL["model_sha256"]:
        raise ValueError("unpinned image checkpoint")
    return p

def coarse(pixels):
    a = np.asarray(pixels)
    if a.shape != SHAPE or a.dtype != np.uint8:
        raise ValueError("canonical 256x256 RGB8 image required")
    return a & np.uint8(252)

def positions(base, key):
    if len(key) != 32 or not np.array_equal(coarse(base), base):
        raise ValueError("invalid placement key or coarse context")
    derived = HKDF(algorithm=hashes.SHA256(), length=32,
                   salt=hashlib.sha256(base.tobytes()).digest(),
                   info=b"ImageCalgacus/cover_rank_v1/placement\0"+bytes.fromhex(canonical_hash(PROTOCOL))).derive(key)
    priorities = [(hmac.digest(derived, b"pixel\0"+struct.pack(">I", i), "sha256"), i)
                  for i in range(256*256)]
    return np.array([i for _, i in sorted(priorities)[:BITS]], dtype=np.int64)

def candidates(base_pixel):
    b = np.asarray(base_pixel)
    if b.shape != (3,) or np.any(b % 4) or np.any(b > 252):
        raise ValueError("invalid RGB cell")
    return b.astype(np.uint8) + OFFSETS

def candidate_log_scores(parameters, colors):
    """Exact discretized joint mixture. No candidate removal or exponentiation.
    Candidate-dependent G/B means are inside each common mixture component.
    """
    obj = RGBConditionals(parameters)
    colors = np.asarray(colors, dtype=np.int64)
    if colors.ndim != 2 or colors.shape[1] != 3 or np.any((colors < 0)|(colors > 255)):
        raise ValueError("invalid colors")
    x = 2 * colors.astype(np.float64) / 255 - 1
    terms = np.broadcast_to(obj.log_weights, (len(colors),10)).copy()
    for c in range(3):
        means = np.broadcast_to(obj.means[c], terms.shape).copy()
        if c >= 1:
            means += obj.coefficients[c-1] * x[:,0,None]
        if c == 2:
            means += obj.coefficients[2] * x[:,1,None]
        inv = np.exp(-obj.log_scales[c])
        middle = (x[:,c,None]-means)*inv
        half = inv/255
        lower, upper = middle-half, middle+half
        with np.errstate(divide="ignore", under="ignore"):
            masses = lower + np.log(np.expm1(2*half)) - np.logaddexp(0,lower) - np.logaddexp(0,upper)
        masses[colors[:,c] == 0] = -np.logaddexp(0,-upper[colors[:,c] == 0])
        masses[colors[:,c] == 255] = -np.logaddexp(0,lower[colors[:,c] == 255])
        terms += masses
    scores = np.logaddexp.reduce(terms, axis=1)
    if not np.all(np.isfinite(scores)):
        raise ValueError("nonfinite candidate log score; no clipping or support reduction")
    return scores

def rank_labels(scores):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.shape != (64,) or not np.all(np.isfinite(scores)):
        raise ValueError("all 64 finite candidate log scores required")
    order = np.lexsort((np.arange(64), -scores))
    labels = np.empty(64, dtype=np.uint8)
    labels[order] = np.arange(64, dtype=np.uint8) % 2
    return labels, order

def nearest(original, colors, labels, bit):
    if bit not in (0,1) or np.sum(labels == bit) != 32:
        raise ValueError("invalid balanced bit partition")
    distance = np.sum((colors.astype(np.int32)-np.asarray(original, dtype=np.int32))**2, axis=1)
    indices = np.flatnonzero(labels == bit)
    return colors[indices[np.argmin(distance[indices])]]

def observed_index(pixel):
    r,g,b = (np.asarray(pixel, dtype=np.int64) % 4).tolist()
    return 16*r + 4*g + b

def partition_distance(labels):
    baseline = OFFSETS.sum(axis=1) % 2
    disagreement = np.sum(labels != baseline, axis=1)
    return np.minimum(disagreement,64-disagreement)/64

def reconstruct(base, selected, arm, backend=None):
    if arm == "parity":
        return np.tile((OFFSETS.sum(axis=1)%2).astype(np.uint8),(BITS,1)), {"model_calls":0}
    if arm != "model_rank" or backend is None:
        raise ValueError("model rank requires a CUDA backend")
    labels = np.empty((BITS,64),dtype=np.uint8)
    lookup = {int(p):j for j,p in enumerate(selected)}
    digests = {k:hashlib.sha256() for k in ("parameters","candidate_log_scores","rank_order")}
    canonical = base + np.uint8(2)
    for ty in range(0,256,32):
        for tx in range(0,256,32):
            output = backend.forward(canonical[ty:ty+32,tx:tx+32]).detach().cpu().numpy().copy()
            if output.shape != (1,100,32,32) or not np.all(np.isfinite(output)):
                raise ValueError("invalid tile parameter map")
            digests["parameters"].update(output.astype("<f4",copy=False).tobytes())
            for y in range(ty,ty+32):
                for x in range(tx,tx+32):
                    p = y*256+x
                    if p not in lookup:
                        continue
                    scores = candidate_log_scores(output[0,:,y-ty,x-tx], candidates(base[y,x]))
                    labels[lookup[p]], order = rank_labels(scores)
                    frame = struct.pack(">I",p)
                    digests["candidate_log_scores"].update(frame+scores.astype("<f8").tobytes())
                    digests["rank_order"].update(frame+order.astype("<i8").tobytes())
    distance = partition_distance(labels)
    return labels, {"model_calls":backend.calls,
        "digests":{k:v.hexdigest() for k,v in digests.items()},
        "partition_disagreement_up_to_swap_mean":float(distance.mean()),
        "nonidentical_partitions":int(np.count_nonzero(distance)),
        "selected_pixels":BITS}

def embed(cover, packet, selected, labels):
    if len(packet) != PACKET_BYTES:
        raise ValueError("wrong packet length")
    bits = np.unpackbits(np.frombuffer(packet,dtype=np.uint8),bitorder="big")
    result = cover.copy()
    base = coarse(cover)
    for j,p in enumerate(selected):
        y,x = divmod(int(p),256)
        result[y,x] = nearest(cover[y,x],candidates(base[y,x]),labels[j],int(bits[j]))
    if not np.array_equal(coarse(result),base) or np.max(np.abs(result.astype(int)-cover.astype(int))) > 3:
        raise AssertionError("embedding violated distortion contract")
    return result

def extract(carrier, selected, labels):
    bits = [labels[j,observed_index(carrier[divmod(int(p),256)])] for j,p in enumerate(selected)]
    return np.packbits(bits,bitorder="big").tobytes()

def conditional_oracle_error(parameters, colors):
    direct = candidate_log_scores(parameters,colors)
    reference = []
    for color in colors:
        obj = RGBConditionals(parameters)
        logp = 0.
        for value in color:
            ids,q,_ = obj.distribution()
            i = np.flatnonzero(ids == value)
            if not len(i):
                raise ValueError("oracle fixture has underflowed conditional support")
            logp += np.log(q[i[0]])
            obj.observe(int(value))
        reference.append(logp)
    return float(np.max(np.abs(direct-reference)))

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)
    for op in ("encode","decode","probe"):
        p = sub.add_parser(op)
        p.add_argument("--profile",required=True)
        p.add_argument("--report",required=True)
        if op == "probe":
            p.add_argument("--cover",required=True)
        else:
            p.add_argument("--arm",choices=("model_rank","parity"),required=True)
            p.add_argument("--key",required=True)
            p.add_argument("--output",required=True)
            if op == "encode":
                p.add_argument("--cover",required=True)
                p.add_argument("--prepared-packet",required=True)
                p.add_argument("--verification-directory")
            else:
                p.add_argument("--carrier",required=True)
    args = parser.parse_args()
    started = time.monotonic(); backend = None
    report = {"operation":args.operation,"status":"failed","source_hash":source_hash(),
              "profile_sha256":sha256_file(args.profile),"packet_complete":False,
              "carrier_complete":False,"authenticated":False}
    stage = "inputs"
    try:
        profile = read_profile(args.profile)
        if args.operation == "probe":
            base = coarse(read_png(args.cover,SHAPE))
            tiles = [(0,0),(96,96),(224,224)]
            maps = []
            stage = "reference_gpu"
            backend = ImageBackend(profile,"reference")
            for y,x in tiles:
                maps.append(backend.forward(base[y:y+32,x:x+32]+np.uint8(2)).detach().cpu().numpy().copy())
            backend.close(); backend = None
            stage = "graph_gpu"
            backend = ImageBackend(profile,"cuda_graph")
            errors = []
            for (y,x),reference in zip(tiles,maps):
                graph = backend.forward(base[y:y+32,x:x+32]+np.uint8(2)).detach().cpu().numpy().copy()
                if not np.array_equal(reference,graph):
                    raise AssertionError("reference and graph tile maps differ")
                errors.append(conditional_oracle_error(graph[0,:,16,16],candidates(base[y+16,x+16])))
            if max(errors) > 1e-10:
                raise AssertionError("joint/conditional scoring disagreement")
            report.update(status="passed",exact_reference_graph_maps=True,
                          joint_conditional_max_log_error=max(errors),tiles=tiles)
        else:
            report["arm"] = args.arm
            key = Path(args.key).read_bytes()
            pixels = read_png(args.cover if args.operation == "encode" else args.carrier,SHAPE)
            base = coarse(pixels); selected = positions(base,key)
            report["coarse_sha256"] = hashlib.sha256(base.tobytes()).hexdigest()
            if args.operation == "encode":
                packet = Path(args.prepared_packet).read_bytes()
                open_packet(packet,key,TEXT)
            stage = "model_loading"
            if args.arm == "model_rank":
                backend = ImageBackend(profile,"cuda_graph")
            phase = time.monotonic()
            stage = "rank_reconstruction"
            labels, diagnostics = reconstruct(base,selected,args.arm,backend)
            report.update(diagnostics)
            if args.operation == "encode":
                stage = "embedding"
                carrier = embed(pixels,packet,selected,labels)
                if extract(carrier,selected,labels) != packet:
                    raise AssertionError("internal packet inversion")
                write_png(args.output,carrier)
                report.update(packet_complete=True,carrier_complete=True,authenticated=True)
                if args.verification_directory:
                    folder = Path(args.verification_directory)
                    folder.mkdir(parents=True,exist_ok=False)
                    y,x = divmod(int(selected[0]),256)
                    tampered = carrier.copy()
                    bit = int(labels[0,observed_index(carrier[y,x])])
                    tampered[y,x] = nearest(carrier[y,x],candidates(base[y,x]),labels[0],1-bit)
                    write_png(folder/"changed_bit.png",tampered)
            else:
                stage = "authentication"
                packet = extract(pixels,selected,labels)
                report["packet_complete"] = True
                payload = open_packet(packet,key,TEXT)
                report["authenticated"] = True
                stage = "serialization"
                Path(args.output).parent.mkdir(parents=True,exist_ok=True)
                Path(args.output).write_bytes(payload.data)
                report["carrier_complete"] = True
            report.update(status="passed",phase_seconds=time.monotonic()-phase,
                          output_sha256=sha256_file(args.output))
    except Exception as exc:
        report.update(failure_stage=stage,failure_reason=type(exc).__name__+": "+str(exc))
    finally:
        if backend is not None:
            report["load_seconds"] = backend.load_seconds
            backend.close()
            report["gpu"] = backend.evidence
        report["total_inner_seconds"] = time.monotonic()-started
        atomic_json(args.report,report)
    return 0 if report["status"] == "passed" else 2

if __name__ == "__main__":
    raise SystemExit(main())
