# dev/search_pipeline/

## Role

Baseline-first stealth/search experimentation. Active engines: Google (pydoll, 30/30 baseline) and DuckDuckGo (pydoll, html-endpoint). Iterated via single-variable experiments against the 7 detection layers documented in `decisions/stealth00_engine_status.md`.

## Layout

| File | Purpose |
|------|---------|
| `config.yml` | Single source of truth for browser, stealth patches, engine selectors + params (google + duckduckgo blocks), run params, detection rules, report format |
| `queries.txt` | 30 baseline queries (Tech 8 + Science 6 + German 6 + Niche 5 + Broad 5) |
| `01_google_smoke.py` | Baseline 30-query smoke runner (standalone pydoll, dev-side control reference) — reads config.yml, writes timestamped report `smoke_<ts>.md` to `01_reports/` |
| `02_burst_smoke.py` | Burst smoke against the production CLI — invokes `searxng-cli search_batch` per batch (one subprocess per N queries, warm Chrome amortized) and writes `burst_<ts>.md` to `01_reports/`. Exists to validate the prod CLI path under the architectural rate pattern (4 queries per burst, optional cooldown). CLI flags: `--queries-per-burst N` (default 4), `--cooldown S` (default 60), `--max-queries N` (default all from queries.txt). |
| `03_hn_smoke.py` | HN-Algolia smoke runner — direct `HNEngine().search()` call (pure HTTP, no browser), runs the 30 baseline queries, writes timestamped report `hn_smoke_<ts>.md` to `01_reports/`. Status taxonomy: OK / EMPTY / ERROR. Smoke result is content-bound — German queries always EMPTY (HN is English), niche-tech queries depend on `tags=story` filter (see search05). |
| `04_ddg_smoke.py` | DuckDuckGo smoke runner — standalone pydoll, reads config.yml `duckduckgo:` block, runs 30 baseline queries against `html.duckduckgo.com/html/` GET endpoint, writes `ddg_smoke_<ts>.md` to `01_reports/`. No consent handling, DOM-based CAPTCHA detection, URL cleaning from DDG redirect wrapper. Status taxonomy: OK / EMPTY / BLOCKED / CAPTCHA / SUSPECT / ERROR. |
| `05_search_smoke.py` | Multi-engine comparison smoke — imports `GoogleEngine` + `DuckDuckGoEngine` from `src/`, fans out per-engine in parallel via `asyncio.gather`, merges by URL preserving per-engine snippets, fetches previews via `src/search/preview.py`, writes `search_smoke_<ts>.md` to `01_reports/`. CLI flags: `--engines google duckduckgo` (default), `--max-queries N`. |
| `06_mojeek_smoke.py` | Mojeek standalone smoke runner — reads config.yml `mojeek:` block, runs 30 baseline queries against `mojeek.com/search`, writes `mojeek_smoke_<ts>.md` to `01_reports/`. No consent, no CAPTCHA check, no URL cleaning. Status taxonomy: OK / EMPTY / BLOCKED / SUSPECT / ERROR. |
| `07_lobsters_smoke.py` | Lobsters standalone smoke runner — reads config.yml `lobsters:` block, runs 30 baseline queries against `lobste.rs/search`, writes `lobsters_smoke_<ts>.md` to `01_reports/`. No consent, no CAPTCHA check, no URL cleaning. Snippet = domain-as-displayed (link-aggregator pattern). Status taxonomy: OK / EMPTY / BLOCKED / SUSPECT / ERROR. |
| `00_single_query.py` | Single-query diagnostic harness — same config as 01, runs one query with verbose output (use for fast iteration during layer experiments) |
| `_capture_sorry.py` | Standalone helper to navigate Google, detect `/sorry/` redirect, save PNG + HTML + metadata to `01_reports/sorry_<ts>.*` (artifacts gitignored, contain public IP) |
| `01_reports/` | Per-run markdown reports — `smoke_*.md` from 01, `burst_*.md` from 02, `ddg_smoke_*.md` from 04, sorry captures gitignored |

## Baseline (current)

### Google

- **Result:** 30/30 OK — first verified 2026-04-21, run 1
- **Stack:** headless Chrome via pydoll, SOCS cookie injection per-tab, fingerprint patches for screen/DPR/outer/css, selectors `#rso h3` + `.MjjYud`, 0 delay between queries, ~2.5min total
- **Layer mapping:** see `decisions/stealth00_engine_status.md` for how the baseline addresses each detection layer

