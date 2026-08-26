## Live focus-steal probe (20260826T213634Z)
- Lane: camoufox
- URL: https://example.com
- Command: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/venv/bin/python /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/cli.py scrape_url_camoufox https://example.com
- Worktree root: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe
- Countdown given before launch: 10s
- Baseline (expected) frontmost app: `ghostty`
- Instrument 2 target app (AXMain/key-window): `Camoufox`
- Nominal poll interval (sleep() argument, NOT the real cadence — see resolution below): 0.25s
- Subprocess exit code: 0
- Wall time (browser launch to subprocess exit): 7.9s

## Verdict
- Instrument 1 (frontmost app): 8 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 8 samples, 6 deviations, longest continuous deviation 5.25s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 0.809s, max gap 3.36s, effective rate ~1.24 samples/s
- Instrument 2: mean interval 0.807s, max gap 3.39s, effective rate ~1.24 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 8)
NONE

## Instrument 2 — deviation offsets (6 of 8)
t=5.08s, t=5.45s, t=5.82s, t=6.19s, t=6.56s, t=6.94s

## Instrument 1 — full sample series
- t=4.73s: ghostty
- t=5.12s: ghostty
- t=5.49s: ghostty
- t=5.86s: ghostty
- t=6.24s: ghostty
- t=6.64s: ghostty
- t=7.03s: ghostty
- t=10.39s: ghostty

## Instrument 2 — full sample series
- t=4.68s: False
- t=5.08s: True
- t=5.45s: True
- t=5.82s: True
- t=6.19s: True
- t=6.56s: True
- t=6.94s: True
- t=10.33s: False
