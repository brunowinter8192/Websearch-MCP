# Framework navigation-tree seed feeder (2026-08-28)

Milestone 2 of the URL-discovery redesign: the third and last seed feeder, alongside M1's robots.txt
and sitemap feeders (`process-docs/url_discovery/2026-08-28_robots_sitemap_seed_feeders.md`). Reads
a site's own navigation tree out of the payload its frontend framework embeds in the served HTML —
on `docs.github.com/de/rest`, the primary benchmark for the milestone after this one, this is the
ONLY feeder that returns anything at all (M1 confirmed both sitemap paths 404 and robots.txt carries
only `User-agent: *`), so this feeder's coverage directly caps what that milestone can reach.

Module: `src/crawler/seed_feeders_navtree.py` (334 LOC), wired into `seed_feeders.py` as
`navtree_feeder_workflow(seed_url) -> FeederResult`.

## Detection: two payload shapes, one extensible dispatch list

Read `process-docs/agentic_discovery/01_gh_live_experiment.md` (the 2026-05-31 experiment that
produced the 305 figure) and `process-docs/news_pipeline/44_coindesk_timeline_api_pagination.md`
(records that a Next.js App Router site's payload can arrive as an RSC stream instead of the older
`__NEXT_DATA__` blob) before designing this. `extract_payloads(html)` tries an ordered list of
extractor functions, each returning a list of parsed JSON payload documents or `[]`; the first
non-empty result wins. Two extractors exist:

- `_extract_next_data_payloads` — the classic Pages Router shape: one `<script id="__NEXT_DATA__">`
  JSON blob.
- `_extract_rsc_stream_payloads` — the current App Router shape: a series of
  `self.__next_f.push([1, "<row>..."])` calls. All decoded chunks are concatenated BEFORE splitting
  into `<hexId>:<value>` rows (a row's content is not guaranteed to end on a push-call boundary);
  each row's value is parsed as JSON independently, and rows that fail to parse (`I[...]` import
  references, `HL[...]` hint rows) are skipped, not an error — they never carry page data.

A further framework's payload shape is added by appending one function to the dispatch tuple — no
restructuring of anything downstream, which only ever sees the resulting payload list.

## Walking the tree: structural shape, not a fixed key path

`find_navigation_tree(payloads)` never hardcodes a path like `props.pageProps.mainContext.sidebarTree`
(the exact path the 2026-05-31 experiment needed one inspection pass to find manually). Tier 1
searches every payload document, recursively, for the LARGEST dict subtree shaped `{url-key: str,
children-key: [dict, dict, ...]}` — `href`/`url` as candidate url-key names, `childPages`/
`children`/`items`/`pages`/`navigation`/`nav`/`subitems` as candidate children-key names, matched by
presence and shape (a non-empty list where every item is itself a dict), never by which one specific
name a given site happens to use. Verified this finds GitHub's `sidebarTree` (254 hrefs) with zero
hardcoded path, automatically, alongside 111 other far-smaller structural false-candidates in the
same blob (breadcrumbs, feature-flag objects, etc.) that the "largest" rule correctly ignores.

**A rendered React element is a real false-positive risk this rule had to be built to reject, not a
theoretical one.** React Server Components serialize an element as `["$", tagName, key, propsDict]`
— a 4-item LIST. A `<button>` with an icon and text renders as `{"href": "/prev", "children":
[["$","svg",...], ["$","span",...]]}` — structurally "has href + a children list", matching a loose
shape check. Verified live: an early version of this rule (checking only `isinstance(value, list)`)
matched 11 such rendered-DOM false positives on `ui.shadcn.com/docs`'s real RSC payload before the
stricter check (`all(isinstance(c, dict) for c in value)` — a React element list's items are
themselves lists, never dicts) was added.

**Tier 2 fallback**, used only when tier 1 finds zero hrefs anywhere: a flat scan for every
`href`/`url` string value anywhere in the payload, regardless of container shape, filtered to drop
empty/fragment-only values and Next.js's own `/_next/` internal build-asset paths. This is the case
a pure-DOM-rendered App Router page (no separate structured nav-data prop) hits.

## Version union: read from the same payload, not guessed

