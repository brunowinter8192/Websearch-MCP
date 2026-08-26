## Live focus-steal probe (20260826T213513Z)
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
- Instrument 1 (frontmost app): 9 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 8 samples, 6 deviations, longest continuous deviation 5.27s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 1.255s, max gap 4.39s, effective rate ~0.8 samples/s
- Instrument 2: mean interval 0.809s, max gap 3.42s, effective rate ~1.24 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 9)
NONE

## Instrument 2 — deviation offsets (6 of 8)
t=4.87s, t=5.24s, t=5.61s, t=5.98s, t=6.35s, t=6.72s

## Instrument 1 — full sample series
- t=0.14s: ghostty
- t=4.53s: ghostty
- t=4.91s: ghostty
- t=5.28s: ghostty
- t=5.65s: ghostty
- t=6.03s: ghostty
- t=6.39s: ghostty
- t=6.76s: ghostty
- t=10.18s: ghostty

## Instrument 2 — full sample series
- t=4.48s: False
- t=4.87s: True
- t=5.24s: True
- t=5.61s: True
- t=5.98s: True
- t=6.35s: True
- t=6.72s: True
- t=10.14s: False
