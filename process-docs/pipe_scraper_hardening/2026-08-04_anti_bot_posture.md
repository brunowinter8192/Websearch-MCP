# Milestone 4 — fixed anti-bot posture for pipe_scraper

2026-08-04. Fourth milestone of the `pipe_scraper_hardening` effort on `src/crawler/pipe_scraper.py`.
Gave the path its first anti-bot configuration — previously `BrowserConfig(headless=True,
verbose=False)`, nothing else. Preceded by milestone 3 (persistent JSONL log) deliberately: the
project's calibration method derives config values from external sources only, never from this
project's own domain sweeps, so the operational log has to exist BEFORE a config change to have
anything to compare later runs against.

## The frame

Two scrapers, opposite objective functions: `src/scraper/scrape_url.py` (ad-hoc, single URL,
agent-invoked) balances extraction QUALITY against getting through; `pipe_scraper` (mass capture)
optimizes ONLY for getting through — an LLM does full cleanup afterwards
(`skills/websearch-capture-and-index/SKILL.md` Phase 3). Consequence: nothing from the ad-hoc path's
extraction side transfers — no content filter, no `PruningContentFilter`, no `preserve_tags`, markdown
stays raw. Only anti-bot posture (stealth, simulation, consent-handling) transfers, and even that
transfers with a different justification on each path in one case (see `remove_consent_popups` below).

## Values set, and where each came from

- `enable_stealth=True` — verified live, not assumed: crawl4ai 0.9.2's `StealthAdapter`
  (`browser_adapter.py`) imports `playwright_stealth`'s `Stealth` class; playwright-stealth 2.0.3
  (installed) provides it. The historical `stealth_async` ImportError
  (`process-docs/scrape_pipeline/crawl4ai_stealth_stack_2026-05-31.md`, crawl4ai 0.8.6 +
  playwright-stealth 2.0.2) targeted a different symbol and no longer applies on this stack — confirmed
  by direct import AND by a wiring test (see Verification). Reachable specifically because
  `pipe_scraper` passes no custom `crawler_strategy`/adapter to `AsyncWebCrawler`: `browser_manager.py`
  only builds the `StealthAdapter` when `enable_stealth and not use_undetected`, and
  `use_undetected = isinstance(self.adapter, UndetectedAdapter)` (`async_crawler_strategy.py:117`)
  resolves False with the default `PlaywrightAdapter`. Measured to hold at
  `CONCURRENCY_PER_DOMAIN=8` on the 316-URL reference set with 0 crashes
  (milestone 2, `2026-08-04_stealth_concurrency_probe.md`, same area). Second effect worth naming:
  crawl4ai only appends `--disable-gpu`/`--disable-gpu-compositing`/`--disable-software-rasterizer`
  when `enable_stealth` is FALSE — its own comment says those flags disable WebGL, itself a headless
  signal anti-bot sensors read; confirmed post-implementation that these flags are genuinely absent
  from the launched browser's args with `enable_stealth=True`.
- `UndetectedAdapter` — deliberately NOT used. crawl4ai issue #1500 documents crashes above
  concurrency 1 ("Target page/context/browser has been closed"); incompatible by construction with
  `CONCURRENCY_PER_DOMAIN=8` on a pacing model already validated at that concurrency.
- `simulate_user=True` + `override_navigator=True` — both `CrawlerRunConfig` fields, confirmed gated
  independently of `magic` in `async_crawler_strategy.py` (mouse/scroll on `config.simulate_user or
  config.magic`, ~line 978; navigator-override init script on `config.override_navigator or
  config.simulate_user or config.magic`, ~line 598) — both available without pulling in magic's third,
  unwanted effect.
- `magic=False` — explicit, not a left-alone default. `magic` bundles the two effects above PLUS a
  random user-agent via `ValidUAGenerator`, triggered by `config.magic or config.user_agent_mode ==
  "random"` (`async_crawler_strategy.py:553-554`). At `CONCURRENCY_PER_DOMAIN=8` that means eight
  different generated UAs from one IP hitting one domain at once — a signal in itself — and a
  generated UA has no knowledge of which Chromium build is actually running, a documented
  UA/browser-version mismatch flagging signal in scraper-practitioner reports. Rejected on those two
  grounds, not an oversight; the code comment carries the full reasoning (not a summary) specifically
  because a bundled "convenience" flag left off looks like a missed improvement to a future reader who
  hasn't read the source as closely.
