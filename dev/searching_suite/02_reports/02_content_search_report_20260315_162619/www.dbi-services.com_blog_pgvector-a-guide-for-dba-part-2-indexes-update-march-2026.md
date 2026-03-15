# pgvector, a guide for DBA - Part 2: Indexes (update march 2026)
**URL:** https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part-2-indexes-update-march-2026/
**Domain:** www.dbi-services.com
**Score:** 0.5
**Source:** scraped
**Query:** pgvector HNSW ef_search tuning production settings

---

NecessaryAlways Active
Necessary cookies are required to enable the basic features of this site, such as providing secure log-in or adjusting your consent preferences. These cookies do not store any personally identifiable data.
No cookies to display.
Functional
Functional cookies help perform certain functionalities like sharing the content of the website on social media platforms, collecting feedback, and other third-party features.
No cookies to display.
Analytics
Analytical cookies are used to understand how visitors interact with the website. These cookies help provide information on metrics such as the number of visitors, bounce rate, traffic source, etc.
No cookies to display.
Performance
Performance cookies are used to understand and analyse the key performance indexes of the website which helps in delivering a better user experience for the visitors.
No cookies to display.
Advertisement
Advertisement cookies are used to provide visitors with customised advertisements based on the pages you visited previously and to analyse the effectiveness of the ad campaigns.
No cookies to display.
Reject All  Save My Preferences  Accept All 
## Introduction
In [Part 1](https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part1-lab-demo/) of this series, we covered what pgvector is, how embeddings work, and how to store them in PostgreSQL. We ended with a working similarity search — but on a sequential scan. That works fine for a demo table with 1,000 rows. It does not work for production.
This post is about what comes next: **indexes**. Specifically, the **three index families** in the pgvector ecosystem as of February 2026 (HNSW, IVFFlat, and DiskANN), including **two DiskANN implementations targeting different deployment models** , what they’re good at, where they break, and the patterns you need, whether you’re the DBA tuning them or the developer looking to understand the the strenghts of PostgreSQL as a vector store. 
Everything in this post was tested on public dataset: **25,000 Wikipedia articles** embedded with OpenAI’s `text-embedding-3-large` at **3,072 dimensions** , the maximum the model supports. The high number of dimension is a choice, to highlight some limitations for pedagogical reasons. You would be ok running and testing with lower dimensions or other embedding models, you might want to look into the RAG series, I will probably make a blog post on how to test embedding models against your data sets. The environment is PostgreSQL 18 with pgvector 0.8.1 and pgvectorscale 0.9.0. 
All the SQL scripts, Python code, and Docker configuration are in the companion lab: [`lab/06_pgvector_indexes`](https://github.com/boutaga/pgvector_RAG_search_lab/tree/main/lab/06_pgvector_indexes).
## The Index Types
Before we dive in, here’s the landscape. pgvector ships with two built-in index types (HNSW and IVFFlat), and two DiskANN implementations are available from different vendors:
HNSW | IVFFlat | DiskANN (pgvectorscale) | DiskANN (pg_diskann)  
---|---|---|---  
**Provider** | pgvector | pgvector | Timescale | Microsoft  
**Availability** | Built-in | Built-in | Open source, self-hosted | Azure DB for PostgreSQL  
**Algorithm** | Multi-layer graph | Voronoi cell partitioning | Vamana graph + SBQ | Vamana graph + PQ  
**Best for** | General purpose | Fast build | Storage-constrained | Azure + high recall  
**Build time (25K, 3072d)** | 29s | 5s | 49s | N/A (Azure)  
**Index size** | 193 MB | 193 MB | **21 MB** | Similar  
**Query time** | 2-6 ms | 2-10 ms | 3 ms | ~3 ms  
That pgvectorscale number is not a typo. 21 MB vs 193 MB for the same data. W
> **Note:** This post uses pgvectorscale for all DiskANN benchmarks since it’s the open-source, self-hosted option. We’ll compare both DiskANN implementations in detail in Section 3. pg_diskann is available only for Azure Flexible Server for PostgreSQL, the managed instance service from Microsoft. 
## HNSW: The Default Choice
HNSW (Hierarchical Navigable Small World) is the most 

[Content truncated...]