# Capture cleanup: signature matches stopped deleting files — 2026-08-06

Orchestrator-side record: skill edit made directly in chat, no worker counterpart, plus the three
capture runs of the same day that exercised the old and new behaviour.

## The contradiction that triggered it

`skills/websearch-capture-and-index/SKILL.md` Step 5 defined a CANDIDATE as "signature match AND
small (thin-page byte range)" and then said a confirmed block page "is garbage → DELETE it". The
signature list is a keyword list: `"consent"`, `"captcha"`, `"verify you are human"`,
`"checking your browser"`, `"access denied"`, and similar.

That is structurally the same construction as `is_garbage_content` in `src/scraper/scrape_url.py` —
a keyword list producing a verdict on content. That construction was removed from the ad-hoc scrape
path on 2026-08-05 after it was shown wrong in both directions on the same four URLs (a complete
trustpilot review page discarded as an HTTP error page; an idealo courtesy page passed through as
clean). The skill had not followed that inversion.

## What changed

Detection stayed, its authority went. Per-class actions, modelled on the class/action table in
`skills/websearch-pdf/SKILL.md`:

- A (block/interstitial page) and B (thin page): SURFACE ONLY — print source URL, byte size, first
  lines; the agent READS them and decides. Deletion is recorded in the Completion Report as a
  decision with a reason, never as the automatic consequence of a match.
- C (chrome + footer): recoverable, strip, with invariants (the `<!-- source: URL -->` comment
  survives; body content outside the stripped span unchanged).
- D (index/aggregator page): surface only, never delete, flagged in the report.
- E (raw HTML instead of markdown): conditional, report and wait for the orchestrator.

Added alongside: a content window borrowed from the PDF skill (pull 1-2 body lines from the middle
third of every md and read them), a `/tmp` backup before any in-place rewrite, a post-clean re-scan
of the class, and two new Completion Report lines — files deleted with reasons, and files flagged
but kept.

The signature list itself was kept and relabelled a SEARCH AID, with an explicit note that vendor and
API documentation legitimately discusses cookies, CAPTCHAs and bot walls, so false positives are the
norm rather than the exception there.

## Evidence from the three capture runs of the same day

All three targeted vendor documentation, so all three were exactly the false-positive-prone case.

| Run | Pages | Old behaviour would have | New behaviour did |
|---|---|---|---|
| Cloudflare Turnstile docs (20 pages) | ran under the OLD skill text | — | no block/thin candidates arose at all |
| Cloudflare Challenges docs (18 pages) | ran under the NEW text | js/bot-wall signature hits on Cloudflare's own CAPTCHA and JS-detection pages | read them, kept them as on-topic, deleted 0, flagged 3 section landing pages |
| Playwright Python docs (13 pages) | ran under the NEW text | signature hits on `events`, `network`, `class-browser`, `class-browsertype` from wording like "subscribe to events" / "register listener" | verified as false positives, deleted 0 |

The Playwright run is the sharpest case: under the old rule `class-browsertype` was a deletion
candidate, and that page was the entire reason the capture was run — it carries Playwright's
documented `launch` timeout default.

## Not addressed here

The skill's operational numbers remain gut values: the BFS render wait of 3.0s (inconsistent with the
ad-hoc lanes), `page_timeout` 15000 (against 30000 in production), concurrency 1 labelled "WAF-safe",
and the 429 policy of 5s-once — which additionally contradicts this project's own no-backoff decision
and ignores the `Retry-After` header entirely. Also untouched: the Cleanup thresholds themselves
(diagnose-script size, shape-group count, thin-page byte range, candidate-set stop threshold,
post-cleanup minimum line count). Those need external sources, which were named but not fetched:
RFC 9110 for `Retry-After`, the Google and Bing crawler documentation for crawl-rate politeness, and
the sitemaps.org protocol spec for discovery.
