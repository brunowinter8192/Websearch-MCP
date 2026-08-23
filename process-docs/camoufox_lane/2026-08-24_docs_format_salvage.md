# DOCS.md format salvage — camoufox_scrape.py (2026-08-24)

Content cut from `src/scraper/DOCS.md`'s `camoufox_scrape.py` module entry during the 2026-08-24
doccheck compression (Purpose condensed to one sentence). Snapshot as of the cut date.

**camoufox_scrape.py** (cut Purpose derivation/history):

- `try_scrape_camoufox(url, block_images=False) -> (content, meta)` launches one headed Camoufox
  (Playwright-Firefox, C++-level fingerprint spoofing), navigates (`page.goto(url,
  timeout=_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, wait_until="domcontentloaded")`, then
  `asyncio.sleep(CAMOUFOX_RENDER_WAIT_S)`), captures HTML + landed URL + status, converts HTML to
  markdown via crawl4ai's own `raw:` pipeline (reused exactly as `pipe_scraper._own_fallback_rescue`
  does — no hand-rolled HTML-to-markdown). As of 2026-08-06: `wait_until` changed from Playwright's
  `"load"` default to `"domcontentloaded"` — a Cloudflare challenge page holds the request and serves
  its own full page while it runs, so the real destination's `load` event cannot fire during that
  phase (observed live as a 30s `Page.goto` timeout on guenstiger.de; `pipe_scraper.py`'s engine
  already used `domcontentloaded`). A post-navigation render wait (`CAMOUFOX_RENDER_WAIT_S=5.0`) was
  also added — this lane previously had none (no crawl4ai `delay_before_return_html` equivalent) —
  same Cloudflare-documented figure/source as scrape_url.py's `delay_before_return_html`. As of
  2026-08-11 (budget-grounding milestone 2): the wait switched from Playwright's
  `page.wait_for_timeout` (vendor-marked "Discouraged" for production) to `asyncio.sleep` — traded a
  page-bound RPC's immediate crash detection for a host-side sleep with no page dependency (see
  `process-docs/camoufox_lane/2026-08-11_budgets_rebooked_and_render_wait_swapped.md`).

