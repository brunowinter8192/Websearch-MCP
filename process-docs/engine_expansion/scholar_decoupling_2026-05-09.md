# Scholar HTTP Migration + Google Decoupling — 2026-05-09

---

## Status Quo (before this change)

- `src/search/engines/scholar.py` — pydoll browser, `ScholarEngine`, `name="google_scholar"`
- Scholar in default engine set via `return ENGINES` in `_select_engines(None)` — ran on every bare query
- Scholar in `_PDF_ENGINES = {google, duckduckgo, mojeek, google scholar}` — ran on every `--pdf` query
- Result as of 2026-05-08: 100% EMPTY_BLOCK in every default or pdf-mode query (triggers a+b both active)
- `no_google_burst_smoke.py` drove `ScholarHTTPProbe` from `dev/`, not the production engine
- `ENGINE_WATCHDOG_OVERRIDE` had no Scholar entry — 3.6s default insufficient for 0.7-5s HTTP range
- `query_log.jsonl` had no visibility into which engines were excluded before fanout

---

## What Changed

**Step 1 — HTTP migration (`src/search/engines/scholar.py`):**
- Replaced pydoll browser with `httpx.AsyncClient` GET (`follow_redirects=False`)
- `CONSENT=YES+` cookie bypasses consent gate without browser interaction
- Redirect detection: 30x status → `/sorry/` location → `S.EMPTY_BLOCK` + `limiter.backoff()`
- Inline captcha detection: `//form[@id='gs_captcha_f']` xpath → `S.EMPTY_BLOCK` + `limiter.backoff()`
- HTML parsed via lxml; selectors: `//div[@data-rp]` (result containers), `//h3[1]//a` (title/url), `.//div[@class='gs_rs']` (snippet)
- `ScholarEngine` class name, `name="google_scholar"`, `BaseEngine` inheritance, rate-limiter registration — all unchanged
- `search` wrapper pattern unchanged (swallows exceptions, calls `limiter.backoff()`, returns `[]`)
- `ENGINE_WATCHDOG_OVERRIDE["google_scholar"] = 6.0` added (HTTP latency 0.7-5s; 3.6s default → TIMEOUT_HTTPX)

**Step 2 — Google decoupling (`src/search/filter_modes.py`, `src/search/search_web.py`):**
- `_DEFAULT_ENGINES` constant added to `filter_modes.py` — 9 engines, excludes `"google scholar"`
- `_PDF_ENGINES` reduced from 4 to 3 engines — `"google scholar"` dropped
- `_select_engines(None)` now filters via `_DEFAULT_ENGINES` instead of returning all `ENGINES`; returns `(selected, excluded)` tuple where `excluded={"google_scholar": "decoupled_from_google"}`
- Scholar remains in `ENGINES` dict and is accessible via explicit `engines="google scholar"` param (escape hatch for testing)
- Scholar dormant in all default production paths until Pooling-Rework

**Step 3 — Exclusion logging (`src/search/search_web.py`, `src/search/query_logger.py`):**
- `apply_filter_mode` returns `(selected, qmm, mode_id, excluded)` — 4th element is engines dropped by active filter mode
- `_select_engines` and `apply_filter_mode` excluded dicts merged in `search_web_workflow` → `engines_excluded`
- `_build_query_log_entry` writes `engines_excluded` to query log JSONL — visibility into what didn't run and why
- `query_logger.py` schema docstring updated with new field + reason enum

---

## Why Option (c) and Not (d)

Option (d): Scholar task awaits `asyncio.sleep(N)` pre-acquire when `google` is in selected set — hypothesis that N=1.5s escapes Google's co-fire detection window.

**Why (d) is rejected:**
- Hypothesis-driven: no empirical data confirms 1.5s suffices. Co-fire detection window is undocumented, may be IP-state-dependent.
- If 1.5s insufficient, smoke fails → tune up toward slowest-engine ceiling (6s open_library). At N≥3s the delay exceeds Scholar HTTP search time (~700ms median) and becomes visible in wallclock — degrades from Rang 1 (absorbed) to Rang 2 (visible) per the project's Mitigation-Choice Discipline. Rang 2 requires explicit user approval.
- Conditional logic in `_engine_with_timing` checking for Google's presence in every fanout call: hot-path complexity that Pooling-Rework would have to work around or remove.
- (c) is deterministic: `_DEFAULT_ENGINES` is a declarative constant, no runtime conditional, no timing hypothesis, no tuning budget. Pooling-Rework gets a clean slate — add a new constant, point Scholar at it.

## Why Not Option (a) or (b)

- **(a) Sequential Scholar after gather** — +700ms unconditional on every academic-with-google query. `total_ms = max(other_engines) + scholar_http` instead of `max(other_engines)`. Mitigation-Choice Discipline Rang 2: requires explicit user acceptance of wallclock cost. Not justified when Rang 3 (Scholar dormant, zero coverage delta from current 100%-blocked state) is available.
- **(b) Mutual-exclusion in `_select_engines` when google present** — functionally equivalent to (c) but implemented as a runtime conditional (`if "google" in selected: drop scholar`) rather than a declarative set. Less readable, harder to extend, same coverage result. Option (c) without a `--scholar` flag IS option (b) semantically — the difference is declarative vs imperative; (c) wins on readability and extension path.

---

## Pooling Handoff

Pooling-Rework designs the pool definitions that control which engines fire together. For Scholar to be production-functional again:

1. Pool definition must place Scholar in a **Google-free pool** — a named engine set constant that excludes `"google"`.
2. Example: `_ACADEMIC_ENGINES = frozenset({"google_scholar", "crossref", "openalex", "semantic_scholar"})` — Scholar + 3 academic HTTP engines, no Google browser.
3. The `_DEFAULT_ENGINES` constant in `filter_modes.py` is the correct extension point — Pooling-Rework adds new constants alongside it, does not touch `_DEFAULT_ENGINES`.
4. This file is the as-is reference for Pooling-Rework design notes when that work starts.

---

## Sources

| Source | Relevance |
|---|---|
| `dev/search_pipeline/01_reports/no_google_burst_20260508_220631.jsonl` | Empirical basis: 12/12 OK for HTTP Scholar in 9-engine no-Google burst |
| `dev/search_pipeline/scholar_http_probe.py` | Probe pattern promoted to production in this change (kept as historical artifact) |
