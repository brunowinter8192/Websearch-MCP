# DOCS.md format salvage — src/crawler/ surface (2026-08-24)

Content cut from `src/crawler/DOCS.md` during the 2026-08-24 doccheck compression (Purpose
condensed to one sentence per module). Snapshot as of the cut date.

**crawl_site.py** (cut Purpose function-signature/CLI-flag detail): `discover_urls_playwright(seed,
include/exclude_patterns, max_pages, max_depth, delay_s, page_timeout_ms, concurrency, stealth)` runs
a manual Playwright-per-page BFS (`crawler.arun()` per URL, links from `result.links.internal`
post-JS DOM), returning `(urls, meta)` with `stop_reason` in {frontier_exhausted, max_pages_reached,
429_persistent}. Per-batch fetch results classified by `_process_batch_results` (status filtering,
found/latency collection, frontier expansion via `_extract_frontier_links`) — sibling to the
pre-existing `_fetch_page`/`_build_crawler_config`/`_handle_429_batch` helpers. `crawl_urls(urls)`
does the parallel content crawl (`SemaphoreDispatcher(max_session_permit=10)`,
`wait_until="networkidle"`). `normalize_url` strips query/fragment/@version/trailing-slash for
visited-set dedup. CLI (`python -m src.crawler.crawl_site`): `--url` seed, `--output-dir`, `--depth`
(3), `--max-pages` (100), `--include/exclude-patterns`, `--url-file` (skips discovery), `--delay`
(3.0), `--page-timeout` (15000), `--concurrency` (1), `--stealth`.

**pipe_scraper.py** (cut Purpose derivation): CLI (`python -m src.crawler.pipe_scraper`):
`--url-file` + `--output-dir` (both required), `--download-delay` (1.0),
`--concurrency-per-domain` (default resolved per-engine when omitted — 8 chromium / 1 camoufox),
`--engine {chromium,camoufox}` (default chromium), `--block-images`/`--no-block-images` (camoufox
only, default off). `scrape_urls_workflow` (orchestrator) delegates to `_scrape_all`, which resolves
the engine's default concurrency, builds a `run_id`/`config_hash`/`config` run context, and dispatches
per-RUN (never per-URL, never auto-selected) to one of two engines: CHROMIUM (default, unchanged)
shares one `AsyncWebCrawler` across all in-flight requests and calls
`pipe_scraper_acquisition._scrape_one` per URL, with one upfront
`pipe_scraper_config._extract_pipe_config_stamp` for the whole run; CAMOUFOX calls
`pipe_scraper_acquisition._scrape_one_camoufox` per URL (own fresh browser launch/teardown per call,
no shared crawler, no upfront config object — each URL's own record reads config off that call's own
meta). `block_images` is only meaningful on the camoufox engine (chromium's `_build_configs()` has no
such param); `False` by default, unified with the ad-hoc lane's own default (`src/scraper/DOCS.md`'s
own Gotcha carries that history).

**pipe_scraper_config.py** (cut Purpose derivation): `_build_configs()` (no params — the browser/run
config does not depend on pacing values, only `_extract_pipe_config_stamp` does) sets a fixed
anti-bot posture for the chromium engine, optimized purely for reachability (not extraction quality —
no content filter/`preserve_tags`, that's the Cleanup-step LLM's job per the capture skill):
`enable_stealth=True` (StealthAdapter, verified live against crawl4ai 0.9.2 + playwright-stealth
2.0.3, reachable because this module passes no custom adapter so `use_undetected` resolves False),
`simulate_user=True` + `override_navigator=True` (mouse/scroll + navigator-override, taken
individually), `magic=False` EXPLICITLY (magic would ALSO randomize the user-agent via
`ValidUAGenerator` — 8 different UAs from one IP at `CONCURRENCY_PER_DOMAIN=8`, plus a
UA/Chromium-version mismatch signal — rejected, not an oversight, see Gotchas),
`remove_consent_popups=True` (an un-dismissed consent wall is a LOST page here, since the capture
skill deletes confirmed block pages rather than cleaning them — a reachability problem, not the
quality-tuning role the same switch plays in `scrape_url.py`). `UndetectedAdapter` is NOT used
(crawl4ai issue #1500: crashes above concurrency 1, incompatible with `CONCURRENCY_PER_DOMAIN=8`).
Wires `pipe_scraper_acquisition._fallback_fetch` as `fallback_fetch_function` (path a). Also stamps
`fallback_armed` (whether path a is wired).

**pipe_scraper_acquisition.py** (cut Purpose derivation): Per-URL engine executors for both engines,
plus the chromium engine's curl_cffi fallback routes (merged into one module — `_own_fallback_rescue`
is called directly from `_scrape_one`'s except block and both need `_url_to_filename`, a real
bidirectional coupling). Two independent fallback-acquisition paths for when the browser is the
weaker client (crossref.org evidence: 0/23 in a capture run, empty at the ~15s page-load ceiling with
no HTTP status, vs plain curl returning HTTP 200/79274 bytes in 7.2s), both built on
`_curl_cffi_get` (`curl_cffi.requests.AsyncSession(impersonate="chrome")`, bounded by
`FALLBACK_FETCH_TIMEOUT_S=15.0` + an outer `asyncio.wait_for`, fail-soft):

