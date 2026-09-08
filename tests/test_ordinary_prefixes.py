"""CPU-only ordinary prefix-report checks; no model inference."""
from contextlib import redirect_stdout
import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from imagecalgacus.runtime import ROOT
from imagecalgacus import ordinary

class UniformText:
    def __init__(self,profile):
        self.prefix=[];self.calls=0;self.load_seconds=0.;self.filter_seconds=0.
        self.evidence={"synthetic_CPU_only":True}
    def start(self,context): self.prefix=[]
    def distribution(self): return np.arange(16),np.full(16,1/16),np.arange(16)
    def observe(self,symbol): self.prefix.append(symbol);self.calls+=1
    def serialize(self): return bytes(v+65 for v in self.prefix)
    def close(self): pass

class OrdinaryPrefixTests(unittest.TestCase):
    def test_prefix_scores_and_bytes_are_matched_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"prompt.txt").write_bytes(b"test")
            args=["ordinary","--modality","text","--profile",str(ROOT/"configs/v0.json"),
                  "--context",str(root/"prompt.txt"),"--seed","4301","--symbols","32",
                  "--purpose","control","--prefix-lengths","8,16,32","--output",str(root/"control")]
            with patch("sys.argv",args),patch("imagecalgacus.text_backend.TextBackend",UniformText),redirect_stdout(io.StringIO()):
                ordinary.main()
            r=json.loads((root/"control/result.json").read_text())
            raw=(root/"control/carrier.txt").read_bytes()
            for n in (8,16,32):
                d=r["prefix_diagnostics"][str(n)]["diagnostics"]["whole"]
                self.assertEqual(d["positions"],n)
                self.assertEqual(d["surprisal_bits_mean"],4)
                self.assertEqual(d["entropy_bits_mean"],4)
                self.assertEqual((root/("control/prefix-%d.txt"%n)).read_bytes(),raw[:n])
            self.assertTrue(r["gpu_evidence"]["synthetic_CPU_only"])

if __name__=="__main__": unittest.main()
