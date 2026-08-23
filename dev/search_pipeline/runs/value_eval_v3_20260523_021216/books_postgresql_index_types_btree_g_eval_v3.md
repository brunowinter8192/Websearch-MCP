# Value Eval v3 — books × postgresql index types btree gin gist performance

**Mode:** books  **Query:** postgresql index types btree gin gist performance  **Pool (filtered):** 41

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 3 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1445 |
| M7 C3+InstrPrefix | 1502 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1343 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 6288 |
| M12 LLM-Selector | 8892 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.053 | 1/10 |
| M2 RRF post-bucket | 0.053 | 1/10 |
| M3 Structural URL | 0.111 | 2/10 |
| M4 BM25 vanilla | 0.176 | 3/10 |
| M5 BM25-Capped | 0.176 | 3/10 |
| M6 C3 Cross-Encoder | 0.111 | 2/10 |
| M7 C3+InstrPrefix | 0.176 | 3/10 |
| M8 RRF+C3 Hybrid | 0.053 | 1/10 |
| M9 SPLADE | 0.176 | 3/10 |
| M10 SPLADE+C3 | 0.176 | 3/10 |
| M11 C3→LLM-Filter | 0.176 | 3/10 |
| M12 LLM-Selector | 0.250 | 4/10 |

## Pool (oracle input — url/title/snippet)

1. https://appmaster.io/blog/btree-gin-gist-index-decision-table
   B-tree vs GIN vs GiST indexes: a practical PostgreSQL guide
   B-tree vs GIN vs GiST indexes: use a decision table to pick the right PostgreSQL index for filters, search, JSONB fields, geo queries, and high-cardinality columns.

2. https://bigdataboutique.com/blog/postgresql-indexes-best-practices
   PostgreSQL Indexes Best Practices: Choosing the Right Index for Every ...
   A practical guide to PostgreSQL index types - B-tree, GIN, GiST, BRIN, and more - covering when to use each, common pitfalls, and optimization techniques for production workloads.

3. https://de.leapcell.io/blog/en/navigating-postgresql-index-choices-b-tree-hash-gin-and-gist-explained
   Navigating PostgreSQL Index Choices B-Tree, Hash, GIN, and GiST ...
   A comprehensive guide to understanding and applying B-Tree, Hash, GIN, and GiST indexes in PostgreSQL for optimal query performance across various data types and use cases.

4. https://dev.to/jhonoryza/sql-index-types-b-tree-hash-gist-gist-brin-and-gin-44g0
   SQL index types B TREE, HASH, GIST, GIST, BRIN, and GIN
   SQL index types B TREE, HASH, GIST, GIST, BRIN, and GINDEV Communityhttps://dev.to › jhonoryza › sql-index-types-b-tree-hash...DEV Communityhttps://dev.to › jhonoryza › sql-index-types-b-tree-hash...2

5. https://dev.to/piteradyson/postgresql-indexing-explained-5-index-types-and-when-to-use-each-45ae
   PostgreSQL indexing explained — 5 index types and when to use each
   1. B-tree — the default workhorse B-tree is the default index type in PostgreSQL. If you run CREATE INDEX without specifying a type, you get a B-tree. It handles equality and range queries on sortable

6. https://docs.bswen.com/blog/2026-04-20-postgresql-index-types-guide/
   PostgreSQL Index Types: B-tree vs BRIN vs GIN - When to Use Each
   Learn how to choose the right PostgreSQL index type for your query patterns. Compare B-tree, BRIN, GIN, and GiST with real production examples.

7. https://doi.org/10.1007/978-1-4842-5663-3
   PostgreSQL Configuration
   Shaik, B. (2020)

8. https://doi.org/10.1007/978-1-4842-5663-3_1
   Best Ways to Install PostgreSQL
   Shaik, B. (2020), PostgreSQL Configuration

9. https://doi.org/10.1007/978-1-4842-5663-3_5
   Enable Logging of Your Database and Monitoring PostgreSQL Instances
   Shaik, B. (2020), PostgreSQL Configuration

10. https://doi.org/10.1007/s10707-020-00407-w
   MongoDB Vs PostgreSQL: A comparative study on performance aspects
   Abstract Several modern day problems need to deal with large amounts of spatio-temporal data. As such, in order to meet the application requirements, more and more systems are adapting to the specific

11. https://doi.org/10.1007/springerreference_62191
   GiST Index
   