### DuckDuckGo

- **Result:** 30/30 OK — first verified 2026-05-03, run 1 — `01_reports/ddg_smoke_20260503_174043.md`
- **Stack:** headless Chrome via pydoll, fingerprint patches (screen/DPR/outer/css), no consent cookie, GET `html.duckduckgo.com/html/?q={}&kl=wt-wt`, 0 delay, ~40s total
- **Nav timing:** mean 1333ms / max 3070ms — DOM-wait 0ms (server-rendered HTML, results present without poll cycle)

## Running

```bash
# Google standalone control (30 queries, dev pydoll, ~2.5 min)
rm -rf ~/.searxng-mcp/browser-session-smoke/Singleton* 2>/dev/null
./venv/bin/python3 dev/search_pipeline/01_google_smoke.py

# DuckDuckGo standalone smoke (30 queries, dev pydoll, ~40s)
./venv/bin/python3 dev/search_pipeline/04_ddg_smoke.py

# Burst against prod CLI (30 queries in 4-per-burst, no cooldown, ~1.7 min)
./venv/bin/python3 dev/search_pipeline/02_burst_smoke.py --queries-per-burst 4 --cooldown 0

# Burst with steady-state rate cap (30 queries, 4-per-burst, 60s cooldown between, ~9 min)
./venv/bin/python3 dev/search_pipeline/02_burst_smoke.py --queries-per-burst 4 --cooldown 60

# Mojeek standalone smoke (30 queries, dev pydoll, ~40s)
./venv/bin/python3 dev/search_pipeline/06_mojeek_smoke.py

# Lobsters standalone smoke (30 queries, dev pydoll, link-aggregator index)
./venv/bin/python3 dev/search_pipeline/07_lobsters_smoke.py

# Multi-engine comparison smoke (30 queries × google + duckduckgo, ~8 min)
./venv/bin/python3 dev/search_pipeline/05_search_smoke.py --engines google duckduckgo

# Multi-engine smoke with query limit for quick validation
./venv/bin/python3 dev/search_pipeline/05_search_smoke.py --engines google duckduckgo --max-queries 5

# Single query diagnostic
./venv/bin/python3 dev/search_pipeline/00_single_query.py "your query here"
```

### Mojeek

- **Result:** 7/30 OK (stress baseline, 0-delay) — first run 2026-05-03, `01_reports/mojeek_smoke_20260503_193022.md`
- **Stack:** headless Chrome via pydoll, fingerprint patches (screen/DPR/outer/css), no consent cookie, GET `mojeek.com/search?q={}&safe=1`, 0 delay
- **Selectors:** `ul.results-standard > li > a.ob` (container), `li h2 a` (title), `li p.s` (snippet) — verified live 2026-05-03
- **Rate-limit break:** 403 at query 10 (~9 queries in 7.5s = ~1.2 req/s burst). Production 4 req/min (1 per 15s) stays well within threshold.
- **Nav timing:** mean 286ms / max 1033ms (queries 1-9 before 403 block)

### Lobsters

- **Result:** 16/30 OK (stress baseline, 0-delay) — first run 2026-05-03, `01_reports/lobsters_smoke_20260503_224702.md`
- **Stack:** headless Chrome via pydoll, fingerprint patches (screen/DPR/outer/css), no consent cookie, GET `lobste.rs/search?q={}&what=stories&order=relevance`, 0 delay
- **Selectors:** `li.story` (container), `a.u-url` (title + href), `a.domain` (snippet as domain-as-displayed) — verified live 2026-05-03
- **Nav timing:** mean 488ms / max 1639ms; DOM-wait mean 477ms / max 613ms
- **Notes:** Link-aggregator — smaller index; German + off-topic queries EMPTY (expected). No rate-limit block observed. Snippet = domain only by design.

### 05 — Multi-engine comparison

- **Script:** `05_search_smoke.py` — imports from `src/` (not standalone), uses production engine instances
- **Design:** per-engine fanout avoids `search_web_workflow` merge so per-engine snippets are preserved for comparison
- **Preview:** calls `src/search/preview.py fetch_previews()` per query on the URL union — adds og/meta block per URL
- **Report:** `01_reports/search_smoke_<ts>.md` — per-query section with engine-set badges, per-engine snippets, preview block

