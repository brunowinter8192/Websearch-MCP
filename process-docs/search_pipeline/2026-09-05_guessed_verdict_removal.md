# Guessed Verdict Removal — 2026-09-05

## Problem

Milestones 1 and 2 (`process-docs/search_pipeline/2026-09-05_diagnosis_snapshot_capture.md`,
`2026-09-05_document_http_status_capture.md`) put the raw observations behind every engine's empty
result into the query log. That made the EMPTY_* verdicts — `EMPTY_BLOCK`, `EMPTY_NO_CONTAINER`,
`EMPTY_CONCURRENT_RACE`, `EMPTY_CONSENT`, `EMPTY_NO_RESULTS` — both redundant and actively
misleading: each one was a guess about what a keyword scan or a URL pattern meant on the remote
side, and the log had no way to say the guess might be wrong. A concrete case from the real log:
the query `roboter-bausatz.de Versandkosten versandkostenfrei ab` was recorded as `EMPTY_BLOCK` for
mojeek. Mojeek's result-page title always echoes the query, and `roboter` contains the substring
`robot`, one of mojeek's block keywords — a false match on ordinary German text, indistinguishable
from a genuine block by the verdict alone, and permanently indistinguishable, since the verdict
carried no more information than the string itself.

## The line drawn

A status describing what OUR OWN code did (a timeout, an exception class, a rate-limiter skip, a
successful parse) is a fact and stays: `OK`, `EMPTY`, `RATE_SKIP`, `TIMEOUT_WATCHDOG`,
`TIMEOUT_NONCOOP`, `TIMEOUT_HTTPX`, `ERROR_BROWSER`, `ERROR_HTTP`, `ERROR_PARSE`, `ERROR_OTHER`. A
status guessing what the REMOTE side meant, by scanning a title/body for keywords or
pattern-matching a URL, is a verdict and goes. An engine that returns no results now logs plain
`EMPTY`, with its diagnosis snapshot carrying the observation instead of a conclusion.

## Method: branch-by-branch signal check before deleting anything

Every removed verdict was checked against the existing (milestone 1/2) snapshot fields before its
code was touched, per this reasoning: if the distinguishing signal already lived in the snapshot,
just stop computing the verdict; if it did not, add the fact first, then remove the verdict. Result:

- `EMPTY_BLOCK`/`EMPTY_CONSENT` (google) → `url` (already had `/sorry/`/`consent.google.com`
  substrings). `EMPTY_BLOCK` (duckduckgo) → `challenge_form`. `EMPTY_BLOCK` (mojeek/bing/startpage)
  → `marker`. `EMPTY_BLOCK` (brave) → `marker`/`pow_link`. `EMPTY_BLOCK` (yandex) → `marker`/`url`.
  `EMPTY_CONCURRENT_RACE` (all 7) → `ready_state`. `EMPTY_NO_CONTAINER` (all 7) → re-derivable as
  "none of the above" once the other fields exist; no field needed. All of the above required no
  new capture — only removing the classify call.
- `EMPTY_NO_RESULTS` (all 7 browser engines) had NO existing field distinguishing it from
  `EMPTY_NO_CONTAINER` — both would show `ready_state="complete"`, `marker=None` after the fact.
  The actual distinguishing signal (`_wait_for_results` succeeded vs. failed) was structural
  (which code branch ran), never stored as data. Added `containers_found: bool | None` — `True` on
  the was-`EMPTY_NO_RESULTS` branch, `False` on the was-classify-failure branch, `None` on branches
  that short-circuit before ever calling `_wait_for_results` (never observed, never fabricated as
  `False` — the same "don't invent an observation" principle milestone 2 established for
  `http_status`).
- `EMPTY_BLOCK` (openalex, 429) → verified in code before acting: `_fetch_results` returns the same
  `status_code` for the 429 branch that `diagnosis["http_status"]` already carries. No new field.
- `EMPTY_BLOCK` (scholar, 30x redirect) → `http_status` already carried the redirect code. No new
  field. `EMPTY_BLOCK`/`EMPTY_NO_RESULTS` (scholar, inline captcha form) → the captcha-form
  element's presence had NO snapshot field (scholar's diagnosis was only `{"http_status": int}`
  before this milestone) — it fed `_parse_response`'s verdict and nowhere else. Added
  `captcha_form: bool`; `_parse_response` now returns `(results, captcha_form)` instead of
  `(results, reason)`.

