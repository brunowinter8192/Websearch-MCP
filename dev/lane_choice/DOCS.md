# dev/lane_choice/

## Role
Calibration data collection for a coming lane-choice metrics feature: fires BOTH acquisition
lanes (chromium, camoufox) fresh against every distinct URL in the production scrape log, so a
future feature can compare them on equal, current footing (historical single-lane records are
config/site-drift stale). Also the focus-steal verification harness for both lanes: an automated
gate wrapped around the backfill subprocess (`02_`), and a live HUMAN probe for one or more ad-hoc
URLs (`03_`) — the human watches/types live while a frontmost-app instrument records independently,
since a human judgment call ("did my focus actually get stolen") is not something an automated
tally alone settles. As of 2026-08-27, a second (AXMain/key-window) instrument that used to run
alongside the frontmost-app one was removed from both scripts — live human-judged runs, including
against 5 real URLs sequentially under sustained load, found that signal fires constantly with ZERO
perceived focus loss, a phantom signal carrying no information about real focus (see
`process-docs/camoufox_lane/`). Also the content/boilerplate metrics report (`04_`) over an already-
produced batch of paired backfill outputs — a mechanical Kohlschuetter Algorithm 2 classifier plus
the jusText heading rescue, reporting per-lane content-word/block counts with no verdict on which
lane is better. Touch this directory when extending the backfill's own resume/report shape, the
focus-steal instrumentation, or the content-metrics classifier/report shape; not the lane
implementations themselves — those are `src/scraper/chromium_scrape.py`/`camoufox_scrape.py`.

## Public Interface
No `__init__.py` — all four scripts are standalone CLI entry points, run directly:
`./venv/bin/python dev/lane_choice/01_backfill_pairs.py [--limit N]`,
`./venv/bin/python dev/lane_choice/02_focus_poll_smoke.py [--limit N]` (wraps the former as a
subprocess), `./venv/bin/python dev/lane_choice/03_live_focus_probe.py [--url URL ...] [--chromium]`
(`--url` may repeat; one countdown up front, then one fresh-browser scrape per URL back-to-back via
THIS worktree's own `cli.py`, for a human to watch live), and
`./venv/bin/python dev/lane_choice/04_lane_metrics.py` (no flags; fixed input path, see Gotchas).

## Flow
`01_backfill_pairs.py`: distinct URLs from the production `scrape_log.jsonl` → skip already-done
(url, engine) pairs in this dir's own resume-state JSONL → fire each remaining pair via the
production `websearch` CLI → read back its fresh log record → append to resume-state → md/ report.
`02_focus_poll_smoke.py`: launches `01_backfill_pairs.py` as a subprocess while polling a macOS
frontmost-app instrument on a background thread → md/ report with its tally and any violation
samples.
`03_live_focus_probe.py`: one countdown (human switches app + starts typing) → for each `--url` in
order, one real `cli.py scrape_url_camoufox`/`scrape_url_chromium` call directly (never the
`websearch` PATH wrapper), each URL its own fresh browser, back-to-back, launch span recorded per
URL → the same frontmost-app instrument polls continuously across the whole sequence → overall +
per-URL verdict printed to the terminal + full sample series to md/.
`04_lane_metrics.py`: fixed `/tmp/lane_pairs_20.json` pairs list → per URL, per lane, its
scrape_content `.md` read once → block classification (Algorithm 2 tree + heading rescue) → per-lane
metrics → per-URL lines + one 20-URL table + aggregate win/disagreement counts, written to md/.

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

### 02_focus_poll_smoke.py (127 LOC)

**Purpose:** Focus-steal verification gate for the backfill — a macOS frontmost-app poll (catches a
regular/non-accessory app's steal). REMOVED 2026-08-27: a second, LSUIElement/accessory-process
key-window instrument that used to run alongside it — proven a phantom signal by live human-judged
runs against the original complaint's own sustained-load, multi-URL workload shape (see
`process-docs/camoufox_lane/`), not just the launch-time-only signal it looked like on the smaller
`example.com` runs that motivated it.
**Reads:** nothing of its own; launches `01_backfill_pairs.py` and reads its stdout/exit code.
**Writes:** `md/02_focus_poll_smoke_report_<ts>.md`.
**Called by:** run directly, ad hoc, whenever a lane's focus-steal posture needs re-verifying.
**Calls out:** the `websearch` PATH command indirectly (via `01_backfill_pairs.py`); macOS
`osascript`/System Events for the poll.

### 03_live_focus_probe.py (364 LOC)

**Purpose:** Live HUMAN focus-steal verification for one or more ad-hoc URLs — one visible countdown
so the human can switch away and start typing, then a real scrape per `--url` (repeatable) via this
worktree's own `cli.py` directly (bypasses the `websearch` PATH wrapper Gotcha below on purpose, the
whole reason this script exists), each URL its own fresh browser, back-to-back, no countdown between
them — the workload shape of the original sustained-load complaint (one fresh Camoufox per scraped
URL across a backfill), not just an isolated single launch. The frontmost-app instrument (reused
from `02_`) polls continuously across the WHOLE sequence, not per URL, so `run_urls_in_sequence`
records each URL's own launch span (elapsed seconds since the countdown ended) and
`compute_per_url_verdicts` slices the one continuous sample series back down per URL afterwards. The
verdict (both the pooled whole-sequence one and each per-URL one) reports the instrument's own
OBSERVED sampling resolution (mean inter-sample interval, largest gap, effective rate) alongside its
deviation count — the real `osascript`-round-trip-bound cadence runs slower and less evenly than the
nominal `POLL_INTERVAL_S=0.25s` sleep alone would suggest (a live run measured mean intervals of
0.4-1.0s and gaps up to ~5s), so `longest_continuous_run` derives any open-run dwell estimate from
the samples' own observed gaps, never from the nominal constant, and both the terminal verdict and
the report say so explicitly. A single `--url` behaves the same as before, just as a one-entry
sequence. REMOVED 2026-08-27: a second (AXMain/key-window) instrument and its target-app-name
resolution (`resolve_target_app_name`/`_resolve_chromium_app_name`) — the live 5-URL sustained-load
check this script itself enabled found that signal fires constantly with zero perceived focus loss
(see `process-docs/camoufox_lane/`).

