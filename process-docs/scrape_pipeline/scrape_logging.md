# Scrape Pipeline — Per-URL Logging

*Snapshot as of 2026-06 — historical process record; the live current state is the source code, not this file.*

## Per-URL Scrape Log

### Current State

**Architecture:** Sidecar split. Every `scrape_url` call emits two artifacts:
1. One structured JSONL record → `src/logs/scrape_log.jsonl` (append-only, gitignored)
2. One content sidecar → `src/logs/scrape_content/<ts>_<url_slug>.md` — the exact final content the caller received

**What is logged:** the FINAL output the caller receives, not intermediate state. For `scrape_url` (filtered mode): the truncated `fit_markdown` (or `raw_markdown` after fallback), after `truncate_content` is applied. Pre-filter and pre-truncation content is NOT logged as sidecar — only the bytes the agent sees.

**Sidecar policy by outcome:**
- `outcome == "ok"` → sidecar written (final content)
- `outcome == garbage type string` → sidecar written (`garbage_content` field from `try_scrape` meta — content that triggered garbage classification, for inspection)
- `outcome == "empty"` → `content_path: null`, no sidecar written

**Log path:** `SEARXNG_SCRAPE_LOG_PATH` env var → fallback `src/logs/scrape_log.jsonl`. Sidecar dir: `<log_dir>/scrape_content/`. Fail-soft: write errors are logged as WARNING, scrape result still reaches caller.

**Implementation:** `src/scraper/scrape_logger.py` — `log_scrape(record)` + `write_sidecar(url, ts, content, outcome, mode) -> str | None`. Called at every return path of `scrape_url_workflow`.

**JSONL record schema:**
```json
{
  "ts": "2026-06-01T14:22:01.123Z",
  "url": "https://example.com/article",
  "domain": "example.com",
  "mode": "filtered",
  "outcome": "ok",
  "timings_ms": {"total_wall": 7241},
  "http_status": 200,
  "content_type": "text/html; charset=utf-8",
  "bytes_returned": 4802,
  "bytes_raw_markdown": 11340,
  "fallback_to_raw": false,
  "truncated": false,
  "consent_stripped": false,
  "garbage_type": null,
  "content_path": "scrape_content/2026-06-01T14-22-01.123Z_example-com-article.md"
}
```

**Field semantics:**

| Field | Values / Notes |
|-------|---------------|
| `mode` | `"filtered"` — only mode (raw mode removed) |
| `outcome` | `"ok"` \| garbage type string (e.g. `"cookie_wall"`, `"cloudflare"`) \| `"empty"` |
| `timings_ms.total_wall` | wall time of full `scrape_url_workflow` call in ms |
| `http_status` | HTTP status from crawl result; null on network failure |
| `content_type` | Content-Type header from crawl result; null if N/A |
| `bytes_returned` | byte length of final content (after truncation); null on failure |
| `bytes_raw_markdown` | raw_markdown length before PruningContentFilter; null on failure |
| `fallback_to_raw` | true iff `fit_markdown < MIN_CONTENT_THRESHOLD` triggered fallback to `raw_markdown` |
| `truncated` | true iff 15K cap applied |
| `consent_stripped` | true iff `strip_consent_prefix()` changed content |
| `garbage_type` | 7 values from `is_garbage_content()` or null; set on failure, null on success |
| `content_path` | relative path under log dir, e.g. `"scrape_content/<file>.md"`; null when no content |

**Sidecar file format:**
```markdown
<!-- url: https://example.com/article -->
<!-- ts: 2026-05-23T22:30:01.234Z -->
<!-- outcome: ok -->
<!-- bytes: 5104 -->
<!-- mode: filtered -->

<actual final markdown content exactly as the agent received it>
```

**URL slug derivation** (deterministic, no randomness): strip `https://` or `http://` → replace non-alphanumeric with `-` → collapse runs → strip leading/trailing `-` → cap at 80 chars.

**ts sanitization for filenames:** replace `:` with `-` (so `2026-05-23T22:30:01.234Z` → `2026-05-23T22-30-01.234Z`).

### Evidence

Design session 2026-05-23. No dev/ probe — this is a logging-emission feature with no empirical tradeoffs to measure. The sidecar split (structured analytics vs. raw content) mirrors the pattern used in `src/search/query_logger.py` (structured JSONL only, no content). Goal: build a data basis over weeks/months to (a) find scraping problems systematically and (b) enable future benchmarks of current Crawl4AI+PruningContentFilter vs. alternatives (Trafilatura, Mozilla Readability) without re-scraping.

### Open Questions

- **Rotation policy:** The per-scrape content sidecar directory grows unboundedly (gitignored, not committed). No rotation or cleanup logic exists. To be addressed if storage becomes uncomfortable (> N GB). Options: TTL-based cleanup script, size cap with LRU eviction, move old sidecars to cold storage.
- **Schema versioning:** no version field in the record schema. If future analysis surfaces fields to add/rename, existing records won't have the new fields. Options: add `"schema_v": 1` to all records, or handle missing fields in analysis scripts. Unresolved.
- **Garbage outcome vs empty:** `try_scrape` uses `is_garbage_content()` and returns `""` for garbage (with `garbage_type` populated in meta). If all phases exhaust with garbage, `outcome` is the last `garbage_type` string (not `"empty"`). Distinction is intentional — `"empty"` means no content AND no garbage detected.

## Sources

None — internal design decision, no external sources.