A versioned site (per the 2026-05-31 experiment: GitHub's FPT/GHEC/GHES) exposes its version list
inside the same payload as the tree. `_find_version_list` searches generically (any key containing
"version" whose value is a dict of 2+ dicts) rather than hardcoding `allVersions`. For each OTHER
version found (the current page's own tree is already in hand, never refetched), a version root URL
is built from two more generically-found sibling fields — `currentVersion` and a "path without
language" field (`currentPathWithoutLanguage` on GitHub) — and fetched, with the same detect+walk
pipeline applied to each. Every harvested URL is canonicalized — a matching `version_key` path
SEGMENT is stripped, wherever it falls in the path (after a language prefix, e.g.
`/de/enterprise-cloud@latest/rest` → `/de/rest`) — before the union, so a page listed under multiple
versions counts once. This canonicalization is deliberately kept in this module, not pushed into
`seed_feeders_scope.normalize_url` (see that module's own Gotcha on why it keeps such segments
intact for every other caller).

**A real bug, caught by a synthetic test, not by the live run.** `currentPathWithoutLanguage` is
version-INCLUSIVE when the current page is already a non-default version (`/enterprise-cloud@latest/rest`
on GHEC's own page) and only happens to look version-free on the default page (`/rest`, since the
default has no URL prefix at all). The first implementation derived the language prefix from the
already-version-stripped content path instead of the original field, producing `/de/v2` instead of
`/de` for a non-default seed. This was invisible against the live `docs.github.com/de/rest` run
itself — the default page never exercises the version-stripping branch, so both code paths
coincidentally produced the same prefix — and caught only by a dedicated synthetic unit test
(`test_build_version_urls_strips_version_prefix_when_seed_is_a_non_default_version`) built
specifically for that scenario. Fixed by deriving `lang_prefix` from the original field before any
version-stripping.

**Honesty note on the version-list heuristic's own generality.** `_find_version_list`'s "any key
containing `version`, shaped like a dict of dicts" rule is verified against exactly one real site.
Labeled the same way the original 2026-05-31 experiment labeled its own analogous move:
"partially generic — heuristic, needs adaptation", not proven to transfer. Shipped anyway because
the failure mode is benign by construction: a false version candidate just produces a URL that
404s or lands on an unexpected page, contributing zero URLs to the union, never a crash or bad
data — the fetch that follows validates the guess for free.

## The `source` field — a review addition to `FeederResult`

Milestone 1's `FeederResult` had no way for a caller to distinguish an authoritative result from a
scrap. Live proof this matters: tier 1 on `ui.shadcn.com/docs` returned 248 URLs from a genuine
navigation tree; tier 2 on `nextjs.org/docs` returned 21 stray hrefs from a site with hundreds of
real documentation pages — structurally indistinguishable as a bare `list[str]`. `FeederResult`
gained a `source: str | None` field, populated on every successful result across ALL THREE feeders
(`"robots"`, `"sitemap"`, `"navtree_tree"`, `"navtree_flat"`) — added to the shared contract, not
bolted onto `navtree_feeder_workflow` alone, specifically so a field meaningful for only one of
three producers would not itself become the kind of half-integrated addition this milestone's own
`normalize_url` Gotcha warns against elsewhere. No filtering and no quality threshold was added on
top of it — `urls` always carries everything either tier found; a downstream frontier-wiring or
coverage-check milestone decides what weight to give `"navtree_flat"`, not this one.

## Verification — real runs, no mocking

**`docs.github.com/de/rest`** (primary benchmark). Default tree alone (tier 1, no union): **254
unique hrefs** (256 in the 2026-05-31 snapshot — 2 fewer, consistent with ~3 months of ordinary
site-content drift, not a regression: `sidebarTree` itself is byte-for-byte the same structure).
Version list today: 8 versions (FPT, GHEC, GHES 3.17–3.22) — one fewer/shifted than the original's
8 (FPT, GHEC, GHES 3.16–3.21): GHES 3.16 has been retired since, GHES 3.22 added, net count
unchanged. Full run through `navtree_feeder_workflow` (default + 7-version union, 8 HTTP requests
total, matching the original experiment's own request count): **304 URLs**, `source="navtree_tree"`,
0.3s wall-clock. Against the reference points: 254→304 (+50, this run) versus 256→305 (+49,
2026-05-31) — closely matching proportional coverage recovery from the union step, and 304 is 1 URL
under the dated 305 snapshot rather than a target to reproduce exactly, consistent with the same
kind of live-site drift already seen in M1's `theblock.co` measurement.

**App Router detection** (`coindesk.com` is the site named in the milestone task as one this project
has already observed in the RSC shape). Tried directly first: `coindesk.com`'s homepage and four
subpages (`/price/bitcoin`, `/latest-crypto-news`, `/markets`, `/tag/bitcoin`) all returned either a
"Vercel Security Checkpoint" JS-challenge page or HTTP 429, with full browser-shaped headers —
confirmed by direct `curl`, currently blocked at the plain-HTTP layer this feeder operates at (no
browser). Substituted two real, reachable App Router sites, per the same precedent M1 used for
`theblock.co`'s own proxy-pool run: **`ui.shadcn.com/docs`** (Fumadocs-based) — RSC stream detected,
tier 1 found a genuine structured page-tree prop (not DOM), **248 unique URLs**, 0.1s. **`nextjs.org/docs`**
— RSC stream detected, tier 1 found nothing (its own doc-content tree lacks `href`/`url` fields at
any level — a page-content AST, not a link tree), tier 2 recovered **21 real URLs**
(`source="navtree_flat"`) via the flat scan. Both prove detection does not fall through on the App
Router shape, for either payload sub-shape (tree-bearing and DOM-only) — exactly what the milestone
asked to be shown, with no gold standard expected or claimed for either count.

**Neither shape**: `books.toscrape.com` (already used as M0's probe target — confirmed no
`__NEXT_DATA__`, no RSC push calls). `navtree_feeder_workflow` → `ok=True, urls=[],
source="navtree_flat"` — clean empty, not an error, in 0.57s.

## Tests

`dev/tests/test_seed_feeders.py`, extended in place (688 LOC total, +261 for this milestone; 64
tests, up from 41). Local fixtures throughout: both payload shapes (including a synthetic import-row
that must be skipped without erroring), the tree/flat tier split (including the React-element
false-positive rejection and the fragment/`_next/`-internal filter), `_build_version_urls`/
`_canonicalize_version_url` (including the non-default-seed case that caught the real bug above),
`resolve_navigation_tree` end-to-end with a synthetic 2-version fixture proving the union recovers a
version-only page while deduping shared ones, and all three workflows' `FeederResult.source` on
their happy paths. `./venv/bin/python -m pytest dev/tests/test_seed_feeders.py -v` → 64 passed.
Full suite: `./venv/bin/python -m pytest` → 314 passed (0 regressions against M1's 291).
