# 71 — CoinDesk error-URL logic (deferred — post-backfill)

**Status:** PLANNED, deferred until after the 61k backfill. NOT implemented.
A prior session removed `remaining_urls.txt` in anticipation of this structured layer. TheBlock's
dead/failed-URL mechanism is the reference design.

## State as of this session

CoinDesk's riding scrape (`run_scrape_only`, proxy_riding branch) is **retry-everything**:
`load_scrape_entries` reads the inventory shards, `filter_new_entries` dedups against `raw/{hash}.html`,
scrapes the rest. A URL that fails (regwall / connect_fail / failed / caught in a stall-abort) gets NO
raw file → on the next run it is simply re-attempted. There is no dead/failed distinction, no permanent
exclusion, no error-URL file. The watchdog's `remaining_urls.txt` was removed in a prior session precisely
because it was a throwaway snapshot meant to be superseded by this layer.

## Why deferred (the design rationale)

CoinDesk runs a LEAN 5-min stall cutoff (vs TheBlock's 60-min). A URL that fails to scrape could be:
- genuinely dead (404/410 / permanently unreachable), OR
- a victim of the 5-min cutoff firing before a carrying proxy was found, OR
- a regwall the assigned proxy didn't carry (the same URL succeeds on a different IP).

At 5-min granularity these are NOT distinguishable. Marking such a URL "dead" now would wrongly exclude
retryable URLs from all future runs. TheBlock can mark dead/failed confidently because its 60-min window
gives the pool a full cooldown cycle — if nothing catches in that window, the URL is genuinely dead.
CoinDesk lacks that per-run confidence by design (it trades the long window for lean throughput).

## The plan (post-backfill)

After the main 61k backfill completes, the un-scraped remainder (inventory URLs still without a raw) is a
small, hard set. Run a re-pass over JUST those — with an INCREASED timeout / more pool cycles. URLs that
STILL don't catch under those relaxed conditions are genuinely dead/failed → record them in a structured,
persistent error-URL store (analogous to TheBlock's `dead_urls.txt` + `failed_urls.txt`, permanently
excluded from future dedup). This is the structured replacement for the removed `remaining_urls.txt`.

## Open questions

- The exact dead-vs-failed split for CoinDesk (origin 404/410 vs persistent-unreachable) and how the
  riding engine surfaces origin status — it currently maps everything non-ok to `"failed"`, with no
  origin-status channel.
- Where the error-URL files live after the inventory→discover rename lands — `discover/`.
- Whether the re-pass is a distinct CLI mode or just a relaxed-config run (`--browsers`/`--slots`/longer
  `stall_timeout_s`) over the remainder.