- `remove_consent_popups=True` — on `scrape_url.py` this switch is a content-QUALITY measure (an
  un-dismissed consent wall degrades one answer). On `pipe_scraper` it is a REACHABILITY measure: the
  capture skill deletes a confirmed block page outright rather than cleaning it
  (`skills/websearch-capture-and-index/SKILL.md` Phase 3, "A confirmed block page is garbage ->
  DELETE it") — so an un-dismissed consent wall here is a LOST page, not a dirty one. That asymmetry
  between the two paths is the actual reason the setting transfers, not just that it worked well on
  the ad-hoc path. Bounded cost: 1.3s worst case, counted from `remove_consent_popups.js`'s six wait
  sites (five 300ms, one 500ms) + the Python-side sleep
  (`process-docs/time_budget/2026-08-04_config_rules_and_the_promised_maximum.md`).
- Pacing/timeout values (`page_timeout`, `delay_before_return_html`, `DOWNLOAD_DELAY`,
  `CONCURRENCY_PER_DOMAIN`) — untouched. No external evidence to change them; this milestone's scope
  was anti-bot posture only.

## Config construction refactor — and a review-caught defect in it

Extracted config construction out of `_scrape_all` into `_build_configs()`, so a test could exercise
the SAME real `BrowserConfig`/`CrawlerRunConfig` objects the module actually builds (not a re-declared
copy) — needed for the wiring test below. First version of `_build_configs` took
`(download_delay, concurrency_per_domain)` as parameters, mirroring `_scrape_all`'s own signature by
habit — but used neither name in its body. Caught in review: a signature that accepts arguments it
ignores asserts a dependency that doesn't exist (the browser/run config does not depend on pacing
values), so it reads as "config is derived from pacing" and sends a future reader looking for a
relationship that isn't there — worse, the two tests that called it were passing those same values in,
documenting the false relationship as if intended. Fixed: `_build_configs()` takes no parameters.
`_extract_pipe_config_stamp` correctly keeps both (it genuinely reads pacing values into the log
stamp) — the two functions were conflated on habit, not on any real shared dependency.

## Verification

**Wiring test, not a dict comparison** — the review specifically required this framing, because
`StealthAdapter._check_stealth_availability` (`browser_adapter.py`) swallows an `ImportError` and
silently degrades `apply_stealth` to a no-op with no error raised anywhere; a test asserting
`browser_cfg.enable_stealth is True` would pass identically whether the underlying stealth injection
actually works or is silently dead — exactly the state this project already shipped once, undetected,
on 2026-05-31. `tests/test_pipe_scraper.py::test_build_configs_produces_live_stealth_adapter`
constructs the real `crawl4ai.async_crawler_strategy.AsyncPlaywrightCrawlerStrategy` from
`_build_configs()`'s real `BrowserConfig` (no network — `__init__` only builds state) and asserts
against crawl4ai's own objects: `browser_manager.use_undetected is False`, `._stealth_adapter is not
None`, `._stealth_adapter._stealth_available is True`, `isinstance(._stealth_adapter._stealth,
playwright_stealth.Stealth)`. Proved the test has teeth (not just a pass-through): manually forced the
`playwright_stealth` import to fail via a `builtins.__import__` hook and re-instantiated
`StealthAdapter()` directly — `_stealth_available` flips to `False`, `_stealth` to `None`, exactly what
would fail these assertions.

316-URL regression run (`dev/explore_pipeline/06_discovered_urls.txt`, the same set milestone 2's
concurrency probe used): `316/316 ok, 0 errors in 317s` — unchanged from the pre-hardening baseline,
confirming the new posture didn't break the validated path. Explicitly not read as evidence the
hardening WORKS (this domain already passed unhardened) — only as a "did we break it" check, per the
project's own calibration rule against tuning on sampled domains.

Full suite: `9 failed, 116 passed, 0 errors` both before and after the post-review `_build_configs()`
signature cleanup — diffed the `FAILED` line list against the milestone-1 baseline at every stage,
identical throughout. The 9 pre-existing `test_query_logger.py`/`test_proxy_pool.py` failures unrelated
and unchanged.

Reviewer independently verified the wiring against live crawl4ai objects post-implementation
(`use_undetected` False, `StealthAdapter` present, `_stealth_available` True, real `Stealth` instance)
and additionally confirmed the `--disable-gpu`-family flags are genuinely absent from the launched
browser's args with `enable_stealth=True` — the WebGL-stays-on claim, not just the stealth-adapter
claim, holds on the real launched browser.
