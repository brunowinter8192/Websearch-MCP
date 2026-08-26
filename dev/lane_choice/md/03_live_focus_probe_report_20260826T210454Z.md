## Live focus-steal probe (20260826T210454Z)
- Lane: camoufox
- URL: https://example.com
- Command: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/venv/bin/python /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/cli.py scrape_url_camoufox https://example.com
- Worktree root: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe
- Countdown given before launch: 10s
- Baseline (expected) frontmost app: `ghostty`
- Instrument 2 target app (AXMain/key-window): `Camoufox`
- Nominal poll interval (sleep() argument, NOT the real cadence — see resolution below): 0.25s
- Subprocess exit code: 0
- Wall time (browser launch to subprocess exit): 7.7s

## Verdict
- Instrument 1 (frontmost app): 13 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 12 samples, 10 deviations, longest continuous deviation 8.37s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 0.987s, max gap 4.96s, effective rate ~1.01 samples/s
- Instrument 2: mean interval 0.795s, max gap 4.93s, effective rate ~1.26 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 13)
NONE

## Instrument 2 — deviation offsets (10 of 12)
t=3.59s, t=3.96s, t=4.36s, t=4.74s, t=5.11s, t=5.48s, t=5.87s, t=6.28s, t=6.65s, t=7.03s

## Instrument 1 — full sample series
- t=0.18s: ghostty
- t=3.27s: ghostty
- t=3.64s: ghostty
- t=4.02s: ghostty
- t=4.41s: ghostty
- t=4.78s: ghostty
- t=5.15s: ghostty
- t=5.53s: ghostty
- t=5.92s: ghostty
- t=6.31s: ghostty
- t=6.69s: ghostty
- t=7.06s: ghostty
- t=12.02s: ghostty

## Instrument 2 — full sample series
- t=3.22s: False
- t=3.59s: True
- t=3.96s: True
- t=4.36s: True
- t=4.74s: True
- t=5.11s: True
- t=5.48s: True
- t=5.87s: True
- t=6.28s: True
- t=6.65s: True
- t=7.03s: True
- t=11.96s: False
