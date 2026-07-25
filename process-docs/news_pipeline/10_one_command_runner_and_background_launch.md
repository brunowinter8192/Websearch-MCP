# Iter 10 — One-Command Runner & Background Browser Launch

**Date:** 2026-06-07
**State:** BUILT + STAGE-01 SMOKE-TESTED. Awaiting user two-run validation (Run 1 indexes everything, Run 2 finds nothing new).

---

## One-Command Orchestrator — run_pipeline.py

Single entry point: `./venv/bin/python dev/news_pipeline/run_pipeline.py`

**Stage chain:**
1. Precondition checks (abort early on failure)
2. Stage 01 — discover (48h window)
3. Stage 04 — dedup gate
4. If 0 new: log + write last-run marker + exit
5. Stage 02b — scrape (only new URLs)
6. If 0 ok scrapes: log + write last-run marker + exit
7. Stage 03 — cleanup
8. Stage 05 — publish (copy + index)
9. Log final summary + write last-run marker

**Precondition checks:**
- (a) Internet reachable: `urllib.request.urlopen("https://www.coindesk.com", timeout=10)` — fails loudly with logged error if coindesk.com unreachable.
- (b) `rag-cli list_collections` exits 0 — confirms rag-cli is on PATH and the RAG server is callable.

**Intermediate dir clearing:** `02b_output/*.md`, `02b_output/manifest.json`, `03_output/*.md`, `03_output/manifest.json` deleted at start of each run. Guarantees publish indexes only current-run articles (without clearing, stale files from a prior run would be re-indexed by 05_publish).

**Logging:**
- Per-run file: `src/logs/coindesk_pipeline_YYYYMMDD.log` (created by orchestrator, `LOG_DIR.mkdir(parents=True, exist_ok=True)`).
- Last-run marker: `src/logs/coindesk_pipeline_last_run.txt` — single-line UTC timestamp. Written on clean exit (including "0 new" early-exit). A missing or stale marker means the pipeline died silently mid-run.
- Per-stage stdout/stderr captured and forwarded to the log file.

**Stage output parsing:** orchestrator extracts counts from stage stdout via regex — no shared state, no imports across stage scripts. Each script remains independently runnable.

---

## Background Browser Launch — [VERIFIED via `man open` + pydoll source]

Applies to **Stage 01 (01_coindesk_discover.py, pydoll)** only. See below for why 02b is exempt.

### Mechanism

```
open -gna "Google Chrome" --args \
  --remote-debugging-port=<PORT> \
  --user-data-dir=<FRESH_TEMPDIR> \
  --user-agent=<UA> \
  --window-size=1920,1080 \
  --disable-blink-features=AutomationControlled \
  --no-first-run \
  --no-default-browser-check
```

Poll `http://localhost:<PORT>/json/version` every 0.5s (30s timeout) → `data["webSocketDebuggerUrl"]`.

```python
chrome = Chrome()          # pydoll, no process spawned
tab = await chrome.connect(ws_url)   # connects to running instance, returns tabs[0]
```

**Cleanup:**
```python
await chrome.close()       # closes WS connection only (pydoll didn't spawn the process)
subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"], check=False)
shutil.rmtree(session_dir, ignore_errors=True)
```

`chrome.stop()` is NOT used — it calls `_browser_process_manager.stop_process()` which would raise `BrowserNotRunning` since pydoll didn't launch this Chrome. `chrome.close()` closes only the WebSocket.

**Port allocation:** `socket.bind(("127.0.0.1", 0))` → OS-assigned free port. Avoids conflicts between concurrent or sequential runs.

### Why `-gna`, not `-ga`

`man open` flags:
- `-g` — do not bring the application to the foreground (no focus steal)
- `-n` — open a new instance even if one is already running
- `-a <app>` — open with the specified application

**`-n` is critical.** Without it: `open -ga "Google Chrome" --args ...` activates the user's already-running Chrome instance and passes no `--args` to it (the existing process ignores the flags). The remote-debugging-port never comes up → `wait_for_ws_url` times out at 30s.

