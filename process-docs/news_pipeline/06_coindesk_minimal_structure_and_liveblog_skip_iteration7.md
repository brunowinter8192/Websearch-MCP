# Iter 7 — Live-Blog Filter + Minimal-Structure Normalization

**Date:** 2026-05-27
**Branch:** news-coindesk-2
**Scope:** `01_coindesk_discover.py` (live-blog filter) + `03_coindesk_cleanup.py` (trailing-ws + paragraph normalization)

## Decisions

### Live-blog skip (Stage 1)

Live-market blog URLs (`/live-markets-*`) are continuously-updated multi-story containers: a single URL
accumulates dozens of timestamped sub-entries over the trading day and is re-fetched as new content
appears. This is structurally incompatible with a daily-cron pipeline that treats URL as the dedup key
and scrapes once per discovery run. A live-blog scraped at 09:00 is already stale by 10:00; storing
it as a static `.md` adds noise rather than signal to the RAG corpus. Decision: filter at Stage 1
after `build_entries()`, before `write_output()`. Two URLs removed in iter-7 run.

### Paragraph normalization (Stage 3)

Crawl4AI's raw markdown output runs consecutive paragraphs without intervening blank lines (wall-of-text
effect confirmed across 26/27 iter-5.2 files). Standard markdown renders adjacent paragraphs as a single
block without the blank-line separator; RAG chunkers that split on blank lines produce oversized chunks
or miss paragraph boundaries entirely. Fix: in `clean_body()` pass 2, insert a blank line between any
two consecutive body-paragraph lines (non-empty, not header/bullet). 668 blank lines inserted across
50 files in the iter-7 run — confirms the issue was pervasive. Blank-run collapse changed from
collapse-to-2 to collapse-to-1 for consistency with the single-blank-line standard now enforced between
paragraphs.

## Run Results — Before / After

| Metric | Iter 6 (prev) | Iter 7 |
|---|---|---|
| Stage 1 URLs discovered | 48 | 46 (−2 live-blogs filtered) |
| Stage 2 ok | 48/48 (11 fallback) | 46/46 (17 fallback) |
| Stage 2 empty | 0 | 0 |
| Stage 3 files processed | 48 | 50 (46 new + 4 residual) |
| Stage 3 mean reduction | 89.7% | 89.4% |
| Trailing-ws strips | — | 154 lines |
| Para blank inserts | — | 668 lines |
| Live-blog URLs in output | 2 | 0 |

## dev/ Scripts Used

- `dev/news_pipeline/01_coindesk_discover.py` — filter_live_blogs() added
- `dev/news_pipeline/02b_coindesk_scrape_fresh_context.py` — unchanged (iter 6 fallback logic)
- `dev/news_pipeline/03_coindesk_cleanup.py` — clean_body() two-pass rewrite
