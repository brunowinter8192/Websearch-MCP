# Iter 4 — Production Discovery Rewrite (UI Pagination)

**Date:** 2026-05-27
**Branch:** news-coindesk-2 (successor to news-coindesk)
**Scope:** Replace `dev/news_pipeline/01_coindesk_discover.py` — sitemap-based → UI-pagination-based

## What We Did

Rewrote `01_coindesk_discover.py` from scratch. Prior implementation fetched the Google News Sitemap
(`/arc/outboundfeeds/news-sitemap-index`) via stdlib HTTP, parsed XML, and filtered to the last 24h. Two
known deficiencies (documented in iter 3):

1. 25-URL hard cap — sitemap only carries the most recent 25 entries
2. Yesterday gap — sitemap frequently omits articles from the previous calendar day

New implementation navigates `https://www.coindesk.com/latest-crypto-news` via pydoll headed browser,
uses three JS constants from `exploration/01_coindesk_ui_probe.py` verbatim:

- `_JS_EXTRACT` — DOM traversal with skipTags (`ASIDE`, `NAV`, `FOOTER`, `HEADER`) and skipCls
  (`related|recommendation|popular|trending|sidebar`) noise filter; extended with `title: a.textContent.trim()`
  to capture article headline from anchor text (not available in the sitemap probe)
- `_JS_CLICK_BTN` — finds + JS-clicks the "More stories" button by text regex
- `_JS_COUNT` — fast poll: same exclusion logic as `_JS_EXTRACT`, returns integer count

Termination: `PRE_TODAY_THRESHOLD = 3` (≥3 articles with URL date < today). Safety cap:
`MAX_CLICK_ROUNDS = 8` with stderr WARNING on cap-fire. Both values carried from iter 3 probe
where 1-3 clicks proved sufficient for 24h coverage.

`lastmod` and `publication_date` both set to UTC midnight ISO string derived from URL's `/YYYY/MM/DD/`
path. Rationale: relative `timeLabel` labels from `_JS_EXTRACT` disappear on older articles (blank for
yesterday's content in iter 3 probe), URL date is the only reliable signal without a sitemap. Stage 2
uses these fields for YAML frontmatter only — no date-based filtering — so UTC midnight is sufficient.

Output schema `{url, lastmod, publication_date, title, section}` is identical to sitemap predecessor.
Stage 2 (`02b_coindesk_scrape_fresh_context.py`) requires zero changes.

## Measurements

### Discovery run (2026-05-27T19:07:24Z)

| Metric | Value |
|---|---|
| Batches (initial + clicks) | 2 (batch 0 + 1 click) |
| Total unique URLs | **32** |
| Sitemap predecessor | 25 (capped) |
| Delta | +7 (+28%) |
| Coverage trigger | 1 click (3 pre-today articles) |
| Section distribution | markets 14 / business 9 / policy 3 / coindesk-indices 2 / tech 2 / opinion 1 / daybook-us 1 |
| Run time (approx) | ~35s |
| MAX_CLICK_ROUNDS fired | No (terminated at batch 1) |

### Stage 2 scrape (02b_coindesk_scrape_fresh_context.py, same session)

| Metric | Value |
|---|---|
| Input URLs | 32 |
| ok (real bodies) | 27 |
| empty | 5 |
| failed | 0 |
| Success rate | **84.4%** |
| Iter 2 baseline | 92% (23/25) |
| Total chars | 957,064 |
| Slowest ok | 8.53s |
| One timeout | 60.5s (empty) |

All 5 empty entries are from today (2026-05-27). Pattern consistent with transient render delay or
rate-limiting on very fresh articles (published within the same run window). No regwall hits (0 failed).
Stage 2 auto-picked the new `discover_*.json` correctly via `pick_latest_input()` — zero code changes.

The 84.4% vs expected ≥90% is a delta worth tracking. Hypothesis: larger batch (32 vs 25) combined with
faster publishing cadence on today's articles means some pages haven't fully settled when crawl4ai visits.
Retry logic or a small per-URL delay increase in Stage 2 would likely close the gap — deferred, out of
iter 4 scope.

## Conclusion

Iter 4 goal achieved: sitemap cap removed, yesterday coverage restored, Stage 2 unchanged. New script
is the production-quality discovery path for `dev/news_pipeline/`. The `--headless` CLI flag provides
a clear path to cron integration when Stage 2 reliability is confirmed at ≥90% over multiple runs.

## dev/ Scripts Used

- `dev/news_pipeline/01_coindesk_discover.py` — new production discovery script (this iteration)
- `dev/news_pipeline/02b_coindesk_scrape_fresh_context.py` — stage 2 unchanged, verified compatible
- `dev/news_pipeline/exploration/01_coindesk_ui_probe.py` — source of JS constants + browser helpers
