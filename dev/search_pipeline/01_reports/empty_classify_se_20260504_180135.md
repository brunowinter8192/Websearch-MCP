# StackEx EMPTY Classification — 20260504_180135

Source: `dev/search_pipeline/01_reports/search_smoke_20260504_023641.md`
Method: direct httpx probe against api.stackexchange.com/2.3/search/advanced, anonymous quota.

## Summary

- ENGINE_EMPTY: 12/15
- ENGINE_NICHE: 0/15
- PIPELINE_BUG: 0/15
- RATE_LIMITED: 3/15
- BOT_BLOCK: 0/15
- UNKNOWN: 0/15

## Per-Query

| # | Smoke # | Query | HTTP | SO total | SO items | XS total | XS items | quota_left | Classification |
|---|---------|-------|------|----------|----------|----------|----------|------------|----------------|
| 1 | 3 | fastapi websocket reconnect handler | 200 | 0 | 0 | None | None | 226 | ENGINE_EMPTY |
| 2 | 10 | RLHF reinforcement learning human feedback | 200 | 0 | 0 | None | None | 224 | ENGINE_EMPTY |
| 3 | 12 | RAG retrieval augmented generation benchmark | 200 | 0 | 0 | None | None | 222 | ENGINE_EMPTY |
| 4 | 13 | climate change carbon capture technology 2025 | 200 | 0 | 0 | None | None | 220 | ENGINE_EMPTY |
| 5 | 14 | epidemiology cohort study design methodology | 200 | 0 | 0 | None | None | 218 | ENGINE_EMPTY |
| 6 | 15 | Bewerbung Lebenslauf Format Deutschland | 200 | 0 | 0 | None | None | 216 | ENGINE_EMPTY |
| 7 | 16 | Mietvertrag Kündigungsfrist gesetzliche Regelung | 200 | 0 | 0 | None | None | 214 | ENGINE_EMPTY |
| 8 | 17 | GmbH Gründung Kosten Schritte | 200 | 0 | 0 | None | None | 212 | ENGINE_EMPTY |
| 9 | 18 | Krankenversicherung Vergleich gesetzlich privat | 200 | 0 | 0 | None | None | 210 | ENGINE_EMPTY |
| 10 | 19 | Python Programmierung Anfänger Tutorial deutsch | 200 | 0 | 0 | None | None | 208 | ENGINE_EMPTY |
| 11 | 21 | crawl4ai stealth browser detection bypass | 200 | 0 | 0 | None | None | 206 | ENGINE_EMPTY |
| 12 | 22 | pydoll chromium CDP automation | 200 | 0 | 0 | None | None | 204 | ENGINE_EMPTY |
| 13 | 24 | trafilatura vs readability content extraction | 429 | None | None | None | None | None | RATE_LIMITED |
| 14 | 25 | SPLADE sparse retrieval model implementation | 429 | None | None | None | None | None | RATE_LIMITED |
| 15 | 29 | kubernetes vs docker swarm comparison | 429 | None | None | None | None | None | RATE_LIMITED |

## Notes

- Smoke#24 `trafilatura vs readability content extraction`: SO returned HTTP 429
- Smoke#25 `SPLADE sparse retrieval model implementation`: SO returned HTTP 429
- Smoke#29 `kubernetes vs docker swarm comparison`: SO returned HTTP 429

## Caveats

**XS probes all failed (non-200) for queries 1–12.** After 12 SO probes the SE API began throttling — XS probes returned 429 (no exception, so notes are silent; xs_http was set to 429 in the record but not surfaced in the table). This means the ENGINE_NICHE vs ENGINE_EMPTY distinction cannot be confirmed from the cross-site probe for any query.

Practical interpretation:
- Queries 1–12: SO confirmed HTTP 200 total=0 items=0. From the production engine perspective (`site=stackoverflow`) these are genuine ENGINE_EMPTY. Whether other SE sites (datascience, stats, superuser…) have results is undetermined — especially relevant for RLHF (#10), RAG (#12), crawl4ai (#21), pydoll (#22), which could plausibly live on datascience.se or similar.
- Queries 13–15: SO probe itself returned 429 before any data was obtained — classification is RATE_LIMITED (inconclusive for both SO and XS).

**To resolve ENGINE_NICHE for the 12 SO-empty queries:** retry cross-site probes after daily quota reset, or probe individual relevant sites (datascience, stats, unix, superuser) per query. The anonymous quota is 300 req/day; today's run consumed ~24+ SO calls.
