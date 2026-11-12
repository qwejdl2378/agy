# agy tuning progress (resume point for Claude)

Goal: find what agy (gemini-3.8-flash, effort high) is best at across coding / solution design / UI interaction design / daily tasks; tune GEMINI.md; publish rules + best practices.

Baseline rules: ~/.gemini/GEMINI.md (r13, UI-heavy, 17 KB). Old bench (r1–r13): SwiftUI/Compose only.

## Steps
- [x] 0. Repo push verified (2026-11-13)
- [x] 1. Build bench v2 (bench/probes/<id>/{prompt.txt,seed.sh,check.py}) across 4 categories
- [ ] 2. Baseline round v2-r0 with current GEMINI.md, 2 reps each
- [ ] 3. Analyse → strengths/weaknesses (docs/findings.md)
- [ ] 4. Tune GEMINI.md, rerun, iterate until stable
- [ ] 5. Publish GEMINI.md, docs/best-practices.md, skills/, bench/

## Log
- 2026-11-13 02:05 bench v2 committed (15 probes: c1-c3 coding, d1-d2 design, u1-u5 UI, t1-t5 daily). Baseline round `v2-r0` launched via `bench/campaign.sh v2-r0 2` (+ u5 separately). Backend was returning 503 "No capacity for gemini-3.8-flash-high"; campaign retries automatically. Check `bench/runs/v2-r0.status`; score with `python3 bench/tools/score.py v2-r0`.
- 2026-11-13 03:50 Root cause of 503s: `magpie agy models` had set agy's model to a bogus name, bypassing magpie routing. Restored with `magpie agy group/agy`. One routed account is now disabled by the provider — benchmark load reduced to AGY_JOBS=3, 1 rep. Restarted `v2-r0` (1 rep).
