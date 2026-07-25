# Logging Audit — stderr Leak Investigation, 2026-05-24

## Symptom

As of 2026-05-24, `searxng-cli search_web` emitted Python `logger.warning()` output to stderr. Claude Code's Bash tool merges stdout+stderr into the tool_result, producing observed noise before the result table:

```
STACK_EXCHANGE_API_KEY not set — anonymous quota (300 req/day)
Lobsters empty (EMPTY_NO_CONTAINER) for: <query>
```

## Root Causes Identified

Two causes found present simultaneously via AST-walk audit of `src/` (`dev/logging_audit/01_audit.py`, 114 call-sites across 24 files):

1. **Semantic misclassification** — per-engine-empty events filed as WARNING in `src/search/engines/*.py`. These events are already captured structurally in `query_log.jsonl` via `query_logger.py` (`{status, drop_reason}` records), making the text warning redundant.
2. **Missing logging config** — `cli.py` had no `logging.basicConfig()` call. Python's default `lastResort` handler emits WARNING+ to stderr for any log call reaching the root logger unconfigured.

## Code Analysis Detail

- `src/search/engines/stack_exchange.py`: `STACK_EXCHANGE_API_KEY not set` logged at WARNING — assessed as config-state notice, not a problem, candidate for INFO reclassification.
- `src/crawler/crawl_site.py:305`: had its own `logging.basicConfig()` inside an `if __name__ == "__main__"` guard — fires only in standalone mode, not via `cli.py`, so unaffected by the `cli.py` fix.

## Audit Tooling

`dev/logging_audit/01_audit.py` — AST walker over `src/`, emits one row per `logger.X()` / `logging.X()` call with file:line, logger object name, current level, message template (truncated 120 chars). Report written to `dev/logging_audit/md/`.

Two audit runs recorded: `01_audit_20260523T233444Z.md` (initial baseline) and `01_audit_20260523T234725Z.md` (re-run after call-site relevel to verify engine-empty entries moved off WARNING).

## Direction Taken

Investigation pointed toward a `cli.py` logging-config fix (FileHandler-only, before any `src.*` imports) combined with call-site relevel of the misclassified WARNING calls — full option evaluation and the finalized call-site change list are a separate concern from this audit-tooling record.
