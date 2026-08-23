# scrape_url contract inversion: from judging content to reporting facts (2026-08-05)

`src/scraper/scrape_url.py` — the ad-hoc, single-URL, agent-invoked path (`websearch scrape_url`,
reached through the web-research skill). Its contract inverted: previously the scraper judged
whether a result was usable and discarded/rewrote content it judged unusable; now it returns
whatever crawl4ai produced, unconditionally, plus the facts about how it got it, and the calling
agent judges — it has the page text and a user to report to, which a keyword list does not.

## The evidence that forced the removal

Three URLs, re-run under the (unchanged) production config:

- `de.trustpilot.com/review/entega.de` — HTTP 403, 42707 bytes of raw markdown that IS the real
  review page (`# ENTEGA Plus GmbH Bewertungen`). The old `status_code >= 400` early return in
  `try_scrape` discarded all of it and returned `"HTTP error page (404/403)"` — a false claim.
- `guenstiger.de/Produkt/AEG/VX9_2_OeKO.html` — HTTP 403, 38691 bytes, the real product page. Same
  false discard by the same gate. At this project's current `delay_before_return_html=2.0` the page
  actually returns a Cloudflare interstitial instead (confirmed on the real CLI run for this
  change: 342 bytes, "Verifying you are human..."); the real product page only appears at 6.0s —
  that render-time question is separate, unaddressed work, explicitly not touched here.
- `idealo.de/preisvergleich/OffersOfProduct/203078159_-fritz-box-7510-avm.html` — HTTP 200, 401
  bytes reading "Sorry! Something has gone wrong… reference ID …". `is_garbage_content` returned
  `None` on this content, so it sailed through as a clean `"ok"` — the classifier was wrong in the
  OTHER direction too.

Conclusion drawn from all three: a status code is not evidence of anything on its own — a real 403
yields no content and the content itself would show that; a 403 with 40KB of article text is a
server using status codes unusually, not a scrape failure. The reverse also holds: a 200 status
proves nothing about content quality.

## The dropped-fallback precedent this milestone deliberately did NOT reopen

