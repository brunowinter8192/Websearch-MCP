# news-area comment/docstring standards conformance sweep (2026-08-20)

Full comment-rule conformance pass across `src/news/**` — every file in the violation map (30 files:
`engine/{dedup,publish,scrape,scrape_job,browser_reporter}.py`,
`engine/proxy_pool/{box_lock,buffer,cooldown,fetch,janitor,logger,loop,pool_loaders,pool_retry,scrape}.py`,
`engine/proxy_riding/{abort,cooldown,reporter,scrape}.py`,
`platforms/coindesk/{__init__,browser,cleanup,config,discover}.py`,
`platforms/theblock/{__init__,cleanup,discover}.py`,
`__main__.py`, `platform.py`, `pipeline.py`, `pipeline_support.py`). Zero code changes — comments
and docstrings only, verified by full-suite parity (182 passed / 10 failed, unchanged) and targeted
re-runs (`test_theblock_discover.py`, `test_proxy_pool.py`, `test_theblock_clean_pass.py`: 40/2
unchanged split — same 2 pre-existing `test_run_loop_refresh_*` failures) plus output-identity checks
(`proxy_riding` synthetic `job.md` byte-diff, `python -m src.news --help` text-diff) after every
batch of edits.

## Method

Every function/class docstring converted to a single `#` line directly above the `def`/`class` (the
codebase's established header convention — no file in this area used docstrings before this sweep
except the ones fixed here). Every multi-line `#` comment block condensed to one line. Every trailing
comment on a constant/field checked against the owning `DOCS.md` before deletion — per the explicit
mandate NOT to blind-delete constant annotations, since several carried the ONLY semantic doc of that
value. `__doc__`/doctest usage grepped repo-wide first (4 hits, all in unrelated `dev/` scripts using
`argparse(description=__doc__)` — none in `src/news/**`) — docstring removal confirmed safe.

## Triage tally (all 30 files)

| Category | Count | Disposition |
|---|---|---|
| Function/class docstrings converted to 1-line `#` header | 34 | format-only change, content mostly preserved verbatim or condensed |
| Multi-line `#` header blocks condensed to 1 line | 12 | content deleted-as-covered or moved (see below) |
| Trailing/inline comments deleted as covered | ~40 | verified against owning `DOCS.md` first |
| Substance moved into owning `DOCS.md` (Purpose/Gotchas) | 19 | new documentation, not previously present |
| Substance moved into this process-docs entry | 1 block (7 corpus-evidence facts) | see below — too granular for `DOCS.md`, genuine investigation record |
| Dead code flagged (not removed — comment-only pass) | 3 | `engine/scrape.py:_RUN_CFG`, `pool_loaders.py`'s 17 per-source `load_X_proxies()` functions, (both already unused pre-sweep, discovered while triaging their comments) |

No case required stopping to ask — every substantive comment found a home (an existing/enriched
`DOCS.md` paragraph, a `DOCS.md` Gotcha, or this entry).

## Per-file breakdown

