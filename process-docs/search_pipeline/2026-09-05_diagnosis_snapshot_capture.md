# Diagnosis Snapshot Capture for Browser Engines — 2026-09-05

## Problem

`query_log.jsonl` recorded a VERDICT per engine (`status: "EMPTY_BLOCK"`, etc.) derived from raw
browser-observed facts — marker text, URL, `document.readyState`, page title, engine-specific flags
like `pow_link`/`iframe_challenge` — that every browser engine already computed at diagnosis time and
then discarded, keeping only the classified string. Concretely: `brave.py`, `bing.py`, `yandex.py`,
`startpage.py` built a `diag` dict, passed it to a `_classify_diagnosis(...)` call, and discarded the
dict; `google.py`, `duckduckgo.py`, `mojeek.py` read the equivalent values one at a time inside an
inline classification chain and discarded them the same way. As of the investigation that motivated
this work, 214 `mojeek` runs over a 14-day window were logged as `EMPTY_BLOCK` with no way to tell
whether the server answered 403 or 200-with-captcha — two completely different situations that had to
be resolved by hand outside the tool.

## Approaches considered and rejected

**Variable-arity `search_with_reason` return** (2-tuple for `openalex`/`scholar`/`BaseEngine`'s
default, 3-tuple for the 7 browser engines), with `_engine_with_timing` sniffing tuple length at the
call site. Rejected: a permanent arity-sniffing adapter living in production code is a worse outcome
than aligning the contract once, and it would silently paper over a real interface mismatch if a
future engine got the shape wrong. Replaced with a uniform 3-tuple
`(results, empty_reason, diagnosis)` across all 9 engines, including `openalex.py`, `scholar.py`, and
`BaseEngine`'s default — `diagnosis` is always `None` for those three, since no diagnosis mechanism
was built for HTTP-API engines (deliberately out of scope for this milestone, not an oversight).

**Attach diagnosis only where a dict was already being built and discarded.** The first cut left
`google.py`'s `/sorry/` short-circuit, `duckduckgo.py`'s early challenge-form check, and
`yandex.py`'s early block-URL-redirect check without any snapshot, since — before this milestone —
those three branches only ran a cheap boolean/URL check, never a full dict. Corrected: those are
precisely the branches producing the most diagnostically valuable `EMPTY_BLOCK` records in the whole
log, i.e. the exact case this milestone exists to fix. Every branch that returns a non-`None`
`empty_reason` now computes and attaches a snapshot, including a newly-added fresh one for
`EMPTY_NO_RESULTS` (successful container wait, zero items after parse) — a branch that previously
carried no diagnosis at all in any engine.

**DuckDuckGo's `marker` field holding the CSS selector `form#challenge-form`.** Rejected: `marker`
means "the text marker that matched" everywhere else (brave/bing/yandex/startpage/mojeek all scan
body/title text against a keyword list); overloading it with a structural selector string on one
engine would destroy the cross-engine comparability the consistent field naming exists for.
DuckDuckGo's challenge-form presence is a structural fact (an element count, not text), so it got its
own boolean field, `challenge_form`, the same pattern as brave's `pow_link` and startpage's
`iframe_challenge`. `marker` stays `None` for DuckDuckGo.

## Decision

Uniform 3-tuple contract `search_with_reason(...) -> (results, empty_reason, diagnosis)` across all 9
engines. `diagnosis: dict | None` — non-`None` whenever `empty_reason` is non-`None` for the 7
browser engines, always `None` for `openalex`/`scholar`/`BaseEngine`'s default.

Common snapshot field names across the 7 browser engines: `marker` (`str | None` — the matched text
marker, `None` when the engine's own block signal isn't text-based, e.g. google's URL-path check or
duckduckgo's element count), `title` (raw `document.title` — the field this milestone specifically
adds; previously it existed only as an intermediate value inside marker matching and was never
retained), `url` (`window.location.href`), `ready_state` (`document.readyState`). Engine-specific
extras keep their own names and are never folded into `marker`: `pow_link` (brave), `iframe_challenge`
(startpage), `challenge_form` (duckduckgo).

`google.py`, `duckduckgo.py`, `mojeek.py` were refactored from an inline classification chain (partial,
for mojeek) into the same `_diagnose(tab) -> dict` + pure `_classify_diagnosis(...)` shape
`brave.py`/`bing.py`/`yandex.py`/`startpage.py` already used, preserving branch order and conditions
exactly — no `status`/EMPTY sub-status value changed anywhere. `brave.py`'s single top-of-function
diagnosis snapshot is reused for both its immediate PoW/CAPTCHA branch and its post-wait-failure
branch (the two checks happen at the same tick, nothing async runs between them); every other engine,
and every engine's `EMPTY_NO_RESULTS` branch, takes a fresh `_diagnose(tab)` call, since real time —
and possibly a captcha appearing — can pass between an engine's own two check points.

`search_web.py`'s `_engine_with_timing` unpacks the uniform 3-tuple and threads `diagnosis` into
`engine_stats[name]["diagnosis"]`, next to `"status"` — read by both `engine_run` (written by
`_query_engines_concurrent`) and `workflow_summary` (written by `_build_query_log_entry`), since they
share the same `engine_stats` dict. A single change point covers both record types.

## Verification

Two live `cli.py search_web` runs (2026-09-05) confirmed the mechanism end to end against real
search-engine responses. `site:reddit.com fritzbox 7590 firmware` produced
`mojeek: status=EMPTY_BLOCK, diagnosis={marker: "captcha", title: "Captcha", url: ".../search?q=...",
ready_state: "complete"}` — resolving exactly the mojeek 403-vs-captcha ambiguity that motivated this
work — and `google: status=EMPTY_NO_RESULTS` with a populated diagnosis snapshot (title/url/
ready_state, marker `None`). A second, deliberately-nonsense query produced
`google: status=EMPTY_NO_CONTAINER` (diagnosis populated) and `startpage: status=TIMEOUT_WATCHDOG`
(diagnosis `None`, correctly — a watchdog timeout never reaches `search_with_reason`'s return, so no
diagnosis mechanism applies). Every `OK`-status engine carried `diagnosis: None` in both runs,
confirming the field is empty-verdict-scoped as designed, and both `engine_run` and `workflow_summary`
records for the same run carried byte-identical `diagnosis` values. Full test suite: 384 passed — 14
new tests (pure `_classify_diagnosis`/`_match_marker` coverage for google/duckduckgo/mojeek, mirroring
the pre-existing bing/brave/yandex/startpage test pattern, plus one new
`search_web_workflow`-level test proving a diagnosis dict propagates unchanged into both record
types).

## Deliberately out of scope

HTTP status capture (real server response codes via CDP Network-domain plumbing) — the snapshot stays
DOM/JS-observable facts only (title/url/readyState/markers), the same "fact, not verdict" precedent as
`src/scraper/chromium_scrape.py`'s `document_status_chain` (see `process-docs/scrape_pipeline/` for
that lane's own history). Collapsing or removing the existing EMPTY sub-statuses now that raw facts
back them — this milestone is additive only, `status` computation is untouched. A diagnosis mechanism
for `openalex.py`/`scholar.py` — their `search_with_reason` signature was aligned to the uniform
3-tuple purely for interface consistency; no diagnosis dict is built for either (HTTP-API engines, no
browser DOM to inspect). The query-log schema itself (`engine_run`/`workflow_summary`/`drilldown`
record types, `search_key` correlation) is unchanged — see `process-docs/logging/` for that history.
