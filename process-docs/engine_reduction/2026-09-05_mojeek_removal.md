# Mojeek Removal

2026-09-05

## Decision

Drop `mojeek` from the engine pool. The production pool moves from 8 engines to 7: google,
duckduckgo, startpage, brave, bing, yandex (pydoll); openalex (HTTP). `mojeek.py` and its test file
were deleted, not parked — same treatment `process-docs/engine_reduction/` already recorded for the
six engines cut earlier in this area; mojeek's own addition history stays in
`process-docs/engine_expansion/`.

## Evidence

`src/logs/query_log.jsonl`: 229 logged runs for mojeek, 9 of which returned results — a hit rate
under 4%. Of 312 total drilldowns logged across all engines, exactly one ever went to mojeek. This
is consistent with an earlier query-log analysis already in `process-docs/engine_reduction/`, which
had flagged mojeek's keep-or-drop as an open item after finding 199/214 EMPTY_BLOCK runs at that
time — the pool of the present analysis is a later, larger pull of the same log and confirms the
same picture rather than reversing it.

Independent of the log analysis, four separate access methods against mojeek.com all converged on
the identical outcome from this project's operating machine: this project's own pydoll/CDP stealth
browser, `ddgs` 9.16.0 (a widely-used HTTP client with TLS impersonation — a completely different
acquisition path), a plain `httpx` request with cookies, a session, and a `Referer` header, and a
real headed (non-automated) Chrome window with no automation at all. All four landed on the same
HTTP-200-with-captcha page. Full detail on the wait-budget mechanism this was measured through is
in `process-docs/search_pipeline/`.

## Cause, as established on 2026-09-05

Two findings together explain why no wait budget, however long, could have changed the outcome:

**The ALTCHA widget never self-starts.** Mojeek's `challenge.js` injects the `altcha-widget` with no
`auto` attribute set. Mojeek's own ALTCHA bundle only self-starts the client-side proof-of-work
computation when that attribute equals `"onload"` — it defaults to off. Without it, the widget sits
inert until a human clicks it; the proof-of-work computation never begins at all in an unattended
browser session, regardless of how long the wait budget is.

**The block is tied to the network this project runs on, not the acquisition method.** All four
access methods above converged on the same captcha page from the same machine, on the university
eduroam network this project's work runs on. That network is this project's permanent operating
environment, so the condition is not expected to change on its own from here.

Both findings are recorded as of 2026-09-05 — as a description of Mojeek's behavior toward this
project's network at this date, not as a permanent property of Mojeek's service in general. The
official Mojeek Web Search API remains the open, unblocked path to that index, should a future need
for it arise; this removal is about the free/scraped access path only.

## Execution

The removal was split across two worker sessions. The first worker did most of the removal and
merged it into `integration` (import, `_DEFAULT_ENGINES`, `_BROWSER_ENGINES`, `ENGINE_MAX_RESULTS`,
`ENGINES` in `search_web.py`; `cli.py` help text; `mojeek.py` and its test deleted;
`06_mojeek_smoke.py` and `ddg_mojeek_selector_probe.py` deleted; mechanical registry trims in
`05_search_smoke.py`, `12_max_results_probe.py`, `13_free_word_probe.py`, `13_timing_ablation.py`,
`no_google_burst_smoke.py`, `stage1_pool_fetch.py`, `value_eval_probe.py`) — but ran out of context
and died mid-edit, leaving the merged `integration` state broken: two dev probes
(`19_books_probe.py`, `20_docs_probe.py`) still imported the deleted module or carried leftover
registry/column entries for it, and several DOCS.md files still described an eight-engine pool or
pointed at the deleted files. A second worker session picked up from that merged, broken state and
finished it:

- `dev/search_pipeline/20_docs_probe.py` and `19_books_probe.py` — dropped the remaining `mojeek`
  registry entries and the hardcoded mojeek table columns/headers in their report-building
  sections (these two probes build columns literally, not generically off the engine registry, so
  trimming only the registry would have left a `KeyError` on the next run). Docstrings and
  heuristic/domain methodology left untouched beyond the engine name itself.
- `src/search/DOCS.md`, `src/search/engines/DOCS.md`, `dev/tests/DOCS.md`,
  `dev/search_pipeline/DOCS.md` — removed the `mojeek.py` module entry and its now-dangling
  Gotchas, the `test_mojeek_engine.py` entry, the `06_mojeek_smoke.py` and
  `ddg_mojeek_selector_probe.py` entries (both deleted files), and corrected engine counts
  (8→7 production, 7→6 browser engines, 9→8 total engine modules) and per-engine lists across the
  four files. Historical/self-contained entries describing untouched dev scripts
  (`31_date_availability_probe.py`, `branch_probe.py`) were left as-is, matching how those scripts'
  own code was left untouched.

A follow-up review pass on this same second-worker change caught one more mismatch of the exact
class this cleanup existed to remove: `20_docs_probe.py`'s Miss Set Analysis empty-state placeholder
row still had 6 cells after the mojeek column was dropped from that table's header, separator, and
data rows, leaving a 6-cell row against a 5-column table — fixed to 5 cells.

Verified: `./venv/bin/python3 -m pytest` — 364 passed. A live `cli.py search_web` run showed
exactly 7 engines in the breakdown table and exactly 7 keys in the newest `workflow_summary`
record's `engines` field.
