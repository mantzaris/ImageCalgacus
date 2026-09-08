"""Two predeclared shared ordinary controls after the pilot; bounded sequential GPU work."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from imagecalgacus.runtime import read_profile,run_budgeted,budget_state,json_write
rows=[]
for run in ("v1-pilot-001","v1-pilot-002"):
    rows.extend(json.loads(line) for line in (ROOT/"runs"/run/"results.jsonl").read_text().splitlines())
if len(rows)!=12 or len({r["work_id"] for r in rows})!=12:
    raise RuntimeError("complete pilot attempts required; no control-driven fixture selection")
lengths=sorted({r["tokens"] for r in rows if r["direction"]=="image-to-text"})
old=json.loads((ROOT/"runs/v1-pilot-001/midpilot_projection.json").read_text())
used,_=budget_state("v1")
future=sum(old["control_seconds_upper"].values())
estimate=used+1.25*future
if estimate>7200: raise RuntimeError("reserved control costs do not fit authorized V1 remainder")
json_write(ROOT/"artifacts/v1_review/control_budget_gate.json",{"spent_seconds":used,
    "control_upper_seconds":future,"future_reserve_seconds":.25*future,"projected_total_seconds":estimate,
    "hard_limit_seconds":7200,"predeclared_seeds":[4301,4302]})
profile=read_profile(ROOT/"configs/v1_fixed.json")
for modality,seed,count,name in (("text",4301,max(lengths),"prompt.txt"),("image",4302,2976,"row.rgb")):
    command=[profile[modality]["interpreter"],"-B","-m","imagecalgacus.ordinary",
        "--modality",modality,"--profile",str(ROOT/"configs/v1_fixed.json"),
        "--context",str(ROOT/"artifacts/v1_review/contexts"/name),"--seed",str(seed),
        "--symbols",str(count),"--purpose","control",
        "--output",str(ROOT/(".runtime/v1/controls/%s-%d"%(modality,seed)))]
    if modality=="text": command+=["--prefix-lengths",",".join(map(str,lengths))]
    status=run_budgeted(command,"control-"+modality+"-"+str(seed),stage="v1",
                         max_seconds=1.25*old["control_seconds_upper"][modality])
    if status: raise SystemExit(status)
