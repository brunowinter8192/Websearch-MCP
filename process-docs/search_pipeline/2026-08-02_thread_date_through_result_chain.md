# Threading a `date` field through the SearchResult chain

Date: 2026-08-02

## Problem

`search_engine_drilldown` output listed position/title/URL/snippet per URL — no date, so a user picking a URL from an engine's pool had no way to tell recency. Four API-backed engines (openalex, stack_exchange, crossref, open_library) already receive a publication date in their API response and discarded it before it ever reached the drilldown output. `semantic_scholar` was excluded — it's DOM-scraped, no date field in reach. The other 9 engines have no date signal available at all.

## Chain traced

`SearchResult` (result.py) → engines populate it per URL → `build_engine_pools` (merge.py) constructs a **fresh** `SearchResult` per winning URL, naming fields explicitly — anything not named is dropped, this was the actual reason the date never survived even where an engine parsed it → `cache_write` (cache.py) serializes an explicit key subset to `~/.cache/websearch/<key>.json` → `format_engine_pool` (cache.py) reads the cached dict and renders the drilldown text. Adding the field required a touch at all four links, not just the engines.

## Decision 1 — precision representation

One field, `date: str | None`, holding an ISO-8601 partial date truncated to exactly the known precision — `"YYYY"`, `"YYYY-MM"`, or `"YYYY-MM-DD"`. No separate `date_precision` field.

Rejected alternative: a sibling precision field. ISO 8601 already defines year-only and year-month as valid reduced-precision forms — the string's own shape (dash count) carries the precision, so a second field would be four more chain touch-points (constructor, merge, cache serialize, render) for zero additional information, and risks the two fields drifting out of sync with each other.

## Decision 2 — CrossRef date-key priority

CrossRef carries publication-date signal under three keys that can disagree for one record: `published-online`, `published-print`, `issued` (plus `created`/`indexed`, which are deposit/indexing timestamps and excluded from consideration entirely).

Final priority: `issued` → `published-online` → `published-print`, extracted via a shared `DATE_KEY_PRIORITY` module constant in `engines/crossref.py`.
- `issued` first: CrossRef documents it as the already-resolved publication date (earliest of print/online) and it is the most consistently populated of the three.
- `published-online` over `published-print` as the fallback: online-first publication typically precedes print, and for a "how recent is this" signal the earlier point of public availability is the more useful one.

This key order was initially applied ONLY to the new `date` field, deliberately left independent of `_synthesize`'s pre-existing year-fallback order (`published-print → issued → published-online`) to guarantee zero behavior change to the existing snippet string, per the original hard constraint ("don't touch `_synthesize`"). Live-tested proof this produced a real problem: query "cancer immunotherapy clinical trial", record *"Issues in Pre-clinical Models..."* — raw fields `issued=[2012,9,19]`, `published-online=[2012,9,19]`, `published-print=[2013]`. Old `_synthesize` order → snippet year "2013"; new `date` → "2012-09-19". Rendered in the same drilldown block:
```
Date: 2012-09-19
Snippet: Bilusic, M. et al. (2013), Cancer Immunotherapy
```
One result stating two different years for the same fact is worse than either value alone — the constraint was reinterpreted as "don't change `_synthesize`'s output SHAPE/fallback behavior", not "preserve its key order at the cost of a visible contradiction." `DATE_KEY_PRIORITY` was promoted to a module-level constant shared by both `_extract_date` and `_synthesize`, so the two can no longer disagree. Re-verified on the same record post-fix: snippet year "2012", `date` "2012-09-19" — now consistent.

## Bug found in review — date-parts gap handling

First `_extract_date` implementation filtered `None` out of `date-parts` before switching on the resulting length: `[p for p in parts if p is not None]` then branched on `len(parts)`. This conflates "element absent" with "list shorter" — `[2019, None, 15]` (year known, month missing, day present) filtered to `[2019, 15]`, hit the `len==2` branch, and rendered `"2019-15"` — day 15 silently relabeled as month 15, a non-existent month presented as fact with no crash to reveal it.

Fixed by reading positionally instead of by post-filter count: year = `parts[0]` unconditionally; month = `parts[1]` only if present and non-`None`; day = `parts[2]` only if BOTH month and day are present and non-`None`. Truncates at the first gap — a gap yields the precision up to that gap, never a value shifted into the wrong slot. Verified against five shapes: `[2019]`→`"2019"`, `[2019,3]`→`"2019-03"`, `[2019,3,15]`→`"2019-03-15"`, `[2019,None,15]`→`"2019"` (was `"2019-15"` before the fix), `[2019,None,None]`→`"2019"`.

## Cache backward-compatibility

The disk cache TTL is 1h, so live cache files written by the pre-change code (no `date` key at all) coexist with the new code for up to an hour. `format_engine_pool` already read `snippet` via `.get()` — extended the same pattern to `date`: `entry.get("date")`, `None` on a missing key, no `Date:` line, no `KeyError`. Verified with a synthetic pool entry dict containing no `"date"` key.

## Per-engine extraction

| Engine | Source | Precision | Notes |
|---|---|---|---|
| openalex | `publication_date`, falls back to `str(publication_year)` | day, else year | `publication_date` nullable per vendor docs |
| stack_exchange | `creation_date` (Unix epoch int) → `datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")` | day | part of the default `withbody` filter, no filter change needed |
| crossref | `date-parts` under `DATE_KEY_PRIORITY`-ordered keys | day / month / year | see decisions above |
| open_library | `first_publish_year` | year | `_build_snippet`'s existing year usage left untouched |

## Verification

Live end-to-end run: `search_web "machine learning retrieval"` → `search_engine_drilldown --engine openalex` — 10/10 entries carried a `Date:` line at day precision. Same query against crossref surfaced year-only and no-date entries in-pool; separate direct-engine calls against other queries ("cancer immunotherapy clinical trial", "quantum computing algorithms") produced day/month/year examples confirming all three precision branches render correctly. Full test suite: 100 passed / 11 failed before and after the change, identical failure set (pre-existing, unrelated: missing `curl_cffi` dependency, `unittest.mock` attribute errors in `test_query_logger.py` / `test_proxy_pool.py`) — no regressions introduced.
