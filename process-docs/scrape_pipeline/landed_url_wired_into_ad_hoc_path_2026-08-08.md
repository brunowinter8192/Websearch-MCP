# Landed URL wired into the ad-hoc scrape path (2026-08-08)

Milestone 2 of the 3-milestone plan; the `is_same_target` primitive it wires in was built in an
earlier session of this same area. `src/scraper/scrape_url.py` now captures crawl4ai's `result.redirected_url`,
logs it alongside a `same_target` verdict, and renders it in `_format_scrape_output` — ONLY when it
deviates. `src/crawler/pipe_scraper.py`/`pipe_scrape_logger.py` (milestone 3) untouched.

## What was recorded, and why raw vs. derived

`landed_url` in `scrape_log.jsonl` is `result.redirected_url` VERBATIM — never run through
`is_same_target`'s normalization. `same_target` is a separate field: `is_same_target(url,
landed_url)` evaluated once, at write time. Splitting these was deliberate: normalization is a
comparison RULE, which can be revised; the raw value is a storage FORMAT, which must stay stable
for old records to be re-analysable under a future rule revision. Collapsing them into one
normalized field would have made that re-analysis impossible.

`status_code` was left untouched, and no second status field was added. crawl4ai's own behavior
(confirmed in the 0.9.2 source ahead of this session, not re-derived here): `status_code` is the
FIRST hop of a redirect chain, while `landed_url` and content are the LAST — so a record can
legitimately show `http_status: 301` next to full, real content. The `landed_url` field alone makes
that combination self-explanatory; a second status field would have been redundant.

## Rendering: only on deviation, and where the doubly-real evidence came from

`_format_scrape_output` appends a `- Landed URL (redirected to a different target than requested):
<url>` line right after the HTTP-status line, gated on `landed_url and not is_same_target(url,
landed_url)`. Absent on the ordinary no-redirect case (the overwhelming majority) by design.

Two real CLI findings surfaced during verification, both accepted as real results rather than
re-run until they matched the pre-session expectation:

- `https://www.rfc-editor.org/rfc/rfc2616` was expected (going into this session) to be a clean
  no-redirect control. It is NOT: HTTP 302 to `https://www.rfc-editor.org/info/rfc2616/`, a real
  path change, correctly rendered as a deviation. Re-requesting the already-landed URL
  (`.../info/rfc2616/`) gave the actual no-redirect control: HTTP 200, `landed_url` identical to
  the request, no line rendered — the correct behavior confirmed end-to-end.
- `https://www.idealo.de/preisvergleich/OffersOfProduct/203078159_-fritz-box-7510-avm.html` (the
  motivating case for `is_same_target` itself) came back with `landed_url` IDENTICAL to the
  requested URL, HTTP 200, 367 bytes of "Sorry! Something has gone wrong" (an Akamai Bot Manager
  block page). `same_target` is therefore `true` and no line renders. Two explanations are equally
  consistent with this single observation: (1) the block page is served directly at the requested
  URL with no browser-level redirect at all, or (2) a redirect back to the SAME URL occurred and is
  indistinguishable from (1) using `landed_url` alone. Recorded as a candidate explanation only,
  not settled — not pursued further, since resolving it needs a different signal than this field
  provides (e.g. `result.redirected_from`/network trace), out of scope for this milestone.

The practical consequence, captured as a Gotcha in `src/scraper/DOCS.md`: `same_target: true`
alongside a thin/blocked-looking page is NOT proof that no redirect happened — it only proves the
FINAL landed URL matches the requested one.

## Verification

54 tests in `tests/test_scrape_url.py` (was 47 after milestone 1): `try_scrape` meta plumbing
(`landed_url` captured raw from a fake `redirected_url`; `None` on every acquisition-failure path
that never obtains a result object), `_format_scrape_output` rendering (present on a real host
deviation, absent on no-redirect, absent on a mere-spelling difference i.e. trailing slash, absent
when `landed_url` itself is absent), and one workflow-level test confirming `scrape_url_workflow`'s
`log_scrape` record carries both `landed_url` and `same_target` correctly derived from `meta`.

Real CLI runs (`./venv/bin/python cli.py scrape_url <url>`), JSONL record + rendered text both
inspected for each:
- idealo (above): `same_target=true`, no line, HTTP 200 — see the ambiguity note above.
- `https://docs.anthropic.com/en/api/getting-started` → landed on
  `https://platform.claude.com/docs/en/api/overview`, HTTP 301, `same_target=false`, line
  rendered — the host-change shape.
- rfc-editor.org (above): both the original 302-redirect case and the true no-redirect control,
  both rendering correctly.

Full suite: `9 failed, 170 passed`. `FAILED` list diffed against the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift.