With `-gna`: macOS spawns a NEW Chrome process with the given args, using the fresh `--user-data-dir` as its profile (isolated from the user's normal Chrome). The window exists but stays in the background.

**Verified:** smoke test on 2026-06-07 with user's Chrome already running — port 58635 came up, ws_url resolved, `Chrome().connect()` returned a Tab, navigation + JS extraction succeeded.

---

## Key Finding: 02b Is crawl4ai (Playwright), NOT pydoll

When this task was designed, 02b was assumed to be pydoll-based and was listed as requiring the open-gna + connect treatment. On reading the source:

```python
# 02b_coindesk_scrape_fresh_context.py
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
browser_config = BrowserConfig(headless=True, verbose=False, user_agent=USER_AGENT)
# ...
async with AsyncWebCrawler(config=browser_config) as crawler:
    ...
```

Crawl4ai uses Playwright, not pydoll. `headless=True` = no visible window = no focus stealing. No `open -gna` treatment needed or applied.

**The per-URL isolation is already correct:** `AsyncWebCrawler` is instantiated fresh for each URL inside the loop — new Playwright browser process + clean BrowserContext per URL. This is what defeats the CoinDesk regwall (confirmed in iter 3: 23/25 real bodies, 0 regwall hits).

**Implication confirmed here:** headless mode is NOT the regwall-defeating mechanism. Fresh cookie jar (clean context) is. A shared crawl4ai session in headless mode still hits the regwall (iter 1 result: 21/25 regwall'd). Only 02b (fresh context per URL) beats it, regardless of headless setting.

Result: **only Stage 01 (pydoll) required background-launch changes. Stage 02b untouched.**

---

## 48h Discover Window

**Termination condition change:**
- Previously: `PRE_TODAY_THRESHOLD = 3`, terminates when ≥3 articles have `url_date < today` (~24h coverage).
- Now: `PRE_48H_THRESHOLD = 3`, `CUTOFF_DAYS = 2`. `cutoff = today - timedelta(days=1)` (= yesterday). Terminates when ≥3 articles have `url_date < cutoff` (= articles 2+ days old).

**Coverage guarantee:** stopping when we've seen day-before-yesterday articles means we've fully traversed today's AND yesterday's feed. Articles published 0–47h ago are all collected.

`MAX_CLICK_ROUNDS = 8` safety cap unchanged — 8 × ~16 URLs ≈ 128 URLs, more than enough for a 48h window.

---

## Storage & Dedup & Publish

**Collection:** `searxng_crypto`
**Collection dir:** `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/searxng_crypto/`
**Filename scheme:** `coindesk__<YYYY-MM-DD>__<sha256(url)[:12]>.md` — pubdate from URL path `/YYYY/MM/DD/`, hash from URL.

**Dedup (04_dedup.py):**
- Pure Python, no browser, no network.
- For each discover entry: construct `collection_dir / f"coindesk__{pubdate}__{hash}.md"` and check `Path.exists()`.
- Filesystem presence IS the seen-state — no separate state file. Rationale: single source of truth, reproducible from cold start, no drift risk (decision confirmed in the prior iteration, collection path updated here to `searxng_crypto`).

**Publish (05_publish.py):**
- Reads `03_output/manifest.json` — has `hash`, `url`, `publication_date` per entry.
- `pubdate = publication_date[:10]`, `h = entry["hash"]` (already `sha256(url)[:12]`).
- `shutil.copy2(src, dest)` — safe to re-run.
- `subprocess.run(["rag-cli", "index", "--collection", "searxng_crypto"])` — rag-cli's hash-skip handles re-index of already-indexed files.
- Parses `Done: N files indexed (M chunks)` from rag-cli stdout.

---

## Smoke Test Result — Stage 01 Background Launch [2026-06-07]

```
[smoke] Launching background Chrome on port 58635 …
[smoke] ws_url: ws://localhost:58635/devtools/browser/44dc4ef6-62ae-445b-8887-ce345e09cc73
[smoke] Connected. Tab type: Tab
[smoke] Navigating to https://www.coindesk.com/latest-crypto-news …
[smoke] Extracted 16 articles
  https://www.coindesk.com/business/2026/06/06/michael-saylor-...
  https://www.coindesk.com/markets/2026/06/07/bitcoin-near-...
[smoke] Cleaned up port 58635
[smoke] PASS — 16 articles extracted, background Chrome mechanism works.
```

User's Chrome was running during the test. `-n` flag caused a new isolated instance to start. No focus steal observed.

---

## Status & Next Step

**Built:** `01_coindesk_discover.py` (modified), `04_dedup.py`, `05_publish.py`, `run_pipeline.py` (all new). `DOCS.md` updated. `.gitignore` extended with `02b_output/`, `03_output/`, `04_output/`.

**Validation outstanding (user-run):** two sequential full-pipeline runs.
- Run 1: discover N articles → dedup finds M new → scrape + clean + index M articles → `searxng_crypto` gets M new files.
- Run 2: discover same N articles → dedup finds 0 new (all M files now exist) → pipeline exits at "nothing new" log line.
- If both match expectations → pipeline is production-ready. RAG queries on `searxng_crypto` then verify content quality.
