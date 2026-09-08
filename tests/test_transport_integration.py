"""Synthetic adapter integration; deliberately no neural/GPU inference claim."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from imagecalgacus.runtime import ROOT
from imagecalgacus.sender import encode
from imagecalgacus.receiver import receive
from imagecalgacus.fixed_rank import stable_order


class SyntheticText:
    unary=False
    uniform=False
    def __init__(self,profile):
        self.prefix=[]; self.calls=0; self.load_seconds=0.; self.filter_seconds=0.
        self.evidence={"synthetic_CPU_only":True}
    def start(self,context): self.prefix=[]
    def distribution(self):
        if self.unary: return np.array([0]),np.array([1.]),np.array([0])
        q=np.full(32,1/32) if self.uniform or len(self.prefix)%2 else np.array([.97]+[.03/31]*31)
        return np.arange(32),q,stable_order(np.log(q))
    def observe(self,symbol): self.prefix.append(symbol); self.calls+=1
    def serialize(self): return bytes(v+33 for v in self.prefix)
    def reconstruct(self,raw): return [v-33 for v in raw]
    def close(self): pass


class TransportIntegration(unittest.TestCase):
    def run_case(self,method,threshold=3,unary=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            profile=json.loads((ROOT/"configs/v0.json").read_text())
            profile["protocol"]="imagecalgacus-v1-three-methods"
            profile["coder"]={"method":method,"precision":32,"framing":"A1","calibration_sha256":"synthetic",
                              "thresholds":{m:{"value":float(threshold),"hex":float(threshold).hex()} for m in ("text","image")}}
            (root/"profile.json").write_text(json.dumps(profile))
            (root/"prompt.txt").write_bytes(b"synthetic context")
            source=np.arange(256,dtype=np.uint8).reshape(16,16)
            Image.fromarray(source).save(root/"source.png")
            send=SimpleNamespace(source=root/"source.png",direction="image-to-text",profile=root/"profile.json",
                                 context=root/"prompt.txt",new_run=root/"case",prepared_packet=None,key=None)
            inbox=root/"case/inbox"
            receive_args=SimpleNamespace(direction="image-to-text",carrier=inbox/"carrier.txt",profile=inbox/"profile.json",
                                        context=inbox/"prompt.txt",key=inbox/"run.key",
                                        output=root/"case/recovered.gray",report=root/"case/receiver.json")
            SyntheticText.unary=unary
            SyntheticText.uniform=method=="arithmetic" and not unary
            with patch("imagecalgacus.text_backend.TextBackend",SyntheticText),redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                sent=encode(send); received=receive(receive_args)
            sender=json.loads((root/"case/sender.json").read_text())
            receiver=json.loads((root/"case/receiver.json").read_text())
            self.assertEqual(sender["packet_bits_recovered"],receiver["packet_bits_recovered"])
            self.assertEqual(sender["packet_stop"],receiver["packet_stop"])
            if sent==0:
                self.assertEqual(received,0)
                self.assertEqual((root/"case/recovered.gray").read_bytes(),source.tobytes())
                self.assertEqual(sender["completion_symbols"],32)
            else:
                self.assertEqual((sent,received),(2,2))
                self.assertFalse(receiver["authenticated"])
                self.assertFalse((root/"case/recovered.gray").exists())
            return sent

    def test_three_methods_saved_file_progress_and_tail(self):
        for method in ("fixed","gated","arithmetic"):
            with self.subTest(method=method): self.assertEqual(self.run_case(method),0)

    def test_capacity_is_retained_and_not_authenticated(self):
        self.assertEqual(self.run_case("gated",threshold=6),2)
        self.assertEqual(self.run_case("arithmetic",unary=True),2)


if __name__=="__main__":
    unittest.main()
