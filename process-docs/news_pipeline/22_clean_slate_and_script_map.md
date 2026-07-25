# 22 — Proxy Exploration: Clean Slate + Script Map

**Date:** 2026-06-12
**State:** All measurement OUTPUTS from the proxy exploration (the prior 8 entries covering theblock discovery through pipe/cycle economics) wiped. Scripts kept. No current measurements exist — measurement restarts from zero with explicit provenance.

## Why a clean slate

The exploration accumulated measurement artifacts whose numbers got quoted across contexts without tracking which run / which scope produced them. Concrete failure: three different "monosans CF" figures were treated as comparable when they are not:

| Figure | What it actually was | Scope |
|---|---|---|
| ~11% | extrapolated CF-rate for the NON-MuRongPIG remainder (4 passers / ~35 non-MuRongPIG alive) | estimate, small-n, prior pipe/cycle-economics entry |
| 0.8% | measured CF-pass rate of the WHOLE 5k sample (MuRongPIG-diluted) | pipe run, prior pipe/cycle-economics entry |
| 0 | `cf_passed=0` for monosans in the scoreboard | monosans contributed ~0 proxies to the 5k sample → never CF-tested, not "failed" |

None of the three is a clean "monosans CF-pass rate". Mixing them is the data-provenance problem. The fix is to delete the muddled outputs and re-measure with each number tied to (script, run, scope).

The SCRIPTS are sound and stay. Only their generated OUTPUTS are wiped.

## Deleted (git rm, recoverable via history)

| File | Producer |
|---|---|
| `source_scoreboard.json` / `.md` | source_tracker.py |
| `freshness_log.md` | source_tracker.py |
| `pipe_log.md` | pipe_theblock.py |
| `discover_coverage_report.md` | probe_discovery.py |
| `probe_liveness_logs/sweep_log.md` | probe_liveness.py |
| `cache/bulk_sitemap_run3.json`, `cache/news_sitemap.json` | probe_discovery.py |

Gitignored ephemeral dirs (`frozen_pool/`, `source_snapshots/`, `*_reports/`, `monosans_out_*/`) were already absent on disk.

## Kept

7 scripts + 2 configs (`monosans_cfg_neutral.toml`, `monosans_cfg_theblock.toml`). Nothing in `src/` is touched by any of this — the proxy work lives entirely in `dev/news_pipeline/theblock/`.

## Go-forward scope: monosans first, expand later

**Decision (2026-06-12):** start with ONE source repo only — `monosans/proxy-list` — and add more lists later, once we have reliable, trustworthy data from this single source.

Why monosans first:
- Cleanest data form. `proxies.json` gives `protocol / host / port` (+ `username` / `password`) as explicit structured fields — no text-format parsing, no protocol-guessing.
- Pre-validated. The `timeout` field means liveness is already measured on monosans' server; these are currently-working proxies, not a raw dump.
- No format acrobatics in the current data: all 103 lines are `scheme://host:port`, zero auth, zero IPv6, zero trailing fields.

Consumption rule: read monosans via the JSON and **keep the protocol**. Do NOT route it through the current `parse_proxy_line()` (probe_pool_size.py), which strips the scheme and discards the protocol — wrong for a protocol-tagged source.

Expansion comes only after monosans gives solid numbers. The broader source set (ErcinDedeoglu, mzyui, TheSpeedX, dpangestuw, r00tee, proxyscrape, ALIILAPRO, iplocate — historically the CF-yielders) is parked until then. Source-count is deliberately 1 to remove pool-composition / dilution as a variable while we re-establish trustworthy measurement.

## Prior exploration entries status

Kept as process history. **Every measured number in the prior entries is HISTORICAL, not current state.** Post-clean-slate there are no current measurements. Treat those entries as the record of how the landscape was explored, not as a source of live figures.

## Script Map (`dev/news_pipeline/theblock/`)

All descriptions taken from the scripts' own headers/code, not from prior DOCS.

| Script | LOC | Contacts proxies? | Standalone? | Output |
|---|---|---|---|---|
| `probe_pool_size.py` | 335 | no (fetch lists only) | yes | `probe_pool_size_reports/` (gitignored) |
| `probe_liveness.py` | 362 | yes (liveness) | yes (CLI) | `probe_liveness_logs/sweep_log.md` |
| `probe_discovery.py` | 457 | no (home IP, curl) | yes | `discover_coverage_report.md` + `cache/` |
| `probe_curl_cffi_discriminator.py` | 261 | yes (CF test) | yes | `*_discriminator_reports/` (gitignored) |
| `probe_monosans.sh` | 82 | yes (via tool) | yes (arg) | `monosans_out_*/` (gitignored) |
| `pipe_theblock.py` | 339 | yes (full pipe) | yes | `pipe_log.md` + `cache/` |
| `source_tracker.py` | 283 | no (helper) | NO — called by pipe | scoreboard + freshness |

### probe_pool_size.py
Fetches the 68 hardcoded source URLs (`HTTP_SOURCES` / `SOCKS4_SOURCES` / `SOCKS5_SOURCES`), parses each line to `host:port`, counts raw + global-unique. No proxy is contacted. **The 68 source URLs live HERE — `probe_liveness.py` imports them.**

### probe_liveness.py
Async liveness checker + concurrency sweep. `--freeze` fetches the 68 sources (lists imported from `probe_pool_size.py`) into `frozen_pool/`. `--sample N` / `--full` check liveness via `curl_cffi.AsyncSession` against `icanhazip`, classifying every dead proxy into a reason bucket. Appends one structured entry per run to `sweep_log.md`.

### probe_discovery.py
Measures theblock.co discovery coverage **from our home IP** (subprocess `curl`, NO proxies). Fetches the full sitemap union, news sitemap, RSS, and a bounded UI crawl. Hits CF IP-block (429) after ~25 sequential fetches; per-sub backoff retry (60/120/180s). Resume-safe via per-sub JSON in `cache/`. Answers "what article URLs exist", not "which proxies work" — separate concern from the proxy machinery.

### probe_curl_cffi_discriminator.py
The a/b/c discriminator (from the passability-discriminator entry). Re-tests neutral-alive proxies with `curl_cffi impersonate=chrome` against a real theblock sitemap to decide whether the TLS signature (a), IP reputation (b), or pool staleness (c) was the blocker.

### probe_monosans.sh
Runs the `monosans/proxy-scraper-checker` TOOL (Docker image, pinned SHA) to produce a checked proxy pool under a neutral `check_url` vs a theblock.co `check_url`. Configs: `monosans_cfg_neutral.toml` / `monosans_cfg_theblock.toml`. This is the TOOL (scrapes + checks many upstream lists), distinct from the `monosans/proxy-list` text repo.

### pipe_theblock.py
The full pipe. Stage 1: fetch fresh 68-source pool, random 5k sample, neutral liveness @ concurrency 128. Stage 2: CF-pass check on neutral-alive via `curl_cffi impersonate=chrome`. Stage 3: sequential-exhaustion sitemap discovery — drain ONE proxy until 403/429 (records per-IP budget B), then rotate. Appends a funnel entry to `pipe_log.md`; calls `source_tracker.update_and_flush()` at the end.

### source_tracker.py
Per-source attribution + cumulative scoreboard + freshness diffs. **Not standalone** — invoked by `pipe_theblock.py` via `update_and_flush()`. Produces `source_scoreboard.json` (canonical state), `source_scoreboard.md` (rendered ranking), `freshness_log.md` (new/dropped per run), `source_snapshots/` (gitignored diff basis).