| File | Docstrings→header | Multi-line blocks condensed | Trailing/inline deleted | DOCS.md additions |
|---|---|---|---|---|
| `engine/dedup.py` | 0 | 1 (`filter_new_entries`) | 0 | 0 |
| `engine/publish.py` | 0 | 2 (`_write_index`, `publish_articles`) | 0 | 0 |
| `engine/scrape.py` | 0 | 4 (`scrape_entries`, `_ensure_domain_state`, `_gate_domain`, `RegwallGuardError`) | 3 (`REGWALL_FAIL_THRESHOLD`, `_RUN_CFG`'s 2 field comments) | 1 (`_RUN_CFG` dead-code flag) |
| `engine/scrape_job.py` | 0 | 2 (`_append_to_raw_manifest`, `_update_blocked_urls`) | 1 (`exc.manifest` comment) | 0 |
| `engine/browser_reporter.py` | 0 | 0 (already conformant from the prior function-size sweep) | 1 (`_BACKFILL_TOTAL`) | 0 |
| `proxy_pool/box_lock.py` | 1 (`LockBusyError`) | 0 | 3 (`cleanup_stale`'s docstring + 2 inline `# ... → held`) | 1 (`cleanup_stale` mechanism) |
| `proxy_pool/buffer.py` | 0 | 0 | 2 (`BUFFER_SIZE`, `DEFAULT_CONCURRENCY`) + 2 docstrings deleted (headers already existed) | 1 (10× relationship, eligibility/refill mechanics) |
| `proxy_pool/cooldown.py` | 6 (class + 5 methods, none had `#` headers before) | 0 | 1 (`COOLDOWN_S`) | 0 (already covered) |
| `proxy_pool/fetch.py` | 0 | 0 | 0 (docstring merged into existing header, deleted) | 1 (status taxonomy) |
| `proxy_pool/janitor.py` | 3 (class + 2 methods) | 0 | 0 (docstring on `_group_pool_sources` deleted, header already existed) | 1 (attempt-events-ignored detail) |
| `proxy_pool/logger.py` | 1 (class) | 0 | 0 (3 method docstrings converted to new headers) | 0 |
| `proxy_pool/loop.py` | 0 | 1 (`_compute_sleep`'s redundant docstring, deleted) | 3 (`_sleep`, `REFRESH_INTERVAL_S`, `STALL_TIMEOUT_S`) + `run_loop`'s body-comment moved to header | 0 (already covered from function-size sweep) |
| `proxy_pool/pool_loaders.py` | 20 (`load_backfill_pool` + 17 `load_X_proxies` + `_try_source` docstring deleted, `_merge_dedup` converted) | 0 | 1 (`(proto, url) pairs` note) | 1 (dead-code flag) |
| `proxy_pool/pool_retry.py` | 1 (`fetch_with_retry`, deleted — header already existed) | 0 | 2 (`_sleep`, `_BACKOFF`) | 1 (~90s worst-case math, restored after an initial over-eager delete — see below) |
| `proxy_pool/scrape.py` | 1 (`scrape_entries_proxy`, deleted — header existed) | 0 | 1 (`fetched` dict shape, self-evident from adjacent code) | 1 (manifest status taxonomy) |
| `proxy_riding/abort.py` | 0 | 0 | 0 | 0 (already fully conformant) |
| `proxy_riding/cooldown.py` | 1 (class, 10-line) | 0 | 3 (3 constants) + 3 inline (`# fixed path` etc., self-evident) | 0 (already covered) |
| `proxy_riding/reporter.py` | 0 | 1 (`_write_load_hist`, leftover from the prior function-size sweep) | 0 | 1 (post-nav load_s-exceeds-timeout landmine) |
| `proxy_riding/scrape.py` | 0 | 2 (`scrape_entries_riding`, `_build_manifest`, leftover from the prior sweep) | 0 | 0 (already covered) |
| `coindesk/__init__.py` | 0 | 0 | 1 (`timeframe`) | 0 (covered) |
| `coindesk/browser.py` | 0 | 1 (`browser_load_feed`) | 0 | 0 (covered) |
| `coindesk/cleanup.py` | 0 | 3 (`cleanup`, `find_end_anchor`, `_find_news_article` — 2 leftover from prior sweep) | 3 (grouping labels: end-anchor, tag-footer, in-body) | 2 (unused `entry` param note, TAG_FOOTER/TAG_LINE relationship + `find_end_anchor` exclusive-end contract) |
| `coindesk/config.py` | 0 | 0 | 9 (all constant/grouping comments) | 1 (5-fact paragraph: REGWALL_SIGNALS precision, CALL_DELAY, REWARM_EVERY, CLICKS_WARMUP SSR rationale, FULL_MODE_FLOOR Binance rationale) |
| `coindesk/discover.py` | 0 | 2 (`discover`, `load_discover_filtered` — leftover from prior sweep) | 0 | 0 (covered) |
| `theblock/__init__.py` | 0 | 0 | 3 (`precondition_url`, `timeframe`, `uses_master_list`) | 0 (covered) |
| `theblock/cleanup.py` | 0 | 1 (`cleanup`) | 7 corpus-evidence comments (see below) | 1 (EOS-anchor Gotcha) + this entry (7 corpus facts) |
| `theblock/discover.py` | 0 | 0 (already conformant) | 1 (`_fetch_xml`'s `return content` comment, self-evident from adjacent code) | 0 |
| `__main__.py` | 0 | 0 | 0 (2 side-effect-import comments kept — fit the cross-module-import allowed type in spirit) | 0 |
| `platform.py` | 0 | 0 | 10 (every dataclass field + Protocol attr) | 1 (name dual-purpose, regwall_signals empty-disables-guard landmine, discover() shape, ProxyScrapeConfig field meanings) |
| `pipeline.py` | 0 | 0 | 1 (`SCRAPE_CHUNK_SIZE`) | 0 (200-URL chunking already covered; crash-loss-window rationale judged self-evident from the chunking Purpose text) |
| `pipeline_support.py` | 0 | 0 | 1 (`PROJECT_ROOT`) | 0 (self-evident, matches the same decision made for the analogous `coindesk/config.py` constant) |

## `pool_retry.py`'s `_BACKOFF` — a self-correction during the sweep

First pass deleted `_BACKOFF`'s trailing comment (`# inter-attempt waits (s); 5 attempts total, ~90s
max at FETCH_TIMEOUT=15`) alongside the adjacent `_sleep` comment without checking it against
`DOCS.md` first — caught on review before commit. `DOCS.md` already stated the 1/2/4/8s backoff
sequence but NOT the combined worst-case latency. Restored as a `DOCS.md` addition instead of a code
comment: 4 backoff sleeps (1+2+4+8=15s) + 5 fetch attempts × `FETCH_TIMEOUT=15s` = ~90s worst case.
Flagged here as the sweep's one near-miss on the "do not blind-delete constant comments" mandate —
caught before it became a lost-substance case, not after.

## `theblock/cleanup.py` corpus-verification evidence (moved here — too granular for `DOCS.md`)

`DOCS.md` already documents WHAT each `_post_clean()` regex does and in what order (11-step list,
pre-existing before this sweep). The per-rule corpus file-counts that justified each rule's shape are
investigation/calibration evidence, not durable module documentation — recorded here instead:

- `_COPYRIGHT_RE`: extended to also match the old brand name "The Block Crypto, Inc." — found in 2
  files of the validated corpus.
- `_NEWSLETTER_CTA_RE`: broadened to drop the trailing-`_` requirement because many CTAs close with
  "here." rather than a markdown-italic-closing `_`.
- `_MCE_SPAN_RE`: TinyMCE bookmark spans that `html2text` passes through as literal HTML — found in
  19 files.
- `_COMMISSIONED_RE`: commissioned-content disclaimer footer — found in 534 files (with an optional
  italic wrapper).
- `_PODCAST_SUB_CTA_RE`: podcast subscribe-CTA line, handling `_`/`*`/`__` markdown-prefix variants —
  found in 371 files.
- `_NEWSLETTER_PROMO_RE`: newsletter promo 2-line block (header + subscribe line) — found in 99 files.
- `_CAMPUS_CTA_RE`: campus trial CTA (any line containing `theblock.co/campus`) — found in 56 files;
  the URL is a pure product-CTA, never appears in editorial prose in the validated corpus.
- `_SPONSOR_BLOCK_RE`: podcast sponsor block, strips header-to-EOS — found in 252 files; the
  EOS-anchor (no closing pattern) was proven safe by checking all 252/252 matching files: zero
  editorial content follows the sponsor-block header, only sponsor descriptions / community promos /
  copyright-disclaimer lines (already stripped by the earlier rules in the pass) appear after it.
  `\*{0,2}` in the pattern covers 2 files whose header lacks the `**` bold prefix.

All validated against the full 22,995-file raw corpus (this aggregate figure IS in `DOCS.md` already;
only the per-rule breakdown is new here).

## Dead code found (flagged in `DOCS.md`, not removed — out of scope for a comment-only pass)

- `engine/scrape.py:_RUN_CFG` — a module-level `CrawlerRunConfig` built but never referenced;
  `scrape_entries` constructs its own `run_cfg` locally instead.
- `proxy_pool/pool_loaders.py`'s 17 per-source `load_X_proxies()` functions (`load_curated_proxies`
  through `load_murongpig_proxies`) — `load_backfill_pool` calls `_try_source` + lambdas directly,
  never these wrapper functions. The only live callers of same-named functions are a separate,
  non-importing copy in `dev/news_pipeline/theblock/curated_sources.py` (confirmed via repo-wide
  grep — no `src/`-internal caller of any of the 17).

Both flagged as `DOCS.md` Gotchas/notes for a future cleanup pass; removing them was out of scope for
a zero-code-change sweep.
