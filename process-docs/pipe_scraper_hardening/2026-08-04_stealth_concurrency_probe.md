# Measuring enable_stealth at CONCURRENCY_PER_DOMAIN=8 (2026-08-04)

Part of the `pipe_scraper_hardening` effort on `src/crawler/pipe_scraper.py` (the mass-capture scrape
path). Its browser config at the time of this measurement was `BrowserConfig(headless=True,
verbose=False)` — no anti-bot posture. Adding `enable_stealth=True` was under consideration; this
measures the one blocking risk before that decision, without touching production source.

## Why this, not UndetectedAdapter

`src/scraper/scrape_url.py` (the single-URL path) already has a stealth posture, but it combines
`enable_stealth=True` with `UndetectedAdapter` — documented (crawl4ai issue #1500) to crash above
concurrency 1 ("Target page/context/browser has been closed"). `pipe_scraper` runs
`CONCURRENCY_PER_DOMAIN=8`, so `UndetectedAdapter` is off the table outright, no measurement needed.
`enable_stealth=True` alone routes through a different mechanism — `StealthAdapter`
(`playwright_stealth`, applied via `add_init_script`) — confirmed by reading the installed
`crawl4ai/browser_manager.py`: `_stealth_adapter` is only constructed `if self.config.enable_stealth and
not self.use_undetected`. On paper this should be concurrency-safe; that was inference, not measurement,
going into this milestone.

## Method

Built `dev/pipe_scraper_hardening/01_stealth_concurrency_probe.py` — a dev-local copy of
`pipe_scraper.py`'s exact per-domain pacing logic (domain lock + jitter gate + per-domain semaphore),
NOT an import (`src/` imports from `dev/` scripts are disallowed by repo convention; enforced by a write
guard that rejected the first draft). The copy adds exactly one thing production lacks: verbatim
exception-message capture into a crash log (production's own `_scrape_one` swallows exception text,
collapsing everything to `outcome='error'` with no detail — the reason a copy-with-instrumentation was
needed rather than a passthrough call).

Ran the validated 316-URL set (`dev/explore_pipeline/06_discovered_urls.txt`,
`docs.github.com/de/rest`) twice, config held constant (`DOWNLOAD_DELAY=1.0`,
`CONCURRENCY_PER_DOMAIN=8`, `page_timeout=15000`, `delay_before_return_html=0.5`): baseline first, then
`enable_stealth=True`, gap = 300s between runs. Gap was raised from an initial 60s plan specifically
because `process-docs/pipe_scraper/` records WAF budget recovery on the order of minutes (an 8s gap alone
had produced a ban in that prior characterization) — at 60s a stealth-run failure could have been
baseline afterglow rather than a stealth effect, which would have made the whole measurement unreadable.
Single ordering, single repeat — not interleaved, not randomized (~640 requests at ~1 req/s already
~16.5 min combined; scope-limited to one pass each).

## Result

Both runs: 316/316 ok, 0×429, 0×http_error, 0×empty, 0×error, 317s wallclock each, 0 exceptions of any
kind in either crash log (no "Target page/context/browser has been closed" or comparable failure).
`enable_stealth=True` held at concurrency 8 on this set — measured, not inferred.

36/316 URLs (11%) differed in byte count between runs (33 grew, 3 shrank, mean delta +72 bytes, max
2987 bytes). Line-diffed the max-delta URL (`using-the-rest-api/issue-event-types`): the difference was
NOT rendering/fingerprint noise — 134 internal anchor links in the stealth run carried a
`?apiVersion=2026-03-10` query-string suffix that baseline's identical links lacked (`grep -c`:
stealth=134, baseline=0). Root cause: docs.github.com's own client-side API-version-selector JS stamps
outgoing links differently depending on session/browser state — a genuine content difference, not a
fetch failure. Whether this is driven by stealth's fingerprint, WebGL availability, or ordinary
session-state variance between two independently-launched browser instances is NOT established by this
data — flagged as inference, not measured causation.

## The measurement's real scope — explicitly not isolated

crawl4ai wires `enable_stealth` to two things simultaneously: the `playwright_stealth` JS injection AND,
per `browser_manager.py` (`if not config.enable_stealth: flags += [--disable-gpu,
--disable-gpu-compositing, --disable-software-rasterizer]`), WebGL availability (its own comment: those
flags are a headless signal anti-bot sensors read). This probe measured that combined package —
"stealth JS + WebGL re-enabled" — surviving concurrency 8. It does NOT isolate the JS injection from the
WebGL/GPU-flag difference riding along with it; decoupling the two would need a third variant
(stealth JS forced with GPU flags still applied, or vice versa), not attempted here.

Also not measured: whether the result transfers to non-github domains/WAFs, sustained/longer runs, or
either run ordering besides baseline-then-stealth.

## Artifacts

`dev/pipe_scraper_hardening/01_stealth_concurrency_probe.py` — probe script, dev-local copy pattern.
`dev/pipe_scraper_hardening/json/01_baseline_results.json`, `01_stealth_results.json` — raw per-URL
results + crash logs, both runs.
`dev/pipe_scraper_hardening/md/01_stealth_concurrency_probe_20260804.md` — full report (outcome table,
crash logs, byte-count comparison, verdict).
