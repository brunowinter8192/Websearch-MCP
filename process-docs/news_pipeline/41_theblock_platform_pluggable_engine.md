# 41 — The Block as a src/news platform: pluggable scrape engine + unified backfill/delta

Decision + design for porting The Block into `src/news/` as a platform, and the contract evolution it
forces. Origin: the user chose to build the article backfill in `src/` (not `dev/`) because backfill is a
permanent capability of every news source — this is integration, not exploration. Builds on the article
structure findings and the validated proxy-rotation engine.

## Decision: scrape step is pluggable (browser | proxy_pool)

The existing `src/news/` shared scrape engine (`engine/scrape.py`) is crawl4ai/**browser** — that is how
CoinDesk fetches (it needs a browser past CoinDesk's protections). The Block fetches via **proxy rotation**
(curl_cffi, no browser): it is server-rendered (JSON-LD `articleBody`), the 27k backfill makes browser-per-URL
infeasible, and volume needs the pool. So "shared scrape engine" no longer holds.

Resolution (implemented in Stage A): a platform declares `scrape_engine ∈ {"browser","proxy_pool"}`; the
pipeline dispatches. **Strictly additive** — `engine/scrape.py` is untouched, CoinDesk's path is byte-for-byte
unchanged, the proxy engine is a parallel path. The validated `dev/.../acquire_pipe/` engine was ported
verbatim (import-fixes only) into `src/news/engine/proxy_pool/`.

## Stage A — DONE (merged on dev)

- `platform.py`: `ProxyScrapeConfig` dataclass (`pool_provider: Callable`, `content_type`, `concurrency=128`,
  `buffer_size=1280`); Protocol gains `scrape_engine: str` + `proxy_scrape_config: ProxyScrapeConfig | None`.
- `coindesk/__init__.py`: `scrape_engine="browser"`, `proxy_scrape_config=None` (additive, 2 lines).
- `pipeline.py`: Stage-3 dispatch — `proxy_pool` → `scrape_entries_proxy()`, `else` → existing `scrape_entries()`
  unchanged.
- `src/news/engine/proxy_pool/` (new): `loop` (run_loop), `fetch`, `cooldown`, `buffer`, `logger`, `janitor`
  (refactored to a `Janitor` class taking jobs/log/report dirs via constructor), `box_lock` (lock_name
  parameterized, default "proxy_pool"), `proxy_key`, `pool_loaders` (from curated_sources), `monosans_loader`,
  `scrape` (`scrape_entries_proxy` entry point). `p3_target` NOT ported (theblock-specific → Stage B).
- `scrape_entries_proxy(entries, output_dir, proxy_cfg)` → manifest `[{url,hash,status,file,char_count,error}]`,
  `done→"ok"` / `dead→"dead"` / `gap→"failed"`; matches the browser manifest so `_run_cleanup` consumes it
  identically. Verified: CoinDesk import clean, `engine/scrape.py` zero edits, mock run produces correct manifest.
- Validation note: the ported modules are faithful copies of the validated engine + import-fixes; runtime
  end-to-end is exercised first by Stage B's live run, not yet.

## Stage B — DONE (merged on dev, end-to-end smoke-validated)

Built as `src/news/platforms/theblock/` (config.py, discover.py, cleanup.py, __init__.py) + `--timeframe`
in `__main__.py` + the additive shared-contract changes (dedup `mode` param, `_run_cleanup` publication_date
fallback). All design points below were implemented exactly as decided.

**End-to-end smoke (`python -m src.news --source theblock --timeframe 48h --skip-index`):** discover → 27
post_type_post subs → highest → 17 entries in 48h window; dedup (hash_only, 17 new, collection empty); scrape
via proxy_pool → 17/17 ok on a 32,189-proxy pool; cleanup → JSON-LD `articleBody`→MD + datePublished mutated
into entries; publish → 17 files `theblock__{datePublished[:10]}__{hash}.md` copied to
`rag-cli/data/documents/theblock/` (un-indexed, --skip-index). Clean bodies are pure article text, no chrome.
The full chain incl. the ported proxy engine is now live-validated on real articles.

Note: the smoke left 17 real un-indexed articles in `data/documents/theblock/`; the next run dedups them
(hash-only skip). precondition_url set to `https://www.google.com` (theblock.co 403s a direct urllib GET; a
proxy_pool platform's home-IP reachability of its own domain is irrelevant — a generic internet check is correct).

The contract implemented:

### Date handling (decided)
- **datePublished is the day of record** — the filename + allocation. Always, no rechecks. From the article's
  JSON-LD `datePublished` (post-fetch).
- **lastmod is ONLY the cheap pre-fetch sieve** — decides which URLs to even fetch. It never touches the
  assigned day. Sub-sitemap `<lastmod>` is a full ISO timestamp w/ NY offset (e.g. `2023-04-26T04:05:56-04:00`),
  day-granularity trivially derived. There is NO published date and NO `news:publication_date` in the sitemap,
  and NO date in the `/post/<id>/slug` URL — datePublished exists only in the fetched article's JSON-LD.
- Consequence (accepted): URL-hash dedup means we never re-fetch an article → we keep the original and miss
  later edits. Fine.

### Dedup (decided)
- Filename `theblock__{datePublished[:10]}__{sha256(url)[:12]}.md`, but the dedup CHECK keys on the **URL-hash
  alone** (glob `theblock__*__{hash}.md`) — the hash is available at discover (from the URL), datePublished is
  not. So overlap is dropped PRE-fetch using only the URL. Dedup is unaffected by timeframe (stable per-article
  name); worst case of overlap = wasted fetch, prevented by the hash-dedup.

### Unified backfill + 48h-delta (decided)
- One `discover(timeframe)`: **48h-delta** (default) = highest `post_type_post_*` sub-sitemap, `lastmod ≥ now−48h`;
  **range [A,B]** = the sub-sitemaps overlapping that span (ascending-by-date pagination: `post_0`=2018, highest=newest),
  `lastmod ∈ [A,B]`; **full** = all post sub-sitemaps, no filter. Entry-point flag, e.g. `--timeframe full|A:B`.
- `cleanup` = parse JSON-LD `NewsArticle` → `articleBody` HTML→MD, NO browser. datePublished from JSON-LD.
- `scrape_engine="proxy_pool"`, `proxy_scrape_config = ProxyScrapeConfig(pool_provider=load_backfill_pool, content_type="html", ...)`.
- `collection="theblock"` — see below.

### Collection per domain (decided — reverses an earlier stage's design)
- Each news domain gets its OWN RAG collection (The Block → `theblock`), NOT one shared `searxng_crypto`.
  Rationale: portals are grazed sequentially and observed for coherence per-portal against BTC daily price;
  uneven backfill depth would otherwise let a deep source numerically dominate top-K in a shared collection.
  Cost: the sentiment layer queries per-collection (fan-out), accepted — it filters by date and never RAGs a
  whole collection anyway. Mechanism is trivial: the platform declares `collection`.

### Stage-B gotcha (must handle)
`pipeline._run_cleanup` reads `publication_date` from the DISCOVER entry (`discover_by_url`), not the manifest.
The Block's datePublished is POST-fetch (JSON-LD), so it is NOT in the discover entry. Stage B must thread
datePublished from the fetched article into cleanup/publish so the filename gets the right day — the CoinDesk
path (date in URL at discover) does not apply here.

## Open
- Stage B build + 48h-delta smoke DONE (above). Remaining: decide whether to index the smoke's 17 articles or
  wipe+redo cleanly; then the ~27k full backfill (`--timeframe full`) — the first at-scale test of the dead-URL
  + exhaustion paths the 64er did not touch.
- `content_handler` writes raw HTML as `{hash}.md` (UTF-8, errors="replace"); The Block cleanup parses HTML, not
  markdown — fine since cleanup is per-platform.