### 04_lane_metrics.py (324 LOC)

**Purpose:** Classifies every block (non-empty, non-full-comment-line) of each paired chromium/
camoufox scrape_content `.md` file as CONTENT or BOILERPLATE — Kohlschuetter/Fankhauser/Nejdl
(WSDM 2010) Algorithm 2's decision tree over `numWords`/`linkDensity`, adapted to markdown image/
link syntax, plus the jusText-style short-heading rescue rule applied once afterwards — then reports
content-word/block counts, overall link density and the longest content block per lane per URL, plus
a cross-pair aggregate of which lane has more CONTENT words / a higher CONTENT percentage and where
those two measures disagree. Purely descriptive: neither the script nor its report ever states which
lane is "better".
**Reads:** `/tmp/lane_pairs_20.json` (a fixed, externally-produced `{url, chromium_file,
camoufox_file, ...}` list — not this dir's own state, not committed, not written by any script here);
the scrape_content `.md` files it names, each read once, line-by-line (several camoufox files run
past 1MB, the largest ~27MB).
**Writes:** `md/04_lane_metrics_report_<ts>.md` only; never touches the input JSON, the source
`scrape_content` files, or `01_`'s resume state.
**Called by:** run directly, ad hoc, whenever a paired-backfill batch needs a content-density
comparison.
**Calls out:** none — stdlib only (`json`, `re`).
**Reads:** nothing of its own; imports `02_focus_poll_smoke.py`'s `get_frontmost_app` via
`importlib.util.spec_from_file_location` (filename starts with a digit, not `import`-able
directly); launches this worktree's own `cli.py` as a subprocess, once per URL.
**Writes:** `md/03_live_focus_probe_report_<ts>.md` (per-URL launch spans, overall + per-URL
verdict, full sample series).
**Called by:** run directly, ad hoc, whenever a human needs to eyeball a lane's live focus posture
(as opposed to `02_`'s automated tally over the backfill).
**Calls out:** this worktree's own `venv/bin/python cli.py` (subprocess, real production entry
point, one call per URL); macOS `osascript`/System Events (via the imported `02_` function).

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
- `PROD_SCRAPE_LOG_PATH` (`01_backfill_pairs.py`) is a hardcoded absolute path into the main repo's
  `src/logs/scrape_log.jsonl`, deliberately — worktrees have their own, separate, gitignored
  `src/logs/` tree, and the backfill's whole premise is enumerating URLs the MAIN repo has actually
  seen in production. Do not "fix" this to a relative/worktree-local path without re-deriving that
  premise first.
- `--limit N` selects the first N URLs of the FULL distinct-URL list, not "the next N unprocessed"
  — with M pairs already resumed/skipped, a smoke run needs `--limit (M/2 + desired_new_urls)` to
  actually fire new pairs rather than skip-looping through already-done ones (skips are near-instant,
  so a too-low limit just produces an empty-feeling report, not a hang).
- **`03_live_focus_probe.py` has no CLI flag or env var to disable any part of the camoufox lane's
  no-focus-steal fix for an A/B measurement, and must never get one — that would be a permanent
  surface for a temporary question.** The one-line-throwaway-branch-edit technique this Gotcha used
  to require for the (now-removed) watchdog is recorded historically in `process-docs/lane_choice/`
  and `process-docs/camoufox_lane/` — the same pattern (edit on a never-merged branch, run, revert in
  the same session, verify an empty `git diff integration -- src/`) applies to any future throwaway
  A/B question against this lane, but nothing here should be built to support it permanently.
- **`04_lane_metrics.py`'s `INPUT_PATH` (`/tmp/lane_pairs_20.json`) is a fixed, externally-produced
  file, not generated by anything in this directory.** It is a manually-curated `{url, chromium_file,
  camoufox_file, ...}` list pointing at existing `scrape_content` files (from an earlier `01_`
  backfill run); regenerating it, if ever needed, is a separate, undocumented step outside this
  script's scope — the script only reads it.
- **A "comment line" for `04_lane_metrics.py`'s block filter means the ENTIRE line is one or more
  HTML comments** (`COMMENT_LINE_RE = ^<!--.*-->$`), matching the sidecar header exactly. A line
  with a comment mixed into other content (e.g. `</div><!-- #page -->`, seen in real camoufox
  `mode: markdown` output) is NOT stripped and becomes a normal block, tag text and all — this is
  the spec's literal definition, not an oversight, so camoufox files with leftover raw HTML/script
  fragments can inflate `blocks_total`/`words_total` well beyond what a human would call "content".
