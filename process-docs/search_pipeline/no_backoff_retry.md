# No Retry-with-Backoff on External-Service Failure

**Bound principle for this project.** Documented because the pattern has been re-introduced into the codebase multiple times despite repeated removal — needs an explicit reference so future Worker / refactor passes can cite it when stripping it out again.

## Rule

When an external service (HTTP API, browser engine, RAG server, MCP tool, third-party endpoint) returns a failure — 429, 403, CAPTCHA challenge, server error, block, refused-connection, timeout — the code MUST NOT:

1. Sleep for an artificial delay before retrying.
2. Implement exponential backoff (`delay = base × 2^attempt`) or any other doubling / escalating wait formula.
3. Carry session-scoped state about which service "failed" — no "dead-for-this-session" flags, no skip-lists that grow during a run.

The code MUST:

1. **Record** the failure in logs / stats / structured status enum (e.g., `EMPTY_BLOCK`, `BLOCKED_CAPTCHA`, `HTTP_429`).
2. **Continue** with the rest of the pipeline — sibling parallel calls finish normally, the pipeline does not stall waiting for the failed service.
3. **Try again naturally** on the next legitimate invocation — the next user query, the next pipeline tick, the next session. Without artificial delay. Without remembering the prior failure.

## Why

Provider-side bot-detection / rate-limit state on systems like Google recovers over **minutes to hours** — not seconds. A 30s, 60s, or even 244s sleep does not change the provider's internal state. The retry produces the same error, the backoff doubles, and the next retry produces the same error again. The waiting is pure wallclock waste; the failure outcome is identical to fail-fast in 0 seconds. Concrete evidence: 2026-05-22 value_eval_probe run wasted ≈466s in backoff sleeps and produced zero Google results across 16 pairs — same outcome as zero-wait would have produced.

Session-state about failed services creates fragile coupling between unrelated user actions: a transient failure during a 9 AM batch should not silently skip an engine at 2 PM. The next natural invocation gives the provider its organic recovery window without our code modeling provider internals.

Sleep-on-failure also tends to recur in code because it *looks* like the safe / well-behaved thing to do. It is not. The reason it keeps coming back: each new Worker session that touches network code re-derives "we should be polite to the provider" as a heuristic and re-implements the same broken backoff. Hence this explicit rule.

## What Stays Allowed

- **Token-bucket pacing** for preventive rate management: sliding-window caps (e.g. 4 req/min) that pace OUTGOING requests to stay under known provider limits. This is rate-management before failure, not retry after failure. See `src/search/rate_limiter.py:39-51` (the `acquire()` token-bucket logic, which stays).
- **Watchdog timeouts** on individual calls (e.g. `asyncio.wait_for(call, timeout=N)`) to prevent a single stuck call from blocking a pipeline. Timeouts replace blocking calls with explicit failure — fail-fast, not retry-with-backoff. See `RATE_WAIT_TIMEOUT = 60.0` in `search_web.py` engine fanout.
- **Application-level immediate-retry** for genuinely transient failures (e.g., one TCP RST, one DNS hiccup): retry immediately, max 1 retry, no doubling delay. Failures that persist past one immediate re-try are real failures and go to the fail-fast handler.

## Anti-Pattern Catalog (Forbidden)

```python
# WRONG: exponential backoff
def backoff(self):
    delay = BASE * (2 ** self._attempt) + jitter
    self._backoff_until = time.monotonic() + delay
    self._attempt += 1

# WRONG: session-scoped "dead-engine" flag
if engine.name in self._known_failed_engines:
    return None

# WRONG: hard-coded sleep on failure
if response.status == 429:
    await asyncio.sleep(60)
    return await retry(request)

# WRONG: explicit delay between retry attempts
for attempt in range(5):
    try:
        return await call()
    except RateLimitError:
        await asyncio.sleep(2 ** attempt)
```

```python
# RIGHT: fail-fast, record, return
if response.status == 429:
    logger.warning("Service %s returned 429 for query %s", service, query)
    return None, Status.RATE_LIMITED

# RIGHT: record once, continue immediately
result, status = await call()
if status == Status.BLOCKED:
    stats.record(service=service, status=status)
    return [], status  # caller's parallel siblings continue, this slot is empty
```

## Scope

Applies to every external service call in this project: search engines (`src/search/engines/*`), RAG GPU services (cross-encoder at port 8082, embedding at 8084, splade at 8083), preview HTTP calls (`src/search/preview.py`), Crawl4AI calls (`src/scraper/*`), MCP tool invocations, any third-party endpoint.

As of 2026-05-22, the implementation state and code-cleanup recommendation targeted `src/search/rate_limiter.py` and its callers in `google.py`.

## History

- **2026-05-09 / 2026-05-21:** `RATE_WAIT_TIMEOUT=60s` cap added on `acquire()` calls (full cascade-fix history covered a session investigating asyncio-cascade starvation). This made the `acquire()` watchdog work as fail-fast for asyncio cascades; it did NOT remove the exponential backoff itself (`backoff()` still escalated `30 × 2^attempt + jitter` until 2026-05-22 rip).
- **2026-05-20:** validation run 2 documented the cascade mechanism — Google CAPTCHA + escalating backoff = same engine locked out across batch.
- **2026-05-22:** value_eval probe reproduced the cascade (4 backoffs, 466s wasted) → user-binding decision to remove the backoff entirely. This rule created as a result.
