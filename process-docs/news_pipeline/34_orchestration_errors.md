# 34 — Orchestration errors + open items (session 2026-06-14)

Honest record of Opus-side process/orchestration mistakes this session, so next session learns from
them. THIS file is the process retrospective. All four
errors below are Opus's, not the workers' — the workers were plan-gated (every stage: plan → Opus review
→ Go) and implemented cleanly; the failures are in orchestration and verification.

## Error 1 — Kill-before-finalize → lost proxy economics
On the first sitemap dev-run, Opus told the worker to KILL the process when it stalled on the straggler
tail — before `logger.finalize()` ran. The 5 logging surfaces (B-per-proxy, fail/success) lived only in
the in-memory logger and were written ONLY at finalize() → all lost. Only the `.xml` mtimes survived
(wall-time, no economics).
- **Cause:** judged the stall "not worth waiting"; did not account for finalize() being the sole
  persistence point.
- **Consequence:** a full re-run was needed; it produced the streaming logger (kill-safe).
- **Lesson:** know WHERE a process persists its data before killing it.

## Error 2 — Under-specified run parameter (`--max_hours`) (64er run)
Opus gave the Stage-E "Go" without specifying `--max_hours`; the worker defaulted to 0.5h (30 min). With
a 60-min cooldown, a 30-min cap means wait-on-exhaustion can NEVER resume — the cap fires before any
cooled-down proxy becomes eligible again. Nonsensical for testing the sustained behavior.
- **Cause:** left a critical run parameter to the worker despite knowing the 60-min cooldown constant.
- **Lesson:** Opus sets run parameters itself when their correctness depends on known design constants.
  The cap MUST exceed the cooldown for a wait-and-resume test (ideally ≥2 cooldown cycles).

## Error 3 — Premature "bug" conclusion from a mid-run snapshot (64er run)
Opus sampled the live JSONL mid-run (59 ok, 761/3396 proxies tried) plus the worker's pessimistic status
("pool exhausted, cooldown-wait"), and concluded to the user: "premature exhaustion bug — 2635 eligible
untried, real bug." **This was WRONG.** The job actually completed **64/64 in 18.6 min** (per the final
`job.md`), well before the cap. The snapshot was a transient low; the loop refilled from the remaining
eligible proxies and finished normally.
- **Cause:** treated a mid-run snapshot + worker narration as a conclusion.
- **Lesson:** the truth is the final `job.md`, NOT mid-run worker narration — the worker's
  "exhausted/cooldown-wait" message did not match the outcome. Hypothesis ≠ conclusion: present a
  snapshot as a question and verify against the final artifact before calling "bug." (This error was
  caught and corrected within the same session, but only after it had been stated to the user as fact.)

## Error 4 — Verification rigor (stage reviews)
Stage reviews leaned on unit/mock tests (small, mocked time/provider). Those pass on code-shape but do
not exercise scale behavior; the 64er run was the first real scale test.
- **Lesson:** validate at scale before declaring "verified" — mock-smoke ≠ runtime-correctness.

## Real design note (not an error)
**Cap vs cooldown:** the safety cap must exceed the cooldown for the wait-and-resume path to ever run.
The 64er run completed in 18.6 min (< 60-min cooldown), so wait-and-resume was **never triggered** → it
remains UNTESTED.

## Open items for next session
- Run on the **22k backfill pool** (`--pool backfill`), **no safety parameters** (user direction).
- **Validate wait-and-resume** — still untested. Needs a run that actually exhausts the pool and waits
  out a cooldown (a longer run, or a deliberately small pool to force exhaustion within a testable window).
- Worker mid-run status narration is unreliable — rely on the end-of-job `job.md`.

## Result this session (for the record)
The box-janitor + sustained machine WORK: 64/64 sub-sitemaps fetched, 47,128 article URLs, mean inter-hit
17.7s / median 10.0s (right-skewed = the straggler tail, as expected), janitor produced `job.md` +
`cumulative_hits.png`. The errors above are about the PROCESS, not the final deliverable.
