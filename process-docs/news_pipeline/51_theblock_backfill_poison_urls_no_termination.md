# 51 — The Block full backfill: poison URLs block termination (no per-URL attempt cap)

**Date:** 2026-06-17. **State:** run KILLED mid-grind; finding captured. Resolution deferred to a
separate The Block session.

## Symptom

`python -m src.news --source theblock --timeframe full` (started 2026-06-16 23:29 CEST, killed
~2026-06-17 20:45 after ~21h, PID 26470). Scraped 22,995 raw articles, then produced **no new scrape
for ~3h** while the proxy-rotation loop kept grinding — the event JSONL grew to 177 MB and was still
being written at kill time. Recent activity per 20k events: **~19,963 `fail` vs ~0 real article
successes** (the handful of `ok` were the 60-min GitHub proxy-source refreshes, not article fetches).

## Root cause (confirmed)

The loop terminates only when every queued URL resolves to `done` (content fetched) or `dead` (404/410
from origin). A residual set of **8 URLs** returns NEITHER — persistent `fail` (CF block or malformed
URL) — so they go to the back of the queue and are retried forever. There is **no per-URL attempt cap**.
`post/361500/...` was first attempted `2026-06-16T22:07Z` and was still failing 20.5h later. The queue
can never empty → the loop never terminates.

## Consequence (the real damage)

Cleanup + publish run only AFTER the scrape stage completes (monolithic scrape-all → clean-all →
publish-all in `run_pipeline`). Because the scrape never terminated, **the 22,995 raw HTML scrapes were
never cleaned and never published**: `data/news/theblock/clean/` is empty; the rag-cli `theblock`
collection is unchanged since the prior run (newest `2026-06-16 23:16`, 3953 files). The entire 21h run
sits as raw HTML in `data/news/theblock/scrape/`, unprocessed.

## A) The 8 stuck URLs (the open set — inspect manually)

| # | URL | Slug oddity |
|---|---|---|
| 1 | `post/128735/korea-crypto-exchange-%e2%80%8ecoinone-withdrawals-external-wallets` | `%e2%80%8e` = LTR mark (U+200E) |
| 2 | `post/193938/mexcs-view-are-cexs-the-answer-for-web3%ef%bc%9f` | `%ef%bc%9f` = fullwidth `?` (U+FF1F) |
| 3 | `post/258853/some-ftx-creditor-claims-rise-above-50%c2%a2-in-over-the-counter-deals` | `%c2%a2` = cent sign `¢` (U+00A2) |
| 4 | `post/356469/sec-casts-doubt-on-rex%e2%80%91osprey-bid-to-launch-staking-ethereum-solana-etfs` | `%e2%80%91` = non-breaking hyphen (U+2011) |
| 5 | `post/361500/metaplanet-plots-acquisition-spree-cash%e2%80%91generating-businesses-bitcoin-gold-rush` | `%e2%80%91` = non-breaking hyphen |
| 6 | `post/363595/trump-media-bitcoin-crypto%e2%80%91treasury` | `%e2%80%91` = non-breaking hyphen |
| 7 | `post/380746/bitmine-buys-44-million-ethereum` | **none — plain ASCII slug** |
| 8 | `post/71139/lithuanias-central-bank-is-releasing-lbcoin-%e2%81%a0-its-blockchain-based-digital-collector-coin` | `%e2%81%a0` = word joiner (U+2060) |

(All under `https://www.theblock.co/`. Full list also at `/tmp/theblock_stuck_urls.txt` at capture time.)

**Pattern:** 7/8 carry an unusual Unicode char in the slug; **#7 is a normal ASCII slug** that is also
stuck — so the cause is NOT purely encoding. Hypothesis: a mix of (a) mis-encoded/non-resolving URLs at
the origin (neither valid-200 nor clean-404) and (b) at least one genuinely CF-hard real article. To
verify: open each manually and observe what the origin actually returns.

## B) Fix direction (pending the manual URL inspection)

- **Per-URL attempt cap (primary):** after N failed attempts across distinct proxies, mark a URL
  `gap`/abandoned and drop it from the queue so the loop terminates. Makes "persistent-fail" a third
  terminal state alongside done/dead — the design currently assumes every URL eventually resolves to
  done or dead, which these 8 violate.
- **URL normalization (maybe):** if the Unicode slugs are mis-encoded on our side, fixing the encoding
  may make 7/8 fetchable. Decide after manual inspection.
- **Decouple downstream (architecture lesson):** monolithic scrape→clean→publish strands ALL output when
  the scrape can't terminate. Incremental/chunked publish (clean+publish as scrapes complete) would have
  preserved the 22,995. This is the same resumability requirement now being designed into the CoinDesk
  scrape job.

## Salvage

The 22,995 raw scrapes are on disk (`data/news/theblock/scrape/`). They can be cleaned + published
WITHOUT re-scraping (run cleanup+publish over the existing raw dir). Decide in the separate The Block
session.

## Status

Run killed (PID 26470, confirmed DEAD).

**Resolved (2026-06-18) — see the proxy-pool stall-termination entry.** The skip-mechanism (B)
is implemented as a global stall-detector in `loop.py`: no done/dead progress for one full pool cycle
(3600s) → terminate, open queue → `failed_urls.txt`. Chosen over a per-URL attempt-cap (bulk-safe by
construction, preserves a slow-but-progressing tail). Salvage of the 22,995 raw was done separately
(cleaner extension + production run in a later stage). The per-URL manual inspection (A) of the 8 poison URLs
remains optional; they now terminate cleanly into `failed_urls.txt` regardless.