12. https://doi.org/10.1088/1742-6596/944/1/012022
   Improving generalized inverted index lock wait times
   Concurrent operations on tree like data structures is a cornerstone of any database system. Concurrent operations intended for improving read\write performance and usually implemented via some way of 

13. https://doi.org/10.1097/01.ana.0000187778.94201.f7
   Performance of the Bispectral Index During Electrocautery
   T, G. et al. (2005), Journal of Neurosurgical Anesthesiology

14. https://doi.org/10.1109/informatics47936.2019.9119265
   An implementation of the M-tree index structure for PostgreSQL using GiST
   Donko, I. et al. (2019), 2019 IEEE 15th International Scientific Conference on Informatics

15. https://doi.org/10.1515/9781503604100-012
   INDEX
   (2020), The Gist of Reading

16. https://doi.org/10.20944/preprints202511.2170.v1
   Indexing in PostgreSQL: Performance Evaluation and Use Cases
   Efficient indexing remains a central factor in achieving predictable performance in modern relational database systems. PostgreSQL provides six native index types—B-Tree, Hash, GiST, SP-GiST, GIN, and

17. https://doi.org/10.3139/9783446473157.bm
   Index
   Fröhlich, L. (2022), PostgreSQL

18. https://doi.org/10.48550/arxiv.2307.06621
   cjdb: a simple, fast, and lean database solution for the CityGML data model
   When it comes to storing 3D city models in a database, the implementation of the CityGML data model can be quite demanding and often results in complicated schemas. As an example, 3DCityDB, a widely u

19. https://doi.org/10.64149/j.ijesrt.15.4.22-31
   A COMPARATIVE EXPERIMENTAL STUDY OF INDEX PERFORMANCE IN MONGODB AND POSTGRESQL
   The continuous growth in data volumes, combined with the increasing complexity of modern enterprise information systems, requires database management systems (DBMS) to guarantee ever faster response t

20. https://en.wikibooks.org/wiki/PostgreSQL/Indices
   PostgreSQL/Indices - Wikibooks, open books for an open world
   GIN (Generalized Inverted Index) supports data types that are divisible into smaller components, e.g., elements of an array, words of a text document ...

21. https://habr.com/en/companies/postgrespro/articles/448746/
   Indexes in PostgreSQL — 7 (GIN) / Habr
   ... with PostgreSQL indexing engine and the interface of access methods and discussed hash indexes , B-trees , as well as GiST and SP-GiST indexes.

22. https://habr.com/en/companies/postgrespro/articles/452900/
   Indexes in PostgreSQL — 9 (BRIN) / Habr
   ... we discussed PostgreSQL indexing engine , the interface of access methods, and the following methods: hash indexes , B-trees , GiST , SP-GiST , GIN ...

23. https://habr.com/ru/company/postgrespro/blog/441962/
   Indexes in PostgreSQL
   habr.com

24. https://hakibenita.com/postgresql-correlation-brin-multi-minmax
   When Good Correlation is Not Enough
   hakibenita.com

25. https://hakibenita.com/postgresql-hash-index
   Re-Introducing Hash Indexes in PostgreSQL
   hakibenita.com

26. https://learnomate.org/postgresql-indexing-strategies-btree-vs-gin-vs-brin/
   PostgreSQL Indexing Strategies: B-Tree vs GIN vs BRIN Explained
   Explore PostgreSQL Indexing Strategies including B-Tree, GIN, and BRIN indexes. Learn how each type works, their use cases, and which index to choose for better query performance.

27. https://medium.com/@sanhdoan/postgresql-indexing-a-practical-guide-to-index-types-ac60f9f08285
   PostgreSQL Indexing: A Practical Guide to Index Types
   PostgreSQL Indexing: A Practical Guide to Index TypesMedium · Sanh Doan7 likes  ·  1 year agoMedium · Sanh Doan7 likes  ·  1 year agoPostgreSQL Indexing: A Practical Guide to Index Types As your datab

28. https://neon.com/postgresql/indexes
   PostgreSQL Indexes
   PostgreSQL IndexesNeonhttps://neon.com › postgresql › indexesNeonhttps://neon.com › postgresql › indexesTypes of PostgreSQL indexes · B-tree index · Hash index · GIN index · GiST index · SP-GiST index

29. https://openalex.org/W2612672839
   PostgreSQL database performance optimization
   The thesis was request by Marlevo software Oy for a general description of the PostgreSQL database and its performance optimization technics. Its purpose was to help new PostgreSQL users to quickly un

