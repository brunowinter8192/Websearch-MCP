# Navtree feeder — post-commit review fixes (2026-08-28)

Two review points on the just-committed navigation-tree feeder
(`process-docs/url_discovery/2026-08-28_navtree_seed_feeder.md`), addressed in
`src/crawler/seed_feeders_navtree.py`/`seed_feeders.py` before recap.

## 1. A failed seed fetch was indistinguishable from "no navigation tree"

Before this fix, `resolve_navigation_tree` treated an unfetchable `seed_url` the same way it
treats a version root that fails to load: return an empty list, tagged `"flat"`. That surfaced to
`navtree_feeder_workflow`'s caller as `FeederResult(ok=True, urls=[], source="navtree_flat")` — the
same shape as a genuinely reachable site that simply carries no framework payload
(`books.toscrape.com`, verified in the milestone's own report). Those are not the same fact: one
means "this site publishes nothing to discover", the other means "the feeder never got to look at
anything".

**Decision: `ok=False`, not a distinct source tag.** `FeederResult`'s own docstring (M1) already
draws this exact line — "ok=True with an empty urls list is a genuine 'found nothing' outcome...
ok=False means the feeder itself could not run". A version root's fetch failure, a missing
robots.txt, and a 404 sitemap are all genuinely optional resources elsewhere in this package — the
target might legitimately not exist. The seed is categorically different: it is not an optional
resource, it is the thing the whole run is about, so its own failure to fetch means the feeder
never ran at all, which is exactly the existing `ok=False` case, not a new third state. A distinct
source tag was considered and rejected: it would still be `ok=True`, contradicting the contract's
own established rule instead of extending it.

Implementation: `resolve_navigation_tree` now raises `RuntimeError(f"could not fetch seed_url:
{seed_url!r}")` when the seed's own `_fetch_html` returns `None`, caught by
`navtree_feeder_workflow`'s existing `except Exception` — the same path an invalid `seed_url`
(`_require_host`'s `ValueError`) already used, since both are preconditions for the feeder to do
any work, not something discovered mid-run.

Verified live (not just against the mock in the new test): `navtree_feeder_workflow` against
`https://docs.github.com/this-page-does-not-exist-at-all-xyz123` (a real, reachable host, a real
404) returns `ok=False, error="could not fetch seed_url: ...", source=None` — not the
`ok=True, urls=[]` shape the "neither shape" case (a genuinely reachable, genuinely payload-less
page) still correctly returns.

## 2. Return-annotation audit

The same defect M1 fixed on `fetch_robots_txt`/`fetch_sitemap` (`-> str` that can return `None`)
was checked across every function added this milestone. Found and fixed: `_child_key_of` (`str` →
`str | None`), `_find_version_list` (`dict` → `dict | None`), `_find_current_version` (`str` →
`str | None`), `_find_path_without_language` (`str` → `str | None`), `_fetch_html` (`str` →
`str | None` — the one named directly in the review), and `_find_tree_candidates`'s `out`
parameter (`list = None` → `list | None = None`). `_build_version_urls`'s three parameters were
also fixed to match, since each is fed directly by one of the now-corrected finder functions above
— not itself independently mismatched, but propagating the same real nullability once the callers
were corrected.

## Verification

`./venv/bin/python -m pytest dev/tests/test_seed_feeders.py -v` → 65 passed (was 64; the
unfetchable-seed test changed from asserting an empty tuple to `pytest.raises(RuntimeError)`, and
one new workflow-level test was added asserting `ok=False` end-to-end). Full suite:
`./venv/bin/python -m pytest` → 315 passed, 0 regressions. Re-ran the milestone's own live
`docs.github.com/de/rest` verification after both fixes — still 304 URLs, `source="navtree_tree"`,
confirming neither fix touched the happy path.
