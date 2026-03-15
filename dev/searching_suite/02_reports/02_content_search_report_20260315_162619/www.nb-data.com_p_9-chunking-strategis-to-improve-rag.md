# 9 Chunking Strategies to Improve RAG Performance - Non-Brand Data
**URL:** https://www.nb-data.com/p/9-chunking-strategis-to-improve-rag
**Domain:** www.nb-data.com
**Score:** 0.4
**Source:** scraped
**Query:** parent child chunking retrieval augmented generation

---

# [Non-Brand Data](https://www.nb-data.com/)
SubscribeSign in
Discover more from Non-Brand Data
Non-Brand Data provides expert tips on Machine Learning, Technology News, and Python Packages to help you excel and stand out in your data career.
Over 9,000 subscribers
Already have an account? Sign in
# 9 Chunking Strategies to Improve RAG Performance
### NBD Lite #52 How you splitting your data can affect the RAG performance
[Cornellius Yudha Wijaya](https://substack.com/@cornellius)
Mar 10, 2025
Share
_**All the code used here is present in the[RAG-To-Know repository](https://github.com/CornelliusYW/RAG-To-Know).**_
Retrieval-augmented generation (RAG) combines data retrieval with LLM-based generation, producing output based on the context from its**retrieved chunk**.
In our previous article, we discussed how to evaluate our RAG system to make it more trustworthy. However, we can still improve its performance by managing the chunking strategy.
## [Explainable RAG for More Trustworthy System](https://www.nb-data.com/p/explainable-rag-for-more-trustworthy)
[Cornellius Yudha Wijaya](https://substack.com/profile/6000855-cornellius-yudha-wijaya)
·
14. Februar 2025
All the code used here is present in the RAG-To-Know repository.
When we talk about chunks, we refer to the _**segmented portion of text from a larger document or dataset split with certain rules and strategies that will be indexed for the RAG knowledge base**_. For example, a simple split below results in two different chunks.
Chunk is effectively used as a manageable embedding, indexing, and retrieval unit. The "retrieval unit" finds relevant context for a given query. Rather than passing all the documents into the generative model, passing the most pertinent passage is much more efficient.
Many chunking strategies are available, each offering advantages and disadvantages. 
In this article, we will explore nine different chunking strategies and how to implement them. Here is an infographic summarizing our discussion.
Curious about it? Let’s get into it!
Non-Brand Data is a reader-supported publication. To receive new posts and support my work, consider becoming a free or paid subscriber.
# **Introduction to Chunking**
As mentioned above, chunking is breaking down large documents into manageable units. We try to extract and restructure the document into multiple parts that the RAG system will retrieve according to the query input.
Remember, RAG functions by embedding a query during inference and retrieving the top-_k_ most relevant chunks from the database. These chunks serve as context for the generative model to generate a grounded and pertinent response.
**Chunks can range from sentences to paragraphs or sections, depending on the use case and the splitting rule**. These rules are what we called the chunking strategy.
There are many strategies for performing chunking, each with advantages and disadvantages. Let’s explore each strategy.
## **1. Fixed-Size Chunking**
**Fixed-size chunking is a strategy for dividing text into segments of uniform length,** such as by word count, token count, or character count. For example, the document might be split into chunks of 200 words each. 
This method relies on straightforward text division, making it easy to implement. It is often used when consistent input size is critical, such as feeding data into machine learning models with fixed input dimensions.
**Advantages:**
  * **Simplicity and Speed:** Requires minimal computational resources or linguistic analysis, allowing fast implementation.
  * **Predictability:** Produces uniform chunk sizes, simplifying storage, indexing, and retrieval in databases.


**Disadvantages:**
  * **Context Fragmentation:** Often splits sentences or paragraphs that will disrupt semantic meaning.
  * **Rigidity:** Fails to adapt to the natural flow of text, potentially isolating related concepts into separate chunks.


[Content truncated...]