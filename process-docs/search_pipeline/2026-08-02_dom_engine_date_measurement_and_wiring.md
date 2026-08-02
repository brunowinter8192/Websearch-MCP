# DOM-scraped engine date measurement + selective wiring

Date: 2026-08-02

## Problem

Milestone 1 threaded an optional `date` field through the result chain for the four API-backed engines that already had a date in their response and discarded it. The 8 DOM-scraped web engines (google, duckduckgo, mojeek, startpage, brave, bing, yandex, lobsters) had no date extraction at all — unknown whether their live pages even carry a date, and if so, in what form. That's only answerable at the live page, not from reading the parser code.

## Measurement (probe)

Built a self-contained probe (`dev/search_pipeline/31_date_availability_probe.py`, no `src/` import — matches the existing convention in `25_startpage_probe.py`/`26_brave_probe.py`/`28_bing_probe.py`/`29_yandex_probe.py`) that navigates each engine exactly as production does (inline copy of the current `src/search/browser.py` + each engine's nav/wait/diagnose logic), then for the first 3 result containers per query captures: `<time>` elements, class/id tokens matching a word-boundary regex (`date|time|age|publish(ed)?|when|ago` — not a substring match, which would false-positive on `update`/`candidate`/`validate`), full container text, and an HTML head. One JS pass covers both the dedicated-element and snippet-text-only cases.

3 queries per engine: 2 English news-shaped ("openai gpt-5 release reaction", "federal reserve interest rate decision 2026") + 1 German reference/timeless ("Photosynthese Prozess pflanzliche Zellatmung") — a single English-news-only query set would have proven "no date for English news queries," not "no date, ever." Pacing was self-imposed (this script never goes through `src/search/rate_limiter.py`), not derived from any production quota — 20s between same-engine queries, a 180s cooldown before a one-shot retry, only fired when an engine was non-OK on all 3 primaries (never happened in this run — `google`/`duckduckgo`/`brave`, pre-flagged as empty in an unrelated earlier session run, all came back OK).

Report: `dev/search_pipeline/md/date_availability_probe_20260802_233409.md`.

**Two real gaps found in the automated regex, both caught only by manual follow-up, not the scan itself:**
- Google's rich SERP features (video carousel, featured snippet, People Also Ask) dominate the first `div.MjjYud` containers for newsy queries — a `CONTAINER_LIMIT=3` sample was 100% rich-feature noise, zero plain organic results. A supplementary organic-only check found Google's real pattern: `"N days ago — "` prefix on ordinary organic snippets.
- Bing's `span.news_dt` uses the abbreviation "dt", not a whole word — slipped past the word-boundary regex entirely. Found only by manually re-checking Bing's `.b_caption` HTML.

Lesson: the regex is a strong first-pass filter, not a complete one. A real classification needs a human eyeball pass per engine.

## Classification (8 engines)

| Engine | Case | Evidence |
|---|---|---|
| lobsters | 1, dedicated | `<time datetime="2025-01-28 01:35:08" title="..." data-at-unix="...">1 year ago</time>` |
| duckduckgo | 1, dedicated (optional) | bare `<span>2026-07-29T18:00:00.0000000</span>`, present only on results with structured source metadata |
| bing | 1 (partial) + 2 fallback | `<span class="news_dt">14. März 2023</span>` when present; plain unwrapped text (e.g. `"...Research May 20, 2026 …"`) when absent |
| google | 2, snippet-text | `"4 days ago — The Committee decided..."` |
| brave | 2, snippet-text | `"9. August 2025 - ..."`, `"vor 4 Tagen - ..."` — cleanest, most consistent prefix pattern of all 8 |
| startpage | 2, snippet-text | `"07.08.2025 ... "`, `"vor 4 Tagen ... "` |
| yandex | 2, weak | only 1 example found (`"Published on9 Apr 2019"`) across 9 sampled containers |
| mojeek | inconclusive | 2/3 probe queries hit a real CAPTCHA page (`{"marker": "captcha", ..., "title": "Captcha"}`), only 1 successful sample |

## Milestone 3 decision — dedicated elements only, no regex on snippet text

Wired: lobsters, bing (news_dt subset). Deliberately left out: google, brave, startpage (all case 2 — the date is free-form localized text embedded in a snippet the user already reads; a regex over that is permanent upkeep for a secondary field, and breaks silently and invisibly on a format shift, with nothing actually lost by not parsing it since the text stays visible). Left out: yandex (one hit isn't a pattern), mojeek (a 2/3 CAPTCHA rate in one short run is a reliability problem independent of the date question).

**DuckDuckGo resolved before wiring, per explicit instruction not to trust the probe's classification at face value.** The probe's raw dump showed the ISO string only in container TEXT, with the HTML-head excerpt truncated before the element that actually carried it — not verifiable evidence for a "dedicated element" claim, and a bare classless `<span>` is the most fragile possible wiring target if it's purely positional. Re-probed with a full, untruncated `.result__extras__url` dump: a dated result has exactly 3 children (icon span, url anchor, bare date span); an undated result (e.g. a Wikipedia hit) has exactly 2 children, cleanly, no different/broken structure. The date span is identifiable by **absence of the icon class** (`span:not(.result__icon)`), not raw position — verified 10/10 correct matches in one query and a correct 4/10-present split in another. That cleared the "stable, identifiable element" bar → wired in alongside lobsters and bing.

## Precision

Day precision only (`YYYY-MM-DD`), consistent with the Milestone-1 convention (stack_exchange's Unix epoch also had second-level source precision but was truncated to day). Lobsters' `<time datetime>` and DuckDuckGo's ISO span both carry finer source precision but are deliberately truncated — no invented, and no kept, time component for a field the project has established as day-max. Bing's `news_dt` parse (`_DE_MONTHS`/`_EN_MONTHS` + two regexes for `"D. Month YYYY"` / `"Month D, YYYY"`) returns `None` on any unrecognized shape (e.g. a relative "vor N Tagen" string) rather than guessing — a failed parse must degrade to no date, never a wrong one.

## Verification

Live end-to-end run, query "openai gpt-5 release reaction": lobsters 6/6 dated; bing showed both the populated case (`Date: 2023-03-14` from `news_dt="14. März 2023"`) and the required no-fallback case in the same run — result #1 had plain-text `"Research May 20, 2026"` in its snippet but no `news_dt` element, correctly produced no `Date:` line and no crash; duckduckgo showed a real mix of dated/undated entries in one pool. Full test suite: 100 passed / 11 failed, identical failure set before and after (pre-existing, unrelated — missing `curl_cffi`, `unittest.mock` gaps in `test_query_logger.py`/`test_proxy_pool.py`).
