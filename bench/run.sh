#!/bin/zsh
# Run one probe once with agy.  usage: run.sh <round> <probe> <rep>
# Output: runs/<round>/<probe>-<rep>/ (workspace), .json (agy result), .err
# A turn killed by a transient backend error (403/429/502/503/timeout) is resumed in the same
# conversation instead of restarting, so finished work is kept. Usage/duration are summed.
S=${0:A:h}; R=$1; P=$2; N=$3; $S/setup.sh
D=$S/runs/$R/$P-$N; rm -rf $D $D.part*(N); mkdir -p $D
[[ -d $S/probes/$P/seed ]] && cp -R $S/probes/$P/seed/. $D/
cd $D && git init -q && git add -A && git -c user.name=bench -c user.email=bench@local commit -qm seed --allow-empty
AGY=( ${=AGY_BIN:-/Applications/magpie.app/Contents/MacOS/magpie agy} run --effort ${AGY_EFFORT:-high} --mode accept-edits
      --output-format json --print-timeout ${AGY_TIMEOUT:-3600s} )
envv=( AGY_PROBE=$R/$P-$N AGY_ADB_LOG=$S/runs/$R/adb.log PATH=$S/tools/shim:$PATH )
env $envv $AGY -p "$(cat $S/probes/$P/prompt.txt)" > $D.json 2> $D.err
for k in {1..6}; do
  cid=$(python3 - $D.json <<'PY'
import json, re, sys
try: d = json.load(open(sys.argv[1]))
except Exception: sys.exit()
if d.get("status") != "SUCCESS" and d.get("conversation_id") and re.search(
        r"403|429|502|503|UNAVAILABLE|PERMISSION_DENIED|ECONNRESET|EOF|capacity|print timeout|quota", d.get("error", ""), re.I):
    print(d["conversation_id"])
PY
)
  [[ -z $cid ]] && break
  sleep 90
  mv $D.json $D.part$k.json; cat $D.err >> $D.part.err
  env $envv $AGY --conversation $cid -p "上一轮因服务端错误中断。请检查当前工作区状态，从中断处继续完成原任务，不要重做已完成的部分。" > $D.json 2> $D.err
done
python3 - $D <<'PY'
import json, glob, sys
D = sys.argv[1]; parts = sorted(glob.glob(D + ".part*.json"))
if parts:
    d = json.load(open(D + ".json")); d["resumed"] = len(parts)
    for p in parts:
        try: x = json.load(open(p))
        except Exception: continue
        d["duration_seconds"] = d.get("duration_seconds", 0) + x.get("duration_seconds", 0)
        for k, v in (x.get("usage") or {}).items(): d.setdefault("usage", {})[k] = d["usage"].get(k, 0) + v
    json.dump(d, open(D + ".json", "w"), ensure_ascii=False)
PY
echo "$R/$P-$N exit=$?"
