# 53 — The Block cleanup audit: how clean is the cleaned corpus?

**Date:** 2026-06-18. **State:** read-only audit complete, no source or corpus edits made.

## Context

After the raw-only decoupling, the existing cleaned corpus in
`rag-cli/data/documents/theblock/` (3952 `.md` files, 2018-08 → 2026-06, 13.4 MB) is the
only indexed content. Before deciding whether to re-clean from raw or patch-and-re-index,
we audited what the current cleaner (`src/news/platforms/theblock/cleanup.py`) actually produced.

## Audit method

Script: `/tmp/theblock_audit.py`. Report: `/tmp/theblock_cleanup_audit.md`.

**Cleaner recipe (as of audit date):**
1. Parse JSON-LD `NewsArticle.articleBody` from raw HTML via `_find_news_article()` (flat 2-level scan, accepts plain dict, `@graph` list, top-level list). On miss → `""`.
2. `_html_to_markdown()` via crawl4ai html2text (`body_width=0`, `ignore_images=True`).
3. `_post_clean()`:
   - `_LINK_URL_RE` — strip `[text](https?://...)` → keep text
   - `_DISCLAIMER_RE` — `^Disclaimer: The Block is an independent media outlet.*$` MULTILINE
   - `_COPYRIGHT_RE` — `^©\s*\d{4}\s+The Block\.\s*All Rights Reserved.*$` MULTILINE
   - `_NEWSLETTER_CTA_RE` — `^_.*subscribe to the .*newsletter.*_\s*$` MULTILINE
   - whitespace normalise (`\n{3,}` → `\n\n`)

**Scan signatures (13 patterns):** residual inline URLs, disclaimer, copyright, newsletter CTA,
campus CTA, SendGrid tracking URLs, bare line-start URLs, raw HTML tags, HTML entities,
footer phrases, regwall phrases. Per-file fingerprint: byte size, line count, H2 count,
link ratio, HTML-tag presence, SendGrid presence. Shape clusters: EMPTY / MICRO /
NEWSLETTER / HTML_CONTAMINATED / RESEARCH_REPORT / STANDARD_NEWS.

## Bottom line

**93 / 3952 files (2.4%) contain at least one noise artifact. 97.6% clean.**

Zero regwall artifacts — JSON-LD extraction bypasses the paywall correctly.
Zero structural HTML (`<div>`, `<table>`, `<script>`). Zero `Continue reading` / site chrome.
The 4 original boilerplate regexes worked correctly for 2018–2025 content.
All noise concentrates in 5 bounded gaps (see below).

## Gap table

| # | Gap | Files | Nature | Fix |
|---|---|---|---|---|
| G1 | Stale 2026-06-13/14/15 batch — inline links + disclaimer + copyright survive | 17 | **Corpus staleness — NOT a regex bug.** Simulation confirms current `_post_clean()` strips all three correctly when applied. Files were indexed with older cleanup.py that pre-dated `_LINK_URL_RE` / `_DISCLAIMER_RE` / `_COPYRIGHT_RE`. | Re-run current `cleanup.py` on these 17 source HTMLs + re-index. Zero code change. |
| G2 | `Sign up for a trial today: theblock.co/campus` CTA | 38 | **Genuine code gap.** CTA added ~Nov 2025 to article templates; plain text (no italic wrapper, no "newsletter" keyword) — all four current regexes miss it. Date range 2025-11-11 → 2026-06-11. | New regex in `_post_clean()` + re-clean 38 files. |
| G3 | `<span data-mce-type="bookmark" ...>﻿</span>` TinyMCE cursor tags | 19 | **html2text pass-through.** Zero-width invisible TinyMCE editor artifacts in `articleBody` HTML. html2text passes unknown `<span>` unchanged. 16 files 2019-02 → 2020-03 (early CMS era); 3 files 2025-12 → 2026-05 (TinyMCE still in use for some content). Cosmetically dirty, semantically zero-width. | Strip `<span[^>]*data-mce-type[^>]*>.*?</span>` before/inside `_html_to_markdown()`. |
| G4 | 2019-09-23 cluster: 9 of 14 zero-byte files on same date | 9 | **Hypothesis, UNVERIFIED.** `_find_news_article()` returned `None` → empty output. Most likely cause: early JSON-LD used `@type: "Article"` not `"NewsArticle"`, causing `_is_news_article()` to skip. Cannot confirm without re-fetching the raw HTML — raw backfill would be required for verification. | Cannot fix until raw is available. If `@type:"Article"` confirmed: extend `_is_news_article()` to accept it. |
| G5 | Bare-line URLs + `&amp;` entity (YouTube / Twitter / Medium embeds) | 3–4 | Minor. Article bodies were primarily media embeds (YouTube, Twitter, Scribd) that became URL stubs after image/embed suppression. `&amp;` not decoded by html2text (pre-encoded in source `articleBody`). Content loss is inherent to the embed-only article type. | Low priority. Could strip bare-URL lines and normalize `&amp;` → `&`. |