30. https://openalex.org/W2896189947
   Highly Efficient Search In Linguistic Data
   Electronic dictionaries and online learning services have become a common tool for translators, linguistics and people trying to learn a new language.This master's thesis work has been carried out in 

31. https://pganalyze.com/blog/gin-index
   Understanding Postgres GIN Indexes: The Good and the Bad
   Understanding Postgres GIN Indexes: The Good and the Badpganalyzehttps://pganalyze.com › blog › gin-indexpganalyzehttps://pganalyze.com › blog › gin-index2 Dec 2021 — GIN indexes can seem like magic, 

32. https://postgrespro.com/blog/pgsql/4175817
   postgrespro.com/blog/pgsql/4175817
   

33. https://postgrespro.com/blog/pgsql/4261647
   Indexes in PostgreSQL — 7 (GIN) : Postgres Professional
   ... GiST and SP-GiST indexes, discussed earlier, GIN provides an application developer with the interface to support various operations over compound data ...

34. https://severalnines.com/blog/postgresql-database-indexing-overview/
   Database Indexing in PostgreSQL
   Database Indexing in PostgreSQLSeveralnineshttps://severalnines.com › posts pagesSeveralnineshttps://severalnines.com › posts pages4 May 2022 — This blog provides a high-level overview of database ind

35. https://stackoverflow.com/questions/12738997/postgres-gist-vs-btree-index
   postgresql - Postgres GIST vs Btree index - Stack Overflow
   It's considerably slower than regular b-tree indexes, but allows you to create a multi-column index that contains both GiST-only types and regular ...

36. https://stackoverflow.com/questions/40780825/btree-vs-gin-vs-gist-index
   postgresql - BTREE vs GIN vs GIST index - Stack Overflow
   5 From PostgreSQL documentation: 11.2. Index Types By default, the CREATE INDEX command creates B-tree indexes The other index types are selected by writing the keyword USING followed by the index typ

37. https://thoughtbot.com/blog/postgres-index-types
   Postgres Index Types
   Postgres Index TypesThoughtbothttps://thoughtbot.com › blog › postgres-index-typesThoughtbothttps://thoughtbot.com › blog › postgres-index-types10 Jan 2025 — The B-Tree index type uses a balanced tree

38. https://vladmihalcea.com/postgresql-index-types/
   PostgreSQL Index Types - Vlad Mihalcea
   What ’ s great about PostgreSQL is that it offers a large variety of index options , such as B+Tree, Hash, GIN, GiST, or BRIN.

39. https://www.2ndquadrant.com/en/blog/parallelism-comes-to-vacuum/
   Parallelism comes to VACUUM
   2ndquadrant.com

40. https://www.citusdata.com/blog/2017/10/17/tour-of-postgres-index-types/
   A tour of Postgres Index Types
   A tour of Postgres Index TypesCitus Datahttps://www.citusdata.com › blog › 2017/10/17 › tour-...Citus Datahttps://www.citusdata.com › blog › 2017/10/17 › tour-...17 Oct 2017 — A tour of Postgres Index

41. https://www.meerako.com/blogs/postgresql-indexing-strategies-btree-gin-gist-guide
   PostgreSQL Indexing Deep Dive: B-Tree, GIN, GiST ...
   PostgreSQL Indexing Deep Dive: B-Tree, GIN, GiST ...Meerakohttps://www.meerako.com › BlogMeerakohttps://www.meerako.com › Blog31 Oct 2025 — Slow queries? The right index is magic. Our Postgres experts

42. https://www.mydbops.com/blog/postgresql-indexing-best-practices-guide
   PostgreSQL Index Best Practices for Faster Queries | Mydbops
   Boost PostgreSQL query performance with the right indexing strategies. Learn best practices for using B-Tree, Hash, GIN, and more to Contact Mydbops today.

43. https://www.percona.com/blog/2019/06/21/hypothetical-indexes-in-postgresql/
   Hypothetical Indexes in PostgreSQL
   percona.com

44. https://www.postgresql.org/about/news/postgresql-18-beta-1-released-3070/
   PostgreSQL 18 Beta 1 Released
   postgresql.org

45. https://www.postgresql.org/docs/current/indexes-types.html
   Documentation: 18: 11.2. Index Types
   Web resultsDocumentation: 18: 11.2. Index TypesPostgreSQLhttps://www.postgresql.org › docs › current › indexes-ty...PostgreSQLhttps://www.postgresql.org › docs › current › indexes-ty...PostgreSQL prov

