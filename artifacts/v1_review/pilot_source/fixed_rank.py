"""Radix-16 adaptation of RankCloak (MIT), ce853d42d6ba64065cb63c6bdfc0d825c62734cd.
Copyright (c) 2026 a.v.mantzaris. See THIRD_PARTY.md.
"""
import numbers
import numpy as np
from .packet import PACKET_BYTES, PACKET_RANKS


def encode_bytes_to_bounded_ranks(data):
    if type(data) is not bytes:
        raise ValueError("bytes required")
    return [rank for byte in data for rank in ((byte >> 4) + 1, (byte & 15) + 1)]


def decode_bounded_ranks_to_bytes(ranks, expected_bytes=PACKET_BYTES):
    ranks = list(ranks)
    if len(ranks) != 2 * expected_bytes:
        raise ValueError("wrong rank count")
    if any(isinstance(r, bool) or not isinstance(r, numbers.Integral) or not 1 <= r <= 16 for r in ranks):
        raise ValueError("rank outside integer alphabet 1..16")
    return bytes(((int(a) - 1) << 4) | (int(b) - 1) for a, b in zip(ranks[::2], ranks[1::2]))


def packet_ranks(packet):
    if len(packet) != PACKET_BYTES:
        raise ValueError("packet must contain exactly 292 bytes")
    return encode_bytes_to_bounded_ranks(packet)


def stable_order(scores):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1 or np.any(np.isnan(scores)) or np.any(np.isposinf(scores)):
        raise ValueError("invalid probability scores")
    ids = np.arange(scores.size, dtype=np.int64)
    return np.lexsort((ids, -scores))


def normalized(scores):
    """Log softmax in input/observable-ID order, without floors."""
    scores = np.asarray(scores, dtype=np.float64)
    stable_order(scores)  # validates
    high = np.max(scores)
    if not np.isfinite(high):
        raise ValueError("empty probability support")
    weights = np.exp(scores - high)
    total = weights.sum(dtype=np.float64)
    if not np.isfinite(total) or total <= 0:
        raise ValueError("invalid normalization")
    return weights / total


def choose_rank(ordered_ids, rank):
    if len(ordered_ids) < 16:
        raise ValueError("insufficient eligible support (<16)")
    if not isinstance(rank, numbers.Integral) or not 1 <= rank <= 16:
        raise ValueError("rank outside 1..16")
    return int(ordered_ids[int(rank) - 1])


def recover_rank(ordered_ids, symbol):
    if len(ordered_ids) < 16:
        raise ValueError("insufficient eligible support (<16)")
    found = np.flatnonzero(np.asarray(ordered_ids[:16]) == symbol)
    if found.size != 1:
        raise ValueError("observed symbol outside fixed rank alphabet")
    return int(found[0] + 1)


def ordinary_sample(ids, probabilities, rng):
    ids = np.asarray(ids)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    order = np.argsort(ids, kind="stable")
    if not len(ids) or not np.isclose(probabilities.sum(), 1, rtol=0, atol=1e-12):
        raise ValueError("invalid sampling distribution")
    cumulative = np.cumsum(probabilities[order])
    cumulative[-1] = 1.0
    return int(ids[order[np.searchsorted(cumulative, rng.random(), side="right")]])
