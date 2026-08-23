# DOCS.md format salvage — src/search/ and src/search/engines/ surfaces (2026-08-24)

Content cut from `src/search/DOCS.md` and `src/search/engines/DOCS.md` during the 2026-08-24
doccheck compression (Purpose condensed to one sentence per module).

## src/search/DOCS.md

**query_logger.py** (cut Purpose enumeration/derivation — the bulk of the module entry):

- Three record types, each a flat dict with `record_type`/`ts`/`query`/`language` common to all:
  `engine_run` (written by `_query_engines_concurrent` — always, including probe queries):
  `engines_requested` (list), `engines` (`{engine_name: {rate_wait_ms, search_ms, result_count,
  status, drop_reason}}`, `status` in the full `status.py` enum). `workflow_summary` (written by
  `search_web_workflow` — production only): `engines_requested`, `engines_excluded`
  (`{engine_name: reason}`), `total_wall_ms`, `bottleneck_engine` (str|null), `engines` (same shape
  as `engine_run`), `search_key`. `drilldown` (written by `cli.py`'s `search_engine_drilldown` branch
  — always, on hit, cache-miss-then-searched, cache-miss-then-still-failed, and engine-not-in-pools
  alike): `engine` (the `--engine` value requested), `search_key`, `cache_status` in `"hit"` |
  `"miss_then_searched"` (cache miss triggered a fresh search that then produced a cache entry) |
  `"miss_then_search_failed"` (miss, re-searched, still no cache entry — `engine`/`urls` fields then
  empty/False), `engine_in_pools` (bool — whether `--engine` was present in this search's cached
  pools at all; `False` distinguishes "engine excluded upstream / never ran" from "engine ran,
  returned zero results", `result_count=0` either way), `result_count` (`len(pools[engine])`; 0 when
  `engine_in_pools` is False), `urls` (list[str] — just the URL strings in position order, not the
  full cached objects; the full objects still live in the cache file if ever needed). The `mode`
  field this record used to carry was dropped when the `--books`/`--pdf`/`--docs` flags were removed
  — absence means the record predates or postdates the field.

- `workflow_summary`/`drilldown` share a `search_key` field (`= cache.cache_key(...)`'s output for
  that search) — the exact join key correlating a drilldown back to the search it came from (or the
  fresh search it triggered on a cache miss); NOT a random per-run id — two separate searches of the
  same query correctly share one value. LIMIT: this file is lazily pruned on a 14-day window, so a
  `drilldown` record can outlive the `workflow_summary` it points at — an unresolvable `search_key` is
  ordinary retention, not corruption. Correlation does NOT extend to `src/logs/scrape_log.jsonl`
  (separate file, no shared identifier) — a scraped URL still cannot be mechanically tied to the
  drilldown that offered it. Records with no `record_type` field at all predate the field entirely
  and are `workflow_summary`-equivalent (backward compatible).

- As of 2026-08-05, the drilldown path is ALSO logged (`record_type: "drilldown"`), closing the "a
  scraped URL cannot be traced back to which engine(s) offered it" gap. **A URL can NEVER be
  attributed to exactly one engine** — engines overlap heavily; the same URL routinely appears in 3+
  drilled engines' pools. What IS answerable (via `query_log.jsonl`'s `drilldown` records +
  `search_key`): "which engines offered this URL in this session" — possibly several, possibly none.
  The none-case is what motivated the drilldown logging in the first place (a scraped idealo.de
  product URL, id-recycled to a different product days later, with no record of which engine — if
  any — ever served it).

**search_web.py** (cut Purpose derivation): Post-dedup pool cap (`_cap_pools`): K =
`len(pools['google'])` if >0 else 10, each pool trimmed to `pool[:K]` (prevents
CrossRef/OpenAlex/StackExchange/OpenLibrary drilldown floods). Three-tier timeout:
`ENGINE_WATCHDOG_TIMEOUT=3.6s` default, `ENGINE_WATCHDOG_OVERRIDE` per-engine (open_library 6.0,
semantic_scholar 5.0, crossref 6.0, startpage 6.0, brave 6.0) — `bing`, `yandex`, and `marginalia`
deliberately have NO override entry: all three probed well under the default (yandex additionally
short-circuits its own blocked-query path via an upfront `showcaptcha`-URL check; marginalia's
httpx-API round-trip never approaches 3.6s regardless of rate-limit outcome). `RATE_WAIT_TIMEOUT
=60.0s` acquire cap → RATE_SKIP. `_engine_with_timing` returns a 5-tuple `(results, rate_wait_ms,
search_ms, status, drop_reason)` with sub-classified TIMEOUT/ERROR statuses — the exception-to-status
mapping is `_classify_engine_exception` (one `except Exception` dispatching via isinstance, same
match order as the original except chain it replaced). Two-record logging: `engine_run` after
fanout, `workflow_summary` after pool-build — as of 2026-08-05, `workflow_summary` also carries
`search_key` (the same value `cache_key(...)` computed for this call, threaded into
`_build_query_log_entry`) — the join key a `cli.py` "drilldown" log record correlates back to.

