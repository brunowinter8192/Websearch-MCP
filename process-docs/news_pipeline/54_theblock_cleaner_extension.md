# 54 — The Block cleaner extension: Stage 1 + Stage 2 + Stage 3

**Date:** 2026-06-18. **Commits:** Stage 1 `48d08d5`, A5-fix `9608bc8`, Stage 2 `da28de4`.
**Branch:** `theblock-cleaner`. **Staged from:** the prior cleanup audit.

---

## What was done

Extended `src/news/platforms/theblock/cleanup.py` with 7 low-risk boilerplate rules (Stage 1)
and 1 high-risk sponsor-block rule (Stage 2), then ran the final cleaner over all 22,995
raw HTMLs to produce the new clean corpus (Stage 3).

---

## Stage 1 — Low-risk rules

Validation script: `/tmp/validate_stage1_v2.py` (isolated per-rule measurement against 22,995 raw).

### Rules added

| Rule | Regex | Files hit | Avg chars removed |
|------|-------|-----------|-------------------|
| A3 extend `_COPYRIGHT_RE` | `^©\s*\d{4}\s+(?:The Block Crypto,\s*Inc.\|The Block)\.?\s*All Rights Reserved.*$` | 2 | 129 |
| A4 broaden `_NEWSLETTER_CTA_RE` | `^_.*subscribe to the .*newsletter.*$` (drop trailing `_`) | 31 | 64 |
| A5 `_CAMPUS_CTA_RE` | `^.*theblock\.co/campus.*$` (URL-anchor, any line) | 56 | 47–50 |
| N1 `_PODCAST_SUB_CTA_RE` | `^[*_]*Listen below[,.]?\s+and subscribe to\b.*$` | 371 | 217 |
| N3 `_NEWSLETTER_PROMO_RE` | `^\*\*The Block Newsletters[^\n]*\n[^\n]*theblock\.co/newsletters[^\n]*` | 99 | 179 |
| N4 `_COMMISSIONED_RE` | `^_?This post is commissioned\b.*$` | 534 | 429 |
| B3 `_MCE_SPAN_RE` | `<span[^>]*data-mce-type[^>]*>.*?</span>` (DOTALL) | 17 | 231 |

A5 initial design anchored on `^Sign up for a trial today:` (44 hits). Residual probe found
12 files with italic `_Sign up for a trial today: theblock.co/campus` — fixed to URL-anchor
in a follow-up commit.

A4 decided NOT to extend beyond `^_` prefix: residual probe found 33 remaining lines, of
which 5 contain genuine editorial content (Crypto.com newsletter mention, TRON newsletter
mention, market analysis + CTA mixed on same line). Cannot safely broaden.

**Content-loss guard:** 0 zero-regressions; 1 >40% tripwire (`76eb7d8408a9`) — confirmed
false alarm: B3 removed 425 chars of TinyMCE span HTML artifacts, leaving 281 chars of
real prose.

---

## Stage 2 — N2 podcast sponsor block

### Design

Regex: `\n\*{0,2}This episode is brought to you by\b.*` with `re.DOTALL | re.IGNORECASE`.

EOS anchor (strip from sponsor header to end of string). Applied last in `_post_clean()`
after Stage 1 rules have already stripped copyright and Foresight disclaimer.

`\*{0,2}`: handles both `**This episode...` (250 files) and `This episode...` no-bold (2 files).

### Safety proof

Validation script: `/tmp/validate_n2.py`, `/tmp/validate_stage2_proof.py`.

- **Broad-signature scan** (any `This episode is brought to you by` with/without `**`): 252 files
- **Regex coverage**: 252/252 — `\*{0,2}` covers all header variants including no-bold
- **Header variants catalogued**: 41 unique patterns (singular/plural "sponsor(s)", with/without `**`,
  various sponsor-name formats) — all start with `This episode is brought to you by`
- **Editorial markers in stripped section** (`according to`, `said`, `announced`, `told The Block`, etc.):
  **0/252 files** — zero editorial content in any stripped section
- **Stripped-section inventory**: 628 sponsor-description-italic, 377 About-sponsor-header,
  250 sponsor-header, 119 bold-line, 82 The-Block-promo, 10 Disclaimer lines, 0 news prose
- **Post-strip article tails** (10 sampled): all articles end cleanly at `* * *` horizontal-rule
  separator with editorial bullet-point content intact
- **N2 sig remaining after full cleanup**: 0/252

**Note on first probe error**: initial probe measured "non-empty content after sponsor HEADER
LINE" — which trivially returns 252/252 because the sponsor block itself is multi-line. Corrected
probe checked what the regex *would strip* for editorial content markers. The 252/252 figure
in the first probe was a false alarm; the corrected proof shows EOS is safe.

---

## Stage 3 — Production run

Script: `/tmp/theblock_stage3.py`.
Input: 22,995 raw HTMLs from `data/news/theblock/scrape/`.
Output: `rag-cli/data/documents/theblock/theblock__{pubdate}__{hash}.md`.

### Funnel

| Step | Count |
|------|-------|
| Raw HTMLs processed | 22,995 |
| Written (non-empty) | 22,929 |
| Body-less / empty | 66 |
| Errors | 0 |

Empty hashes listed in `rag-cli/data/documents/theblock/theblock_empty_urls.txt`.
`theblock__index.jsonl` not touched.

### Char-count guard

Min=8 · P10=1,182 · Median=2,111 · P90=4,066 · Max=114,388. No zero-regressions.

### Residual noise scan

| Signature | Files | Assessment |
|-----------|-------|------------|
| N2_sponsor_block | 0 | ✓ |
| A5_campus | 0 | ✓ |
| B3_mce_span | 0 | ✓ |
| A4_newsletter_cta | 28 | Intentional residual: Frank Chaparro mixed editorial+CTA lines |
| N1_podcast_cta | 9 | Mid-paragraph "Listen below" embedded in episode-context sentence; `^` anchor correct |
| N3_newsletter_promo | 5 | Blank-line format variant: `**The Block Newsletters**\n\n**The Block's newsletters...` — regex expects consecutive lines. Open item. |
| N4_commissioned | 1 | Triple-underscore variant `___This post is commissioned` — `^_?` only handles 0–1 `_`. Open item. |
| A3_copyright_old | 4 | **False positive in scan**: editorial text mentioning "The Block Crypto" as brand name (e.g., "data collected by The Block Crypto"). Copyright lines ARE stripped. Rule is correct. |

Open items (N3 blank-line variant × 5, N4 triple-`_` × 1): total 6 files, negligible
residual (0.026% of 22,929). Fix in a future cleanup pass.
