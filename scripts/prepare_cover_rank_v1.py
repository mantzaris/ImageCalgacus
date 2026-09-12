"""Freeze deterministic BSDS cover selection and retained text assignments.
Downloads only the 26 selected JPEGs and provenance, never loads a model.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime,timezone
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from imagecalgacus.cover_rank import PROTOCOL
from imagecalgacus.packet import NewRun,Payload,TEXT
from imagecalgacus.runtime import ROOT,atomic_json,sha256_file,source_hash,apply_cover_rank_allowance,DEFAULT_PHASE_LIMITS,budget_state

REVIEW=ROOT/"artifacts/cover_rank_v1_review"
PRIVATE=ROOT/"runs/cover-rank-v1-001"
REV="a04b7c6c3a9f0ace74bf205c72a43d32e1c72722"

def main():
    if (REVIEW/"manifest.json").exists():
        raise SystemExit("Manifest exists. Continue retained packets; do not prepare another run.")
    REVIEW.mkdir(parents=True,exist_ok=True)
    # Snapshot accepted evidence and private histories before any new execution.
    protected={}
    for root in ("artifacts","runs",".runtime"):
        for p in sorted((ROOT/root).rglob("*")):
            if p.is_file() and not p.is_symlink() and REVIEW not in p.parents and PRIVATE not in p.parents and "cover_rank_v1" not in p.parts and p.name!="gpu.lock":
                protected[str(p.relative_to(ROOT))]=sha256_file(p)
    (ROOT/".runtime/cover_rank_v1").mkdir(parents=True,exist_ok=True)
    atomic_json(ROOT/".runtime/cover_rank_v1/preservation.json",protected)
    apply_cover_rank_allowance()
    run=NewRun(PRIVATE)
    profile0=json.loads((ROOT/"configs/v1_fixed.json").read_text())
    profile={"protocol":PROTOCOL,"gpu_uuid":profile0["gpu_uuid"],"image":profile0["image"]}
    atomic_json(ROOT/"configs/cover_rank_v1.json",profile)
    shutil.copyfile(ROOT/"configs/cover_rank_v1.json",REVIEW/"profile.json")
    sources=json.loads((ROOT/"data/qualification_v1/manifest.json").read_text())
    texts={p["id"]:p for p in sources["payloads"] if p["direction"]=="text-to-image"}
    tree=json.load(urllib.request.urlopen("https://api.github.com/repos/BIDS/BSDS500/git/trees/"+REV+"?recursive=1"))
    cache=ROOT/".runtime/cover_rank_v1/source_cache";cache.mkdir()
    readme=urllib.request.urlopen("https://raw.githubusercontent.com/BIDS/BSDS500/"+REV+"/README.md").read()
    (REVIEW/"BSDS_MIRROR_README.md").write_bytes(readme)
    groups=[];bindings={}
    for partition,count,split,prefix in (("train",6,"development","T"),("test",20,"heldout","HT")):
        paths=[x["path"] for x in tree["tree"] if "/images/"+partition+"/" in x["path"] and x["path"].endswith(".jpg")]
        selected=sorted(paths,key=lambda p:int(Path(p).stem))[:count]
        for i,path in enumerate(selected,1):
            ident=split+"-"+Path(path).stem
            folder=REVIEW/"cases"/ident;folder.mkdir(parents=True)
            url="https://raw.githubusercontent.com/BIDS/BSDS500/"+REV+"/"+path
            raw=urllib.request.urlopen(url).read()
            original=cache/(partition+"-"+Path(path).name);original.write_bytes(raw)
            with Image.open(original) as im:
                width,height=im.size
                if min(width,height)<256: raise ValueError("source too small; no substitution")
                box=((width-256)//2,(height-256)//2,(width-256)//2+256,(height-256)//2+256)
                crop=im.convert("RGB").crop(box)
                crop.save(folder/"cover.png",compress_level=6)
                pixel_hash=__import__("hashlib").sha256(np.asarray(crop).tobytes()).hexdigest()
            payload=texts[prefix+str(i)]
            text=ROOT/"data/qualification_v1"/payload["source"]
            if sha256_file(text)!=payload["file_sha256"]: raise ValueError("retained text changed")
            shutil.copyfile(text,folder/"source.txt")
            clear=Payload(TEXT,text.read_bytes()).validate()
            packet=run.encrypt(clear); packet_path=PRIVATE/(ident+".packet")
            packet_path.write_bytes(packet);packet_path.chmod(0o600)
            bindings[ident]={"packet":str(packet_path.relative_to(ROOT)),
                "packet_sha256":sha256_file(packet_path),"key":str((PRIVATE/"run.key").relative_to(ROOT)),
                "source_sha256":sha256_file(text),"coarse_source":str((folder/"cover.png").relative_to(ROOT))}
            groups.append({"id":ident,"split":split,"bsds_id":Path(path).stem,"partition":partition,
                "url":url,"original_sha256":sha256_file(original),"original_dimensions":[width,height],
                "crop_box":box,"cover":str((folder/"cover.png").relative_to(REVIEW)),
                "cover_sha256":sha256_file(folder/"cover.png"),"pixel_sha256":pixel_hash,
                "source":str((folder/"source.txt").relative_to(REVIEW)),"source_sha256":sha256_file(text),
                "source_bytes":len(clear.data),"text_id":payload["id"],"text_provenance":payload["provenance"],
                "arms":["model_rank","parity"],"work_ids":[ident+"-"+a for a in ("model_rank","parity")]})
    if len({g["pixel_sha256"] for g in groups})!=26: raise ValueError("duplicate canonical photographs")
    atomic_json(PRIVATE/"bindings.json",bindings)
    manifest={"schema":"cover-rank-study-v1","starting_revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        "created_utc":datetime.now(timezone.utc).isoformat(),"source_revision":REV,"source_manifest_sha256":sha256_file(ROOT/"data/qualification_v1/manifest.json"),
        "selection":"smallest numeric JPEG identifiers in train (6) and test (20), before outcomes; center crop floor offsets, RGB, no resize",
        "groups":groups,"execution_order":[w for g in groups for w in g["work_ids"]],
        "packet_pairing":"one fresh encryption per group, immutable packet shared across both arms",
        "checks":"first development group, both arms: original recovery, wrong key, one bit flip, PNG compression-9 pixel-preserving resave",
        "probe":"first development cover; tiles (0,0),(96,96),(224,224), exact reference/graph maps, conditional oracle",
        "metrics":{"psnr":"RGB pooled MSE, peak 255","ssim":"mean of 3 channel SSIMs; Gaussian sigma 1.5, 11x11 window, valid centers, population covariance, K1=.01,K2=.03, data_range=255"},
        "summaries":"paired descriptive means and ranges only; no new tests or detection analysis",
        "figures":"first three numeric held-out identifiers; absolute difference amplified 32x; first held-out text example",
        "budget_seconds":7200,"whole_project_seconds":144000,"history_seconds":{s:budget_state(s)[0] for s in DEFAULT_PHASE_LIMITS},
        "source_hash":source_hash(),"profile_sha256":sha256_file(REVIEW/"profile.json"),
        "failure_rule":"retain every attempt; stop on unexpected recovery, invariant, rank, GPU or budget failure; no replacement",
        "terms":"BIDS mirror January 2013 BSDS500 distribution. Attribution required by README to Arbelaez et al. TPAMI 2011. No explicit blanket image redistribution license found; photographs are not relicensed under project MIT. Local research/review derivatives only; author must confirm publication reuse permissions.",
        "no_selection_from_outputs":True}
    atomic_json(REVIEW/"manifest.json",manifest)
    print(json.dumps({"groups":len(groups),"carriers":52,"manifest_sha256":sha256_file(REVIEW/"manifest.json")}))
if __name__=="__main__":main()
