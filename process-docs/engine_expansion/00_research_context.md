# Engine Expansion 2026-05 — Research Context & Deferred Items

Research pass and evaluation summary from the May 2026 engine expansion, which converged on a 9-engine set. Per-engine implementation history is in the sibling files in this folder.

## Research Pass (2026-05-01)

GitHub search for engines that extend the stack with technical bias, without new browser load.

**Stract** (StractOrg/stract, 2.4k Stars, active April 2026): Open-source web search engine with own index, Optics-system for ranking customization (domain boosts like github.com / *.readthedocs.io configurable), DDG-style !bang, Wikipedia + StackOverflow sidebar built-in. Self-description: "targeted towards tinkerers and developers". Hosted API at docs.stract.com. **Rejected** — commercial API access $27/month, out per user constraint.

**Marginalia** (MarginaliaSearch/MarginaliaSearch, 1.8k Stars, active April 2026): Self-description "Internet search engine for text-oriented websites. Indexing the small, old and weird web." Java stack, own crawler. README: "non-commercial share-alike is always free, commercial API licenses available". API-Key + per-Key rate-limiting in DB schema. User-facing API docs not present in docs.marginalia.nu repo. Self-hosting not practical — README specifies 32 GB RAM minimum + several TB storage. **Deferred** — try-or-drop probe at hosted endpoint `search.marginalia.nu` after HN+SE stabilization.

**HN Algolia API** (hn.algolia.com/api/v1): Free, no auth, no API key. Reference implementations: cyanheads/hn-mcp-server (Apache-2.0, April 2026), voska/hn-cli (Go, April 2026), wei/hn-mcp-server. Endpoints: `/search?query=` (relevance), `/search_by_date?query=` (recency). Filter via `tags` and `numericFilters`. Rate limit not prominently documented. **Added then dropped 2026-05-04** — backoff behavior made it rate-limit-cascade-hostile in the parallel engine architecture (see sibling drop rationale in this folder).

**Stack Exchange API** (api.stackexchange.com): Free. Python wrapper: lucjon/Py-StackExchange (active January 2026). 300 req/day anonymous, 10k/day with free registered key. **Added 2026-05-04** as the HN replacement.

**SearXNG** (searxng/searxng, 29k Stars): Pattern reference only — user removed SearXNG stack in engine-cut 2026-04-15 in favor of pydoll-direct architecture.

**Kagi-Skill** (hffmnnj/kagi-skill, 6 Stars): Exists as Claude skill for Kagi Search / Summarizer / FastGPT, but Kagi subscription is paid — out per user constraint (no paid subscriptions).

## Deferred Items

**Marginalia probe** — deferred, no concrete timeline. Try-or-drop at `search.marginalia.nu` when there is a specific use-case gap in the 9-engine pool (as of this expansion) (e.g. text-heavy / non-commercial / small-web queries underserved by Google/DDG/Mojeek). Open question: does a public endpoint exist without API key?

**Domain-boost layer** — deferred. SE and Lobsters already cover the relevant developer platforms directly; a re-rank heuristic is not needed while those engines source those domains.

## Open Questions (from expansion phase)

- SE API without key: 300 req/day — sufficient for agentic-search volume? Should a free registered key be added from the start?
- Marginalia hosted API: public endpoint without key? Clarifies on first HTTP probe.
- Engine dedup for discussion-aggregator results: HN/SE hits often lead to the same URLs as Google + additional discussion threads. `build_engine_pools()` dedup-by-position handled this correctly as of this expansion.

## Sources

- StractOrg/stract — Stract Search Engine (Repo, dropped: $27/mo commercial API)
- MarginaliaSearch/MarginaliaSearch — Marginalia Engine (Repo, deferred)
- MarginaliaSearch/docs.marginalia.nu — Marginalia Self-Hosting Docs (Repo)
- cyanheads/hn-mcp-server — HN MCP Reference Implementation (Repo)
- voska/hn-cli — HN CLI Reference (Repo)
- lucjon/Py-StackExchange — Stack Exchange Python Wrapper (Repo)
- searxng/searxng — Metasearch Pattern Reference (Repo)
- hffmnnj/kagi-skill — Kagi Claude Skill (Repo, dropped: paid)
