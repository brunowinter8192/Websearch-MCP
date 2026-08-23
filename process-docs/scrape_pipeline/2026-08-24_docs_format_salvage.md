# DOCS.md format salvage — src/scraper/ surface (2026-08-24)

Content cut from `src/scraper/DOCS.md` during the 2026-08-24 doccheck compression (Purpose
condensed to one sentence per module). Snapshot as of the cut date; camoufox_scrape.py's cuts are
salvaged separately to `process-docs/camoufox_lane/`.

**scrape_url.py** (cut Purpose derivation/history):

- `_acquire_cdp_headed` is the single acquisition path as of 2026-08-22 (the `WEBSEARCH_HEADLESS`-forced
  direct-`playwright.chromium.launch()` escape hatch was removed). Self-launches patchright's currently-installed
  chromium headed-but-backgrounded via macOS `open -g -n -a`, path resolved dynamically every call via
  `patchright.async_api`'s `BrowserType.executable_path` (never hardcoded to a revision like "chromium-1228" —
  crawl4ai's own `get_chromium_path()` resolves the wrong, plain-playwright bundle). Waits on a bounded
  `DevToolsActivePort` poll (`CDP_PORT_WAIT_TIMEOUT_S=10.0`), connects crawl4ai over `cdp_url`
  (`browser_mode="custom"`, `cdp_cleanup_on_close=True`). Self-launch flags come from a live call to
  `crawl4ai.browser_manager.ManagedBrowser.build_browser_flags()` (never pinned) plus `--window-size`;
  deliberately does not reach "full" parity with patchright's own RPC-launched cmdline
  (`dev/browser_posture/05_cdp_headed_probe.py`'s 34-flag delta) — those flags are constructed by patchright's
  internal Node driver for a `browserType.launch()`/`connectOverCDP` RPC call, confirmed unreachable by any
  raw-subprocess launcher (including crawl4ai's own `ManagedBrowser`) by reading `ManagedBrowser.start()`.
  One deliberate 3-flag deviation even within the reachable surface: `build_browser_flags()` gates
  `--disable-gpu`/`--disable-gpu-compositing`/`--disable-software-rasterizer` behind `not enable_stealth`
  (keeping WebGL on under stealth) — kept as-is rather than matching the older, now-removed direct-launch
  path's sibling function (an existing inconsistency in installed crawl4ai 0.9.2, not replicated here).
  `test_build_browser_flags_symbol_resolves_and_is_callable` is a loud-failure guard against a crawl4ai
  upgrade renaming/removing/reshaping that symbol.

- `TOTAL_SCRAPE_BUDGET_S=245.8` composition (renamed from `TOTAL_SCRAPE_BUDGET_CDP_S` when the escape hatch's
  `TOTAL_SCRAPE_BUDGET_HEADLESS_S` was removed): the self-launch's own bounded wait does NOT replace the old
  180s cold-start summand — `patchright/_impl/_browser_type.py`'s `connect_over_cdp` also falls back to
  `DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS=180000` when crawl4ai passes no explicit timeout (it
  doesn't). The 180s ceiling moves from `launch()` to `connect_over_cdp()`, with two new summands added in
  front: 1.0 (bundle-path resolution, measured) + 10.0 (`DevToolsActivePort` wait) + 15.5 (crawl4ai's own
  `_verify_cdp_ready`: 5x2s `aiohttp.ClientTimeout` + backoff, source-derived) + 180.0 (connect_over_cdp
  fallback) + 30.0 (nav) + 5.0 (render wait) + 1.3 (consent) + 3.0 (date, `HTMLDATE_TIMEOUT_S`) = 245.8.

- `extract_config_stamp` stamps a fixed `LAUNCH_MODE="cdp_headed_backgrounded"` module constant (no longer a
  passed param) into `launch_mode`, replacing the old `headless` boolean field entirely —
  `browser_config.headless` is dead on the cdp path (never read inside crawl4ai's `cdp_url` branch of
  `browser_manager.py`'s `start()`).

- Teardown (`_kill_by_profile` + `shutil.rmtree` on the throwaway `--user-data-dir`) runs in a `finally`
  inside `_acquire_cdp_headed`. `_kill_by_profile` uses `psutil` to terminate-then-`wait_procs`-then-force-kill
  BEFORE returning — a plain `pkill` (first implementation) returns as soon as the signal is sent, raced
  against the immediately-following `rmtree` and left a real, non-empty profile directory behind (caught via
  a real live `cli.py scrape_url` run, not a mock).

- `page_timeout` reasoning: falls back to 30000 (down from a prior, unmeasured 60000) on the rule "a phase cap
  is not raised above the default of the layer that executes it without evidence for the raise" — patchright
  1.61.2's own `DEFAULT_PLAYWRIGHT_TIMEOUT_IN_MILLISECONDS` is 30000, crawl4ai's CHANGELOG documents its
  60000 as an unmeasured raise. `delay_before_return_html` raised 2.0→5.0 (2026-08-06) to stop self-resolving
  Cloudflare challenge pages being captured too early (measured on guenstiger.de: 2.0s → interstitial, 6.0s →
  real product page); 5.0 is Cloudflare's own documented figure (developers.cloudflare.com, "Non-Interactive
  Challenges", "typically less than five seconds"), taken as-is, not derived from the guenstiger.de
  measurement (corroborating only). Superseded: the earlier 2.0 came from crawl4ai issue #1665's third-party
  saturation-knee measurement, discounted against `remove_consent_popups`'s own unconditional ~1s wait on the
  same render window — see `process-docs/scrape_pipeline/` (2026-08-06 five-second-wait entry) for the full
  history and both sources.

- 2026-08-05 no-content-judgment change: removed the `status_code >= 400` early return (real evidence it was
  wrong: `de.trustpilot.com/review/entega.de` returns HTTP 403 WITH the real 42707-byte review page), the
  `is_garbage_content` gate call (real evidence wrong in the other direction: `idealo.de`'s `OffersOfProduct`
  page returns HTTP 200 + 401 bytes of "Sorry! Something has gone wrong" and sailed through as clean),
  `strip_consent_prefix`, `truncate_content`/`DEFAULT_MAX_CONTENT_LENGTH`, `_GARBAGE_MESSAGES`,
  `get_plugin_hint`, `build_config_record`.

- `is_garbage_content` (7 categories, unchanged logic) still exported, called ONLY by
  `src/crawler/crawl_site.py`'s unattended batch crawl. `extract_date(html, url)` pulls the publication date
  (day-precision ISO) from `result.html` via `htmldate.find_date(extensive_search=True, original_date=True)`,
  off the event loop with a 3.0s hard timeout (`HTMLDATE_TIMEOUT_S`, re-grounded from an ungrounded 5.0 as of
  2026-08-22), any exception/timeout/absence degrades to `None`. `extract_crawl4ai_diagnosis(result)` reads
  crawl4ai's own anti-bot verdict (`success`, `error_message`, `crawl_stats["attempts"|"resolved_by"|
  "fallback_fetch_used"]`) — an observation, never consulted for this module's own return value.
  `hash_config(config)` derives a 10-hex-char sha256 grouping key; `config_hash` changed shape on 2026-08-05
  (no more `max_content_length`), so it does not group with pre-change records.

**scrape_logger.py** (cut Purpose derivation/history):

- JSONL record carries `published_date` (htmldate-extracted, `"ok"` outcome only; sidecar header does not —
  judged redundant with the returned content). Also carries crawl4ai's anti-bot diagnosis verbatim
  (`crawl4ai_success`, `crawl4ai_error_message`, `crawl4ai_attempts`, `crawl4ai_resolved_by`,
  `crawl4ai_fallback_fetch_used`, all null when no result obtained) — recorded for later analysis, never fed
  back into a verdict (crawl4ai's block detector has documented false positives, e.g. reports "Cloudflare JS
  challenge" on guenstiger.de even when the full product page came back).

- `outcome` (`ok`/`empty`/`budget_exhausted`/`browser_missing`/`exception`) as of 2026-08-05 no longer
  includes content-judgment categories (`http_error`/`cookie_wall`/`login_wall`/`cloudflare`/`nav_dump`/
  `minimal_content`/`crawl4ai_error`) — those are historical-only values on pre-2026-08-05 records (the
  classifier that emitted them was removed, not evidence those failure modes stopped happening). Same
  historical-only treatment for the dropped `garbage_type`/`truncated`/`consent_stripped` fields.

- `landed_url` (str|null, crawl4ai's `result.redirected_url` verbatim, raw/unnormalized) — absent on records
  written before this field was added. No verdict is stored alongside it: an earlier design (`same_target`,
  `is_same_target(url, landed_url)` computed at write time) was added then removed — `same_target` is a
  narrow-window historical field, not an ongoing one.

- `config`/`config_hash` stamp adds ~450 bytes/record — deliberate given this is a slow-growing log
  (~160 records/2 weeks of real use pre-2026-08-05), and the point is comparing outcomes across config
  changes over weeks of accumulation.

- Shared by both acquisition lanes as of camoufox_scrape.py's ad-hoc CLI wiring. `"engine"`
  (`"chromium"`|`"camoufox"`) is the discriminator, absent on records predating the field. Fields only ONE
  lane can produce are documented as ABSENT (key never written) on the other's records:
  `content_type`/`crawl4ai_*`/`published_date` (chromium-only) vs `markdown_conversion_error`/
  `content_is_raw_html` (camoufox-only). `landed_url`/`config`/`config_hash` are populated by both, though
  `config`'s key set differs completely by engine — exactly the shape difference `"engine"` exists to avoid
  making a reader detect manually. `"mode"` gained two camoufox-only values (`"markdown"`/`"raw_html"`)
  alongside the chromium lane's fixed `"filtered"`.
