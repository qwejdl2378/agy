#!/bin/zsh
# Exit 0 if agy answers a trivial prompt successfully within 90s and no try in that request hit 502/503.
cd $(mktemp -d) || exit 1
out=$(/Applications/magpie.app/Contents/MacOS/magpie agy run -p "只回复 OK" --effort high --output-format json --print-timeout 120s 2>/dev/null)
ok=$(print -r -- "$out" | python3 -c "import json,sys;d=json.load(sys.stdin);print(int(d['status']=='SUCCESS' and d['duration_seconds']<90))" 2>/dev/null)
f=$(ls -t ~/.config/magpie/routing/*.jsonl | head -1)
bad=$(tail -1 $f | python3 -c "import json,sys;d=json.loads(sys.stdin.read());print(sum(t.get('status') in (502,503) for t in d.get('tries',[])))" 2>/dev/null)
echo "$(date '+%T') health ok=$ok bad_tries=$bad"
[[ $ok == 1 && $bad == 0 ]]
