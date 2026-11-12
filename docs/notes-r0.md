# v2-r0 baseline notes (GEMINI.md r13, effort high)

Backend context: 2026-11-13 Antigravity backend degraded (median call 26s vs 7s on 11-10, many 502/503), so wall-clock times are inflated ~3x.

- c1-bugfix: 100. Found all 5 bugs incl. 2 only implied by the spec comment (half-up discount rounding, total ≥ 0) — spec-reading is good. Minimal diff, tests untouched, ran pytest + extra edge script. Summary followed the 5-part format; mild absolutist wording ("严格满足", "绝不").
