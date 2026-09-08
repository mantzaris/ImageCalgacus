"""Pure CPU equivalence of optimized top-k, ties, normalization and sampling."""
import unittest
import numpy as np
from imagecalgacus.fixed_rank import stable_order, normalized, ordinary_sample
from imagecalgacus.text_backend import exact_top_k, probabilities_without_sort


class TextOptimization(unittest.TestCase):
    def test_top_k_ties_and_probability_bytes(self):
        rng=np.random.Generator(np.random.PCG64(7101))
        for size in (16,256,513,128256):
            for scores in (rng.normal(size=size),rng.integers(-4,5,size=size).astype(float),np.zeros(size)):
                np.testing.assert_array_equal(exact_top_k(scores),stable_order(scores)[:256])
                self.assertEqual(probabilities_without_sort(scores).tobytes(),normalized(scores).tobytes())
        scores=np.concatenate((np.ones(255),np.zeros(1000),np.array([-np.inf])))
        np.testing.assert_array_equal(exact_top_k(scores),np.arange(256))

    def test_sampling_and_invalid_numerics(self):
        scores=np.array([2.,-1.,0.,0.,-np.inf])
        ids=np.arange(4)
        old,new=normalized(scores)[:4],probabilities_without_sort(scores)[:4]
        a,b=np.random.Generator(np.random.PCG64(19)),np.random.Generator(np.random.PCG64(19))
        self.assertEqual([ordinary_sample(ids,old,a) for _ in range(1000)],
                         [ordinary_sample(ids,new,b) for _ in range(1000)])
        for scores in (np.array([np.nan]),np.array([np.inf]),np.array([])):
            with self.assertRaises(ValueError): exact_top_k(scores)
        with self.assertRaises(ValueError): probabilities_without_sort(np.array([-np.inf]))


if __name__ == "__main__":
    unittest.main()
