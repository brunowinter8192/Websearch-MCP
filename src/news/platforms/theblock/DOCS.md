# src/news/platforms/theblock/

## Role

The Block platform implementation. Uses the `proxy_pool` scrape engine (curl_cffi rotation,
no browser) and its own RAG collection `"theblock"`. Discovery is sitemap-based (not feed-scroll).
`dedup_mode` attribute is not used by `run_pipeline` (which always uses `mode="raw"` against
`data/news/theblock/raw/`). The Block has no `publication_date` at discover time — the date
comes from JSON-LD post-fetch and is mutated into `entry["publication_date"]` by `cleanup.py`.

Imported for side-effects by `__main__.py` — the import registers `TheBlockPlatform()` into the
registry. No other module should import from here directly.

## Public Interface

`__init__.py` exports `TheBlockPlatform` (implements `Platform` Protocol).
Auto-registers via `register(TheBlockPlatform())` at module end.

Extra platform attributes (not in Protocol):
- `timeframe: str` — discovery mode (`"delta"` default); overwritten by `__main__` from `--timeframe`.
- `dedup_mode: str = "hash_only"` — legacy attribute, not consumed by `run_pipeline` (which uses `mode="raw"`).
- `uses_master_list: bool = True` — signals `pipeline.py` to write a single `data/news/theblock/discover/master_urls.txt`
  instead of per-year shards. Consumed via `getattr(platform, "uses_master_list", False)` in both
  `run_discover_only()` and `run_pipeline()` proxy_pool path.

## Modules

### config.py (14 LOC)

**Purpose:** Platform constants — `SITEMAP_INDEX`, `DIRECT_TIMEOUT`, `DEFAULT_TIMEFRAME`,
`PROXY_SCRAPE_CONFIG` (`ProxyScrapeConfig(pool_provider=load_backfill_pool, content_type="html")`),
`SCRAPE_CONFIG` (default `ScrapeConfig()`, required by Protocol but ignored by proxy path).
**Reads:** nothing.
**Writes:** nothing.
**Called by:** `__init__.py`, `discover.py`.
**Calls out:** `engine/proxy_pool/pool_loaders.py:load_backfill_pool`.

---

### discover.py (170 LOC)

**Purpose:** Sitemap-based article discovery. Fetches theblock sitemap index (direct httpx →
proxy pool fallback), selects `post_type_post_*` sub-sitemaps by mode (`delta`/`full`/`sub:N`/`sub:A-B`),
parses `<url>/<loc>/<lastmod>` blocks — no date filtering. Returns `[{url, lastmod}]` — NO
`publication_date` (comes from JSON-LD post-fetch in cleanup).
**Reads:** `https://www.theblock.co/sitemap_tbco_index.xml` + selected sub-sitemaps (network).
**Writes:** nothing.
**Called by:** `__init__.py:TheBlockPlatform.discover`.
**Calls out:** `httpx`, `engine/proxy_pool/fetch.py:fetch_url`,
`engine/proxy_pool/pool_loaders.py:load_backfill_pool`.

Four timeframe modes (read from `self.timeframe`); no `lastmod` date filtering in any mode:
- `"delta"` (default) — top-2 highest-numbered `post_type_post_*` subs, all URLs. Rollover-safe recurring run.
- `"full"` — all `post_type_post_*` subs, all URLs. Complete backfill.
- `"sub:N"` — exactly the sub whose trailing index == N (e.g. `sub:0` → `post_type_post_0.xml`), all URLs.
- `"sub:A-B"` — all subs with trailing index in [A, B] inclusive, returned descending (newest-first).

Proxy pool is lazy-loaded into `pool_cache` on first fallback; shared across all XML fetches
in the same discover call (index + sub-sitemaps) to avoid loading the pool twice.

`discover`'s timeframe dispatch (2026-08-20, extracted from `discover()`'s body) lives in
`_resolve_target_subs(timeframe, post_subs)` — the four-mode branch above, `RuntimeError` messages
preserved verbatim (pytest-covered: `tests/test_theblock_discover.py`'s `discover("sub:27-24")` /
`discover("sub:x-y")` / `discover("sub:10-20")` end-to-end error-message assertions).

After `discover()`, both `run_discover_only()` and `run_pipeline()` call
`_persist_master_list(entries, master_path, log)` → `data/news/theblock/discover/master_urls.txt`
(format `YYYY-MM-DD\t{url}`, sorted+deduped, set-union append). No timestamped snapshot JSON,
no per-year shards. Persistence is in `pipeline_support.py:_persist_master_list`, not in discover.py.

---

### cleanup.py (140 LOC)

**Purpose:** Parse JSON-LD `NewsArticle` block from raw HTML fetched by proxy engine →
extract `articleBody` (HTML) → convert to Markdown via `crawl4ai.html2text.HTML2Text` →
apply `_post_clean()` regex pass → mutate `entry["publication_date"] = datePublished`.
**Reads:** raw HTML string (proxy engine output), entry dict (scrape manifest).
**Writes:** mutates `entry["publication_date"]` in place.
**Called by:** `clean_pass.py:_run_clean_pass` (proxy_pool arm, dispatched from `pipeline.py:_run_pipeline_proxy_pool`).
**Calls out:** `crawl4ai.html2text` (bundled, no new dep).

JSON-LD shape hardening — `_iter_candidates()` handles all common shapes without crashing:
plain dict, dict with `@graph`, top-level array, non-dict values (int/str) silently skipped.

`_post_clean()` regex pass (applied after html2text, in this order):
1. Inline-URL strip: `[text](url)` → `text`.
2. TinyMCE bookmark spans (`_MCE_SPAN_RE`): `<span[^>]*data-mce-type[^>]*>.*?</span>` removed (DOTALL).
3. Disclaimer line (`_DISCLAIMER_RE`): `^Disclaimer: The Block is an independent media outlet.*$` removed.
4. Copyright line (`_COPYRIGHT_RE`): covers both `The Block.` and old brand `The Block Crypto, Inc.`.
5. Newsletter CTA (`_NEWSLETTER_CTA_RE`): `^_.*subscribe to the .*newsletter.*$` (trailing `_` not required).
6. Commissioned disclaimer (`_COMMISSIONED_RE`): `^_?This post is commissioned\b.*$`.
7. Podcast subscribe CTA (`_PODCAST_SUB_CTA_RE`): `^[*_]*Listen below[,.]?\s+and subscribe to\b.*$`.
8. Newsletter promo block (`_NEWSLETTER_PROMO_RE`): `**The Block Newsletters` header + subscribe line.
9. Campus CTA (`_CAMPUS_CTA_RE`): any line containing `theblock.co/campus`.
10. Podcast sponsor block (`_SPONSOR_BLOCK_RE`): `\n\*{0,2}This episode is brought to you by\b.*` to EOS (DOTALL).
11. Trailing whitespace per line; blank-run collapse to single blank; final strip.

Rules validated against full 22,995 raw corpus.
Fallback: if no `NewsArticle` or no `articleBody` → returns `""` + stderr log, no crash.

---

### __init__.py (32 LOC)

**Purpose:** `TheBlockPlatform` class wrapping config + discover + cleanup; auto-registers on import.
Fields: `name/collection="theblock"`, `scrape_engine="proxy_pool"`, `regwall_signals=[]`,
`proxy_scrape_config=PROXY_SCRAPE_CONFIG`, `timeframe="delta"`, `dedup_mode="hash_only"`,
`uses_master_list=True`.
`precondition_url="https://www.google.com"` (theblock.co returns 403 on plain urllib).
**Called by:** `__main__.py` (side-effect import).
