# Result-date feature — orchestration decisions (2026-08-02)

Companion to the per-milestone worker recaps in this area and in `scrape_pipeline/`. Those record WHAT was
built; this records the decisions taken in the orchestrator↔user exchange, which exist nowhere else.

## Framing that shaped the whole cut

The user's opening constraint: the date should ideally appear already in the URL list, but arriving only at
scrape time is acceptable — *that* it arrives matters more than *when*. That single sentence is why the work
split into "wire what the engines already hand us" first and "extract from the target page" last, rather
than jumping straight to page extraction (which covers all 14 engines but only after a URL is already
chosen).

## Milestone cut

1. thread an optional `date` field through result → pool-build → cache → render, filled from the 4
   API-backed engines that already receive a date and discard it
2. MEASURE what the 8 DOM-scraped web engines actually carry (probe only, no wiring)
3. wire whichever of those the measurement justifies
4. scrape-time extraction via `htmldate`

Milestone 2 existing as a separate, non-shipping milestone was deliberate: whether the web engines carry a
date is answerable only at the live page, and the answer decides whether milestone 3 exists at all.

## Decisions where the worker's proposal beat the orchestrator's model

- **Date precision representation.** Orchestrator model: a `date` field plus a sibling `date_precision`
  field. Worker's counter: ISO 8601 already defines year-only and year-month as reduced-precision forms, so
  the string encodes its own precision and a second field adds 4 touch points through the chain for zero
  information. Adopted.
- **CrossRef key priority.** Orchestrator leaning: `published-online` > `published-print` > `issued`.
  Worker's counter: CrossRef documents `issued` as the already-resolved publication date (earliest of
  print/online where both exist), so the orchestrator's ordering is effectively contained in it, and
  `issued` is additionally the most consistently populated. Adopted; the orchestrator's ordering was wrong.
- **DuckDuckGo date element.** The orchestrator rejected the worker's case-1 classification as unverifiable
  from its own raw dump (the quoted excerpt showed only the favicon span and the URL anchor) and demanded a
  targeted re-probe. The re-probe showed the element is identified by ABSENCE of the icon class, not by
  position — structurally stable, verified 10/10 on one query and a 4-dated/6-undated split on another. The
  rejection was wrong on the substance but produced the evidence that settled it; DDG was wired.

## Decision reversed mid-flight on evidence

Milestone 1 was dispatched with a hard constraint: do not touch CrossRef's `_synthesize` (the snippet
builder), to keep snippet behaviour unchanged. The worker then produced a live record where the new
`Date:` line read `2012-09-19` while the snippet in the SAME block read `(2013)` — because `_synthesize`
sourced its year from `published-print` while the new extractor used `issued`.

The constraint was then lifted, with the reasoning stated to the worker: it had been about preserving the
snippet's SHAPE and fallback behaviour, not about conserving a key order now shown to produce a visible
contradiction. One result stating two different years is worse for a reader than either value alone. The
worker's fix went further than instructed and shared a single module-level `DATE_KEY_PRIORITY` constant
between both functions, so they cannot diverge again even under later edits.

Accepted consequence: CrossRef snippets whose `published-print` year differs from `issued` now display a
different year than before this change. Deliberate — the new year is the more correct one.

## The narrow-wiring decision (milestone 3)

The probe classified the 8 web engines into: dedicated date element (lobsters `<time>`, bing
`span.news_dt`, duckduckgo after re-probe), date only as free text inside the snippet (google, startpage,
brave), one weak single instance (yandex), and unmeasurable (mojeek — real CAPTCHA on 2/3 queries).

Only dedicated elements were wired. The case-2 engines were dropped despite being technically parseable,
on the user's "lieber keine Wartung" call. The reasoning recorded: their dates are localized free text —
`"vor 4 Tagen"` beside `"4 days ago"`, `"9. August 2025"` beside `"07.08.2025"` — so a regex is permanent
upkeep for a secondary field AND it breaks silently and invisibly when a format shifts. The user still sees
the date in the snippet text on those engines, so nothing is actually lost by not parsing it.

## Probe-design conditions the orchestrator imposed (milestone 2)

- **Case 4 (engine returned nothing) must be reported separately from case 3 (no date found).** Five engines
  had returned 0 results in a live run earlier that day; a blocked engine that lands in the report as "no
  date" gets wrongly excluded.
- **Retry gap in minutes, not seconds.** The worker proposed a 20s cooldown; that cannot distinguish
  "blocked" from "transiently empty", and engines already worn by earlier same-day runs would look like
  fresh blocks the probe caused.
- **A non-news, non-English query in addition to the news-shaped ones.** Both proposed queries were English
  news topics, which maximizes dated results but means a case-3 verdict would only say "no date for English
  news queries". The added German reference query (`"Photosynthese Prozess pflanzliche Zellatmung"`)
  produced the only yandex date found — a video-card text, which is what kept yandex classified as too weak
  to wire.

Two methodology self-corrections the worker surfaced unprompted and which are worth keeping: sampling only
3 containers under-sampled Google (its `div.MjjYud` selector interleaves video carousel / answer box /
People-Also-Ask ahead of organic results, so all 3 samples were rich-feature noise), and its own
word-boundary regex on class/id tokens (`date|time|age|publish|when|ago`) structurally cannot match Bing's
`span.news_dt` abbreviation — found only by hand. The regex is a strong first-pass filter, not a complete
one.

## Milestone 4 — orchestrator argued against it twice, wrongly

The orchestrator twice re-litigated whether scrape-time extraction belonged in this session, arguing the
date arrives too late to help choose a URL. The user had settled this in the opening exchange ("zur Not kann
das Datum auch erst beim Scrape kommen"). Re-opening a decided question cost two exchanges and produced
nothing; the milestone was then built as originally scoped.

## Coverage as of end of session

7 of 14 engines surface a date in the drilldown: 4 API-backed (openalex, crossref, stack_exchange,
open_library), 3 DOM (lobsters, bing, duckduckgo). The remaining 7 have no date in the drilldown; all 14 are
covered at scrape time via htmldate.

Not verified in rendered output: stack_exchange — it returned 0 results in every live run across this
session, so its date line is proven in code only, never seen on screen.
