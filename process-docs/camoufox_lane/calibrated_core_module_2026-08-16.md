# Camoufox lane, milestone 1: calibrated core acquisition module (2026-08-16)

New area. Adopts Camoufox 0.5.4 as a SECOND, parallel acquisition lane beside crawl4ai's chromium
path — not a fallback, no trigger logic anywhere in code; the calling agent (ad-hoc) or run
operator (pipe) chooses the lane deliberately. Motivation: a fundamentally different engine
(Firefox fork, fingerprint spoofing compiled in at the C++ level) fails DIFFERENTLY than crawl4ai's
chromium — a prior probe measured it passing idealo.de's Akamai Bot Manager wall where the chromium
lane has months of documented failure there. This session built the calibrated core module
(`src/scraper/camoufox_scrape.py`, `try_scrape_camoufox`) — no CLI surface, no logging wiring; both
are later milestones. Draws on both `scrape_pipeline` (the landed-URL surface, `hash_config` reuse,
the fact-reporting contract) and `pipe_scraper_hardening` (the `raw://` markdown-conversion
pattern, reused exactly as `_own_fallback_rescue` does) — a genuinely new area, not a continuation
of either.

## Calibration: every value read from source, not assumed

Read the installed `camoufox` package source (`utils.py`'s `launch_options`, `ip.py`, `pkgman.py`,
`exceptions.py`) and the official docs (usage/config/geoip/browserforge/stealth/cursor-movement
pages) before setting anything. Decisions:

