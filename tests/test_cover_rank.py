"""Focused public synthetic checks. No neural inference."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from cryptography.exceptions import InvalidTag
from imagecalgacus.cover_rank import (
    BITS, SHAPE, OFFSETS, coarse, candidates, positions, rank_labels,
    candidate_log_scores, conditional_oracle_error, nearest, embed, extract,
    partition_distance, observed_index,
)
from imagecalgacus.packet import Payload,TEXT,seal,open_packet
from imagecalgacus.image_backend import read_png,write_png
from imagecalgacus.runtime import apply_cover_rank_allowance,phase_limit

class CoverRankTests(unittest.TestCase):
    def test_joint_matches_sequential_conditional_with_dependencies_and_edges(self):
        params = np.linspace(-1,1,100)
        params[10:] = np.sin(np.arange(90))*.8
        for cell in ([0,0,0],[124,128,132],[252,252,252]):
            self.assertLess(conditional_oracle_error(params,candidates(cell)),1e-10)
        a = candidate_log_scores(params,candidates([124,128,132]))
        params[10:].reshape(3,30)[:,20:] = 0
        self.assertFalse(np.allclose(a,candidate_log_scores(params,candidates([124,128,132]))))

    def test_log_underflow_does_not_remove_candidates(self):
        params = np.zeros(100)
        rest = params[10:].reshape(3,30)
        rest[:,:10] = 100
        rest[:,10:20] = -7
        scores = candidate_log_scores(params,candidates([0,0,0]))
        self.assertTrue(np.all(np.isfinite(scores)))
        self.assertEqual(np.count_nonzero(np.exp(scores)),0)
        labels,_ = rank_labels(scores)
        self.assertEqual(int(labels.sum()),32)

    def test_ties_and_independent_nearest_oracle(self):
        labels,order = rank_labels(np.zeros(64))
        self.assertEqual(order.tolist(),list(range(64)))
        colors = candidates([124,0,252])
        original = np.array([125,1,254])
        for bit in (0,1):
            expected = min((tuple(map(int,c)) for c,l in zip(colors,labels) if l == bit),
                           key=lambda c:(sum((int(a)-b)**2 for a,b in zip(original,c)),c))
            self.assertEqual(tuple(nearest(original,colors,labels,bit)),expected)

    def test_partition_comparison_allows_label_swap(self):
        parity = OFFSETS.sum(axis=1)%2
        same = np.stack([parity,1-parity])
        self.assertEqual(partition_distance(same).tolist(),[0.,0.])
        changed=parity.copy(); changed[0],changed[1]=changed[1],changed[0]
        self.assertEqual(partition_distance(changed[None])[0],2/64)

    def test_keyed_placement_and_artifact_only_recovery(self):
        cover=np.random.default_rng(31).integers(0,256,SHAPE,dtype=np.uint8)
        key=bytes(range(32)); base=coarse(cover)
        selected=positions(base,key)
        self.assertEqual(len(set(selected)),BITS)
        self.assertTrue(np.array_equal(selected,positions(base.copy(),key)))
        self.assertFalse(np.array_equal(selected,positions(base,key[::-1])))
        labels=np.tile((OFFSETS.sum(axis=1)%2).astype(np.uint8),(BITS,1))
        source=b"A literal message with enough UTF-8 bytes."
        packet=seal(Payload(TEXT,source),key,bytes(12))
        carrier=embed(cover,packet,selected,labels)
        self.assertTrue(np.array_equal(coarse(carrier),base))
        self.assertLessEqual(int(np.max(np.abs(carrier.astype(int)-cover.astype(int)))),3)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"carrier.png"; write_png(path,carrier)
            delivered=read_png(path,SHAPE)
            # Receiver recomputes placement solely from delivered pixels.
            got=extract(delivered,positions(coarse(delivered),key),labels)
            self.assertEqual(open_packet(got,key,TEXT).data,source)
            with self.assertRaises(InvalidTag): open_packet(got,key[::-1],TEXT)
            y,x=divmod(int(selected[0]),256)
            bit=int(labels[0,observed_index(delivered[y,x])])
            delivered[y,x]=nearest(delivered[y,x],candidates(base[y,x]),labels[0],1-bit)
            with self.assertRaises(InvalidTag):
                open_packet(extract(delivered,selected,labels),key,TEXT)
            # Unused low bits are not authenticated as image content.
            unused=next(p for p in range(65536) if p not in set(selected))
            y,x=divmod(unused,256); carrier[y,x,0]^=np.uint8(1)
            self.assertEqual(open_packet(extract(carrier,selected,labels),key,TEXT).data,source)

    def test_theoretical_distortion_bound(self):
        sse=2336*3*3**2
        mse=sse/(256*256*3)
        psnr=10*np.log10(255**2/mse)
        self.assertAlmostEqual(psnr,53.0685,places=3)

    def test_allowance_is_absolute_and_v0_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"auth.json"
            self.assertTrue(apply_cover_rank_allowance(path))
            self.assertFalse(apply_cover_rank_allowance(path))
            self.assertEqual(phase_limit("cover_rank_v1",path),7200)
            self.assertEqual(phase_limit("v0",Path(tmp)/"absent"),7200)
            value=json.loads(path.read_text());value["absolute_seconds"]=14400
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError): phase_limit("cover_rank_v1",path)

if __name__=="__main__": unittest.main()
