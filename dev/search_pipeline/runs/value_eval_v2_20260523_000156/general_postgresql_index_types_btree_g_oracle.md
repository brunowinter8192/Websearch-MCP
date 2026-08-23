# Oracle — general × postgresql index types btree gin gist performance

Top-10 selected from 48 URLs in the oracle pool.

## Selection Criteria

General mode: primary sources (official PostgreSQL docs), authoritative practical guides with performance focus, and empirical performance studies. Off-topic entries (Bispectral Index anesthesiology, CityGML database, iris recognition, "The Gist of Reading") are excluded. Stack Overflow answers are included when they provide specific performance data or practical decision criteria.

## Top-10

### 1. PostgreSQL: Documentation: 18: 11.2. Index Types
**URL:** https://www.postgresql.org/docs/current/indexes-types.html
**Reason:** Official PostgreSQL documentation — the canonical primary source for all index types (B-tree, Hash, GiST, SP-GiST, GIN, BRIN, bloom).

### 2. Indexing in PostgreSQL: Performance Evaluation and Use Cases
**URL:** https://doi.org/10.20944/preprints202511.2170.v1
**Reason:** Comprehensive academic preprint with empirical performance evaluation of all six native PostgreSQL index types — the most authoritative performance-focused analysis in the pool.

### 3. PostgreSQL Indexes Best Practices: Choosing the Right Index for Every ...
**URL:** https://bigdataboutique.com/blog/postgresql-indexes-best-practices
**Reason:** Comprehensive practical guide covering B-tree, GIN, GiST, BRIN with when-to-use criteria, common pitfalls, and production optimization techniques.

### 4. PostgreSQL Indexes Deep Dive: B-Tree, GIN, GiST, and BRIN
**URL:** https://www.iamraghuveer.com/posts/postgresql-indexes-deep-dive/
**Reason:** Detailed practical guide covering all query-relevant index types with performance trade-offs and use cases.

### 5. Best PostgreSQL Indexes for Performance | Elysiate
**URL:** https://www.elysiate.com/blog/best-postgresql-indexes-for-performance
**Reason:** Practical performance guide covering B-tree, GIN, GiST, BRIN, partial, multicolumn, covering, and expression indexes.

### 6. postgresql - Index method for very few updates and many inserts
**URL:** https://dba.stackexchange.com/questions/46685/index-method-for-very-few-updates-and-many-inserts
**Reason:** DBA StackExchange with direct GIN vs GiST performance guidance: 'GIN is faster to search, slower to build/update'. Authoritative practical answer.

### 7. GiST vs GIN index for LIKE searches – a comparison
**URL:** https://elephanttamer.net/?p=9
**Reason:** Specific performance benchmark for trigram indexing — 'always use GIN for trigram indexing'. Direct performance comparison for LIKE query patterns.

### 8. Comparative analysis of indexing strategies in PostgreSQL under various load scenarios
**URL:** https://www.semanticscholar.org/paper/Comparative-analysis-of-indexing-strategies-in-load-Zolotukhina/a1bcf6c3ddb11cd3dc7cb9cafbbae31fd2c222f7
**Reason:** Empirical study comparing PostgreSQL indexing strategies under various load scenarios with recommendations by query type and execution conditions.

### 9. postgresql - BTREE vs GIN vs GIST index - Stack Overflow
**URL:** https://stackoverflow.com/questions/40780825/btree-vs-gin-vs-gist-index
**Reason:** SO comparison of B-tree vs GIN vs GiST citing PostgreSQL documentation — community-vetted practical answers on choosing between the exact index types in the query.

### 10. A Comparative Experimental Study of Index Performance in MongoDB and PostgreSQL
**URL:** https://doi.org/10.64149/j.ijesrt.15.4.22-31
**Reason:** Empirical performance measurements across PostgreSQL index types and query patterns, providing concrete performance data.
