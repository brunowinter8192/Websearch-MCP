# Oracle — docs × postgresql index types btree gin gist performance

Top-10 selected from 40 URLs in the oracle pool.

## Selection Criteria

Docs mode: official PostgreSQL documentation pages (postgresql.org, postgrespro.com/docs) rank first. Followed by technical series from PostgreSQL commercial providers (Postgres Pro/Postgres Professional), then academic performance evaluations, then comprehensive practical guides. Off-topic entries (Bispectral Index anesthesiology, CityGML database, "The Gist of Reading", VACUUM parallelism) are excluded.

## Top-10

### 1. PostgreSQL: Documentation: 18: 11.2. Index Types
**URL:** https://www.postgresql.org/docs/current/indexes-types.html
**Reason:** Official PostgreSQL documentation (v18) on all index types — the canonical reference covering B-tree, Hash, GiST, SP-GiST, GIN, BRIN, and bloom.

### 2. PostgreSQL: Documentation: 18: 65.4. GIN Indexes
**URL:** https://www.postgresql.org/docs/current/gin.html
**Reason:** Official PostgreSQL documentation on GIN internals, extensibility, and performance — deep reference for GIN specifically.

### 3. PostgreSQL : Documentation: 14: 11.2. Index Types
**URL:** https://postgrespro.com/docs/postgresql/14/indexes-types
**Reason:** Official PostgreSQL v14 index types documentation via Postgres Pro — same canonical reference for the previous stable release.

### 4. Btree_gin - Nile Documentation
**URL:** https://www.thenile.dev/docs/extensions/btree_gin
**Reason:** Nile Documentation for the btree_gin extension — explains how GIN indexes can support B-tree indexable data types, covering the B-tree/GIN intersection directly relevant to the query.

### 5. Indexes in PostgreSQL — 7 (GIN) / Habr
**URL:** https://habr.com/en/companies/postgrespro/articles/448746/
**Reason:** Postgres Pro technical series on GIN index internals — deep technical coverage from PostgreSQL's commercial support provider; part of a comprehensive series covering hash, B-tree, GiST, SP-GiST.

### 6. Indexes in PostgreSQL — 5 (GiST)
**URL:** https://medium.com/postgres-professional/indexes-in-postgresql-5-gist-86e19781b5db
**Reason:** Postgres Professional 'Indexes in PostgreSQL — 5 (GiST)' — deep technical treatment of GiST extensibility and internals from the official PostgreSQL support company.

### 7. Indexing in PostgreSQL: Performance Evaluation and Use Cases
**URL:** https://doi.org/10.20944/preprints202511.2170.v1
**Reason:** Preprint with comprehensive performance evaluation of all six native PostgreSQL index types (B-Tree, Hash, GiST, SP-GiST, GIN, BRIN) — empirical performance data directly on the query topic.

### 8. Postgres Indexes Beyond B-Tree—GIN, GiST, BRIN, SP-GiST
**URL:** https://explain.technical.li/postgres-indexes-beyond-b-tree/
**Reason:** Practical guide with concrete performance benchmarks (20-1000x B-tree improvement) for GIN, GiST, BRIN — directly covers the advanced index types in the query.

### 9. PostgreSQL Indexes Best Practices: Choosing the Right Index for Every ...
**URL:** https://bigdataboutique.com/blog/postgresql-indexes-best-practices
**Reason:** Comprehensive production guide covering B-tree, GIN, GiST, BRIN with when-to-use criteria, pitfalls, and optimization techniques for production workloads.

### 10. A Comparative Experimental Study of Index Performance in MongoDB and PostgreSQL
**URL:** https://doi.org/10.64149/j.ijesrt.15.4.22-31
**Reason:** Empirical performance study of PostgreSQL indexes — provides comparative performance data across index types and query patterns.
