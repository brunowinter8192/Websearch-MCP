# The pacing measurement this area could not take before the fixture existed (2026-09-05)

Continues the `url_discovery` area, closing the specific open item
`2026-08-28_fetch_success_and_frontier_visibility.md` recorded: the "before" for
`TRAVERSAL_MEAN_DELAY_S`/`TRAVERSAL_MAX_RANGE_S`/`TRAVERSAL_CONCURRENCY` was solid (a real
instrumented run against `docs.github.com/de/rest`, 101 successes against 682 failures out of 783
attempts, dominated by real `429`s and 168-byte anti-bot stubs), but the "after" could never be
taken — this project's OWN repeated diagnostic testing pushed GitHub's rate limiting for this
environment's IP into a sustained penalty, confirmed directly: even 3 isolated, minimal-volume
single-page fetches kept returning `429` long after the offending burst, and a 20+ minute paced run
stalled without completing. That milestone's verification was recorded as partial for that reason
alone, and named exactly what would have made the measurement takeable: a target that produces
rate limiting on demand. `2026-09-05_fixture_site.md`'s fixture is that target. This entry is the
measurement that milestone could not finish.

## The fixture's rate limiting had to change first, and why

The fixture's 429 mode, as M1 built it, was an absolute counter: after N total requests, every
subsequent request gets 429, permanently. That shape cannot distinguish a well-paced caller from a
badly-paced one — both eventually send N total requests and both trip it identically, with no way
back. `dev/url_discovery/_fixture_site.py`'s rate-limit mode was replaced with a genuine sliding
window (`/_control/rate_limit?limit=M&window=T`: at most M requests in the trailing T seconds,
pruned lazily, recoverable once a caller slows down) — the property real per-domain pacing actually
needs to be checked against. Verified directly: `limit=3,window=1` let 3 requests through, blocked
the 4th and 5th, then allowed a fresh request again after the window cleared.

## The threshold is invented, and that is stated plainly, not left implicit

Window=4s / limit=8 was derived from the two compared configurations' own `mean_delay`/`max_range`
specifications, before any run: current production (`base_delay=(1.0,1.5)`) implies
[0.667,1.0] req/s, i.e. [2.67,4.0] requests in 4 seconds; crawl4ai's own defaults
(`base_delay=(0.1,0.4)`) imply [2.5,10.0] req/s, i.e. [10.0,40.0] requests in 4 seconds. 8 sits
strictly between 4.0 and 10.0, with margin on both sides. **This number does not come from any real
host.** It is a value this project chose to sit between two specifications, computed before running
anything specifically so the measurement could not be adjusted after seeing an inconvenient result.
What it establishes is the *relative* ordering between configurations under one fixed, arbitrary
yardstick — never an absolute claim that a given configuration is safe against a real WAF, which no
local fixture can support.

## Two vendor-source findings, the reason the pipe_scraper values never transferred

Read directly, not assumed, from `venv/.../crawl4ai/async_dispatcher.py` and
`deep_crawling/bfs_strategy.py`:

1. **A fresh `RateLimiter` per BFS level.** `bfs_strategy.py:253` clones the config
   (`deep_crawl_strategy=None`) before each level's own `arun_many` call, and `arun_many`'s
   `dispatcher is None` branch builds a brand-new `MemoryAdaptiveDispatcher`/`RateLimiter` for that
   call. `RateLimiter.domains` — the exponential-backoff state (`current_delay`/`fail_count`)
   built up from 429s — lives on that instance. Backoff earned during one BFS level is discarded
   before the next level's fresh `RateLimiter` starts, back at the plain base delay with no memory
   of the trouble.
2. **`RateLimiter.wait_if_needed` has no lock around its read-sleep-write sequence.**
   `DomainState.last_request_time`/`current_delay` default to 0; concurrent tasks can read the SAME
   stale `last_request_time` before any of them writes it, sleep for approximately the same
   duration, and wake up together. `pipe_scraper_pacing.py`'s own `_gate_domain` serializes this
   exact sequence via `async with state['lock']` — crawl4ai's mechanism has no equivalent. This is
   the concrete reason `CONCURRENCY_PER_DOMAIN=8`, measured for the LOCKED mechanism
   (`process-docs/pipe_scraper_hardening/2026-08-04_stealth_concurrency_probe.md`, 0×429 across 316
   URLs), did not transfer to this module's UNLOCKED one — the number looked reusable and was not.

**Direct evidence of the burst, not inference.** A diagnostic run (non-blocking window, raw
request-arrival timestamps read back from the fixture) at `semaphore_count=8`: **7 of the first BFS
level's 15 requests arrived within 11ms of each other** — a real cluster, not the claimed ~1 req/s
per-domain cadence.

## The curve: four points, and the one that is not reproducible is the answer

Same derived threshold (window=4s, limit=8), same `mean_delay=1.0`/`max_range=0.5`, 4 repetitions
per `semaphore_count` value:

