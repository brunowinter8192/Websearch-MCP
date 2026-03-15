# Revisiting Chunking in the RAG Pipeline - AI Exploration Journey
**URL:** https://aiexpjourney.substack.com/p/revisiting-chunking-in-the-rag-pipeline
**Domain:** aiexpjourney.substack.com
**Score:** 2.1
**Source:** scraped
**Query:** LLM generated context prefix per chunk retrieval

---

# [AI Exploration Journey](https://aiexpjourney.substack.com/)
SubscribeSign in
# Revisiting Chunking in the RAG Pipeline
### Unveiling the Cutting-Edge Advances in Chunking
Sep 06, 2024
∙ Paid
Share
Chunking involves dividing a long text or document into smaller, logically coherent segments or “chunks.” Each chunk usually contains one or more sentences, with the segmentation based on the text’s structure or meaning. Once divided, each chunk can be processed independently or used in subsequent tasks, such as retrieval or generation.
The role of chunking in the mainstream RAG pipeline is shown in Figure 1.
Figure 1 : The role of the Chunking process(red box) in the mainstream RAG pipeline. Image by author.
[In the previous article](https://florianjune.substack.com/p/advanced-rag-05-exploring-semantic-chunking-97c12af20a4d), we explored various methods of semantic chunking, explaining their underlying principles and practical applications. These methods included:
  * Embedding-based methods: When the similarity between consecutive sentences drops below a certain threshold, a chunk boundary is introduced.
  * Model-based methods: Utilize deep learning models, such as BERT, to segment documents effectively.
  * LLM-based methods: Use LLMs to construct propositions, achieving more refined chunks.


However, since the previous article was published on February 28, 2024, there have been significant advancements in chunking over the past few months. **Therefore, this article presents** some of the latest developments in chunking within the RAG pipeline, focusing primarily on the following topics:
  * : A more dynamic and contextually aware chunking method.
  * **[Mix-of-Granularity(MoG)](https://arxiv.org/pdf/2406.00456v1)** : Optimizes the chunking granularity for RAG.
  * **[Prepare-then-Rewrite-then-Retrieve-then-Read(PR3)](https://arxiv.org/pdf/2408.09017v1)** : Enhances retrieval precision and contextual relevance by generating synthetic question-answer pairs (QA pairs) and Meta Knowledge (MK Summaries) Summaries.
  * **[Chunking-Free In-Context Retrieval(CFIC)](https://arxiv.org/pdf/2402.09760v1)** : Eliminates the chunking process by utilizing encoded hidden states of documents.


For each topic, additional thoughts and insights are offered.
## **LumberChunker**
#### **Key Idea**
LumberChunker’s key idea is to dynamically segment long-form texts into contextually coherent chunks using a large language model, optimizing information retrieval by dynamically segmenting text to maintain semantic coherence and relevance.
Figure 2: LumberChunker follows a three-step process. Source: [LumberChunker](https://arxiv.org/pdf/2406.17526v1).
Figure 2 illustrates the LumberChunker pipeline, where documents are first segmented paragraph-wise, then paragraphs are grouped together until a predefined token count is exceeded, and finally, a model like Gemini identifies significant content shifts, marking the boundaries for each chunk; this process is repeated cyclically for the entire document.
Here’s a streamlined breakdown of its workflow:
  1. **Paragraph-wise Segmentation** : The document is first divided into individual paragraphs, each assigned a unique ID. This initial step creates manageable units of text that serve as the foundation for further processing.
  2. **Grouping Paragraphs** : These paragraphs are then grouped sequentially into a group (referred to as `Gi`​) until the total token count exceeds a set threshold `θ`, which is optimally set around 550 tokens. This threshold is crucial for balancing the context provided to the model without overwhelming it.
  3. **Identifying Content Shifts:** The group `Gi`​ is analyzed by the LLM (e.g., Gemini 1.0-Pro), which identifies the precise point where the content shifts significantly. This point marks the boundary between the current chunk and the next.
  4. **Iterative Chunk Formation:** After identifying the content shift, the document is iteratively segmented, with each new group start

[Content truncated...]