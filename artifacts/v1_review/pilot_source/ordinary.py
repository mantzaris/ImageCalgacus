"""Ordinary GPU development traces and shared matched controls; no keys/payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import time
import numpy as np
from .coders import Trace
from .entropy_coding import shannon_entropy_bits
from .fixed_rank import ordinary_sample
from .runtime import read_profile,json_write,canonical_hash,source_hash


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--modality",choices=["text","image"],required=True)
    parser.add_argument("--profile",required=True)
    parser.add_argument("--context",required=True)
    parser.add_argument("--seed",type=int,required=True)
    parser.add_argument("--symbols",type=int,required=True)
    parser.add_argument("--purpose",choices=["calibration","control"],required=True)
    parser.add_argument("--prefix-lengths",default="")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    profile=read_profile(args.profile)
    if args.modality=="image" and args.symbols!=2976 or args.modality=="text" and not 1<=args.symbols<=2048:
        raise ValueError("invalid ordinary carrier budget")
    args.output.mkdir(parents=True,exist_ok=False)
    model=None; entropies=[]; trace=Trace(); started=time.monotonic()
    result={"purpose":args.purpose,"modality":args.modality,"seed":args.seed,
            "profile_id":canonical_hash(profile),"source_hash":source_hash(),
            "context_sha256":hashlib.sha256(Path(args.context).read_bytes()).hexdigest(),"passed":False}
    try:
        if args.modality=="text":
            from .text_backend import TextBackend
            model=TextBackend(profile)
        else:
            from .image_backend import ImageBackend
            model=ImageBackend(profile)
        result["cold_load_seconds"]=model.load_seconds
        begin=time.monotonic(); model.start(Path(args.context).read_bytes())
        rng=np.random.Generator(np.random.PCG64(args.seed))
        prefixes=set(map(int,args.prefix_lengths.split(","))) if args.prefix_lengths else set()
        if any(n<1 or n>args.symbols for n in prefixes): raise ValueError("invalid matched control length")
        for i in range(args.symbols):
            ids,q,order=model.distribution()
            entropies.append(shannon_entropy_bits(q))
            symbol=ordinary_sample(ids,q,rng)
            trace.observe(ids,q,order,symbol,"completion",0,model)
            model.observe(symbol)
            if args.modality=="text" and i+1 in prefixes:
                (args.output/("prefix-%d.txt"%(i+1))).write_bytes(model.serialize())
            if (i+1)%256==0: print("ordinary",i+1,flush=True)
        if args.modality=="text":
            carrier=args.output/"carrier.txt"; carrier.write_bytes(model.serialize())
        else:
            from .image_backend import write_png
            carrier=args.output/"carrier.png"; write_png(carrier,model.canvas[1:])
        result.update({"passed":True,"generation_seconds":time.monotonic()-begin,"model_calls":model.calls,
                       "carrier":str(carrier),"carrier_bytes":carrier.stat().st_size,
                       "carrier_sha256":hashlib.sha256(carrier.read_bytes()).hexdigest(),
                       "symbols":args.symbols,"entropies_bits":entropies,"diagnostics":trace.summary()})
        if args.modality=="text": result["filter_seconds"]=model.filter_seconds
    finally:
        if model is not None:
            result["gpu_evidence"]=model.evidence; model.close()
        result["total_seconds"]=time.monotonic()-started
        result["peak_rss_kib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        json_write(args.output/"result.json",result)
    print(json.dumps({k:v for k,v in result.items() if k not in {"gpu_evidence","entropies_bits","diagnostics"}}))


if __name__=="__main__":
    main()
