# Closing the last open item from the 2026-08-28 work: version-duplicate recognition (2026-09-05)

Continues the `url_discovery` area, and closes the last item left open since the 2026-08-28
session that built the frontier-wiring and navtree feeder: a link discovered mid-traversal to an
explicit-version URL (e.g. `/de/free-pro-team@latest/rest/quickstart`, found on the real
`docs.github.com/de/rest` seed page) was treated as a distinct, genuinely-new URL from the
already-known canonical seed, even though it is the same page. `2026-08-28_fetch_success_and_
frontier_visibility.md` recorded this as real, not hypothetical, and deliberately deferred it —
"its own milestone, next." This is that milestone.

## Design: promote, surface, import — no new abstraction

`_canonicalize_version_url` (`seed_feeders_navtree.py`) is now public
(`canonicalize_version_url`), on the same precedent `seed_feeders_scope.host_key` already set:
promote the specific helper in its owning module once another module needs the identical rule, not
a new shared abstraction layer. The site's own version-key list is surfaced through a new
`FeederResult.version_keys` field, populated only by the navtree feeder from data it already
computed (`_find_version_list`) — no new fetch, `None` for a version-less site or a failed navtree
feeder. `discovery.py` imports `canonicalize_version_url` directly and reads `version_keys` off the
navtree feeder's own `FeederResult` after `_run_feeders` completes.

## Annotation versus prevention — the reasoning, in full, because it is the lasting part

Preventing the duplicate's fetch entirely was considered first, since the mechanism looks like it
already exists: `_build_resume_state` pre-populates `resume_state["visited"]`, and the
version-prefixed forms of already-known seeds are derivable from the same version keys this
milestone surfaces. Rejected, on two grounds, both worth keeping on record.

**First: pre-population does not yield a not-fetched entry for free.** `link_discovery`'s own `if
base_url in visited: continue` (`bfs_strategy.py`) makes a matching URL vanish from the traversal's
bookkeeping entirely — it never reaches `next_level`, `valid_links`, or any other tracked
structure, exactly like a filter-chain rejection would. Keeping the duplicate visible under
prevention would mean reconstructing it ourselves, independent of anything the traversal actually
observed, not reading it back from crawl4ai's own state.

**Second, and decisive: reconstructing the URL ourselves means handing a caller a URL this run
never confirmed resolves at all, and a wrong reconstruction has a genuinely bad failure mode.**
Two ways to reconstruct were examined:
- **Mechanical derivation** (`lang_prefix` + `version_key` + `content_path`, the same pattern
  `_build_version_urls` already uses for a version's root). If the derivation is wrong for a
  specific page — real sites are not perfectly uniform — the REAL, DIFFERENT page that happens to
  collide with the guessed string would be silently absorbed into `"visited"` and never fetched or
  reported. A silently lost page is the exact failure mode this whole area exists to prevent
  (`2026-08-28_validation_against_live_sites_was_the_wrong_unit.md`'s entire argument is against
  exactly this kind of unverifiable claim), and trading a wasted fetch for the RISK of one is a bad
  trade.
- **The navtree feeder's own per-version href lists** (`_resolve_one_version` already walks each
  other version's own tree — real, confirmed data, no new fetch). This closes the reliability
  problem but opens a coverage one: it only covers pages the navtree's own sidebar-tree structure
  lists. **The actual case on record — the `docs.github.com` link that started this whole
  question — was found in a page's own rendered body, not necessarily present in the sidebar JSON
  at all.** Prevention built this way would have silently missed precisely the case that motivated
  the fix.

Annotation has neither failure mode: it operates on whatever `link_discovery` actually found, from
anywhere on the page, and only ever labels a URL after a real fetch already confirmed it exists.
`DiscoveredURL.canonical_url` is set on the duplicate's own entry after that real fetch; the
canonical entry is never touched; the duplicate stays visible, because a distinct URL that really
resolves is real information for a caller whose goal is the largest possible URL list, and the
existing "visited"-rediscovery precedent does not transfer here (that case is the same string
discovered twice — zero new information; this is a different string serving the same content —
the URL itself is new information).

## The cost, stated as a number, not invented as one

At `TRAVERSAL_CONCURRENCY=1` (this area's own current, measured value — `2026-09-05_pacing_
measurement.md`), each duplicate that annotation still pays for costs roughly
`TRAVERSAL_MEAN_DELAY_S` to `TRAVERSAL_MEAN_DELAY_S+TRAVERSAL_MAX_RANGE_S` = **1.0 to 1.5 seconds**
— a real number from values this area already measured, not a new one made up for this entry. The
AGGREGATE cost on a real site is genuinely unmeasured: its shape is `pages × (versions − 1)` — every
canonical page's own links to its alternate-version forms, if a real site's version-switcher UI
links every page to every other version of itself. The fixture deliberately contains exactly one
such case by design, so this milestone cannot and does not produce that aggregate number. Whoever
next revisits this should count `pages × (versions − 1)` on a real target rather than rederiving
the question from scratch.

## Scope boundaries, stated so neither gets read back into something larger

**The alias check runs against already-known SEEDS only, never against another traversal find.**
`_resolve_canonical_alias(url, seeds, version_keys)` checks `canonical in seeds`, nothing broader —
matching the actual case this was built for (a link that duplicates a canonical page a FEEDER
already delivered), not a general URL-equivalence or deduplication mechanism. Do not extend it to
compare traversal finds against each other; that was explicitly out of scope and stays out of
scope.

**An inherited, disclosed, not-fixed-here risk:** `canonicalize_version_url` strips ANY path
segment matching a known version key, wherever it occurs in the path — the same rule the navtree
feeder's own version union already accepts for itself, not something new introduced here. A
coincidental non-version path segment that happens to equal a real version key (e.g. a blog post
literally titled `/blog/v1-announcement` on a site whose docs version key is also `"v1"`) could
false-positive, marking two genuinely different pages as aliases of each other. Fixing this would
itself be the general URL-equivalence mechanism this milestone was told to stay clear of, so it is
named here and left alone.

## Ground truth — before and after, side by side

| | Before | After |
|---|---|---|
| `total_urls` | 20 | 20 (unchanged — the duplicate was already its own entry, only its shape changes) |
| `by_source` | `{seed:1, robots:3, sitemap:5, navtree_tree:6, traversal:5}` | identical |
| duplicate's entry | `source="traversal", fetched=True` | `source="traversal", fetched=True, canonical_url=<canonical>` |
| canonical's entry | `source="navtree_tree"` | `source="navtree_tree", canonical_url=None` (untouched) |

## Verification

A real fixture run: `total=20`, `by_source` identical to `ground_truth()`, `pages_fetched=19`,
`pages_failed=1` — all unchanged from every prior milestone's run of this same fixture. Exactly one
alias found (`/docs/v1/guide/intro` → `/docs/guide/intro`); every other traversal-discovered entry
(`related-links`, `see-versions`, both orphan pages) confirmed `canonical_url=None` — no false
positives on a versioned site's own unrelated traversal finds. Version-less-site proof at the unit
level: `_merge_results` called with `version_keys=None` produces a byte-identical result to calling
it with the argument omitted entirely. 11 new pure-logic tests
(`_extract_version_keys`/`_resolve_canonical_alias`/`_merge_results`'s version handling), 1
fixture-backed test rewritten. Full suite, run twice: 388 passed both times (was 377).