## Experiment Log

Each iteration after a stress-break adds a NEW numbered script (02_\<name\>.py, 03_\<name\>.py, ...) and a row in this table. Keep the baseline script untouched — it's the control. Experiment scripts may copy from the baseline and modify ONE variable (one detection layer's control setting) to isolate the effect.

| Date | Run-ID | Config | Hypothesis | Delta vs Baseline | Layer | Result X/30 | First Fail Idx | Nav ms (mean/max) | DOM ms (mean/max) | Report |
|------|--------|--------|-----------|-------------------|-------|-------------|----------------|-------------------|-------------------|--------|
| 2026-04-21 | baseline-run-1 | `config.yml` @ `a2cff3d` | Baseline established (SOCS + new selectors + parse_js fix) | — | — | 30/30 | — | — / — | — / — | `01_reports/smoke_20260421_022343.md` |
| 2026-04-21 | baseline-run-2 | `config.yml` @ `e0077dd` | Re-verify same config after refactor | — (same config) | — | 28/30 | 2× CAPTCHA | — / — | — / — | `01_reports/smoke_20260421_182917.md` |
| 2026-04-21 | baseline-run-3 | `config.yml` @ `80cff93` | First run with timing measurement — same baseline config | — (timing instrumentation only) | — | 28/30 | 2× CAPTCHA (Q24+Q25) | 551 / 816 | 1 / 4 | `01_reports/smoke_20260421_193051.md` |
| 2026-04-22 | stress-run-1 | `config.yml` @ `f63b688` | Back-to-back stress without cooldown provokes rate-limit break | — (same config, run 1 of batch) | 5 (rate-limit) | 30/30 | — | 520 / 887 | 2 / 3 | `01_reports/smoke_20260422_012435.md` |
| 2026-04-22 | stress-run-2 | `config.yml` @ `f63b688` | Back-to-back stress without cooldown provokes rate-limit break | — (same config, run 2 of batch) | 5 (rate-limit) | 27/30 | 3× CAPTCHA (Q26) | 422 / 701 | 2 / 5 | `01_reports/smoke_20260422_012456.md` |
| 2026-04-22 | stress-run-3 | `config.yml` @ `f63b688` | Back-to-back stress without cooldown provokes rate-limit break | — (same config, run 3 of batch) | 5 (rate-limit) | 28/30 | 2× CAPTCHA (Q11) | 345 / 664 | 3 / 9 | `01_reports/smoke_20260422_012516.md` |
| 2026-04-22 | stress-run-4 | `config.yml` @ `f63b688` | Back-to-back stress without cooldown provokes rate-limit break | — (same config, hard-break run) | 5 (rate-limit) | 0/30 | 30× CAPTCHA (Q1) | 537 / 661 | 0 / 0 | `01_reports/smoke_20260422_012539.md` |

Convention for new entries:
- **Run-ID:** `<hypothesis-slug>-run-N` (e.g. `webgl-run-1`)
- **Config:** git hash of config.yml at time of run
- **Hypothesis:** 1-line statement (e.g. "WebGL vendor override improves fingerprint score")
- **Delta:** concrete config/code diff vs baseline (e.g. `js_patches.webgl_vendor: Apple M1 Pro`)
- **Layer:** which stealth layer is being tested (1–7, see stealth00_engine_status.md)
- **Result X/30 + First Fail Idx:** from the report file
- **Nav/DOM ms:** from Timing Summary section of report
- **Report:** path to the run report

## Stress Test Methodology

Baseline proves a single clean 30/30 run. The actual stress-test is multiple back-to-back runs WITHOUT cooldown between runs — run until Google's rate-limit/CAPTCHA kicks in. That's the signal to start iterating on stealth layers.

## Conventions

- One script per experiment — never mutate the baseline script.
- Each experiment changes ONE variable (one layer's control). Multi-variable tests are NOT experiments — they're speculation.
- Report every run, even failures. Failure data IS the data.
- When a layer experiment succeeds: the SOLL section of the corresponding `decisions/stealthNN_*.md` gets updated with evidence.
