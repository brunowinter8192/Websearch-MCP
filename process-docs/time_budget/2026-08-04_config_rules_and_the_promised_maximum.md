# Time budget — the config rules, and the maximum a scrape was made to promise (2026-08-04)

Orchestrator-side record of the reasoning that produced this session's code changes. The per-milestone
worker entries in `process-docs/scrape_pipeline/` record WHAT was built; this records WHY those values
and not others, and what the decision cost.

Scope: the ad-hoc path (`src/scraper/scrape_url.py`, reached via the web-research skill's
search → drilldown → scrape). `pipe_scraper` carries separate time values from a different line of
reasoning and was deliberately not touched.

## The framing that changed mid-session

The opening question was "what maximum time may a scrape promise" — a question about a number. It was
replaced, on the user's call, by a question about RULES: explicit figures are worth little because they
do not survive the next toolbox addition, while a rule tells the next reader how to derive the figure
again. The session's output is therefore R1–R9 below; the numbers in the code are consequences of them.

A second constraint governed the whole session: levers are set on EXTERNAL sources — vendor docs, vendor
source, issue trackers, third-party field data — never on own measurements. The operational log
(`src/logs/scrape_log.jsonl`) is an observation channel that accumulates over time, not the instrument
that sets a value. This mirrors the method already recorded for the toolbox scoping in
`process-docs/scrape_toolbox/`.

## Where the old values came from

**`page_timeout=60000` was an inherited default, twice over.** crawl4ai's own CHANGELOG documents it as
replacing a previously hardcoded 30-second timeout, justified as "better handling for slow-loading
pages" — no measurement cited. The layer that actually executes the timeout, patchright 1.61.2
(`DEFAULT_PLAYWRIGHT_TIMEOUT_IN_MILLISECONDS`, `_impl/_helper.py`), defaults to 30000. crawl4ai's own
docs/examples scatter across 10000/30000/60000/80000/120000/200000, so the vendor is not self-consistent
either. This project then made crawl4ai's number explicit in 2026-06 and labelled it "determinism" —
what was actually derived at that point was the EXISTENCE of a hard navigation limit, never its height.

**`delay_before_return_html` had never seen a decision at all** on this path — the crawl4ai default of
0.1s applied by omission. The pipe path uses 0.5s and the explore path 3.0s, each from their own
reasoning, neither transferred here.

**`remove_consent_popups=True` was added 2026-08-03 with its ~1s cost documented but not booked against
anything** — there was no ceiling to book it against. That is the concrete precedent that motivated this
whole line of work.

## What the promise actually was before this session: there was none

`page_timeout` bounds only Playwright's `page.goto`. After a SUCCESSFUL goto, crawl4ai runs two further
waits that no config value reaches — `wait_for_selector("body", state="attached", timeout=30000)` and a
visibility poll via `csp_compliant_wait` with a literal 30000 in the generated JS
(`async_crawler_strategy.py`). Both are hardcoded. Confirmed by a third party, not only by source-read:
crawl4ai issue #219 shows a user running `page_timeout=90000` whose run nevertheless died at
`Page.wait_for_selector: Timeout 30000ms exceeded / waiting for locator("body") to be visible`.

Worse, markdown generation with `PruningContentFilter` is synchronous CPU work with no timeout anywhere.
So the honest description of the prior state is not "60s worst case" and not "~121s" — it is that the
call had no upper bound at all.

Why the 60s cap nonetheless looked like the ceiling in the log: on a goto timeout crawl4ai raises at the
goto site, so the two body waits are never reached. They bite only in the other constellation — goto
returns, body hangs or computes as invisible. That class had not occurred in this project's traffic.
This says something about the sample to date, not about what the code promises.

`ignore_body_visibility` defaults to True, which does NOT skip the visibility poll — it discards its
verdict. Per crawl4ai issue #219 the flag was introduced as a rescue for pages that keep `body` hidden
deliberately. The time is spent either way; only the consequence is dropped.

## The rules

