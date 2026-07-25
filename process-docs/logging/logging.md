# Python Logger Setup

*Snapshot as of 2026-06 — historical process record; the live current state is the source code, not this file.*

## Current State

`cli.py` installs a `FileHandler`-only logging config at startup, before any `src.*` imports:

```python
_log_path = Path(__file__).parent / "src" / "logs" / "cli.log"
_log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[logging.FileHandler(_log_path, mode="a", encoding="utf-8")],
)
```

- **Handler:** FileHandler only — `src/logs/cli.log`, append mode, UTF-8
- **Root logger level:** DEBUG (captures all named loggers regardless of their own level)
- **Format:** `%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s`
- **StreamHandler:** none installed — `basicConfig(handlers=[...])` with explicit handler list never adds the default StreamHandler
- **Gitignore:** `src/logs/` pattern in `.gitignore` covers `src/logs/cli.log`

**Call-site taxonomy enforced as of 2026-05-24 audit (`dev/logging_audit/01_reports/audit_20260523T233444Z.md`):**

| Category | Level | Examples |
|---|---|---|
| Per-engine-empty | DEBUG | "Engine X empty (%s) for: %s" — redundant with `query_log.jsonl` |
| Config state | INFO | "STACK_EXCHANGE_API_KEY not set — anonymous quota" |
| Mode-flag precedence | INFO | "Multiple mode flags set — pdf takes precedence" |
| CAPTCHA / block detection | WARNING | "Google CAPTCHA detected for: %s" |
| Rate-limited (HTTP 429) | WARNING | "CrossRef rate limited: %d" |
| Engine exception | ERROR | "DuckDuckGo search failed: %s" |
| I/O failure (log write) | WARNING | "scrape_log write failed: %s" |
| Genuine scrape failure | WARNING | "Failed to scrape %s: %s" |
| Per-URL verbose trace | DEBUG | fast-path hit, consent strip, chain resolution steps |

Standalone invocations (`python src/crawler/crawl_site.py`) call `logging.basicConfig(level=INFO, format="%(message)s")` inside their own `if __name__ == "__main__"` guard — unaffected by this config (fires in standalone mode only).

**Janitor (since 2026-05-24):** 14-day uniform retention, on-write trigger only, 1h marker throttle on slow-path. `SEARXNG_LOG_RETENTION_DAYS` env override (read at call time, not module load). `cli.log` uses `TimedRotatingFileHandler` (daily rotation, `backupCount=get_retention_days()`, stdlib auto-deletes older rotated files). Three JSONL surfaces (`query_log.jsonl`, `scrape_log.jsonl`, `download_log.jsonl`) use `maybe_prune_jsonl()` — ts-based filter, atomic rewrite via `.tmp + os.replace`. Sidecar dir (`scrape_content/`) uses `maybe_prune_sidecars()` — file-level mtime-based `unlink`. All failures logged as WARNING and swallowed — calling logger never receives an exception.

## Evidence

Symptom observed: `searxng-cli search_web "X"` produced warning lines before the breakdown table in tool_result (Claude Code Bash merges stdout+stderr):

```
STACK_EXCHANGE_API_KEY not set — anonymous quota (300 req/day)
Lobsters empty (EMPTY_NO_CONTAINER) for: X
```

Audit script: `dev/logging_audit/01_audit.py`
Report: `dev/logging_audit/01_reports/audit_20260523T233444Z.md`
Scope: 114 call-sites across 24 `src/` files

Key findings from audit:
- 5 WARNING "engine empty" calls → reclassified DEBUG (structural duplicate of `query_log.jsonl` `engine_run` records)
- 3 WARNING "config state" calls → reclassified INFO (STACK_EXCHANGE_API_KEY, filter_modes precedence)
- 13 INFO verbose progress calls → reclassified DEBUG (per-URL/per-iteration crawler+scraper traces)
- 93 calls unchanged (already correct level or genuine WARNING/ERROR/INFO)

## Open Questions

None currently. Rate-limited (HTTP 429) calls stay WARNING — distinct from "engine empty" (no results, normal operation). If 429s become frequent enough to be noise, revisit.

## Sources

Internal architectural decision — no external references.

Implementation: `src/log_janitor.py`, `dev/log_janitor/01_prune_test.py`.
