## Live focus-steal probe (20260826T205950Z)
- Lane: camoufox
- URL: https://example.com
- Command: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/venv/bin/python /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe/cli.py scrape_url_camoufox https://example.com
- Worktree root: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/steal-probe
- Countdown given before launch: 10s
- Baseline (expected) frontmost app: `ghostty`
- Instrument 2 target app (AXMain/key-window): `Camoufox`
- Poll interval: 0.25s
- Subprocess exit code: 0
- Wall time (browser launch to subprocess exit): 12.5s

## Verdict
- Instrument 1 (frontmost app): 8 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 9 samples, 6 deviations, longest continuous deviation 2.15s

## Instrument 1 — deviation offsets (0 of 8)
NONE

## Instrument 2 — deviation offsets (6 of 9)
t=6.74s, t=7.11s, t=7.49s, t=7.87s, t=8.25s, t=8.64s

## Instrument 1 — full sample series
- t=6.41s: ghostty
- t=6.79s: ghostty
- t=7.2s: ghostty
- t=7.64s: ghostty
- t=8.03s: ghostty
- t=8.42s: ghostty
- t=8.82s: ghostty
- t=12.22s: ghostty

## Instrument 2 — full sample series
- t=6.36s: False
- t=6.74s: True
- t=7.11s: True
- t=7.49s: True
- t=7.87s: True
- t=8.25s: True
- t=8.64s: True
- t=12.16s: False
- t=15.57s: False
