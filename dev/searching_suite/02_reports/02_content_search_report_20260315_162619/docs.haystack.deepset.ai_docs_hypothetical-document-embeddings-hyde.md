# Hypothetical Document Embeddings (HyDE) - Haystack Documentation
**URL:** https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde
**Domain:** docs.haystack.deepset.ai
**Score:** 4.6
**Source:** scraped
**Query:** HyDE hypothetical document embeddings implementation

---

[Skip to main content](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#__docusaurus_skipToContent_fallback)
Version: 2.25
On this page
Copy
Enhance the retrieval in Haystack using HyDE method by generating a mock-up hypothetical document for an initial query.
## When Is It Helpful?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#when-is-it-helpful "Direct link to When Is It Helpful?")
The HyDE method is highly useful when:
  * The performance of the retrieval step in your pipeline is not good enough (for example, low Recall metric).
  * Your retrieval step has a query as input and returns documents from a larger document base.
  * Particularly worth a try if your data (documents or queries) come from a special domain that is very different from the typical datasets that Retrievers are trained on.


## How Does It Work?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#how-does-it-work "Direct link to How Does It Work?")
Many embedding retrievers generalize poorly to new, unseen domains. This approach tries to tackle this problem. Given a query, the Hypothetical Document Embeddings (HyDE) first zero-shot prompts an instruction-following language model to generate a “fake” hypothetical document that captures relevant textual patterns from the initial query - in practice, this is done five times. Then, it encodes each hypothetical document into an embedding vector and averages them. The resulting, single embedding can be used to identify a neighbourhood in the document embedding space from which similar actual documents are retrieved based on vector similarity. As with any other retriever, these retrieved documents can then be used downstream in a pipeline (for example, in a Generator for RAG). Refer to the paper “[Precise Zero-Shot Dense Retrieval without Relevance Labels](https://aclanthology.org/2023.acl-long.99/)” for more details.
## How To Build It in Haystack?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#how-to-build-it-in-haystack "Direct link to How To Build It in Haystack?")
First, prepare all the components that you would need:
python
```
import osfrom numpy import array, meanfrom typing import Listfrom haystack.components.generators.openai import OpenAIGeneratorfrom haystack.components.builders import PromptBuilderfrom haystack import component, Documentfrom haystack.components.converters import OutputAdapterfrom haystack.components.embedders import SentenceTransformersDocumentEmbedder## We need to ensure we have the OpenAI API key in our environment variablesos.environ["OPENAI_API_KEY"]="YOUR_OPENAI_KEY"## Initializing standard Haystack componentsgenerator = OpenAIGenerator(    model="gpt-3.5-turbo",    generation_kwargs={"n":5,"temperature":0.75,"max_tokens":400},prompt_builder = PromptBuilder(    template="""Given a question, generate a paragraph of text that answers the question.    Question: {{question}}    Paragraph:""",adapter = OutputAdapter(    template="{{answers | build_doc}}",    output_type=List[Document],    custom_filters={"build_doc":lambda data:[Document(content=d)forin data]},embedder = SentenceTransformersDocumentEmbedder(    model="sentence-transformers/all-MiniLM-L6-v2",embedder.warm_up()## Adding one custom component that returns one, "average" embedding from multiple (hypothetical) document embeddings@componentclassHypotheticalDocumentEmbedder:@component.output_types(hypothetical_embedding=List[float])defrun(self, documents: List[Document]):        stacked_embeddings = array([doc.embedding for doc in documents])        avg_embeddings = mean(stacked_embeddings, axis=0)        hyde_vector = avg_embeddings.reshape((1,len(avg_embeddings)))return{"hypothetical_embedding": hyde_vector[0].tolist()}
```

[Content truncated...]