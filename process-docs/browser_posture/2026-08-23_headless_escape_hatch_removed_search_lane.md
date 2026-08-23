# WEBSEARCH_HEADLESS escape hatch removed from the search lane — single headed-backgrounded path (2026-08-23)

Follow-on to this area's 2026-08-22 scrape-lane removal entry, which removed the
same hatch from the scrape lane and explicitly left the search lane (`src/search/browser.py`) as a
tracked follow-up. This entry closes that follow-up: `src/search/browser.py`'s `get_tab()` now
unconditionally swaps `_open_background_process_creator` onto `_browser_process_manager` before
`await browser.start()` — no `options.headless` branch, no env read.

## Why removed

Same two grounds as the scrape-lane removal — no re-derivation, this is the mirrored decision:
policy rejects a second, runtime-selectable acquisition path even when operator-explicit; the
no-display justification does not apply to this deployment (a Mac with a display).

## What changed

- `src/search/browser.py`: removed `_FALSY_ENV_VALUES`, the `os` import, and the
  `options.headless = os.environ.get(...)` line from `build_options()`. `get_tab()`'s
  `if not options.headless:` branch collapsed — the process-manager swap now always runs.
  127 -> 121 LOC.
- `.env.example`: deleted the "Force Headless Browser" block entirely (`WEBSEARCH_HEADLESS` had no
  other reader left in the project after this change — the scrape-lane removal already dropped its
  own read on 2026-08-22, this was the last one).
- Stale "headless" documentation corrected to the headed reality (headed default shipped
  2026-08-03, this area's headed-default rebuild entry; these claims predated it and were
  never updated when that shipped): `src/search/DOCS.md`'s `browser.py` module entry + gotchas (the
  `_FALSY_ENV_VALUES` landmine gotcha removed outright — the guard it warned about no longer exists),
  `src/search/engines/DOCS.md`'s brave/bing/yandex module entries ("via pydoll Chrome tab, headless"
  -> "headed"), `src/search/engines/brave.py:60`'s module comment. No engine logic touched — doc/comment
  truth only.

## Verification

**Test suite, pre/post diff.** Baseline recorded before touching `browser.py`: 209 passed. Re-run
after the change: 209 passed, identical — no test file imports `src/search/browser.py` directly
(grep-confirmed), matching the scrape-lane removal's own finding for its own lane.

**One real end-to-end run**, `cli.py search_web "python asyncio tutorial"`. All 14 engines ran, 11
OK, 3 empty-family (`mojeek: EMPTY_BLOCK`, `open_library: EMPTY`, `marginalia: EMPTY`) — no
ERROR/TIMEOUT status, no engine landing outside its already-documented outcome shape.

**No foreground steal.** Continuous frontmost-app poll (`osascript`/System Events, 0.5s interval) ran
for the full duration of the real CLI search: only the terminal app in use (`ghostty`) appeared —
`Google Chrome` never appeared.

**Clean teardown.** `pgrep -f user-data-dir=<SESSION_DIR>` empty after the run.

## What was deliberately NOT touched

`src/scraper/DOCS.md:29` and `tests/test_scrape_url.py` (lines 5, 379, 587) still name
`WEBSEARCH_HEADLESS` — both predate this session (the scrape lane's own 2026-08-22 removal commit),
describing that lane's own history, not a live reader. Left untouched: the scrape lane and its tests
are out of this session's scope.
