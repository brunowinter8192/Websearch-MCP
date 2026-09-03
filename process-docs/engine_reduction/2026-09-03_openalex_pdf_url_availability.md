# OpenAlex PDF-URL Availability Probe (Milestone 1)

2026-09-03

## Context

The search pool fans out to 14 engines. A query-log analysis (214 searches, 2026-08-20 to 2026-09-03) showed the seven non-general engines are essentially never drilled by agents. The reduction decision: keep exactly one specialised engine, `openalex`, and make it useful for the user's paper-download workflow — the user downloads PDFs from URLs the agent hands over, so the drilldown needs to carry a direct PDF URL when OpenAlex has one, not just the DOI/landing-page URL the current `_pick_url` (ids.arxiv > doi > id) selects.

Milestone 1 asked: on real agent queries, how often does an OpenAlex work actually carry a direct PDF URL (`best_oa_location.pdf_url`), so milestone 3 can decide how to render it. This entry is measurement only — no `src/` change.

## Method

`dev/engine_reduction/openalex_pdf_probe.py` — plain `httpx` GET against `https://api.openalex.org/works?search=<q>&per_page=100`, no `mailto` param (confirmed ignored by the API since 2026-02), no API key. 7 queries pulled verbatim from the query log (WHO noise-guideline queries, Basner/McGuire citation queries, and two non-academic-leaning queries — web-extraction benchmark, clothing-lifespan study — to check the fallback case). Each work classified via `best_oa_location`: `pdf_url` set / `best_oa_location` present but `pdf_url` null (landing page only) / `best_oa_location` null (no OA). Counted over the full up-to-100-result page and over the first 10 (the pool-cap-typical slice). `open_access.oa_url` was explicitly NOT used as a PDF signal (per vendor docs it may be a landing page, not reliably a PDF).

Full report: `dev/engine_reduction/01_reports/openalex_pdf_probe_20260903_150829.md`.

## Findings

Across all 7 queries (557 works total): 501 pdf_url set (90%), 52 landing-only (9%), 4 no-OA (1%). Restricted to the top-10 slice (61 works across 7 queries, one query returned only 1 result total): 50 pdf_url set (82%), 10 landing-only, 1 no-OA. Per query the pdf_url share ranged from 82% (Q1, top-10 4/10 landing-only) up to 100% (Q6 top-10, 10/10). The one query with a genuinely thin result set (Q5, `Basner McGuire 2018 IJERPH 15 519 sleep pdf full text` — an exact-citation-style query) returned exactly 1 OpenAlex work total, which did carry a pdf_url.

Type breakdown of pdf_url-present works is dominated by `article` in every query (68-92% of that query's pdf_url-present works), with `review`, `preprint`, `conference-paper`, `book`, `dissertation`, `report`, `book-chapter` as minor buckets — no query showed a type-driven cliff in PDF availability.

Eyeballed the first 10 results of Q3 (Basner McGuire systematic review) and Q6 (web extraction benchmark) side by side: chosen URL (`_pick_url`, current production logic) vs `best_oa_location.pdf_url`. In both sets the chosen URL was a `doi.org` redirect in all 20 rows (no arXiv IDs present), while `pdf_url` — when set — pointed at a publisher-hosted direct PDF path (e.g. `mdpi.com/.../pdf`, `sciencedirect.com/.../pdf`, `academic.oup.com/.../article-pdf/...`), one row a `.jpg` figure asset rather than the paper PDF (Q6 row 2 — `best_oa_location.pdf_url` is not always full-text; a images/supplementary-file link can occupy that field), and one row in Q3 (row 7) had `best_oa_location.pdf_url` empty despite `best_oa_location` presumably present with only a landing page (a doi.org URL and empty pdf_url both shown). The DOI URL and the pdf_url are consistently different targets — the DOI never resolves directly to the PDF path OpenAlex records.

## Implication for later milestones

The pdf_url field is populated often enough (90% overall, ~82% in the top-10 slice actually surfaced to agents) to be worth rendering distinctly from the canonical DOI URL in the drilldown output. The one observed pdf_url pointing at a non-PDF asset (an image) means milestone 3's rendering logic should not assume `pdf_url` is always a true full-text PDF without at least a sanity check, though no test-worthy pattern for that emerged from this small a sample.
