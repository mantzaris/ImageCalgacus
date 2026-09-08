"""Small method dispatch; profiles are data, not a plugin registry."""
from .entropy_coding import RankCoder
from .arithmetic_coding import ArithmeticCoder


def make_coder(method, packet=None, threshold=None):
    if method == "fixed":
        return RankCoder(packet)
    if method == "gated":
        if threshold is None:
            raise ValueError("frozen modality threshold required")
        return RankCoder(packet,threshold)
    if method == "arithmetic":
        return ArithmeticCoder(packet)
    raise ValueError("unknown coding method")

def coder_for_profile(profile, modality, packet=None):
    config = profile.get("coder", {})
    method = config.get("method", "fixed")
    threshold = config.get("thresholds", {}).get(modality, {}).get("value")
    return make_coder(method,packet,threshold)


class Trace:
    """Compact online diagnostics; never used to reconstruct receiver state."""
    def __init__(self):
        self.groups = {key:{"count":0,"surprisal_bits_sum":0.0,"rank_sum":0.0,"log_rank_sum":0.0,
                            "entropy_bits_sum":0.0} for key in ("whole","packet_span","packet_bearing","skipped","completion")}
        self.top256_mass_sum = self.eligible_mass_sum = 0.0
        self.distortion_sum = 0.0
        self.distortion_count = 0

    def observe(self, ids, q, order, symbol, role, carrying_bits, backend):
        import math
        import numpy as np
        from .entropy_coding import shannon_entropy_bits
        index = int(np.flatnonzero(ids == symbol)[0])
        rank = int(np.flatnonzero(order == symbol)[0]) + 1
        values = {"surprisal_bits_sum":-math.log2(float(q[index])),
                  "rank_sum":rank,"log_rank_sum":math.log2(rank),"entropy_bits_sum":shannon_entropy_bits(q)}
        names = ["whole"]
        if role == "completion":
            names.append("completion")
        else:
            names.append("packet_span")
            if carrying_bits: names.append("packet_bearing")
            if role == "skipped": names.append("skipped")
        for name in names:
            group = self.groups[name]
            group["count"] += 1
            for key,value in values.items(): group[key] += value
        masses = getattr(backend,"last_diagnostics",{})
        self.top256_mass_sum += masses.get("top256_mass",1.0)
        self.eligible_mass_sum += masses.get("eligible_mass",1.0)
        if len(order) >= 16:
            lookup = {int(v):float(p) for v,p in zip(ids,q)}
            self.distortion_sum += -4-sum(math.log2(lookup[int(v)]) for v in order[:16])/16
            self.distortion_count += 1

    def summary(self):
        result={}
        for name,group in self.groups.items():
            result[name]={"positions":group["count"]}
            for field,value in group.items():
                if field != "count":
                    result[name][field.replace("_sum","_mean")] = value/group["count"] if group["count"] else None
        count=self.groups["whole"]["count"]
        result["mean_top256_mass"]=self.top256_mass_sum/count if count else None
        result["mean_eligible_mass"]=self.eligible_mass_sum/count if count else None
        result["mean_top16_uniform_rank_divergence_bits"]=self.distortion_sum/self.distortion_count if self.distortion_count else None
        return result
