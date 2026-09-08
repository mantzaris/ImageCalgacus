"""GPU reference/optimized matched-state and fixed-packet regression, not a receiver.
Private preparation is confined to this diagnostic run, outside pilot receivers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from imagecalgacus.packet import NewRun
from imagecalgacus.sender import read_source
from imagecalgacus.fixed_rank import packet_ranks, choose_rank, recover_rank, decode_bounded_ranks_to_bytes, ordinary_sample
from imagecalgacus.runtime import read_profile,json_write,source_hash
from imagecalgacus.text_backend import TextBackend
from imagecalgacus.text_reference import reference_distribution


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile",required=True)
    parser.add_argument("--source",required=True)
    parser.add_argument("--context",required=True)
    parser.add_argument("--new-run",required=True)
    args=parser.parse_args()
    run=NewRun(args.new_run)
    payload=read_source(args.source,"image-to-text")
    packet=run.encrypt(payload)
    (run.directory/"packet.bin").write_bytes(packet)
    ranks=packet_ranks(packet)
    context=Path(args.context).read_bytes()
    profile=read_profile(args.profile)
    model=TextBackend(profile)
    record={"source_hash":source_hash(),"fixed_packet_sha256":hashlib.sha256(packet).hexdigest(),
            "source":"I1","sequences":{},"eligible_ids_equal":True,"probability_bytes_equal":True,
            "ordering_equal":True,"sampling_equal":True,"carrier_bytes_equal":False}
    reference_carrier=None
    try:
        for mode in ("reference","optimized"):
            # Distribution fingerprints compare ALL 616 matched model states,
            # including the ordinary completion decisions.
            fingerprints=[]
            start=time.monotonic(); model.start(context)
            rng=np.random.Generator(np.random.PCG64(profile["completion_seed"]))
            distribution=reference_distribution if mode=="reference" else lambda m:m.distribution()
            for position in range(616):
                ids,q,order=distribution(model)
                fingerprints.append(hashlib.sha256(ids.tobytes()+q.tobytes()+order.tobytes()).hexdigest())
                symbol=choose_rank(order,ranks[position]) if position<584 else ordinary_sample(ids,q,rng)
                model.observe(symbol)
            raw=model.serialize()
            elapsed=time.monotonic()-start
            (run.directory/(mode+".txt")).write_bytes(raw)
            record["sequences"][mode+"_encode_seconds"]=elapsed
            record["sequences"][mode+"_carrier_sha256"]=hashlib.sha256(raw).hexdigest()
            if mode=="reference":
                reference_carrier=raw; reference_fingerprints=fingerprints
            else:
                if fingerprints != reference_fingerprints:
                    raise ValueError("matched-state eligible IDs/q/order differ")
                if raw != reference_carrier:
                    raise ValueError("carrier bytes/sampling decisions differ")
                record["carrier_bytes_equal"]=True
            start=time.monotonic(); model.start(context)
            decoded=[]
            for position,symbol in enumerate(model.reconstruct(raw)):
                ids,q,order=distribution(model)
                if symbol not in ids: raise ValueError("replay membership changed")
                if position<584: decoded.append(recover_rank(order,symbol))
                model.observe(symbol)
            if decode_bounded_ranks_to_bytes(decoded)!=packet:
                raise ValueError("fixed packet replay changed")
            record["sequences"][mode+"_decode_seconds"]=time.monotonic()-start
            print(mode,"passed",flush=True)
        record.update({"passed":True,"compared_states":616,"cold_load_seconds":model.load_seconds,"gpu_evidence":model.evidence})
        json_write(run.directory/"result.json",record)
        print(json.dumps({k:v for k,v in record.items() if k!="gpu_evidence"}))
    finally:
        model.close()


if __name__ == "__main__":
    main()
