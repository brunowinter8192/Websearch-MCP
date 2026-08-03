# browser.py rebuild for a headed-background default (2026-08-03)

Milestone 3 of 3 (this area's other entries: `2026-08-03_launch_latency_and_flag_probe.md`,
`2026-08-03_fingerprint_patch_consistency_under_headed.md`) — the production change. Every decision
below implements a verdict measured in this area's first two milestones; nothing here is newly
decided from first principles.

## Window-size caught during this session, same defect class as Milestone 2

Original plan kept `--window-size=1920,1080` on the reasoning that a real instruction to Chrome
isn't a contradiction the way a JS-level lie is. Measured before committing to that: launched headed
with the flag as-is and read back `outerWidth/outerHeight` against `screen.width/availHeight`. Real
screen on this machine: 1728x1117 CSS px, availHeight 998. Requested 1920x1080 got silently clamped
by Chrome to 1728x998 — the flag doesn't do what it says, on this display. Dropped the explicit size
entirely rather than deriving a fitted one; Chrome's own default (measured: ~1200x954 outer,
1200x867 inner) is internally consistent by construction and needs no machine-dependent computation.
Not verified against any engine's viewport-dependent behavior — the dev probes ran at 900x700,
production has never run at a checked, fixed size either way; the code comment says so rather than
implying more than was checked.

## What changed in `src/search/browser.py`

- **Headed-backgrounded default.** `_open_background_process_creator` (`open -g -n -a "Google
  Chrome"`) swapped onto `_browser._browser_process_manager` in `get_tab()`, before `await
  browser.start()` — the exact mechanism `dev/browser_posture/02_parallel_chrome_probe.py` already
  proved against this same real `SESSION_DIR`. `new_tab()` needed no change: it creates tabs via CDP
  on the already-running browser, no new OS process, so the swap only has to happen once.
- **`WEBSEARCH_HEADLESS`** (new name, inverted meaning from the old opt-in `WEBSEARCH_HEADED`) forces
  headless — direct launch, no `-g` needed. Documented in `build_options()`, `src/search/DOCS.md`,
  and `.env.example` (the old var had no documentation anywhere outside the source; this is the first
  time either name appears in project docs).
- **`BACKGROUNDING_FLAGS` added unconditionally**, matching Playwright's own always-on behavior. Code
  comment states plainly: Playwright's defaults + the Chromium switch reference's description, AND
  that Milestone 1 could not confirm their effect (occlusion never materialized on this machine) —
  in on external evidence, not on measurement, and the comment says exactly that, not more.
- **Both JS patch blocks removed**, along with `apply_fingerprint_patches` and its two call sites
  (`get_tab`, `new_tab`) and the now-unused `PageCommands` import. Milestone 2's verdict was DROP on
  both; nothing was left behind for symmetry.
- **`REAL_USER_AGENT` dropped entirely**, both headed and forced-headless. It was already four Chrome
  major versions stale (146 vs the actual 150.0.7871.187) and would drift again after every Chrome
  update. Its stated purpose — masking the `HeadlessChrome` UA signal — is a headless-only concern a
  headed browser doesn't have; keeping it only for the rare forced-headless debug path would
  re-import the exact staleness defect Milestone 2 just removed from the JS patches, for a path that
  doesn't need anti-detection (debugging / no-display machine, not production traffic). Chrome now
  sends its own real, always-current UA in both modes.

`kill_stale_chrome`, `kill_tab`, `close_browser` are untouched — already proven correct against the
real `SESSION_DIR` in Milestone 1's probe 02, and the backgrounded launch's `open` Popen being a
short-lived wrapper (not Chrome) was already the reason `kill_stale_chrome`'s unconditional `pkill`
is the actual teardown, not pydoll's own `stop_process()`.

## Verification

**Test suite, pre/post diff.** Baseline recorded before touching `browser.py`: 9 failed, 83 passed, 2
collection errors (`ModuleNotFoundError: curl_cffi`, unrelated news/proxy_pool module). Re-run after
the rebuild: identical — 9 failed, 83 passed, 2 errors, same failing tests
(`test_proxy_pool.py` x2, `test_query_logger.py` x7 — pre-existing `AttributeError: ... 'fetch_previews'`
drift, unrelated to `browser.py`). No new failures, no fixed failures either — grep confirmed no test
file imports `src/search/browser.py` directly.

**One real end-to-end run**, `cli.py search_web "python asyncio tutorial"`, read from the fresh
`workflow_summary` record in `src/logs/query_log.jsonl` (this file didn't exist yet in the worktree
before this run). Read as a non-regression check against the 30-run baseline this milestone was
given, NOT as a causal or improvement claim — a single sample cannot establish that, and an engine
landing on its historically-minority outcome is exactly that, one sample of already-known variance:

| Engine | This run | 30-run baseline | Read |
|---|---|---|---|
| bing | OK, 2120ms | 30/30 OK | consistent |
| startpage | OK, 5327ms | 30/30 OK, max 4671ms | status consistent; latency above prior observed max but still inside its 6.0s watchdog override — noted, not alarmed |
| yandex | OK, 2824ms | 30/30 OK | consistent |
| google | OK, 2533ms | 27/30 OK, 3 TIMEOUT_WATCHDOG | consistent |
| duckduckgo | TIMEOUT_WATCHDOG, 3605ms | 24/30 OK, 6 TIMEOUT_WATCHDOG | within already-known failure variance, not a new failure mode |
| semantic_scholar | OK, 3892ms | 14/30 OK, 9 TIMEOUT_WATCHDOG | landed on the OK side of a historically volatile engine — one sample |
| brave | OK, 4232ms | 15/30 OK, 15 EMPTY_BLOCK | one sample of a ~50/50 engine |
| mojeek | OK, 1959ms | 7/30 OK, 23 EMPTY_BLOCK | one sample, historically the minority outcome |
| lobsters | OK, 2690ms | 4/30 OK, 26 EMPTY_NO_CONTAINER | one sample, historically the minority outcome |

No engine newly hit the watchdog outside its already-known pattern; nothing that worked in the
baseline broke here.

**No foreground steal.** Continuous frontmost-app poll (`osascript`/System Events, 0.5s interval, the
Milestone 1 method) ran for the full duration of the real CLI search: 58 samples, only `CotEditor`
(the app actually in use) — `Google Chrome` never appeared.

**Clean teardown.** `pgrep -f user-data-dir=<SESSION_DIR>` empty after the run — `atexit` →
`kill_stale_chrome()` fired correctly on process exit, the real production teardown path, not a dev
probe's.

No screen captures were taken anywhere in this milestone.
