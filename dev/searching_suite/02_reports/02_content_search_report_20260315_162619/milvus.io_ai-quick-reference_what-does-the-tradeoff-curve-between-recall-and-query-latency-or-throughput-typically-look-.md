# What does the trade-off curve between recall and query latency or ...
**URL:** https://milvus.io/ai-quick-reference/what-does-the-tradeoff-curve-between-recall-and-query-latency-or-throughput-typically-look-like-and-how-can-this-curve-inform-decisions-about-index-parameters
**Domain:** milvus.io
**Score:** 8.0
**Source:** scraped
**Query:** HNSW index parameters recall vs latency tradeoff

---

  * What does the trade-off curve between recall and query latency or throughput typically look like, and how can this curve inform decisions about index parameters?


Copy page
# What does the trade-off curve between recall and query latency or throughput typically look like, and how can this curve inform decisions about index parameters?
The trade-off curve between recall and query latency or throughput generally follows a concave shape, where increasing recall comes at the cost of higher latency or reduced throughput, especially as you approach higher recall values. Initially, small improvements in recall might require only modest increases in latency. For example, expanding a search from checking 10% to 20% of an index’s data might boost recall significantly with minimal impact on speed. However, beyond a certain point, further gains in recall demand disproportionately more computational work, causing latency to spike. This is because exhaustive methods (like brute-force search) achieve near-perfect recall but are slow, while approximate nearest neighbor (ANN) techniques sacrifice some recall for speed by limiting the search scope.
Index parameters directly influence where a system operates on this curve. For instance, in a vector database using hierarchical navigable small world (HNSW) graphs, increasing the `efSearch` parameter—which controls how many nodes are explored during a query—improves recall but slows down each query. Similarly, in inverted file index (IVF) methods, raising the `nprobe` value (the number of clusters to scan per query) increases recall but requires more distance calculations, impacting latency. Quantization settings also matter: using 8-bit integers instead of 32-bit floats reduces memory usage and speeds up searches but introduces approximation errors, lowering recall. These parameters allow developers to tune the balance between accuracy and speed based on their application’s needs.
To make informed decisions, developers must first define their application’s requirements. For example, a real-time recommendation system might prioritize latency (e.g., <50ms per query) and tolerate 80% recall, while a batch data analysis tool could accept higher latency for 95% recall. Testing with representative workloads is critical: measuring how recall and latency change as parameters like `nprobe` or `efSearch` are adjusted helps identify the “knee” of the curve—the point where further gains in recall become too costly. Additionally, techniques like sharding or caching can shift the curve itself. Splitting an index across multiple machines (sharding) improves throughput without directly affecting recall, while caching frequent queries reduces latency but doesn’t change the underlying index behavior. By combining parameter tuning with system-level optimizations, developers can tailor the trade-off to their specific use case.
## Need a VectorDB for Your GenAI Apps?
Zilliz Cloud is a managed vector database built on Milvus perfect for building GenAI applications.
[Try Free](https://cloud.zilliz.com/signup?utm_source=milvusio&utm_medium=referral&utm_campaign=milvus_right_card&utm_content=ai-quick-reference/what-does-the-tradeoff-curve-between-recall-and-query-latency-or-throughput-typically-look-like-and-how-can-this-curve-inform-decisions-about-index-parameters)
#### Recommended Tech Blogs & Tutorials
  * [Building AI Agents in 10 Minutes Using Natural Language with LangSmith Agent Builder + Milvus ](https://milvus.io/blog/building-ai-agents-in-10-minutes-using-natural-language-with-langsmith-agent-builder-milvus.md)
  * [Stop Paying for Cold Data: 80% Cost Reduction with On-Demand Hot–Cold Data Loading in Milvus Tiered Storage ](https://milvus.io/blog/milvus-tiered-storage-80-less-vector-search-cost-with-on-demand-hot%E2%80%93cold-data-loading.md)
  * [7 Years, 2 Major Rebuilds, 40K+ GitHub Stars: The Rise of Milvus as the Leading Open-Source Vector Database ](https://milvus.io/blog/milvus-exceeds-40k-github-st

[Content truncated...]