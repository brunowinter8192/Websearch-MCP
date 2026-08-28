# resume_state Pre-Seeding Probe (2026-08-28)

The planned redesign of the capture pipeline's URL-discovery step uses link-graph traversal as
the frame, with robots.txt/sitemaps/framework-nav-tree sources feeding seed URLs into the
traversal frontier before traversal starts. The whole design rests on one assumption: that
`crawl4ai`'s `BFSDeepCrawlStrategy` can have its frontier pre-populated with an arbitrary URL set
via the `resume_state` constructor parameter, instead of starting from a single seed URL. Source
reading (`crawl4ai/deep_crawling/bfs_strategy.py`, `crawl4ai` 0.9.2) suggested `resume_state` was
the hook, but the assumption had never been executed. This entry records four small, real runs
against `books.toscrape.com` (static, stable, low request volume — 8 real page fetches total
across all four experiments) that verify it.

Probe script: `dev/url_discovery/01_resume_state_probe.py`.

## Result 1 — the pending set gets crawled; start_url is dropped, not collided

`resume_state={"pending": [{"url": u, "parent_url": None} for u in [travel_url, mystery_url,
philosophy_url]]}`, `max_depth=0`, `start_url` set to the site's real homepage. Result: all 3
pending URLs came back with `success=True status=200`; the homepage did NOT appear among the
results (`start_url_crawled: False`). Both `_arun_batch` and `_arun_stream` gate their entire
initialization on `if self._resume_state:` — the `start_url` parameter passed to `.arun()` is
never referenced anywhere in the resume branch. So when `resume_state` is truthy and non-empty,
`start_url` is silently DROPPED, not crawled and not merged/deduplicated against the pending set.

## Result 2 — exact resume_state shape, and two silent-failure shapes

Three subtests, all at `max_depth=0`:
- **Minimal correct shape:** `{"pending": [{"url": ..., "parent_url": ...}]}` — no `"visited"`,
  `"depths"`, or `"pages_crawled"` keys needed; the strategy's `.get()` defaults cover all of
  them. 1 result, success.
- **Wrong key** (`{"seed_urls": [...]}` instead of `"pending"`): the dict is truthy so resume mode
  IS entered, but `current_level` is built from `resume_state.get("pending", [])`, which finds
  nothing. 0 results, no exception. `start_url` is also not used (resume mode was entered). A
  silent empty crawl.
- **Empty dict** (`resume_state={}`): falsy in Python, so `if self._resume_state:` takes the FALSE
  branch and the strategy falls back to a plain single-`start_url` crawl as if no `resume_state`
  had been passed at all. 1 result — the homepage, not any pending URL (there were none). This is
  a real footgun for a caller: an empty-seed-list path that naively builds `resume_state = {}`
  gets silent single-URL behavior instead of an empty crawl or an error.

Required shape for real pre-seeding: a non-empty dict with a `"pending"` key holding a list of
`{"url": ..., "parent_url": ...}` dicts. `"visited"`, `"depths"`, `"pages_crawled"` are optional
and default to empty/0.

## Result 3 — depth bookkeeping honors an explicit "depths" entry; unstamped URLs default to depth 0

Single seed (`mystery_url`), `max_depth=2`, two variants:
- **A — pre-stamped:** `resume_state["depths"] = {mystery_url: 2}`. The seed result carries
  `depth=2`; link discovery computed `next_depth = 3 > max_depth(2)` and returned early — 0
  children discovered (captured via the next BFS level size in the `on_state_change` state).
- **B — depths omitted:** the seed result carries `depth=0` (the `depths.get(url, 0)` default);
  link discovery computed `next_depth = 1 <= max_depth(2)` — 73 children discovered, each freshly
  stamped `depth=1` in the captured state's `depths` dict (sample value checked directly).

So `max_depth` is applied relative to whatever the `"depths"` dict says for an injected URL, and
an injected URL NOT listed in `"depths"` is silently treated as depth 0 — i.e. as if it were a
fresh BFS root, not as "continuing" from wherever its real position in the link graph might be.
A caller that wants correct depth-relative `max_depth` behavior for pre-seeded URLs MUST supply
their intended depths explicitly; omitting them does not error, it just resets them to 0.

(Caveat on the measurement itself: Variant A's "0 children" comes from the captured
`on_state_change` state, which only exists if the callback fired. It did fire here — the seed
fetch succeeded, and `on_state_change` runs whenever `result.success` is `True` regardless of what
`link_discovery` found — so this particular `0` is a real "no children" result. The conclusion
does not depend on it either way, since the seed's `depth=2` was also observed directly on the
fetched result. But the probe's `.get(..., {}).get(..., [])` read has no explicit assertion that
the callback ran, so the same code shape would misreport a callback-never-fired case as "0
children" too.)

## Result 4 — injected seeds bypass the FilterChain; the same URL rediscovered as a child does not

Single seed (`philosophy_url`), `filter_chain = FilterChain([URLPatternFilter(patterns=
"*philosophy_7*", reverse=True)])` (rejects any URL containing `philosophy_7`), `max_depth=1`.
The seed itself matches the blocking pattern. Result: the seed was still fetched successfully
(`success=True status=200`) — `can_process_url`/the filter chain is never called on the top-level
`"pending"`/`current_level` URLs at all in either `_arun_batch` or `_arun_stream`, only on links
discovered FROM a result via `link_discovery`. The philosophy category page happens to link back
to itself (the sidebar's active-category entry resolves, via relative-URL normalization, to the
exact same absolute URL as the seed) — and that rediscovered self-link WAS rejected: it is absent
from the 62 children in the captured next-level state, and `filter_chain.stats` showed
`total=63 passed=62 rejected=1`. So a `"pending"`-injected URL bypasses the `FilterChain` the same
way `can_process_url`'s own docstring says a depth-0 `start_url` does; the same URL discovered a
second time as a child of itself is subject to the full chain like any other link.

## Verdict

The pre-seeding assumption HOLDS, under one constraint: `resume_state` must be a non-empty dict
shaped `{"pending": [{"url": ..., "parent_url": ...}, ...], "depths": {...}}` (depths supplied
explicitly if depth-relative `max_depth` behavior matters for the injected set) — passed alongside
any `start_url` value, which is then silently ignored rather than merged in. Both silent-failure
shapes (wrong key, empty dict) produce no exception, so a seed-feeder building this dict needs its
own validation that `"pending"` is present and non-empty before handing it to the strategy.