`_classify_diagnosis` (and its per-engine equivalents, including scholar's inline captcha-form
branch) was deleted in every one of the 7 browser engines plus scholar, since nothing else needed
it once its outputs were gone. `_match_marker` (mojeek) and `_is_block_url` (yandex) were kept —
both populate a snapshot field directly (`marker`, and `_is_block_url` doubles as the early
short-circuit optimization inside `search_with_reason`), not solely a classification input.

## Corrections made during review

**The early short-circuit branches stay as runtime optimizations, only their reported reason
changes.** Google's `/sorry/` check, duckduckgo's `challenge_form` check, brave's PoW check,
yandex's block-URL check all skip a pointless `_wait_for_results` poll when the engine already
knows from a URL/element check that the page won't produce results. That skip is independent of
what verdict gets reported and was left in place; only the `S.EMPTY_BLOCK` return value at each of
those sites became `None`.

**Dev-script fix scope, corrected mid-review on two points:**
1. `acquire_probe.py`, `branch_probe.py`, `cdp_starvation_probe.py` categorize queries via
   `timings["engine_details"]`, which carries only `status`/`ms` — no diagnosis. The first pass
   left their `"captcha"` category keyed on the new bare `"EMPTY"` status, which would have
   silently counted every empty run (of any cause) as a captcha detection — exactly the kind of
   guess-dressed-as-fact this milestone removes, just relocated from the production log into a
   probe report. Corrected: the category was renamed `"captcha"` → `"empty"` in all three files,
   an honest narrower label reflecting exactly what `engine_details` can still see. No widening of
   `engine_details` to carry diagnosis was done — that would have been a capability addition
   outside this milestone's scope, and none of the three probes need more than the rename to keep
   running.
2. `no_google_burst_smoke.py`'s block-rate metric (Scholar's block frequency under a concurrent
   burst) is the probe's entire reason to exist, and unlike the three probes above it calls
   `search_with_reason` directly — its diagnosis dict was one line away, previously discarded via
   `results, reason, _ = await ...`. The first pass would have dropped the metric entirely for lack
   of a verdict to key on. Corrected: `_run_engine` now keeps the diagnosis and a new
   `_is_blocked(diagnosis)` derives the same fact the removed verdict used to encode —
   `diagnosis.get("captcha_form")` truthy, or `diagnosis.get("http_status")` in the 300-399 range —
   both fields already present in scholar's snapshot from this same milestone's own scholar.py
   change. The metric survived, keyed on the fact instead of the verdict.

`scholar_http_probe.py` (a standalone, currently-unused probe class independent of production
`ScholarEngine`) kept its own local sentinel strings (`_BLOCK`, `_NO_RESULTS`) rather than adopting
`src.search.status`'s (now-removed) constants or the production diagnosis-snapshot pattern — its
internal backoff experiment never reaches the production query log, so it has no reason to share
either vocabulary.

## Verification

Live `cli.py search_web` run against the milestone's own motivating query,
`roboter-bausatz.de Versandkosten versandkostenfrei ab`: mojeek's record now reads
`status: "EMPTY"` (not `EMPTY_BLOCK`) with `diagnosis: {marker: "captcha", title: "Captcha",
containers_found: false, http_status: 200, document_status_chain: [200], url: ...}` — the exact
case named in the motivating example, now honestly labeled and fully explained by the attached
facts rather than asserted by a verdict. A second run on a random nonsense query exercised the new
`containers_found` field's `True` branch (google: wait succeeded, zero parsed) alongside a
`startpage: TIMEOUT_WATCHDOG` (a fact status, correctly unchanged and correctly diagnosis-`None`).
Full test suite: 367 passed. Two test files were deleted outright
(`test_google_engine.py`, `test_duckduckgo_engine.py` — each tested only the now-deleted
`_classify_diagnosis`, no remaining subject to keep alive with a rewritten assertion) rather than
patched; five more had only their `_classify_diagnosis` sections removed, keeping every other test
(`_build_results`, `_clean_url`, `_is_self_referential`, `_is_block_url`, `_match_marker`)
untouched; `test_openalex_engine.py`'s 429 test and `test_query_logger.py`'s diagnosis-propagation
mock were rewritten in place, since their subject (429 handling, diagnosis propagation) still
exists — only the specific verdict behavior they asserted on changed.
