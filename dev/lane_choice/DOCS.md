# dev/lane_choice/

## Role
Calibration data collection for a coming lane-choice metrics feature: fires BOTH acquisition
lanes (chromium, camoufox) fresh against every distinct URL in the production scrape log, so a
future feature can compare them on equal, current footing (historical single-lane records are
config/site-drift stale). Also the focus-steal verification harness for both lanes: an automated
gate wrapped around the backfill subprocess (`02_`), and a live HUMAN probe for a single ad-hoc URL
(`03_`) — the human watches/types live while both instruments record independently, since a human
judgment call ("did my focus actually get stolen") is not something an automated tally alone
settles. Touch this directory when extending the backfill's own resume/report shape or the
focus-steal instrumentation; not the lane implementations themselves — those are
`src/scraper/chromium_scrape.py`/`camoufox_scrape.py`.

## Public Interface
No `__init__.py` — all three scripts are standalone CLI entry points, run directly:
`./venv/bin/python dev/lane_choice/01_backfill_pairs.py [--limit N]`,
`./venv/bin/python dev/lane_choice/02_focus_poll_smoke.py [--limit N]` (wraps the former as a
subprocess), and `./venv/bin/python dev/lane_choice/03_live_focus_probe.py [--url URL] [--chromium]`
(launches a single real scrape via THIS worktree's own `cli.py`, countdown first, for a human to
watch live).

## Flow
`01_backfill_pairs.py`: distinct URLs from the production `scrape_log.jsonl` → skip already-done
(url, engine) pairs in this dir's own resume-state JSONL → fire each remaining pair via the
production `websearch` CLI → read back its fresh log record → append to resume-state → md/ report.
`02_focus_poll_smoke.py`: launches `01_backfill_pairs.py` as a subprocess while polling two macOS
focus-steal instruments (frontmost-app, camoufox key-window/AXMain) concurrently on background
threads → md/ report with both instruments' tallies and any violation samples.
`03_live_focus_probe.py`: countdown (human switches app + starts typing) → launches one real
`cli.py scrape_url_camoufox`/`scrape_url_chromium` call directly (never the `websearch` PATH
wrapper) while polling the same two instruments concurrently → verdict printed to the terminal +
full sample series to md/.

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

### 03_live_focus_probe.py (353 LOC)

**Purpose:** Live HUMAN focus-steal verification for a single ad-hoc URL — launches ONE real scrape
via this worktree's own `cli.py` directly (bypasses the `websearch` PATH wrapper Gotcha below on
purpose, the whole reason this script exists), after a visible countdown so the human can switch
away and start typing, then reports what the two automated instruments (reused from `02_`) saw
during that same span. The verdict reports each instrument's own OBSERVED sampling resolution
(mean inter-sample interval, largest gap, effective rate) alongside its deviation count — the real
`osascript`-round-trip-bound cadence runs slower and less evenly than the nominal
`POLL_INTERVAL_S=0.25s` sleep alone would suggest (a live run measured mean intervals of
0.4-1.0s and gaps up to ~5s), so `longest_continuous_run` derives any open-run dwell estimate from
the samples' own observed gaps, never from the nominal constant, and both the terminal verdict and
the report say so explicitly.
**Reads:** nothing of its own; imports `02_focus_poll_smoke.py`'s instrument functions via
`importlib.util.spec_from_file_location` (filename starts with a digit, not `import`-able
directly); launches this worktree's own `cli.py` as a subprocess.
**Writes:** `md/03_live_focus_probe_report_<ts>.md` (full sample series, both instruments).
**Called by:** run directly, ad hoc, whenever a human needs to eyeball a lane's live focus posture
(as opposed to `02_`'s automated tally over the backfill).
**Calls out:** this worktree's own `venv/bin/python cli.py` (subprocess, real production entry
point); `patchright.async_api` (chromium bundle-name resolution for `--chromium` runs); macOS
`osascript`/System Events (via the imported `02_` functions).

---

## State
`jsonl/backfill_pairs_state.jsonl` is the backfill's own resume state — one line per fired
(url, engine) pair, owned and appended-to exclusively by `01_backfill_pairs.py`; read (never
mutated) by nothing else in this package. `md/` holds every report ever produced by any of the
three scripts, timestamped, never overwritten.

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
  something about whatever is currently in the main repo. `03_live_focus_probe.py` builds this
  worktree-direct invocation in from the start (`WORKTREE_ROOT = Path(__file__).resolve().parents[2]`,
  never `WEBSEARCH_CMD`) — it is the one script here safe to use for verifying an unmerged change.
- **`03_live_focus_probe.py`'s instrument-2 target is dynamic, not always "Camoufox".** It targets
  whichever lane is actually launched (`--chromium` resolves the real chromium bundle name via
  `patchright`, same as `chromium_scrape.py`'s own resolution). Chromium is a regular,
  non-accessory app already caught by instrument 1 (frontmost), so a `--chromium` run's instrument-2
  numbers are expected to be structurally redundant with instrument 1's — that is not a bug, only an
  LSUIElement accessory process (Camoufox) is where instrument 1 is structurally blind.
- `PROD_SCRAPE_LOG_PATH` (`01_backfill_pairs.py`) is a hardcoded absolute path into the main repo's
  `src/logs/scrape_log.jsonl`, deliberately — worktrees have their own, separate, gitignored
  `src/logs/` tree, and the backfill's whole premise is enumerating URLs the MAIN repo has actually
  seen in production. Do not "fix" this to a relative/worktree-local path without re-deriving that
  premise first.
- `--limit N` selects the first N URLs of the FULL distinct-URL list, not "the next N unprocessed"
  — with M pairs already resumed/skipped, a smoke run needs `--limit (M/2 + desired_new_urls)` to
  actually fire new pairs rather than skip-looping through already-done ones (skips are near-instant,
  so a too-low limit just produces an empty-feeling report, not a hang).
- **`03_live_focus_probe.py` has no built-in way to disable `_key_window_steal_watchdog` for an A/B
  measurement, and must never get one (no env var, no CLI flag — that would be a permanent surface
  for a temporary question).** The proven throwaway technique (2026-08-26,
  `process-docs/lane_choice/`): a single-line `src/scraper/camoufox_scrape.py` edit on a
  never-merged branch (`watchdog_task = None` in place of the `asyncio.create_task(...)` line in
  `_acquire_camoufox`), committed alone, run against, then reverted in the SAME session so the
  branch ends with an empty `git diff integration -- src/`. Do not leave that disable commit
  un-reverted, and do not merge it.
