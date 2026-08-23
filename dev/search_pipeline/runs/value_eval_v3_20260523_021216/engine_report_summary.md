# Engine Report Summary — value_eval_v2

**Run:** 20260523_021216
**Pairs:** 16 (4 modes × 4 queries)

## Per-Engine Aggregate

| Engine | n | OK | EMPTY% | BLOCK% | TIMEOUT% | ERROR% | Total URLs | Mean URLs/Pool | Dominant Failure |
|--------|---|----|----|----|----|---|---|---|---|
| crossref | 16 | 16 | 0 | 0 | 0 | 0 | 3200 | 200.0 | — |
| duckduckgo | 16 | 16 | 0 | 0 | 0 | 0 | 160 | 10.0 | — |
| google | 16 | 13 | 0 | 19 | 0 | 0 | 136 | 8.5 | EMPTY_BLOCK |
| lobsters | 16 | 16 | 0 | 0 | 0 | 0 | 216 | 13.5 | — |
| mojeek | 16 | 16 | 0 | 0 | 0 | 0 | 160 | 10.0 | — |
| open_library | 16 | 4 | 75 | 0 | 0 | 0 | 16 | 1.0 | EMPTY |
| openalex | 16 | 16 | 0 | 0 | 0 | 0 | 2080 | 130.0 | — |
| semantic_scholar | 16 | 16 | 0 | 0 | 0 | 0 | 152 | 9.5 | — |
| stack_exchange | 16 | 8 | 50 | 0 | 0 | 0 | 244 | 15.2 | EMPTY |

## Per-Mode Engine Availability (OK out of 4 pairs per mode)

| Engine | general | pdf | books | docs |
|--------|---------|-----|-------|------|
| crossref | 4/4 | 4/4 | 4/4 | 4/4 |
| duckduckgo | 4/4 | 4/4 | 4/4 | 4/4 |
| google | 1/4 | 4/4 | 4/4 | 4/4 |
| lobsters | 4/4 | 4/4 | 4/4 | 4/4 |
| mojeek | 4/4 | 4/4 | 4/4 | 4/4 |
| open_library | 1/4 | 1/4 | 1/4 | 1/4 |
| openalex | 4/4 | 4/4 | 4/4 | 4/4 |
| semantic_scholar | 4/4 | 4/4 | 4/4 | 4/4 |
| stack_exchange | 2/4 | 2/4 | 2/4 | 2/4 |
