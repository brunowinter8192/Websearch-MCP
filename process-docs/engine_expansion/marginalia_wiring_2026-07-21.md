# Marginalia Wired as Production Engine (2026-07-21)

**Engine:** `src/search/engines/marginalia.py` — `MarginaliaEngine(BaseEngine)`
**Registry:** `src/search/search_web.py` — added to `ENGINES`
**Default set:** `src/search/filter_modes.py` — added to `_DEFAULT_ENGINES` and all three mode-sets `_BOOKS_ENGINES`, `_PDF_ENGINES`, `_DOCS_ENGINES`.

Follows the same-day `30_marginalia_probe.py` re-evaluation. **This is an HTTP-API engine, not a browser engine** — `httpx` against `api2.marginalia-search.com/search`, header `API-Key: public` (shared free key, no signup), mirroring `crossref.py`/`openalex.py`/`stack_exchange.py`/`open_library.py` structurally, not `google.py`/`startpage.py`/`brave.py`/`bing.py`/`yandex.py`.

## The 429/403 -> None -> [] path matches existing API-engine precedent exactly

`_fetch_results()` returns `None` on HTTP 429 or 403, logging `logger.warning("Marginalia rate limited: %d", response.status_code)` — the identical shape and identical log-message pattern (`"<Engine> rate limited: %d"`) already used by `crossref.py`, `openalex.py`, `stack_exchange.py`, and `open_library.py`. `search()` maps `None -> []`. This means 429-frequency for Marginalia is observable via the same log-grep pattern already used for the other API engines (`grep "rate limited" src/logs/*.log` style), which matters concretely here: the shared `public` key's real-world contention rate is an open operational question (see below), and this logging gives a cheap, already-established way to observe it over time without new instrumentation.

## Deliberate NO `search_with_reason` override

`MarginaliaEngine` implements only `search()`, relying on `BaseEngine`'s default `search_with_reason` (`return results, None`) — exactly like all four reference API engines, none of which override it either. This was a deliberate check against actual codebase precedent rather than an assumption: the wiring milestone's phrasing suggested picking "the closest existing status the API engines use for a rate-limited/blocked empty," but reading all four reference engines first showed that none of them sub-classify a rate-limited empty from any other empty — they all just return `[]` uniformly. Mirroring the real pattern was chosen over inventing a new one that has no precedent in this engine family.

## Config values

- `ENGINE_MAX_RESULTS["marginalia"] = 10` — `count` API param, matches the probe.
- `_limiters["marginalia"] = RateLimiter(4, 60)` — same uniform rate limiter as every other production engine (a good-citizen throttle toward the shared, contended public-key quota, independent of Marginalia's own server-side quota).
- **Deliberately NO `ENGINE_WATCHDOG_OVERRIDE` entry** — probe median latency ~74ms, max ~1430ms, far under the `ENGINE_WATCHDOG_TIMEOUT=3.6s` default; a rate-limited (429) response returns just as fast as a successful one, so neither outcome path approaches the ceiling.

## Mode-set membership rationale (not just copied for consistency)

Marginalia was added to `_BOOKS_ENGINES`/`_PDF_ENGINES`/`_DOCS_ENGINES` alongside `google`/`duckduckgo`/`mojeek`/`startpage`/`brave`/`bing`/`yandex` — NOT alongside `crossref`/`openalex`, which are excluded from those three mode-sets. The reason is structural, not just "stay consistent": `crossref`/`openalex` return DOI-resolvable URLs only (`doi.org/...` or similar), which yield zero results after the PDF/docs URL post-filter — that's WHY they're excluded. Marginalia, by contrast, is a genuine web crawler returning arbitrary real external URLs, same as the browser-scraped general engines — so the `+book`/`+pdf`/`+documentation` query modifier and the corresponding URL post-filter apply to it exactly the way they apply to google/ddg/mojeek. This was verified by inspection before adding the memberships, not assumed.

## Framing: new coverage, different axis (recap of the probe's framing, now live in production)

Marginalia is new coverage on a DIFFERENT axis from every other general engine in the pool (google/duckduckgo/mojeek/startpage/brave/bing/yandex all lean mainstream/commercial web) — its own independent crawler explicitly targeting the small/old/text-heavy/non-commercial web. It does not compete with or duplicate any other engine's coverage; it fills a gap none of the others address.

## Verification — live, including a real 429-and-recover cycle

- First live smoke (production `MarginaliaEngine().search()`, 3 queries incl. `unix philosophy essay`/`self hosting guide`): all 3 hit the real shared-key rate limit (429) — expected, given the SAME `public` key had already been hit heavily earlier the same session (the probe itself, plus manual exploration calls). Each returned a clean `[]` in 169-239ms with zero exceptions, directly proving the graceful-empty contract under a genuine live rate-limit event.
- Minutes later, `cli.py search_web "self hosting guide"` succeeded with `marginalia: 10` in the full 14-engine breakdown — the shared quota is contended, not permanently exhausted, matching the probe's characterization exactly. Drilldown confirmed real, relevant indie-web titles/URLs (`discuss.privacyguides.net`, `foundryvtt.com`, `bsdnow.tv`, `discuss.tchncs.de`, `ophanimkei.com`).
- Full test suite: same 9 pre-existing `test_query_logger`/`test_proxy_pool` failures as before this change, no new failures; 7 new tests (4 pure-function parsing cases + 3 monkeypatched-httpx 429/403 cases) all pass.

## Open item carried forward, not resolved here

The shared `public` key vs. a personal free non-commercial key (requiring an email to `contact@marginalia-search.com`) remains an open operational question — a personal-key request was made on 2026-05-02 per prior process history and was never answered. This wiring proceeds on the shared key as instructed; the new `logger.warning("Marginalia rate limited: %d", ...)` line gives a concrete, already-integrated way to observe how often that contention actually bites in real usage over time, informing whether pursuing a personal key is worth it later.

## Pool status

The general/mainstream web axis is now covered by 7 engines (`google`, `duckduckgo`, `mojeek`, `startpage`, `brave`, `bing`, `yandex`) plus this new different-axis niche engine (`marginalia`), for **14 total production engines**. This expansion round's general-axis engine additions are considered complete as of this wiring.