| `semaphore_count` | pages fetched (4 runs) | total URLs (4 runs) | wall time (mean) | reproducible? |
|---|---|---|---|---|
| 1 | 15, 15, 15, 15 | 18, 18, 18, 18 | 30.2s | yes |
| 2 | 14, 14, 14, **8** | 18, 18, 18, **12** | 23.5s | **no** |
| 4 | 7, 7, 7, 7 | 13, 13, 13, 13 | 14.7s | yes |
| 8 | 3, 3, 3, 3 | 13, 13, 13, 13 | 10.3s | yes |

`semaphore_count=1`, `4`, and `8` are each perfectly reproducible across their own 4 runs. `2` — the
one value that looked like a cheap middle ground — is not: 3 of 4 runs land close to `1`'s good
outcome, the 4th collapses to nearly `4`'s degraded one. This is not a graded curve with a soft
knee; it is a cliff, because `semaphore_count=1` is the only value that cannot race at all (never
more than one coroutine inside `wait_if_needed` at a time, by construction) — anything ≥2 exposes
the same lock-free race, and at `2` it fires unpredictably rather than consistently. An
unpredictable configuration is worse for a coverage-focused caller than a slower, predictable one,
because a caller cannot plan around a coin flip.

Cost per confirmed fetch (wall time ÷ pages fetched, mean) closes the argument on its own terms:
`1`≈2.01s, `2`≈1.88s (across its own inconsistent results), `4`≈2.10s, `8`≈3.43s. Going from
concurrency 1 to 4 is not an efficiency trade — it is not buying speed per confirmed page, it is
only failing faster. `8` is worse on both coverage and efficiency simultaneously.

## Decision

`TRAVERSAL_CONCURRENCY`: `8` → `1`. `TRAVERSAL_MEAN_DELAY_S`/`TRAVERSAL_MAX_RANGE_S`: unchanged —
held constant across every configuration in the curve above, and `semaphore_count=1` with those
SAME two values reached 15/20 pages fetched reproducibly, so the delay values were never shown to
be the problem. No flag, no env var, no per-caller override.

## The wall-time arithmetic this decision rests on — arithmetic from the configured values, not a measured run

Not measured, and not claimed as measured: at `semaphore_count=1`, each page's own delay is drawn
from `base_delay=(mean_delay, mean_delay+max_range)=(1.0s, 1.5s)`, and strict serialization means
that cost is paid once per page, not amortized across concurrent slots. For N pages: N×1.0s to
N×1.5s. A 300-page site: 300s to 450s — **five to seven and a half minutes**. A 1000-page site:
1000s to 1500s — **about seventeen to twenty-five minutes**. Real per-page fetch/render time and
the (separate, unpaced) feeder phase add a small amount on top of this floor, not measured at this
scale. This is the number that decides whether `semaphore_count=1` ever needs revisiting — not
this fixture's own 20-page wall time (24-36s), which is too small to say anything about whether a
real, hundreds-of-pages run would take long enough to be abandoned or hit a session limit, a real
cost this fixture cannot measure directly but which this arithmetic bounds.

## The unpaced feeder phase — a separate, real, now-recorded finding

All three feeders' own `httpx` requests (robots.txt, sitemap resolution including the nested
index, navtree plus its version union — 9 requests total) arrive within roughly 6 milliseconds of
each other, confirmed by the same timestamp diagnostic used for the traversal burst above. This is
unrelated to and unaffected by `TRAVERSAL_MEAN_DELAY_S`/`MAX_RANGE_S`/`CONCURRENCY` — feeders never
construct a `CrawlerRunConfig` at all, they call `httpx.AsyncClient` directly with no pacing
whatsoever. It is the largest single unpaced burst anywhere in this path, tighter and larger than
even the `semaphore_count=8` traversal burst it was compared against. **It is what the residual
failures at `semaphore_count=1` trace back to**: of the 2 pages `semaphore_count=1` still failed to
fetch (beyond the one genuinely-404 robots seed, which fails regardless of pacing), both are
sitemap-sourced seeds fetched early in the traversal, immediately after the feeder burst had
already partially consumed the shared rate-limit window — confirmed by identity, not inferred.
Out of scope to fix here (`discovery.py`'s three named constants govern the traversal only, not
the feeders), but it is now on record so the next reader does not have to rediscover it.

## Verification

`./venv/bin/python3 -m pytest dev/tests/test_discovery.py dev/tests/test_seed_feeders.py` after the
concurrency change: 106 passed, unchanged, no test edited. Full suite, run twice: 376 passed both
times. Nothing broke — but the cost is real and reported plainly, not absorbed silently: the full
suite's wall time roughly doubled (~22s → ~53.6s/~50.8s), and `test_discovery.py`'s own
fixture-backed section alone went from ~10.7s to ~40.9s, because its shared `discover_urls_workflow`
fixture run is now fully sequential — a direct, expected, and now-explained consequence of
`TRAVERSAL_CONCURRENCY=1`.
