# Mojeek ALTCHA Wait Extension — Negative Result — 2026-09-05

## What this milestone built

`mojeek.py`'s `_wait_for_results` was changed from a fixed `MAX_WAIT_CYCLES=3 × WAIT_INTERVAL=0.2`
(0.6s total) to a single wall-clock deadline (`MOJEEK_BUDGET_S=4.5`, anchored via
`time.monotonic()` at `search_with_reason`'s first line, covering navigation and the results poll
together) — sized to leave 1.0-1.5s of margin under the shared, unmodified 6.0s per-engine
watchdog. Separately, all 7 browser engines' success branches were changed to attach the
already-collected `document_status_chain`/`http_status` network facts (`attach_document_status({},
status_chain)`, no extra CDP call, no extra JS eval) instead of `diagnosis=None`, so a success
record can show whether a page reload happened before the results arrived — the DOM-fact half of
the snapshot (`_diagnose(tab)`) stays empty-only, since a successful search has nothing to
diagnose. See `process-docs/search_pipeline/2026-09-05_document_http_status_capture.md` and
`2026-09-05_guessed_verdict_removal.md` for the snapshot fields this milestone built on.

## What was measured

Seven live `cli.py search_web` runs against mojeek on 2026-09-05, distinct queries, production
code path (real rate limiter, real 6.0s watchdog, no test doubles):

| Query | search_ms | document_status_chain | result_count |
|---|---|---|---|
| mojeek altcha proof of work test query one | 4585 | `[200]` | 0 |
| python asyncio event loop tutorial | 4680 | `[200]` | 0 |
| rust programming language guide | 4699 | `[200]` | 0 |
| kubernetes container orchestration basics | 4530 | `[200]` | 0 |
| postgresql index performance tuning | 4518 | `[200]` | 0 |
| docker compose tutorial for beginners | 4597 | `[200]` | 0 |
| machine learning gradient descent explained | 4538 | `[200]` | 0 |

Every run: `status="EMPTY"`, `diagnosis.containers_found=False`, `diagnosis.marker="captcha"`,
`diagnosis.title="Captcha"`. `document_status_chain` never grew past its single initial `200` entry
in any of the 7 runs — no post-verification reload was ever observed. Zero results across all 7.

The mechanism itself worked exactly as designed: the watchdog never fired once (every `search_ms`
landed 1.3-1.5s clear of the 6.0s ceiling), and the log carried a full, honest snapshot on every
run. What the mechanism revealed is that the extended wait made no difference to the outcome — the
result is negative, and the negative result plus its cause is the point of this entry.

## Cause established after the measurement

Two independent findings, established after the 7 runs above, together explain why a longer wait
could not have changed the outcome:

**1. The PoW widget never self-starts.** Mojeek's `challenge.js` injects the `altcha-widget` with
no `auto` attribute set. Mojeek's own ALTCHA bundle only self-starts the proof-of-work computation
when that attribute equals `"onload"` — it defaults to off. Without it, the widget sits inert until
a human clicks it; the client-side PoW computation this milestone was budgeting time for never
begins at all in an unattended browser session. This is not a timing problem — no waiting budget,
however long, can make an inert widget start computing on its own. The 4.5s deadline gave the
challenge time to run; the challenge was never running in the first place.

**2. The block is tied to the network, not the acquisition method.** `ddgs` 9.16.0 — a widely-used
HTTP client with TLS impersonation, i.e. a completely different acquisition path from this
project's pydoll/CDP browser automation — was tried directly from this same machine and returned
zero mojeek results, while the identical call returned real results for duckduckgo and brave in the
same run. Separately, a plain `httpx` request with cookies, a session, and a `Referer` header, and
also a real headed (non-automated) Chrome window, both landed on the same HTTP-200-with-captcha
page mojeek's engine already observes. Four different acquisition methods (pydoll/CDP stealth
browser, `ddgs`, plain `httpx` with session/cookies/referer, and a real headed Chrome with no
automation at all) converged on the identical outcome. As of 2026-09-05, this points at the network
this project runs on — a university eduroam network — as the actual gate, not at this project's
browser fingerprint or request shape. This project's permanent operating environment is that same
network, so the condition is not expected to change on its own; it is recorded here as of this
date, not asserted as a permanent property of Mojeek's service.

## What this means for the shipped mechanism

The deadline-based wait, the `MOJEEK_BUDGET_S=4.5` sizing, and the network-facts-on-success change
across all 7 browser engines are NOT reverted by this finding — they are the reason the finding is
knowable at all, and they behave correctly regardless of what any future network/session condition
turns out to be (a resolving challenge would still show up as a second `document_status_chain`
entry on a success record, exactly as designed, if PoW auto-start or network access ever changes).
Nothing here suggests raising `MOJEEK_BUDGET_S` further, since the widget was never running in the
first place — a longer wait watches an inert widget for longer, no more. Any future fix belongs to
a different lane entirely: either triggering the ALTCHA widget's PoW programmatically (a
`auto="onload"` equivalent invoked from our own injected JS, not a wait-budget change) or a
different network path for this specific engine — both out of scope for the wait-budget deliverable
this entry records.
