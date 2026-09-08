"""Four predeclared ordinary traces; freeze medians before any stego pilot."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from imagecalgacus.entropy_coding import calibrate_median
from imagecalgacus.runtime import ROOT,read_profile,run_budgeted,json_write,canonical_hash,sha256_file

profile=read_profile(ROOT/"configs/v0.json")
equivalence=json.loads((ROOT/"runs/v1-text-equivalence-001/result.json").read_text())
if not equivalence.get("passed") or not equivalence.get("carrier_bytes_equal"):
    raise RuntimeError("GPU behavior equivalence must pass before calibration")
base=ROOT/".runtime/v1/calibration"
base.mkdir(parents=True,exist_ok=False)
records={}
for modality,seeds,count,context in [("text",[4101,4102],1024,"prompt.txt"),("image",[4201,4202],2976,"row.rgb")]:
    records[modality]=[]
    for seed in seeds:
        output=base/(modality+"-"+str(seed))
        command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.ordinary",
                 "--modality",modality,"--profile",str(ROOT/"configs/v0.json"),
                 "--context",str(ROOT/"artifacts/v0_review/contexts"/context),
                 "--seed",str(seed),"--symbols",str(count),"--purpose","calibration","--output",str(output)]
        status=run_budgeted(command,"calibration-"+modality+"-"+str(seed),stage="v1",max_seconds=600)
        if status: raise SystemExit(status)
        record=json.loads((output/"result.json").read_text())
        if not record["passed"]: raise RuntimeError("ordinary trace failed")
        records[modality].append(record)
settings={"scope":"small_development_pilot_not_full_qualification","ordinary_only":True,"steGo_outcomes_used":False,
          "traces":{m:[{"seed":r["seed"],"symbols":r["symbols"],"carrier_sha256":r["carrier_sha256"],
                        "profile_id":r["profile_id"],"context_sha256":r["context_sha256"]} for r in rs]
                    for m,rs in records.items()},
          "modalities":{m:calibrate_median([v for r in rs for v in r["entropies_bits"]]) for m,rs in records.items()}}
target=ROOT/"configs/v1_calibration.json"
if target.exists(): raise FileExistsError("calibration already frozen")
json_write(target,settings)
print(json.dumps(settings),flush=True)
