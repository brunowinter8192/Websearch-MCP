# Bing Search Re-Evaluation — Dev Probe (2026-07-21)

**Probe:** `dev/search_pipeline/28_bing_probe.py` (self-contained, no `src/` import)
**Report:** `dev/search_pipeline/md/bing_probe_20260721_234046.md`
**Question tested:** scrapeability + latency for bing.com as a SECOND, independent access path to the Bing web index — NOT new coverage. DuckDuckGo already surrogates the Bing index in the production pool; Bing-direct is redundancy, symmetric to google(direct)+startpage(surrogate). Overlapping DDG's result set is expected and fine by design — the only question this probe answers is whether Bing-direct is reachable and fast enough today.

## Verdict: CANDIDATE

10/10 queries OK, 0 blocked, 0 errors, all 10 ≤5s. Latency distribution: min=531ms, median=691ms, max=2073ms — the fastest browser-scraped engine probed this week by a wide margin (sub-second on 7 of 10 queries), against mainstream/local-biz/docs queries in both German and English.

## Correction to the 2026-05-04 drop note's selector-drift assumption

The prior drop rationale cited `#b_results .b_algo` as having drifted, alongside the (separately valid) coverage argument. Re-derived from scratch here: **the selector had NOT actually structurally drifted** — `li.b_algo` inside `#b_results` is still the live, populated result container (10 per page). Whatever the state was in 2026-05, today's DOM matches the old shape at the container level.

## Key new handling detail: tracking-redirect unwrap

What DID require new handling: every organic result's href is now wrapped in a `bing.com/ck/a?...&u=<prefixed-base64>&...` tracking redirect rather than a direct destination URL. Unwrap logic (`_clean_url` in the probe): parse the `u` query parameter, strip its 2-character prefix (observed value: `a1`), base64url-decode the remainder with padding restored, and fall back to the raw wrapped href if decoding fails for any reason (never raises, degrades to the tracking URL rather than dropping the result). Verified correct against multiple live results, e.g. `u=a1aHR0cHM6Ly9kb2NzLnB5dGhvbi5vcmcvMy9saWJyYXJ5L2FzeW5jaW8uaHRtbA` → `https://docs.python.org/3/library/asyncio.html`.

## Selectors (current, live-verified)

- Search URL: `https://www.bing.com/search?q=<q>` (spaces → `+`), plain GET.
- Result container: `li.b_algo`.
- Title + href: `h2 a` inside the container (href is the wrapped tracking URL — needs `_clean_url`).
- Snippet: `.b_caption p` (falls back to `.b_caption` itself when no `p` child).
- A Microsoft cookie/consent banner (`Microsoft und unsere Drittanbieter verwenden Cookies...`) is present in the DOM alongside full results — it does NOT gate rendering. No click/accept step is needed for scraping; the banner is a visual-only concern for a human user, irrelevant to DOM-level extraction.
- Block detection: title/body scan for EN + DE bot-check phrasing (`captcha`, `unusual traffic`, `verify you are human`, `ungewöhnlichen datenverkehr`, etc.) — none triggered across the run.

## Sub-10-result queries are a legitimate data point, not a block signal

4 of 10 queries returned fewer than the full 10 results (`beste kaffeemaschine test`: 2, `gebrauchte waschmaschine frankfurt`: 9, `hausgeräte händler frankfurt`: 3, `gebrauchtwagen ankauf frankfurt`: 5) — all classified `OK` (no block marker fired, page loaded normally, just fewer organic `li.b_algo` slots on those particular SERPs, e.g. crowded out by non-organic SERP features). This is noted here as a real observation for any future result-count/max-results tuning, explicitly not evidence of blocking or degraded scrapeability — every one of those queries still returned real, on-topic results (e.g. `testsieger.de`/`faz.net` for the 2-result kaffeemaschine query).

## Sample quality confirms independent-index diversity

`python asyncio tutorial` → `realpython.com`, `datacamp.com`, `docs.python.org`, `computerwoche.de`. `how does DNS work` → `hostinger.com`, `cloudflare.com`, `geeksforgeeks.org`, `dnschecker.org`, `serveravatar.com`. `gebrauchte waschmaschine frankfurt` → `kleinanzeigen.de`, `hausgeraete-frankfurt.de`, `hgs-horn.de`. Several of these domains did not appear in the same-week Google/Startpage/Brave probes, consistent with genuine Bing-index content rather than a re-served Google/Brave result set.
