# Worker Report: PDF-to-Markdown Conversion (5 Papers)

## Task
Convert 5 IR/search evaluation PDFs to cleaned Markdown and produce chunked JSON files ready for RAG indexing into the `searxng` collection. Skip indexing step (SPLADE bug blocks it).

## Results

All 5 PDFs successfully converted, cleaned, and chunked. Total: **689 chunks**.

| PDF | Stem | Raw Lines | Clean Lines | Chunks | Status |
|-----|------|-----------|-------------|--------|--------|
| 1509.08396v1.pdf | Meta_Search_Engine_Optimization | 283 | 276 | 51 | DONE |
| 2404.01012v3.pdf | QPP_GenRE_Query_Performance_Prediction | 695 | 682 | 183 | DONE |
| 3241064.pdf | IR_Evaluation_Without_Relevance_Judgments | 641 | 626 | 168 | DONE |
| chapelle_etal_12a.pdf | Interleaved_Search_Evaluation | 866 | 858 | 207 | DONE |
| clickthrough_2.pdf | Clickthrough_Search_Optimization | 374 | 374 | 80 | DONE |

## Cleanup Notes

**PDF 1 (Meta Search Engine Optimization):** Minimal LaTeX. Fixed broken images (4), LaTeX OCR artifacts in HTML code examples (`conten ^ { \iota }` etc.), `\mathscr` heading, letter-spaced math variables, superscript footnote.

**PDF 2 (QPP-GenRE):** Heavy LaTeX throughout (IR evaluation formulas, LLM training loss). Fixed via agent + manual residual pass (22 additional fixes): broken images (9), `\mathcal`/`\mathbb`/`\mathsf`, letter-spaced metrics (`R R @k` → `RR@k`), `\begin{array}`, `\bullet`, `\sum`, `\frac`, `\mid`, `\left[`/`\right]`. 2 `??` OCR placeholders remain (genuinely unreadable symbols in source).

**PDF 3 (IR Evaluation Without Relevance Judgments):** Very clean. Fixed broken images (8), `\longrightarrow`, `\mathcal { P }`, journal metadata artifacts (RESEARCH-ARTICLE, Published/Accepted lines), duplicate title.

**PDF 4 (Interleaved Search Evaluation):** Complex LaTeX with `\mathcal` ranking function names (84×), `\succ` comparison operator (59×), algorithm pseudocode. Fixed via agent + 1 manual residual fix (`{ \mathcal A } _Y`). Letter-spaced DCG@/NDCG@ cleaned.

**PDF 5 (Clickthrough Search Optimization):** Proof appendix with SVM optimization math (`\frac`, `\sum`, `\binom`, `\begin{array}`, letter-spaced variable names like `A v g P r e c`). Fixed via partial direct cleanup + agent pass.

## Files Changed

**RAG project** (`RAG/data/documents/searxng/`):
- `Meta_Search_Engine_Optimization/raw/Meta_Search_Engine_Optimization.md` — MinerU output
- `Meta_Search_Engine_Optimization/Meta_Search_Engine_Optimization.md` — cleaned
- `Meta_Search_Engine_Optimization.json` — 51 chunks
- `QPP_GenRE_Query_Performance_Prediction/raw/QPP_GenRE_Query_Performance_Prediction.md`
- `QPP_GenRE_Query_Performance_Prediction/QPP_GenRE_Query_Performance_Prediction.md`
- `QPP_GenRE_Query_Performance_Prediction.json` — 183 chunks
- `IR_Evaluation_Without_Relevance_Judgments/raw/IR_Evaluation_Without_Relevance_Judgments.md`
- `IR_Evaluation_Without_Relevance_Judgments/IR_Evaluation_Without_Relevance_Judgments.md`
- `IR_Evaluation_Without_Relevance_Judgments.json` — 168 chunks
- `Interleaved_Search_Evaluation/raw/Interleaved_Search_Evaluation.md`
- `Interleaved_Search_Evaluation/Interleaved_Search_Evaluation.md`
- `Interleaved_Search_Evaluation.json` — 207 chunks
- `Clickthrough_Search_Optimization/raw/Clickthrough_Search_Optimization.md`
- `Clickthrough_Search_Optimization/Clickthrough_Search_Optimization.md`
- `Clickthrough_Search_Optimization.json` — 80 chunks

Debug scripts in each `<Stem>/debug/` subfolder (process artifacts, not committed).

## Open Issues

- **Indexing skipped** (as instructed): SPLADE bug blocks indexing. Run `workflow.py index-json --input <stem>.json` for each file once bug is fixed.
- **PDF 2 residual `??` placeholders**: 2 remain in QPP-GenRE where source symbols were unreadable by OCR.
- **PDF 2 `R -hat` notation**: `\hat{R}` (set notation) was rendered as `R -hat` — readable but not ideal. Acceptable for RAG purposes.
- **Output path**: All files in RAG project repo (`RAG/data/documents/searxng/`), NOT plugin cache. Verified.
