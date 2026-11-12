#!/bin/zsh
# Run one probe once with agy.  usage: run.sh <round> <probe> <rep>
# Output: runs/<round>/<probe>-<rep>/ (workspace), .json (agy result), .err
S=${0:A:h}; R=$1; P=$2; N=$3; $S/setup.sh
D=$S/runs/$R/$P-$N; rm -rf $D; mkdir -p $D
[[ -d $S/probes/$P/seed ]] && cp -R $S/probes/$P/seed/. $D/
cd $D && git init -q && git add -A && git -c user.name=bench -c user.email=bench@local commit -qm seed --allow-empty
env AGY_PROBE=$R/$P-$N AGY_ADB_LOG=$S/runs/$R/adb.log PATH=$S/tools/shim:$PATH \
  ${=AGY_BIN:-/Applications/magpie.app/Contents/MacOS/magpie agy} run -p "$(cat $S/probes/$P/prompt.txt)" \
  --effort ${AGY_EFFORT:-high} --mode accept-edits --output-format json --print-timeout ${AGY_TIMEOUT:-3600s} \
  > $D.json 2> $D.err
echo "$R/$P-$N exit=$?"
