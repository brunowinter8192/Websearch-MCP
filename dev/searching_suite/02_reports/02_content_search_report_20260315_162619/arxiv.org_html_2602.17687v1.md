# irpapers: A Visual Document Benchmark for Scientific Retrieval and ...
**URL:** https://arxiv.org/html/2602.17687v1
**Domain:** arxiv.org
**Score:** 16.0
**Source:** scraped
**Query:** HyDE vs direct retrieval comparison benchmark

---

[License: CC BY 4.0](https://info.arxiv.org/help/license/index.html#licenses-available)
arXiv:2602.17687v1 [cs.IR] 05 Feb 2026
#  irpapers: A Visual Document Benchmark for Scientific Retrieval and Question Answering
Report issue for preceding element
Connor Shorten Weaviate &Augustas Skaburskas Weaviate &Daniel M. Jones Weaviate &Charles Pierse Weaviate  Roberto Esposito Weaviate &John Trengrove Weaviate &Etienne Dilocker Weaviate &Bob van Luijt Weaviate 
Report issue for preceding element
###### Abstract
Report issue for preceding element
AI systems have achieved remarkable success in processing text and relational data, however, visual document processing remains relatively underexplored. Whereas traditional systems require OCR transcriptions to convert these visual documents into text and metadata, recent advances in multimodal foundation models offer an alternative path: retrieval and generation directly from document images. This raises a timely and important question: How do image-based systems compare to established text-based methods? To answer this question, we present IRPAPERS, a benchmark totaling 3,230 pages sourced from 166 scientific papers, with both an image and OCR transcription for each page. We present a curation of 180 needle-in-the-haystack questions for evaluating retrieval and question answering systems with this corpus. We begin by comparing image- and text-based retrieval with open-source models, as well as multimodal hybrid search. For image retrieval, we evaluate the ColModernVBERT multi-vector embedding model. For text retrieval, we evaluate Arctic 2.0 dense single-vector embeddings, BM25, and their combination in hybrid text search. Text-based methods achieved 46% Recall@1, 78% Recall@5, and 91% Recall@20, while image-based retrieval achieved 43% Recall@1, 78% Recall@5, and 93% Recall@20. These retrieval systems exhibit complementary failures, each succeeding on queries where the other fails, enabling multimodal fusion to exceed either modality alone. Multimodal hybrid search achieved the highest performance with 49% Recall@1, 81% Recall@5, and 95% Recall@20. We additionally evaluate the efficiency-performance tradeoff of MUVERA encoding with varying levels of ef, as well as the performance of the ColPali and ColQwen2 multi-vector image embeddings models. To contextualize open-source performance, we further evaluate leading closed-source models. Cohere Embed v4 page image embeddings reached 58% Recall@1, 87% Recall@5, and 97% Recall@20, outperforming Voyage 3 Large text transcription embeddings at 52% Recall@1, 86% Recall@5, and 95% Recall@20, as well as all tested open-source models. For question answering, we evaluate RAG using an LLM-as-Judge to assess binary semantic equivalence between the ground truth and the answer from the tested RAG system. RAG systems using text inputs achieved a ground truth alignment score of 0.82, compared to 0.71 for image inputs. Notably, both modalities benefit substantially from increased retrieval depth for question answering. Retrieving five documents outperforms even oracle single-document retrieval, suggesting that related pages provide valuable supporting context for answer synthesis. We conclude by exploring the comparative limitations of text and image unimodal representations: Are there questions that require the image representation to answer?, and inversely, Are there questions that require a text representation to answer?. These results illuminate the current state of visual document search and question answering technologies. We have open-sourced our IRPAPERS dataset on HuggingFace at huggingface.co/weaviate/IRPAPERS and GitHub at github.com/weaviate/IRPAPERS. Our experimental code is also available on GitHub at github.com/weaviate/query-agent-benchmarking.
Report issue for preceding element
##  1 Introduction
Report issue for preceding element
Visual document processing has seen rapid and sustained progress in recent years. Advances in multimodal repre

[Content truncated...]