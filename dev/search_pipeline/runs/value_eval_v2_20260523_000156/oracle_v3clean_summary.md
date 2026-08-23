# Oracle v3clean Summary

**v2 ref:** `value_eval_v2_20260523_000156`
**Drop engines:** ['google', 'semantic_scholar']

## Loss Pairs — Backfill Detail

### general_transformer_attention_mechanis

**Lost picks (google/semantic_scholar only):**
- `https://sebastianraschka.com/blog/2023/self-attention-from-scratch.html`
- `https://www.ibm.com/think/topics/attention-mechanism`

**Replacement picks:**
- rank 9: `https://deeprevision.github.io/posts/001-transformer/`
  - 'The Transformer Blueprint: A Holistic Guide to the Transformer Neural Network Architecture' — Lobsters-surfaced (pos=1, community quality signal), practitioner-grade implementation depth comparable to the dropped sebastianraschka.com self-attention tutorial. Primary technical guide covering attention mechanisms end-to-end.
- rank 10: `https://aman.ai/primers/ai/LLM/#overview`
  - Aman.ai AI Primers 'Overview of Large Language Models' — Lobsters-surfaced (pos=3), comprehensive reference covering attention mechanisms as core LLM architecture. Well-regarded in the ML practitioner community as authoritative explainer. Replaces the dropped ibm.com attention-mechanism overview.

### general_postgresql_index_types_btree_g

**Lost picks (google/semantic_scholar only):**
- `https://www.semanticscholar.org/paper/Comparative-analysis-of-indexing-strategies-in-load-Zolotukhina/a1bcf6c3ddb11cd3dc7cb9cafbbae31fd2c222f7`

**Replacement picks:**
- rank 10: `https://habr.com/ru/company/postgrespro/blog/441962/`
  - Habr/PostgresPro 'Indexes in PostgreSQL' — authored by PostgreSQL Pro (vendor documentation quality), Lobsters-surfaced (pos=1). Comprehensive technical reference covering all PostgreSQL index types (B-tree, GIN, GiST, Hash, BRIN) with performance trade-offs. Directly matches the query.

### pdf_postgresql_index_types_btree_g

**Lost picks (google/semantic_scholar only):**
- `https://www.semanticscholar.org/paper/Intra-page-Indexing-in-Generalized-Search-Trees-of-Borodin-Mirvoda/a402de1fc7c031608b9a55083b5084aaf4390e97`

**Replacement picks:**
- rank 10: `https://habr.com/ru/company/postgrespro/blog/441962/`
  - Habr/PostgresPro 'Indexes in PostgreSQL' — authored by PostgreSQL Pro (vendor documentation quality), Lobsters-surfaced (pos=1). Replaces the dropped SemanticScholar intra-page indexing paper; directly covers PostgreSQL index type performance (B-tree, GIN, GiST) matching the query.

### docs_contrastive_learning_self_supe

**Lost picks (google/semantic_scholar only):**
- `https://www.semanticscholar.org/paper/Supervised-Contrastive-Learning-Khosla-Teterwak/38643c2926b10f6f74f122a7037e2cd20d77c0f1`

**Replacement picks:**
- rank 10: `https://arxiv.org/pdf/2510.10572`
  - arXiv 2510.10572 'Understanding Self-supervised Contrastive Learning through Supervised ...' — primary research source directly on the query topic (DuckDuckGo pos=1). Replaces the dropped SemanticScholar Supervised Contrastive Learning paper with its underlying arXiv primary source.

## All 16 Pairs — Survival Count

| pair | surviving | lost | backfilled | top_10_count |
|------|-----------|------|------------|--------------|
| general_transformer_attention_mechanis | 8 | 2 | 2 | 10 |
| general_postgresql_index_types_btree_g | 9 | 1 | 1 | 10 |
| general_python_asyncio_event_loop_conc | 10 | 0 | 0 | 10 |
| general_contrastive_learning_self_supe | 10 | 0 | 0 | 10 |
| pdf_transformer_attention_mechanis | 10 | 0 | 0 | 10 |
| pdf_postgresql_index_types_btree_g | 9 | 1 | 1 | 10 |
| pdf_python_asyncio_event_loop_conc | 10 | 0 | 0 | 10 |
| pdf_contrastive_learning_self_supe | 10 | 0 | 0 | 10 |
| books_transformer_attention_mechanis | 10 | 0 | 0 | 10 |
| books_postgresql_index_types_btree_g | 10 | 0 | 0 | 10 |
| books_python_asyncio_event_loop_conc | 10 | 0 | 0 | 10 |
| books_contrastive_learning_self_supe | 10 | 0 | 0 | 10 |
| docs_transformer_attention_mechanis | 10 | 0 | 0 | 10 |
| docs_postgresql_index_types_btree_g | 10 | 0 | 0 | 10 |
| docs_python_asyncio_event_loop_conc | 10 | 0 | 0 | 10 |
| docs_contrastive_learning_self_supe | 9 | 1 | 1 | 10 |
