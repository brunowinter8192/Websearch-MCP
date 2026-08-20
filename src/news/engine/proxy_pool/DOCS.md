# src/news/engine/proxy_pool/

## Role

Generic proxy-rotation scrape engine. Called by `pipeline.py` via `scrape_entries_proxy()` when
`platform.scrape_engine == "proxy_pool"`. Manages a rotating pool of HTTP/SOCKS4/SOCKS5 proxies
with sustained concurrent fetching via curl_cffi chrome impersonation, 60-min pool refresh,
2-strikes lifecycle, per-job lock, and audit trail.

No platform-specific logic lives here — target URLs, content type, and pool provider are all
caller-supplied. Touch this package when changing rotation mechanics, pool loader sources, or
the job lifecycle (lock, janitor). Do NOT touch when adding a browser-engine platform.

## Public Interface

`__init__.py` is empty — callers import modules directly.

- `scrape_entries_proxy(entries, output_dir, proxy_cfg, logger)` in `scrape.py` — sole entry point for `pipeline.py`; `logger` is a caller-supplied `AcquireLogger`.
- `load_backfill_pool()` in `pool_loaders.py` — used by platform `ProxyScrapeConfig.pool_provider`; returns `(pool, sources)` where `sources` is `[{url, ok, count}, …]` per fetched URL.

## Flow

1. `pipeline.py:_run_pipeline_proxy_pool` acquires `box_lock`, instantiates `Janitor` + `AcquireLogger`; calls `start_job` (wipes log_dir) before opening the JSONL. The unified job spans discover + scrape: discovery proxy fetches in `theblock/discover.py:_fetch_xml` call `logger.record_attempt`; article scrape fetches call it via `run_loop`.
2. `scrape_entries_proxy` receives the caller-supplied `logger` + instantiates `PersistentCooldownManager`; delegates to `run_loop`.
3. `run_loop` sustains concurrent rotation: `pool_provider()` → `build_active_buffer` → batches of `(proxy, URL)` → `fetch_url` via `ThreadPoolExecutor`.
4. Per ok fetch: `content_handler` decodes bytes → writes `output_dir/{hash}.md`.
5. `logger` streams all events to JSONL (discovery + scrape combined); `pipeline.py:_run_pipeline_proxy_pool` calls `logger.close()` + `janitor.end_job` in `finally` — fires on all exit paths including 0-entries and 0-new-after-dedup early returns. `end_job` derives `job.md` + `cumulative_hits.png`.
6. `_build_manifest` maps `(done, dead, gap)` → `[{url, hash, status, file, char_count, error}]` matching the browser engine manifest contract.

## Modules

### scrape.py (90 LOC)

**Purpose:** Proxy-pool scrape entry point — wires `run_loop` with a caller-supplied `AcquireLogger`; returns pipeline manifest. Job lifecycle (box_lock, Janitor, AcquireLogger) is owned by `pipeline.py:_run_pipeline_proxy_pool`.
**Reads:** `entries` list (in-memory) + `proxy_cfg.pool_provider()`.
**Writes:** `output_dir/{url_hash}.md` per ok fetch.
**Called by:** `pipeline.py:_run_pipeline_proxy_pool`.
**Calls out:** `loop.py`, `cooldown.py`, `logger.py` (type reference only).

---

### loop.py (218 LOC)

**Purpose:** Sustained concurrent rotation loop — 60-min pool refresh, 2-strikes lifecycle, tail-race, wait-on-exhaustion, stall-terminate.
**Reads:** `pool_provider()` callback (returns `(pool, sources)`) + target URL list (in-memory).
**Writes:** delegates state to `AcquireLogger` + `PersistentCooldownManager`; calls `content_handler` per ok fetch. Returns `(done, dead, gap)`. After each `pool_provider()` call: `record_pool_refresh(len(pool))` then `record_pool_source(url, ok, count)` per source.
**Called by:** `scrape.py:scrape_entries_proxy`.
**Calls out:** `fetch.py`, `cooldown.py`, `logger.py`, `buffer.py`.

