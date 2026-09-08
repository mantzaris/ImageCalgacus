"""Independent finite-precision arithmetic steganography with approved framing A1.
Ziegler, Deng & Rush (2019), https://aclanthology.org/D19-1115/.
No source is copied from the unlicensed NeuralSteganography implementation.
Half-open integer bounds; no EOF, endpoint dump, E3 adaptation or tail flushing.
"""
import numpy as np
from .entropy_coding import shannon_entropy_bits

PRECISION = 32


def partition(ids, q, order, width):
    """A1: probability-order truncation, nearest/even widths, residual to first."""
    ids, q, order = np.asarray(ids), np.asarray(q, dtype=np.float64), np.asarray(order)
    shannon_entropy_bits(q)  # validates positive normalized eligible q
    if width < 1 or width > 1 << PRECISION or len(ids) != len(q):
        raise ValueError("invalid arithmetic width/distribution")
    if len(set(map(int,ids))) != len(ids) or set(map(int,order)) != set(map(int,ids)):
        raise ValueError("arithmetic symbol ordering must be a permutation")
    indexes = {int(v):i for i,v in enumerate(ids)}
    probabilities = np.asarray([q[indexes[int(v)]] for v in order], dtype=np.float64)
    minimum = min(2, len(ids), width)
    retained = (probabilities >= 1.0 / width) | (np.arange(len(ids)) < minimum)
    symbols, probabilities = order[retained], probabilities[retained]
    mass_before_rounding = float(probabilities.sum(dtype=np.float64))
    sizes = np.rint(probabilities / mass_before_rounding * width).astype(np.int64)
    over = np.flatnonzero(np.cumsum(sizes, dtype=np.int64) > width)
    if len(over):
        symbols, probabilities, sizes = symbols[:over[0]], probabilities[:over[0]], sizes[:over[0]]
    if not len(sizes):
        raise ValueError("arithmetic partition empty after overflow removal")
    sizes[0] += width - int(sizes.sum(dtype=np.int64))
    keep = sizes > 0
    symbols, probabilities, sizes = symbols[keep], probabilities[keep], sizes[keep]
    if not len(sizes) or int(sizes.sum()) != width or np.any(sizes <= 0):
        raise ValueError("invalid arithmetic partition")
    cdf = np.concatenate((np.array([0],dtype=np.int64), np.cumsum(sizes,dtype=np.int64)))
    retained_mass = float(probabilities.sum(dtype=np.float64))
    effective = sizes.astype(np.float64) / width
    diagnostic = {"retained_mass":retained_mass, "removed_mass":max(0.0,1-retained_mass),
                  "quantization_l1":float(np.abs(effective-probabilities).sum()) + max(0.0,1-retained_mass),
                  "support":len(symbols)}
    return symbols.astype(np.int64), cdf, diagnostic


def narrow_and_emit(lower, upper, offset_low, offset_high, precision=32):
    bound = 1 << precision
    lo, hi = lower + int(offset_low), lower + int(offset_high)
    if not (0 <= lower <= lo < hi <= upper <= bound):
        raise ValueError("invalid half-open interval")
    count = precision - (lo ^ (hi-1)).bit_length()
    emitted = format(lo, "0%db" % precision)[:count]
    mask = bound - 1
    next_low = (lo << count) & mask
    next_high = (((hi-1) << count) & mask) + (1 << count)
    return next_low, next_high, emitted


class ArithmeticCoder:
    def __init__(self, packet=None, bit_length=2336, precision=32, source_bits=None):
        if precision != 32:
            raise ValueError("public comparator precision is fixed at 32")
        if bit_length <= 0:
            raise ValueError("positive target required")
        self.target, self.precision = bit_length, precision
        self.source = "".join(format(b,"08b") for b in packet) if packet is not None else source_bits
        if self.source is not None and (len(self.source) != bit_length or set(self.source)-{"0","1"}):
            raise ValueError("source bit length mismatch")
        self.lower, self.upper = 0, 1 << precision
        self.bits = ""
        self.positions = self.packet_positions = self.skipped_positions = self.zero_bit_positions = 0
        self.termination_positions = self.termination_suffix_bits = self.lookahead_zero_bits = 0
        self.removed_mass_sum = self.quantization_l1_sum = 0.0
        self.minimum_retained_mass = 1.0

    @property
    def done(self):
        return len(self.bits) >= self.target

    def prepare(self, ids, q, order):
        if self.done:
            raise ValueError("packet already complete; no endpoint/tail flush")
        symbols, cdf, diagnostic = partition(ids,q,order,self.upper-self.lower)
        return {"ids":ids,"q":q,"order":order,"symbols":symbols,"cdf":cdf,"diagnostic":diagnostic}

    def select(self, step, rng=None):
        if self.source is None:
            raise ValueError("receiver cannot select arithmetic symbols")
        window = self.source[len(self.bits):len(self.bits)+self.precision].ljust(self.precision,"0")
        point = int(window,2)
        if not self.lower <= point < self.upper:
            raise ValueError("source point outside current arithmetic interval")
        bucket = int(np.searchsorted(step["cdf"], point-self.lower, side="right"))-1
        return int(step["symbols"][bucket])

    def consume(self, step, symbol):
        matches = np.flatnonzero(step["symbols"] == symbol)
        if len(matches) != 1:
            raise ValueError("observed symbol outside quantized arithmetic support")
        j = int(matches[0])
        before = len(self.bits)
        self.lookahead_zero_bits = max(self.lookahead_zero_bits, max(0,before+self.precision-self.target))
        self.lower,self.upper,emitted = narrow_and_emit(self.lower,self.upper,step["cdf"][j],step["cdf"][j+1],self.precision)
        if self.source is not None:
            expected = self.source[before:before+len(emitted)].ljust(len(emitted),"0")
            if emitted != expected:
                raise ValueError("arithmetic emitted bits differ from selected source")
        self.bits += emitted
        self.positions += 1
        self.packet_positions += bool(emitted)
        self.zero_bit_positions += not bool(emitted)
        d = step["diagnostic"]
        self.removed_mass_sum += d["removed_mass"]
        self.quantization_l1_sum += d["quantization_l1"]
        self.minimum_retained_mass = min(self.minimum_retained_mass,d["retained_mass"])
        if self.done:
            suffix = self.bits[self.target:]
            if len(suffix) > 31 or any(b != "0" for b in suffix):
                raise ValueError("invalid arithmetic zero-extended suffix")
            self.termination_suffix_bits = len(suffix)
            self.termination_positions = int(bool(suffix))  # overlaps last packet position
        return min(len(emitted), max(0,self.target-before))

    def packet(self):
        if not self.done:
            raise ValueError("capacity/truncation: arithmetic packet incomplete; no implicit flush")
        if self.target % 8:
            raise ValueError("byte packet requested for a non-byte test target")
        return int(self.bits[:self.target],2).to_bytes(self.target//8,"big")

    def diagnostics(self):
        result = {name:getattr(self,name) for name in ("positions","packet_positions","skipped_positions",
                  "zero_bit_positions","termination_positions","termination_suffix_bits","lookahead_zero_bits")}
        result.update({"minimum_retained_mass":self.minimum_retained_mass,
                       "mean_removed_mass":self.removed_mass_sum/max(1,self.positions),
                       "mean_quantization_l1":self.quantization_l1_sum/max(1,self.positions),
                       "precision":self.precision,"framing":"A1_common_prefix_known_2336_zero_extended"})
        return result
