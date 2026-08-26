## Live focus-steal probe (20260826T212646Z)
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
- Instrument 1 (frontmost app): 8 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 8 samples, 5 deviations, longest continuous deviation 1.93s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 0.814s, max gap 3.3s, effective rate ~1.23 samples/s
- Instrument 2: mean interval 0.814s, max gap 3.4s, effective rate ~1.23 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 8)
NONE

## Instrument 2 — deviation offsets (5 of 8)
t=5.06s, t=5.43s, t=5.8s, t=6.18s, t=6.57s

## Instrument 1 — full sample series
- t=4.74s: ghostty
- t=5.12s: ghostty
- t=5.53s: ghostty
- t=5.95s: ghostty
- t=6.35s: ghostty
- t=6.74s: ghostty
- t=7.14s: ghostty
- t=10.44s: ghostty

## Instrument 2 — full sample series
- t=4.69s: False
- t=5.06s: True
- t=5.43s: True
- t=5.8s: True
- t=6.18s: True
- t=6.57s: True
- t=6.99s: False
- t=10.39s: False
