"""Fresh-process artifact receiver; no sender/evaluator/reference imports."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import time
import traceback
from .packet import open_packet, TEXT, GRAYSCALE
from .coders import coder_for_profile, Trace
from .runtime import read_profile, json_write, canonical_hash


def receive(args):
    inputs=[Path(p).resolve() for p in (args.carrier,args.profile,args.context,args.key)]
    if len(set(inputs))!=4 or len({p.parent for p in inputs})!=1:
        raise ValueError("stage four distinct permitted inputs in one receiver directory")
    if {p.resolve() for p in inputs[0].parent.iterdir()}!=set(inputs):
        raise ValueError("receiver directory contains undeclared inputs")
    if Path(args.output).resolve().parent==inputs[0].parent or Path(args.report).resolve().parent==inputs[0].parent:
        raise ValueError("outputs must be outside receiver input directory")
    if Path(args.output).exists() or Path(args.report).exists():
        raise FileExistsError("refusing to overwrite recovered output/report")
    profile=read_profile(args.profile)
    context,key=Path(args.context).read_bytes(),Path(args.key).read_bytes()
    if len(key)!=32: raise ValueError("wrong key length")
    modality="text" if args.direction=="image-to-text" else "image"
    method=profile.get("coder",{}).get("method","fixed")
    coder=coder_for_profile(profile,modality)
    trace=Trace()
    record={"stage":"decode","direction":args.direction,"method":method,
            "profile_id":canonical_hash(profile),"model_id":profile[modality]["model_sha256"],
            "carrier":str(Path(args.carrier)),"output":str(Path(args.output)),
            "input_roles":["carrier","profile","context","key"],"input_files":[p.name for p in inputs],
            "packet_complete":False,"authenticated":False,"carrier_complete":False,
            "failure_stage":None,"failure_reason":None}
    model=None; emitted=0; packet_stop=None; phase="backend"; started=time.monotonic()
    try:
        if modality=="text":
            from .text_backend import TextBackend
            model=TextBackend(profile); symbols=model.reconstruct(Path(args.carrier).read_bytes())
            cap,expected_kind=2048,GRAYSCALE
        else:
            from .image_backend import ImageBackend,read_png
            pixels=read_png(args.carrier); symbols=pixels.reshape(-1).tolist()
            record["pixel_sha256"]=hashlib.sha256(pixels.tobytes()).hexdigest()
            model=ImageBackend(profile); cap,expected_kind=2976,TEXT
        record["cold_load_seconds"]=model.load_seconds
        begin=time.monotonic(); model.start(context); phase="replay"
        for position,symbol in enumerate(symbols):
            ids,q,order=model.distribution()
            if int(symbol) not in ids: raise ValueError("ineligible observed symbol at position "+str(position))
            if coder.done:
                role="completion"; carrying=0
            else:
                step=coder.prepare(ids,q,order)
                carrying=coder.consume(step,int(symbol))
                role="skipped" if method=="gated" and not carrying else "packet"
            trace.observe(ids,q,order,int(symbol),role,carrying,model)
            model.observe(int(symbol)); emitted+=1
            if coder.done and packet_stop is None:
                packet_stop=emitted; record["packet_complete"]=True; phase="authentication_and_parsing"
                payload=open_packet(coder.packet(),key,expected_kind)
                record.update({"authenticated":True,"payload_bytes":len(payload.data),"width":payload.width,"height":payload.height})
                output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
                with output.open("xb") as stream: stream.write(payload.data)
                record["recovered_sha256"]=hashlib.sha256(payload.data).hexdigest()
                phase="completion_conformance"
            if emitted%128==0: print("replayed",emitted,"packet bits",min(len(coder.bits),2336),flush=True)
        record["decode_seconds"]=time.monotonic()-begin
        if modality=="text":
            record.update({"tokens":len(symbols),"filter_seconds":model.filter_seconds})
        else:
            record.update({"pixels":992,"channels":len(symbols)})
        if not coder.done:
            phase="capacity" if len(symbols)==cap else "truncation"
            raise ValueError("packet incomplete in delivered symbols; no endpoint flush")
        if modality=="text" and len(symbols)!=packet_stop+32:
            phase="capacity" if len(symbols)==cap and packet_stop+32>cap else "completion_conformance"
            raise ValueError("incorrect required 32-token completion")
        if modality=="image" and len(symbols)!=2976: raise ValueError("incorrect full-canvas completion")
        record.update({"carrier_complete":True,"model_calls":model.calls})
    except Exception as exc:
        record.update({"failure_stage":phase,"failure_reason":type(exc).__name__+": "+str(exc),
                       "failure_position":emitted})
        traceback.print_exc()
    finally:
        record.update({"packet_complete":coder.done,"packet_stop":packet_stop,
                       "completion_symbols":emitted-packet_stop if packet_stop is not None else 0,
                       "packet_bits_recovered":min(len(coder.bits),2336),"coder_diagnostics":coder.diagnostics(),
                       "diagnostics":trace.summary(),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        for name in ("packet_positions","skipped_positions","zero_bit_positions","termination_positions",
                     "termination_suffix_bits","lookahead_zero_bits"):
            record[name]=getattr(coder,name)
        if model is not None:
            record["gpu_evidence"]=model.evidence; record["model_calls"]=model.calls; model.close()
        record["total_seconds"]=time.monotonic()-started
        json_write(args.report,record); print(json.dumps(record),flush=True)
    if record["authenticated"] and record["carrier_complete"]: return 0
    return 2 if record["failure_stage"]=="capacity" else 1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("direction",choices=["image-to-text","text-to-image"])
    for name in ("carrier","profile","context","key","output","report"):
        parser.add_argument("--"+name,required=True)
    raise SystemExit(receive(parser.parse_args()))


if __name__=="__main__":
    main()
