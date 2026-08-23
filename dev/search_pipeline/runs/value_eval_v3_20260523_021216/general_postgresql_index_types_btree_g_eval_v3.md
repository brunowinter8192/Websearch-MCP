# Value Eval v3 — general × postgresql index types btree gin gist performance

**Mode:** general  **Query:** postgresql index types btree gin gist performance  **Pool (filtered):** 40

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 3 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1384 |
| M7 C3+InstrPrefix | 1443 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1734 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 7601 |
| M12 LLM-Selector | 9597 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.176 | 3/10 |
| M2 RRF post-bucket | 0.176 | 3/10 |
| M3 Structural URL | 0.111 | 2/10 |
| M4 BM25 vanilla | 0.176 | 3/10 |
| M5 BM25-Capped | 0.176 | 3/10 |
| M6 C3 Cross-Encoder | 0.333 | 5/10 |
| M7 C3+InstrPrefix | 0.250 | 4/10 |
| M8 RRF+C3 Hybrid | 0.176 | 3/10 |
| M9 SPLADE | 0.333 | 5/10 |
| M10 SPLADE+C3 | 0.333 | 5/10 |
| M11 C3→LLM-Filter | 0.357 | 5/10 |
| M12 LLM-Selector | 0.111 | 2/10 |

## Pool (oracle input — url/title/snippet)

1. https://bigdataboutique.com/blog/postgresql-indexes-best-practices
   PostgreSQL Indexes Best Practices: Choosing the Right Index for Every ...
   A practical guide to PostgreSQL index types - B-tree, GIN, GiST, BRIN, and more - covering when to use each, common pitfalls, and optimization techniques for production workloads.

2. https://blog.devops.dev/how-to-choose-between-index-types-b-tree-gin-gist-in-postgresql-2954638ec4b6
   How to Choose Between Index Types (B-tree, GIN, GiST) in PostgreSQL
   Choosing the right index type in PostgreSQL can make the difference between blazing-fast queries and sluggish performance. While B-tree indexes are the default and work for most situations, GIN and Gi

3. https://dba.stackexchange.com/questions/46685/index-method-for-very-few-updates-and-many-inserts
   postgresql - Index method for very few updates and many inserts
   As a rule of thumb, a GIN index is faster to search than a GiST index, but slower to build or update; so GIN is better suited for static data and ...

4. https://docs.bswen.com/blog/2026-04-20-postgresql-index-types-guide/
   PostgreSQL Index Types: B-tree vs BRIN vs GIN - When to Use Each
   Learn how to choose the right PostgreSQL index type for your query patterns. Compare B-tree, BRIN, GIN, and GiST with real production examples.

5. https://doi.org/10.1007/978-1-4842-5663-3
   PostgreSQL Configuration
   Shaik, B. (2020)

6. https://doi.org/10.1007/978-1-4842-5663-3_1
   Best Ways to Install PostgreSQL
   Shaik, B. (2020), PostgreSQL Configuration

7. https://doi.org/10.1007/978-1-4842-5663-3_5
   Enable Logging of Your Database and Monitoring PostgreSQL Instances
   Shaik, B. (2020), PostgreSQL Configuration

8. https://doi.org/10.1007/s10707-020-00407-w
   MongoDB Vs PostgreSQL: A comparative study on performance aspects
   Abstract Several modern day problems need to deal with large amounts of spatio-temporal data. As such, in order to meet the application requirements, more and more systems are adapting to the specific

9. https://doi.org/10.1007/springerreference_62191
   GiST Index
   

10. https://doi.org/10.1088/1742-6596/944/1/012022
   Improving generalized inverted index lock wait times
   Concurrent operations on tree like data structures is a cornerstone of any database system. Concurrent operations intended for improving read\write performance and usually implemented via some way of 

11. https://doi.org/10.1097/01.ana.0000187778.94201.f7
   Performance of the Bispectral Index During Electrocautery
   T, G. et al. (2005), Journal of Neurosurgical Anesthesiology

12. https://doi.org/10.1109/informatics47936.2019.9119265
   An implementation of the M-tree index structure for PostgreSQL using GiST
   Donko, I. et al. (2019), 2019 IEEE 15th International Scientific Conference on Informatics

13. https://doi.org/10.1515/9781503604100-012
   INDEX
   (2020), The Gist of Reading

14. https://doi.org/10.20944/preprints202511.2170.v1
   Indexing in PostgreSQL: Performance Evaluation and Use Cases
   Efficient indexing remains a central factor in achieving predictable performance in modern relational database systems. PostgreSQL provides six native index types—B-Tree, Hash, GiST, SP-GiST, GIN, and

15. https://doi.org/10.3139/9783446473157.bm
   Index
   Fröhlich, L. (2022), PostgreSQL

16. https://doi.org/10.48550/arxiv.2307.06621
   cjdb: a simple, fast, and lean database solution for the CityGML data model
   When it comes to storing 3D city models in a database, the implementation of the CityGML data model can be quite demanding and often results in complicated schemas. As an example, 3DCityDB, a widely u

