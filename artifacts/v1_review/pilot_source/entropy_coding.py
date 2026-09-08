"""RankCloak entropy mechanism, adapted to approved strict H > median.
MIT attribution: mantzaris/llm-rankcloak ce853d42; see THIRD_PARTY.md.
"""
import numpy as np
from .fixed_rank import choose_rank, recover_rank, encode_bytes_to_bounded_ranks, ordinary_sample


def shannon_entropy_bits(q):
    q = np.asarray(q, dtype=np.float64)
    if q.ndim != 1 or not len(q) or not np.all(np.isfinite(q)) or np.any(q <= 0):
        raise ValueError("entropy requires positive finite eligible probabilities")
    if not np.isclose(q.sum(dtype=np.float64), 1, rtol=0, atol=1e-12):
        raise ValueError("entropy probabilities must normalize")
    return float(-np.sum(q * np.log2(q), dtype=np.float64))


def entropy_eligible(entropy, threshold):
    if not np.isfinite(entropy) or not np.isfinite(threshold) or threshold < 0:
        raise ValueError("invalid entropy/threshold")
    return bool(entropy > threshold)


def calibrate_median(entropies):
    values = np.asarray(entropies, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("ordinary development entropies required")
    threshold = float(np.quantile(values, .5, method="linear"))
    return {"threshold_bits": threshold, "threshold_hex": threshold.hex(),
            "position_count": len(values), "quantile_method": "numpy_linear",
            "rule": "strict_H_gt_threshold", "source": "ordinary_development_only"}


class RankCoder:
    def __init__(self, packet=None, threshold=None, bit_length=2336):
        if bit_length % 4:
            raise ValueError("rank target must contain complete nibbles")
        self.target = bit_length
        self.threshold = threshold
        self.ranks = encode_bytes_to_bounded_ranks(packet) if packet is not None else None
        if packet is not None and len(packet) * 8 != bit_length:
            raise ValueError("packet size mismatch")
        self.bits = ""
        self.positions = self.packet_positions = self.skipped_positions = 0
        self.zero_bit_positions = self.termination_positions = self.termination_suffix_bits = self.lookahead_zero_bits = 0

    @property
    def done(self):
        return len(self.bits) == self.target

    def prepare(self, ids, q, order):
        if self.done:
            raise ValueError("packet already complete")
        if len(order) < 16:
            raise ValueError("insufficient eligible support (<16), including gated skips")
        entropy = shannon_entropy_bits(q)
        carry = self.threshold is None or entropy_eligible(entropy, self.threshold)
        return {"ids":ids, "q":q, "order":order, "carry":carry, "entropy":entropy}

    def select(self, step, rng):
        if not step["carry"]:
            return ordinary_sample(step["ids"], step["q"], rng)
        if self.ranks is None:
            raise ValueError("receiver cannot select packet symbols")
        return choose_rank(step["order"], self.ranks[len(self.bits)//4])

    def consume(self, step, symbol):
        if symbol not in step["ids"]:
            raise ValueError("ineligible observed symbol")
        self.positions += 1
        if not step["carry"]:
            self.skipped_positions += 1
            return 0
        rank = recover_rank(step["order"], symbol)
        self.bits += format(rank-1, "04b")
        self.packet_positions += 1
        return 4

    def packet(self):
        if not self.done:
            raise ValueError("capacity/truncation: rank packet incomplete")
        return int(self.bits,2).to_bytes(self.target//8, "big")

    def diagnostics(self):
        return {name:getattr(self,name) for name in ("positions","packet_positions","skipped_positions",
                "zero_bit_positions","termination_positions","termination_suffix_bits","lookahead_zero_bits")}
