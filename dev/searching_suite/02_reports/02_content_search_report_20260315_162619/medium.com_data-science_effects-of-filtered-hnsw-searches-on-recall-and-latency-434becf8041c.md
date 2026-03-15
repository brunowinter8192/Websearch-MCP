# Effects of filtered HNSW searches on Recall and Latency - Medium
**URL:** https://medium.com/data-science/effects-of-filtered-hnsw-searches-on-recall-and-latency-434becf8041c
**Domain:** medium.com
**Score:** 16.0
**Source:** scraped
**Query:** HNSW index parameters recall vs latency tradeoff

---

[Sitemap](https://medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
Follow publication
An archive of data science, data analytics, data engineering, machine learning, and artificial intelligence writing from the former Towards Data Science Medium publication.
Follow publication
# Effects of filtered HNSW searches on Recall and Latency
## An experiment to see how both loose and restrictive filters affect vector search speed and quality.
Follow
8 min read Oct 18, 2021
Share
This article contains an experiment of how applying filters to an HNSW-based vector search affects recall and query speed. Using a simple trick, we can achieve high recall and low response times on any kind of filter — without knowing what filters would look like upfront.
Press enter or click to view image in full size
Filtered HNSW Vector Search — Effects on Recall and Query times. Image by Author.
Vector search is a hot topic right now and [HNSW](https://arxiv.org/abs/1603.09320) is one of the [top contenders](http://ann-benchmarks.com/hnsw\(nmslib\).html) for ANN index models with regards to Recall/Latency trade-offs. If incremental build-up and CRUD operations are important — as is typically the case for vector search engines — HNSW is often considered the best option. In real-life cases, vector searches often need to be filtered. For example, in an e-commerce application, users may wish to find items related to the ones currently in the shopping cart (vector search) but filter them by availability and profit margin (structured search).
HNSW can be tweaked to allow for such structured filtering, but this raises the question of the effects of such filtering on both query speed and recall. Existing benchmarks only measure these trade-offs for unfiltered searches. In this article, we will run a few experiments with filtered vector search using the open-source vector search engine [Weaviate](https://www.semi.technology/developers/weaviate/current/) which supports [these operations out of the box](https://www.semi.technology/developers/weaviate/current/graphql-references/filters.html#where-filter). We will apply filters of varying restrictiveness and compare query speed and recall to unfiltered vector searches.
## Post-Filtering vs. Pre-Filtering
Generally, there are two paradigms with regards to filtering vector-search; either the filter is applied after a vector search has already been completed or before. Post-filtering may work well if the filter is not very restrictive, that is when it contains a large portion of the dataset. However, when the filter gets very restrictive, the recall drops dramatically on post-filtering. Imagine a scenario where the filter matches just 5% of the dataset. Now perform a k=20 vector search. Assuming data were evenly distributed, we expect to only contain a single match in our result set, yet the user asked for 20 results.
> Post-filtering can lead to very low recall values when the filters become more restricve. Thus, pre-filtering in combination with an efficient vector index is required to achieve great overall recall.
This shows that post-filtering is not a viable option if we want to address filters of all levels of restrictiveness. Instead, we need to apply pre-filtering. Some authors suggest that the term per-filtering implies that an ANN model can no longer be used. However, this is not the definition used in this article. We use the term pre-filtering to mean that an efficient “traditional” index structure, such as an inverted list, can be used to determine the allowed set of candidates. Then this list is passed to the ANN model — in this case, HNSW.
## The test setup
For our experiment, we have chosen the following settings:
  * Running with Weaviate v1.8.0 which uses a custom HNSW implementation with extended filtering 

[Content truncated...]