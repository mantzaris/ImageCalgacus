"""Fresh-process artifact receiver; no sender/evaluator/reference imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time
import traceback
from .packet import open_packet, TEXT, GRAYSCALE
from .coders import coder_for_profile, Trace
from .runtime import read_profile, json_write, canonical_hash


def receive(args, arithmetic_observer=None):
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
    if args.direction != "image-to-text" and "development_text_filter" in profile:
        raise ValueError("text-filter option is only for the development text comparison")
    context,key=Path(args.context).read_bytes(),Path(args.key).read_bytes()
    if len(key)!=32: raise ValueError("wrong key length")
    modality="text" if args.direction=="image-to-text" else "image"
    method=profile.get("coder",{}).get("method","fixed")
    if arithmetic_observer is not None and method != "arithmetic":
        raise ValueError("interval diagnostics require the A1 arithmetic profile")
    coder=coder_for_profile(profile,modality)
    trace=Trace()
    record={"stage":"decode","direction":args.direction,"method":method,
            "profile_id":canonical_hash(profile),"model_id":profile[modality]["model_sha256"],
            "text_filter_arm":profile.get("development_text_filter","sequence") if modality=="text" else None,
            "carrier":str(Path(args.carrier)),"output":str(Path(args.output)),
            "input_roles":["carrier","profile","context","key"],"input_files":[p.name for p in inputs],
            "packet_complete":False,"authenticated":False,"carrier_complete":False,
            "failure_stage":None,"failure_reason":None}
    model=None; emitted=0; packet_stop=None; phase="backend"; started=time.monotonic(); begin=None
    try:
        if modality=="text":
            from .text_backend import TextBackend
            model=TextBackend(profile)
            record["cold_load_seconds"]=model.load_seconds
            phase="artifact_parsing"
            symbols=model.reconstruct(Path(args.carrier).read_bytes())
            cap,expected_kind=2048,GRAYSCALE
        else:
            from .image_backend import ImageBackend,read_png
            pixels=read_png(args.carrier); symbols=pixels.reshape(-1).tolist()
            record["pixel_sha256"]=hashlib.sha256(pixels.tobytes()).hexdigest()
            model=ImageBackend(profile); cap,expected_kind=2976,TEXT
        record["cold_load_seconds"]=model.load_seconds
        record["parsed_symbol_count"]=len(symbols)
        begin=time.monotonic(); model.start(context); phase="replay"
        for position,symbol in enumerate(symbols):
            ids,q,order=model.distribution()
            if int(symbol) not in ids: raise ValueError("ineligible observed symbol at position "+str(position))
            if coder.done:
                role="completion"; carrying=0
            else:
                step=coder.prepare(ids,q,order)
                if arithmetic_observer is not None:
                    previous=(coder.lower,coder.upper,len(coder.bits))
                carrying=coder.consume(step,int(symbol))
                if arithmetic_observer is not None:
                    arithmetic_observer(coder,step,int(symbol),previous)
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
        if begin is not None and "decode_seconds" not in record:
            record["decode_seconds"]=time.monotonic()-begin
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
    parser.add_argument("--private-arithmetic-trace",help="diagnostic output under ignored .runtime/; contains recovered packet bits")
    args=parser.parse_args()
    if args.private_arithmetic_trace:
        from .runtime import ROOT
        trace_path=Path(args.private_arithmetic_trace).resolve()
        if not trace_path.is_relative_to(ROOT/".runtime") or trace_path.parent==Path(args.carrier).resolve().parent:
            parser.error("private trace must be outside inputs and under ignored .runtime/")
        trace_path.parent.mkdir(parents=True,exist_ok=True)
        # Copy state AFTER unchanged consume; no sender/evaluator input or extra model call.
        with os.fdopen(os.open(trace_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as stream:
            def observe(coder,step,symbol,previous):
                lower,upper,before=previous
                item={"position":coder.positions,"lower":lower,"upper":upper,
                      "next_lower":coder.lower,"next_upper":coder.upper,
                      "bits_before":before,"emitted":coder.bits[before:],
                      "symbol":symbol,"lookahead_zero_bits":coder.lookahead_zero_bits,
                      "done":coder.done,"termination_suffix_bits":coder.termination_suffix_bits,
                      **{name:step[name].tolist() for name in ("ids","q","order","symbols","cdf")},
                      "partition_diagnostic":step["diagnostic"]}
                stream.write(json.dumps(item,allow_nan=False)+"\n")
            status=receive(args,arithmetic_observer=observe)
    else:
        status=receive(args)
    raise SystemExit(status)


if __name__=="__main__":
    main()
