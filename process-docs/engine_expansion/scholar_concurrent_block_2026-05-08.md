# Scholar Concurrent Block — Policy As-Is + Investigation Summary

Date: 2026-05-08

---

## Symptom

As of 2026-05-08, Google Scholar returned 0 results on every query when fired as part of the default 10-engine concurrent set. The query log recorded `status: EMPTY_BLOCK` on every burst-opener (first query of a session where the rate-limiter has tokens), followed by `RATE_SKIP` cascade on subsequent queries in the same process (Scholar's backoff timer exceeds `RATE_WAIT_TIMEOUT=5.0s`). Measured in `src/logs/query_log.jsonl`: 3/3 effective Scholar attempts = `EMPTY_BLOCK`, 9/9 cascade = `RATE_SKIP`. Net: Scholar contributed 0 URLs to every result set observed in this session.

---

## Root Cause

Two independent anti-bot triggers can cause Scholar EMPTY_BLOCK. They are stacked in production; both must be eliminated for Scholar to function reliably.

**(a) Concurrent Chrome tab burst — Scholar's own tab.** Scholar's pydoll browser tab opens inside a Chrome instance that is simultaneously rendering tabs for other concurrent browser engines (DDG, Mojeek, Lobsters, Semantic Scholar, and optionally Google). Google's infrastructure detects the concurrent-tab origin on `scholar.google.com` and issues a reCAPTCHA Enterprise challenge before serving the search page. HTTP Scholar opens no browser tab and therefore does not emit this signal — HTTP Scholar fires alongside 4 concurrent browser-engine tabs (DDG, Mojeek, Lobsters, Semantic Scholar) with 0% block rate (12/12 OK, row 4 of Evidence Table). **HTTP migration eliminates trigger (a).**

**(b) Google-domain co-fire — Google browser + Scholar HTTP from same IP.** When `google.com` (browser) and `scholar.google.com` (HTTP) are accessed concurrently from the same IP, Google's infrastructure issues a block even though Scholar makes no browser request of its own. Evidence: Phase B Full Smoke (discarded branch) ran HTTP Scholar with 10 engines including Google browser → 2/2 EMPTY_BLOCK. Same HTTP Scholar without Google (row 4) → 0/12 block. The causal delta is Google's browser tab running concurrently with the Scholar HTTP request. **HTTP migration does NOT eliminate trigger (b).** Eliminating trigger (b) requires Google-decoupling: Scholar must not fire in the same `asyncio.gather` call as Google browser engine.

Evidence ruling out other hypotheses:

- **Not fingerprint:** bot.sannysoft.com probe (commit `c2b2d73`, `dev/search_pipeline/01_reports/pydoll_stealth_phase_a_20260508.md`) showed all 57 detection checks passing. Fingerprint is identical between isolated (0% block) and concurrent (100% block) browser Scholar. Cannot explain the difference.
- **Not behavioral scoring:** browser Scholar receives `/sorry/` during `go_to()` at 1.7–2.0s, before any Scholar page content loads or user interaction is simulated. Timing rules out any analysis of page-interaction behavior.
- **Google-domain co-fire is architecture-dependent:** for browser Scholar, Google's presence is not the primary trigger — no-Google browser smoke (12/12 EMPTY_BLOCK, row 3) shows trigger (a) is sufficient to cause block without Google present. For HTTP Scholar, Google's presence is the remaining trigger — HTTP Scholar without Google = 0/12 block (row 4); HTTP Scholar with Google = 2/2 block (row 5).

**Mechanistic path (browser Scholar):** `asyncio.gather` fires 9–10 coroutines. Browser engines each open a pydoll tab. Scholar's tab opens in a Chrome instance already rendering other tabs. Google detects concurrent-tab origin on `scholar.google.com` → `/sorry/` redirect before page load. **Mechanistic path (HTTP Scholar + Google browser):** `asyncio.gather` fires HTTP Scholar (`httpx.AsyncClient` GET, no tab) concurrently with Google browser tab loading `google.com`. Google's IP-level scoring detects simultaneous access to both `google.com` and `scholar.google.com` from the same IP → `/sorry/` on Scholar HTTP response.

---

## Evidence Table

| Test | Engines | Scholar arch | Google? | Scholar BLOCK | Effective N | Avg search_ms | Reference |
|---|---|---|---|---|---|---|---|
| Production baseline | 10 | BROWSER | Yes | **100% (3/3)** | 3 (rest RATE_SKIP cascade) | 1910 | concurrent_block report, discarded branch commit `9feaab6` |
| HTTP isolation (Phase B, discarded) | 3 | HTTP | No | **0% (0/4)** | 4 | ~1800 | Phase B branch discarded; 0 other browser tabs |
| no-Google browser smoke (this session, pre-redirect) | 9 | BROWSER | No | **100% (12/12)** | 12 | 1850 | main `src/logs/query_log.jsonl` lines 55–66 |
| **no-Google HTTP probe smoke (this session)** | 9 | HTTP | No | **0% (0/12)** | 12 | 724 | `dev/search_pipeline/01_reports/no_google_burst_20260508_220631.jsonl` |
| Phase B Full Smoke (HTTP+Google, discarded) | 10 | HTTP | Yes | **100% (2/2)** | 2 | ~1900 | Phase B branch discarded; N=2, inline-summarized |

**Architecture × Google presence — 2×2 matrix:**

| | Google absent | Google present |
|---|---|---|
| **HTTP Scholar** | **0%** (rows 2, 4 — triggers a+b both absent) | **100%** (row 5 — trigger b active) |
| **Browser Scholar** | **100%** (row 3 — trigger a sufficient) | **100%** (row 1 — triggers a+b both active) |

Reading: HTTP migration eliminates trigger (a) only. Google-decoupling eliminates trigger (b). Production-functional Scholar requires both.

---

## Policy As-Of 2026-05-08

**Two sequential steps are required. Neither alone restores Scholar in production default queries.**

**Step 1 — HTTP migration (eliminates trigger a):** Promote `dev/search_pipeline/scholar_http_probe.py` pattern to `src/search/engines/scholar.py`. Replaces pydoll browser tab with `httpx.AsyncClient` GET. Validated: 0/12 block in no-Google concurrent burst (row 4).

**Step 2 — Google-decoupling (eliminates trigger b):** Prevent Scholar from firing in the same `asyncio.gather` call as the Google browser engine. Required because all default production engine sets (`--academic`, `--pdf`, `--books`, `--docs`, and the bare default) include `google`. HTTP migration alone leaves Scholar blocked in every production default query path. Implementation options documented in Open Items below.

**Step 1 without Step 2:** Scholar fires concurrently with Google browser → trigger (b) active → EMPTY_BLOCK. Scholar remains non-functional in all default production paths.

**Step 2 without Step 1:** Browser Scholar decoupled from Google → trigger (b) eliminated, trigger (a) still active (Scholar's own browser tab in concurrent burst) → EMPTY_BLOCK persists. Still non-functional.

As of 2026-05-08, `src/search/engines/scholar.py` was browser-based (pydoll). Neither step was implemented yet. Scholar was non-functional in all query paths tested this session.

**HTTP probe performance note:** HTTP Scholar (row 4) averages 724ms search_ms vs browser Scholar isolation baseline ~1900ms — 2.5× faster. Migration eliminates a Chrome tab from the concurrent burst AND improves latency.

**Cascade note on row 3:** `search_web` CLI calls are separate processes; Chrome-warm + 9-engine gather + preview overhead ≥15s per call ≥ Scholar's 15s token replenishment interval → no RATE_SKIP cascade → 12 effective attempts. Original production smoke (`search_batch`) fires queries back-to-back within one process; inter-query gap ≤15s triggers cascade → only 3 effective burst-openers. Denominator differs; block-rate finding (100% vs 0%) is architecture-driven, not cascade-driven.

---

## Discarded Approaches

| Approach | Reason discarded |
|---|---|
| Sequential Scholar after gather (option from original mitigation recommendation) | Architecturally correct for trigger (b) but unnecessary given that HTTP migration + Google-decoupling together deliver 0% block at lower complexity. Revisit only if HTTP Scholar develops problems requiring a sequential fallback. |
| Stagger tab opening (200–500ms inter-engine delays) | Adds global latency tunable, slows all browser engines; doesn't address IP-level concurrent scoring. User declined. |
| Patchright migration | Patches `Runtime.enable` CDP leak — not relevant to concurrent Chrome-tab or Google-co-fire triggers. Both triggers active regardless of CDP implementation. |
| PoW auto-solve on `/sorry/` | Fragile, maintains BLOCK as an expected code path. Superseded by HTTP architecture which avoids trigger (a) entirely. |
| Residential proxy (paid) | Out of scope (free-fix-path constraint). |

**Note on "Remove Google from engine set" policy:** NOT discarded for HTTP Scholar. For browser Scholar it was empirically falsified (row 3: browser Scholar blocks even without Google, trigger (a) sufficient). For HTTP Scholar, removing Google IS what produces 0% block (row 4 vs row 5). Google-decoupling is Step 2 of the production fix — see Open Items #1 + #2.

---

## Open Items

### 1. Promote scholar_http_probe.py → src/search/engines/scholar.py (Step 1 of 2)

**Prerequisite for Step 2. Promotion alone does NOT restore Scholar in production default queries** — all default engine sets (`--academic`, `--pdf`, `--books`, `--docs`, bare default) include `google`. After Step 1, trigger (b) (Google co-fire) remains active → Scholar still blocks on every default production query. Step 2 is required to complete the fix.

Promotion steps:
- Replace `src/search/engines/scholar.py` with probe pattern from `dev/search_pipeline/scholar_http_probe.py`
- Rename class → `ScholarEngine`, restore `name = "google_scholar"` (ENGINES dict key)
- Remove probe-local `RateLimiter` constructor; production scholar uses `get_limiter(self.name)` for backoff (acquire handled by `_engine_with_timing`)
- Add `"google_scholar": 6.0` to `ENGINE_WATCHDOG_OVERRIDE` in `search_web.py` (was in commit `82bc88f`, add if not present)
- Update `src/search/DOCS.md` scholar entry: `browser → HTTP`
- Smoke verify with `dev/search_pipeline/08_scholar_smoke.py` (isolated Scholar) + `dev/search_pipeline/no_google_burst_smoke.py` (concurrent no-Google burst)

Contained, scoped — `dev/` probe exists.

### 2. Google-decoupling implementation (Step 2 of 2)

Prevent Scholar from firing in the same `asyncio.gather` as the Google browser engine. Required because all production default engine sets include `google`. Implementation options:

| Option | Description | Wallclock cost | Trade-off |
|---|---|---|---|
| (a) Sequential after gather | When `google` in selected set, fire Scholar in a post-gather sequential step | +700ms unconditional | Reliable. Adds visible latency to every academic-with-google query. |
| (b) Mutual-exclusion in `_select_engines` | Drop Scholar from selected set when `google` is present | 0ms | Scholar loses output in all default queries (status quo Scholar effectively non-functional, so net zero coverage delta). Simplest code. |
| (c) Mode-specific engine sets | Define mutually-exclusive sets — `--academic` excludes Scholar (Google in); explicit `--scholar` flag excludes Google (Scholar in) | 0ms | Breaking UX change. Cleanest by-design separation — Google and Scholar never co-occur in any query. |
| (d) Conditional pre-acquire delay | Scholar's task awaits `asyncio.sleep(N)` (default 1.5s) before acquire when `google` is in selected set; still inside the gather but temporally offset | 0ms IF delay fits in slowest-engine wallclock window | Empirically untested whether 1.5s suffices to escape Google's co-fire detection. With 5–6s timeout engines (open_library, semantic_scholar, crossref) absorbing the delay, no visible cost. May need tuning up if 1.5s insufficient. |

**No recommendation — decision deferred to the implementation session.** Two candidate paths sit awkwardly:

- **(d) Pre-acquire delay** is the only candidate that satisfies the project's Mitigation-Choice Discipline Rang-1 tier (absorbed in existing wallclock). Trade-off: hypothesis-driven — 1.5s might not be enough to escape Google's co-fire detection. If smoke fails, tune delay up to slowest-engine ceiling (~6s); above that, wallclock becomes visible and the option degrades to Rang-2.
- **(c) Mode-specific engine sets** is the architecturally cleanest — by-design mutual exclusion, no runtime conditional logic, no timing hypothesis. UX cost: user opts into Scholar via explicit flag. Coverage cost on default `--academic` (no Scholar there) is recoverable via the new flag.

Both are awkward differently: (d) is hacky timing-based with empirical unknowns, (c) is a UX break. The decision is whether to:
1. Try (d) empirically first (cheap to test — adapt `dev/search_pipeline/no_google_burst_smoke.py` to include `google` + pre-delayed Scholar, measure block rate)
2. Commit to (c) up-front and design the new `--scholar` flag

Option (a) downgraded to fallback for if (d) fails empirically. Option (b) downgraded to "current production state by explicit code path" — only acceptable if (c) is rejected as too disruptive.

### 3. `--pdf` mode Scholar re-evaluation

`_PDF_ENGINES` in `search_web.py` includes `google_scholar` (Scholar surfaces arxiv.org/abs/ links → TIER1 transform → PDF download). `_PDF_ENGINES` also includes `google`. After Step 1 + Step 2 (HTTP promotion + Google-decoupling), Scholar in `--pdf` mode will run sequentially post-gather while Google runs concurrently. Verify with `dev/search_pipeline/no_google_burst_smoke.py` adapted for a PDF-flavored query set post-promotion.

### 4. Empirical re-validation cadence

HTTP Scholar's 0% block rate was measured at 12 queries in one session from a home/residential IP. Quarterly re-validation via `./venv/bin/python dev/search_pipeline/no_google_burst_smoke.py` (or subset of 4 queries). If block rate rises above 0% post-promotion, fall back to sequential-after-gather option from the discarded approaches table above.

---

## Files Touched This Session (scholar-no-google-test branch)

| File | Change |
|---|---|
| `dev/search_pipeline/scholar_http_probe.py` | New — HTTP Scholar probe class (cherry-picked from commit `82bc88f`, adapted for dev/) |
| `dev/search_pipeline/no_google_burst_smoke.py` | New — 9-engine no-Google burst smoke script (drives HTTP probe + 8 production engines) |
| `dev/search_pipeline/01_reports/no_google_burst_20260508_220631.jsonl` | New — smoke run output (12 queries, all `scholar_http=OK`) |

Browser smoke data (no-Google, 12-query, all EMPTY_BLOCK): written to main repo `src/logs/query_log.jsonl` lines 55–66 — no file committed here (main repo's log, not worktree artifact).