17. https://doi.org/10.64149/j.ijesrt.15.4.22-31
   A COMPARATIVE EXPERIMENTAL STUDY OF INDEX PERFORMANCE IN MONGODB AND POSTGRESQL
   The continuous growth in data volumes, combined with the increasing complexity of modern enterprise information systems, requires database management systems (DBMS) to guarantee ever faster response t

18. https://elephanttamer.net/?p=9
   GiST vs GIN index for LIKE searches – a comparison
   Takeaway: always use GIN for trigram indexing, and if your database suffers from poor LIKE performance, check not only the scan type, but also the ...

19. https://habr.com/ru/company/postgrespro/blog/441962/
   Indexes in PostgreSQL
   habr.com

20. https://hakibenita.com/postgresql-correlation-brin-multi-minmax
   When Good Correlation is Not Enough
   hakibenita.com

21. https://hakibenita.com/postgresql-hash-index
   Re-Introducing Hash Indexes in PostgreSQL
   hakibenita.com

22. https://ntsd.dev/postgresql-index-types/
   Explain index types in PostgreSQL | Jirawat Boonkumnerd
   Postgres provides many index types such as B-tree, hash, GiST, and GIN. ... GiST and GIN are indexes for supporting Full-Text Search which I’ll ...

23. https://oneuptime.com/blog/post/2026-01-25-use-index-types-effectively-postgresql/view
   How to Use Index Types Effectively in PostgreSQL
   Learn how to choose and use the right index types in PostgreSQL. This guide covers B-tree, Hash, GIN, GiST, BRIN, and partial indexes with practical examples for optimal query performance.

24. https://openalex.org/W2612672839
   PostgreSQL database performance optimization
   The thesis was request by Marlevo software Oy for a general description of the PostgreSQL database and its performance optimization technics. Its purpose was to help new PostgreSQL users to quickly un

25. https://openalex.org/W2896189947
   Highly Efficient Search In Linguistic Data
   Electronic dictionaries and online learning services have become a common tool for translators, linguistics and people trying to learn a new language.This master's thesis work has been carried out in 

26. https://stackoverflow.com/questions/12738997/postgres-gist-vs-btree-index
   postgresql - Postgres GIST vs Btree index - Stack Overflow
   It's considerably slower than regular b-tree indexes, but allows you to create a multi-column index that contains both GiST-only types and regular ...

27. https://stackoverflow.com/questions/1540374/why-are-postgresql-text-search-gist-indexes-so-much-slower-than-gin-indexes
   performance - Why are PostgreSQL Text-Search GiST indexes so
   The docs have a nice overview of the performance differences between GiST and GIN indexes if you're interested: GiST and GIN Index Types .

28. https://stackoverflow.com/questions/21830/postgresql-gin-or-gist-indexes
   indexing - PostgreSQL: GIN or GiST indexes? - Stack Overflow
   First of all, do you need to use them for text search indexing? GIN and GiST are index specialized for some data types.

29. https://stackoverflow.com/questions/40780825/btree-vs-gin-vs-gist-index
   postgresql - BTREE vs GIN vs GIST index - Stack Overflow
   5 From PostgreSQL documentation: 11.2. Index Types By default, the CREATE INDEX command creates B-tree indexes The other index types are selected by writing the keyword USING followed by the index typ

30. https://stackoverflow.com/questions/766488/whats-the-difference-between-b-tree-and-gist-index-methods-in-postgresql
   indexing - What's the difference between B-Tree and GiST
   There was a recent post on the PG lists about a huge performance hit for using GiST indexes; they're expected to be slower than B-Trees (such is the ...

31. https://www.2ndquadrant.com/en/blog/parallelism-comes-to-vacuum/
   Parallelism comes to VACUUM
   2ndquadrant.com