Stall-terminate (`STALL_TIMEOUT_S = 3600`): `_last_progress` tracks the last time a URL resolved
to `done` or `dead` (queue shrinks). If `now - _last_progress >= STALL_TIMEOUT_S` at the top of
the `while queue:` loop, the loop breaks and returns `gap = list(queue)` — the remaining unresolved
URLs. These flow through `_build_manifest` as `status="failed"` and land in
`data/news/{name}/discover/failed_urls.txt` via `_update_blocked_urls`. Only done/dead events advance
`_last_progress` — a batch of pure proxy-failures does not reset the clock. Stall fires when
poison URLs (neither 200 nor 404 from origin) consume all proxies for a full pool-cycle with
no terminal resolution.

Key: `_sleep = time.sleep` is a module-level alias — patch it in tests, not `time.sleep`.

---

### fetch.py (46 LOC)

**Purpose:** curl_cffi chrome-impersonating HTTP fetch primitive + content-type gate (`"html"` | `"xml"`).
**Reads:** remote URL via curl_cffi Session (routed through proxy).
**Writes:** nothing — returns `(status, content)` where `status ∈ {"ok", "dead", "fail"}`.
**Called by:** `loop.py:run_loop`; `theblock/discover.py:_fetch_xml` (proxy fallback during discovery).
**Calls out:** `curl_cffi`.

---

### cooldown.py (47 LOC)

**Purpose:** In-memory per-job cooldown tracking — clean slate per instantiation, 60-min burn window.
**Reads:** nothing (in-memory only).
**Writes:** nothing.
**Called by:** `buffer.py`, `loop.py`, `scrape.py`.
**Calls out:** `proxy_key.py:proxy_key`.

---

### buffer.py (45 LOC)

**Purpose:** Active-buffer helpers — `build_active_buffer`, `refill_buffer`; holds `BUFFER_SIZE = 1280`, `DEFAULT_CONCURRENCY = 128`.
**Reads:** proxy pool + `PersistentCooldownManager` eligibility (in-memory).
**Writes:** returns new buffer lists (pure — no mutation of inputs).
**Called by:** `loop.py:run_loop`.
**Calls out:** `cooldown.py:PersistentCooldownManager`.

---

### logger.py (56 LOC)

**Purpose:** Streams per-fetch events to JSONL (line-buffered, kill-safe). Stats derived by `janitor.end_job`.
**Reads:** events pushed via `record_attempt` / `record_pool_refresh` / `record_pool_source`.
**Writes:** `{platform_dir}/proxy_pool_logs/acquire_events_{ts}.jsonl` (streamed, line-buffered). Event types: `{proxy_key, ts, url, result}` (attempt), `{event:"pool_refresh", size, ts}`, `{event:"pool_source", url, ok, count, ts}`.
**Called by:** `pipeline.py:_run_pipeline_proxy_pool` (instantiates + closes); `loop.py` (`record_attempt` + `record_pool_refresh` + `record_pool_source` per pool load); `theblock/discover.py:_fetch_xml` (`record_attempt` per discovery proxy fetch).
**Calls out:** `proxy_key.py:proxy_key`.

---

### janitor.py (284 LOC)

**Purpose:** Job lifecycle — `Janitor(jobs_dir, log_dir, report_dir)`; wipes transient dirs at start; reads JSONL → `job.md` + `cumulative_hits.png` at end. `_compute_window_stats` buckets attempt events into 60-min windows from t0 and derives per-window `{probiert, erfolgreich, urls_handled, fetch_attempts, pool_size}` (`urls_handled` = distinct target URLs; `fetch_attempts` = total attempt events). `_group_pool_sources` groups `pool_source` events by preceding `pool_refresh` in JSONL order; rendered as a `## Pool source breakdown` section at the bottom of `job.md` (absent when no pool_source events — backward-compatible with old JSONL).
**Reads:** JSONL at `jsonl_path` passed to `end_job`.
**Writes:** `{jobs_dir}/{job_id}/job.md`, `cumulative_hits.png`; wipes `log_dir` + `report_dir` at start and end.
**Called by:** `pipeline.py:_run_pipeline_proxy_pool`.
**Calls out:** `matplotlib.pyplot` (lazy import in `_write_plot`), `statistics` (stdlib).

---

### box_lock.py (102 LOC)

**Purpose:** System-wide single-job flock — `acquire(job, target, lock_name="proxy_pool")`; crash-safe (kernel releases flock on process death). Raises `LockBusyError` on contention.
**Reads:** `~/.websearch-locks/{lock_name}.lock` sidecar (in `cleanup_stale` + busy message).
**Writes:** `~/.websearch-locks/{lock_name}.{flock,lock}`.
**Called by:** `pipeline.py:_run_pipeline_proxy_pool`.
**Calls out:** `fcntl`, `os` (stdlib).