**merge.py** (cut Purpose detail): `build_engine_pools(results)` groups SearchResults by URL, assigns
each URL to the owner engine (lowest position value, random tie-break), returns
`{engine → [owned SearchResult, ...]}` sorted by native position. Populates `engine_positions` on
each result (all engines' positions for that URL). Constructs a FRESH `SearchResult` per winning URL
— any field not explicitly named in that constructor call (e.g. `date`) is silently dropped, so new
`SearchResult` fields must be threaded through here explicitly.

**cache.py** (cut Purpose detail): Cache key `sha256(query|language|engines|time_range)[:16]`; path
`~/.cache/websearch/<key>.json`; 1h mtime TTL; atomic write via `tempfile.mkstemp` + `os.replace`.
JSON holds the full per-engine pool dict with native positions. `date` (ISO-8601 partial:
`"YYYY"`/`"YYYY-MM"`/`"YYYY-MM-DD"`, or `None`) is serialized per entry and rendered as a
`Date: <value>` line when present; read via `entry.get("date")` so cache files written before this
field existed (no `date` key at all) still render without error.

**browser.py** (cut Purpose detail): `BACKGROUNDING_FLAGS` (Playwright's own Chromium defaults)
applied unconditionally; evidentiary status of their effect is honestly uncertain — see the code
comment. No JS fingerprint patches, no UA override, no explicit `--window-size` —
`process-docs/browser_posture/` (Milestones 1-2) found the prior JS screen/getComputedStyle patches
and the hardcoded UA/window-size all contradicted observable reality under headed and removed them;
Chrome now reports its own real values throughout. Cleanup paths: `kill_tab(tab)` (browser-level
`Target.closeTarget`, 5s cap), `close_browser()` (in-loop shutdown for dev), `kill_stale_chrome()`
(nuclear `pkill` fallback — the actual teardown for the backgrounded launch, since `open -g`'s Popen
is a short-lived wrapper, not Chrome itself).

**status.py** (cut Purpose enumeration): 17 total. Legacy coarse (5, still emitted on clean paths):
`OK`, `EMPTY`, `TIMEOUT`, `ERROR`, `RATE_SKIP`. EMPTY sub-statuses (Stage 2, per-engine
`_diagnose_empty`): `EMPTY_NO_RESULTS` (page loaded, container found, 0 hits — legit empty),
`EMPTY_NO_CONTAINER` (result-container selector found 0 elements — DOM-drift suspect), `EMPTY_CONSENT`
(consent-detection fired, redirect not handled), `EMPTY_BLOCK` (CAPTCHA/block-page marker detected),
`EMPTY_CONCURRENT_RACE` (page-state unexpected, possible concurrent-tab collision). TIMEOUT
sub-statuses: `TIMEOUT_WATCHDOG` (`asyncio.wait_for` fired AND `search_ms < timeout*1.2` — clean
cancel), `TIMEOUT_NONCOOP` (fired but `search_ms >> timeout` — non-cooperative), `TIMEOUT_HTTPX`
(`httpx.TimeoutException` — engine-internal, not watchdog). ERROR sub-statuses: `ERROR_BROWSER`
(pydoll/Chrome connection failure), `ERROR_HTTP` (`httpx.HTTPError` non-timeout: 4xx/5xx or
transport), `ERROR_PARSE` (`JSONDecodeError`/`KeyError`/`ValueError`/`AttributeError` from parser),
`ERROR_OTHER` (uncategorized exception).

## src/search/engines/DOCS.md

**bing.py** (cut Purpose detail): Every organic href arrives wrapped in a
`bing.com/ck/a?...&u=<prefixed-base64>&...` tracking redirect — `_clean_url` unwraps it: parses the
`u` query param, strips its 2-char prefix (observed `a1`), base64url-decodes with padding restored,
graceful fallback to the raw wrapped href on any failure or missing `u` param. `_extract_date`
populates `SearchResult.date` from `span.news_dt`'s localized display string (`"14. März 2023"` /
`"May 20, 2026"`) via two regexes + DE/EN month-name maps — inconsistent across results (only present
on some, e.g. news-style listings), an unrecognized shape (e.g. relative "vor N Tagen") or absent
element returns `None`, never a guess. Deliberately no snippet-text fallback — a result with a
plain-text date but no `news_dt` span gets no `date`.

**yandex.py** (cut Purpose detail): Two refinements over the plain google/startpage/brave/bing
pattern: (1) checks `tab.current_url` for a `showcaptcha`/`checkcaptcha`/`/captcha` redirect
IMMEDIATELY after navigation, before the result-wait poll, so a blocked query returns `S.EMPTY_BLOCK`
fast (~0.4-1.6s live) instead of burning the full ~6-8s poll budget; (2) `_build_results` drops any
result whose hostname carries `yandex` as a dot-separated label (`_is_self_referential` — catches
`yandex.com`/`*.yandex.*` self-links and video-carousel cards without false-positiving on a lookalike
domain like `notyandex.com`).

**startpage.py** (cut Purpose detail): Two-step form-driven flow — a direct GET to
`/sp/search?query=...` silently returns zero results (missing per-session `sc` token): loads
homepage, sets `#q` via the native `HTMLInputElement.value` setter + `input` event (React controlled
input), real `.click()` on `button.search-btn` (NOT `form.submit()`, which bypasses React's handler).

**brave.py** (cut Purpose detail): Detects Brave's Proof-of-Work (PoW) CAPTCHA via title/body marker
scan (`captcha`, `schieberegler ziehen`, `drag the slider`, `proof of work`) or
`a[href*="pow-captcha"]` presence — a PoW hit returns `[], S.EMPTY_BLOCK` immediately (graceful
empty, never an exception); this is the load-bearing design point, since Brave's PoW is
IP/velocity-based, not defeated architecturally.

**scholar.py** (cut Purpose detail): Migrated off pydoll 2026-05-09. `_TIMEOUT=6.0` — own probe:
Scholar HTTP latency measured 0.7-5s range; the module-wide 3.6s default would trip `TIMEOUT_HTTPX`
— not registered in `search_web.py`'s `ENGINE_WATCHDOG_OVERRIDE` since this engine isn't wired into
that path at all.
