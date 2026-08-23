# DOCS.md format salvage — news_pipeline surface (2026-08-23)

Content cut from the area's DOCS.md files during the 2026-08-23 doccheck compression (format
standard: Purpose one sentence, no function-level documentation, no free paragraphs between module
entries). Snapshot as of the cut date — none of this is maintained; the code is the live truth.

## src/news/DOCS.md

**pipeline.py** (cut Purpose detail + trailing paragraphs):
- `run_pipeline` dispatches `_run_pipeline_proxy_pool` (TheBlock: box_lock+Janitor lifecycle spans
  discover→dedup→scrape, then `_persist_proxy_pool_results` runs the clean-pass) or
  `_run_pipeline_browser` (CoinDesk-style: discover→dedup→scrape with `RegwallGuardError` recovery).
  `run_scrape_only` dispatches `_run_scrape_only_riding` (bypasses chunking — engine owns
  concurrency/watchdog/requeue) or `_run_scrape_only_browser` (200-URL chunks via `scrape_chunks_raw`).
  `_build_ok_manifest_entries` is the one shared helper behind all 3 arms.
- `_run_pipeline_proxy_pool`/`_run_pipeline_browser` return `bool`: `True` = ran to completion
  (caller logs `"=== complete ==="` + writes the marker), `False` = aborted early (the arm already
  wrote the marker inline before returning; `run_pipeline`'s trailing code only runs `if completed`).
- `box_lock.acquire(...)` scopes the ENTIRE discover+dedup+scrape stage (a `with` block); `j.end_job`
  + `logger.close()` run in a `finally` nested inside that `with`, guaranteeing Janitor bookkeeping
  closes even on an exception, before the lock releases.

**pipeline_support.py** (cut Purpose detail + trailing paragraph):
- Split out of `pipeline.py` because none of the five helpers are specific to any engine arm;
  `PROJECT_ROOT`/`LOG_DIR` live here since both this module AND `pipeline.py` need `LOG_DIR` —
  `pipeline.py` imports from here to avoid a cycle.
- `_persist_master_list`: format `YYYY-MM-DD\t<url>` (date from `entries[i]["lastmod"][:10]`,
  entries without `lastmod`/`url` skipped), set-union merged with existing file content, sorted
  before write. TheBlock-specific — called only when `platform.uses_master_list` is `True`.

**clean_pass.py** (cut trailing paragraphs):
- `pub_date_str` moved in-module from the deleted `engine/publish.py` (2026-08-20) — the only live
  symbol there; `url_hash`, `copy_articles`, `run_rag_index`, `parse_index_result`, `_write_index`,
  `publish_articles` had zero external callers and were deleted with the module.
- Returns `{"n_cleaned", "n_bodyless", "total"}`. Empty `ok_entries` short-circuits to `{0,0,0}`
  without creating `collection_dir`.

**__main__.py** (cut trailing paragraph):
- `main` (2026-08-20, 116→30 code lines): argparse setup extracted to `_build_parser`
  (`_add_core_args` 9 always-present flags, `_add_scrape_only_args` 4 proxy_riding flags). Pure
  declarative move, verified via `--help` text diff before/after.

**platform.py** (cut trailing paragraphs):
- `Platform.name` is dual-purpose: the `--source` CLI value AND the filename prefix (`f"{name}__"`)
  used by legacy pubdate/hash_only dedup modes.
- `discover()`'s per-platform return shape: `[{url, lastmod, publication_date, title, section}, ...]`
  (CoinDesk adds `_new` internally, stripped before return); not every platform populates every key
  (TheBlock's `publication_date` is empty until `cleanup()` back-fills it from JSON-LD).
- `ProxyScrapeConfig.pool_provider` is called once on `run_loop` startup and again at each
  `refresh_interval_s` tick; returns `(pool, sources)`. `content_type` gates `fetch.py:fetch_url`
  validation ("html" | "xml"). `concurrency`/`buffer_size` defaults (128/1280) mirror
  `proxy_pool/buffer.py`'s constants.

## src/news/engine/DOCS.md

**scrape.py** (cut trailing paragraphs):
- `RegwallGuardError` is raised (not sys.exit) at regwall fraction ≥ `REGWALL_FAIL_THRESHOLD` (0.20);
  `.manifest` on the exception carries the full per-entry manifest including ok entries written
  before abort.
- `_fetch_one` delegates its ok/regwall/empty classify-and-log branch to `_classify_fetch`
  (2026-08-20 extraction, mirrors `proxy_riding/fetch.py:_classify_crawl_result`); write-to-disk
  (`_write_body`) happens only on `ok`.

**dedup.py** (cut function-level docs):
- `filter_new_entries(entries, collection_dir, source, mode="pubdate", exclude_urls=None,
  raw_ext=".md") → (new_entries, n_skip_raw, n_excluded)`.
- `raw_ext` — extension for `mode="raw"` existence check; `".html"` for proxy_riding (CoinDesk).
- `exclude_urls` — URLs permanently excluded (counted `n_excluded`) before the existence check;
  only proxy_pool's `run_pipeline` branch passes this (from `dead_urls.txt` + `failed_urls.txt`).
- Modes: `"raw"` exact `{hash}{raw_ext}` in raw_dir; `"pubdate"` exact `{source}__{pubdate}__{hash}.md`
  (legacy); `"hash_only"` glob `{source}__*__{hash}.md` (legacy, no pubdate).

**scrape_job.py** (cut function-level docs):
- `scrape_chunks_raw(chunks, raw_dir, platform, log)` — outer per-chunk loop, delegates to
  `_scrape_one_chunk` (2026-08-20 extraction — `scrape_entries()` → `_append_to_raw_manifest()` →
  `_update_blocked_urls({"regwall":…,"empty":…})`, mutates `totals` in place). On `RegwallGuardError`:
  `exc.manifest` recovered, ok files preserved, `aborted=True`, outer loop stops. Returns
  `(totals, job_records, regwall_abort)`.
- `_append_to_raw_manifest(raw_dir, ok_entries)` — appends `{hash,url,publication_date}` lines to
  `raw/manifest.jsonl`; append-only, dedup happens upstream.
- `_update_blocked_urls(raw_dir, manifest, status_filenames)` — read, union, write back sorted;
  keys `"regwall"/"empty"` (browser), `"dead"/"failed"` (proxy_pool).
- `job_records`: `[{t_chunk_start, url, hash, file, char_count, status, error, wait_strategy,
  elapsed_s}]` — consumed by `browser_reporter.py`. `regwall_abort` True when the guard terminated
  the chunk loop early.

**browser_reporter.py** (cut trailing paragraphs):
- Key metric: `completion_s ≈ (t_chunk_start − t_job_start).total_seconds() + elapsed_s` per ok
  record — x-axis of the cumulative plot. Backfill projection extrapolates URLs/min → hours to
  scrape `_BACKFILL_TOTAL` (61k).
- `_write_md` (2026-08-20 split, mirrors `proxy_riding/reporter.py`): one section-builder per
  heading (`_md_header`, `_md_char_distribution`, `_md_failure_list`, shared
  `_md_url_list_section(title, job_records, status, limit=50)` for Regwall/Empty tables). Output
  byte-identical, verified via synthetic-state before/after diff; no test suite covers this module.

## src/news/engine/proxy_pool/DOCS.md

**scrape.py** (cut trailing paragraph):
- Manifest: `[{url, hash, status, file, char_count, error}]` in entries order — `status` ∈
  `{"ok", "dead" (404/410 from origin), "failed" (gap — never resolved)}`. Only `"ok"` proceeds to
  `clean_pass.py:_run_clean_pass`.

**loop.py** (cut trailing paragraphs):
- Stall-terminate (`STALL_TIMEOUT_S = 3600`): `_last_progress` tracks the last done/dead resolution
  (queue shrink). Timeout at loop top breaks and returns `gap = list(queue)` → manifest
  `status="failed"` → `failed_urls.txt`. Only done/dead advance `_last_progress` — pure
  proxy-failure batches do not reset the clock. Fires when poison URLs consume all proxies for a
  full pool-cycle with no terminal resolution.
- `run_loop` (2026-08-20, 122→52 code lines): startup + refresh-tick pool-load extracted to
  `_refresh_pool`; batch block extracted to `_execute_batch` (mutates `done`/`dead`/`wset`/
  `consec_fail` in place, returns `(buf, batch_done, batch_failed, last_progress)`).
  `_build_batch`'s two near-identical Phase-1 loops deduped into `_assign_batch_slots(...)`.

**buffer.py** (cut trailing paragraph):
- `build_active_buffer` eligibility delegated entirely to `cm.eligible_candidates()` (wall-clock UTC
  check). `refill_buffer` no-op at/above `target_size`; otherwise tops up with eligible-pool proxies
  not already in `buf`, appended in pool order.

**janitor.py** (cut Purpose detail):
- `_compute_window_stats` buckets attempt events into 60-min windows from t0 (`int((ts-t0)/3600)`;
  boundary refresh lands in the later window), deriving per-window `{probiert, erfolgreich,
  urls_handled, fetch_attempts, pool_size}` via `_compute_one_window` (2026-08-20 extraction).
- `_group_pool_sources` groups `pool_source` events by preceding `pool_refresh` in JSONL order;
  rendered as `## Pool source breakdown` at the bottom of `job.md` (absent when no such events —
  backward-compatible with old JSONL) via `_md_source_breakdown` / `_md_window_table` (2026-08-20
  extractions, pytest-covered in `tests/test_proxy_pool.py`). Attempt events between a
  `pool_refresh` and its `pool_source` events are ignored by the grouping.

**box_lock.py** (cut trailing paragraph):
- `cleanup_stale`: checks the sidecar's `pid` via `os.kill(pid, 0)`. Unreadable/corrupt sidecar →
  treated as held (conservative). `ProcessLookupError` → sidecar removed. `PermissionError`
  (alive, other user) → treated as held.

**pool_retry.py / pool_loaders.py** (cut source list + key notes):
- Sources active in `load_backfill_pool` as of 2026-08-23 (46 URLs / 18 repos): monosans,
  roosterkid, TheSpeedX, themiralay, r00tee, iplocate, sunny9577, ALIILAPRO, dpangestuw, Zaeem20,
  zloi-user, hookzof, proxifly (JSON), jetkai (http/https/socks4/socks5), prxchk (http/socks5,
  validated, 10-min refresh), ShiftyTR (hourly), vakhov (fresh/working), MuRongPIG (`_checked`
  subsets only). databay-labs removed (repo deleted — all URLs 404). Pool ~32k unique.
- `_try_source(url, fn, entries, sources)` is the per-URL isolation helper — catches all exceptions
  after retries exhaust, records `ok=False`, never raises from `load_backfill_pool`.

## src/news/engine/proxy_riding/DOCS.md

**cooldown.py** (cut Purpose detail):
- Two policies via `RidingScrapeConfig.cooldown_policy`: `"fixed"` (60-min flat, byte-identical to
  the production control arm) and `"exp"` (full-jitter exponential backoff ported from
  scrapy-rotating-proxies: base=300s, cap=3600s; reset-on-productive-ride — `ride_ok >= 1` resets
  `failed_attempts` before computing backoff). `cooldown_count()` correct under both policies —
  `now < next_eligible` (exp) or `now - burned_at < 3600s` (fixed); used by the watchdog's
  `pool_samples` A/B telemetry. Read-only `.policy` property for the reporter.

**state.py** (cut dataclass walkthroughs):
- `RiderState` fields: `output_dir` (raw writes), `job_dir` (report writes), `target_urls`
  (frozenset), `done_urls`, `pool_samples` (`(elapsed_s, n_eligible, n_cooldown)` per watchdog
  poll), `pool_provider` (async, 30-min refresh, None = static), `proxy_pool`;
  `all_resolved = len(done_urls) >= len(target_urls)`.
- `JobRecord.status` ∈ `{ok, regwall, connect_fail, failed, empty}`. `RideRecord.positions` =
  `(url, status, elapsed_s)` per URL attempted on that proxy.
- `JobRecord.load_s: float | None` — nav load time for OK fetches, `max(0, elapsed_s −
  DELAY_BEFORE_HTML)`; crawl4ai exposes no nav-timing field, so subtracting the fixed 0.5s
  post-load delay approximates it. Non-OK → None.
- `RiderState.connect_fail_records`: `(elapsed_s, subtype)` per connect_fail, appended in
  `_apply_fetch_result` BEFORE the ride-exiting break (connect_fail never reaches `job_records`);
  populated on all abort paths.

**fetch.py** (cut trailing paragraphs):
- `_fetch_one_url` always closes the Playwright session (`kill_session`) in a `finally` — fresh
  cookies guaranteed on the next fetch even after an exception.
- `_classify_crawl_result` → `(status, html, markdown_len, err)`: not-success → `connect_fail` if
  lowercased error matches `_PROXY_ERR` substrings else `failed`; no `result.html` → `empty`;
  regwall signal in `raw_markdown` → `regwall`; else `ok`.

**abort.py** (cut Purpose detail + trailing paragraph):
- Split out of `rider.py`: all three abort paths triplicated ~40 lines of report-write-with-fallback;
  `_abort_write_report_and_exit` is the single dedup, parametrized by log prefix / exit code /
  fallback title / stub lines. Output byte-identical to the pre-split version.
- Each public function sets `state.termination` + prints its own log line BEFORE the shared helper
  (done/stall use `[watchdog]`, interrupted `[rider]`); the helper reads `state.termination` back
  for the fallback stub, keeping callers thin (10-13 lines).

**rider.py** (cut Purpose detail + trailing paragraphs):
- `_run_slot` delegates the per-fetch status branch to `_apply_fetch_result` (returns
  `"continue"|"append"|"break"`, mirroring the original inline control flow: `connect_fail` and
  fail-threshold both `"break"` WITHOUT appending; `ok`/`regwall`/below-threshold `"append"`;
  dup-race `ok` `"continue"`s) and `finally`-block `RideRecord` construction to `_finalize_ride`.
  Both mutate a `_RideProgress` scratch dataclass (`burn_count`, `fail_count`, `ride_ok`,
  `positions`, `cf_broke`) — ephemeral, never persisted.
- Signal handler lifecycle: after `state` construction, `loop.add_signal_handler(SIGINT/SIGTERM,
  _abort_interrupted, state, signum)`; removed in `_teardown_pool` (before `watchdog.cancel()`)
  so they don't fire during normal-completion report writing.
- `_watchdog` poll loop (every `min(30, stall_timeout_s/4)`s), in order: (1) append pool sample;
  (2) pool refresh if `POOL_REFRESH_INTERVAL_S = 1800` elapsed — `pool_provider()` via
  `run_in_executor`, guard empty result, atomic assign, cooldown_mgr persists; (3) `all_resolved
  AND in_flight == 0` → clean return; (4) `all_resolved AND in_flight > 0` → `_abort_done`
  (`os._exit(0)`, wedge-after-done); (5) `idle > stall_timeout_s` → `_abort_stall` (`os._exit(1)`).

**reporter.py** (cut Purpose detail + trailing paragraphs):
- `_compute_stats` helpers per concern: `_compute_retry_outcome`, `_compute_pool_windows`,
  `_compute_load_percentiles`, `_compute_connect_fail_stats`; `_write_md` one section-builder per
  heading (`_md_header_counts`, `_md_proxy_riding`, `_md_pool_windows`, `_md_regwall`,
  `_md_connect_fail`, `_md_load_time`, `_md_plots`) — 2026-08-20 mechanical split, output
  byte-identical (synthetic-state diff), no test coverage.
- Stats: `load_times`/`load_perc` (OK fetches, inclusive percentiles, None <2 samples),
  `cf_times`/`cf_perc`, `cf_subtype_counts` (`page_timeout`, `net_timed_out`, `proxy_connect`,
  `other`), `page_timeout_s` (shared axis reference).
- job.md "Connect-fail breakdown" (between Regwall and Success load-time): percentile table
  p50/p90/p95/p99/max + subtype table in fixed order for cross-run comparability; note + no
  histogram when <2 samples. "Success load-time distribution": percentiles over OK fetches only.

**scrape.py** (cut trailing paragraphs):
- `_pool_provider()` — shared async helper for BOTH initial load AND the 30-min watchdog refresh;
  `load_backfill_pool()` in `run_in_executor`, filtered to `BROWSER_ELIGIBLE_PROTOS =
  {"http","socks5"}`, shuffled. Single source of truth.
- Returns `(manifest, RiderState)`; state consumed by `pipeline.py` for `write_riding_report`,
  manifest for `_append_to_raw_manifest`.
- `_build_manifest` status mapping: any ok `job_record` with a written file → `"ok"`; everything
  else → `"failed"`. No `"dead"` (CoinDesk regwalls, never 404s through proxy).

## src/news/platforms/coindesk/DOCS.md

**config.py** (cut constants detail):
- `CALL_DELAY = 0.3` s between cursor calls. `REWARM_EVERY = 240.0` s proactive re-warm interval.
  `CLICKS_WARMUP = 8` — CoinDesk's SSR buffer clears at ~click 6; 8 gives margin.
  `FULL_MODE_FLOOR = "2018-01-01"` — Binance candle data (cross-referencing) starts 2017-08.

**discover.py** (cut Purpose detail + trailing paragraphs):
- Cursor loop pages backward reverse-chronologically. Each 16-article batch: parse, filter
  live-blogs, append genuinely new URLs to per-year shards (`coindesk_{year}.txt`, format
  `YYYY-MM-DD\t<url>`). Termination: oldest article in batch < stop_date. Re-warm: httpx feedpage
  GET first, browser re-warm fallback. Crash-safe: URLs written per-article; re-runs skip
  already-present URLs via `load_discover()` diff. Proactive re-warm fires every `REWARM_EVERY` s
  mid-loop, but ONLY once `httpx_rewarm_confirmed` is set (a prior reactive re-warm proved the
  cheap method works this session).
- Timeframe parsing: `"full"` → FULL_MODE_FLOOR; integer string N → today − N days; anything else
  (incl. `"delta"`) → DEFAULT_DELTA_DAYS (30).
- `load_discover_filtered(discover_dir, year, from_date, to_date, limit)` — standalone; reads
  per-year shards, optional date-range filter, caps at `limit`, returns `[{url, publication_date}]`;
  called by `__init__.py:load_scrape_entries` for `--scrape-only`.
- `cursor_loop` (2026-08-20, 138→63 code lines): accumulators bundled into `_CursorLoopStats`
  (mirrors `_RideProgress`); `_process_batch` per-batch build/filter/dedup/shard-write;
  `_fetch_next_page` cursor-fallback loop (up to `MAX_CURSOR_FALLBACKS` trailing articles as
  anchors); `_handle_cursor_exhaustion` returns `(headers, body, fatal)` so the caller
  distinguishes "re-warm failed, stop now" from "no fallback candidate" without double stop
  messages. Outer `while True:` control flow stays inline.

**cleanup.py** (cut logic detail + trailing paragraphs):
- Logic: H1 start-anchor → first end-anchor (`_END_ANCHORS`: MORE_FOR_YOU, PRIVACY, TAG_FOOTER) →
  `clean_body` (tag-footer strip, image strip, byline/date strip, inline-link substitution,
  paragraph normalization). No H1 → returns `raw_markdown.strip()`.
- `cleanup(raw_markdown, entry)`'s `entry` param is unused — kept for the platform-generic
  signature; do not remove as dead.
- `_RE_TAG_FOOTER` (end-anchor, ≥2 concatenated `[text](url)` groups) vs `_RE_TAG_LINE` (body
  strip, 1+ groups — broader, orphan single-tag lines appear mid-body) are deliberately different
  patterns; `_RE_TAG_LINE` applies BEFORE inline-link substitution while the `[text](url)` form is
  still matchable. `find_end_anchor`'s `end_idx` is exclusive; none found → `(len(body_lines),
  "NONE")`.
- `clean_body` (2026-08-20, 52→8 code lines): `_strip_and_substitute_lines` (Pass 1) +
  `_normalize_paragraphs` (Pass 2) extracted 1:1; leading/trailing trim stayed inline.

**__init__.py** (cut Purpose detail):
- `scrape_engine = "proxy_riding"`; `riding_scrape_config = RidingScrapeConfig()` production
  defaults `n_slots=64, n_browsers=4, stall_timeout_s=300.0, burn_threshold=2,
  page_timeout_ms=8_000`. Raw output `.html`. `proxy_scrape_config = None`. `timeframe = "30"`.
  `load_scrape_entries(...)` delegates to `load_discover_filtered` — the `--scrape-only` interface.

## src/news/platforms/theblock/DOCS.md

**discover.py** (cut mode list + trailing paragraphs):
- Four timeframe modes (no `lastmod` filtering in any): `"delta"` top-2 highest-numbered
  `post_type_post_*` subs (rollover-safe recurring run); `"full"` all subs; `"sub:N"` exactly index
  N; `"sub:A-B"` inclusive range, descending.
- Proxy pool lazy-loaded into `pool_cache` on first fallback; shared across all XML fetches of the
  discover call.
- Timeframe dispatch extracted to `_resolve_target_subs(timeframe, post_subs)` (2026-08-20),
  `RuntimeError` messages preserved verbatim (pytest end-to-end error-message assertions).
- After `discover()`, both orchestrators call `_persist_master_list` → `master_urls.txt`
  (`YYYY-MM-DD\t{url}`, sorted+deduped set-union). No snapshot JSON, no per-year shards.

**cleanup.py** (cut JSON-LD + regex detail):
- `_iter_candidates()` handles: plain dict, dict with `@graph`, top-level array, non-dict values
  silently skipped.
- `_post_clean()` pass order: (1) inline-URL strip `[text](url)` → `text`; (2) TinyMCE bookmark
  spans; (3) Disclaimer line; (4) Copyright (both `The Block.` and `The Block Crypto, Inc.`);
  (5) newsletter CTA; (6) commissioned disclaimer; (7) podcast subscribe CTA; (8) newsletter promo
  block; (9) campus CTA (`theblock.co/campus`); (10) podcast sponsor block (header to EOS, DOTALL);
  (11) trailing-ws strip + blank-run collapse + final strip. Rules validated against the full
  22,995 raw corpus (per-rule counts: `refactor_sweep` area). No `NewsArticle`/`articleBody` →
  returns `""` + stderr log.

**__init__.py** (cut field list):
- Fields: `name/collection="theblock"`, `scrape_engine="proxy_pool"`, `regwall_signals=[]`,
  `proxy_scrape_config=PROXY_SCRAPE_CONFIG`, `timeframe="delta"`, `dedup_mode="hash_only"`,
  `uses_master_list=True`, `precondition_url="https://www.google.com"` (theblock.co 403s plain
  urllib).

## dev/news_pipeline/coindesk_proxy_riding/DOCS.md

**p2_browser_rider.py** (cut Purpose detail): per-URL
`CrawlerRunConfig(proxy_config=ProxyConfig(server=pstr))` → fresh context per config-signature;
`kill_session()` after each fetch. Status routing: ok → write; regwall → requeue + burn_count,
rotate at threshold; connect_fail → requeue + rotate immediately; failed/empty → requeue +
fail_count, rotate at `FAIL_THRESHOLD=2` — ride ends, `finally` calls `mark_burned()` (60-min
cooldown). Watchdog polls `asyncio.sleep(min(30, stall_timeout_s/4))`; on stall → `_abort_stall`:
drain queue + in-flight → `remaining_urls.txt` + `job.md` → `os._exit(1)`. `in_flight_urls`
deliberately NOT in try/finally — wedged slots never reach discard, keeping the wedged URL visible
until abort (diagnostic capture).

**smoke_stage1.py** (cut Purpose detail): three sections — import check (no network; also greps
`abort.py` source for the late-import-of-reporter pattern), deterministic watchdog test (patches
`os._exit`; pre-existing stale `RiderState` construction fails independent of the module split),
mini live run (10 inventory URLs, 2 slots, 1 browser, 300s stall — validates manifest shape,
shuffle, raw `.html` writes). Import lines point at each symbol's post-split owning module.

**test_sigint_report.py** (cut Purpose detail): Test 1 — `_abort_interrupted` SIGINT: partial
`RiderState`, `os._exit` patched to `SystemExit`, asserts exit code 130, `job.md` +
`cumulative.png` written, `termination=interrupted`. Test 2 — SIGTERM → 143.

**test_tail_race.py** (cut Purpose detail): 5 cases — surplus-slots race (2 URLs, 6 slots → both
done, no double-write); write-exactly-once (1 URL, 3 racing slots → exactly 1 raw file);
no-spurious-requeue; normal path (4 URLs, 4 slots); fail-before-success (re-queued, succeeds
second, done exactly once). Mocking via `unittest.mock.patch.object(rider_mod, ...)` works only
because `_fetch_one_url`/`_next_proxy` stay defined in `rider.py` (see `refactor_sweep` area).
