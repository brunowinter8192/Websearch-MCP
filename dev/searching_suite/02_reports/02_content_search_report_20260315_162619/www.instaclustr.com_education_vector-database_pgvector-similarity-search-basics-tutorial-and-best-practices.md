# pgvector similarity search: Basics, tutorial and best practices
**URL:** https://www.instaclustr.com/education/vector-database/pgvector-similarity-search-basics-tutorial-and-best-practices/
**Domain:** www.instaclustr.com
**Score:** 0.3
**Source:** scraped
**Query:** pgvector HNSW ef_search tuning production settings

---

# pgvector similarity search: Basics, tutorial and best practices
pgvector is an open source extension for PostgreSQL that enables efficient vector similarity search within the database. It allows for the storage of high-dimensional vectors and the execution of various similarity metrics to find data points that are "closest" to a given query vector.
[Talk to a consultant](https://www.instaclustr.com/contact-us/)
## pgvector similarity search: Basics, tutorial, and best practices
### How does pgvector support similarity search?
pgvector is an open source extension for PostgreSQL. By integrating natively with PostgreSQL, it removes the need to use external [vector databases](https://www.instaclustr.com/education/vector-database/vector-databases-explained-use-cases-algorithms-and-key-features/) or retrieval systems, simplifying architecture for applications that require similarity search and machine learning capabilities.
Pgvector enables efficient vector similarity search directly within a PostgreSQL database. It allows for the storage of high-dimensional vectors and the execution of various similarity metrics to find data points that are “closest” to a given query vector.
Key similarity search capabilities include:
  * **Vector storage:** pgvector introduces a vector data type in PostgreSQL, allowing for the direct storage of numerical vectors representing embeddings of various data types (e.g., text, images, audio).
  * **Similarity metrics:** It supports common distance metrics for similarity search, including: L2 Distance (Euclidean Distance): Measures the straight-line distance between two vectors. Represented by the `<->` operator.
  * **Inner product:** Measures the magnitude and direction of two vectors. Represented by the `<#>` operator (returns negative inner product, so multiply by -1 for the actual inner product).
  * **Cosine distance:** Measures the cosine of the angle between two vectors, indicating their directional similarity. Represented by the `<=>` operator. Cosine similarity is calculated as 1 – `cosine_distance`.
  * **Indexing for performance:** pgvector supports indexing techniques like HNSW (Hierarchical Navigable Small Worlds) to accelerate approximate nearest neighbor (ANN) searches on large datasets, significantly improving query performance.


## A bit of background: What Is similarity search?
Similarity search is a technique used to find items in a dataset that are most similar to a given query item. Unlike traditional exact-match searches, similarity search compares high-dimensional representations, such as image embeddings or text vectors, to identify results that are not only identical but contextually or semantically close. This is central to use cases like image recognition, recommendation systems, and natural language processing where relevance is derived from approximate resemblance, not just strict equality.
There are multiple approaches to implementing similarity search. These typically use distance metrics to measure closeness between vectors, with lower distances indicating greater similarity. Indexing schemes and algorithmic optimizations ensure that searches remain efficient, even with large datasets and vectors with hundreds or thousands of dimensions, enabling real-time or near-real-time querying for interactive applications.
## Tips from the expert
Perry Clark
Professional Services Consultant
Perry Clark is a seasoned open source consultant with NetApp. Perry is passionate about delivering high-quality solutions and has a strong background in various open source technologies and methodologies, making him a valuable asset to any project.
In my experience, here are tips that can help you better optimize similarity search with pgvector for real-world ML workloads:
  1. **Select the right embedding model:** Use `all-MiniLM-L6-v2` for efficient, pre-trained embeddings with a balance of speed and accuracy. Chunk large documents to fit within the model’s context window.
  2. **Boost query 

[Content truncated...]