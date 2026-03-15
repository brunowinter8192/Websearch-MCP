# Understanding Recall in HNSW Search - Marqo's AI
**URL:** https://www.marqo.ai/blog/understanding-recall-in-hnsw-search
**Domain:** www.marqo.ai
**Score:** 4.8
**Source:** scraped
**Query:** HNSW index parameters recall vs latency tradeoff

---

We use essential cookies to make our site work. With your consent, we may also use non-essential cookies to improve user experience and analyze website traffic. By clicking “Accept,” you agree to our website's cookie use as described in our Cookie Policy. You can change your cookie settings at any time by clicking “Preferences.”
PreferencesDeclineAccept
State of AI in Consumer & Retail 2026 — Now Available
[Get the report](https://www.marqo.ai/state-of-ai-in-consumer-and-retail-2026)
Product
Customer Stories
Resources
Company
[Back to all Blog Posts](https://www.marqo.ai/blog)
Research
July 18, 2025
# Understanding Recall in HNSW Search
Have you calculated the recall of your vector search system? We observe HNSW with under-configured parameters dropping NDCG@10 by as much as 18% on popular benchmark datasets, changing rankings of models compared to exact KNN. Additionally the order in which you insert your data into the graph can result in up to a 17% relative change in recall. This holds true for text only datasets with text embedding models and multimodal datasets with CLIP models.
Unlike other articles which search for a fixed recall and tune parameters, we focus on a fixed set of parameters. While it is great to evaluate systems at various combinations of parameters this is also a time-consuming and expensive exercise that is cost and/or computationally intractable for many users. As such, default parameters will tend to be used in the majority of implementations, these are often poorly documented and in some libraries not easily accessible via the API. Many users also choose to access Vector databases through abstraction layers such as LangChain and LLaMaIndex which further obfuscates the HNSW parameters and behaviour.
Our exploration of recall in HNSW has led to the default configuration in Marqo V2. We opt for significantly higher defaults than other vector databases with efConstruction = 512, M = 16, and efSearch = 2000. In particular, efSearch is found to have a significant impact on recall in our experiments. Marqo V2 utilises Vespa which can handle these parameters without sacrificing performance.
## Quick Recap on HNSW
HNSW is an algorithm for approximate search that is used by many vector databases. HNSW offers a time complexity of n log(n) indexing of data and log(n) searching of data; this is better than doing exact KNN at search time which requires all distances to be calculated for a search complexity of n. This time complexity has made HNSW a popular choice for production search systems as indexing is typically not as time sensitive as search is. HNSW also has other nice properties, including parameterisation which makes it configurable with ways to trade-off computation time and memory usage. The algorithm works by forming a multi-layered graph where the density increases with each layer - the bottom layer contains all data and is usually implemented with twice the number of connections. This means that during search long distance connections can traject the query across the graph and land in the correct part of the base layer.
Indexing and search are very similar procedures. At indexing time a layer is randomly selected from an exponentially decaying distribution to decide the entry layer for that data point - the graph is searched and bidirectional links are formed to nearest neighbours.
Search is similar except it always starts at the entry point in the highest layer, the search continues through the layers, until the base layer where the nearest neighbours are found. An illustration of the process is given below.
There are three main parameters in HNSW:
  * M: The maximum number of bidirectional links to form from each node in the graph. Usually implementations will use 2 * M for base layer with all points. Higher M increases memory usage as well as latency for both indexing and search.
  * efConstruction: The number of candidates to consider when indexing. Typically implementations will store these cand

[Content truncated...]