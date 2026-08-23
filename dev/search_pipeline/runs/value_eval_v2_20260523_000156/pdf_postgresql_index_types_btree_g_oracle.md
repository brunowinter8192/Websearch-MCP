# Oracle — pdf × postgresql index types btree gin gist performance

Top-10 selected from 49 URLs in the oracle pool.

## Selection Criteria

PDF mode without URL filter: direct PDFs (.pdf URLs) ranked highest, then academic papers with available PDFs (IOP open-access, IEEE, preprints), then PDF-document aggregators (Scribd, SlideShare). Blog posts and HTML-only guides are demoted. Off-topic entries (Bispectral Index, CityGML, iris recognition, "The Gist of Reading") excluded.

## Top-10

### 1. PDF Flexible Indexing with Postgres - Momjian
**URL:** https://momjian.us/main/writings/pgsql/indexing.pdf
**Reason:** Direct PDF by Bruce Momjian (PostgreSQL core committer) — covers GiST range-type indexing, R-tree bounding boxes, and GIN index specialization. Authoritative primary source.

### 2. PDF Optimal Indexing for PostgreSQL Performance
**URL:** https://minervadb.xyz/wp-content/uploads/2025/04/Optimal-Indexing-for-PostgreSQL-Performance.pdf
**Reason:** Direct PDF covering GiST, SP-GiST, GIN for specialized domains where B-tree is inefficient — performance-focused PDF matching the query exactly.

### 3. Indexing in PostgreSQL: Performance Evaluation and Use Cases
**URL:** https://doi.org/10.20944/preprints202511.2170.v1
**Reason:** Academic preprint with downloadable PDF — comprehensive performance evaluation of all six native PostgreSQL index types (B-Tree, Hash, GiST, SP-GiST, GIN, BRIN).

### 4. A Comparative Experimental Study of Index Performance in MongoDB and PostgreSQL
**URL:** https://doi.org/10.64149/j.ijesrt.15.4.22-31
**Reason:** Academic paper with PDF — empirical performance study comparing PostgreSQL index types under various query patterns and loads.

### 5. Improving generalized inverted index lock wait times
**URL:** https://doi.org/10.1088/1742-6596/944/1/012022
**Reason:** IOP open-access paper with PDF — research on GIN index concurrent performance improvements targeting read/write performance bottlenecks.

### 6. An implementation of the M-tree index structure for PostgreSQL using GiST
**URL:** https://doi.org/10.1109/informatics47936.2019.9119265
**Reason:** IEEE paper with PDF — covers GiST extensibility and custom M-tree index implementation in PostgreSQL; demonstrates GiST mechanism in practice.

### 7. PostgreSQL Index Types and Optimization | PDF
**URL:** https://www.scribd.com/document/831033974/Index
**Reason:** Scribd PDF document on PostgreSQL index types and optimization — covers performance considerations for B-tree, GIN, GiST overhead and selection criteria.

### 8. Indexing Complex PostgreSQL Data Types | PDF
**URL:** https://www.slideshare.net/slideshow/explain-the-index-of-postgresql-indexes/27810834
**Reason:** SlideShare PDF presentation by Jonathan Katz — covers B-trees, GiST, and GIN applications for complex PostgreSQL data types including performance characteristics.

### 9. Intra-page Indexing in Generalized Search Trees of PostgreSQL
**URL:** https://www.semanticscholar.org/paper/Intra-page-Indexing-in-Generalized-Search-Trees-of-Borodin-Mirvoda/a402de1fc7c031608b9a55083b5084aaf4390e97
**Reason:** Semantic Scholar [PDF] — proposes skip-tuple intra-page indexing for GiST to improve insert/update performance by an order of magnitude. GiST performance research.

### 10. PostgreSQL: Documentation: 18: 11.2. Index Types
**URL:** https://www.postgresql.org/docs/current/indexes-types.html
**Reason:** Official PostgreSQL documentation — canonical authoritative reference for all index types; best non-PDF option in the pool.
