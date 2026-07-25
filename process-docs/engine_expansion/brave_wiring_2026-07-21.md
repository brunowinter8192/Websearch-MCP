# Brave Wired as Production Engine (2026-07-21)

**Engine:** `src/search/engines/brave.py` — `BraveEngine(BaseEngine)`
**Registry:** `src/search/search_web.py` — added to `ENGINES`
**Default set:** `src/search/filter_modes.py` — added to `_DEFAULT_ENGINES`, and to all three mode-sets `_BOOKS_ENGINES`, `_PDF_ENGINES`, `_DOCS_ENGINES` (general web engine, same class as `google`/`duckduckgo`/`mojeek`/`startpage` — receives the mode query modifier + participates in the mode's URL post-filter).

Follows on from three dev-only probes the same day (`26_brave_probe.py`, the Patchright-real-Chrome hand-tests, `27_brave_headed_lane_probe.py`) that established the mechanism and selectors, and concluded a "simplest form, no architecture" wiring was the right call for this engine.

## Config values

- `ENGINE_MAX_RESULTS["brave"] = 10` — no result-count URL param; DOM renders a fixed 10 `div[data-type="web"]` per page.
- `ENGINE_WATCHDOG_OVERRIDE["brave"] = 6.0` — probe latency measured up to ~3.9s, already close to the `ENGINE_WATCHDOG_TIMEOUT=3.6s` default; same treatment as `open_library`/`semantic_scholar`/`crossref`/`startpage`.
- Rate limiter: uniform `RateLimiter(max_requests=4, window_seconds=60)`, same as every other production engine — no Brave-specific throttling.

## The load-bearing design decision: graceful PoW→empty, never an exception

Brave's PoW/CAPTCHA is detected via the same title/body marker scan and `a[href*="pow-captcha"]` check validated across the day's probes. On a hit, `search_with_reason()` returns `[], S.EMPTY_BLOCK` directly inside its `try` block — a clean return value, not a raised exception. This is the entire mechanism by which Brave is safe to run inside the shared `asyncio.gather` fan-out alongside every other engine: a PoW hit degrades Brave's own contribution to zero for that query while every other engine's result set is unaffected, exactly like Google's existing `/sorry/`→`EMPTY_BLOCK` handling.

## Why no headed lane / isolated profile / proxy (the scope decision)

Brave's PoW block is IP/velocity-based and scoped to the Brave domain — it does not touch other engines' sessions or the shared browser profile in a way that matters for normal usage patterns. Real usage via the web-research skill is 2-4 near-simultaneous `search_web` queries per session, then days idle before the next session. That volume sits comfortably inside the clean window observed across the day's probes (up to 4 clean queries before a block, in the headless run), with a full multi-day cooldown between sessions — far longer than the ~30s-plus persistence window observed for an active block. At this volume, the more elaborate headed-background lane (`27_brave_headed_lane_probe.py` — proven working as a launch mechanism, but itself DROPPED for Brave specifically since even headed didn't clear the gate reliably) and any isolated-profile or proxy scheme are unneeded complexity. If real-world usage patterns turn out to burst harder than 2-4 near-simultaneous queries, that would be the trigger to revisit.

## Verification — what is proven today vs. what is pending IP cooldown

**Proven live, today:**
- Block-path correctness: `BraveEngine().search_with_reason()` run directly (production class, not a probe) against 3 queries returned `[], S.EMPTY_BLOCK` for all three, with zero exceptions and zero tracebacks — this IS the behavior being verified, and it held under a REAL active block (this IP was warm from the day's prior three Brave probes).
- CLI/entry-point integration: `cli.py search_web "python asyncio tutorial"` completed cleanly with `brave` present in the breakdown table at a graceful `0`, alongside the other 10 engines — no crash to the overall workflow from Brave's block state.
- Full test suite: same 9 pre-existing unrelated failures as before this change, no new failures; 7 new pure-function tests for `_build_results`/`_classify_diagnosis` passing.

**Proven at pure-function / reused-verbatim level, NOT re-demonstrated live end-to-end today:**
- Result-parsing correctness (`div[data-type="web"]` → title/url/snippet mapping) is validated by unit tests against synthetic item dicts, and the exact same selectors were live-verified against real, unblocked Brave result pages earlier the same day in `26_brave_probe.py` (20 real results per query) and `27_brave_headed_lane_probe.py` (10 real results in its first 2 clean queries). The selectors were copied verbatim into `brave.py`, unchanged.
- What was NOT observed today: the newly-wired `BraveEngine` itself returning real, non-empty results end-to-end in its final production form, because the IP was already blocked by the time this engine was wired (a direct consequence of the day's own probing activity). That specific confirmation — the wired class parsing a real live results page, not just its logic exercised against synthetic data — is pending natural IP cooldown and should be treated as an open verification item, not assumed passing by transitivity from the probes.
