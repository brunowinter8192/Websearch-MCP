# HN Dropped (2026-05-04)

**Engine:** `src/search/engines/hn.py` (deleted 2026-05-04)
**Dropped by:** Bruno verdict

**Reason:** HN Algolia's backoff behavior is rate-limit-cascade-hostile in the parallel engine architecture. Any query that yields 0 results (link-stories EMPTY, German queries, non-tech topics) triggers `limiter.backoff()` because `_wait_for_results` returns False on empty content — the engine cannot distinguish "rate limited" from "no matching content". In a 4-engine parallel gather, this compounds exponentially across consecutive empty queries (attempt 0: 34s → attempt 1: 63s → attempt 2: 125s → ...), effectively stalling the entire search gather on sequences of non-HN queries. Replaced by Stack Exchange API which returns empty result list cleanly without backoff penalty.
