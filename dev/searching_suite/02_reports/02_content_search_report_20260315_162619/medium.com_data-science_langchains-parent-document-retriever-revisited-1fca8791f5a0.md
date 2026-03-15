# LangChain's Parent Document Retriever — Revisited - Medium
**URL:** https://medium.com/data-science/langchains-parent-document-retriever-revisited-1fca8791f5a0
**Domain:** medium.com
**Score:** 36.0
**Source:** scraped
**Query:** sentence window retrieval vs parent document retrieval

---

[Sitemap](https://medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
Follow publication
An archive of data science, data analytics, data engineering, machine learning, and artificial intelligence writing from the former Towards Data Science Medium publication.
Follow publication
# LangChain’s Parent Document Retriever — Revisited
## Enhance retrieval with context using your vector database only
Follow
6 min read Jul 22, 2024
Share
**TL;DR** — We achieve the same functionality as LangChains’ Parent Document Retriever ([link](https://python.langchain.com/v0.1/docs/modules/data_connection/retrievers/parent_document_retriever/)) by utilizing metadata queries. You can explore the code [here](https://gist.github.com/omriel1/7243ce233eb2986ed2749de6ae79ecb7).
## Introduction to RAG
Retrieval-augmented generation (RAG) is currently one of the hottest topics in the world of LLM and AI applications.
In short, RAG is a technique for grounding a generative models’ response on chosen knowledge sources. It comprises two phases: retrieval and generation.
  1. In the retrieval phase, given a user’s query, we retrieve pieces of relevant information from a predefined knowledge source.
  2. Then, we insert the retrieved information into the prompt that is sent to an LLM, which (ideally) generates an answer to the user’s question based on the provided context.


A commonly used approach to achieve efficient and accurate retrieval is through the usage of embeddings. In this approach, we preprocess users’ data (let’s assume plain text for simplicity) by splitting the documents into chunks (such as pages, paragraphs, or sentences). We then use an embedding model to create a meaningful, numerical representation of these chunks, and store them in a vector database. Now, when a query comes in, we embed it as well and perform a similarity search using the vector database to retrieve the relevant information
Press enter or click to view image in full size
Image by the author
If you are completely new to this concept, I’d recommend [deeplearning.ai](https://www.deeplearning.ai/) great course, [LangChain: Chat with Your Data](https://www.deeplearning.ai/short-courses/langchain-chat-with-your-data/).
## What is “Parent Document Retrieval”?
“Parent Document Retrieval” or “Sentence Window Retrieval” as referred by others, is a common approach to enhance the performance of retrieval methods in RAG by providing the LLM with a broader context to consider.
In essence, we divide the original documents into relatively small chunks, embed each one, and store them in a vector database. Using such small chunks (a sentence or a couple of sentences) helps the embedding models to better reflect their meaning [1].
Then, **at retrieval time, we do not return the most similar chunk as found by the vector database only, but also its surrounding context**(chunks)**in the original document**. That way, the LLM will have a broader context, which, in many cases, helps generate better answers.
LangChain supports this concept via Parent Document Retriever [2]. The Parent Document Retriever allows you to: (1) retrieve the full document a specific chunk originated from, or (2) pre-define a larger “parent” chunk, for each smaller chunk associated with that parent.
Let’s explore the example from [LangChains’ docs](https://python.langchain.com/v0.1/docs/modules/data_connection/retrievers/parent_document_retriever/):
```
# This text splitter is used to create the parent documentsparent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)# This text splitter is used to create the child documents# It should create documents smaller than the parentchild_splitter = RecursiveCharacterTextSplitter(chunk_size=400)# The vectorstore to use to index the child chunksvectorstore = Chroma(    collec

[Content truncated...]