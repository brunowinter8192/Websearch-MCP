# Camoufox lane, milestone 3: no-focus-steal launch + pipe engine switch (2026-08-20)

Continues the `camoufox_lane` area. Two halves: resolving the no-focus-steal requirement deferred
since milestone 1, and wiring the pipe path's own engine switch (`--engine {chromium,camoufox}`).

## No-focus-steal: LSUIElement, not `open -g`

The chrome lane's mechanism (macOS `open -g -n -a`, `src/search/browser.py`) does not transfer to
Camoufox: it depends on pydoll's `BrowserProcessManager.process_creator` hook, which lets that lane
substitute its OWN subprocess launcher. Playwright has no equivalent — the browser process is
spawned from inside Playwright's own internal Node.js driver, never exposed to Python. Confirmed by
reading the installed `playwright` package directly rather than assuming from the pydoll precedent.

Camoufox's fetched macOS build turned out to be a genuine `.app` bundle (`Camoufox.app`, confirmed
via `launch_path()`'s resolved path) — not the bare binary the milestone-1 framing assumed. That
opened a different lever: `LSUIElement=true` in the bundle's `Info.plist`, a property of the app
itself read by macOS at `NSApplication` startup, independent of how the process was spawned (unlike
`open -g`, which only suppresses LaunchServices' OWN activation-on-open behavior).

Verified empirically before trusting it: built a real focus-poll (`osascript`/System Events
sampling the frontmost application every 250ms) around a live `try_scrape_camoufox` call.
**Without** the fix: "camoufox" became frontmost for ~1.2s of a 1.8s run — focus genuinely stolen
from the calling terminal. **With** `LSUIElement=true` set on the same bundle: frontmost stayed the
calling terminal for the entire run, same URL, same code path. Reproduced again under a real
4-URL pipe batch run at the end of this session: 46/46 poll samples showed the terminal frontmost
throughout.

Implemented as `_ensure_no_focus_steal(executable_path)` in `camoufox_scrape.py` — idempotent
(checked before written), cheap, macOS-only (a silent no-op elsewhere), called once per
`_acquire()` so both the ad-hoc lane and this session's pipe engine get it for free.

The throttling half of the same concern (does Firefox throttle timers/rendering in an unfocused
window) turned out to already be handled: Camoufox's own shipped `camoufox.cfg` sets
`focusmanager.testmode=true`, with the comment "Allow the application to have focus even it runs
in the background." Found directly in the installed config file, not guessed — this is exactly the
kind of Selenium/Marionette-ecosystem preference built for this purpose, already present before
this session touched anything.

## The pipe engine switch

`scrape_urls_workflow`/`_scrape_all` gained `engine: "chromium" | "camoufox"` (per-RUN, never
per-URL, never auto-selected) and `block_images: bool`. Chromium path unchanged in behavior;
camoufox path dispatches to a new `_scrape_one_camoufox`/`_log_pipe_camoufox_record` pair, siblings
to the existing chromium functions rather than one shared function with extra optional
parameters — the crawl4ai-own-fallback and pipe-own-rescue mechanisms are chromium-lane machinery
that does not run on the camoufox engine at all (camoufox IS the deliberate alternative; a
fallback-of-the-alternative would be exactly the auto-selection this whole lane exists to avoid).

`CAMOUFOX_CONCURRENCY_PER_DOMAIN=1`, a new, deliberately conservative constant: the chromium
default of 8 was earned by measurement (`process-docs/pipe_scraper_hardening/
2026-08-04_stealth_concurrency_probe.md`, 0 crashes at 8) for a model where 8 concurrent requests
share ONE already-launched browser. `try_scrape_camoufox` launches a fresh, real, headed Firefox
process per call — no measurement yet exists for how many concurrent instances this machine
tolerates, and field evidence already on record for this lane says Camoufox's memory footprint is
heavier per-instance than patchright/undetected-chromium. Per this project's standing rule (no
raise without evidence), defaults to the most conservative value. `--concurrency-per-domain` still
applies to either engine explicitly; only the default when the flag is omitted is
engine-conditional, resolved inside `_scrape_all` itself (not just the CLI parser) so any direct
caller gets the same engine-aware default.

`config_hash`/`config` are NOT comparable across engines, ever — the pipe log's own schema comment
now says so explicitly. Chromium's `config` is the full pacing/stealth surface, computed once per
whole run off the real shared `BrowserConfig`/`CrawlerRunConfig` objects. Camoufox's own `config`
(`headless`/`os`/`block_images`/`timeout`/`executable_path`/`total_budget_s`) has no pacing/stealth
keys at all and is read PER URL off that call's own `try_scrape_camoufox` meta — there is no shared
browser to stamp once. A later log reader grouping by `config_hash` must stay within one `engine`
value; a hash collision across engines proves nothing.

## `block_images`: an open tension, not a settled default

Chose `block_images=True` for the pipe engine (raw mass capture never consumes images; camoufox's
own docs frame the flag as bandwidth-saving, relevant at pipe volume) against the ad-hoc lane's
`block_images=False` default from milestone 1. This split was not examined closely enough at the
time of writing pipe_scraper's own default — the real pipe run this session surfaced Camoufox's own
`LeakWarning` on every single URL: *"Blocking image requests has been reported to cause detection
issues on major WAFs. If this is intentional, pass i_know_what_im_doing=True."* This is the
library's own documented anti-bot-signal risk, not a hypothetical concern, and it surfaces at
exactly the volume (many URLs in one run) where a WAF is likeliest to notice a pattern. No
measurement exists on either side of this split — recorded as an OPEN calibration question for a
future session, not as two independently-justified, settled defaults. A future session should
measure (pass rate with vs. without `block_images` on a real domain set) before trusting either
lane's current default.

## Verification

13 new tests (7 `test_pipe_scraper.py`: default-engine-unchanged, camoufox-dispatch, concurrency
default resolution via timing, both engines' record-shape absent/present fields, acquisition-error
outcome mapping; 6 `test_camoufox_scrape.py`: `_find_app_bundle`, `_ensure_no_focus_steal`
idempotency/platform-gating, using real tmp_path bundle-shaped directories + real `plistlib`
round-trips, no fakes needed for that part).

Real CLI runs, both engines, JSONL records inspected directly:
- Chromium, 3 URLs: unchanged behavior, `engine="chromium"` now present, all camoufox-only fields
  absent.
- Camoufox, 4 URLs (`example.com`, the confirmed `rfc-editor.org` 302 redirect, the
  `docs.anthropic.com` host-change redirect, and the idealo showcase): 4/4 `ok`. idealo record:
  `http_status=200` (Akamai passed), `landed_url` the wrong product (the jacket page),
  `content_is_raw_html=true`, `markdown_conversion_error` carrying crawl4ai's verbatim error, and a
  real 916,879-byte raw-HTML `.md` file actually written to `--output-dir` — the full showcase
  reproduced inside a pipe record, not just the ad-hoc one from the prior milestone.

Full suite: `9 failed, 180 passed`. `FAILED` list diffed against the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift.

## What remains open after this session

This closes the camoufox lane's build-out for this session. `skills/` wiring for BOTH
`websearch-web-research` (ad-hoc) and `websearch-capture-and-index` (pipe) is deliberately deferred
to a user session — lane choice will be documented there as OPTIONAL, since no reliability data yet
exists favoring either lane over the other for any particular site or use case. The `block_images`
tension above and the config-shape-divergence note are the two open items a future session should
pick up before treating either lane's current calibration as final.
