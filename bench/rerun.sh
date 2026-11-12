#!/bin/zsh
# Keep re-running a round (resume mode) until every run succeeded or 6 passes are used.
S=${0:A:h}; R=${1:?round}; REPS=${2:-1}
for pass in {1..6}; do
  $S/campaign.sh $R $REPS
  bad=$(python3 -c "import json,glob;print(sum(1 for f in glob.glob('$S/runs/$R/*.json') if json.load(open(f)).get('status')!='SUCCESS'))")
  echo "$(date '+%F %T') pass $pass: $bad runs not successful" >> $S/runs/$R.status
  (( bad == 0 )) && break
  sleep 300
done
