# 60 — TheBlock full backfill run + raw-as-gate diff model

**Date:** 2026-06-18. **State:** backfill run launched (in progress at session close); scrape→raw migration done.

## scrape/ → raw/ migration (one-time)

The 22,995 pre-existing raw HTML files lived in `data/news/theblock/scrape/` (the old pre-decoupling location). As of 2026-06-18, the pipe dedups against `data/news/theblock/raw/` — `filter_new_entries(..., mode="raw")` checks `raw/{hash}.md` existence. `raw/` did not exist → a `--timeframe full` run would have found raw/ empty and re-scraped all ~26,955 discovered URLs from scratch.

Fix: directory rename `scrape/` → `raw/`. The files are named `{sha256(url)[:12]}.md` — identical to the convention `filter_new_entries` and the proxy `content_handler` use — and hold raw HTML, format-identical to what `content_handler` writes. The rename makes the 22,995 recognized as already-fetched. No `manifest.jsonl` was present in scrape/; dedup is pure file-existence so this is irrelevant (a manifest is appended for newly-scraped entries going forward).

## Recurring run model = `--timeframe full` (scrape-from-master rejected)

The standing real run is `python -m src.news --source theblock --timeframe full`: fetch the sitemap index, pull ALL `post_type_post` subs, union-append new URLs into `discover/master_urls.txt`, dedup the discovered set against `raw/` (+ failure exclusion), scrape the gap, clean-pass into the rag collection dir. `full` auto-skips rag-index (`__main__.py` sets `skip_index=True` for non-delta timeframes): the run scrapes+cleans, then the user runs `rag-cli index --collection theblock` after review.

A "scrape-from-master" mode (read `master_urls.txt`, diff against raw, scrape without re-discovery) was considered and REJECTED — the recurring run wants fresh sitemaps to catch new articles, and `full` already subsumes both the backfill (gap = unscraped) and new-article pickup. `master_urls.txt` therefore stays a discovery artifact (write + union-self-read only), not a scrape input.

## Raw-as-gate diff model

`raw/{hash}.md` existence is the universal "already-fetched" gate. Three terminal classes interact with it differently:

| Class | Fetched? | Raw file? | Diff exclusion |
|---|---|---|---|
| dead (404/410 origin) | no | no | needs `raw/dead_urls.txt` — no raw to gate it |
| failed (60min stall gap) | no | no | needs `raw/failed_urls.txt` — no raw to gate it |
| body-less (fetched ok, no articleBody) | yes | yes | gated by raw automatically — never needs a list |

dead+failed require the explicit exclusion lists because they have no raw file to skip them; body-less URLs DID fetch successfully (status ok, raw written) and are skipped forever by raw-existence. The body-less log (`clean/bodyless_urls.txt`) is therefore pure diagnostics — scraping does NOT read it. Deleting a body-less article's (absent) clean MD from the rag collection does NOT trigger re-scrape, because the diff checks `raw/`, not the rag clean dir. If a body-less raw is in truth a proxy junk page, the manual recovery is: delete that `raw/{hash}.md` → it re-enters the next `full` diff.

## Pending (as of 2026-06-18)

The full backfill run was launched this session (~3,960 expected gap = discovery 26,955 − raw 22,995). Pending verification:
1. Inspect the job report MD under `data/news/theblock/proxy_pool_jobs/<job_id>/`.
2. If clean → `rag-cli index --collection theblock`.

The failures-exclusion is a no-op for this first run — no dead/failed lists existed at its dedup time, they are created during it — and takes effect from the second run.

## Relationship to prior work
- Raw-only decoupling (cleanup removed from pipe). Superseded for cleanup by later work re-wiring clean-pass into the proxy_pool path; only indexing stays decoupled.
- Single master list, later relocated into `discover/`.
- proxy_pool stall termination → source of `failed_urls.txt`.
- In-pipe clean-pass (body-less log → `clean/bodyless_urls.txt`).
- Failure-URL diff exclusion.
