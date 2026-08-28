# robots.txt + sitemap seed feeders (2026-08-28)

Milestone 1 of the URL-discovery redesign: the first two of the seed sources that will feed the
link-graph-traversal frontier (Milestone 0, `process-docs/url_discovery/2026-08-28_resume_state_preseed_probe.md`,
verified the frontier can be pre-populated at all). This milestone builds the robots.txt and
sitemap feeders only — no frontier wiring, no CLI, `crawl_site.py` untouched. Two findings from
Milestone 0 constrained the design directly: `resume_state["pending"]` bypasses crawl4ai's own
`FilterChain` entirely, so scope must be enforced by this code, not the crawler; and a malformed
`resume_state` fails silently, so feeder output needs its own explicit empty-vs-failed signal a
caller can check before trusting it.

Modules: `src/crawler/seed_feeders.py` (entry point, `robots_feeder_workflow`/
`sitemap_feeder_workflow`), `seed_feeders_constants.py`, `seed_feeders_scope.py`
(`FeederResult`, `normalize_url`, `scope_and_dedup`), `seed_feeders_robots.py`,
`seed_feeders_sitemap.py`.

## Not using crawl4ai's `AsyncUrlSeeder`

Read `venv/lib/python3.14/site-packages/crawl4ai/async_url_seeder.py` (`source="sitemap"`) before
deciding. Rejected on four grounds: (1) `_from_sitemaps` tries the conventional sitemap paths
BEFORE falling back to `robots.txt`'s `Sitemap:` lines — this milestone's scope decision requires
the opposite priority, robots-declared locations preferred; (2) it has no Allow/Disallow
extraction at all, and that disclosure is an explicit deliverable here; (3) it writes an on-disk
cache under `~/.crawl4ai/` as a side effect, unwanted for a feeder meant to be a pure function of
its input; (4) its `urls()` returns a bare list with no empty-vs-failed signal, and its internal
producer/worker/queue/BM25-scoring machinery is far harder to cover with local-fixture unit tests
than plain functions plus a mocked `httpx.AsyncClient` — this project's own established test
pattern (`dev/tests/test_marginalia_engine.py`). Direct parsing (stdlib `xml.etree.ElementTree`,
namespace-agnostic; `httpx.AsyncClient`) won on every axis that mattered.

`filter_nonsense_urls` (default `True`) is therefore moot — not used — but its default would have
been rejected even if the seeder had been used: it drops API paths and media files, which is wrong
for a feeder whose explicit goal is maximum coverage. Content-type filtering, if ever wanted, is a
downstream concern for whatever consumes the seed list, not this feeder's job.

## The normalizer: NOT `crawl_site.normalize_url`

The task that specified this milestone initially pointed at `crawl_site.normalize_url` as a
behavior worth carrying forward. That was corrected before implementation: `crawl_site.normalize_url`
strips the entire query string and cuts `@version` path segments. Both are wrong here. Stripping
the query merges `?page=2`/`?id=123`/`?lang=de` into one URL, permanently removing genuinely
different documents from a feeder whose whole purpose is maximum coverage. Cutting `@version`
segments is GitHub-Docs-experiment-specific logic living in a generically-named function; applied
to an arbitrary host it mangles a real path like `/@user` or `/package/@scope/name`.

The required reading for the correction was `process-docs/scrape_pipeline/landed_url_comparison_primitive_2026-08-06.md`
(`is_same_target`, a requested-vs-landed comparison primitive built for a different, POST-fetch
purpose). Its own same/different boundary — scheme/host case, leading `www.`, the scheme's default
port, empty path vs `/`, trailing slash, fragment, and `http` vs `https` all "same"; any query
difference "different" — does not transfer here unmodified, and the reason is a cost-model
inversion the correction note itself named: over-merging is safe for a BFS visited set (worst case:
refetch a page) or for a post-fetch same/different judgment (the page was already fetched
successfully either way), but a merged SEED is never fetched at all.

`seed_feeders_scope.normalize_url` therefore draws its own boundary, one dimension at a time:

