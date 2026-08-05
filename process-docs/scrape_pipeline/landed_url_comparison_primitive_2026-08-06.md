# Requested-vs-landed URL comparison primitive (2026-08-06)

Milestone 1 of a 3-milestone plan (JSONL logging and acquisition-facts surfacing are the other
two, not touched in this session): `src/scraper/scrape_url.py` gained `is_same_target(requested_url,
landed_url) -> bool`, a pure, network-free comparison the later milestones will call to detect when
a redirect delivered different content than requested. As of this session it is NOT called from
`try_scrape`/`scrape_url_workflow`/`pipe_scraper` — comparison primitive only.

Motivating case (informed the same/different boundary below): a request for
`idealo.de/preisvergleich/OffersOfProduct/203078159_-fritz-box-7510-avm.html` lands on
`…/203078159_-woman-hybrid-jacket-fix-hood-33z6026-cmp-campagnolo.html` — HTTP 200, a complete,
plausible product page, wrong product. Status code, byte count, and crawl4ai's own diagnosis all
looked normal; only requested-vs-landed exposes the mismatch.

## Same/different boundary, decided with the user

Same target (mere spelling, never reported): scheme/host case, a leading `www.`, the scheme's own
default port (`:80` http / `:443` https), empty path vs `/`, a trailing slash, the fragment,
`http` vs `https`.

Different target (reported): any other host difference, any other path difference (the idealo
case: identical numeric product ID, rewritten slug), and ANY query-string difference — including
tracking-parameter-shaped ones. Deliberately no allowlist/denylist of "harmless" params: such a
list is guesswork, and a query parameter often DOES determine content — an allowlist tuned to
swallow tracking params risks swallowing an idealo-shaped case too. Cost model: an occasional
redundant report is cheaper than a rule that silently swallows a real content change.

## RFC-level normalization: implemented one, skipped one

Implemented: RFC 3986 §6.2.2.2 percent-encoding normalization — decode percent-encoded octets that
name an unreserved character (`%2D` → `-`), uppercase the hex of everything else (`%2f` → `%2F`).
Applied to path and query.

Skipped: dot-segment resolution (`../`, `./`). Would require `urljoin`-style resolution against a
base rather than a plain string operation; dot-segments essentially never occur in a redirect's
landed URL; no case in the evidence for this module needs it.

No third-party dependency added — `courlan` was evaluated and rejected earlier in this project for
pulling in trafilatura and doing far more than this comparison needs (see the
`process-docs/scrape_toolbox/` area for that evaluation).

## Degenerate inputs: two distinct failure shapes, two different defaults

**Missing (`None`/`""`) on either side → `True` (same, no deviation reported).** This is an
expected, known shape — crawl4ai leaves the landed URL unset on some paths (e.g. an exception
before navigation) — and a fact-reporting function has no fact to report from an absence; claiming
a deviation from missing data would be a fabricated signal, the failure mode
`content_judgment_removal_2026-08-05.md` (this same area) was written to eliminate in the sibling
content-judgment path.

**Present but unparseable as a URL (bad port, out-of-range port, malformed IPv6 literal) → `False`
(different, reported), and never raises.** This distinction was NOT caught in the first pass: a
review probe against the committed function raised `ValueError` on `is_same_target('https://x.test
:notaport/a', 'https://x.test/a')`, `'http://x.test:99999/a'` (port out of range), and
`'https://[:::1]/a'` (malformed IPv6). Root cause: `urlparse()` itself is lazy — on CPython 3.14 the
bracketed-IPv6 check raises INSIDE the `urlparse()` call itself (`_check_bracketed_netloc` →
`ipaddress.ip_address`), while `.port` raises lazily on read for bad/out-of-range ports (confirmed
by direct interpreter probe, both behaviors reproduced). Fix: wrap the `urlparse()` calls plus the
host-normalization read in one `try/except ValueError`, returning `False`. Chosen over `True`
because this is a categorically different failure than the missing-input case: there, nothing was
given to compare; here, two strings ARE present but fail to parse as a URL at all — an anomaly
worth surfacing, not silence. Defaulting to "same" would risk masking a genuine mismatch behind a
parse failure, same cost model as the no-tracking-allowlist decision above. This matters beyond
correctness of the primitive itself: milestone 2 will call this from inside `try_scrape`'s guarded
acquisition span AFTER content has already been fetched successfully — an uncaught exception there
would have turned a successful scrape into a hard failure over an annotation step, inverting this
module's fact-reporting contract from `content_judgment_removal_2026-08-05.md`.

## Why `crawl_site.normalize_url` (existing, in `src/crawler/crawl_site.py`) was not reused

It strips the entire query string and cuts `@version` path segments — correct for its own use
(BFS visited-set dedup, where over-merging is safe: worst case is revisiting a page). Wrong here:
a differing query CAN mean a genuinely different page, which is exactly the idealo-shaped signal
this primitive exists to preserve, not discard.

## Verification

47 tests in `tests/test_scrape_url.py` (was 21 before this session): same-target spelling-pair
table, different-target table (including the literal idealo host/path shape and multiple
tracking-parameter-shaped query pairs), degenerate-input table (all `None`/`""` combinations), and
a malformed-URL table covering the three reported failing inputs plus their reverse position
(malformed on the landed side). Full suite: `9 failed, 163 passed` — diffed the `FAILED` list
against the standing baseline (7 `test_query_logger.py` + 2 `test_proxy_pool.py`), identical, no
drift.
