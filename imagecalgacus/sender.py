"""Fresh encoding run or one immutable sender-prepared packet, GPU inference only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import time
import traceback
import numpy as np
from PIL import Image
from .packet import NewRun, Payload, TEXT, GRAYSCALE, open_packet
from .fixed_rank import ordinary_sample
from .coders import coder_for_profile, Trace
from .runtime import read_profile, json_write, canonical_hash, source_hash, sha256_file

def read_source(path, direction):
    path = Path(path)
    if direction == "image-to-text":
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode != "L" or image.size != (16, 16):
                raise ValueError("source must be a canonical 16x16 8-bit grayscale PNG")
            data = np.asarray(image, dtype=np.uint8).tobytes()
        return Payload(GRAYSCALE, data, 16, 16).validate()
    return Payload(TEXT, path.read_bytes()).validate()



def encode(args):
    profile = read_profile(args.profile)
    if args.direction != "image-to-text" and "development_text_filter" in profile:
        raise ValueError("text-filter option is only for the development text comparison")
    payload = read_source(args.source,args.direction)
    context = Path(args.context).read_bytes()
    prepared = getattr(args,"prepared_packet",None)
    if bool(prepared) != bool(getattr(args,"key",None)):
        raise ValueError("prepared packet and retained sender key must be supplied together")
    if prepared:
        packet = Path(prepared).read_bytes()
        key = Path(args.key).read_bytes()
        if open_packet(packet,key,payload.kind) != payload:
            raise ValueError("prepared immutable packet does not match sender's source")
        directory = Path(args.new_run)
        directory.mkdir(parents=True,exist_ok=False,mode=0o700)
        fd=os.open(directory/"run.key",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"wb") as stream: stream.write(key)
    else:
        run=NewRun(args.new_run); directory=run.directory
        packet=run.encrypt(payload)
    inbox=directory/"inbox"; inbox.mkdir(mode=0o700)
    shutil.copy2(directory/"run.key",inbox/"run.key")
    json_write(inbox/"profile.json",profile)
    context_name="prompt.txt" if args.direction=="image-to-text" else "row.rgb"
    (inbox/context_name).write_bytes(context)
    source_name="source.png" if args.direction=="image-to-text" else "source.txt"
    shutil.copyfile(args.source,directory/source_name)
    json_write(directory/"reference.json",{"kind":payload.kind,"bytes":len(payload.data),
               "sha256":hashlib.sha256(payload.data).hexdigest(),"source":source_name,
               "width":payload.width,"height":payload.height})
    modality="text" if args.direction=="image-to-text" else "image"
    method=profile.get("coder",{}).get("method","fixed")
    coder=coder_for_profile(profile,modality,packet)
    trace=Trace()
    result={"stage":"encode","direction":args.direction,"method":method,
            "profile_id":canonical_hash(profile),"source_hash":source_hash(),
            "text_filter_arm":profile.get("development_text_filter","sequence") if modality=="text" else None,
            "model_id":profile[modality]["model_sha256"],"packet_complete":False,"carrier_complete":False,
            "packet_bytes":292,"prepared_packet_sha256":hashlib.sha256(packet).hexdigest(),
            "failure_stage":None,"failure_reason":None}
    json_write(directory/"attempt.json",{"stage":"started","method":method})
    model=None; emitted=0; packet_stop=None; started=time.monotonic(); phase="backend"
    try:
        if modality=="text":
            from .text_backend import TextBackend
            model=TextBackend(profile); carrier=inbox/"carrier.txt"; cap=2048
        else:
            from .image_backend import ImageBackend
            model=ImageBackend(profile); carrier=inbox/"carrier.png"; cap=2976
        result["cold_load_seconds"]=model.load_seconds
        begin=time.monotonic(); model.start(context); phase="generation"
        rng=np.random.Generator(np.random.PCG64(profile["completion_seed"]))
        support_min=1000000
        for position in range(cap):
            ids,q,order=model.distribution()
            support_min=min(support_min,len(order))
            if coder.done:
                symbol=ordinary_sample(ids,q,rng); role="completion"; carrying=0
            else:
                step=coder.prepare(ids,q,order); symbol=coder.select(step,rng)
                carrying=coder.consume(step,symbol)
                role="skipped" if method=="gated" and not carrying else "packet"
            trace.observe(ids,q,order,symbol,role,carrying,model)
            model.observe(symbol); emitted+=1
            if coder.done and packet_stop is None: packet_stop=emitted
            if emitted%128==0: print("generated",emitted,"packet bits",min(len(coder.bits),2336),flush=True)
            if modality=="text" and packet_stop is not None and emitted==packet_stop+32: break
        phase="serialization"
        if modality=="text":
            carrier.write_bytes(model.serialize())
            result.update({"tokens":emitted,"filter_seconds":model.filter_seconds,
                           "serialization":getattr(model,"serialization_diagnostics",{})})
        else:
            from .image_backend import write_png
            write_png(carrier,model.canvas[1:])
            result.update({"pixels":992,"channels":2976,
                           "pixel_sha256":hashlib.sha256(model.canvas[1:].tobytes()).hexdigest()})
        complete=coder.done and (modality=="image" or emitted==packet_stop+32)
        result.update({"carrier":str(carrier),"carrier_bytes":carrier.stat().st_size,
                       "carrier_sha256":sha256_file(carrier),"artifact_saved":True,
                       "carrier_complete":complete,"encode_seconds":time.monotonic()-begin,
                       "support_minimum":support_min,"model_calls":model.calls})
        if not complete:
            result.update({"failure_stage":"capacity","failure_reason":"packet or required completion unfinished at fixed carrier cap"})
    except Exception as exc:
        failure_stage="support" if "insufficient eligible support" in str(exc) else phase
        result.update({"failure_stage":failure_stage,"failure_reason":type(exc).__name__+": "+str(exc)})
        traceback.print_exc()
        if model is not None:
            if modality=="text":
                try: (directory/"failed-prefix.txt").write_bytes(model.serialize())
                except Exception: pass
            else:
                np.save(directory/"failed-prefix.npy",model.canvas.reshape(-1)[:model.position])
    finally:
        result.update({"packet_complete":coder.done,"packet_stop":packet_stop,"emitted_symbols":emitted,
                       "completion_symbols":emitted-packet_stop if packet_stop is not None else 0,
                       "packet_bits_recovered":min(len(coder.bits),2336),"coder_diagnostics":coder.diagnostics(),
                       "diagnostics":trace.summary(),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        for name in ("packet_positions","skipped_positions","zero_bit_positions","termination_positions",
                     "termination_suffix_bits","lookahead_zero_bits"):
            result[name]=getattr(coder,name)
        if model is not None:
            result["gpu_evidence"]=model.evidence
            model.close()
        result["total_seconds"]=time.monotonic()-started
        json_write(directory/"sender.json",result)
        print(json.dumps(result),flush=True)
    if result["carrier_complete"]: return 0
    return 2 if result["failure_stage"] in {"capacity","support"} else 1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("direction",choices=["image-to-text","text-to-image"])
    parser.add_argument("--source",required=True)
    parser.add_argument("--profile",required=True)
    parser.add_argument("--context",required=True)
    parser.add_argument("--new-run",required=True)
    parser.add_argument("--prepared-packet",help="sender-only immutable encrypted packet")
    parser.add_argument("--key",help="sender-only retained key for the prepared packet")
    raise SystemExit(encode(parser.parse_args()))


if __name__=="__main__":
    main()
