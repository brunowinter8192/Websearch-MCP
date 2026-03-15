# Announcing: pgvector 0.8.0 released and available on Nile
**URL:** https://www.thenile.dev/blog/pgvector-080
**Domain:** www.thenile.dev
**Score:** 8.5
**Source:** scraped
**Query:** pgvector 0.8 iterative scan HNSW performance

---

[Auth](https://www.thenile.dev/auth)[Docs](https://www.thenile.dev/docs)[Pricing](https://www.thenile.dev/pricing)[Templates](https://www.thenile.dev/templates)[Blog](https://www.thenile.dev/blog)[Community](https://www.thenile.dev/community)[About](https://www.thenile.dev/about-us)
[Auth](https://www.thenile.dev/auth)[Docs](https://www.thenile.dev/docs)[Pricing](https://www.thenile.dev/pricing)[Templates](https://www.thenile.dev/templates)[Blog](https://www.thenile.dev/blog)[Community](https://www.thenile.dev/community)[About](https://www.thenile.dev/about-us)
## Announcing: pgvector 0.8.0 released and available on Nile
2024-11-05
●
6 min read
●
Gwen Shapira
The pgvector community shipped the much anticipated version 0.8.0 with significant performance and functionality improvements. Naturally, we couldn't wait to make it available to Nile users.
## Release highlights
Per the official release notes, pgvector 0.8.0 includes:
  * Added support for iterative index scans
  * Added casts for arrays to sparsevec
  * Improved cost estimation for better index selection when filtering
  * Improved performance of HNSW index scans
  * Improved performance of HNSW inserts and on-disk index builds
  * Dropped support for Postgres 12


The most anticipated feature is iterative index scanning, which addresses a longstanding challenge with vector indexes. Previously, filters were applied after the index scan completed, which often yielded fewer results than expected. According to the pgvector documentation:
> With approximate indexes, filtering is applied after the index is scanned. If a condition matches 10% of rows, with HNSW and the default hnsw.ef_search of 40, only 4 rows will match on average.
Common workarounds include scanning more rows, using partial indexes, or partitioning, but these methods can be impractical or undesirable. The new iterative scan feature offers a more straightforward and intuitive solution:
  1. Scan the vector index
  2. Apply filter
  3. Check if enough results are returned. If not, repeat the scan.


Lets see this in action with a very small example. I strongly recommend running small experiments - you learn so much if the actual results don't match your expectations. Follow along for important pgvector lessons:
To start, I create a table with sample data:
```
CREATE TABLE filtest(id INTEGER, category INTEGER, embedding vector(3));
INSERT INTO filtest VALUES
    (1, 1, '[3, 1, -2]'),
    (2, 1, '[3, 1, -2]'),
    (3, 1, '[3, 1, -2]'),
    (1, 2, '[1.1, 2.2, 3.3]'),
    (2, 2, '[1.1, 2.2, 3.3]'),
    (3, 2, '[1.1, 2.2, 3.3]');
CREATE INDEX ON filtest USING hnsw (embedding vector_cosine_ops);

```

The table contains six rows divided into two categories. Vectors in category 2 closely resemble `[1, 2, 3]`, while vectors in category 1 differ significantly, representing **orthogonal** (unrelated) data. In real use-cases, categories can be different companies (tenants), different departments within the same company, genres if the table stores information about movies, etc. Anything that you may want to use for filtering.
What would you expect the following query to return?
```
SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1
ORDER BY distance LIMIT 3;

```

### Index scans in pgvector 0.7.4
I searched for 3 vectors, from category 1, that are closest to `[1,2,3]`, so the correct answer is to return all vectors from category 1. However, this is what I expected pgvector 0.7.4 to do:
  1. Scan the vector index and find the 3 vectors closest to `[1,2,3]`, some of which should belong to category 2.
  2. Filter the results and keep only vectors from category 1.
  3. Return partial results.


However, in practice:
```
SELECT extversion FROM pg_extension WHERE extname = 'vector';
 extversion
------------
 0.7.4
(1 row)

[Content truncated...]