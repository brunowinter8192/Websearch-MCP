# Live human focus-steal probe, a sampling-honesty fix, and a watchdog A/B measurement (2026-08-26)

Continues the `lane_choice` area (dev/lane_choice/ already hosts the dual-instrument focus-steal
harness, `02_focus_poll_smoke.py`, per its own DOCS.md scope) and draws on `process-docs/camoufox_lane/`
(the two-layer watchdog fix this session probes). Driving question: the existing automated harness
(`02_`) tallies deviations over a backfill subprocess, but nothing in this project let a HUMAN sitting
at the Mac watch a single real Camoufox launch live and judge for themselves whether their own focus
was actually stolen — a judgment call an automated tally alone cannot settle.

## New tool: `dev/lane_choice/03_live_focus_probe.py`

Launches ONE real scrape via this worktree's own `cli.py` directly — never the `websearch` PATH
wrapper, which the existing Gotcha (`dev/lane_choice/DOCS.md`) already documents as pinned to the
main repo and structurally blind to unmerged worktree changes. Concretely:
`WORKTREE_ROOT = Path(__file__).resolve().parents[2]`, then
`[WORKTREE_ROOT/"venv"/"bin"/"python", WORKTREE_ROOT/"cli.py", subcommand, url]` run with
`cwd=WORKTREE_ROOT` — `cli.py`'s own `sys.path.insert(0, ...)` then resolves every `src.*` import to
THIS worktree, never the main repo's currently-merged code.

Before launch, a 10s second-by-second countdown tells the human to switch to another application and
start typing — judged long enough for the read-then-act sequence (a 2-3s countdown was rejected as too
tight). During the run, both of `02_`'s instruments (frontmost-app poll, AXMain key-window poll) run
concurrently on background threads, reused via `importlib.util.spec_from_file_location` rather than
re-declared (same numbered-script-reuse pattern already established by
`dev/search_pipeline/00_single_query.py` importing `01_google_smoke.py`). Instrument 2's target app
name is resolved dynamically for whichever lane is under test (`--chromium` resolves the real
patchright chromium bundle name, same shape as `chromium_scrape.py`'s own resolution, duplicated here
rather than imported per this project's own small-mechanism-duplication precedent) — deliberately NOT
hardcoded to "Camoufox" always, so a `--chromium` run produces a same-shape (if expectedly
instrument-1-redundant) report row instead of an always-False no-op.

## Sampling-honesty fix

The first real self-run (camoufox, `https://example.com`) surfaced a review finding: 8-9 samples over
a 12.5s wall at a nominal `POLL_INTERVAL_S=0.25s` implied ~50 samples, not 8-9. Each sample pays a real
`osascript` subprocess round-trip the `sleep(0.25)` call doesn't account for — observed mean intervals
across runs this session ranged 0.4s to 1.5s, with max gaps up to ~5s. The original
`longest_continuous_run` added a hardcoded `+POLL_INTERVAL_S` per run, understating true dwell for a
run that closes on a later sample and, more importantly, letting a sparse 8-9-sample verdict read like
dense coverage.

Fix: a run that closes on a later non-deviating sample is now bounded by that sample's own real
timestamp (an honest fact — the deviation was gone by then, regardless of nominal cadence). A run still
open at series-end is extended by the mean gap actually observed in that series
(`sample_gaps`-derived), never a nominal constant. New `instrument_resolution_stats()` (sample count,
mean interval, max gap, effective rate) is now printed in the terminal verdict and written to the
report, next to every deviation count, with an explicit caveat that a 0-deviation line only covers the
span actually sampled. Verified via hand-computed pure-function cases (closed run, open run, empty
deviation — all matched) plus a real re-run.

## Three human verification runs: AXMain fires, human perceives nothing

Once the probe worked, the human ran it three consecutive times (reports:
`dev/lane_choice/md/03_live_focus_probe_report_2026082621{2545,2646,2711}Z.md`). Result: the human lost
NO focus at all across all three runs, while instrument 2 (AXMain) recorded 5-6 deviations per run,
consistently starting around t≈5.0s and spanning roughly 1.9s of observed samples (mean intervals
1.1-1.5s in these particular runs — sparse, per the sampling-honesty fix above). Instrument 1
(frontmost) recorded zero deviations in all three.

Two hypotheses to explain the gap between "AXMain fires" and "human perceives nothing":
- **A — watchdog genuinely winning:** `_key_window_steal_watchdog` polls every 0.25s vs. the probe's
  own ~1.1-1.5s observed cadence, so it could be reclaiming faster than either the human or the probe
  can perceive — the probe would only ever catch the flicker mid-reclaim, never a sustained steal.
- **B — phantom signal:** AXMain=true on a named process queried directly (not system-wide) may not
  imply the app was ever actually activated/foregrounded at all — the whole instrument-2 signal would
  then be structurally decoupled from real focus, and the watchdog would be reclaiming a state that was
  never a real steal to begin with.

## Throwaway watchdog A/B measurement (never merged)

To start discriminating, `_key_window_steal_watchdog`'s scheduling was disabled with the crudest
one-line change possible — no env var, no CLI flag, no permanent surface, per explicit instruction —
on this branch only: `_acquire_camoufox`'s `watchdog_task = asyncio.create_task(...)` line replaced
with `watchdog_task = None` (commit `b8b64e8`, message flagged DO NOT MERGE). Reverted to the exact
original line in the same session (commit `333ab79`); `git diff integration -- src/` was empty both
right after the revert and after committing it — the branch carries no net `src/` change.

One agent self-run against the disabled commit (`https://example.com`, report at
`03_live_focus_probe_report_20260826T213513Z.md`) measured 6 deviations, longest continuous deviation
5.27s, first offset at t=4.87s — statistically indistinguishable from the three watchdog-ENABLED human
runs above (5-6 deviations, ~5s span, starting ~t=5.0s each). Disabling the reclaim mechanism did not
visibly worsen the AXMain signal, which leans toward Hypothesis B — but this is a single non-human run
against a fast, static test page, not proof, and not the human's own live judgment with the watchdog
off.

## Open at entry time

- The human has not yet run the probe live with the watchdog disabled (the exact
  `git checkout b8b64e8 -- src/scraper/camoufox_scrape.py` / run / `git checkout HEAD --` cycle was
  handed over for that, not yet executed by a human as of this entry).
- Hypothesis A vs. B is undecided pending that live run.
- If Hypothesis B holds up, the two-layer watchdog fix (`process-docs/camoufox_lane/`) may be reacting
  to a signal that was never a real steal — worth revisiting `_is_key_window_owner`'s own semantics
  (does AXMain=true on a queried-by-name process require actual foreground activation, or can a
  background/occluded window hold it?) before any further tuning of the watchdog itself.