- `headless=False`, `block_webgl` not set — both fixed by the user ahead of this session (headed
  is the strongest posture per field evidence; WebGL/GPU stays on, same posture as the chromium
  lane's `enable_stealth`).
- `os="macos"`, fixed to the real host OS rather than Camoufox's own default (random choice among
  windows/macos/linux). Reasoning: headed mode's screen size is generated from the REAL monitor
  regardless of which OS is spoofed (documented in Camoufox's own browserforge page) — spoofing a
  different OS while rendering on a real, visible macOS window risks the exact internal
  fingerprint inconsistency the stealth doc says gets Camoufox flagged.
- `humanize` left unset. Its cursor-movement humanization only fires on explicit Playwright mouse
  actions; this module's flow is `goto()` + `content()` only, no clicks — enabling it would add up
  to its own `maxTime` (1.5s default) of wall time for a benefit that doesn't apply here.
- `geoip` left unset — a deliberate REVERSAL of the earlier probe, which ran with `geoip=True`.
  Reading `camoufox/ip.py` found that without a proxy, `geoip=True` calls `public_ip()`
  synchronously during option resolution: a real, previously invisible network round-trip against
  up to 6 third-party IP-echo services at 5s timeout each — a genuine (if unlikely) 30s worst case
  added to EVERY acquisition before the browser even launches. `geoip`'s documented core value is
  proxy-IP matching (the project has no proxy, a separate fixed decision); the earlier probe's
  Akamai pass cannot be specifically attributed to `geoip=True` rather than to running from a
  residential IP at all, per field evidence that Akamai's Camoufox detection is tied to datacenter
  IPs specifically. Concrete newly-discovered cost against an unverified benefit → off.
- `enable_cache` left unset (one-shot fetch, no back/forward use, costs memory Camoufox is already
  field-reported as heavier on than patchright/undetected-chromium) and `locale` left unset (no
  target IP to match without geoip; hand-picking one would be the same non-representative override
  the stealth doc warns against).
- `block_images` is the one PARAMETERIZED knob (`try_scrape_camoufox(url, block_images=False)`) —
  flagged by the brief as a likely per-lane decision; left as a caller-facing parameter rather than
  a fixed value so later ad-hoc/pipe wiring can each choose.
- Every other parameter on the 33-param surface (fonts, addons, screen, window,
  fingerprint_preset, ff_version, main_world_eval, disable_coop, block_webrtc, webgl_config,
  firefox_user_prefs, `config`) left at its library default under one blanket rule: BrowserForge's
  defaults are built to mimic the real statistical distribution of device characteristics;
  hand-setting any of them without a measured reason reintroduces the exact non-representative
  fingerprint the stealth doc says gets Camoufox detected. `config` specifically must never be
  hand-populated per Camoufox's own docs.

## The budget: 61.1s, same discipline as TOTAL_SCRAPE_BUDGET_S

`TOTAL_CAMOUFOX_BUDGET_S = 61.1` = 30.0 (Camoufox/Playwright-Firefox browser launch — Playwright's
own `BrowserType.launch()` default, confirmed in the installed package's generated stubs, no
Camoufox-specific evidence to depart from it) + 30.0 (`page.goto`, Playwright's own default,
`wait_until="load"` also left at default) + 1.1 (the markdown-conversion step's own throwaway
chromium browser cold start — reused from this project's own earlier measured chromium/patchright
figure, a legitimate same-class proxy, not an invented number, since that conversion step ALSO
launches a fresh browser instance via crawl4ai). Markdown generation itself is uncounted, same
honesty caveat as the chromium lane's own budget constant.

The config stamp (`_extract_camoufox_config_stamp`) reads `executable_path` off the REAL resolved
`launch_options()` output but deliberately excludes the rest of that dict (fingerprint config,
per-launch random seeds, env vars) — those are randomized by BrowserForge design on every launch,
so hashing them would make `config_hash` unique every call and defeat its purpose as a grouping
key. `launch_options()` is called once, by this module, and handed back to `AsyncCamoufox` via
`from_options=` specifically so a second, different random fingerprint isn't generated just for
the stamp.

## Real-run results (module-level driver, no CLI yet, visible headed window each run)

| URL | Wall | Status | Landed URL | Outcome |
|---|---|---|---|---|
| `idealo.de` OffersOfProduct (Fritz Box) | 3.7–3.9s | 200 | `.../203078159_-woman-hybrid-jacket-...html` | See finding below |
| `rfc-editor.org/info/rfc2616/` | 8.2s | 200 | identical (no redirect) | 470,169 bytes real markdown, control passes |
| `docs.anthropic.com/en/api/getting-started` | 4.9–5.0s | 200 | `platform.claude.com/docs/en/api/overview` | 20,306 bytes real markdown, host-change redirect confirmed |

**idealo.de: Camoufox passed Akamai.** Direct diagnostic capture confirmed 916,008 bytes of real
markup — `tagManagerDataLayer` showing `"name":"CMP Woman Hybrid Jacket Fix Hood (33Z6026)"` — a
genuine product page, NOT the "Sorry! Something has gone wrong" Akamai block page this project has
seen from the chromium lane. It landed on the WRONG product (a jacket, not the requested Fritz
Box) — a real redirect to unrelated content, exactly the shape the landed-URL work
(`scrape_pipeline` area) exists to detect, now reproduced on a second engine.

## Finding: a pre-existing crawl4ai raw:// bug, with a cross-module blast radius

The idealo HTML above initially produced 0 markdown bytes with no exception — investigated rather
than accepted at face value. Root cause, confirmed via a 2-line local reproduction: crawl4ai's OWN
internal `urlparse()` call on the `raw://<html>` pseudo-URL raises `ValueError: Invalid IPv6 URL`
whenever the HTML contains a bare `[` before the first `/` in the document (idealo's page has one
in an early inline `<script>`, a JS array literal: `var utag_data = [{"country":"DE",...`).
`urlparse`'s bracketed-netloc check requires nothing before a `[` in what it treats as netloc; any
`[` appearing in the long slash-free HTML prefix before it triggers the same crash. crawl4ai's own
`_crawl_web` wrapper catches this internally and returns `success=False`/`markdown=None` rather
than propagating — not a Camoufox defect, not fixed here (no crawl4ai patch, no hand-rolled
markdown, both explicitly out of this milestone's scope).

This is NOT unique to the Camoufox lane: `src/crawler/pipe_scraper.py`'s already-shipped
`_own_fallback_rescue` calls the exact same `crawler.arun(url=f"raw://{html}", config=run_cfg)`
pattern and would hit the identical crash on any HTML shaped the same way. `pipe_scraper`'s own
test suite only ever exercises tiny synthetic HTML fakes, so this was never caught there — a real,
latent defect in already-shipped code, surfaced by this session's real-run testing, left
unaddressed (a question for whoever next touches that reuse pattern, not chased here, matching this
project's established discipline of recording such findings rather than silently patching around
them mid-milestone).

## Fix within this milestone: the conversion failure must be a visible fact, not a silent loss

Initial implementation returned `("", meta with acquisition_error=None, raw_markdown_bytes=0)` on
the idealo run above — indistinguishable from "the page was genuinely empty," even though 916KB of
real HTML was already captured and in hand. This is the exact invisible-failure class the whole
session's landed-URL work has repeatedly targeted, now found inside this milestone's own new code
before recap, not after.

Fix: two new, orthogonal meta fields. `markdown_conversion_error` (str | None) — crawl4ai's error
message verbatim, an OBSERVATION. `content_is_raw_html` (bool) — an explicit format flag, not
inferred from the error field's truthiness, since format matters structurally to the caller, not
just diagnostically. Deliberately NOT folded into `acquisition_error`: that field's contract is "no
result at all," which is false here — real HTML, status, and landed_url were all captured; a
downstream conversion failure is a categorically different state. When conversion fails, `content`
returned is the RAW CAPTURED HTML (never `""`) — honoring "returns whatever came back,
unconditionally" literally: the real page is never silently discarded just because the markdown
step failed. `_html_to_markdown` itself made internally fail-soft (returns `(markdown, error)`,
never raises) with a second, defense-in-depth try/except at the call site, so ANY conversion-layer
failure — whether crawl4ai swallows it internally (the observed shape) or something else raises —
is guaranteed to land in the new fields, never in `acquisition_error`.

## Open requirement, MANDATORY, DEFERRED to the pipe-wiring milestone

This lane's headed launch currently has no no-focus-steal mechanism — accepted as this
milestone's interim state, not resolved here. The chromium lane launches headed-but-backgrounded
via macOS `open -g -n -a` (`src/search/browser.py`) so the window never steals focus; that
mechanism does not transfer 1:1 to Camoufox, which has no app bundle (the fetched binary lives
under `~/.cache/camoufox`, launched via the Python library through Playwright, not `open`). Finding
the equivalent — prefs/args/window positioning, or `open -g` pointed directly at the resolved
`executable_path` — plus the Firefox background-throttling question this raises, is deferred,
explicit, unstarted work, resolution point named as the pipe-wiring milestone. Until then, a
`try_scrape_camoufox` call may steal window focus.

## Verification

12 tests in `tests/test_camoufox_scrape.py`: normal fetch, redirect landed_url capture, budget
exhaustion, browser-binary-missing detection (`CamoufoxNotInstalled`), generic exception fail-soft,
config-stamp real-value reads, config-stamp excludes randomized fingerprint data, config_hash
stability across calls, and two dedicated tests for the markdown-conversion-failure fix (one
faking `_html_to_markdown` raising directly, one faking the actual crawl4ai-swallows-it-internally
shape) — both asserting the captured HTML survives and `acquisition_error` stays `None`.

Full suite: `9 failed, 160 passed`. `FAILED` list diffed against the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift.

`requirements.txt`: `+camoufox` (the official PyPI package, 0.5.4, already installed in this
environment from an earlier dev probe — not `cloverlabs-camoufox`). The Camoufox browser binary
and GeoIP MaxMind database were also already fetched/cached from that same earlier probe (~700MB),
so no fresh download cost was incurred this session.
