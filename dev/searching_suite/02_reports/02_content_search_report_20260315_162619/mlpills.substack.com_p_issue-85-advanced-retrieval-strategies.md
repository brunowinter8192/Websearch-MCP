# Issue #85 - Advanced Retrieval Strategies: HyDE
**URL:** https://mlpills.substack.com/p/issue-85-advanced-retrieval-strategies
**Domain:** mlpills.substack.com
**Score:** 9.0
**Source:** scraped
**Query:** HyDE vs direct retrieval comparison benchmark

---

SubscribeSign in
# Issue #85 - Advanced Retrieval Strategies: HyDE
Jan 04, 2025
∙ Paid
Share
#  💊 **Pill of the Week**
Large Language Models (LLMs) have revolutionized how we process and retrieve information, but they face challenges when dealing with mismatches between query formats and document content. Hypothetical Document Embeddings (HyDE) offers an innovative solution to this problem by transforming user queries into document-like formats before performing retrieval.
In the past, we've explored **other advanced retrieval strategies**. You can review them here:
#### [Issue #66 - Advanced Retrieval Strategies: Query Translation I · 21. Juli 2024 ](https://mlpills.substack.com/p/issue-67-advanced-retrieval-strategies)
#### [Issue #70 - Advanced Retrieval Strategies: Query Translation II · 25. August 2024 ](https://mlpills.substack.com/p/issue-71-advanced-retrieval-strategies)
## Understanding HyDE
HyDE addresses a fundamental challenge in Retrieval Augmented Generation (RAG) systems: the disparity between short, potentially informal user queries and longer, well-structured documents. The technique works by using an LLM to generate a hypothetical document that answers the user's query, then using this generated document for retrieval instead of the original query.
The power of HyDE lies in its ability to bridge the gap between query and document spaces. When a user submits a query, HyDE first transforms it into a well-structured document that might contain the answer. While this generated document may contain inaccurate information, its structure and format more closely match the actual documents in the knowledge base, making retrieval more effective.
_🎉**15-Day Free Subscription Giveaway!** 🎉We love giving back to our readers! In every issue of this newsletter, one lucky person who ❤️ likes the article will win a **free 15-day subscription** to MLPills._
_Don’t miss your chance—**like this article** and you could be our next winner!_
## When to Use HyDE
HyDE is particularly valuable in several scenarios:
The technique shines when working with embedding models trained through contrastive learning on document-document pairs. These models, which learn to distinguish between semantically similar and dissimilar texts, benefit from HyDE's document-like query representations.
It's especially useful when dealing with specialized domains that differ significantly from typical datasets that retrievers are trained on. In these cases, HyDE can help bridge the domain gap between queries and documents.
HyDE can also be beneficial when your retrieval performance metrics, such as recall, aren't meeting expectations. By generating multiple hypothetical documents for each query, HyDE can capture different aspects of the information need, potentially improving retrieval accuracy.
However, not all scenarios require HyDE. If your embedding model has been specifically trained for asymmetric semantic search (matching short queries to longer documents) using supervised learning, HyDE may not provide significant benefits. This is often the case for models trained on question-answering datasets like MS MARCO.
## Implementation Process
Implementing HyDE involves a sequence of structured steps, each designed to enhance retrieval performance by leveraging the power of large language models (LLMs) and embedding-based similarity search. Here's a detailed breakdown of the process:
  1. **Query Generation:** The process begins with the user submitting a query, which the system processes using an LLM capable of generating hypothetical documents. Along with the query, the system provides an instruction for the LLM to **produce documents that comprehensively address the query's intent**. To ensure diversity and robustness in the generated responses, the system typically creates multiple hypothetical documents, often around five, by varying the temperature settings during generation. **This approach captures a broader semantic spectrum of the query, making the

[Content truncated...]