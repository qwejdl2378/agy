#!/bin/zsh
# Run a full round; each run retries after quota renewal.  usage: campaign.sh <round> [reps=2] [probes...]
zmodload zsh/parameter
S=${0:A:h}; R=${1:?round}; REPS=${2:-2}; shift 2 2>/dev/null
PROBES=( ${@:-${(f)"$(ls $S/probes)"}} )
ST=$S/runs/$R.status; mkdir -p $S/runs/$R
cp ~/.gemini/GEMINI.md $S/runs/$R.GEMINI.md
log() { echo "$(date '+%F %T') $*" >> $ST; }
quota_hit() {  # agy failed because of quota/rate limiting (not a normal task failure)
  local st=$(python3 -c "import json;print(json.load(open('$1.json')).get('status'))" 2>/dev/null)
  [[ $st == SUCCESS ]] && return 1
  grep -qiE 'RESOURCE_EXHAUSTED|quota|429|rate.?limit|too many requests' $1.err $1.json 2>/dev/null
}
capacity_hit() {  # backend overloaded (503 / dropped streams): retry after a short pause
  local st=$(python3 -c "import json;print(json.load(open('$1.json')).get('status'))" 2>/dev/null)
  [[ $st == SUCCESS ]] && return 1
  grep -qiE 'No capacity|UNAVAILABLE|503|unexpected EOF|deadline|timed? ?out' $1.err $1.json 2>/dev/null || [[ ! -s $1.json ]]
}
one() {
  local p=$1 n=$2
  for attempt in {1..40}; do
    $S/run.sh $R $p $n >/dev/null
    if quota_hit $S/runs/$R/$p-$n; then
      local w=$(python3 $S/tools/quota_wait.py); log "$p-$n quota hit (attempt $attempt), sleeping ${w}s"; sleep $w
    elif capacity_hit $S/runs/$R/$p-$n; then
      log "$p-$n backend unavailable (attempt $attempt): $(tail -c 160 $S/runs/$R/$p-$n.err | tr '\n' ' ')"; sleep $((120 + RANDOM % 180))
    else
      log "$p-$n done ($(python3 -c "import json;d=json.load(open('$S/runs/$R/$p-$n.json'));print(d.get('status'),int(d.get('duration_seconds',0)))" 2>/dev/null))"; return
    fi
  done
  log "$p-$n gave up"
}
log "start probes=${PROBES[*]} reps=$REPS"
# At most $AGY_JOBS concurrent sessions: a busy backend sheds load with 503s, so more parallelism only adds retries.
for n in $(seq 1 $REPS); do for p in $PROBES; do
  [[ -s $S/runs/$R/$p-$n.json ]] && [[ $(python3 -c "import json;print(json.load(open('$S/runs/$R/$p-$n.json')).get('status'))" 2>/dev/null) == SUCCESS ]] && continue  # resume
  while (( ${#jobstates} >= ${AGY_JOBS:-4} )); do sleep 5; done
  one $p $n &
done; done; wait
python3 $S/tools/score.py $R > $S/runs/$R.score 2>&1
log "ALL DONE"