| Dimension | Decision | Reasoning |
|---|---|---|
| Scheme casing (`HTTP://` vs `http://`) | Merge, rewrite to lowercase in output | RFC: scheme is case-insensitive; every HTTP client already lowercases it before the real request — zero risk of producing an unreachable URL. |
| Host casing | Merge, rewrite to lowercase in output | DNS is case-insensitive (RFC 4343); same zero-risk argument. |
| Default port (`:80` http, `:443` https) | Merge, strip from output | RFC 3986 §6.2.3: identical to no port at all — literally the same network destination, not a heuristic. |
| Fragment | Merge, drop from output | Never sent to the server under any circumstance — cannot affect what content-comparison purposes it might otherwise be relevant to. |
| Empty path vs `/` | Merge, canonicalize to `/` | RFC 3986 §6.2.3: an empty path is request-target `/` by specification — the identical HTTP request line either way. |
| `www.` vs apex | Merge FOR COMPARISON ONLY, output text untouched | The scope decision already settled this as a normalization concern, not a scope concern. But rewriting the host in the actual output risks producing a form the site does not actually serve (some hosts are strict about one form). Implemented as a separate `_host_key` helper used by both the scope filter and the dedup key; `normalize_url` itself never touches host spelling beyond casing. |
| Query string | Keep distinct, never touched | Explicit correction requirement — `?page=2` etc. can be a genuinely different document; no RFC identity exists to justify merging. |
| `http` vs `https` | Keep distinct | Unlike every merged dimension above, this is not a protocol-level identity — it is a common redirect CONVENTION that does not hold universally. The landed_url precedent could safely include it because that comparison runs POST-fetch, after a redirect (if any) already resolved the two to the same real content; a pre-fetch feeder has no such guarantee, and merging risks silently dropping a resource if the assumption fails for some host. |
| Non-root trailing slash (`/a` vs `/a/`) | Keep distinct | Same reasoning as scheme: not a proven identity. Some servers genuinely distinguish a file from a directory index at this exact boundary (REST list vs single resource, static file vs directory listing); the landed_url precedent's own inclusion of this case was justified post-fetch, not pre-fetch. |
| Malformed input (bad port, malformed IPv6, ...) | Drop the single URL, never raise | `scope_and_dedup` wraps `normalize_url` in `try/except ValueError`; one bad entry in untrusted sitemap/robots content must not fail the whole feeder run. `normalize_url` itself still raises when called directly (a pure function, callers decide whether to catch) — verified against the same `urlparse().port`-raises-lazily behavior the landed_url primitive's own verification session first found in CPython 3.14. |

Percent-encoding normalization (RFC 3986 §6.2.2.2, which the landed_url primitive itself
implements) was considered and left out — it wasn't in the correction note's required dimension
list, and adding it would be scope beyond the listed deliverables.

## Verification — real runs, no mocking

`docs.github.com`: `robots.txt` → 200, but its ONLY content is `User-agent: *` (confirmed by
direct fetch) — zero Allow/Disallow/Sitemap directives exist, so `robots_feeder_workflow` correctly
returns `ok=True, urls=[]` (0, not a bug: there is nothing to extract). `sitemap_feeder_workflow`
tried both conventional fallback paths (`/sitemap.xml`, `/sitemap_index.xml` — both confirmed 404
by direct fetch) and returned `ok=True, urls=[]` in 0.26s — the clean-empty outcome the milestone
required. (The task's own reference case additionally named `/sitemaps/sitemap-0.xml`, GitHub's own
non-conventional pagination path, not one of this feeder's two general conventions — confirmed
404 too, by direct fetch, so the empty conclusion holds regardless of which reasonable fallback
set is used.)

`theblock.co` (sitemap-index reference; `process-docs/news_pipeline/29_sitemap_devrun.md` recorded
64 `post_type_post` sub-sitemaps / 44,041 unique `<loc>` URLs via a proxy pool at concurrency 128
on 2026-06-14): reachable DIRECTLY in this environment today, no proxy needed — `robots.txt` (200,
real `Sitemap:` lines: `sitemap_tbco_index.xml` AND `sitemap_tbco_news.xml`, both consumed since
`sitemap_feeder_workflow` resolves every robots-declared sitemap, not just the first).
`sitemap_tbco_index.xml` is a real `<sitemapindex>`, 63 sub-sitemaps today (one level of nesting,
each sub a plain `<urlset>`). Full resolution of both robots-declared trees: 44,547 raw `<loc>`
URLs, 44,519 after `scope_and_dedup` (28 dropped — cross-tree duplicates between the `index` and
`news` sitemaps and/or a handful of off-host or malformed entries), completed in 4.89s at
`SITEMAP_FETCH_CONCURRENCY=8`. Same order of magnitude as the 2026-06-14 figure, not identical —
expected, since ~2.5 months of new articles separate the two measurements, and 44,519 > 44,041 is
consistent with organic growth, not a red flag. `robots_feeder_workflow` on the same host returned
8 real Allow/Disallow-derived paths (`/search`, `/api/`, `/preview/`, `/wp-json/`, `/ping`,
`/tbco/prebid.js`, `/_tbp/`, `/tbco/`).

No substitution was needed — `theblock.co` was reachable on the first attempt, unlike the proxied
run this milestone's reference case was drawn from.

## Verdict

Both feeders work end-to-end against real hosts, at both extremes of the expected outcome range
(a genuinely sitemap-less host returning a clean empty result; a 63-sub-sitemap index resolving to
~44.5k real URLs in under 5 seconds). `FeederResult.ok` is the caller's empty-vs-failed
discriminator: `ok=True` covers every documented "normal" outcome (missing robots.txt, a 404
sitemap, zero directives found), `ok=False` is reserved for genuine orchestration failure (checked
directly: an unparseable `seed_url` produces `ok=False` with a non-null `error`, never a silent
empty list indistinguishable from a real empty result).
