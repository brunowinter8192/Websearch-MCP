# Bee CDP Starvation — Phase 1 Probe

**Date:** 2026-05-21  
**Verdict:** REFUTED  
**Report:** `dev/search_pipeline/01_reports/cdp_probe_20260521_174959.md`

---

## Hypothesis

During Google CAPTCHA navigation, Chrome emits a burst of CDP events processed by
pydoll's `ConnectionHandler._receive_events()` (`connection_handler.py:226`) in a
tight `async for raw_message in _incoming_messages()` loop. When websockets' internal
queue is non-empty, `Queue.get()` completes without yielding — near-non-yielding
busy loop. All 9 engines' `asyncio.wait_for(limiter.acquire(), 5.0)` calls
(`_engine_with_timing()` in `search_web.py:299`) never get a scheduler turn and
expire as TimeoutError simultaneously — including HTTP-only engines.

## Instrumentation

Three measurements sharing the same asyncio event loop across 20 sequential queries:

- **Pattern A** — `loop.slow_callback_duration=0.05s; loop.set_debug(True)` + asyncio
  logger capture: records any callback blocking >50ms.
- **Pattern B** — canary task: `await asyncio.sleep(0.1)` every 100ms, scheduling
  latency = actual_elapsed − 100ms. From Ray Serve production pattern.
- **CDP counter** — monkey-patch on `ConnectionHandler._process_single_message`
  (`connection_handler.py:244`): timestamps each CDP message received.

Query categories used for latency segmentation:
- `captcha`: google_status == EMPTY_BLOCK (Chrome actively navigating CAPTCHA page)
- `zero_cascade`: all 9 engines RATE_SKIP simultaneously
- `normal`: all other queries

## Key Numbers

| Metric | normal | captcha | zero_cascade |
|--------|--------|---------|--------------|
| samples n | 754 | 115 | 396 |
| scheduling latency p50 ms | 1.2 | 1.2 | 1.2 |
| scheduling latency p95 ms | 1.3 | 1.3 | 1.3 |
| scheduling latency p99 ms | 3.0 | 1.4 | 1.4 |
| scheduling latency max ms | 19.1 | 2.7 | 1.4 |

Slow-callback events captured (Pattern A, >50ms): 2  
Total CDP messages received: 1378  

### CDP Rate by Query

| # | Query | category | cdp_events | cdp_rate/s |
|---|-------|----------|------------|------------|
| 1 | python asyncio best practices | captcha | 162 | 24.5 |
| 2 | rust ownership borrow checker explained | normal | 118 | 15.7 |
| 3 | fastapi websocket reconnect handler | normal | 135 | 15.6 |
| 4 | docker compose health check restart policy | normal | 132 | 17.7 |
| 5 | git rebase vs merge workflow | zero_cascade | 0 | 0.0 |
| 6 | PostgreSQL query optimization composite in | captcha | 41 | 8.2 |
| 7 | react server components vs client componen | zero_cascade | 0 | 0.0 |
| 8 | nginx reverse proxy websocket configuratio | zero_cascade | 0 | 0.0 |
| 9 | transformer attention mechanism explained | zero_cascade | 0 | 0.0 |
| 10 | RLHF reinforcement learning human feedback | normal | 118 | 10.5 |
| 11 | vector database approximate nearest neighb | normal | 132 | 18.3 |
| 12 | RAG retrieval augmented generation benchma | normal | 113 | 13.9 |
| 13 | climate change carbon capture technology 2 | normal | 121 | 14.0 |
| 14 | epidemiology cohort study design methodolo | zero_cascade | 0 | 0.0 |
| 15 | Bewerbung Lebenslauf Format Deutschland | zero_cascade | 0 | 0.0 |
| 16 | Mietvertrag Kündigungsfrist gesetzliche Re | zero_cascade | 0 | 0.0 |
| 17 | GmbH Gründung Kosten Schritte | captcha | 40 | 8.0 |
| 18 | Krankenversicherung Vergleich gesetzlich p | zero_cascade | 0 | 0.0 |
| 19 | Python Programmierung Anfänger Tutorial de | normal | 135 | 13.6 |
| 20 | Datenschutz DSGVO Website Impressum | normal | 129 | 17.1 |

## Verdict

**REFUTED**

No significant elevation: captcha p99=1.4ms, zero_cascade p99=1.4ms vs normal p99=3.0ms.
CDP starvation hypothesis not supported. Alternative root cause required.

## New Observations From This Probe

Two findings that constrain the next hypothesis:

**1. Zero CDP events during zero_cascade queries.** CDP counter shows exactly 0 events for
every zero_cascade query (Q5, Q7-Q9, Q14-Q16, Q18). Chrome is completely silent — it is not
processing residual CAPTCHA page events in the background between queries. The event flooding
mechanism cannot operate during zero_cascade regardless; Chrome simply does nothing.

**2. Event loop is completely free during zero_cascade.** Scheduling latency p50=1.2ms,
max=1.4ms during zero_cascade — identical to normal queries. The event loop is not starved.
Any mechanism causing simultaneous RATE_SKIP of all 9 engines must be one that blocks
coroutines from being SCHEDULED despite the event loop being free — or one that is not
visible to the scheduling-latency canary.

**Combined constraint:** the zero_cascade mechanism operates without (a) CDP activity and
without (b) event loop starvation. It must be internal to the rate limiter or asyncio task
machinery.

## New Candidate Hypothesis

`RateLimiter.acquire()` (`rate_limiter.py:27`) uses `async with self._lock:` (line 30).
During backoff, the critical section looks like:

```python
async with self._lock:
    await asyncio.sleep(remaining_backoff_s)  # ← wait_for cancels here after 5s
```

When `asyncio.wait_for(limiter.acquire(), 5.0)` times out and sends CancelledError into
Google's acquire(), the `async with` context manager's `__aexit__` runs. If Python 3.14's
`asyncio.Lock.__aexit__` does not release the lock cleanly under cancellation (regression
or edge case), Google's lock stays locked. But Google's lock is per-instance (separate from
non-Google engines) — so this would only block future Google acquires, not CrossRef etc.

Alternative: `asyncio.wait_for` in Python 3.14 (running at `/opt/homebrew/Cellar/python@3.14/`)
may have subtle scheduling behavior where 9 concurrent `wait_for(immediate_coro, 5.0)` tasks
all report 5000ms rate_wait despite the inner coroutine being ready. One slow-callback event
captured at 17:48:51 — a `wait_for` task taking 58ms — may be a hint at ordering issues.

**Next probe target:** instrument `RateLimiter.acquire()` directly — add entry/exit timestamps
around the lock acquire and the token append — and run against zero_cascade queries to determine
whether non-Google engines' acquire() ever starts executing, or whether `asyncio.wait_for`
never schedules it.

## Next Steps

Pending:
- Direct instrumentation of `RateLimiter.acquire()`: timestamp lock-enter, token-append, lock-exit
  per engine per query — distinguish "acquire never started" from "acquire started but blocked".
- Check Python 3.14 asyncio.Lock cancellation behavior: does `__aexit__` release under
  `CancelledError` propagated via `asyncio.wait_for` timeout?
- If acquire never starts: the issue is task scheduling priority or `asyncio.gather` behavior
  when one task is long-lived (Google's asyncio.sleep(backoff_s)).
