# download_pdf — Removal (2026-06)

Process record for retiring the `download_pdf` feature.

## Decision

`download_pdf` removed completely. PDF download is delegated to the user.

**Driver:** the tool was unreliable. The multi-step resolution path (`citation_pdf_url` two-hop) only resolved a freely-downloadable PDF in a minority of cases (user assessment: ~40% hit rate). A tool that fails the majority of the time is not worth maintaining — the user downloads PDFs manually instead.

**Trigger case** (the failure that surfaced the unreliability): bot-protected academic hosts (MDPI Open Access, SSRN) served a non-article page to the `requests`-based fetch, so the `citation_pdf_url` meta-tag parse never saw the tag → "no direct PDF path or citation_pdf_url meta tag found". This is anti-bot, not a missing file — and chasing per-host anti-bot fixes for a 40%-tool was not justified.

## What was removed

| Surface | Detail |
|---|---|
| `src/scraper/download_pdf.py` | `download_pdf_workflow` + resolution chain (blacklist → github-blob → TIER1 transform → direct `.pdf` → multi-step `citation_pdf_url`) |
| `src/scraper/pdf_chain.py` | chain primitives: `HARD_BLACKLIST`, `TIER1_DOMAINS`, `apply_tier1_transform`, `is_blacklisted`, `is_github_blob`, `should_download_as_pdf`, `parse_citation_pdf_url`, `extract_citation_pdf_url` |
| `src/scraper/download_logger.py` | per-call JSONL log (`download_log.jsonl`) — built to measure chain effectiveness over weeks; never reached a verdict before removal |
| `cli.py` | `download_pdf` subcommand + the `should_download_as_pdf` auto-routing weiche in the `scrape_url` handler |
| Per-URL Download Log documentation | obsolete with the logger, removed |

## New behavior

`scrape_url` on a `.pdf`-suffix URL returns the error `PDF must be downloaded by the user: <url>` (inline `urlparse(url).path.lower().endswith(".pdf")` check in `cli.py` — NO `pdf_chain` dependency reintroduced) instead of scraping garbage. Non-PDF URLs scrape as before.

"Tell the user which PDFs/books" is a skill-level concern, served by the existing search-side filters — not by any download code.

## What was kept

- **Search-side PDF/book surfacing** — `src/search/pdf_filter.py`, `src/search/book_whitelist.py`, the `--pdf` / `--books` / `--docs` flags. Independent of `pdf_chain` (only a comment referenced it). This is the mechanism that surfaces PDF/book URLs to the user.
- **Dev artifacts (kept, now non-functional)** — `dev/scrape_pipeline/test_pdf_chain.py` and `dev/search_pipeline/16_search_to_pdf_probe.py` import the deleted `pdf_chain` and will `ImportError` if run. Retained on purpose as historical record of the download-viability investigation (probes 14/15/16 measured direct-GET vs multi-step downloadability across the search pool).

## Why not keep a TIER1-aware guard

The original `should_download_as_pdf` also flagged TIER1 academic landing/PDF URLs without a `.pdf` suffix (e.g. arxiv `/pdf/<id>`). Reintroducing the TIER1 domain list purely to widen the scrape_url error guard was rejected — it would resurrect part of the chain logic the removal set out to delete. The `.pdf`-suffix check is the minimal, dependency-free detection; the arxiv `/pdf/<id>`-without-suffix edge is left to skill-level guidance (give the user the URL).
