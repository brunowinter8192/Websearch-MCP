# Scrape toolbox — scoping the box, and what got set on the ad-hoc path (2026-08-03)

Orchestrator-side record of a scoping discussion that has no worker counterpart: the four milestones
executed this session each wrote their own entry under `process-docs/scrape_pipeline/`. What follows
is the framing those milestones came out of, plus two decisions that ended in *not* building
something.

## Reframing: hardening → a toolbox with two consumers

The starting brief was "bring `pipe_scraper.py`'s anti-bot posture to parity with
`scrape_url.py`". That framing was dropped. The target instead:

- a set of levers governing whether a domain is reachable at all and how clean the extracted content
  is — the *box*
- **`src/scraper/scrape_url.py`** (ad-hoc path, reached via the web-research skill's search →
  drilldown → scrape) gets ONE fixed calibration, the one that does best across a mass of unknown
  domains, because nobody adjusts it per call
- the **capture worker** gets the same box open, and adapts it to the domain in front of it

Consequence: the ad-hoc path is a mass-calibration problem, the capture path is a per-domain tuning
problem. Only the ad-hoc half was worked this session.

## One library, tuned — not more libraries

Decided: stay on crawl4ai (0.9.2, current — no newer release exists; 0.9.1/0.9.2 have no CHANGELOG
entries at all, and 0.9.0's breaking changes are Docker-server-only, the pip library unaffected) and
exhaust its parameter surface before adding anything.

Explicitly deferred, both real and both already present in this project's orbit:
- **trafilatura** — 24 documents of its docs sit indexed in `websearch-reference`, the library itself
  is not installed. Never adopted; the alternative to `PruningContentFilter` on the extraction side.
- **curl_cffi** — referenced by the news pipeline. `process-docs/news_pipeline/` records a measured
  result: `impersonate=chrome` got 80/425 proxies through Cloudflare with HTTP 200 + valid XML where
  another client managed 0/17202, the isolating variable being the TLS fingerprint alone.

Both stay parked until a limit is shown to be unreachable *within* crawl4ai.

## Calibration method: external sources, not domain sweeps

A sweep over a drawn domain set was rejected as the calibration basis: a dozen elements with several
settings each, plus cross-element interaction, is not affordable, and the result would hold for the
drawn sample rather than the next unknown domain. Domain-specific tuning is what one does when
scraping ONE site; this scraper has to work across the mass.

What replaced it: the vendor's own docs and source, its issue tracker, and — for time values — this
project's own operational log rather than a staged measurement.

Two consequences worth recording:

- The **extraction side was already calibrated** and did not need redoing. A 36-config × 20-URL sweep
  (2026-05, recorded in `process-docs/scrape_pipeline/`) settled `PruningContentFilter(threshold=0.48)`
  under an explicitly asymmetric preference — residual chrome is worse than content loss. That sweep
  predates `preserve_classes`/`preserve_tags` (crawl4ai 0.9.1), which is why a guard could be added on
  top without reopening the threshold.
- The **reachability side has no comparable basis**. External evidence names the elements; it does not
  yield thresholds.

## Optimising for an average, with an ordering over failure kinds

An earlier framing — "more domains, never fewer; cleaner, never swallowing real content" — was
withdrawn as unfalsifiable: it is a promise about a population that cannot be sampled exhaustively.
An average over a cross-section is the honest formulation.

With one qualifier: failure kinds are not equally expensive. Correct content beats an honest failure
beats silently-delivered wrong content. A raw pass/fail mean treats the last two alike and would
reward trading honest failures for silent false hits — the `geizhals.de` case (router URL requested,
e-guitar page delivered, `outcome=ok`, 19783 bytes) is that class.

## `wait_for` — rejected for both paths

Considered against the `Loading...` placeholder class (13 pages of one domain returning nav chrome
plus 51 occurrences of `Loading`, counted `ok` by the funnel, surfacing one stage later as the
cleaner's `no h1`).

- **Ad-hoc**: `wait_for` never discards anything — it waits, then delivers the same page either way.
  An empty output and a not-yet-loaded page are the same state to the caller, and a caller is right
  there looking at it. Pure cost, no counter-value.
- **Pipe**: a per-domain CSS selector is the hamster-wheel this project already rejected on record,
  and every URL in a mass run pays the wait, including the 36 of 49 that were fine. The problem there
  is *detection*, not waiting — nobody is watching, which is why the placeholder pages overwrote
  working files unnoticed.

Determinism is being handled as its own question rather than through a per-call condition.

## `fallback_fetch_function` — built up, then dropped for the ad-hoc path

Mechanism (verified in `async_webcrawler.py`): an async `(url) -> html` callable on
`CrawlerRunConfig`, invoked at `:553` when either the browser produced no result at all or
`is_blocked()` flags the one it produced. At `max_retries=0` that is exactly one extra attempt. The
returned HTML runs through the normal pipeline. A *successful* fallback skips the re-block-check
(`:617`) — the fallback result is treated as authoritative.

The motivating case was real but came from the OTHER path: a capture run took 0/23 on crossref.org,
every URL empty at the ~15s page-load ceiling with no HTTP status, while plain `curl` on the same URL
returned HTTP 200 with 79274 bytes in 7.2s. That is `pipe_scraper.py`, whose browser carries no
hardening at all.

Checked against the ad-hoc path's own record before building it — all 19 non-`ok` outcomes in
`src/logs/scrape_log.jsonl` (166 records, from 2026-07-21):

| outcome | n | what a plain-HTTP retry would return |
|---|---|---|
| `http_error` 404 (×5) | 5 | the same 404 |
| `http_error` 403 (idealo, guenstiger, trustpilot) | 3 | worse — a bare HTTP client is the *weaker* client from the same IP |
| `http_error` 401 | 1 | still unauthenticated |
| `http_error` 301/308 redirect | 2 | the same redirect |
| `empty`, no HTTP status | 6 | unknown, but never the crossref signature |
| `minimal_content` | 2 | the same thin page |

Not one resembles the crossref case. The class the fallback covers — browser blocked, plain HTTP gets
through — arises where the browser is *weaker* than a plain client. `scrape_url` runs
`enable_stealth` plus `UndetectedAdapter`; there it is not. Dropped, and the reasoning transfers to
`pipe_scraper`, where the evidence actually sits.

Framing that drove the check: a fallback appends a second acquisition path to the first, so the
worst-case envelope becomes browser-cap + HTTP-cap. Against a determinism constraint that is a real
cost, not a free safety net.

## Time distribution — the input for the determinism question

From the same 166 records, 143 with `outcome=ok`, wall time in ms:

| min | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| 914 | 2539 | 4850 | 6928 | 10267 | 33714 |

The single success above 15s (33714ms, stromauskunft.de, 47859 bytes) is a genuinely slow page. Among
the failures the maximum is 60333ms — `page_timeout=60000` running out in full, twice, on
`youniq-living.com`, both returning zero bytes.

So: the ceiling promised to a caller is >60s while 99 of 100 successes finish under 10.3s, and the
~50s between p99 and the cap is occupied almost exclusively by failures producing nothing. This is
the operational corpus, not a staged measurement — appropriate for time values, too thin for content
thresholds.

Two further cost items landed this session and belong in the same accounting:

- `remove_consent_popups=True` spends a fixed ~1s on EVERY page (two unconditional 500ms sleeps: one
  in crawl4ai's own `remove_consent_popups.js`, one Python-side after the eval), measured +0.96s on a
  page with no consent layer, to help only the subset that has one.
- Wait time is not just cost — it changes *what* is captured. A page still hydrating client-side
  yields different content at 0.1s than at 1.1s (root-caused on `rfc-editor.org`, a Nuxt SPA whose
  accessibility tooling injects a clip-hidden title span between those two windows). Any future change
  to the time budget alters extracted content on that page class.

## What was set on the ad-hoc path

Four milestones, each with its own entry under `process-docs/scrape_pipeline/`: crawl4ai's own
diagnosis surfaced into the log (record-only, never acted on — its detector has documented false
positives); a config stamp per record (hash for grouping + full dict for reading, so accumulating real
traffic becomes the calibration basis instead of staged sweeps); `preserve_tags=["pre","code"]`
guarding code blocks; `remove_consent_popups=True` added alongside the three existing consent layers.

`avoid_ads` was evaluated and REJECTED: its 21 block patterns are hardcoded and unextendable, and the
globs require a literal `/` before the domain, so `**/google-analytics.com/**` cannot match
`www.google-analytics.com` — which is how trackers are actually served. On this project's own
60s-tracker-incident page (BfN.de) it blocked 0 of 16 requests; the tracker there (etracker) is not on
the list at all.

## Open items carried forward

- The block-path mapping of the new diagnosis fields is established by source-read only — no live
  anti-bot-blocked page was scraped.
- `preserve_classes` was rejected on two reproduced cases; a wrapper scoring below threshold and being
  decomposed *before* recursion reaches a nested `<pre>` remains theoretically possible, unverified.
- MDN's runnable code samples never reach the captured markdown at all (likely a cross-origin iframe)
  — a separate limitation of this scrape path, found while verifying something else.
- One unreproduced 60.32s zero-content run on stepstone.de with `remove_consent_popups=True`; three
  immediate retries completed cleanly in ~4s. Watch-item.
