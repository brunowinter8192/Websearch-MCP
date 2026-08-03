# Parallel-Chrome Collision Probe — 20260803_175741

Simulated already-running user Chrome (throwaway profile, foregrounded) + a production-shape headed-backgrounded launch attempt against the REAL production SESSION_DIR (`~/.websearch/browser-session`), while the simulated user Chrome is running.

## Result

- **Baseline Chrome running before probe:** True (any profile, any purpose — this machine may run unrelated headless automation under its own profile; that alone is not evidence of the user's own foreground browsing session)
- **Simulated user Chrome processes (its own profile) after spawn:** 8
- **Frontmost app after simulated user Chrome spawn:** Google Chrome
- **Frontmost app right before our launch attempt (re-focused to Terminal):** Terminal
- **Our backgrounded launch succeeded (CDP connected + tab drivable):** True
- **Connect latency (ms):** 1018
- **Drivable latency (ms):** 1024
- **Chrome processes pinned to SESSION_DIR during the run:** 7 (counts the main process plus its GPU/renderer/network-service children, which all inherit `--user-data-dir` — not a count of distinct browser instances)
- **Frontmost app immediately after our launch attempt:** Terminal
- **Focus stolen by our launch (frontmost became Google Chrome because of it):** False

## Teardown

- SESSION_DIR processes after teardown: 0
- Simulated-user-profile processes after teardown: 0
- **Clean teardown:** True

## Reading

- `open -g -n -a "Google Chrome" --args ... --user-data-dir=<SESSION_DIR>` DID reach a genuinely separate, distinctly-profiled Chrome process even with another Chrome instance already running under a different profile — `-n` + a distinct `--user-data-dir` forced a new instance rather than macOS `open` addressing the already-running one and dropping `--args`. CDP connected and the tab was drivable.
- No focus steal observed: frontmost app did not change to Google Chrome because of our launch. Instrumentation verified functional this run (a Finder-activation control changed frontmost as expected). Caveat: this session runs in an agent-driven execution context, not a fully interactive login session — the OS-level signal is real and verified working, but a human visual spot-check is the stronger confirmation for the visual/attention-stealing claim specifically (Verification Levels: rendered/visual correctness is the one thing self-checks cannot fully replace).