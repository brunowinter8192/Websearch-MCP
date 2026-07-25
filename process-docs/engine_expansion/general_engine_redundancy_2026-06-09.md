# GENERAL Engine Redundancy + Skill Fallback Guidance

**Date:** 2026-06-09
**Type:** Enhancement (engine pool + skill docs) — field observation, not yet implemented.
**Source:** real research session (German university degree-program search: "which university of applied sciences offers a business-informatics master's in city X")
**Affected:** `src/search/engines/`, `src/search/filter_modes.py`, the search-related skill docs

## Summary

In a longer research session, **Google returned 0 results on 5 of 8 `search_web` queries** (CAPTCHA/EMPTY_BLOCK — consistent with the documented 73% OK / 23% CAPTCHA baseline as of that date). The fallback to the remaining GENERAL engines kept the session afloat, **but barely**: as of 2026-06-09 there were only **2 other GENERAL engines** (duckduckgo, mojeek), and **mojeek delivered garbage throughout** (SEO aggregators, dead directory pages, forums). Effectively, redundancy hinged on **DuckDuckGo alone**.

Biggest lever per user assessment: **not tuning Google** (known, backoff deliberately removed — see the no-backoff-retry decision), but **(a) more GENERAL engines** in the pool and **(b) making the skill docs explicit that the remaining GENERAL engines replace Google when it returns 0.**

## Field Evidence (Session 2026-06-09)

GENERAL engine yield per `search_web` (only google/ddg/mojeek; academic engines omitted):

| Query | google | ddg | mojeek | usable? |
|---|---:|---:|---:|---|
| "...university of applied sciences" | 0 | 0 | 0 | no — only academic noise |
| "...Munich university" (variant 1) | 0 | 0 | 0 | no — only academic noise |
| "...FH Dortmund Münster Hannover" | 10 | 9 | 10 | yes |
| "...Munich Nuremberg Ohm university" | 9 | 9 | 9 | yes |
| "...HAW Hamburg Bremen" | **0** | 9 | 10 | partial — without Google, ddg/mojeek carried |
| "FH Münster...admission requirements" | **0** | **0** | 10 (junk) | no — only Mojeek junk |
| "Munich university business informatics master" | 8 | 8 | 8 | yes |
| "...Hannover Bremen Bielefeld" | **0** | 10 | 10 | yes — ddg/mojeek carried |

- **Google: 0 results on 5/8 (62.5%)** — within the expected range of the documented 23% CAPTCHA rate + query variance, but clustered in this session.
- **DuckDuckGo was the actual carrier** of the fallback. When ddg failed *simultaneously* (2 queries), only Mojeek remained — meaning junk or nothing.
- **Mojeek quality:** drilldowns consistently returned `studienwahl-deutschland.de` ("no longer available"), `stuvia`, `fernstudium-direkt`, `wiwi-treff` forums instead of the actual `.de` program pages. Effective value-add ≈ 0 for "find the official program page".
- **Academic engines (crossref/openalex/semantic_scholar)** returned 8-10 hits on *every* query, but for "which university offers program X" this was pure noise (research papers). On the two total-outage queries, the breakdown consisted only of this noise — visually a "hit", practically unusable.

### Scrape side (for completeness)
- **1 hard error:** `scrape_url` on the FH Münster business-informatics page → `Page returned only whitespace or near-empty content` (JS-rendered / cookie wall). Otherwise 6/7 scrapes clean.
- **DAAD detail pages + official `.de` university pages scraped excellently** (structured admission requirements + deadlines). Reliable source once search finds a program page.

## Root Cause (consistent with baseline)

1. **Only 3 GENERAL engines** in the pool as of this session (`google`, `duckduckgo`, `mojeek`). On Google CAPTCHA, this left a **2-engine redundancy**, one of which (mojeek) was qualitatively weak — effectively a **single point of failure on DuckDuckGo**.
2. **Google was additionally the K-anchor** of the pool cap (`K = google_count`, fallback 10). Its failure also degraded the cap logic to the default of 10.
3. **Academic engines diluted the breakdown** on non-academic queries — creating the appearance of a "successful" breakdown even when 0 usable GENERAL hits were present.

## Skill Wording Clarification (minor finding, lower priority)

The skill wording "Mode flags `--books`/`--pdf`/`--docs` **restrict to google/duckduckgo/mojeek**, append the modifier, post-filter the URLs" was **factually correct** (google/ddg/mojeek are the engines whose query gets the modifier appended + URL-postfiltered — `_BOOKS_/_PDF_/_DOCS_ENGINES` in `filter_modes.py`). "restrict" = **modifier + URL postfilter**, not an engine subset.

**Only ambiguous:** "restrict to" reads as "only these 3 engines fire". In fact the bucket-uniformity invariant holds — **all 9 engines keep firing** (`apply_filter_mode()` → `excluded={}`); the flag only affects the query for 3 engines + the URL postfilter. One clarifying sentence suffices — no behavior bug.

Operationally relevant: **`--docs` is NOT the remedy for academic noise** — it doesn't remove crossref/openalex, appends "documentation" to the query (counterproductive for program search), and only blacklists forums/blogs/tutorials. Academic noise is a **separate** point (addressed via skill guidance "academic ≠ general search").

## Proposed Direction

### A) Engine pool — more GENERAL redundancy
- **Marginalia** (`search.marginalia.nu`) — already noted as "Pending — Marginalia probe: try-or-drop ... when there is a concrete use-case gap" as of the prior engine-expansion research. **This session IS that use-case gap** → prioritize the probe.
- Evaluate further GENERAL candidates (Brave Search API / Startpage / possibly Scholar in a Google-free pool, blocked on the pooling rework).
- Target: when Google=0, at least **2 qualitatively usable** GENERAL engines remain (not just ddg + Mojeek junk).

### B) Skill guidance — make the fallback explicit
- Clarify in the skill docs: **GENERAL engines are mutually substitutable; Google=0 is the normal case (CAPTCHA), not an error — then drill down on the remaining GENERAL engines.**
- **Explicitly mark academic engines as a non-general source** — ignore them for "find entity/program/product" queries rather than misreading them as "hits".
- Correct the `--docs` wording + clarify what the mode flags actually do.

### C) Optional (scrape robustness, low priority)
- Fallback on `whitespace/near-empty` scrapes (the FH Münster case): automatically fall back to a **DAAD mirror page / Hochschulkompass**.

## Acceptance Criteria
- ≥1 additional GENERAL engine in the active pool (Marginalia probe first) **or** a documented try-or-drop decision with rationale.
- Skill docs: mode-flag wording clarified (all engines fire; "restrict" = modifier/URL postfilter on 3 engines).
- Skill docs: explicit section "Google=0 is normal → GENERAL fallback; academic engines != general search".
- (optional) Scrape fallback to DAAD/Hochschulkompass on empty content.

## Non-Goals
- **No Google backoff/retry** — deliberately removed (466s of backoff waste for zero benefit; bot detection does not decay within seconds, per the no-backoff-retry decision).
- No global cross-engine ranking (pooling rework abandoned).

## Sources
- 9-engine baseline, "Pending — Marginalia probe", pooling rework, K=google_count cap — per the search-pipeline design as of this session.
- Google 73% OK / 23% CAPTCHA, fail-fast, no-backoff rationale — per the rate-limiting decision as of this session.
- `src/search/filter_modes.py` — bucket-uniformity invariant (`excluded={}`), mode-modifier sets.
