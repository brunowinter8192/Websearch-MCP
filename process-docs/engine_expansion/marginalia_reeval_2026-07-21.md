# Marginalia Search Re-Evaluation — Dev Probe (2026-07-21)

**Probe:** `dev/search_pipeline/30_marginalia_probe.py` (plain `httpx`, no browser/stealth stack)
**Report:** `dev/search_pipeline/md/marginalia_probe_20260722_003427.md`
**Prior status:** deferred in `process-docs/engine_expansion_2026-05/00_research_context.md` — "try-or-drop probe... open question: does a public endpoint exist without API key?"

## Verdict: CANDIDATE

A free public JSON API exists and requires no signup: `https://api2.marginalia-search.com/search?query=<q>&count=10`, header `API-Key: public` — a literal shared key string that works immediately with no email, no registration. Discovered via `api.marginalia.nu`, which redirects to the current API docs page (`about.marginalia-search.com/article/api/`); the actual API host is `api2.marginalia-search.com`.

## Cleanest integration path of all engines evaluated this expansion round

Marginalia needs NO browser and NO stealth stack at all — a plain `httpx` GET against a JSON endpoint. This mirrors the existing HTTP-API engine pattern (`crossref.py`, `openalex.py`, `stack_exchange.py`, `open_library.py`), not the pydoll-browser engine pattern (`google.py`, `startpage.py`, `brave.py`, `bing.py`, `yandex.py`). A future wiring milestone should follow the httpx-API engine shape, not the browser-engine shape.

## Framing: new coverage, different axis

Distinct from every other engine evaluated this expansion round. Bing/Startpage are redundancy paths to indexes already represented (Bing's own index / Google's index). Yandex is new coverage on the same general/mainstream axis as Google/Bing. Marginalia is new coverage on a genuinely DIFFERENT axis: its own independent crawler explicitly targeting "the small, old and weird web" — indie blogs, personal essays, non-commercial text-heavy content — a category none of the other engines in the pool are optimized for.

## Quality, called honestly per axis

- **Niche/text-heavy axis (Marginalia's stated strength) — excellent, 4/5 OK.** `unix philosophy essay` → `tedinski.com`, `ssp.sh` (personal blog), `blog.korny.info`, `xahlee.info`. `self hosting guide` → `noted.lol`, `lemmy.funami.tech`, `cprimozic.net`. `plain text accounting` → `forum.plaintextaccounting.org`, `plaintextaccounting.org`, `tech.stonecharioteer.com`. These are genuinely distinct indie-web hits from what Google/Bing/Yandex surfaced for comparable topics earlier this week — real evidence the different-axis framing is correct, not just a claim.
- **Mainstream/local axis — honestly mixed, not uniformly bad.** `gebrauchte waschmaschine frankfurt` (German local-business) returned results with ZERO relevance — German-grammar-textbook PDF download sites, no local businesses at all. This is a genuine, complete miss on non-English local-commercial intent, and is reported as such, not softened. By contrast, `climate change carbon capture technology 2025` (Wikipedia, IPCC PDF reports) and `how does DNS work` (relevant personal-blog explainers) came back reasonably relevant — English-language mainstream/informational queries are not automatically a bad fit, only the non-English local-commercial case was a clear failure.

## Key operational caveat: the shared public key rate-limits for real

2 of 10 queries returned a genuine HTTP 429, confirmed via the actual status code (not an inferred text marker) — matching the API docs' own warning that the public key "often hits a rate limit." This is a SHARED quota across every caller of the literal `public` key worldwide, not a per-integration allowance. The docs describe two paths for anyone building on this API long-term: continue using the shared `public` key (zero setup, but contended by unrelated global traffic) or email `contact@marginalia-search.com` for a personal free non-commercial key with a dedicated quota. This choice, plus a graceful `429 -> empty` handling contract (mirroring how every browser-scraped engine this week handles its own block condition), is the concrete decision point for a future wiring milestone — not resolved here, since this was a scrapeability probe, not a wiring task.

## Self-corrected bug during this probe

An earlier version of the probe misclassified the `api-event-type: Cached` response header as a rate-limit signal, when it is in fact a benign cache-hit state observed on ordinary successful responses. This was caught by inspecting the actual header value on a query that clearly should have succeeded, and fixed to rely on the real HTTP status code (429) as the block signal before the report was finalized — the committed report and script reflect the corrected logic, not the initial misdiagnosis.

## Latency

Fastest of every engine probed this expansion round: min=53ms, median=74ms, max=1430ms (10/10 ≤5s) — expected, given there is no browser/rendering overhead at all, only a direct JSON API call.
