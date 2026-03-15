# Chunking Strategies for RAG: Early, Late, and Contextual ... - Medium
**URL:** https://medium.com/@visrow/chunking-strategies-for-rag-early-late-and-contextual-chunking-explained-with-code-71b88e4709f9
**Domain:** medium.com
**Score:** 12.0
**Source:** scraped
**Query:** LLM generated context prefix per chunk retrieval

---

[Sitemap](https://medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
Press enter or click to view image in full size
# Chunking Strategies for RAG: Early, Late, and Contextual Chunking Explained (With Code)
Follow
10 min read Dec 17, 2025
Share
In Retrieval-Augmented Generation (RAG) systems, the quality of your results hinges on a critical but often overlooked decision: **how you chunk your documents**. While most developers focus on choosing the right embedding model or tuning their vector database, the chunking strategy you select can make or break your RAG system’s performance.
Think of chunking as the foundation of your RAG pipeline. A poor chunking strategy is like building a house on sand — no matter how sophisticated your retrieval or generation components are, your system will struggle to deliver accurate results. Conversely, choosing the right chunking strategy for your document type can dramatically improve retrieval accuracy, reduce hallucinations, and enhance user satisfaction.
But here’s the challenge: **there is no one-size-fits-all chunking strategy**. A strategy that excels for legal contracts may fail miserably for source code. An approach optimized for news articles might produce poor results with scientific papers. Understanding the strengths and weaknesses of different chunking approaches is essential for building production-quality RAG systems.
This article explores the landscape of chunking strategies, from traditional approaches to cutting-edge techniques, and presents real-world experimental results comparing nine different strategies using the [agenticmemory ](https://github.com/vishalmysore/agenticmemory)library.
> For comparing all startegis using Java you can look at this example <https://github.com/vishalmysore/chunkking/blob/main/src/main/java/io/github/vishalmysore/chunkking/AllChunkingStrategiesComparison.java>
## The Evolution of Chunking: Early, Late, and Contextual Approaches
## Early Chunking: The Traditional Approach
**Early chunking** refers to the traditional method that most RAG systems use today:
  1. **Split first:** Divide the document into chunks using simple heuristics (fixed size, sentence boundaries, paragraph breaks)
  2. **Embed separately:** Generate embeddings for each chunk independently
  3. **Index and search:** Store chunks in a vector database and retrieve based on similarity

```
Document → [Chunk 1] [Chunk 2] [Chunk 3] → Embed each → Vector DB
```

**The Problem:** When you chunk text before embedding, you lose critical context. Consider this example:
```
Chunk 1: "Berlin is the capital and largest city of Germany..."Chunk 2: "Its more than 3.85 million inhabitants make it..."Chunk 3: "The city is also one of the states of Germany..."
```

In Chunk 2, what does “Its” refer to? In Chunk 3, which city? When these chunks are embedded separately, the embedding model cannot resolve these anaphoric references, leading to poor-quality embeddings that hurt retrieval performance.
**Advantages:**
  * Simple to implement
  * Fast processing
  * Works with any embedding API


**Disadvantages:**
  * Loses cross-chunk context
  * Poor handling of anaphoric references (pronouns, “the city”, “it”, etc.)
  * Arbitrary boundaries can split related information


## Late Chunking: Preserving Full Context
**Late chunking** reverses the order of operations:
  1. **Embed first:** Generate token-level embeddings for the entire document
  2. **Chunk later:** Apply chunking boundaries to the token embeddings
  3. **Pool tokens:** Aggregate token embeddings within each chunk

```
Full Document → Token-level embeddings → Apply chunk boundaries → Pool → Vector DB
```

[Content truncated...]