---

### proxy_key.py (16 LOC)

**Purpose:** Canonical proxy key — `proxy_key(proto, host_port) → "proto://host:port"` (auth stripped if present).
**Reads:** nothing.
**Writes:** nothing (pure).
**Called by:** `cooldown.py`, `logger.py`, `pool_loaders.py`.
**Calls out:** stdlib only.

---

### pool_retry.py (22 LOC)

**Purpose:** Bounded exponential-backoff retry for httpx fetches — `fetch_with_retry(fn)` calls `fn()` up to 5 times, sleeping 1/2/4/8s between attempts; re-raises last exception on final failure.
**Reads:** nothing.
**Writes:** nothing (pure control-flow wrapper).
**Called by:** `monosans_loader.py:_fetch_json`, `pool_loaders.py:_fetch_bare_txt` / `_fetch_roosterkid` / `_fetch_proxifly`.
**Calls out:** stdlib only.

Key: `_sleep = time.sleep` is a module-level alias — patch `pool_retry._sleep` in tests, not `time.sleep`.

---

### pool_loaders.py (341 LOC)

**Purpose:** 18 proxy-source loaders + `load_backfill_pool()` — fetches all sources per-URL with retry and per-source failure isolation; returns `(pool, sources)` where `pool` is deduped `[(protocol, host:port)]` (~32k unique) and `sources` is `[{url, ok, count}, …]` one entry per URL.

Sources active in `load_backfill_pool` (46 URLs across 18 repos):
monosans, roosterkid, TheSpeedX, themiralay, r00tee, iplocate, sunny9577, ALIILAPRO, dpangestuw,
Zaeem20, zloi-user, hookzof, proxifly (JSON), jetkai (http/https/socks4/socks5),
prxchk (http/socks5, validated, refreshed every 10 min),
ShiftyTR (http/socks5, updated hourly),
vakhov (http/socks5, fresh/working),
MuRongPIG (http/socks5 validated subset — `_checked` files only; raw dumps excluded).
databay-labs removed (repo deleted from GitHub — all URLs 404).

**Reads:** 44 GitHub raw proxy-list URLs via httpx (each wrapped in `fetch_with_retry`).
**Writes:** nothing.
**Called by:** `theblock/config.py` (via `ProxyScrapeConfig.pool_provider`); `theblock/discover.py:_fetch_xml` (fallback pool, unpacks `pool, _ = load_backfill_pool()`).
**Calls out:** `httpx`, `pool_retry.py:fetch_with_retry`, `monosans_loader.py:load_monosans_proxies`, `proxy_key.py:proxy_key`.

Key: `_try_source(url, fn, entries, sources)` is the per-URL isolation helper — catches all exceptions after retries exhaust, records `ok=False`, continues. Never raises from `load_backfill_pool`.

---

### monosans_loader.py (40 LOC)

**Purpose:** Fetch monosans/proxy-list JSON; return `[(protocol, host:port)]` in source order. `_fetch_json` is wrapped with `fetch_with_retry` — transient network errors ride out automatically.
**Reads:** monosans GitHub raw JSON URL via httpx.
**Writes:** nothing.
**Called by:** `pool_loaders.py:load_backfill_pool` (via `_try_source`).
**Calls out:** `httpx`, `pool_retry.py:fetch_with_retry`.

## Gotchas

- `pool_loaders.py` at 341 LOC exceeds the 200-LOC heuristic — no extractable concern exists (flat list of 18 loader functions sharing one `_merge_dedup` utility). Do not split.
- `janitor.end_job` calls `jsonl_path.unlink()` then wipes `log_dir`. Interrupt between these two orphans the JSONL in `log_dir`. Non-critical: `start_job` wipes `log_dir` at the next run.
- `box_lock`: SIGTERM kills Python before `finally` runs → sidecar stays; kernel releases flock. Next `acquire()` recovers via `cleanup_stale()` (dead-PID detection).
- `_sleep` in `loop.py` AND `pool_retry.py` are both module aliases (`_sleep = time.sleep`) — patch the alias in the target module in tests, not `time.sleep` directly. For retry tests patch `pool_retry._sleep`; for exhaustion-sleep tests patch `loop._sleep`.
