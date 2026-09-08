from decimal import Decimal, localcontext
import tempfile
from pathlib import Path
import unittest
import numpy as np
from PIL import Image

from imagecalgacus.pixel_probabilities import component_log_masses, RGBConditionals
from imagecalgacus.image_backend import write_png, read_png
from imagecalgacus.text_backend import consistent_candidate, reset_model


def scalar_mass(value, mean, scale):
    with localcontext() as context:
        context.prec = 100
        x = Decimal(2) * Decimal(value) / Decimal(255) - 1
        half = Decimal(1) / Decimal(255)
        m, s = Decimal(str(mean)), Decimal(str(scale))
        def cdf(z):
            return 1 / (1 + (-z).exp())
        if value == 0:
            result = cdf((x + half - m) / s)
        elif value == 255:
            result = 1 - cdf((x - half - m) / s)
        else:
            result = cdf((x + half - m) / s) - cdf((x - half - m) / s)
        return float(result)


class PixelTests(unittest.TestCase):
    def test_independent_cdf_oracle(self):
        for mean, log_scale in [(0.13, -1.2), (-0.6, 0.2), (0, -7)]:
            actual = np.exp(component_log_masses([mean], [log_scale])[:, 0])
            for value in [0, 1, 32, 127, 128, 240, 254, 255]:
                expected = scalar_mass(value, mean, np.exp(log_scale))
                self.assertAlmostEqual(actual[value], expected, delta=2e-13)
            self.assertAlmostEqual(actual.sum(), 1, delta=1e-12)

    def test_rgb_joint_oracle_and_posteriors(self):
        raw = np.zeros(100)
        raw[:10] = [-0.3, 0.7] + [-1000] * 8
        rest = raw[10:].reshape(3, 30)
        rest[:, :2] = [[-0.5, 0.6], [0.1, -0.4], [-0.7, 0.2]]
        rest[:, 10:20] = -0.3
        rest[:, 20:22] = [[0.4, -0.7], [0.2, 0.3], [-0.4, 0.6]]
        weights = np.exp(raw[:2] - np.logaddexp.reduce(raw[:2]))
        for rgb in [(0, 255, 127), (64, 129, 210), (255, 0, 255)]:
            coder = RGBConditionals(raw)
            product = 1
            for value in rgb:
                ids, q, order = coder.distribution()
                product *= q[np.flatnonzero(ids == value)[0]]
                coder.observe(value)
            joint = 0
            xr, xg = 2 * rgb[0] / 255 - 1, 2 * rgb[1] / 255 - 1
            for k in range(2):
                means = [rest[0, k],
                         rest[1, k] + np.tanh(rest[0, 20 + k]) * xr,
                         rest[2, k] + np.tanh(rest[1, 20 + k]) * xr + np.tanh(rest[2, 20 + k]) * xg]
                masses = [scalar_mass(v, m, np.exp(-0.3)) for v, m in zip(rgb, means)]
                joint += weights[k] * np.prod(masses)
            self.assertAlmostEqual(product, joint, delta=max(1e-20, abs(joint) * 1e-11))

    def test_png_pixels_and_strict_modes(self):
        pixels = np.random.Generator(np.random.PCG64(43)).integers(0, 256, (31, 32, 3), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "carrier.png"
            write_png(path, pixels)
            np.testing.assert_array_equal(read_png(path), pixels)
            # Same samples survive different lossless compression.
            Image.fromarray(pixels).save(path, compress_level=0)
            np.testing.assert_array_equal(read_png(path), pixels)
            Image.fromarray(pixels).convert("RGBA").save(path)
            with self.assertRaises(ValueError):
                read_png(path)
            write_png(path, pixels)
            path.write_bytes(path.read_bytes() + b"hidden")
            with self.assertRaises(ValueError):
                read_png(path)


class FakeTokenizer:
    pieces = {1: b"a", 2: b"b", 3: b"ab", 4: b"\xc3", 5: b"\xa9", 6: "é".encode(),
              7: b" ", 8: b"\n", 9: b"<special>", 10: b"", 11: "🙂".encode(), 12: "e\u0301".encode()}
    def detokenize(self, ids, special=False):
        assert special is False
        return b"".join(self.pieces[i] for i in ids)
    def tokenize(self, data, add_bos=True, special=True):
        assert add_bos is False and special is False
        values = {b"a": [1], b"b": [2], b"ab": [3], "é".encode(): [6], b" ": [7], b"\n": [8],
                  b"<special>": [9], "🙂".encode(): [11], "e\u0301".encode(): [12]}
        return values.get(data, [])


class TextTests(unittest.TestCase):
    def test_complete_prefix_not_singletons(self):
        model = FakeTokenizer()
        self.assertTrue(consistent_candidate(model, [], 1))
        self.assertTrue(consistent_candidate(model, [], 2))
        self.assertFalse(consistent_candidate(model, [1], 2))
        self.assertFalse(consistent_candidate(model, [], 4))
        self.assertFalse(consistent_candidate(model, [4], 5))
        for token in [6, 7, 8, 9, 11, 12]:
            self.assertTrue(consistent_candidate(model, [], token))

    def test_reset_clears_actual_context(self):
        events = []
        class Context:
            def kv_cache_clear(self): events.append("clear")
        class Model:
            _ctx = Context()
            def reset(self): events.append("reset")
        reset_model(Model())
        self.assertEqual(events, ["reset", "clear"])
        Model._ctx = object()
        with self.assertRaises(RuntimeError):
            reset_model(Model())


if __name__ == "__main__":
    unittest.main()