- Path (a): `_fallback_fetch` wired as `CrawlerRunConfig.fallback_fetch_function` (crawl4ai's own
  mechanism, fires when the browser returns a non-exception result `is_blocked()` flags). Signature
  (`str | None`) is a contract with crawl4ai — cannot carry extra data (e.g. landed URL).
- Path (b): `_own_fallback_rescue`, called from `_scrape_one`'s `except Exception:` block — the ONLY
  path reaching a browser-raised hard exception (crawl4ai's path (a) cannot, at `max_retries=0`).
  Calls `_curl_cffi_get` directly to also read `response.url` (real `landed_url`). Converts via
  crawl4ai's `raw:` pipeline (not `raw://`, avoids the `urlsplit()` IPv6 crash).

`landed_url`: plain-success route reads `result.redirected_url` raw. Path (a) stays `None` — crawl4ai
hardcodes `redirected_url=url` on that route regardless of curl_cffi's actual fetch, and
`_fallback_fetch`'s str-only contract carries no channel out. Path (b) gets a real `landed_url`
(curl_cffi's own `response.url`). No `same_target` verdict computed anywhere.

`_scrape_one` (chromium) vs `_scrape_one_camoufox` (camoufox) — completely different per-URL function
and record shape. `_scrape_one_camoufox` calls `try_scrape_camoufox` per URL (fresh browser
launch/teardown, no shared crawler) — no crawl4ai-own-fallback, no pipe-own-rescue at all on this
engine (both are chromium-lane machinery; camoufox IS the deliberate alternative). Both executors
share `pipe_scraper_pacing`'s gate mechanism but different concurrency defaults
(`CAMOUFOX_CONCURRENCY_PER_DOMAIN=1`). `_scrape_one_camoufox`'s outcome mapping checks
`meta["acquisition_error"]` FIRST — `budget_exhausted`/`browser_missing`/`exception` all leave
`status_code=None` and content empty, which would otherwise fall through to `outcome='empty'` and
misreport a hard acquisition failure as "browser succeeded, page had nothing."

**pipe_scrape_logger.py** (cut Purpose derivation): `outcome` in `"ok"|"waf_429"|"http_error"|
"empty"|"error"`. `run_id` (uuid4) shared by every record of one `scrape_urls_workflow` invocation.
`ts` is REQUEST START, stamped after the per-domain pacing gate (see Gotchas). Separate file/schema
from `src/logs/scrape_log.jsonl` (the ad-hoc single-URL path's log): has `run_id`/`domain`, no
sidecar/`content_path`/`mode` (pipe_scraper already writes every page's raw markdown to
`--output-dir`; that IS the content record). `config` carries `simulate_user`/`override_navigator`/
`magic`/`remove_consent_popups`/`fallback_armed` alongside stealth/pacing fields.

`landed_url` (str|null, raw): real on plain-success AND path (b); `null` on path (a) (crawl4ai's own
`fallback_fetch_function` — structurally hardcoded there) and on path (b) when the curl_cffi fetch
never completed; absent by definition on records predating this field. No verdict stored alongside
it: `same_target` (`is_same_target(url, landed_url)`, tri-state) was added then REMOVED — now a
narrow-window historical field only. `config_hash` groups records under the same config but is NOT a
stable identity across schema versions — changes whenever any stamped value changes, including a
field being added/removed from the stamp itself. `crawl4ai_*` fields describe ONLY crawl4ai's own
fallback (path a) — never pipe_scraper's own rescue. `pipe_fallback_used`/`pipe_fallback_resolved`
describe path (b) exclusively: `used` = except-block rescue attempted; `resolved` = curl_cffi
returned a genuine 200 with a body (describes the FETCH, not conversion — `resolved=True` next to
`outcome="empty"` is legitimate, not a contradiction). `wall_ms` on a `pipe_fallback_used=True` record
includes the full failed browser attempt PLUS the fallback fetch — failure records got systematically
longer once this path landed; a time-distribution analysis spanning the before/after boundary must
cross-check `pipe_fallback_used`.

Shared by TWO acquisition engines as of pipe_scraper.py's engine switch (chromium via
`_log_pipe_record`, camoufox via the sibling `_log_pipe_camoufox_record` — deliberately not one
shared function with extra optional params, since the crawl4ai-own-fallback/pipe-own-rescue fields
are chromium-lane machinery that never runs on camoufox). `"engine"` is the first-class
discriminator, same reasoning as scrape_log.jsonl's own field. Every chromium-only field
(`crawl4ai_*`, `pipe_fallback_used`, `pipe_fallback_resolved`) is ABSENT on camoufox records; every
camoufox-only field (`markdown_conversion_error`, `content_is_raw_html`) is ABSENT on chromium
records. `config`'s key set differs completely by engine: chromium's full pacing/stealth surface
computed ONCE per run off the real shared `BrowserConfig`/`CrawlerRunConfig` objects, vs camoufox's
smaller surface (headless/os/block_images/timeout/executable_path/total_budget_s) read PER URL off
that call's own meta. `config_hash` is therefore never comparable across engines even on collision.
