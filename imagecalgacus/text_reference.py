"""Accepted V0 distribution, retained verbatim for focused V1 equivalence checks.
Source revision bc9e98d3ed99fc040c341f50f74e6b9cd017d8dc; package hash 77ef233f...
No payload/reference fixtures are embedded here.
"""
import time
import numpy as np
from .fixed_rank import stable_order, normalized
from .text_backend import consistent_candidate, detokenize_bytes

def reference_distribution(self):
    started = time.monotonic()
    scores = np.asarray(self.model.scores[self.model.n_tokens - 1], dtype=np.float64)
    pool = stable_order(scores)[:256]
    raw_q = normalized(scores)
    allowed = []
    for value in pool:
        token = int(value)
        if token not in self._special:
            attributes = self.model._model.token_get_attr(token)
            self._special[token] = bool(attributes & (1 | 2 | 8 | 16))
        if self._special[token] or raw_q[token] == 0:
            continue
        if not detokenize_bytes(self.model, [token]):
            continue
        if consistent_candidate(self.model, self.prefix, token):
            allowed.append(token)
    if not allowed:
        raise ValueError("empty text support after complete-prefix filtering")
    ids = np.sort(np.asarray(allowed, dtype=np.int64))
    q = normalized(scores[ids])
    keep = q > 0
    ids, q = ids[keep], q[keep]
    q /= q.sum(dtype=np.float64)
    order = np.asarray([v for v in allowed if v in ids], dtype=np.int64)
    self.last_diagnostics = {"support": len(ids), "top256_mass": float(raw_q[pool].sum()),
                             "eligible_mass": float(raw_q[ids].sum())}
    self.filter_seconds += time.monotonic() - started
    return ids, q, order
