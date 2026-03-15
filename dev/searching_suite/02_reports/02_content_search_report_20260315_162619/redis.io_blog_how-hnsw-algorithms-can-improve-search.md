# How hierarchical navigable small world (HNSW) algorithms can ...
**URL:** https://redis.io/blog/how-hnsw-algorithms-can-improve-search/
**Domain:** redis.io
**Score:** 2.1
**Source:** scraped
**Query:** HNSW index parameters recall vs latency tradeoff

---

All eyes on AI: 2026 predictions – The shifts that will shape your stack.
[Read now](http://redis.io/2026-predictions/)
Resource Center
[Events & webinars](https://redis.io/events/)[Blog](https://redis.io/blog/)[Videos](https://redis.io/resources/videos/)[Glossary](https://redis.io/glossary/)[Resources](https://redis.io/resources/all/)[Architecture Diagrams](https://redis.io/resources/architecture-diagrams/)[Demo Center](https://redis.io/demo-center/)
Blog
[Events & webinars](https://redis.io/events/)[Videos](https://redis.io/resources/videos/)[Glossary](https://redis.io/glossary/)[Resources](https://redis.io/resources/all/)[Architecture Diagrams](https://redis.io/resources/architecture-diagrams/)[Demo Center](https://redis.io/demo-center/)
Blog
# How hierarchical navigable small world (HNSW) algorithms can improve search
June 10, 202511 minute read
Jim Allen Wallace
Think of the ["six degrees of Kevin Bacon" game](https://en.wikipedia.org/wiki/Six_Degrees_of_Kevin_Bacon): everyone is connected by just a few people. That same principle powers hierarchical navigable small world (HNSW) algorithms, which link data points so queries can reach the right match in far fewer hops.
Modern applications frequently deal with high-dimensional data—embeddings of images, text, and more. A brute-force k-Nearest Neighbors (KNN) search becomes impractical as dimensionality increases, which is why approximate nearest neighbors (ANN) algorithms trade slight accuracy for much better speed. But not all ANN algorithms are created equal. Many introduce latency issues and scalability bottlenecks that limit their usefulness.
HNSW has emerged as the leading ANN approach for high-dimensional [vector search](https://redis.io/learn/howtos/solutions/vector/getting-started-vector)—whether you're building similarity search, recommendation engines, or AI applications—because it balances speed, accuracy, and scalability better than alternatives. By organizing data into layered graphs, HNSW dramatically reduces search complexity while maintaining high recall, making it the go-to choice for enterprise-scale workloads.
## What is a hierarchical navigable small world (HNSW)?
Hierarchical navigable small world, or HNSW, is a graph-based ANN algorithm that combines navigable small worlds (networks of points where each point is connected to its nearest neighbors) and hierarchy (layers that refine search to support speed). Researchers Yu A. Malkov and D. A. Yashunin introduced the idea in the [2016 paper](https://arxiv.org/abs/1603.09320), “Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs.”
Unlike other ANN algorithms, which tend to require an exhaustive and often slow search, HNSW provides a graph that minimizes hops from point to point and a hierarchy that doesn’t require many distance computations. The combination of the two is what makes HNSW stand apart from other ANN algorithms: [One study](https://arxiv.org/pdf/1807.05614) found that, in comparison to other ANN algorithms, “Over all recall values, HNSW is fastest.”
HNSW algorithms also tend to outcompete ANN algorithms in practical terms. Many ANN methods require a training phase, but HNSW doesn’t, meaning teams can build the HNSW incrementally and update it over time.
Because of its performance and practicality, HNSW shines in numerous use cases, including:
  * Image recognition and retrieval, where search functions have to search across high-dimensional vectors.
  * Natural language processing (NLP), where it can support semantic and similarity search functions.
  * Recommendation engines, where it can suggest a relevant product for a shopper or highlight the best paragraph from a help center to assist a user with troubleshooting.
  * Anomaly detection, where it can support search across large datasets to detect fraud and monitor networks.


[Content truncated...]