- `TOTAL_CAMOUFOX_BUDGET_S=245.0` composition: 30.0 Camoufox browser launch
  (`_PLAYWRIGHT_DEFAULT_TIMEOUT_MS`, an explicit override of Playwright's real implicit
  launch-timeout fallback, probe-confirmed via `dev/camoufox_lane/01_launch_timeout_probe.py`) +
  30.0 `page.goto` navigation cap (Playwright's documented default) + 5.0 post-navigation render wait
  (`CAMOUFOX_RENDER_WAIT_S`) + 180.0 markdown-conversion browser cold start (as of 2026-08-11,
  Playwright's own enforced launch-timeout fallback,
  `DEFAULT_PLAYWRIGHT_LAUNCH_TIMEOUT_IN_MILLISECONDS=180000`, since crawl4ai's `_build_browser_args()`
  never passes a `timeout` kwarg for this throwaway crawler; replaces an earlier 1.1s figure — a
  measured TYPICAL duration transferred from a different lane, not a ceiling — see
  `process-docs/camoufox_lane/2026-08-11_launch_timeout_enforcement_and_coldstart_ceiling.md`).

- Calibration surface (`_build_camoufox_kwargs`): `headless=False` (fixed — headless is the
  most-detected posture per field evidence), `os="macos"` (fixed to the real host OS — headed mode's
  screen size derives from the real monitor regardless of spoofed OS, so matching real host avoids an
  internal fingerprint mismatch), `block_webgl` not set (GPU/WebGL stays on, same posture as
  scrape_url.py's `enable_stealth`), `humanize`/`geoip`/`enable_cache`/`locale` all deliberately left
  unset (`humanize`: no mouse-driven interaction to benefit from it; `geoip`: reverses an earlier
  probe after reading `camoufox/ip.py` — without a proxy it triggers a real, previously-invisible
  network round-trip up to 30s worst case against 6 third-party IP-echo services, for an unverified
  benefit since geoip's documented core value is proxy-IP matching and this project has no proxy;
  `enable_cache`: no multi-page benefit for a one-shot fetch, costs memory Camoufox is already
  field-reported heavier on; `locale`: no target IP to match without geoip). `block_images` is the
  one parameterized (per-lane) knob. Every other launch parameter left at library default — BrowserForge's
  defaults mimic the real statistical distribution of device characteristics; hand-setting any without a
  measured reason reintroduces fingerprint inconsistency. `config` must never be hand-populated (Camoufox's
  own docs).

- `_extract_camoufox_config_stamp(kwargs, resolved)` reads `executable_path` off the real resolved
  `launch_options()` output but deliberately excludes the rest (fingerprint config, seeds, env vars) —
  those are randomized PER LAUNCH by BrowserForge design, hashing them would make `config_hash` unique
  every call. `launch_options()` is called once by this module itself (not left to `AsyncCamoufox`'s
  internal call) and handed back via `from_options=` to avoid generating a second random fingerprint
  just for the stamp.

- Markdown-conversion failure surfaced as fact: `meta["markdown_conversion_error"]` (crawl4ai's
  verbatim message) and `meta["content_is_raw_html"]` (explicit format flag) — when conversion fails,
  `content` is the raw captured HTML, never silently discarded. Deliberately not folded into
  `acquisition_error` (that means "no result at all," false here). As of 2026-08-06, the one
  identified trigger is closed at the source: `_html_to_markdown` calls
  `crawler.arun(url=f"raw:{html}", ...)`, not `raw://` — crawl4ai's own `urlparse()` on a
  `raw://<html>` pseudo-URL raises `Invalid IPv6 URL` whenever the HTML contains a bare `[` before
  the first `/` (real repro against `idealo.de`: 950 KB raw HTML returned instead of ~106 KB
  markdown); `raw:` carries no netloc and isn't subject to that parsing. Both prefixes equivalent in
  crawl4ai's own contract (`async_webcrawler.py`'s `_is_raw_url`, `async_crawler_strategy.py`'s
  raw-html branch, upstream `test_raw_html_browser.py::test_raw_prefix_variations`).

- `scrape_url_camoufox_workflow` mirrors `scrape_url_workflow`: logs to the SAME `scrape_log.jsonl`
  (`"engine": "camoufox"` discriminator), renders via `_format_camoufox_output`. `config_hash` read
  straight off `meta["config_hash"]` (computed once inside `try_scrape_camoufox`) — not re-hashed
  here, unlike the chromium lane, to avoid double-hashing.

- `_format_camoufox_output` is a sibling to `scrape_url.py`'s `_format_scrape_output`, not shared —
  same fixed-shape philosophy applied to this lane's own fact vocabulary (no `content_type`, no
  crawl4ai diagnosis; has `markdown_conversion_error`/`content_is_raw_html`). Sharing one renderer
  would require conditional logic violating "always the same shape."

- No-focus-steal launch: `_ensure_no_focus_steal(executable_path)` sets `LSUIElement=true` on the
  resolved Camoufox `.app` bundle's `Info.plist` — Playwright launches from inside its own internal
  Node.js driver, no `process_creator`-style hook exists (unlike the chrome lane's `open -g`).
  Verified empirically: a real `osascript`/System Events focus-poll around a live
  `try_scrape_camoufox` call showed "camoufox" frontmost for ~1.2s of a 1.8s run WITHOUT the fix, the
  calling terminal staying frontmost the ENTIRE run WITH it — reproduced under a real 4-URL pipe batch
  run (46/46 poll samples, terminal frontmost throughout). Firefox timer/render throttling in an
  unfocused window is already handled by Camoufox's own shipped `camoufox.cfg`
  (`focusmanager.testmode=true`).
