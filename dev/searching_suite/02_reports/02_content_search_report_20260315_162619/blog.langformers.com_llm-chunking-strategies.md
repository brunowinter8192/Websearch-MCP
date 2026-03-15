# Fixed-size, Semantic and Recursive Chunking Strategies for LLMs
**URL:** https://blog.langformers.com/llm-chunking-strategies/
**Domain:** blog.langformers.com
**Score:** 30.0
**Source:** scraped
**Query:** recursive chunking vs semantic chunking comparison

---

🚀 Build chatbots, embeddings, semantic search & more with one simple API — free & open-source — [__try Langformers in minutes →__](https://langformers.com/)
In modern Retrieval-Augmented Generation (RAG) systems, handling large documents efficiently is critical. Embedding models have token limits that, when exceeded, can lead to incomplete processing or errors. This is where **chunking** becomes critical. By breaking large documents into smaller, manageable pieces, chunking ensures that information remains accessible, relevant, and optimized for retrieval and processing.
In this blog post, we will dive deep into chunking techniques with **Langformers** , exploring all three **Fixed-size, Semantic and Recursive chunking** strategies — complete with practical examples.
## What is Chunking?
**Chunking** is the process of splitting a large document into smaller units called _chunks_. Each chunk is small enough to fit within the token limits of the chosen embedding model, yet sufficient enough to retain meaningful information.
The ultimate goal of chunking is to improve:
  * **Retrieval accuracy** — relevant chunks are retrieved instead of entire documents.
  * **Processing efficiency** — smaller inputs lead to faster model inference. LLMs have token generation limits; feeding a whole text document, such as a book, is not feasible.


Across all chunking strategies in Langformers, **tokenization** plays a central role. The chunk size is defined in terms of **tokens** (not words), and the number of tokens can vary based on the tokenizer used.
## Chunking Strategies in Langformers
As of writing this post, Langformers provides three main chunking strategies:
  1. **Fixed-size Chunking**(also with overlapping)
  2. **Semantic Chunking**
  3. **Recursive Chunking**


Let's explore each in detail.
## Fixed-size Chunking
Fixed-size chunking is the simplest method: documents are split into chunks of a specified number of tokens. It’s fast, predictable, and works well for content where structure is less important.
### Key Features
  * Divides text based purely on token count.
  * Optional **overlapping** between chunks for better context preservation.


Let's see how we can implement this chunking strategy with Langformers.
First, make sure you have Langformers installed in your environment. If not, install it using pip:
```
pip install -U langformers
```

### Fixed-size Chunking Example
```
# Import Langformers
from langformers import tasks

# Create a fixed-size chunker
chunker = tasks.create_chunker(strategy="fixed_size", tokenizer="sentence-transformers/all-mpnet-base-v2")

# Chunk a document
chunks = chunker.chunk(
    document="This is a test document. It contains several sentences. We will chunk it into smaller pieces.",
    chunk_size=8
)

```

In this example:
  * We use the `sentence-transformers/all-mpnet-base-v2` tokenizer.
  * Each chunk contains approximately 8 tokens.
  * Overlapping chunks can be created by specifying the `overlap` parameter.


## Semantic Chunking
Semantic chunking goes a step further by considering the _meaning_ of the content. It first creates small initial chunks, then merges them based on **semantic similarity**. This leads to more contextually meaningful chunks.
Semantic chunking is ideal for:
  * Technical documents
  * Research papers
  * Legal texts
  * Any domain where preserving semantic integrity is crucial


### How Semantic Chunking Works
  1. Initially, the document is split into small chunks based on a token limit.
  2. The chunks are then grouped together based on their semantic similarity, controlled by a **similarity threshold**.


### Semantic Chunking Example
```
# Import Langformers
from langformers import tasks

# Create a semantic chunker
chunker = tasks.create_chunker(strategy="semantic", model_name="sentence-transformers/all-mpnet-base-v2")

[Content truncated...]