## Zero-byte files (14) — named explicitly

Content loss: `cleanup.py` returned `""` for each. Every empty file = URL that produced no indexed content.

| # | File | Date | Notes |
|---|---|---|---|
| 1 | `theblock__2019-09-10__f54c7c86a324.md` | 2019-09-10 | |
| 2 | `theblock__2019-09-23__09e7ed3b83c4.md` | 2019-09-23 | G4 cluster |
| 3 | `theblock__2019-09-23__1ce3f634dce1.md` | 2019-09-23 | G4 cluster |
| 4 | `theblock__2019-09-23__258be4bf2382.md` | 2019-09-23 | G4 cluster |
| 5 | `theblock__2019-09-23__424f804dfa93.md` | 2019-09-23 | G4 cluster |
| 6 | `theblock__2019-09-23__574b2cfcff12.md` | 2019-09-23 | G4 cluster |
| 7 | `theblock__2019-09-23__67507a9a26cd.md` | 2019-09-23 | G4 cluster |
| 8 | `theblock__2019-09-23__a25459ec0cc3.md` | 2019-09-23 | G4 cluster |
| 9 | `theblock__2019-09-23__d1ed87a321eb.md` | 2019-09-23 | G4 cluster |
| 10 | `theblock__2019-09-23__df4dc01c1f89.md` | 2019-09-23 | G4 cluster |
| 11 | `theblock__2019-10-31__c986ed699dd2.md` | 2019-10-31 | |
| 12 | `theblock__2020-05-14__f9014743d36e.md` | 2020-05-14 | |
| 13 | `theblock__2020-08-19__e3be0deaaffe.md` | 2020-08-19 | |
| 14 | `theblock__2021-12-09__e8cca59dc3bc.md` | 2021-12-09 | |

Priority: no relevant content should be silently lost. These 14 URLs must be resolved before any re-indexing pass.

## Micro files (<1 KB, non-zero, 14 files)

5 media-stub articles: body was YouTube / Twitter / Scribd embed → stub after image suppression
(`theblock__2019-01-12__eed62a11ff8a.md`, `theblock__2019-10-04__18f7421bac0f.md`,
`theblock__2019-11-15__64d84d1c4c96.md`, `theblock__2020-03-19__ea5da2ef6602.md`,
`theblock__2020-03-22__b7532cc3e8cd.md`).

9 legitimately short articles: breaking-news briefs, abstract-only research previews, one event
announcement with form-widget "Loading..." artifact. None are regwall blocks. All contain
real prose and are indexable as-is.

## Shape clusters (3952 files)

