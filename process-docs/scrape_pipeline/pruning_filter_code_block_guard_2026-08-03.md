# Scrape Pipeline — Guarding PruningContentFilter Against Code-Block Destruction

*Dated entry — historical record of the investigation; the live current state is the source code, not this file.*

## Problem

`src/scraper/scrape_url.py`'s `try_scrape` runs `PruningContentFilter(threshold=0.48)` and returns
its `fit_markdown`. Filed upstream as crawl4ai issue #2110 (OPEN as of this project's installed
0.9.2, reported with `threshold=0.48, threshold_type="fixed"` — this project's exact configuration):
the filter's block-level scoring treats whitespace-only spans inside syntax-highlighted code as
near-zero density and decomposes them, corrupting the code around them. This was already known
locally — `process-docs/scrape_pipeline/scrape_pipeline.md` records under Open Questions that the
pruning filter is destructive for code pages, predating the upstream filing.

## Root Cause, Read From Source

`_prune_tree` in the installed `crawl4ai/content_filter_strategy.py` (`venv/lib/python3.14/
site-packages/crawl4ai/content_filter_strategy.py:701-755`): for a kept node, it recurses into
every child and decomposes any child scoring below `threshold`. A syntax highlighter (Rouge, Prism,
highlight.js — all token-per-`<span>` structures) splits code into many `<span>` fragments with bare
whitespace text nodes between tokens; those whitespace spans score near-zero and get removed. crawl4ai
added `preserve_tags`/`preserve_classes` to `PruningContentFilter` in 0.9.1 (PR #1904) — confirmed
present on the installed 0.9.2 via `inspect.signature`: `(user_query, min_word_threshold,
threshold_type, threshold, preserve_classes, preserve_tags)`, both `None` by default.
`_is_preserved(node)` is checked BEFORE scoring/recursion in `_prune_tree` — on a tag-name or
class match it returns immediately, skipping the whole subtree, so no child is individually
re-evaluated.

## Investigation — Offline Repro Before Touching Anything

Fetched real, live HTML via `curl` (not a fixture) for the three pages issue #2110 names:
kubernetes.io's Service concept page, MDN's `Array.prototype.reduce()` reference, and a real dev.to
multi-stage-Docker-for-Go post (`young_gao`'s article — the exact article named in the issue could
not be located, so a structurally identical live substitute with the same Rouge-highlighted-span
markup was used instead). Ran the installed `PruningContentFilter` directly against the raw HTML,
with and without `preserve_tags=["pre","code"]`, before writing any code:

- **kubernetes.io**, first YAML `<pre class="chroma">` block — without guard:
  `'apiVersion:v1kind:Servicemetadata:name:my-serviceselector:app.kubernetes.io/name:MyApp-
  protocol:TCPport:80targetPort:9376'`; with guard: properly indented multi-line YAML, byte-identical
  to source.
- **dev.to**, Dockerfile block — without guard:
  `'FROMgolang:1.22-alpineASbuilder\nWORKDIR /app\n...'`; with guard:
  `'FROM golang:1.22-alpine AS builder\nWORKDIR /app\n...'`.
- Confirmed mechanically: `<pre>` TAG COUNTS were identical before/after in both pages (19 vs 19 for
  k8s, 16 vs 16 for dev.to) — the defect is content lost INSIDE a surviving `<pre>`, not the `<pre>`
  itself being removed. This is what explains the corruption pattern rather than just restating the
  symptom.
- **MDN**: zero byte difference in the offline test. The curl-fetched static HTML has no
  per-token highlighter spans at all (code sits as plain text in `<code>`) — MDN applies syntax
  highlighting client-side via JS after load, so the static fetch structurally cannot trigger this
  particular bug. Not evidence the fix is unneeded there — evidence this fetch never hit it.

## Decision — `preserve_tags` Only, `preserve_classes` Rejected

Both real repros were fully fixed by `preserve_tags=["pre","code"]` alone. In both cases the `<pre>`
tag itself — not an intermediate wrapping `<div>`/`<figure>` — is what the top-down `_prune_tree`
recursion evaluates directly, so the tag-name guard reaches it before any ancestor could be
decomposed wholesale first. `preserve_classes` was considered and rejected: it would require
enumerating highlighter-specific wrapper class names (Rouge's `highlight`, Prism's `token`,
highlight.js's `hljs`, GitHub's, CodeMirror's, ...) — an open-ended, brittle list with no evidence
requiring it, since `preserve_tags` alone already fully restored both real cases. `threshold` (0.48)
left untouched — this is a guard on the existing 36-config × 20-URL calibration recorded in
`scrape_pipeline.md`, not a revision of it.

## Verification — Through the Real CLI, Not Just the Offline Filter

The offline reproduction above used the filter directly against raw HTML — a different, weaker
verification level than the actual claim being made. Re-ran all four pages (the three from #2110 plus
`rfc-editor.org` RFC 2616 as a prose-only control) through the real `scrape_url_workflow` via the CLI,
before/after the code change, isolated with `git stash`/`stash pop`:

- **kubernetes.io** and **dev.to**: identical corrupted/fixed strings as the offline test, now
  confirmed end-to-end through browser fetch → markdown generation → truncation → the actual
  `TextContent` returned to the caller. `bytes_returned` 13795→14134 (k8s), 11402→11413 (dev.to) —
  small increases from the restored whitespace/structure.
- **MDN**: does not reproduce through the CLI either, at the default 15000-char cap OR at 60000
  (called directly against `scrape_url_workflow(url, max_content_length=60000)` to rule out
  truncation as the reason) — `sumWithInitial`/`const array`/`accumulator, currentValue` are absent
  from `result.markdown` entirely in both configurations, before and after the fix, byte-identical
  output (17332 chars both). The interactive code examples never reach crawl4ai's captured markdown
  on this scrape path at all — most likely a cross-origin `<iframe>` MDN uses for runnable examples,
  not captured by `wait_until="load"`. Reported as a separate, unrelated finding: MDN is genuinely
  untestable for this fix through this pipeline, not a third success and not a fix failure.
- **RFC 2616 control**: `outcome`, `http_status`, `bytes_returned` (12168/12168), `bytes_raw_markdown`,
  `fallback_to_raw`, `truncated`, `consent_stripped`, `garbage_type`, `published_date`, all 5
  `crawl4ai_*` fields — byte-identical field-by-field diff, confirming no collateral behavior change
  on a page with no code blocks.
- Config stamp: `content_filter_preserve_tags: ["code", "pre"]` now present, read back off
  `content_filter.preserve_tags` (never hand-declared). `config_hash` shifted from `7ac9eefa4b` to
  `956e088b10` consistently across all 4 URLs — confirms the milestone-2 grouping mechanism correctly
  separates pre-fix from post-fix records.

NOT verified: a hypothetical page where a non-`pre`/`code` wrapper itself scores below threshold and
gets decomposed before recursion ever reaches a nested `<pre>` — theoretically possible per
`_prune_tree`'s top-down short-circuit, not observed on either real repro, remains unverified.
`tests/test_scrape_url.py` (10 cases) unaffected — pure-function regression guard on
`is_garbage_content`/browser-launch classification, no new case added since this fix touches neither.

## Sources

crawl4ai issue #2110 (open, upstream repo — page/thresholds/workaround as filed); crawl4ai PR #1904
(added `preserve_tags`/`preserve_classes` to `PruningContentFilter` in 0.9.1, confirmed present in the
installed 0.9.2 via direct introspection); real live fetches of kubernetes.io, dev.to, and MDN pages
at the time of this session (2026-08-03) — not archived, subject to further site changes.
