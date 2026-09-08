"""CPU checks against the actual frozen sources and explicit allocation."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import unittest
import numpy as np
from PIL import Image
from imagecalgacus.runtime import ROOT,sha256_file,canonical_hash
from imagecalgacus.evaluate import validate_allocation


class QualificationSources(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/"data/qualification_v1"
        self.manifest=json.loads((self.root/"manifest.json").read_text())
        self.allocation=json.loads((ROOT/"configs/v1_qualification.json").read_text())

    def test_counts_bytes_disjointness_and_fixture_preservation(self):
        counts=Counter(); bands=Counter(); hashes=[]
        for item in self.manifest["payloads"]:
            path=self.root/item["source"]
            self.assertEqual(sha256_file(path),item["file_sha256"])
            if item["direction"]=="image-to-text":
                with Image.open(path) as im:
                    self.assertEqual((im.mode,im.size,im.format),("L",(16,16),"PNG"))
                    raw=im.tobytes()
                self.assertEqual(len(raw),256)
            else:
                raw=path.read_bytes(); self.assertEqual(raw.decode("utf-8").encode("utf-8"),raw)
                self.assertTrue(32<=len(raw)<=128)
                bands[item["split"],"32-64" if len(raw)<=64 else "65-128"]+=1
            counts[item["split"],item["direction"]]+=1
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item["source_sha256"])
            hashes.append(item["source_sha256"])
            if item["provenance"]["type"]=="accepted_fixture":
                self.assertEqual(path.read_bytes(),(ROOT/item["provenance"]["original_path"]).read_bytes())
        self.assertEqual(len(set(hashes)),80)
        self.assertEqual(list(counts.values()),[20]*4)
        self.assertEqual(sorted(bands.values()),[10]*4)

    def test_source_offsets_and_original_image_indices(self):
        cache=ROOT/".runtime/source_cache"
        if not cache.exists(): self.skipTest("requires the pinned source cache")
        spans={}; originals=[]
        for item in self.manifest["payloads"]:
            p=item["provenance"]
            if p["type"]=="gutenberg":
                raw=(cache/p["archive"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),self.manifest["sources"][p["archive"]]["sha256"])
                start,end=p["byte_start"],p["byte_end_exclusive"]
                self.assertEqual(raw[start:end],(self.root/item["source"]).read_bytes())
                self.assertTrue(p["body_byte_bounds"][0]<=start<end<=p["body_byte_bounds"][1])
                for a,b in spans.get(p["book"],[]): self.assertFalse(start<b and a<end)
                spans.setdefault(p["book"],[]).append((start,end))
            elif p["type"]=="fashion_mnist":
                raw=gzip.decompress((cache/p["archive"]).read_bytes())
                offset=16+784*p["original_index"]
                pixels=raw[offset:offset+784]
                self.assertEqual(hashlib.sha256(pixels).hexdigest(),p["original_sha256"])
                originals.append(p["original_sha256"])
                im=Image.frombytes("L",(28,28),pixels).resize((16,16),Image.Resampling.BOX)
                with Image.open(self.root/item["source"]) as saved: self.assertEqual(im.tobytes(),saved.tobytes())
                labels=gzip.decompress((cache/p["archive"].replace("images-idx3","labels-idx1")).read_bytes())
                self.assertEqual(labels[8+p["original_index"]],p["class"])
        self.assertEqual(len(set(originals)),35)
        held=[p["provenance"]["class"] for p in self.manifest["payloads"] if p["split"]=="heldout" and p["direction"]=="image-to-text"]
        self.assertEqual(Counter(held),Counter({i:2 for i in range(10)}))

    def test_context_freeze_and_reproduction(self):
        contexts={c["id"]:c for c in self.manifest["contexts"]}
        for c in contexts.values(): self.assertEqual(sha256_file(self.root/c["path"]),c["sha256"])
        self.assertEqual((self.root/"contexts/prompt1.txt").read_bytes(),(ROOT/"artifacts/v0_review/contexts/prompt.txt").read_bytes())
        self.assertEqual((self.root/"contexts/row1.rgb").read_bytes(),(ROOT/"artifacts/v0_review/contexts/row.rgb").read_bytes())
        self.assertEqual((self.root/"contexts/prompt2.txt").read_bytes(),b"Explain how a home cook prepares a simple vegetable soup. Use continuous prose.")
        self.assertEqual(len((self.root/"contexts/row2.rgb").read_bytes()),96)
        other=ROOT/".runtime/v1_2/source-reproduction"
        if other.exists():
            for path in self.root.rglob("*"):
                if path.is_file() and path != self.root/"README.md":
                    self.assertEqual(path.read_bytes(),(other/path.relative_to(self.root)).read_bytes())

    def test_pair_ids_and_exact_legacy_credits(self):
        cases=self.allocation["cases"]
        self.assertEqual(len(cases),152)
        self.assertEqual(len({c["work_id"] for c in cases}),152)
        legacy=json.loads((ROOT/"artifacts/v1_review/pilot_manifest.json").read_text())["cases"]
        self.assertEqual({c["work_id"] for c in cases if c["status"]=="credited"},{c["work_id"] for c in legacy})
        pair=[c for c in cases if c["pair_id"]=="I6-prompt1" and c["method"]=="fixed"]
        self.assertEqual({c["text_filter_arm"] for c in pair},{"static","sequence"})
        self.assertEqual(len({c["source_sha256"] for c in pair}),1)
        self.assertEqual(len({c["context_sha256"] for c in pair}),1)
        profiles=[json.loads((ROOT/c["profile"]).read_text()) for c in pair]
        for p in profiles: p.pop("development_text_filter",None)
        self.assertEqual(profiles[0],profiles[1])
        row=dict(case=pair[0]["id"],work_id=pair[0]["work_id"],attempted=True,terminal=True,
                 evidence_valid=True,carrier_complete=True,exact_recovery=True)
        self.assertFalse(validate_allocation(pair,[row])["allocation_complete"])
        self.assertFalse(validate_allocation(pair,[row,row])["allocation_complete"])
        traces=self.allocation["traces"]
        self.assertEqual(Counter((t["purpose"],t["status"]) for t in traces),
            {("ordinary","credited"):4,("ordinary","pending"):12,("control","credited"):2,("control","pending"):46})


if __name__=="__main__": unittest.main()
