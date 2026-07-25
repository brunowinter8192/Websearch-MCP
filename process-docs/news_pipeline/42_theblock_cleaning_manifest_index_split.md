# 42 — The Block index-readiness: articleBody-completeness, cleaning, URL-manifest, scrape/index split, collection rename

Post-Stage-B finalization, building on the platform's Stage-B work. Four changes + one empirical verification, all merged on dev,
to make The Block's output index-ready and the per-domain model consistent — before the big backfill.

## articleBody completeness — VERIFIED (no content loss)

The Block's MD content is the JSON-LD `NewsArticle.articleBody` field (proxy-fetched raw HTML → JSON-LD →
html2text). Open question: does taking only `articleBody` lose content vs the visible article? Verified
empirically across all 17 smoke articles (raw HTML compared: JSON-LD `articleBody` text vs the
server-rendered visible body in `<div class="fallback-content">`):

- **14/17:** word-for-word identical (ratio 1.00, articleBody fully contained in visible).
- **3/17:** visible body had 2-6 MORE words — the ONLY delta is the UI string **"Expand Chart"** (chart-button
  label; one article had 3 charts → 3×). No article prose is missing.

Conclusion: `articleBody` is the COMPLETE body and actually CLEANER than the visible body (it omits the
"Expand Chart" chrome). The page is a Vue app; the body exists 3× in static HTML (JSON-LD articleBody + the
`fallback-content` SSR div + a Vue-state JSON blob) — all carry the same prose. articleBody is the right source;
no extraction change needed. (Method: `BeautifulSoup` get_text on JSON-LD articleBody vs `fallback-content` div,
word-count + `difflib` segment diff on the divergent 3.)

## The Block cleaning — regex post-clean in `theblock/cleanup.py`

The articleBody→html2text MD carries boilerplate that must be stripped for RAG. Patterns confirmed across the
17 (`_post_clean()`, applied after `_html_to_markdown`, order matters):

1. **Inline-link URLs** (`\[([^\]]+)\]\(https?://[^)]+\)` → `\1`) — keep anchor text, drop URL. THE critical
   fix: one article ("The Funding" newsletter) had ~14 SendGrid email-click-tracking links, 500+ chars each
   (`https://u22280551.ct.sendgrid.net/ls/click?upn=…`), which made the MD unindexable. Prose was fine; only
   the link URLs were garbage. After strip: clean prose (e.g. `Others [expect](600-char-url) more` → `Others
   expect more`).
2. **Disclaimer paragraph** (`^Disclaimer: The Block is an independent media outlet.*$`, MULTILINE) — identical
   boilerplate line in all 17.
3. **Copyright footer** (`^©\s*\d{4}\s+The Block\.\s*All Rights Reserved.*$`, MULTILINE, year-agnostic).
4. **Newsletter CTA** (`^_.*subscribe to the .*newsletter.*_\s*$`, MULTILINE; anchored to the italic line, safe
   vs body prose).
5. Normalize: per-line rstrip + collapse `\n{3,}`→`\n\n` + strip.

Verified: applied to the 17 → 0 residual disclaimer/copyright/`](http`; prose intact (−~102 words = boilerplate
only). The-Block-specific by design; every other domain gets its OWN cleaner (the Platform `cleanup` seam).

## URL-manifest — general, per-collection (`engine/publish.py`)

Published MDs are pure content (no URL). `publish._write_index()` writes/merges `{collection}__index.jsonl` in
the collection dir, one line per article `{hash, url, publication_date, filename}`, dedup by hash, written even
under `--skip-index`. Domain-agnostic (CoinDesk + The Block + future). Purpose: cross-check completeness in a
browser (URL→on-disk-MD). The URL is known only at publish time (not on disk in the pure-content MD), so the
manifest is the append-merge record of it.

## Scrape/index split for non-48h runs (`__main__.py`)

A `full`/range backfill could produce 200+ articles — must NOT auto-index before inspection. `__main__` now:
if the platform has a `timeframe` attr and it is NOT `"48h"` → force `skip_index=True` + print "review, then run
`rag-cli index --collection <collection>`". The 48h standard run keeps scrape+index together. CoinDesk (no
`timeframe` attr) unaffected.

## Collection rename searxng_crypto → coindesk (per-domain consistency)

A prior stage decided per-domain collections. CoinDesk's collection was still the legacy shared name `searxng_crypto`.
Renamed: data (Opus — `cp` dir → `rag-cli index --collection coindesk` (68 articles, 195 chunks) → `rag-cli
delete --collection searxng_crypto`; old dir + DB collection gone) + source refs (`coindesk/__init__.py`
`collection="coindesk"`, `platform.py` comment, dev `04_dedup`/`05_publish`, dev DOCS). Earlier process history
left as-is (dated record of when searxng_crypto was the collection name).

## Open
- The actual backfill: `python -m src.news --source theblock --timeframe full` (auto-skip-index) → inspect →
  `rag-cli index --collection theblock`. First at-scale test of dead-URL (404/410) + exhaustion + 60-min refresh.
- The 17 smoke articles in `data/documents/theblock/` are un-indexed (cleaned WITHOUT the new regex — they
  predate the cleaner); a clean re-run or wipe+redo would regenerate them through `_post_clean`.
