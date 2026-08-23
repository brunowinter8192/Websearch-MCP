# Value Eval Summary

**Pairs:** 16 / 16  
**Oracle:** present  

## Per-Mode Mean Jaccard

| Mode | C1 Overlap-Count | C2 BM25 vanilla | C2' BM25-Capped | C3 Cross-Encoder | Winner |
|------|---|---|---|---|--------|
| general | 0.164 | 0.179 | 0.164 | 0.242 | **C3 Cross-Encoder** |
| pdf | 0.113 | 0.131 | 0.118 | 0.213 | **C3 Cross-Encoder** |
| books | 0.115 | 0.100 | 0.118 | 0.236 | **C3 Cross-Encoder** |
| docs | 0.117 | 0.098 | 0.197 | 0.179 | **C2' BM25-Capped** |

## Overall Winner

| Method | Mean Jaccard (all pairs) |
|--------|--------------------------|
| C1 Overlap-Count | 0.127 |
| C2 BM25 vanilla | 0.127 |
| C2' BM25-Capped | 0.149 |
| C3 Cross-Encoder | 0.218  ← **WINNER** |

## Mode-Specific Signals (margin ≥ 0.10 vs second-best)

- **books**: C3 Cross-Encoder leads by 0.118 (vs C2' BM25-Capped at 0.118)