**R1 — Two tiers: phase caps plus one total cap, and the promise sits on the total cap.**
Apache Nutch separates exactly so: `http.timeout` bounds a single network read, `http.time.limit` bounds
the total duration of one document. Playwright argues the same from the other side — in the API v1.0
review (microsoft/playwright#1348) Joel Einbinder: "Trying to tune individual timeouts seems like an
always wrong strategy to me", with Pavel adding "let's for now agree that present default timeout
setters are broken".

**R2 — The total cap must exceed the largest phase cap.**
Nutch checks this in `HttpBase` and warns when `http.time.limit` falls below `http.timeout`, because
otherwise the whole request expires before any individual read ever can.

**R3 — Only deterministically bounded waiting is admissible: a sleep yes, waiting on an event no.**
Playwright's own navigations doc states that modern pages keep loading after the `load` event and "there
is no way to tell that the page is loaded". An event-based wait cannot terminate by construction; a
fixed sleep costs exactly its value. This is the rule under which this project's earlier rejections of
`networkidle` and of `wait_for` fall retroactively — both were right, but were single cases without a
rule.

**R4 — A render wait is set at the documented saturation knee, not at the safe upper edge.**
crawl4ai issue #1665 carries a third-party measurement of this exact parameter: 0s → 12,376 chars
(partial), 3s → 33,874 (full), 5s → 33,874, 20s → 33,874. Knee at 3s, flat above it across nearly an
order of magnitude, so going higher only costs. The rule follows from the SHAPE of the curve, which
transfers; the LOCATION of the knee does not.

**R5 — Posts with the same effect are netted against each other, not added.**
The ~1s that `remove_consent_popups` spends IS render wait. Established by this project's own
reproduction (recorded in `process-docs/scrape_pipeline/`): an identical 126-byte `raw_markdown` diff on
rfc-editor.org was produced by `delay_before_return_html=1.1` ALONE with `remove_consent_popups=False`,
so the effect belongs to the waiting, not to the consent JS.

**R6 — A toolbox element is admitted only if its upper bound is countable from source.**
This is where `remove_consent_popups` had slipped through: benefit shown, cost documented, but no rule to
book it against. Counted retroactively — six wait sites in `remove_consent_popups.js`, five of them 300ms
behind `break`/`return` and therefore mutually exclusive (at most one fires, and only after an actual
click), plus one unconditional 500ms at the end of the click phase, plus 500ms Python-side after the
eval. Upper bound 1.3s, hard. No `MutationObserver`, no `waitForSelector`, no unbounded loop, no network
wait. The switch passes and stays on.

**R7 — A phase cap is not raised above the default of the layer that executes it without evidence for
the raise.**
Applied to `page_timeout`: patchright executes, patchright says 30000, crawl4ai's raise to 60000 has no
measurement behind it. No evidence → falls back to the executing layer's default.

**R8 — Non-configurable wait sites are not worked around; they are covered by the total cap.**
Settles crawl4ai's two 30s blocks without undercutting the library, and is simultaneously the reason the
total cap has to exist at all. Consistent with the standing decision to exhaust one library rather than
add more.

**R9 — The total cap is the sum of the countable maxima. Posts that are not countable get no reserved
share; they are covered by being inside the cap.**
Follows from R6, and closes R1+R2 upward — without it those two only yield a lower bound, and any figure
above the largest phase cap would satisfy them equally. This rule is this project's own construction; no
external source states it.

## The resulting number

| Summand | Value | Where it comes from |
|---|---|---|
| browser cold start | 1.1s | worst case of this project's own launch-latency probe (`process-docs/browser_posture/`) |
| navigation cap | 30.0s | R7 → patchright's own default |
| render wait | 2.0s | R4 (knee 3s) minus R5 (~1s already spent by consent handling) |
| consent handling | 1.3s | R6, counted from `remove_consent_popups.js` + the Python-side sleep |
| date extraction | 5.0s | `HTMLDATE_TIMEOUT_S`, this project's own pre-existing guard, passes R6 |
| markdown + PruningContentFilter | — | R9: not countable, no reserved share |
| **total** | **39.4s** | |

Not rounded — rounding would be a setting, and the point of the figure is that every summand has a
provenance. Enforced by one `asyncio.wait_for` around the acquisition in `try_scrape`; a caller that
exceeds it receives a regular failure result with `outcome="budget_exhausted"` in the scrape log.

For orientation, not as the basis: at the time of this session the ad-hoc log held 143 successful
records with p50 2.5s, p99 10.3s, max 33.7s.

## What the promise does not cover

- **Synchronous CPU inside crawl4ai.** `asyncio.wait_for` cancels at await points only. Markdown
  generation runs as sync CPU inside `arun()`; a pathological parse can overrun the budget, and the guard
  fires only once control returns to an await. Not fixed (no thread offload, no executor) — documented in
  the constant's comment and in `src/scraper/DOCS.md`.
- **Post-acquisition local work.** `truncate_content`, `write_sidecar` and `log_scrape` sit outside the
  guarded span on purpose, so that a budget-exhausted record stays writable. `timings_ms.total_wall` can
  therefore exceed 39.4s by that cost. Observed in the live timeout run: 39.45s inside the guard, ~40.3s
  process wall time.

## Prices paid, stated plainly

- **The one slow success is now cut.** Of 143 successful records to date exactly one exceeded 15s —
  stromauskunft.de at 33.7s, 47,859 bytes, a genuinely slow page. It falls under the new 30s navigation
  cap; it would have passed under the 39.4s total cap. One case in 143, and a real one.
- **R4 could not be confirmed on our own side.** The differential run built to test it — same URL through
  `cli.py`, once at the 0.1s library default, once at 2.0 — returned identical `bytes_raw_markdown`
  (11,218 both) on rfc-editor.org. Reason: under the current full config `remove_consent_popups`'s own
  forced ~1s already crosses that page's hydration window, so the page does not exercise the parameter at
  all. That run is evidence of no-regression only. It does confirm R5 sharply, and leaves R4 resting
  entirely on the third-party #1665 curve.

## What was deliberately NOT done

- crawl4ai's two 30s waits were not patched, monkey-patched or circumvented (R8).
- `wait_until="load"` untouched — backed by Playwright's own doc and R3-conformant.
- No fallback fetch path, no retries — both previously evaluated and rejected on this path.
- No per-domain logic of any kind; the ad-hoc path stays one fixed calibration for a mass of unknown
  domains.

## Weak points in this reasoning, for whoever reads this next

- R9 is our own construction with no external backing; it follows logically from R6 but nothing outside
  this project states it.
- R4 generalises the shape of a single third-party measurement on one JS-heavy page class, and our own
  attempt to reproduce the effect under production config produced no observable difference.
- The cold-start summand of 1.1s was measured on the SEARCH path (`src/search/browser.py`), not on the
  scraper. It is the best countable value available, but it is a transfer.
- The real duration of the synchronous markdown phase is unknown to anyone; only its theoretical
  unboundedness is established.
- That a 30s navigation cap does not cut legitimately slow pages holds for 143 records of this project's
  traffic, not for the web. The scrape log is the channel that will show this over time — the config
  stamp per record (`page_timeout_ms`, `delay_before_return_html_s`, `total_budget_s`) exists precisely
  so those outcomes stay comparable across config changes.

## Sources

crawl4ai 0.9.2 installed source (`async_crawler_strategy.py`, `async_configs.py`, `async_webcrawler.py`,
`config.py`, `browser_manager.py`, `js_snippet/remove_consent_popups.js`); patchright 1.61.2
(`_impl/_helper.py`); crawl4ai CHANGELOG + docs/examples in `unclecode/crawl4ai`; crawl4ai issues #219
(body-visibility wait, `ignore_body_visibility` origin), #1665 (render-wait saturation);
microsoft/playwright `docs/src/navigations.md`, `docs/src/test-timeouts-js.md`, issue #1348 (API v1.0
review, timeout philosophy); `apache/nutch` `conf/nutch-default.xml` + `HttpBase.java` (`http.timeout`
vs `http.time.limit`); `scrapy/scrapy` `default_settings.py` (`DOWNLOAD_TIMEOUT=180`);
HTTP Archive Web Almanac 2025 performance chapter (`HTTPArchive/almanac.httparchive.org`,
`src/content/en/2025/performance.md`) for the order of magnitude of real-world load timings — CrUX-based
LCP/FCP/TTFB distributions, not `load`-event distributions, so used as an analogy for scale only.
