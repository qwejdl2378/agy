#!/bin/zsh
# Wait until the backend passes 2 consecutive health checks (15 min apart), then run rerun.sh.
S=${0:A:h}; R=${1:?round}; REPS=${2:-1}; streak=0
for i in {1..40}; do
  if $S/tools/health.sh >> $S/runs/$R.status; then (( streak++ )); else streak=0; fi
  (( streak >= 2 )) && { echo "$(date '+%F %T') healthy, starting" >> $S/runs/$R.status; exec $S/rerun.sh $R $REPS; }
  sleep $(( streak ? 120 : 900 ))
done
