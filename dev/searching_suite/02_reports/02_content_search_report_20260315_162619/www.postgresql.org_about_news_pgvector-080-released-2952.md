# pgvector 0.8.0 Released! - PostgreSQL
**URL:** https://www.postgresql.org/about/news/pgvector-080-released-2952/
**Domain:** www.postgresql.org
**Score:** 24.0
**Source:** scraped
**Query:** pgvector 0.8 iterative scan HNSW performance

---

February 26, 2026: [ PostgreSQL 18.3, 17.9, 16.13, 15.17, and 14.22 Released! ](https://www.postgresql.org/about/news/postgresql-183-179-1613-1517-and-1422-released-3246/)
## Quick Links
  * [Sponsors](https://www.postgresql.org/about/sponsors/)
  * [Upcoming Events](https://www.postgresql.org/about/events/)


# pgvector 0.8.0 Released!
Posted on **2024-11-11** by pgvector
[pgvector](https://github.com/pgvector/pgvector/), an open-source PostgreSQL extension that provides vector similarity search capabilities, has released [v0.8.0](https://github.com/pgvector/pgvector/releases/tag/v0.8.0). This release includes features that improve query performance and usability when using filters (e.g. the `WHERE` clause), and performance improvements for searching and building [HNSW](https://github.com/pgvector/pgvector?tab=readme-ov-file#hnsw) indexes.
This latest version of pgvector has a variety of improvements for filtering. This includes an update to how PostgreSQL estimates when to scan a approximate nearest neighbor (ANN) index like HNSW and IVFFlat, which could lead PostgreSQL to select a B-tree or other index that more efficiently executes the query. If you can achieve the same query performance without using an ANN index, this is usually preferable as it lets you achieve 100% recall, or high relevancy searches.
Additionally, this pgvector release adds [iterative index scans](https://github.com/pgvector/pgvector?tab=readme-ov-file#iterative-index-scans), which is a technique to prevent "overfiltering" or not returning enough results to satisfy the conditions of a query. You can enable iterative scanning with the `hnsw.iterative_scan` and `ivfflat.iterative_scan` parameters for HNSW and IVFFlat indexes respectively, and if an initial index scan doesn't satisfy the query conditions, pgvector will continue to search the index until it hits a configurable threshold (`hnsw.max_scan_tuples` and `ivfflat.max_probes`). 
For more information, please see the [CHANGELOG for 0.8.0](https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md#080-2024-10-30):
<https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md#080-2024-10-30>
For more information about pgvector, including how to get started, please visit the [project repository on GitHub](https://github.com/pgvector/pgvector):
<https://github.com/pgvector/pgvector>
