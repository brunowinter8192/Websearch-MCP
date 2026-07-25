# Google Scholar — Re-Eval (2026-05-03, pydoll stack)

**Status before:** "Engine crash 0/0, cause unclear" (2026-04-21 SearXNG stack).

**Phase-A findings (2026-05-03, pydoll stack):**
- DOM probe: page loads correctly, no CAPTCHA, no `/sorry/` redirect, 170 KB HTML
- Selectors `div.gs_r.gs_or.gs_scl` = 10, `.gs_rt` = 10, `h3.gs_rt a` = 10 — all correct
- `ScholarEngine().search()` returns 0 results despite correct DOM
- Root cause (confirmed via raw pydoll result dict): `_JS_PARSE` is a Python triple-quoted string starting with `\nreturn JSON.stringify(...)`. Pydoll's `execute_script` wraps single-line scripts in a function context that permits `return`, but passes multi-line scripts raw to Chrome's `Runtime.evaluate`, where a top-level `return` statement is illegal → `SyntaxError: Illegal return statement`. `_extract_value()` silently returns `None` → `_parse_results()` returns `[]`.

**Fix applied (2026-05-03):** Rewrote `_JS_PARSE` as flat JS: variable declarations first (`var _n`, `var _o`, for-loop), `return JSON.stringify(_o)` as the final statement. No IIFE wrapper. Pattern matches config.yml selector blocks (mojeek/DDG/Lobsters). Selectors unchanged. Rate limit unchanged (3 req/60s — stricter than general engines).

**Smoke baseline:** `dev/search_pipeline/01_reports/scholar_smoke_*.md` (2026-05-03).

**Subsequent removal (2026-05-21):** Scholar fully removed from ENGINES dict as part of the CDP-starvation cascade resolution investigation. Scholar re-integration deferred to pooling-rework (Google-free pool). `src/search/engines/scholar.py` retained in tree, inert.
