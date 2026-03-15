# Better RAG with HyDE - Hypothetical Document Embeddings - Zilliz
**URL:** https://zilliz.com/learn/improve-rag-and-information-retrieval-with-hyde-hypothetical-document-embeddings
**Domain:** zilliz.com
**Score:** 5.0
**Source:** scraped
**Query:** HyDE hypothetical document embeddings implementation

---

  * Retrieval Augmented Generation (RAG) 101


Copy page
# Improving Information Retrieval and RAG with Hypothetical Document Embeddings (HyDE)
Jul 25, 20249 min read
HyDE (Hypothetical Document Embeddings) is a retrieval method that uses "fake" documents to improve the answers of LLM and RAG. 
By [ Haziqa Sajid](https://zilliz.com/authors/_Haziqa_Sajid)
Read the entire series
  * [Build AI Apps with Retrieval Augmented Generation (RAG)](https://zilliz.com/learn/Retrieval-Augmented-Generation)
  * [Mastering LLM Challenges: An Exploration of Retrieval Augmented Generation](https://zilliz.com/learn/RAG-handbook)
  * [Key NLP technologies in Deep Learning](https://zilliz.com/learn/nlp-technologies-in-deep-learning)
  * [How to Evaluate RAG Applications](https://zilliz.com/learn/How-To-Evaluate-RAG-Applications)
  * [Optimizing RAG with Rerankers: The Role and Trade-offs ](https://zilliz.com/learn/optimize-rag-with-rerankers-the-role-and-tradeoffs)
  * [Exploring the Frontier of Multimodal Retrieval-Augmented Generation (RAG)](https://zilliz.com/learn/multimodal-RAG)
  * [Enhancing ChatGPT with Milvus: Powering AI with Long-Term Memory](https://zilliz.com/learn/enhancing-chatgpt-with-milvus)
  * [How to Enhance the Performance of Your RAG Pipeline](https://zilliz.com/learn/how-to-enhance-the-performance-of-your-rag-pipeline)
  * [Enhancing ChatGPT with Milvus: Powering AI with Long-Term Memory](https://zilliz.com/learn/enhancing-chatgpt-with-milvus)
  * [Pandas DataFrame: Chunking and Vectorizing with Milvus](https://zilliz.com/learn/pandas-dataframe-chunking-anf-vectorizing-with-milvus)
  * [How to build a Retrieval-Augmented Generation (RAG) system using Llama3, Ollama, DSPy, and Milvus](https://zilliz.com/learn/how-to-build-rag-system-using-llama3-ollama-dspy-milvus)
  * [A Guide to Chunking Strategies for Retrieval Augmented Generation (RAG)](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag)
  * [Improving Information Retrieval and RAG with Hypothetical Document Embeddings (HyDE)](https://zilliz.com/learn/improve-rag-and-information-retrieval-with-hyde-hypothetical-document-embeddings)
  * [Building RAG with Milvus Lite, Llama3, and LlamaIndex](https://zilliz.com/learn/build-rag-with-milvus-lite-llama3-and-llamaindex)
  * [Enhancing RAG with RA-DIT: A Fine-Tuning Approach to Minimize LLM Hallucinations](https://zilliz.com/learn/enhance-rag-with-radit-fine-tune-approach-to-minimize-llm-hallucinations)
  * [Building RAG with Dify and Milvus](https://zilliz.com/learn/building-rag-with-dify-and-milvus)
  * [Top 10 RAG & LLM Evaluation Tools You Don't Want To Miss](https://zilliz.com/learn/top-ten-rag-and-llm-evaluation-tools-you-dont-want-to-miss)


In recent years, **dense retrievers** powered by [neural networks](https://zilliz.com/learn/Neural-Networks-and-Embeddings-for-Language-Models) have emerged as a modern alternative to traditional sparse methods based on term frequency in [information retrieval](https://zilliz.com/learn/information-retrieval-metrics). These models have obtained state-of-the-art results on datasets and tasks where large training sets are available. However, extensive labeled datasets are not always available or suitable due to restrictions on use. Moreover, these datasets often do not encompass the full spectrum of real-world search scenarios, limiting their effectiveness.
[**Zero-shot methods**](https://zilliz.com/learn/what-is-zero-shot-learning), therefore, aim to transcend these limitations by enabling retrieval systems that can generalize across tasks and domains without relying on explicit relevance supervision. Performing document retrieval without prior training on task-specific data can minimize the training overhead and lower the cost of dataset creation.
This blog will cover the details of a zero-shot retrieval method, [Hypothetical Document Embeddings (HyDE)](https://arxiv.org/pdf/2212.10496), which outperforms unsupervised and fine-tuned dense retrievers. Later, the blog will a

[Content truncated...]