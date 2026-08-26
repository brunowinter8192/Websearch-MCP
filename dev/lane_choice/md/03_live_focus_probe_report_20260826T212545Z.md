## Live focus-steal probe (20260826T212545Z)
- Lane: camoufox
- URL: https://example.com
- Command: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/venv/bin/python /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/cli.py scrape_url_camoufox https://example.com
- Worktree root: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe
- Countdown given before launch: 10s
- Baseline (expected) frontmost app: `ghostty`
- Instrument 2 target app (AXMain/key-window): `Camoufox`
- Nominal poll interval (sleep() argument, NOT the real cadence — see resolution below): 0.25s
- Subprocess exit code: 0
- Wall time (browser launch to subprocess exit): 10.5s

## Verdict
- Instrument 1 (frontmost app): 10 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 9 samples, 6 deviations, longest continuous deviation 5.35s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 1.501s, max gap 4.38s, effective rate ~0.67 samples/s
- Instrument 2: mean interval 1.141s, max gap 3.47s, effective rate ~0.88 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 10)
NONE

## Instrument 2 — deviation offsets (6 of 9)
t=4.84s, t=5.2s, t=5.57s, t=5.95s, t=6.32s, t=6.72s

## Instrument 1 — full sample series
- t=0.14s: ghostty
- t=4.52s: ghostty
- t=4.89s: ghostty
- t=5.28s: ghostty
- t=5.71s: ghostty
- t=6.1s: ghostty
- t=6.48s: ghostty
- t=6.87s: ghostty
- t=10.25s: ghostty
- t=13.65s: ghostty

## Instrument 2 — full sample series
- t=4.46s: False
- t=4.84s: True
- t=5.2s: True
- t=5.57s: True
- t=5.95s: True
- t=6.32s: True
- t=6.72s: True
- t=10.19s: False
- t=13.59s: False
