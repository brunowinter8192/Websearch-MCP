# Faster similarity search performance with pgvector indexes
**URL:** https://cloud.google.com/blog/products/databases/faster-similarity-search-performance-with-pgvector-indexes
**Domain:** cloud.google.com
**Score:** 6.7
**Source:** scraped
**Query:** pgvector HNSW ef_search tuning production settings

---

cloud.google.com uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. [Learn more](https://policies.google.com/technologies/cookies?hl=en)
Hide
Databases
December 2, 2023
##### Eeshan Gupta
Software Engineer
**_Update April 22, 2024_** _: Cloud SQL for PostgreSQL version 12 and above now_ [_supports_](https://cloud.google.com/sql/docs/postgres/release-notes) _pgvector 0.6.0. This version brings multiple performance and stability_ [_improvements_](https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md#060-2024-01-29) _, with a focus on HNSW index building. Key improvements include:_
  * _Parallel HNSW index builds are now supported_
  * _Reduced memory and storage (WAL) during HNSW build_
  * _Improved index search performance_


In the fast evolving landscape of approximate nearest neighbor (ANN) search, one of the most important recent launches is pgvector extension version 0.5.0, which adds support for Hierarchical Navigable Small Worlds (HNSW) indexes. With the constant quest for efficiency, speed and performance, HNSW indexes significantly reduce ANN query latency for the desired recall. We are excited to [announce](https://cloud.google.com/sql/docs/postgres/release-notes#September_21_2023) support for pgvector 0.5.0 in Cloud SQL for PostgreSQL.
In this post, we explain pgvector indexes, clarify different configurations, and give hands-on coding examples for improving the performance and viability of a pgvector-based application using HNSW indexes.
## **_The pgvector extension in Cloud SQL for PostgreSQL_**
The pgvector extension can be installed within an existing instance of Cloud SQL for PostgreSQL using the CREATE EXTENSION command as shown below. If you do not have an existing instance, [create one today](https://cloud.google.com/sql/docs/postgres/create-instance). Cloud SQL for PostgreSQL now supports pgvector 0.5.0, which adds HNSW indexes in pgvector, in addition to Inverted File Flat (IVFFlat) indexes.
postgres=> CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION
```
postgres=> CREATE EXTENSION IF NOT EXISTS vector;
```

```
CREATE EXTENSION
```

If you have already installed an older version of pgvector in your Cloud SQL for PostgreSQL instance, it can now be upgraded to pgvector 0.5.0 using the following command.
postgres=> ALTER EXTENSION vector UPDATE TO '0.5.0'; ALTER EXTENSION
```
postgres=> ALTER EXTENSION vector UPDATE TO '0.5.0';
```

```
ALTER EXTENSION
```

The extension registers a new data type called “vector” in PostgreSQL and defines several new operators on it:
  * Element-wise addition (+)
  * Element-wise subtraction (-)
  * Element-wise multiplication (*)
  * Euclidean distance (<->)
  * Cosine distance (<=>)


The distance operators allow finding vectors that are [semantically similar](https://en.wikipedia.org/wiki/Semantic_similarity). You can find more in-depth details about how they work in our [previous pgvector blog](https://cloud.google.com/blog/products/databases/using-pgvector-llms-and-langchain-with-google-cloud-databases).
The commands below demonstrate how to insert vectors to a PostgreSQL table and compute row-wise cosine distances.
postgres=> CREATE TABLE embeddings( id INTEGER, embedding vector(3) ); CREATE TABLE ​ ​ postgres=> INSERT INTO embeddings VALUES (1, '[1, 0, -1]'), (2, '[1, 1, 1]'), (3, '[1, 1, 50]'); INSERT 0 3 postgres=> SELECT id, embedding, 1 - ('[2, 2, 2]' <=> embedding) AS cosine_similarity FROM embeddings ORDER BY cosine_similarity DESC; id | embedding | cosine_similarity ----+-----------+-------------------- 2 | [1,1,1] | 1 3 | [1,1,50] | 0.6002042462558512 1 | [1,0,-1] | 0 (3 rows)
```
postgres=> CREATE TABLE embeddings(
```

```
     id INTEGER,
```

```
     embedding vector(3)
```

```
CREATE TABLE
```

```
postgres=> INSERT INTO embeddings
```

```
          VALUES
```

```
                  (1, '[1, 0, -1]'),
```

```
                  (2, '[1, 1, 1]'),
```

[Content truncated...]