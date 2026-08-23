# curl_cffi fallback acquisition path for pipe_scraper

2026-08-05. Final milestone of the `pipe_scraper_hardening` effort on `src/crawler/pipe_scraper.py`
(the mass-capture scrape path). Gives the path a fallback acquisition attempt over plain HTTP with a
browser TLS fingerprint, for the narrow case where the BROWSER is the weaker client.

## The motivating case, and why the fallback stayed dropped on the ad-hoc path

A capture run took 0/23 on crossref.org, every URL empty at the ~15s page-load ceiling with no HTTP
status recorded, while plain `curl` on the same URLs returned HTTP 200 with 79274 bytes in 7.2s. The
same fallback mechanism was evaluated for `src/scraper/scrape_url.py` (the ad-hoc path) and dropped —
checked against all 19 non-`ok` outcomes in that path's own log (166 records), none matched the
crossref signature, because `scrape_url` runs `UndetectedAdapter` and is therefore not the weaker
client (`process-docs/scrape_pipeline/`, 2026-08-03 toolbox-scoping entry). The
class the fallback covers only arises where the browser is weaker than a plain client — true for
`pipe_scraper` (no `UndetectedAdapter`, incompatible with its `CONCURRENCY_PER_DOMAIN=8` per crawl4ai
issue #1500), not true for `scrape_url`. The drop decision did not transfer; the analysis behind it did.

## Mechanism, verified against installed crawl4ai 0.9.2 rather than trusted from any prior account

`CrawlerRunConfig.fallback_fetch_function: Optional[Callable[[str], Awaitable[str]]]` (confirmed
constructor kwarg, `async_configs.py:1705`). `async_webcrawler.py`: invoked at L553-565 when either
`crawl_result is None` or `is_blocked(crawl_result.status_code, crawl_result.html)[0]`; on success,
`status_code` is forced to `200` and `resolved_by` set to `"fallback_fetch"` (L599-603) UNCONDITIONALLY
— regardless of what the fallback function actually returned; the re-block-check is skipped only when
`resolved_by == "fallback_fetch"` (L612-629).

## The finding that changed the design: max_retries=0 blocks the fallback from ever seeing an exception

`async_webcrawler.py:405`: `_max_attempts = 1 + max_retries`. `_get_proxy_list()` returns `[None]` when
no proxy is configured (`async_configs.py:1940`) — `pipe_scraper`'s exact situation. L543-544:
```python
if len(_proxy_list) <= 1 and _max_attempts <= 1:
    raise
```
At `pipe_scraper`'s default config (`max_retries=0`, no proxy), a browser-call exception (e.g. a real
navigation timeout — the crossref shape) re-raises PAST the fallback block entirely, straight to the
outer `except Exception as e:` handler, which returns a bare failed `CrawlResult` with no `crawl_stats`
at all. Verified empirically with a local synthetic TCP server that accepts a connection and never
responds (no external domain — this tests crawl4ai's own control flow):

| `max_retries` | fallback invoked on a hard navigation timeout? | `crawl_stats` present? |
|---|---|---|
| 0 (pipe_scraper's default) | No | No |
| 1 | Yes | Yes |

Separately confirmed the non-exception path (browser returns a real result that `is_blocked()`
flags — e.g. a synthetic HTTP-200-near-empty-body response) DOES reach the fallback correctly at
`max_retries=0` — no gap there.

**Decision: `max_retries` stays at 0.** Raising it to 1 does not buy "one extra acquisition attempt" —
it buys a full second browser attempt (same config, same IP, same target) BEFORE the fallback is even
considered, unconditionally, on the bet that a retried failure differs from the first. Worst case per
URL would become ~2×`page_timeout` + fallback timeout (at 15s page_timeout: ~45s/URL) across runs of
thousands of URLs. That trade was rejected.

## Two independent paths instead, each reaching only where it can

- **Path (a):** `fallback_fetch_function=_fallback_fetch` wired on `CrawlerRunConfig` — crawl4ai's OWN
  mechanism, reaches the non-exception `is_blocked()`-flagged case (HTTP 403/503 block page, HTTP 200 +
  near-empty body). Costs nothing when nothing is blocked (confirmed: 316/316 regression run,
  `crawl4ai_fallback_fetch_used=False` throughout).
- **Path (b):** `_own_fallback_rescue`, called directly from `_scrape_one`'s existing `except Exception:`
  block — the ONE place crawl4ai's own mechanism cannot reach at `max_retries=0`. Cost: exactly one HTTP
  attempt, no second browser call.

Both share `_fallback_fetch` (`curl_cffi.requests.AsyncSession(impersonate="chrome")`), the actual
fetch primitive. `impersonate="chrome"` chosen for the browser TLS fingerprint specifically — an
httpx/requests fallback would be the weaker client again and defeat the purpose
(`process-docs/news_pipeline/`, methods-optimization entry: `impersonate="chrome"` got
80/425 (18.8%) proxies through Cloudflare with HTTP 200 where another client (rustls-based monosans)
managed 0/17202, the isolating variable being the TLS fingerprint alone). Not reused from
`src/news/engine/proxy_pool/fetch.py` — its `(status, bytes)` contract with XML/HTML marker validation
is shaped for the news pipeline; crawl4ai needs `(url) -> html`. Bounded (curl_cffi's own `timeout=`
plus an outer `asyncio.wait_for`, `FALLBACK_FETCH_TIMEOUT_S=15.0`, symmetric with `PAGE_TIMEOUT_MS`)
and fail-soft (any exception returns `None`, never propagates).

`status_code != 200` gate in `_fallback_fetch`, deliberate: crawl4ai's own fallback wiring (path a)
forces `status_code=200` on ANY non-empty return — if curl_cffi itself got blocked (403/429) but still
returned an HTML block page, returning it anyway would make crawl4ai mark that a false success. Gating
on a genuine 200 before returning `.text` prevents that regardless of which path calls it.

## raw:// pipeline for path (b)'s markdown conversion

Verified live (in-process HTML, no external domain): `crawler.arun(url=f"raw://{html}", config=run_cfg)`
runs the fetched HTML through the same `DefaultMarkdownGenerator()` as a normal scrape, produces clean
markdown, and — confirmed via source read — `raw://` URLs are explicitly exempted from all
anti-bot/fallback machinery (`_is_raw_url` short-circuits `is_blocked` and the fallback check both), so
reusing `run_cfg` (which itself carries `fallback_fetch_function`) for this second call carries no
recursion risk. Used rather than hand-rolling HTML-to-markdown.

One trap this surfaced and avoided: the `raw://` conversion call produces its OWN `crawl_stats`
(`resolved_by: "direct"`, `success: True`, `attempts: 1`) describing the trivial "convert this local
string" step — feeding that into the log's `crawl4ai_*` fields would have claimed the browser fetched a
page it never touched. Those fields stay `None` on every path-(b) record (correct: no real crawl4ai
diagnosis exists for a browser call that raised before producing a result). Path (b)'s own outcome is
carried entirely in two NEW fields instead, kept structurally separate from `crawl4ai_*`:

- `pipe_fallback_used`: the except-block rescue was attempted.
- `pipe_fallback_resolved`: curl_cffi returned a genuine 200 with a body — describes the FETCH
  succeeding, not whether that body converted into usable markdown. The two fields can legitimately
  disagree: `resolved=True` with `outcome="empty"` means curl_cffi got a real 200 but the raw://
  conversion produced too little content to clear `EMPTY_THRESHOLD_BYTES` — read as "fetch worked,
  content didn't," not a contradiction.

Three states derivable without ambiguity: browser succeeded (`False, False`); pipe's own fallback
rescued it (`True, True`); everything failed (`True, False`).

`wall_ms` on a `pipe_fallback_used=True` record now includes the full failed browser attempt PLUS the
fallback fetch time — failure records got systematically longer once this landed, with no other field
marking why. Documented in the schema comment so a time-distribution read across a log spanning the
before/after boundary doesn't misread the jump as a general slowdown.

`config_hash`/`config` extended with `fallback_armed` (path a's wiring state, read off the real
`CrawlerRunConfig.fallback_fetch_function is not None` — path b is unconditional code, not a config
object attribute, so it has no stamp field of its own).

## Verification

**Wiring, not a dict comparison** — matching the pattern the stealth milestone established.
Path (a): `run_cfg.fallback_fetch_function is _fallback_fetch` (identity, against the real object).
Path (b): an integration test through the REAL `_scrape_one` except block (`_scrape_all` → `_scrape_one`
→ `except Exception:` → `_own_fallback_rescue`), not a direct call to the rescue function in isolation —
verified this actually depends on the real wiring by stashing the source change and re-running the same
test: it failed with `AttributeError` (the function didn't exist), confirming it isn't a shortcut that
passes regardless.

`is_blocked` branch check (`crawl4ai.antibot_detector.is_blocked`, real function, no network): the
brief's framing (HTTP 200 + near-empty body) takes the "HTTP 200 + near-empty content" branch — but the
crossref case's ACTUAL recorded signature ("no HTTP status recorded") is `is_blocked(None, "")`, which
does NOT take that branch (requires `status_code==200`); it takes Tier 3 structural integrity, Signal 1
("no `<body>` tag"), which needs no status code at all. This distinction is why path (a) alone cannot
rescue the crossref case even where it's reachable — precise branch identification mattered.

316-URL reference set (`dev/explore_pipeline/06_discovered_urls.txt`): `316/316 ok, 0 errors in 311s`.
Log confirms both fallback flags stayed False on all 316 records while `config.fallback_armed=True`
throughout — armed but correctly dormant on a healthy domain, not firing spuriously.

Full suite: `9 failed, 126 passed, 0 errors` (was 116 passed at the prior milestone, +10 new tests).
Diffed the `FAILED` line list against the original baseline — identical, no drift. The 9 pre-existing
`test_query_logger.py`/`test_proxy_pool.py` failures unrelated and unchanged throughout this entire
`pipe_scraper_hardening` effort, milestone to milestone.
