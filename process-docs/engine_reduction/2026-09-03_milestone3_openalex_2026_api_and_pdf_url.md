# Milestone 3 — OpenAlex 2026 API Migration + pdf_url Through the Result Chain

2026-09-03

## Context

Milestone 2 stabilized the production pool at 8 engines with `openalex` as the sole specialised one. Milestone 1 measured that `best_oa_location.pdf_url` is populated on ~90% of works overall and ~82% of the top-10 slice actually surfaced to agents (`process-docs/engine_reduction/2026-09-03_openalex_pdf_url_availability.md`), and vendor docs captured the same day showed `OPENALEX_MAILTO` is dead (ignored by the API since 2026-02), `per_page` capped at 100 (the module was requesting 200), and 429 vs 403 carrying distinct meanings (budget-exceeded vs forbidden-resource). Milestone 3 closed both gaps: bring `openalex.py` onto the 2026 API surface, and thread `pdf_url` through the same four-touch-point chain the `date` field needed (`process-docs/search_pipeline/2026-08-02_thread_date_through_result_chain.md`: `result.py` → `merge.py`'s per-winner `SearchResult` reconstruction → `cache.py`'s serialize/render).

## API migration

`OPENALEX_MAILTO` removed entirely — no `mailto` param is ever sent again. Replaced with an optional `OPENALEX_API_KEY` env var, sent as `api_key` only when set (no default, no hardcoded key). `per_page` clamped via `min(max_results, 100)`; `ENGINE_MAX_RESULTS["openalex"]` in `search_web.py` dropped from 200 to 100 to match — the two were already inconsistent before this milestone (module requested 200, vendor max was 100 all along per the 2026-09-03 vendor docs), so the clamp is a correctness fix, not just future-proofing.

## 429 as a tripwire, not a silent empty

Before this milestone, `_fetch_results` treated 429 and 403 identically — both returned `None`, both surfaced as `search()` returning `[]` with no way to distinguish "budget exhausted" from "legitimately zero results" or "forbidden resource". Per the tripwire principle (a failure surfaces, it does not disguise itself as a valid empty), `search_with_reason` was added (the `base.py`/`scholar.py` pattern already established for Stage-2 empty-reason engines) so 429 now returns `S.EMPTY_BLOCK` explicitly. 403 was deliberately left as a plain empty with no reason — the milestone scope named only 429 for this treatment, and 403 (forbidden resource, e.g. hitting a collections endpoint) is a different failure class the vendor docs explicitly distinguish from rate limiting; conflating them into the same `EMPTY_BLOCK` reason would have been a scope-exceeding guess, not something either the milestone brief or the vendor docs asked for.

## pdf_url extraction

`_extract_pdf_url(work)` reads `work.get("best_oa_location")` (nullable) then its `.get("pdf_url")` (nullable independently) — two separate null checks, since a work can have a `best_oa_location` object with no `pdf_url` (landing-page-only OA) as well as no `best_oa_location` at all (no OA found). No validation beyond presence: per milestone 1's finding of one `.jpg`-asset `pdf_url` in the sample, the field is vendor data passed through as-is — flagged as a Gotcha in `src/search/DOCS.md`, not defended against in code (no test-worthy failure pattern emerged from that single observation, and milestone 1 explicitly declined to invent one). `_pick_url` (arxiv > doi > id) is untouched and stays the canonical `url` field — `pdf_url` is an additive signal, never a URL substitute.

## Chain-threading verification

Same four touch points as the `date` precedent: `result.py` (`pdf_url: str | None = None`, dataclass default so no existing keyword-only `SearchResult(...)` call site anywhere in `src/` or `dev/` breaks — verified via a full-repo grep of `SearchResult(` construction sites, all keyword-based), `merge.py` (`build_engine_pools`'s per-winner reconstruction now names `pdf_url=winner.pdf_url` explicitly — confirmed via the same reasoning the date entry documented: an unnamed field silently drops here, not at the dataclass level), `cache.py` (`cache_write` serializes `pdf_url` into the per-entry dict; `format_engine_pool` reads it via `.get()` so a cache file written before this milestone, up to 1h old under the existing TTL, renders with no `PDF:` line and no `KeyError` — mirrors the `date` field's backward-compat handling exactly).

## PDF line placement

Rendered directly after `URL:` and before `Date:` — `Title / URL / PDF / Date / Snippet` — per the milestone brief's explicit instruction ("directly after the URL: line"), not appended after `Date:`. No independent reasoning needed here beyond following the stated order.

## Verification

`./venv/bin/python3 -m pytest`: 354 passed, 0 failed (full suite — the 11-failure baseline noted in the `date`-threading entry from 2026-08-02 is no longer present in this environment; not investigated further, out of this milestone's scope). Live end-to-end: `search_web "Basner McGuire systematic review environmental noise effects on sleep 2018"` → `search_engine_drilldown --engine openalex` — 9/10 entries carried a `PDF:` line directly after `URL:`, one entry (a `doi.org` publisher without an indexed OA location) had none, consistent with milestone 1's ~82-90% availability measurement on real queries.
