# Chunking Strategies for RAG: Fixed, Recursive, Semantic, Language-Based ...
**URL:** https://matheusjerico.medium.com/chunking-strategies-for-rag-fixed-recursive-semantic-language-based-and-context-aware-4ab476aea7d1
**Domain:** matheusjerico.medium.com
**Score:** 12.4
**Source:** scraped
**Query:** recursive chunking vs semantic chunking comparison

---

[Sitemap](https://matheusjerico.medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
# Chunking Strategies for RAG: Fixed, Recursive, Semantic, Language-Based, and Context-Aware Approaches
Follow
5 min read Sep 5, 2025
Share
Press enter or click to view image in full size
Retrieval-Augmented Generation (RAG) pipelines rely on **chunking** — splitting documents into smaller units before embedding them into a vector database. While embeddings and vector search are often the focus, **how you chunk your data has a profound effect** on retrieval quality, efficiency, and ultimately the usefulness of your RAG system.
In this post, we’ll explore the main chunking strategies used in production RAG systems:
  * Fixed-size chunking
  * Recursive character splitting
  * Semantic chunking
  * Language-based chunking
  * Context-aware chunking


We’ll look at **how each works, when to use them, pros and cons, Python examples, and diagrams** to help visualize the approaches. Finally, we’ll evaluate emerging techniques beyond these five, and wrap up with best practices.
## Why Chunking Matters in RAG
When we embed raw text, embeddings models (for example, OpenAI’s `text-embedding-3-large`, Cohere, or Sentence Transformers) have **token limits**. Feeding entire documents usually isn’t possible, or even desirable.
Instead, we split documents into **chunks** , embed them, and later use vector search to retrieve only the most relevant pieces.
The **chunking strategy directly affects retrieval** :
  * Too small: fragments lack context, leading to irrelevant answers.
  * Too large: context gets diluted, increasing token cost and retrieval noise.
  * Poor boundaries: semantic meaning gets cut mid-sentence, confusing embeddings.


## 1. Fixed-Size Chunking
**Definition** : Split text into equal-sized segments (for example, 500 characters or 256 tokens), regardless of semantics.
```
def fixed_size_chunking(text: str, size: int = 500, overlap: int = 50) -> list[str]:    """    Splits text into fixed-size chunks with optional overlap.        Args:        text: The input string.        size: The maximum size of each chunk.        overlap: Overlap between consecutive chunks.            Returns:        A list of text chunks.    """    chunks = []    for i in range(0, len(text), size - overlap):        chunks.append(text[i:i+size])    return chunks
```

**Pros**
  * Simple and fast.
  * Good for uniform documents (logs, code).


**Cons**
  * Cuts through sentences
  * Ignores semantics.


**When to Use**
  * Structured/uniform text (system logs, code, JSON).
  * When speed is more important than semantic precision.


**Diagra**
Press enter or click to view image in full size
## 2. Recursive Character Splitting
**Definition** : Split text hierarchically, first by paragraphs, then by sentences, then by characters, until chunks fit within a size limit.
## Get Matheus Jericó’s stories in your inbox
Join Medium for free to get updates from this writer.
Subscribe
Subscribe
Remember me for faster sign in
Example using LangChain framework:
```
from langchain.text_splitter import RecursiveCharacterTextSplittertext_splitter = RecursiveCharacterTextSplitter(    chunk_size=500,    chunk_overlap=50,    separators=["\n\n", "\n", ". ", " ", ""])chunks = text_splitter.split_text("Your long document here...")
```

**Pros**
  * Preserves natural boundaries better than fixed-size.
  * Widely used in practice.


**Cons**
  * Still somewhat arbitrary.
  * Performance overhead for very large docs.


**When to Use**
  * General-purpose RAG pipelines.
  * Best baseline strategy for mixed documents.


[Content truncated...]