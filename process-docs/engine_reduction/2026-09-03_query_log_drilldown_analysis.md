# Query-Log Drilldown Analysis — Why Seven Specialised Engines Became One

2026-09-03

## Question

The pool carried seven non-general engines (crossref, openalex, semantic_scholar, stack_exchange, open_library, lobsters, marginalia) next to seven general ones. The user had not consciously seen an agent use any of them in months, and had observed that general engines find papers too. Question: what value do the specialised engines actually deliver, measured by whether agents drill into them?

## Data

`src/logs/query_log.jsonl`, 2026-08-20 to 2026-09-03: 214 `engine_run` records, 297 `drilldown` records. The log is pruned to a recent window, so earlier months are not covered. Queries were classified by keyword regex into academic (7), German (83), other English (124); the boundary between academic and other English is coarse.

## Findings

Drilldowns per engine over 297: google 84, duckduckgo 65, brave 61, startpage 40, bing 27, yandex 10, openalex 5, crossref 2, semantic_scholar 2, mojeek 1, stack_exchange / open_library / lobsters / marginalia 0. Nine of 297 drilldowns went to specialised engines.

Hit rate (runs with >0 results out of 214): crossref 210, openalex 70, semantic_scholar 35, lobsters 19, marginalia 17, open_library 8, stack_exchange 4. By query class, the paper engines delivered on the academic queries (crossref 7/7, openalex 6/7, semantic_scholar 5/7) and near-nothing on German ones (openalex 9/83, semantic_scholar 5/83). The four niche engines returned nothing on more than 90% of runs regardless of class — they answer only programming, book-catalog or tech-blog queries, which the real query mix hardly contains.

Two engines failed independent of query type. semantic_scholar (DOM-scraped) hit EMPTY_NO_CONTAINER 133x and TIMEOUT_WATCHDOG 38x, and was the sweep bottleneck 84x per the watchdog comment in `search_web.py`. crossref returned up to 200 results on 82/83 German queries — delivering is not the same as being useful; two drilldowns on 210 non-empty runs say the results were noise.

Decisive observation: on the seven academic queries the paper engines delivered, yet seven of eight drilldowns still went to google, duckduckgo and brave. The general engines found the papers' landing pages, and nothing in the breakdown table made the paper engines look like the better source.

## Decision

Keep exactly one specialised engine and make it carry something general engines cannot: the direct open-access PDF URL, because the user's paper workflow is "agent hands over URLs, user downloads". openalex was chosen over crossref, semantic_scholar and arXiv: largest open corpus (300M+ works as of 2026-09 per vendor docs, books and book chapters included as work types), pure JSON API without browser, no CAPTCHA, and a per-work `best_oa_location.pdf_url`. arXiv was rejected as sole engine: STEM-only preprints, roughly 2.5M works, and everything on arXiv is in OpenAlex with a link to the arXiv PDF. The six other engines were deleted rather than parked (parked code is dead code in every DOCS.md and review; history lives in `process-docs/engine_expansion/`).

Mojeek stayed in the pool despite 199/214 EMPTY_BLOCK, because the session scope named only the specialised axis; its keep-or-drop is an open item.

A web search during the session surfaced that OpenAlex replaced its polite pool with API keys in 2026-02; the vendor docs were captured into `websearch-reference` and drove the milestone-3 API migration.

## Area decision

New area `engine_reduction` rather than continuing `engine_expansion`: the work draws on `engine_expansion/` (engine history, keep-criterion) and on `search_pipeline/` (the result-chain threading precedent) alike, and a reduction filed under "expansion" would mislead later readers.

## Sources

- `src/logs/query_log.jsonl` (pruned window 2026-08-20 to 2026-09-03)
- `process-docs/engine_expansion/` (2026-06-09 academic-noise field observation, 2026-07-21 keep-criterion, openalex and semantic_scholar records)
- `process-docs/search_pipeline/` (date-field chain threading)
- `websearch-reference` collection, `help_openalex_org_*` documents (captured 2026-09-03)
