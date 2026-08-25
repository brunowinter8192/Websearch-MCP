# dev/lane_choice/

## Role
Calibration data collection for a coming lane-choice metrics feature: fires BOTH acquisition
lanes (chromium, camoufox) fresh against every distinct URL in the production scrape log, so a
future feature can compare them on equal, current footing (historical single-lane records are
config/site-drift stale). Also the focus-steal verification harness for both lanes, run around the
same backfill subprocess. Touch this directory when extending the backfill's own resume/report
shape or the focus-steal instrumentation; not the lane implementations themselves — those are
`src/scraper/chromium_scrape.py`/`camoufox_scrape.py`.

## Public Interface
No `__init__.py` — both scripts are standalone CLI entry points, run directly:
`./venv/bin/python dev/lane_choice/01_backfill_pairs.py [--limit N]` and
`./venv/bin/python dev/lane_choice/02_focus_poll_smoke.py [--limit N]` (wraps the former as a
subprocess).

## Flow
`01_backfill_pairs.py`: distinct URLs from the production `scrape_log.jsonl` → skip already-done
(url, engine) pairs in this dir's own resume-state JSONL → fire each remaining pair via the
production `websearch` CLI → read back its fresh log record → append to resume-state → md/ report.
`02_focus_poll_smoke.py`: launches `01_backfill_pairs.py` as a subprocess while polling two macOS
focus-steal instruments (frontmost-app, camoufox key-window/AXMain) concurrently on background
threads → md/ report with both instruments' tallies and any violation samples.

## Modules

### 01_backfill_pairs.py (274 LOC)

**Purpose:** Orchestration only — fires the production `websearch scrape_url_chromium`/
`scrape_url_camoufox` CLI per distinct URL, resumable via its own state file; never writes scrape
content itself (the CLI's own `scrape_log.jsonl`/sidecars do that).
**Reads:** production `scrape_log.jsonl` (hardcoded absolute path to the MAIN repo, never a
worktree copy — see Gotchas); this dir's own `jsonl/backfill_pairs_state.jsonl`.
**Writes:** `jsonl/backfill_pairs_state.jsonl` (appended per fired pair, resumable); `md/01_backfill_pairs_report_<ts>.md`.
**Called by:** `02_focus_poll_smoke.py` (as a subprocess); run directly for a bare backfill with no
focus-steal instrumentation.
**Calls out:** the `websearch` PATH command (subprocess) — see Gotchas.

### 02_focus_poll_smoke.py (193 LOC)

**Purpose:** Focus-steal verification gate for the backfill — two concurrent macOS instruments:
frontmost-app poll (catches a regular/non-accessory app's steal) and camoufox key-window (AXMain)
poll (catches an LSUIElement/accessory app's steal, which never registers as "frontmost" in the
first instrument's sense — instrument 1 alone is blind to it).
**Reads:** nothing of its own; launches `01_backfill_pairs.py` and reads its stdout/exit code.
**Writes:** `md/02_focus_poll_smoke_report_<ts>.md`.
**Called by:** run directly, ad hoc, whenever a lane's focus-steal posture needs re-verifying.
**Calls out:** the `websearch` PATH command indirectly (via `01_backfill_pairs.py`); macOS
`osascript`/System Events for both polls.

---

## State
`jsonl/backfill_pairs_state.jsonl` is the backfill's own resume state — one line per fired
(url, engine) pair, owned and appended-to exclusively by `01_backfill_pairs.py`; read (never
mutated) by nothing else in this package. `md/` holds every report ever produced by either script,
timestamped, never overwritten.

## Gotchas
- **The `websearch` command on PATH is pinned to the MAIN repo's `cli.py`, never a worktree.**
  `01_backfill_pairs.py`'s `WEBSEARCH_CMD = "websearch"` resolves via the shell PATH wrapper at
  `~/.local/bin/websearch`, which is a fixed shell script (`exec .../websearch/cli.py "$@"` against
  the main repo's own absolute path) — confirmed by reading the wrapper directly. This means
  **neither script in this directory can ever exercise an unmerged worktree's own `src/scraper/`
  changes** — every real launch runs the main repo's currently-merged code, regardless of which
  worktree these scripts themselves are edited/run from. Discovered concretely 2026-08-25: a
  2-URL `02_focus_poll_smoke.py` smoke run intended to verify a worktree-only camoufox focus-steal
  fix instead showed the OLD pre-fix behavior (sustained multi-second key-window steals) — traced
  to this wrapper, not a defect in the fix itself; direct verification required invoking the
  worktree's own `venv/bin/python cli.py <subcommand> <url>` in place of the `websearch` PATH
  command (see `process-docs/camoufox_lane/`). Do not treat an all-green
  `02_focus_poll_smoke.py` run as evidence about an unmerged worktree change — it only proves
  something about whatever is currently in the main repo.
- `PROD_SCRAPE_LOG_PATH` (`01_backfill_pairs.py`) is a hardcoded absolute path into the main repo's
  `src/logs/scrape_log.jsonl`, deliberately — worktrees have their own, separate, gitignored
  `src/logs/` tree, and the backfill's whole premise is enumerating URLs the MAIN repo has actually
  seen in production. Do not "fix" this to a relative/worktree-local path without re-deriving that
  premise first.
- `--limit N` selects the first N URLs of the FULL distinct-URL list, not "the next N unprocessed"
  — with M pairs already resumed/skipped, a smoke run needs `--limit (M/2 + desired_new_urls)` to
  actually fire new pairs rather than skip-looping through already-done ones (skips are near-instant,
  so a too-low limit just produces an empty-feeling report, not a hang).