| Shape | Count | Criterion |
|---|---|---|
| EMPTY | 14 | 0 bytes |
| MICRO | 14 | 0 < size < 1 KB |
| NEWSLETTER | 3 | SendGrid URL present OR link_ratio > 35% |
| HTML_CONTAMINATED | 19 | Raw `<span>` HTML tag present |
| RESEARCH_REPORT | 6 | size ≥ 15 KB AND H2 count ≥ 3 |
| STANDARD_NEWS | 3896 | all others |

Size distribution (non-zero): P10 = 1.7 KB · median = 2.7 KB · P90 = 5.2 KB · max = 62 KB.

## Decision context (Opus-owned)

Cleaner stays in the pipeline; these gaps inform the next cleanup iteration.
No-content-loss is the top priority — empty files resolved before re-index.
G1 (re-clean 17) and G2 (new regex + re-clean 38) are the highest-value quick wins.
G4 (9 zero-bytes) requires raw backfill before verification.
G3 (19 TinyMCE) is a code fix with negligible content impact.

---

## Stage 2 — full 22,995 raw fold-in

**Date:** 2026-06-18. **Script:** `/tmp/theblock_raw_stage2.py`. **Report:** `/tmp/theblock_22995_audit.md`.

All 22,995 raw HTMLs from `data/news/theblock/scrape/` run through current `cleanup.py` logic
(same `_find_news_article → _html_to_markdown → _post_clean` path, entry dict mocked minimal).
Output to `/tmp/theblock_raw_scratch_full/`. Zero harness exceptions.

### Zero-byte rate: 66 / 22,995 (0.29%)

**G4 FALSIFIED** (worker), and the worker's follow-up "gated/paywalled" reading is ALSO
wrong (Opus cross-check on the raw, articleBody + fallback `<div>` both inspected for all 66).
Schema is `NewsArticle` throughout (not `@type:"Article"`). True root cause: these are
**body-less posts** — there is NO article prose anywhere in the raw. Verified breakdown of the 66:

- **8 video-only** — `articleBody` is a YouTube/Twitter/Scribd `<iframe>` embed (+ copyright footer). The content IS the video; no text.
- **43 boilerplate-only** — `articleBody` contains ONLY the `© … The Block` copyright/disclaimer footer, no prose.
- **15 no-body** — `NewsArticle` present but no usable `articleBody`, and no `fallback-content` div either.
- **0 / 66 recoverable** — the `fallback-content` SSR div carries no prose for ANY of them (51 empty/boilerplate div, 15 no div).

`cleanup.py` is CORRECT to emit `""` here — there is nothing to index. These are NOT content
loss: no retrievable text exists. 0-byte = a legitimate
body-less post, must be LOGGED/LISTED (not silently dropped), but is not a failure needing recovery.

**G4 update for the 3952-corpus zero-bytes:** same class (body-less posts), not `@type`, not gated.
The 2019-09-23 cluster is the same pattern. `_is_news_article()` does not need extension.

**OPEN RESOLVED:** fallback `<div>` probed for all 66 → 0 recoverable prose. No fallback
extraction path would recover any of them.

### Noise signature table (22,995 raw → cleaned)