32. https://www.depesz.com/2014/05/12/joining-btree-and-gingist-indexes/
   Joining BTree and GIN/GiST indexes – select * from depesz;
   ... gin_btree (there is also gist_btree if your “ base" index ... What it is – it adds “ btree" type of operators support to gin index.

33. https://www.elysiate.com/blog/best-postgresql-indexes-for-performance
   Best PostgreSQL Indexes for Performance | Elysiate
   A practical PostgreSQL guide to choosing the best indexes for performance, including B-tree, GIN, GiST, BRIN, partial, multicolumn, covering, and expression indexes.

34. https://www.iamraghuveer.com/posts/postgresql-indexes-deep-dive/
   PostgreSQL Indexes Deep Dive: B-Tree, GIN, GiST, and BRIN
   PostgreSQL Indexes Deep Dive: B-Tree, GIN, GiST, and BRIN Choosing the wrong index type or missing an index entirely is among the most common causes of database performance problems.

35. https://www.meerako.com/blogs/postgresql-indexing-strategies-btree-gin-gist-guide
   PostgreSQL Indexing Deep Dive | Meerako
   PostgreSQL Indexing Deep Dive: B-Tree, GIN, GiST, and When to Use Them Slow queries? The right index is magic. Our Postgres experts explain different index types (B-Tree, GIN, GiST) and how to optimiz

36. https://www.mydbops.com/blog/postgresql-indexing-best-practices-guide
   PostgreSQL Index Best Practices for Faster Queries | Mydbops
   Boost PostgreSQL query performance with the right indexing strategies. Learn best practices for using B-Tree, Hash, GIN, and more to Contact Mydbops today.

37. https://www.percona.com/blog/2019/06/21/hypothetical-indexes-in-postgresql/
   Hypothetical Indexes in PostgreSQL
   percona.com

38. https://www.postgresql.org/about/news/postgresql-18-beta-1-released-3070/
   PostgreSQL 18 Beta 1 Released
   postgresql.org

39. https://www.postgresql.org/docs/current/indexes-types.html
   PostgreSQL: Documentation: 18: 11.2. Index Types
   PostgreSQL provides several index types: B-tree, Hash, GiST, SP-GiST, GIN, BRIN, and the extension bloom. Each index type uses a different algorithm that is best suited to different types of indexable

40. https://www.semanticscholar.org/paper/Comparative-analysis-of-indexing-strategies-in-load-Zolotukhina/a1bcf6c3ddb11cd3dc7cb9cafbbae31fd2c222f7
   Comparative analysis of indexing strategies in PostgreSQL under various load scenarios
   TLDRThe main conclusions of the conducted research are recommendations on the choice of indexes depending on the types of queries and their execution conditions, which makes it possible to improve app

41. https://www.semanticscholar.org/paper/Efficient-Iris-Recognition-Management-in-Databases-Alvez-Miranda/cd69c81398ea9b392f8f93f9e290cc5402cf5b5f
   Efficient Iris Recognition Management in Object-Related Databases
   TLDRAn extension of an Object Relational Database Management System for the integral management of a biometric system based on the human iris was presented, which includes both the extension of the ty

42. https://www.semanticscholar.org/paper/Intra-page-Indexing-in-Generalized-Search-Trees-of-Borodin-Mirvoda/a402de1fc7c031608b9a55083b5084aaf4390e97
   Intra-page Indexing in Generalized Search Trees of PostgreSQL
   TLDRThis paper proposes changes to this limitation with additional intra-page indexing, based on the concept of skip tuples, which allows to increase of insert and update performance by the factor of 

43. https://www.semanticscholar.org/paper/Purdue-e-Pubs-Purdue-e-Pubs-non-traditional-Oracle/685f1a3f6b6207a98830f4e6d082c729af9f2e05
   Purdue e-Pubs Purdue e-Pubs
   TLDRThis paper presents a serious attempt at plementing and realizing SP-GiST-based in dexes inside Postgres facilitated by rapid SP-GiST instantiations and highlights the performance gains and severa

44. https://www.semanticscholar.org/paper/Research-and-Comparative-Analysis-of-Approaches-to-Dubrovskaia-Balanev/ef8e4bbf124a1ae45eec52efbab4c3b0dd9e00f0
   Research and Comparative Analysis of Approaches to Data Storage Architecture, Hashing, Indexing, and
   TLDRThe comparative analysis demonstrates that Oracle is oriented toward performance and scalability, while PostgreSQL emphasizes flexibility and architectural extensibility.Expand

45. https://www.semanticscholar.org/paper/Space-Partitioning-Trees-in-PostgreSQL%3A-Realization-Eltabakh-Eltarras/35cab96c86bae325db7a456ffc64f57c142fe56c
   Space-Partitioning Trees in PostgreSQL: Realization and Performance
   TLDRThis paper presents a serious attempt at implementing and realizing SP-GiST-based indexes inside PostgreSQL, and interesting results that highlight the potential performance gains of SP GiST- base

46. https://www.semanticscholar.org/paper/Supporting-Trajectory-UDF-Queries-and-Indexes-on-Yang-Nam/d0162e56e832f5bb439a2fba1825ed8b58521308
   Supporting Trajectory UDF Queries and Indexes on PostGIS
   TLDRA new system supporting trajectory queries on PostGIS using UDFs is developed and Experimental results show that the pre‐materialization techniques are about 1.2 times faster than naïve query proc

47. https://www.semanticscholar.org/paper/To-Trie-or-Not-to-Trie-Realizing-Space-partitioning-Eltabakh-Eltarras/ed662da5a5b1211803258fff46e287ced52b10f8
   To Trie or Not to Trie? Realizing Space-partitioning Trees inside PostgreSQL: Challenges, Experience
   TLDRThis paper presents a serious attempt at implementing and realizing SP-GiST-based indexes inside PostgreSQL and highlights the potentifd performance gains of SP-GiST-based indexes as well as sever

48. https://www.thenile.dev/docs/extensions/btree_gin
   Btree_gin - Nile Documentation
   The btree_gin extension in PostgreSQL enables GIN indexes to support B-tree indexable data types. ... GIN index with btree_gin is useful when ...
