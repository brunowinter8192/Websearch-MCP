# Value Eval Summary v3 — 12-Method Phase 13

**Pairs:** 16 / 16  **Oracle:** v3clean

## Per-Mode Mean Jaccard

| Mode | M1 C1 Overlap-Count | M2 RRF post-bucket | M3 Structural URL | M4 BM25 vanilla | M5 BM25-Capped | M6 C3 Cross-Encoder | M7 C3+InstrPrefix | M8 RRF+C3 Hybrid | M9 SPLADE | M10 SPLADE+C3 | M11 C3→LLM-Filter | M12 LLM-Selector | Winner |
|------|---|---|---|---|---|---|---|---|---|---|---|---|--------|
| general | 0.164 | 0.164 | 0.144 | 0.197 | 0.179 | 0.242 | 0.276 | 0.183 | 0.329 | 0.329 | 0.303 | 0.127 | **M9 SPLADE** |
| pdf | 0.131 | 0.131 | 0.131 | 0.113 | 0.113 | 0.218 | 0.262 | 0.179 | 0.221 | 0.221 | 0.240 | 0.181 | **M7 C3+InstrPrefix** |
| books | 0.115 | 0.115 | 0.127 | 0.098 | 0.098 | 0.162 | 0.216 | 0.113 | 0.185 | 0.185 | 0.252 | 0.213 | **M11 C3→LLM-Filter** |
| docs | 0.131 | 0.131 | 0.129 | 0.082 | 0.179 | 0.195 | 0.232 | 0.148 | 0.273 | 0.273 | 0.239 | 0.246 | **M9 SPLADE** |

## Overall Mean Jaccard

| Method | Mean Jaccard |
|--------|--------------|
| M1 C1 Overlap-Count | 0.135 |
| M2 RRF post-bucket | 0.135 |
| M3 Structural URL | 0.133 |
| M4 BM25 vanilla | 0.122 |
| M5 BM25-Capped | 0.142 |
| M6 C3 Cross-Encoder | 0.204 |
| M7 C3+InstrPrefix | 0.246 |
| M8 RRF+C3 Hybrid | 0.155 |
| M9 SPLADE | 0.252 |
| M10 SPLADE+C3 | 0.252 |
| M11 C3→LLM-Filter | 0.259  ← **WINNER** |
| M12 LLM-Selector | 0.192 |

## Per-Mode Mean Latency (ms)

| Mode | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 |
|------|---|---|---|---|---|---|---|---|---|---|---|---|
| general | 0 | 0 | 0 | 10 | 1 | 1836 | 1876 | 0 | 1798 | 0 | 6914 | 9758 |
| pdf | 0 | 0 | 0 | 10 | 1 | 1853 | 1938 | 0 | 1798 | 0 | 7949 | 11217 |
| books | 0 | 0 | 0 | 10 | 1 | 1882 | 1981 | 0 | 1491 | 0 | 7083 | 11005 |
| docs | 0 | 0 | 0 | 10 | 1 | 1862 | 1956 | 0 | 1510 | 0 | 7664 | 10338 |

## Per-Method Latency Statistics (across 16 pairs)

| Method | Mean | p50 | p95 | Max | Tokens in/out (LLM) |
|--------|------|-----|-----|-----|---------------------|
| M1 C1 Overlap-Count | 0 | 0 | 0 | 0 | — |
| M2 RRF post-bucket | 0 | 0 | 0 | 0 | — |
| M3 Structural URL | 0 | 0 | 0 | 0 | — |
| M4 BM25 vanilla | 10 | 12 | 15 | 15 | — |
| M5 BM25-Capped | 1 | 1 | 1 | 1 | — |
| M6 C3 Cross-Encoder | 1858 | 1908 | 2499 | 2499 | — |
| M7 C3+InstrPrefix | 1938 | 1912 | 2653 | 2653 | — |
| M8 RRF+C3 Hybrid | 0 | 0 | 0 | 0 | — |
| M9 SPLADE | 1649 | 1574 | 2586 | 2586 | — |
| M10 SPLADE+C3 | 0 | 0 | 0 | 0 | — |
| M11 C3→LLM-Filter | 7403 | 7502 | 8791 | 8791 | 25314/4307 |
| M12 LLM-Selector | 10579 | 11087 | 13420 | 13420 | 58837/4453 |

## Quality × Latency Pareto

| Method | Mean Jaccard | Mean Latency (ms) | Pareto Status |
|--------|--------------|-------------------|---------------|
| M11 C3→LLM-Filter | 0.259 | 7403 | Pareto-optimal |
| M9 SPLADE | 0.252 | 1649 | DOMINATED |
| M10 SPLADE+C3 | 0.252 | 0 | Pareto-optimal |
| M7 C3+InstrPrefix | 0.246 | 1938 | DOMINATED |
| M6 C3 Cross-Encoder | 0.204 | 1858 | DOMINATED |
| M12 LLM-Selector | 0.192 | 10579 | DOMINATED |
| M8 RRF+C3 Hybrid | 0.155 | 0 | DOMINATED |
| M5 BM25-Capped | 0.142 | 1 | DOMINATED |
| M1 C1 Overlap-Count | 0.135 | 0 | DOMINATED |
| M2 RRF post-bucket | 0.135 | 0 | DOMINATED |
| M3 Structural URL | 0.133 | 0 | DOMINATED |
| M4 BM25 vanilla | 0.122 | 10 | DOMINATED |
