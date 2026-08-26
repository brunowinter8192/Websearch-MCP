## Live focus-steal probe (20260826T212711Z)
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
- Instrument 1 (frontmost app): 8 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 8 samples, 6 deviations, longest continuous deviation 9.76s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 1.449s, max gap 7.8s, effective rate ~0.69 samples/s
- Instrument 2: mean interval 1.449s, max gap 7.88s, effective rate ~0.69 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 8)
NONE

## Instrument 2 — deviation offsets (6 of 8)
t=5.07s, t=5.45s, t=5.81s, t=6.19s, t=6.57s, t=6.95s

## Instrument 1 — full sample series
- t=4.74s: ghostty
- t=5.11s: ghostty
- t=5.53s: ghostty
- t=5.9s: ghostty
- t=6.29s: ghostty
- t=6.68s: ghostty
- t=7.08s: ghostty
- t=14.88s: ghostty

## Instrument 2 — full sample series
- t=4.69s: False
- t=5.07s: True
- t=5.45s: True
- t=5.81s: True
- t=6.19s: True
- t=6.57s: True
- t=6.95s: True
- t=14.83s: False
