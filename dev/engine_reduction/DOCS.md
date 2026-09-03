# dev/engine_reduction/

## Role
Measurement scripts backing the 14-engine-to-1-specialised-engine reduction decision (keep `openalex`, cut the other 7 non-general engines). Probes here answer specific go/no-go questions for each milestone of that reduction; they do not touch `src/`.

## Modules

### openalex_pdf_probe.py (226 LOC)

**Purpose:** Milestone 1 measurement — for 7 real agent queries, how often does an OpenAlex work carry a direct PDF URL (`best_oa_location.pdf_url`) vs a landing page only vs no OA location, over the full 100-result page and over the top 10; plus a `type` breakdown of pdf_url-present works and an eyeball listing (title/type/chosen URL/pdf_url) for 2 queries.
**Reads:** none (live HTTP fetch against `https://api.openalex.org/works`, no `mailto`, no API key).
**Writes:** `01_reports/openalex_pdf_probe_<ts>.md`.
**Called by:** CLI only. `./venv/bin/python3 dev/engine_reduction/openalex_pdf_probe.py`.
**Calls out:** `httpx`. `_pick_url` is a dev-script-isolation inline copy of `src/search/engines/openalex.py::_pick_url` (ids.arxiv > doi > id) — not a shared import, matching the isolation convention of `dev/search_pipeline/25..31_*_probe.py`, so the probe keeps measuring even if `src/` changes underneath it later.

---

## State
No shared state; each run is self-contained. Report outputs live in `01_reports/` (readable reports), separate from any future data-dump folder, per the dev/ layout convention.

## Gotchas
OpenAlex's keyless budget is $0.10/day at $0.001/search call — 7 queries per run is trivial, but a 429 means budget or per-minute rate exceeded; the script stops immediately on 429 and reports the partial results rather than retrying. `open_access.oa_url` is NOT used as a PDF signal here (it may be a landing page) — only `best_oa_location.pdf_url` counts as "has PDF".
