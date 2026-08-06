# --books/--pdf/--docs mode flags removed (2026-08)

The three mutually-exclusive `search_web`/`search_engine_drilldown` mode flags — each appending a
query modifier and applying a domain whitelist/blacklist post-filter — were removed at the user's
decision: not used in practice, pure CLI surface + code-path + cache-key/logging-variant cost with
no real use-case. Removed, not deprecated.

## What was deleted

`src/search/filter_modes.py`, `book_whitelist.py`, `pdf_filter.py`, `docs_filter.py` — all four,
in full. `docs_filter.py` was not on the initial candidate list (only `filter_modes.py`,
`book_whitelist.py`, `pdf_filter.py` were named up front) but grep confirmed it was imported ONLY
by `filter_modes.py`, same mode-only status as the other three — found by investigation, not by
filename match, per the task's own instruction not to delete by filename alone.

## What stayed, and why (shared-vs-mode-only triage)

`_DEFAULT_ENGINES` lived in `filter_modes.py` alongside the mode machinery but is NOT mode-specific
— it's the general 14-engine default set consumed by `search_web.py`'s `_select_engines` on every
plain query. Relocated (definition + comment) directly into `search_web.py`'s INFRASTRUCTURE
section rather than deleted.

`query_modifier_map` (the per-engine query-string-modifier parameter threaded through
`search_web_workflow` → `_run_engine_fanout` → `_query_engines_concurrent` → `_engine_with_timing`)
looked mode-adjacent (the removed `apply_filter_mode` was its only caller-side producer) but is
generic plumbing still exercised directly by `dev/search_pipeline/stage1_pool_fetch.py` and
`value_eval_probe.py`, which call `_query_engines_concurrent` with their own hand-built modifier
maps, bypassing `search_web_workflow` entirely. Kept as-is, unchanged signature.

## Cache-key and log-schema dimension removal

`cache.cache_key`'s `modifier_id` param was fed ONLY by the removed `mode` value. Removed the
param entirely rather than leaving it as an unused optional kwarg. Verified the general (no-flag)
path is byte-for-byte unaffected: the old canonical string was
`f"{query}|{language}|{engines}|{time_range}{mid}"` where `mid` was already `""` whenever
`modifier_id` was `None` — i.e. the hash `cache_key` produced for every real plain-query call
before this change is identical to what the param-less version produces now. No cache-key drift
for existing/future plain-query cache entries.

The `drilldown` record's `"mode"` field (see the prior `drilldown_logging_and_search_key_2026-08-05`
entry in this same area for its original design) is DROPPED, not kept as a null-valued field.
`query_logger.py`'s schema comment carries an explicit note: absence of the key means the record
predates or postdates the field, not corruption — following the same "lazy-pruned, opportunistic
join" posture the schema comment already used for `search_key`.

## Test fallout (general-path tests, not mode-only, so fixed not deleted)

No test file exercised the removed flags directly (`--books`/`--pdf`/`--docs` never appeared in
`tests/`). Three spots in `tests/test_query_logger.py` referenced the mode dimension as part of
otherwise general-path test coverage and needed signature/shape updates to keep passing:
`test_log_query_accepts_drilldown_record_shape` (dropped the `"mode": None` key from its manually
constructed record), `test_search_web_workflow_writes_search_key_matching_cache_key` (dropped
`modifier_id=None` from its real `cache.cache_key(...)` call), and
`test_log_drilldown_all_cache_status_and_pool_combinations` (dropped the `None` positional arg from
its three subprocess-isolated `cli._log_drilldown(...)` calls — real function, real subprocess,
per that test's own isolation rationale).

## Verification

Live CLI: `cli.py search_web "test" --books` and `cli.py search_engine_drilldown "test" --engine
google --pdf` both exit 2 with `unrecognized arguments`. Live plain-query run (`search_web
"python asyncio tutorial"`) produced a real 14-engine breakdown table (counts capped to Google's
pool size of 4, per the existing K-cap logic); the resulting cache entry was then read back via a
real `search_engine_drilldown ... --engine google` call, returning real URLs — full path exercised
end-to-end, not just unit-level.

Full suite: `9 failed, 181 passed` both before and after — the FAILED line list diffed identical
across the two runs (7 pre-existing `test_query_logger.py` failures against a stale
`.search`/`fetch_previews`/`ql.LOG_PATH` interface, unrelated to this change and left untouched, +
2 pre-existing `test_proxy_pool.py` failures). The 3 fixed spots above were already passing before
this change (general-path coverage, not among the 7 baseline failures) and remained passing after.
