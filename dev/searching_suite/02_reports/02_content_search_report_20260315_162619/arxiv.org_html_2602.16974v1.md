# A Comprehensive Taxonomy and Evaluation of Document Chunking ...
**URL:** https://arxiv.org/html/2602.16974v1
**Domain:** arxiv.org
**Score:** 2.0
**Source:** scraped
**Query:** chunk overlap size impact retrieval quality embedding

---

[License: CC BY-SA 4.0](https://info.arxiv.org/help/license/index.html#licenses-available)
arXiv:2602.16974v1 [cs.IR] 19 Feb 2026
# Beyond Chunk-Then-Embed: A Comprehensive Taxonomy and Evaluation of Document Chunking Strategies for Information Retrieval
Report issue for preceding element
Yongjie Zhou1* Shuai Wang1*† Bevan Koopman1,2 Guido Zuccon1,3 The University of Queensland, Australia 2CSIRO, Australia 3Google {yongjie.zhou@student.uq.edu.au, shuai.wang2@uq.edu.au, g.zuccon@uq.edu.au} Bevan.Koopman@csiro.au *Equal contribution †Corresponding author 
Report issue for preceding element
###### Abstract
Report issue for preceding element
Document chunking is a critical preprocessing step in dense retrieval systems, yet the design space of chunking strategies remains poorly understood. Recent research has proposed several concurrent approaches, including LLM-guided methods (e.g., DenseX and LumberChunker) and contextualized strategies(e.g., Late Chunking), which generate embeddings before segmentation to preserve contextual information. However, these methods emerged independently and were evaluated on benchmarks with minimal overlap, making direct comparisons difficult.
Report issue for preceding element
This paper reproduces prior studies in document chunking and presents a systematic framework that unifies existing strategies along two key dimensions: (1) segmentation methods, including structure-based methods (fixed-size, sentence-based, and paragraph-based) as well as semantically-informed and LLM-guided methods; and (2) embedding paradigms, which determine the timing of chunking relative to embedding (pre-embedding chunking vs. contextualized chunking). Our reproduction evaluates these approaches in two distinct retrieval settings established in previous work: in-document retrieval (needle-in-a-haystack) and in-corpus retrieval (the standard information retrieval task).
Report issue for preceding element
Our comprehensive evaluation reveals that optimal chunking strategies are task-dependent: simple structure-based methods outperform LLM-guided alternatives for in-corpus retrieval, while LumberChunker performs best for in-document retrieval. Contextualized chunking improves in-corpus effectiveness but degrades in-document retrieval. We also find that chunk size correlates moderately with in-document but weakly with in-corpus effectiveness, suggesting segmentation method differences are not purely driven by chunk size. Our code and evaluation benchmarks are publicly available at Anonymoused for review.
Report issue for preceding element
##  1 Introduction
Report issue for preceding element
Dense retrieval systems represent queries and documents as low-dimensional vectors and power applications from web search engines to retrieval-augmented generation (RAG) frameworks . However, embedding models have fixed-size input windows, requiring long documents to be partitioned into smaller segments: a process known as document chunking. The choice of chunking methods significantly impacts retrieval effectiveness: chunks that are too small may lack sufficient context to match relevant queries, while oversized chunks can dilute relevant information with irrelevant content, and chunks that divide up cohesive relevant content might be highly detrimental to downstream tasks.
Report issue for preceding element
Document chunking has evolved rapidly along two dimensions: segmentation methods and embedding-chunking ordering. Segmentation methods determine how documents are divided into chunks, while embedding paradigms determine when chunking occurs relative to embedding (e.g., chunking before or after encoding). For segmentation, structure-based methods use fixed windows or linguistic boundaries like paragraphs , while recent work has introduced semantically-informed methods such as proposition-based chunking like DenseX and LLM-guided methods like LumberChunker , which leverage large language models to identify discourse-aware boundaries. 

[Content truncated...]