| Sig | Files | Verdict |
|---|---|---|
| `A1_inline_url` | **0** | CLEAN — `_LINK_URL_RE` grips correctly on fresh raw |
| `A2_disclaimer` | **0** | CLEAN — Foresight disclaimer stripped correctly |
| `A3_copyright` | **2** | GAP — `© 2022 The Block Crypto, Inc.` (old brand name) not matched by `_COPYRIGHT_RE` which requires literal `The Block.` |
| `A4_newsletter_cta` | **64** | GAP — `_NEWSLETTER_CTA_RE` too narrow: requires leading AND trailing `_`; many CTA variants close with `here.` not `_` |
| `A5_campus_cta` | **56** | GAP — G2 confirmed at scale (2025-11 → 2026-06) |
| `B1_sendgrid` | **0** | CLEAN |
| `B2_bare_url` | **17** | MINOR — YouTube/GitHub/whitepaper links as bare line-start URLs |
| `B3_html_tags` | **17** | MCE-spans — same rate as 3952 corpus |
| `B4_html_entity` | **1** | MINOR — `&amp;` in one file |
| `C1_footer_chrome` | **168** | MIXED — 56 are campus CTA (noise); remainder are "sign up for" in editorial prose (false positives) |
| `D1_regwall` | **2** | FALSE POSITIVES — "Create a free account with Tenderly" + "private members only collective" in body text |
| `N1_podcast_sub_cta` | **371 (1.6%)** | **NEW NOISE** — `_Listen below, and subscribe to The Scoop on_ _Apple_...` — podcast articles, fully unhandled |
| `N2_podcast_sponsor` | **252 (1.1%)** | **NEW NOISE** — `**This episode is brought to you by our sponsors...` + multi-paragraph sponsor ad copy |
| `N3_newsletter_block` | **87** | **NEW NOISE** — `**The Block Newsletters` promo block in podcast articles |
| `N4_commissioned` | **527 (2.3%)** | **LARGEST NEW GAP** — `_This post is commissioned by [Sponsor]...` sponsored-content footer disclaimer; appears on Quick Takes and paid-partnership articles |

Content tracked (not noise — no strip): Quick Take headers (6), Editor's note / Correction (59).

### Shape clusters (22,995 files)

| Shape | Count | % | Criterion |
|---|---|---|---|
| EMPTY | 66 | 0.3% | 0 bytes |
| MICRO | 1,032 | **4.5%** | 0 < size < 1 KB — much higher ratio than 3952 corpus (0.35%) |
| PODCAST | 358 | 1.6% | `N1_podcast_sub_cta` OR `N2_podcast_sponsor` present |
| SPONSORED | 527 | 2.3% | `N4_commissioned` present |
| NEWSLETTER | 1 | 0.0% | SendGrid URL OR link_ratio > 35% |
| HTML_CONTAMINATED | 15 | 0.1% | Raw `<span>` tag present |
| RESEARCH_REPORT | 12 | 0.1% | size ≥ 15 KB AND H2 ≥ 3 |
| STANDARD_NEWS | 20,984 | **91.3%** | all others |

Date range: 2018-08-17 → 2026-06-16 (full overlap with 3952 corpus; raw store is not "2023-2024 only").

### Cleaner gap priority list (for next cleanup.py update)

| Priority | Gap | Files | Regex anchor | Risk note |
|---|---|---|---|---|
| 1 | `N4_commissioned` | 527 | `^_?This post is commissioned by` MULTILINE | Low strip-risk: always trailing, one paragraph |
| 2 | `N1_podcast_sub_cta` | 371 | `^_Listen below[^_]*subscribe to` MULTILINE | Low: always line 3, self-contained |
| 3 | `N2_podcast_sponsor` | 252 | start: `^\*\*This episode is brought to you by` — **multi-paragraph block**, end anchor TBD | **HIGH RISK** — sponsor copy spans variable # of paras; strip requires clear end-anchor (next `* * *` rule / next `**` section header) to avoid content loss |
| 4 | `A4_newsletter_cta` fix | 64 | Drop trailing-`_` requirement: `^_.*subscribe to the .*newsletter` MULTILINE | Low |
| 5 | `N3_newsletter_block` | 87 | `^\*\*The Block Newsletters` + following 1-2 lines | Low |
| 6 | `A5_campus_cta` | 56 | `^Sign up for a trial today:.*theblock\.co/campus` MULTILINE | Low |
| 7 | `A3_copyright` (old brand) | 2 | Extend `_COPYRIGHT_RE` to also match `The Block Crypto` | Low |
| 8 | `B3_MCE_spans` | 17 | `<span[^>]*data-mce-type[^>]*>.*?</span>` in `_html_to_markdown()` | Low |
| 9 | `B2_bare_url` | 17 | `^https?://\S+\s*$` MULTILINE | Low; may strip intentional URL citations |
