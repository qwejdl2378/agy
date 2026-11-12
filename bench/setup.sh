#!/bin/zsh
# Regenerate large/derived probe data (deterministic).
S=${0:A:h}
[[ -f $S/probes/t2-log/seed/app.log ]] || python3 $S/probes/t2-log/gen.py
