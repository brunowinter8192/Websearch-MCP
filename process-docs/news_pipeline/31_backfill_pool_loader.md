# 31 — Backfill Pool Loader (22k Top-13 Repos)

## What we did

Built the 22k-candidate backfill proxy pool into `curated_sources.py` and wired a
`--pool` CLI flag into `acquire_pipe.py`. The pool selection (curated vs backfill)
uses the top-13 survey repos by CF-passability rank; this session
implements the loader and verifies the pool size.

## Design

**Format unification via `_fetch_roosterkid` / `_IP_PORT_RE`:**
All 9 new repos are parsed by the existing `_fetch_roosterkid(proto, url)` helper,
which applies `_IP_PORT_RE = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}:\d+")` to every
line. This regex extracts `host:port` correctly from all three format variants:
- Bare `host:port` — direct match
- Scheme-prefixed `http://host:port` (dpangestuw) — match after scheme
- Decorated `host:port:Country` (zloi-user) — match on first IPv4:port token

No new fetch helper was needed. `_fetch_bare_txt` vs `_fetch_roosterkid` distinction
is now: _bare_txt is fine-tuned for files where every line IS `host:port` (strict);
_roosterkid is the robust universal extractor for any format. Both produce identical
output on clean bare files.

**New constants (INFRASTRUCTURE):**
9 `*_SOURCES` lists covering the 9 new repos, following existing pattern.
r00tee uses capitalized filenames (`Https.txt`, `Socks4.txt`, `Socks5.txt`) — preserved
exactly as verified live.

**New loaders (ORCHESTRATOR):**
9 `load_*_proxies()` functions, each iterating its `*_SOURCES` list via
`_fetch_roosterkid` + `_merge_dedup`. Pattern identical to `load_roosterkid_proxies`.

**`load_backfill_pool()` (ORCHESTRATOR):**
Calls `load_monosans_proxies()` directly (already imported) + 12 loader functions
via a loop, collects into one flat list, applies a single `_merge_dedup` at the end
for cross-repo deduplication. Each individual loader already deduplicates internally;
the final dedup only eliminates cross-repo duplicates. proxifly excluded (rank 15,
below survey cutoff).

**`acquire_pipe.py` change:**
`acquire_pipe_workflow(concurrency, pool_name="curated")` — new `pool_name` parameter.
`--pool {curated,backfill}` argparse choice (default `curated`). Pool selection:
```python
pool = load_backfill_pool() if pool_name == "backfill" else load_curated_proxies()
```
Default stays `curated` — all existing dev-runs remain unaffected.

## Verification results

Run via standalone script (no proxy fetching, no acquire loop):

| Repo | Pre-merge count |
|---|---|
| monosans | 71 |
| roosterkid | 218 |
| databay-labs | 1,229 |
| TheSpeedX | 7,881 |
| themiralay | 127 |
| r00tee | 15,442 |
| iplocate | 2,041 |
| sunny9577 | 1,447 |
| ALIILAPRO | 4,852 |
| dpangestuw | 10,328 |
| Zaeem20 | 1,685 |
| zloi-user | 1,705 |
| hookzof | 879 |
| **Total raw** | **47,905** |
| **load_backfill_pool() unique** | **22,723** |

Cross-repo dedup rate: 47,905 → 22,723 = 52.6% unique (47.4% cross-repo overlap).
Dominant sources by raw size: r00tee (15,442), dpangestuw (10,328), TheSpeedX (7,881),
ALIILAPRO (4,852). After dedup, overlap between these large repos absorbs roughly half
the raw volume.

**~22k target confirmed: 22,723 unique.**

## Decision / next

The backfill pool loader is complete. Next step: run the 64-sub-sitemap loop with
`--pool backfill` to measure B-per-proxy and fail/success ratio on the 22k pool.
That is the proxy-economics measurement that determines whether the backfill wall-time
is tractable (open point as of this stage).
