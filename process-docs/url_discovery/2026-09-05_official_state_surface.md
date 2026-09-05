# The private stop-reason read was never necessary — the official surface was already in hand (2026-09-05)

Continues the `url_discovery` area. `_determine_stop_reason` read `strategy._pages_crawled`, a
private, underscore-prefixed crawl4ai attribute, flagged in `src/crawler/DOCS.md` since the
frontier-wiring milestone as fine-to-use-but-fragile — no compatibility guarantee across a
dependency bump. `_traverse`'s own `on_state_change` callback was built the same session, reading
`bfs_strategy.py` as if `resume_state`/`on_state_change` were undocumented internals being relied
on out of necessity, not choice.

**They are not undocumented.** Crash recovery — `resume_state`, `on_state_change`, and
`export_state()` — is an officially documented crawl4ai feature since 0.8.0, carries vendor tests,
and is described in the library's own deep-crawling docs. This module's dependency on them was
never the reverse-engineered gamble the earlier entries' own framing implied; it was already using
the documented, supported surface, just without knowing that was what it was doing.

## The design that was proposed and rejected

Reading `bfs_strategy.py`'s `export_state()` (`return self._last_state`) turned up one fact:
`self._last_state` is written ONLY inside the `if self._on_state_change:` gate, from the same
`state` object handed to the callback — meaning `export_state()` cannot replace registering a
callback, it can only change where the state gets read back from afterward. The first design
proposed on that basis kept a callback (registered as a pure no-op, purely so crawl4ai's own
internal bookkeeping would run) and read the result back through `export_state()` — two mechanisms
doing one job, plus a Gotcha that would have had to explain to every future reader why a callback
that does nothing must stay registered. Rejected before implementing: the module's EXISTING
callback already captures `state` for the frontier-leftover purpose, and that captured dict is
provably the identical object `export_state()` would return at the same point (both are assigned
from the same local variable, in the same gated block, in the same iteration — checked by reading
the exact order, not assumed). The simpler path needed nothing new: keep the existing callback,
read `pages_crawled` off the dict it already captures, delete the private read. No `export_state()`
call appears anywhere in the module.

## What changed

`_determine_stop_reason(strategy) -> str` became `_determine_stop_reason(state: dict | None,
max_pages: int) -> str`, reading `state.get("pages_crawled", 0)`. `state` is the same dict
`_traverse`'s own `_capture_state` callback already produces for the frontier-leftover purpose —
one captured object now serves both jobs that used to be split across a callback and a private
attribute read.

**One genuinely new case, not present before:** `state` is `None` when a run has zero successful
fetches (the callback never fires — crawl4ai only invokes it after a successful result), and
`pages_crawled` must default to `0` in that case. The old private-attribute read never had this
gap, since `strategy._pages_crawled` is an instance attribute initialized in `__init__` and always
present regardless of whether anything succeeded. A dedicated test
(`_determine_stop_reason(None, max_pages=500) == "frontier_exhausted"`) covers it — the one place
this refactor added behavior rather than only relocating it.

`dev/tests/test_discovery.py`'s `_StrategyStub` (a stand-in built specifically for the old
`._pages_crawled`/`.max_pages` interface) is gone; its three tests now call
`_determine_stop_reason({"pages_crawled": N}, max_pages=M)` directly, same three scenarios
including the real 586-vs-500 overshoot figure. `src/crawler/DOCS.md`'s stale private-attribute
Gotcha is removed, not left standing.

## Verification

Fixture-backed tests unchanged in assertion, +1 for the new `None` case: 107 passed (was 106). A
real fixture run after the change: `stop_reason="frontier_exhausted"`, `pages_fetched=19`,
`pages_failed=1`, `total=20`, `by_source` identical to `ground_truth()` — the same numbers every
prior milestone's run of this fixture produced. Full suite, run twice: 377 passed both times.
