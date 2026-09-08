"""Exact discrete PixelCNN++ RGB conditionals, computed on the CPU in float64.
Likelihood parameter layout follows the attributed PixelCNN++ implementations.
Unlike their small-mass training-loss approximation, these are exact bin masses.
"""
import numpy as np
from .fixed_rank import normalized, stable_order


def component_log_masses(means, log_scales):
    means = np.asarray(means, dtype=np.float64)
    log_scales = np.maximum(np.asarray(log_scales, dtype=np.float64), -7)
    if not np.all(np.isfinite(means)) or not np.all(np.isfinite(log_scales)):
        raise ValueError("nonfinite logistic parameters")
    inv_scale = np.exp(-log_scales)
    x = 2 * np.arange(256, dtype=np.float64) / 255 - 1
    middle = (x[:, None] - means) * inv_scale
    half = inv_scale / 255
    lower, upper = middle - half, middle + half
    with np.errstate(divide="ignore", under="ignore"):
        # sigmoid(upper)-sigmoid(lower), avoiding subtracting two near-ones.
        log_mass = lower + np.log(np.expm1(2 * half)) - np.logaddexp(0, lower) - np.logaddexp(0, upper)
    log_mass[0] = -np.logaddexp(0, -upper[0])
    log_mass[255] = -np.logaddexp(0, lower[255])
    if np.any(np.isnan(log_mass)) or np.any(np.isposinf(log_mass)):
        raise ValueError("invalid logistic masses")
    if not np.allclose(np.exp(log_mass).sum(axis=0), 1, rtol=0, atol=1e-12):
        raise ValueError("logistic bins do not normalize")
    return log_mass


class RGBConditionals:
    def __init__(self, parameters):
        values = np.asarray(parameters, dtype=np.float64)
        if values.shape != (100,) or not np.all(np.isfinite(values)):
            raise ValueError("expected 100 finite mixture parameters")
        logits = values[:10]
        self.log_weights = logits - np.logaddexp.reduce(logits)
        rest = values[10:].reshape(3, 30)
        self.means = rest[:, :10]
        self.log_scales = np.maximum(rest[:, 10:20], -7)
        self.coefficients = np.tanh(rest[:, 20:30])
        self.observed = []
        self.current_masses = None

    def distribution(self):
        channel = len(self.observed)
        if channel >= 3:
            raise ValueError("pixel already complete")
        means = self.means[channel].copy()
        if channel >= 1:
            red = 2 * self.observed[0] / 255 - 1
            means += self.coefficients[channel - 1] * red
        if channel == 2:
            means += self.coefficients[2] * (2 * self.observed[1] / 255 - 1)
        self.current_masses = component_log_masses(means, self.log_scales[channel])
        log_probs = np.logaddexp.reduce(self.current_masses + self.log_weights, axis=1)
        q = normalized(log_probs)
        ids = np.flatnonzero(q > 0)
        q = q[ids]
        q /= q.sum(dtype=np.float64)
        order = stable_order(log_probs)
        order = order[np.isin(order, ids)]
        return ids, q, order

    def observe(self, value):
        if self.current_masses is None or not isinstance(value, (int, np.integer)) or not 0 <= value <= 255:
            raise ValueError("observation without a valid channel distribution")
        self.log_weights = self.log_weights + self.current_masses[int(value)]
        normalization = np.logaddexp.reduce(self.log_weights)
        if not np.isfinite(normalization):
            raise ValueError("zero posterior mass")
        self.log_weights -= normalization
        self.observed.append(int(value))
        self.current_masses = None
