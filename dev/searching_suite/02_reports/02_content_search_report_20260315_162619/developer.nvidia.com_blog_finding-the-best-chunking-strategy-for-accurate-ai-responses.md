# Finding the Best Chunking Strategy for Accurate AI Responses
**URL:** https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/
**Domain:** developer.nvidia.com
**Score:** 2.3
**Source:** scraped
**Query:** chunk overlap size impact retrieval quality embedding

---

[ Related Resources ](https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/#main-content-end)
[Agentic AI / Generative AI](https://developer.nvidia.com/blog/category/generative-ai/)
English 中文
# Finding the Best Chunking Strategy for Accurate AI Responses
Jun 18, 2025 
+11


AI-Generated Summary
Like
Dislike
  * Page-level chunking achieved the highest average accuracy (0.648) across diverse datasets and showed the lowest standard deviation (0.107), indicating consistent performance.
  * The optimal chunking strategy varies depending on the specific dataset and query characteristics, with factoid queries performing well with smaller chunks (256-512 tokens) and complex analytical queries benefiting from larger chunks (1,024 tokens) or page-level chunking using NVIDIA NeMo Retriever extraction.
  * Testing multiple chunking strategies, including page-level, token-based, and section-level chunking, is recommended to determine the best approach for a specific use case and content type.


AI-generated content may summarize information incompletely. Verify important information. 
A chunking strategy is the method of breaking down large documents into smaller, manageable pieces for AI retrieval. Poor chunking leads to irrelevant results, inefficiency, and reduced business value. It determines how effectively relevant information is fetched for accurate AI responses. With so many options available—page-level, section-level, or token-based chunking with various sizes—how do you determine which approach works best for your specific use case?
This blog post shares insights from our extensive experimentation across diverse datasets to help you optimize your [retrieval-augmented generation (RAG)](https://www.nvidia.com/en-us/glossary/retrieval-augmented-generation/) system’s chunking strategy.
## Introduction 
Chunking is a critical preprocessing step in [RAG pipelines](https://docs.nvidia.com/nemo-framework/user-guide/24.07/rag/ragoverview.html). It involves splitting documents into smaller, manageable pieces that can be efficiently indexed, retrieved, and used as context during response generation. When done poorly, chunking can lead to irrelevant or incomplete responses, frustrating users and undermining trust in the system. It can also increase the computational burden by forcing the retriever or generator to process excessive or unnecessary information.
On the other hand, a smart chunking strategy improves retrieval precision and contextual coherence, which directly enhances the quality of the generated answers. For users, this means faster, more accurate, and more helpful interactions. For businesses, it translates to higher user satisfaction, lower churn, and reduced operational costs due to more efficient resource utilization. In short, chunking isn’t just a technical detail—it’s a fundamental design choice that shapes the effectiveness of your entire RAG system.
Our research evaluated different chunking strategies across multiple datasets to establish guidelines for selecting the optimal approach based on your specific content and use case.
## Experimental setup 
_Figure 1. Experiment pipeline for evaluation and extraction_
### Chunking strategies tested 
We tested three primary chunking approaches to understand their impact on retrieval quality and response accuracy:
  1. **Token-based chunking** : Documents are split into fixed-size token chunks using content extracted by NVIDIA NeMo Retriever extraction. 
     * Sizes tested: 128, 256, 512, 1,024, and 2,048 tokens
     * With 15% overlap between chunks (we tested 10%, 15%, and 20% overlap values and found 15% to perform the best on FinanceBench with 1,024 token chunks. While not a full-grid search, this result aligns with the 10–20% overlap commonly seen in industry practices.)
  2. **Page-level chunking** : Each page of a document becomes a separate chunk. 
     * Implemented with bothNeMo Retriever extraction and[ nemoretriever-parse]

[Content truncated...]