# Enhancing RAG with contextual retrieval - Claude Developer Platform
**URL:** https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide
**Domain:** platform.claude.com
**Score:** 2.9
**Source:** scraped
**Query:** contextual chunking prepend context before embedding

---

# 
Enhancing RAG with Contextual Retrieval
> Note: For more background information on Contextual Retrieval, including additional performance evaluations on various datasets, we recommend reading our accompanying [blog post](https://www.anthropic.com/news/contextual-retrieval).
Retrieval Augmented Generation (RAG) enables Claude to leverage your internal knowledge bases, codebases, or any other corpus of documents when providing a response. Enterprises are increasingly building RAG applications to improve workflows in customer support, Q&A over internal company documents, financial & legal analysis, code generation, and much more.
In a [separate guide](https://github.com/anthropics/anthropic-cookbook/blob/main/capabilities/retrieval_augmented_generation/guide.ipynb), we walked through setting up a basic retrieval system, demonstrated how to evaluate its performance, and then outlined a few techniques to improve performance. In this guide, we present a technique for improving retrieval performance: Contextual Embeddings.
In traditional RAG, documents are typically split into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context. Contextual Embeddings solve this problem by adding relevant context to each chunk before embedding. This method improves the quality of each embedded chunk, allowing for more accurate retrieval and thus better overall performance. Averaged across all data sources we tested, Contextual Embeddings reduced the top-20-chunk retrieval failure rate by 35%.
The same chunk-specific context can also be used with BM25 search to further improve retrieval performance. We introduce this technique in the "Contextual BM25" section.
In this guide, we'll demonstrate how to build and optimize a Contextual Retrieval system using a dataset of 9 codebases as our knowledge base. We'll walk through:
  1. Setting up a basic retrieval pipeline to establish a baseline for performance.
  2. Contextual Embeddings: what it is, why it works, and how prompt caching makes it practical for production use cases.
  3. Implementing Contextual Embeddings and demonstrating performance improvements.
  4. Contextual BM25: improving performance with _contextual_ BM25 hybrid search.
  5. Improving performance with reranking,


### 
Evaluation Metrics & Dataset:
We use a pre-chunked dataset of 9 codebases - all of which have been chunked according to a basic character splitting mechanism. Our evaluation dataset contains 248 queries - each of which contains a 'golden chunk.' We'll use a metric called Pass@k to evaluate performance. Pass@k checks whether or not the 'golden document' was present in the first k documents retrieved for each query. Contextual Embeddings in this case helped us to improve Pass@10 performance from ~87% --> ~95%.
You can find the code files and their chunks in `data/codebase_chunks.json` and the evaluation dataset in `data/evaluation_set.jsonl`
#### 
Additional Notes:
Prompt caching is helpful in managing costs when using this retrieval method. This feature is currently available on Anthropic's first-party API, and is coming soon to our third-party partner environments in AWS Bedrock and GCP Vertex. We know that many of our customers leverage AWS Knowledge Bases and GCP Vertex AI APIs when building RAG solutions, and this method can be used on either platform with a bit of customization. Consider reaching out to Anthropic or your AWS/GCP account team for guidance on this!
To make it easier to use this method on Bedrock, the AWS team has provided us with code that you can use to implement a Lambda function that adds context to each document. If you deploy this Lambda function, you can select it as a custom chunking option when configuring a [Bedrock Knowledge Base](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-create.html). You can find this code in `contextual-rag-lambda-function`. The main l

[Content truncated...]