# dev/search_pipeline/

## Role

Baseline-first stealth/search experimentation. Single active engine (Google) with a reproducible 30/30 headless pydoll stack, iterated via single-variable experiments against the 7 detection layers documented in `decisions/stealth00_engine_status.md`.

## Layout

| File | Purpose |
|------|---------|
| `config.yml` | Single source of truth for browser, stealth patches, Google selectors, consent cookie, run params, detection rules, report format |
| `queries.txt` | 30 baseline queries (Tech 8 + Science 6 + German 6 + Niche 5 + Broad 5) |
| `01_google_smoke.py` | Baseline 30-query smoke runner — reads config.yml, writes timestamped report to `01_reports/` |
| `00_single_query.py` | Single-query diagnostic harness — same config, runs one query with verbose output (use for fast iteration during layer experiments) |
| `01_reports/` | Per-run markdown reports from `01_google_smoke.py` |

## Baseline (current)

- **Result:** 30/30 OK — first verified 2026-04-21, run 1
- **Stack:** headless Chrome via pydoll, SOCS cookie injection per-tab, fingerprint patches for screen/DPR/outer/css, selectors `#rso h3` + `.MjjYud`, 0 delay between queries, ~2.5min total
- **Layer mapping:** see `decisions/stealth00_engine_status.md` for how the baseline addresses each detection layer

## Running

```bash
# Full smoke (30 queries)
rm -rf ~/.searxng-mcp/browser-session-smoke/Singleton* 2>/dev/null
./venv/bin/python3 dev/search_pipeline/01_google_smoke.py

# Single query diagnostic
./venv/bin/python3 dev/search_pipeline/00_single_query.py "your query here"
```

## Experiment Log

Each iteration after a stress-break adds a NEW numbered script (02_\<name\>.py, 03_\<name\>.py, ...) and a row in this table. Keep the baseline script untouched — it's the control. Experiment scripts may copy from the baseline and modify ONE variable (one detection layer's control setting) to isolate the effect.

| Date | Run-ID | Config | Hypothesis | Delta vs Baseline | Layer | Result X/30 | First Fail Idx | Nav ms (mean/max) | DOM ms (mean/max) | Report |
|------|--------|--------|-----------|-------------------|-------|-------------|----------------|-------------------|-------------------|--------|
| 2026-04-21 | baseline-run-1 | `config.yml` @ `a2cff3d` | Baseline established (SOCS + new selectors + parse_js fix) | — | — | 30/30 | — | — / — | — / — | `01_reports/smoke_20260421_022343.md` |
| 2026-04-21 | baseline-run-2 | `config.yml` @ `e0077dd` | Re-verify same config after refactor | — (same config) | — | 28/30 | 2× CAPTCHA | — / — | — / — | `01_reports/smoke_20260421_182917.md` |
| 2026-04-21 | baseline-run-3 | `config.yml` @ `80cff93` | First run with timing measurement — same baseline config | — (timing instrumentation only) | — | 28/30 | 2× CAPTCHA (Q24+Q25) | 551 / 816 | 1 / 4 | `01_reports/smoke_20260421_193051.md` |

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