46. https://www.preprints.org/manuscript/202511.2170
   Indexing in PostgreSQL: Performance Evaluation and Use ...
   Indexing in PostgreSQL: Performance Evaluation and Use ...Preprints.orghttps://www.preprints.org › manuscriptPreprints.orghttps://www.preprints.org › manuscriptby G Toktomusheva · 2025 · Cited by 2 — 

47. https://www.scalingpostgres.com/episodes/194-go-faster-gin-indexes-collation-stability-pg14-beyond/
   Go Faster, GIN Indexes, Collation Stability, PG14 & Beyond |
   ... an extension called btree_gin which allows you to combine a B-tree index and a GIN index at the same time and they show a use case of doing that here.

48. https://www.semanticscholar.org/paper/Comparative-analysis-of-indexing-strategies-in-load-Zolotukhina/a1bcf6c3ddb11cd3dc7cb9cafbbae31fd2c222f7
   Comparative analysis of indexing strategies in PostgreSQL under various load scenarios
   TLDRThe main conclusions of the conducted research are recommendations on the choice of indexes depending on the types of queries and their execution conditions, which makes it possible to improve app

49. https://www.semanticscholar.org/paper/Efficient-Iris-Recognition-Management-in-Databases-Alvez-Miranda/cd69c81398ea9b392f8f93f9e290cc5402cf5b5f
   Efficient Iris Recognition Management in Object-Related Databases
   TLDRAn extension of an Object Relational Database Management System for the integral management of a biometric system based on the human iris was presented, which includes both the extension of the ty

50. https://www.semanticscholar.org/paper/Intra-page-Indexing-in-Generalized-Search-Trees-of-Borodin-Mirvoda/a402de1fc7c031608b9a55083b5084aaf4390e97
   Intra-page Indexing in Generalized Search Trees of PostgreSQL
   TLDRThis paper proposes changes to this limitation with additional intra-page indexing, based on the concept of skip tuples, which allows to increase of insert and update performance by the factor of 

51. https://www.semanticscholar.org/paper/Purdue-e-Pubs-Purdue-e-Pubs-non-traditional-Oracle/685f1a3f6b6207a98830f4e6d082c729af9f2e05
   Purdue e-Pubs Purdue e-Pubs
   TLDRThis paper presents a serious attempt at plementing and realizing SP-GiST-based in dexes inside Postgres facilitated by rapid SP-GiST instantiations and highlights the performance gains and severa

52. https://www.semanticscholar.org/paper/Research-and-Comparative-Analysis-of-Approaches-to-Dubrovskaia-Balanev/ef8e4bbf124a1ae45eec52efbab4c3b0dd9e00f0
   Research and Comparative Analysis of Approaches to Data Storage Architecture, Hashing, Indexing, and
   TLDRThe comparative analysis demonstrates that Oracle is oriented toward performance and scalability, while PostgreSQL emphasizes flexibility and architectural extensibility.Expand

53. https://www.semanticscholar.org/paper/Space-Partitioning-Trees-in-PostgreSQL%3A-Realization-Eltabakh-Eltarras/35cab96c86bae325db7a456ffc64f57c142fe56c
   Space-Partitioning Trees in PostgreSQL: Realization and Performance
   TLDRThis paper presents a serious attempt at implementing and realizing SP-GiST-based indexes inside PostgreSQL, and interesting results that highlight the potential performance gains of SP GiST- base

54. https://www.semanticscholar.org/paper/Supporting-Trajectory-UDF-Queries-and-Indexes-on-Yang-Nam/d0162e56e832f5bb439a2fba1825ed8b58521308
   Supporting Trajectory UDF Queries and Indexes on PostGIS
   TLDRA new system supporting trajectory queries on PostGIS using UDFs is developed and Experimental results show that the pre‐materialization techniques are about 1.2 times faster than naïve query proc

55. https://www.semanticscholar.org/paper/To-Trie-or-Not-to-Trie-Realizing-Space-partitioning-Eltabakh-Eltarras/ed662da5a5b1211803258fff46e287ced52b10f8
   To Trie or Not to Trie? Realizing Space-partitioning Trees inside PostgreSQL: Challenges, Experience
   TLDRThis paper presents a serious attempt at implementing and realizing SP-GiST-based indexes inside PostgreSQL and highlights the potentifd performance gains of SP-GiST-based indexes as well as sever
