# Contextualized Chunk Embeddings - Introduction - Voyage AI
**URL:** https://docs.voyageai.com/docs/contextualized-chunk-embeddings
**Domain:** docs.voyageai.com
**Score:** 3.5
**Source:** scraped
**Query:** contextual chunking prepend context before embedding

---

# 
Model Choices
Voyage currently provides the following contextualized chunk embedding models:
Model | Context Length (tokens) | Embedding Dimension | Description  
---|---|---|---  
`voyage-context-3` | 32,000 | 1024 (default), 256, 512, 2048 | Contextualized chunk embeddings optimized for general-purpose and multilingual retrieval quality. See [blog post](https://blog.voyageai.com/2025/07/23/voyage-context-3/) for details.  
# 
Python API
Voyage contextualized chunk embeddings are accessible in Python through the `voyageai` [package](https://docs.voyageai.com/docs/api-key-and-installation#install-voyage-python-package). Please install the `voyageai` package, [set up](https://docs.voyageai.com/docs/api-key-and-installation) the API key, and use the `voyageai.Client.contextualized_embed()` function to vectorize your inputs.
>
**Parameters**
  * **inputs** (List[List[str]]) - A list of lists, where each inner list contains a query, a document, or document chunks to be vectorized. 
    * Each inner list in `inputs` represents a set of text elements that will be embedded together. Each element in the list is encoded not just independently, but also encodes context from the other elements in the same list. `inputs = [["text_1_1", "text_1_2", ..., "text_1_n"], ["text_2_1", "text_2_2", ..., "text_2_m"]]`
    * **Document Chunks**. Most commonly, each inner list contains chunks from a single document, ordered by their position in the document. In this case: `inputs = [["doc_1_chunk_1", "doc_1_chunk_2", ..., "doc_1_chunk_n"], ["doc_2_chunk_1", "doc_2_chunk_2", ..., "doc_2_chunk_m"]]` Each chunk is encoded in context with the others from the same document, resulting in more context-aware embeddings. **We recommend that supplied chunks _not_ have any overlap**.
    * **Context-Agnostic Behavior for Queries and Documents**. If there is one element per inner list, each text is embedded independently—similar to standard (context-agnostic) embeddings: `inputs = [["query_1"], ["query_2"], ..., ["query_k"]]` `inputs = [["doc_1"], ["doc_2"], ..., ["doc_k"]]` Therefore, if the inputs are queries, each inner list should contain a single query (i.e., a length of one), as shown above, and the `input_type` should be set to `query`.
    * The following constraints apply to the `inputs` list: 
      * The list must not contain more than 1,000 inputs.
      * The total number of tokens across all inputs must not exceed 120K.
      * The total number of chunks across all inputs must not exceed 16K.
  * **model** (str) - Name of the model. Recommended options: `voyage-context-3`.
  * **input_type** (str, optional, defaults to `None`) - Type of the input text. Options: `None`, `query`, `document`. 
    * When `input_type` is `None` , the embedding model directly converts the inputs into numerical vectors. For retrieval/search purposes, where a "query" is used to search for relevant information among a collection of data, referred to as "documents", we recommend specifying whether your inputs are intended as queries or documents by setting `input_type` to `query` or `document` , respectively. In these cases, Voyage automatically prepends a prompt to your inputs before vectorizing them, creating vectors more tailored for retrieval/search tasks. Embeddings generated with and without the `input_type` argument are compatible.
    * For transparency, the following prompts are prepended to your input. 
      * For query, the prompt is "_Represent the query for retrieving supporting documents: _".
      * For document, the prompt is "_Represent the document for retrieval: _".
  * **output_dimension** (int, optional, defaults to `None`) - The number of dimensions for resulting output embeddings. `voyage-context-3` supports the following `output_dimension` values: 2048, 1024 (default), 512, and 256.
  * **output_dtype** (str, optional, defaults to `float`) - The data type for the embeddings to be returned. Options: `float`, `int8`, `uint8`, `binary`, `ubinary`. P

[Content truncated...]