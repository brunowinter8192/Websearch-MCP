# Predli Blog - RAG series: Two types of chunks
**URL:** https://www.predli.com/post/rag-series-two-types-of-chunks
**Domain:** www.predli.com
**Score:** 0.8
**Source:** scraped
**Query:** sentence window retrieval vs parent document retrieval

---

# RAG series: Two types of chunks
By 
Matouš Eibich
October 14, 2024
## Introduction
Welcome back to our exploration of Retrieval-Augmented Generation (RAG). Having laid the groundwork with an[ introduction to RAG](https://www.predli.com/post/rag-series-intro) and delved into [query expansion techniques](https://www.predli.com/post/rag-series-query-expansion), our series progresses to a critical aspect of advanced RAG: decoupling the chunks used for retrieval from those used for synthesis in Large Language Models (LLMs). This post aims to dissect the rationale and methodologies behind separating these two processes. Let us get to it!
## Decoupling retriever and LLM
The motivation behind this approach is clear: retrieval processes are more efficient with smaller chunks of data, while the generation of responses by LLMs benefits from larger, more contextually rich chunks. By separating the chunk sizes used for these two stages, we optimize the performance of both retrieval and generation—ensuring precise, relevant information retrieval and comprehensive, nuanced response synthesis. This decoupling addresses the unique needs of each process, leading to a significant improvement in the overall effectiveness of RAG applications.
## Sentence-window retriever
‍
The Sentence-window Retriever technique optimizes retrieval by focusing exclusively on individual sentences, acknowledging that short chunks yield better retrieval outcomes. For generation, it expands the context by including a couple of surrounding sentences alongside the retrieved sentence. This approach recognizes the LLM's need for a broader context to enhance reasoning capabilities. By retrieving based on single sentences and enriching the input to the LLM with additional context, SWR strikes a balance between efficient retrieval and effective synthesis, ensuring precise information retrieval and richer, more nuanced generation.
source: https://docs.llamaindex.ai/en/stable/optimizing/production_rag.html
## Auto-merging retrieval 
Auto-merging retrieval employs a hierarchical chunking strategy where documents are segmented into multiple levels (e.g., 2048, 512, 128), focusing retrieval on the smallest chunks to leverage efficiency. The innovation lies in merging these small, related chunks into their larger parent chunk when a majority are relevant, based on embedding similarity. This approach capitalizes on the retrieval efficiency of small chunks while ensuring the LLM benefits from a broader context for generation. It offers a dynamic balance, enhancing coherence and reducing token usage by smartly selecting when to provide more extensive context, thereby improving the LLM's generative output without overwhelming it with excessive detail.
source: https://twitter.com/llama_index/status/1729302797802451239
‍
## Document summary
The Document Summary technique streamlines retrieval by creating summaries for each document chunk at build-time, using these summaries for efficient lookup during query-time. This method relies on leveraging the summaries for initial retrieval—either through LLM-based determination of relevance and scoring or by comparing summary embeddings for similarity. The full text chunk associated with the relevant summary is then provided to the LLM for detailed response generation. This approach optimizes retrieval by focusing on condensed, essence-capturing summaries, ensuring that the LLM has access to comprehensive context without the inefficiency of processing entire documents, thereby marrying efficiency in retrieval with richness in synthesis.
source: https://www.llamaindex.ai/blog/a-new-document-summary-index-for-llm-powered-qa-systems-9a32ece2f9ec
## Conclusion
By decoupling the retrieval and synthesis processes and introducing innovative methods such as Sentence-window Retriever, Auto-merging Retrieval, and Document Summary, we significantly improve the LLM's ability to generate precise, contextually rich responses. These techniques, each addressi

[Content truncated...]