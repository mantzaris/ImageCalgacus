"""CPU tokenizer counterexample: concatenation can merge singleton-stable tokens."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from imagecalgacus.text_backend import TextBackend
from imagecalgacus.runtime import ROOT, read_profile
from imagecalgacus.receiver import receive


class MergeTokenizer:
    pieces = {0:b"a", 1:b"b", **{i:bytes([65+i]) for i in range(2,31)}, 31:b"ab"}
    def detokenize(self, ids, special=False):
        return b"".join(self.pieces[i] for i in ids)
    def tokenize(self, raw, add_bos=False, special=False):
        # Independent greedy merger, not the backend's eligibility calculation.
        result=[]
        while raw:
            piece = b"ab" if raw.startswith(b"ab") else raw[:1]
            result.append(next(k for k,v in self.pieces.items() if v==piece))
            raw=raw[len(piece):]
        return result


def adapter(arm):
    obj=TextBackend.__new__(TextBackend)
    obj.model=MergeTokenizer(); obj.prefix=[0]; obj._carrier_bytes=b"a"
    obj.text_filter=arm; obj._singleton_mask={}
    return obj


class SavedBytesReplay:
    def __init__(self, profile):
        self.tokenizer=adapter(profile["development_text_filter"])
        self.calls=0; self.filter_seconds=0.; self.load_seconds=0.
        self.evidence={"synthetic_CPU_only":True}
    def reconstruct(self, raw): return self.tokenizer.reconstruct(raw)
    def start(self, context): pass
    def distribution(self): return np.arange(32),np.full(32,1/32),np.arange(32)
    def observe(self, symbol): self.calls+=1
    def close(self): pass


class StaticFilter(unittest.TestCase):
    def test_singleton_differs_only_at_prefix_merge(self):
        sequence,static=adapter("sequence"),adapter("static")
        self.assertFalse(sequence.eligible_piece(1,b"b"))
        self.assertTrue(static.eligible_piece(1,b"b"))
        self.assertTrue(sequence.eligible_piece(2,b"C"))
        self.assertTrue(static.eligible_piece(2,b"C"))
        self.assertFalse(static.eligible_piece(32,b"\xff"))
        self.assertFalse(sequence.eligible_piece(32,b"\xff"))
        self.assertEqual(static._singleton_mask[1],True)

    def test_static_retains_drift_sequence_remains_strict(self):
        for arm in ("static","sequence"):
            obj=adapter(arm); obj.prefix=[0,1]; obj._carrier_bytes=b"ab"
            if arm=="sequence":
                with self.assertRaisesRegex(ValueError,"final text tokenization changed"): obj.serialize()
            else:
                raw=obj.serialize()
                self.assertEqual(raw,b"ab")
                self.assertEqual(obj.reconstruct(raw),[31])
                self.assertTrue(obj.serialization_diagnostics["tokenization_drift"])
                self.assertEqual(obj.serialization_diagnostics["retokenized_tokens"],1)

    def test_saved_bytes_alone_fail_without_sender_token_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); inbox=root/"inbox"; inbox.mkdir()
            profile=json.loads((ROOT/"configs/v1_fixed.json").read_text())
            profile["development_text_filter"]="static"
            (inbox/"profile.json").write_text(json.dumps(profile))
            (inbox/"carrier.txt").write_bytes(b"ab"*308)
            (inbox/"prompt.txt").write_bytes(b"context")
            (inbox/"run.key").write_bytes(bytes(32))  # synthetic, not an encoding key
            args=SimpleNamespace(direction="image-to-text",carrier=inbox/"carrier.txt",
                context=inbox/"prompt.txt",profile=inbox/"profile.json",key=inbox/"run.key",
                output=root/"recovered.gray",report=root/"receiver.json")
            with patch("imagecalgacus.text_backend.TextBackend",SavedBytesReplay),redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                self.assertEqual(receive(args),1)
            record=json.loads((root/"receiver.json").read_text())
            self.assertEqual(record["parsed_symbol_count"],308)
            self.assertEqual(record["failure_stage"],"replay")
            self.assertFalse(record["authenticated"])
            self.assertFalse((root/"recovered.gray").exists())
            self.assertEqual(set(p.name for p in inbox.iterdir()),{"carrier.txt","profile.json","prompt.txt","run.key"})

    def test_profile_default_and_opt_in_bounds(self):
        self.assertNotIn("development_text_filter",read_profile(ROOT/"configs/v1_fixed.json"))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"profile.json"
            for method in ("fixed","gated","arithmetic"):
                profile=json.loads((ROOT/("configs/v1_"+method+".json")).read_text())
                profile["development_text_filter"]="static"
                path.write_text(json.dumps(profile))
                if method=="fixed": self.assertEqual(read_profile(path)["development_text_filter"],"static")
                else:
                    with self.assertRaises(ValueError): read_profile(path)


if __name__=="__main__": unittest.main()