Unrelated to content judgment, but same file, same session's neighborhood: a `curl_cffi` fallback
mechanism was evaluated for THIS path (`scrape_url.py`) in an earlier session
(this area's 2026-08-03 toolbox-scoping entry) and dropped —
all 19 non-`ok` outcomes in this path's own log at the time were checked, none matched the
"browser weaker than plain HTTP" signature, because this path runs `UndetectedAdapter` and is
therefore not the weaker client. That analysis and its conclusion are untouched by this session;
mentioned only because it's easy to confuse with the present change — this session removed content
JUDGMENT, not acquisition method, and did not revisit the fallback question at all.

## What was removed, and what deliberately was not

Removed from `try_scrape`/`scrape_url_workflow`: the `status_code >= 400` early return;
`is_garbage_content()` as a GATE (the call site, not the function); `_GARBAGE_MESSAGES` and the
error-string return path; `strip_consent_prefix()` (content surgery predicated on a garbage
verdict); `truncate_content()`/`DEFAULT_MAX_CONTENT_LENGTH`/the `max_content_length` parameter
(full content, always — a monitor-cc PreToolUse hook already strips pipes/redirects off
`websearch scrape_url` so output can't be shunted to a file and partially read; the 15000-char cap
was the last remaining place something decided what the agent may not see); `get_plugin_hint()`
(dead code); `build_config_record()` (its only job — merging the now-gone `max_content_length` —
disappeared with it); `CONSENT_WORDS`/`CONSENT_DENSITY_THRESHOLD`/`CONSENT_SKIP_OFFSET` (only
consumer was the removed `strip_consent_prefix`).

Explicitly NOT removed: `PruningContentFilter`, `remove_consent_popups`, `COOKIE_CONSENT_SELECTOR`
— these act on the live page BEFORE capture/selection and improve what is fetched, not judge what
was fetched. The `fit_markdown`-too-thin → `raw_markdown` fallback (`MIN_CONTENT_THRESHOLD`,
`meta["fallback_to_raw"]`) also stays — it selects between two crawl4ai-provided candidates, not a
verdict on whether the selected content is "good".

**A cross-module dependency the task brief didn't name:** `src/crawler/crawl_site.py` imports and
calls `is_garbage_content` for its own unattended BFS batch-crawl filter — a categorically
different consumer (no agent reviewing that output, writes files to disk unattended), where an
automatic verdict remains the correct design. `is_garbage_content` stays, unchanged, exported —
only its use as a gate INSIDE `scrape_url.py`'s own workflow was removed. A regression test
(`test_try_scrape_does_not_call_is_garbage_content`) guards against reintroducing that call.

## The new returned shape

`scrape_url_workflow` still returns `list[TextContent]` (unchanged type, no `cli.py` consumer
change needed) — one text block via a new `_format_scrape_output`, facts always before content,
separated by a fixed `## Content` delimiter so the shape is identical regardless of outcome:

```
# Content from: <url>
Published: <date>                          (if present)

## Acquisition facts
- HTTP status: <status or None>
- Bytes (raw markdown from crawl4ai): <n>
- Bytes (content below, after PruningContentFilter[+ raw fallback]): <n>
- crawl4ai diagnosis (an OBSERVATION off crawl4ai's own anti-bot detector, NOT a verdict —
  it has documented false positives and is not acted on by this scraper): success=..., ...
- Acquisition error: <description>          (only when set)

## Content

<full content, or "(no content returned)">
```

The "OBSERVATION, NOT a verdict" caveat is on the rendered line itself, not only in a code
comment — the caller reads it directly. Proof this framing matters, not boilerplate: on
`guenstiger.de` at `delay_before_return_html=6.0` (a different, unaddressed render-time setting)
the full 38691-byte product page comes back AND crawl4ai's own detector still reports
`"Blocked by anti-bot protection: Cloudflare JS challenge"` — presenting that as a status claim
would just swap one bad automatic judgment for another, the exact failure mode this whole change
targets.

Zero content is a legitimate, visible outcome (`(no content returned)` under the same delimiter,
real 0 byte counts in the facts) — never a discard message standing in for the page, because that
state no longer exists.

## Failure-state renaming: acquisition_error, not garbage_type

`meta["garbage_type"]` → `meta["acquisition_error"]`, restricted to the three states that already
existed in `try_scrape`'s outer `except` and mean "acquisition itself produced no result at all" —
categorically different from a content verdict: `None` (normal), `"budget_exhausted"`,
`"browser_missing"`, and a newly-NAMED `"exception"` for the generic catch-all that previously
collapsed silently into the same state as a real empty page. Naming it is not new detection — the
branch already existed in the code; only the label was added, surfacing information the code
already had instead of discarding it.

## Log schema (`scrape_logger.py`)

`outcome` values going forward: `ok` | `empty` | `budget_exhausted` | `browser_missing` |
`exception` — no content-judgment categories. `config` drops `max_content_length`, keeps
`min_content_threshold` (folded directly into `extract_config_stamp`, same treatment as the
existing `total_budget_s`). `config_hash` changes shape as a result — does not group with
pre-2026-08-05 records even under an otherwise-similar config.

Per explicit review instruction: `garbage_type`/`truncated`/`consent_stripped` are dropped from the
ACTIVE schema (not kept as always-null) — a permanently-null field for a mechanism that is never
coming back would just be clutter, categorically different from a forward-compatible field like
`pipe_scraper`'s `crawl4ai_fallback_fetch_used` (reserved for something already planned). Because
164 existing records in `scrape_log.jsonl` DO carry those fields, the schema comment names them
explicitly as historical-only, so a reader across the boundary reads "the log is consistent, this
mechanism was retired on this date" rather than "the log is broken" or "these fields vanished
unexplained." Same treatment for the historical-only `outcome`/`garbage_type` values that no longer
occur (`http_error`, `cookie_wall`, `login_wall`, `cloudflare`, `nav_dump`, `minimal_content`,
`crawl4ai_error`) — an aggregate spanning the change must read their disappearance as "the
classifier that emitted them was removed," not "those failure modes stopped happening on the live
web."

## Verification

Unit tests: `tests/test_scrape_url.py` rewritten from 13 to 21 tests. Three tests updated
`garbage_type` → `acquisition_error`; two `_GARBAGE_MESSAGES` tests moved to the smaller
`_ACQUISITION_ERROR_MESSAGES` (2 entries: `browser_missing`/`budget_exhausted` only — categorically
different from the removed 9-category dict since these two states have no content to judge at all).
New: the trustpilot-shaped HTTP-403-with-content passthrough (a fake crawler returning real
content at 403, asserting it comes through); the named `"exception"` state; config-stamp no longer
carrying `max_content_length`; `is_garbage_content` still importable and NOT called from
`try_scrape`; four `_format_scrape_output` tests (facts-before-content ordering, content never
replaced by a message, zero-content explicit, crawl4ai diagnosis carrying the observation caveat in
the rendered text itself).

Real CLI runs (`./venv/bin/python cli.py scrape_url <url>`), all four target URLs:
- trustpilot: HTTP 403, 28171 bytes returned (the real review page, PruningContentFilter-selected
  from the raw 43253).
- guenstiger: HTTP 403, 342 bytes returned (the Cloudflare interstitial — correct at this
  project's unchanged `delay_before_return_html=2.0`, matching the brief's own predicted caveat).
- idealo: HTTP 200, 367 bytes returned (the "Sorry!" page, `crawl4ai_success=True` — no diagnosis
  flag at all here, proving content-level judgment is now entirely the agent's job).
- rfc-editor.org (ordinary page, regression check): HTTP 200, 683005 bytes returned in full — no
  truncation (old cap was 15000 chars).

All four confirmed logged with real `outcome`/`http_status`/`bytes_returned` values and no
`garbage_type`/`truncated`/`consent_stripped` keys in the new records.

Full suite: `9 failed, 134 passed, 0 errors` (was 126 passed pre-change). Diffed the `FAILED` line
list against the standing baseline — identical, no drift. The 9 pre-existing
`test_query_logger.py`/`test_proxy_pool.py` failures unrelated and unchanged.
