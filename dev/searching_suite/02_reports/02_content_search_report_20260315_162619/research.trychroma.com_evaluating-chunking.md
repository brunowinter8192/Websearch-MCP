# Evaluating Chunking Strategies for Retrieval - Chroma Research
**URL:** https://research.trychroma.com/evaluating-chunking
**Domain:** research.trychroma.com
**Score:** 19.0
**Source:** scraped
**Query:** chunk overlap size impact retrieval quality embedding

---

Table of Contents
Evaluating Chunking Strategies for Retrieval
[Chroma Technical Report](https://research.trychroma.com/)
July 03, 2024
Evaluating Chunking Strategies for Retrieval
[Brandon Smith](https://x.com/@brandonstarxel)Researcher in Residence - Chroma
[Anton Troynikov](https://x.com/atroyn)Cofounder - Chroma
Despite document chunking being virtually ubiquitous as a pre-processing step, little work has been done to investigate its impact on retrieval performance. This is partially due to the structure of commonly used information retrieval benchmarks, which are aimed at whole-document retrieval tasks. 
In this work we present an evaluation approach which takes token-level relevance into account, and allows for the evaluation of several popular document chunking strategies. We demonstrate that the choice of chunking strategy can have a significant impact on retrieval performance, with some strategies outperforming others by up to 9% in recall. 
Evaluation of various popular chunking strategies on our evaluation, as well as new (★) strategies we propose. We show that the choice of chunking strategy can have significant impact on retrieval performance, in terms of accuracy and efficiency. Size denotes chunk size in tokens, in brackets indicates mean chunk size where it may vary by chunking strategy. Overlap denotes the chunk overlap in tokens. Bold values highlight the best performance in each category. See metrics section for details of each metric.
Chunking is a commonly used pre-processing step when ingesting documents for retrieval in the context of AI applications. Chunking serves to divide documents into units of information, with semantic content suitable for embeddings-based retrieval and processing by an LLM.
The purpose of this technical report is to evaluate the impact of the choice of chunking strategy on retrieval performance, in a way representative of how chunking and retrieval is used in the context of AI applications.
While LLM context lengths have grown, and it has become possible to insert entire documents, or even text corpora into the context window, in practice doing so is often inefficient, and can distract the model. For any given query, only a small portion of the text corpus is likely to be relevant, but all tokens in the context window are processed for each inference. Ideally, for each query, the LLM would only need to process only the relevant tokens, and hence one of the primary goals of a retrieval system in AI applications is to identify and retrieve only the relevant tokens for a given query.
Commonly used benchmarks like [MTEB](https://arxiv.org/abs/2210.07316) take a traditional information retrieval (IR) approach, where retrieval performance is typically evaluated with respect to the relevance of entire documents, rather than at the level of passages or tokens, meaning they cannot take chunking into account.
In AI applications, excerpts containing all tokens relevant to a query may be found within or across many documents. Chunks may contain both relevant and irrelevant tokens, and relevant excerpts may be split across chunks.
Traditional IR benchmarks also often focus on the relative ranking of the retrieved documents, however in practice, LLMs are relatively insensitive to the position of the relevant information within the context window. Additionally, the information relevant to a given query may be spread across multiple documents, making the evaluation of relative ranking between documents ambiguous.
Motivated by these limitations, we propose a new evaluation strategy, evaluating retrieval performance at the token level. Our evaluation uses an LLM to generate, and subsequently filter, a set of queries and associated relevant exerpts from any given text corpus, and subsequently evaluates retrieval performance via precision, recall, and intersection-over-union ([Jaccard index](https://en.wikipedia.org/wiki/Jaccard_index)) on the basis of retrieved _tokens_.
Our evaluation takes a fin

[Content truncated...]