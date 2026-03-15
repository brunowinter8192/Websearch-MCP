# Advanced RAG — Improving retrieval using Hypothetical Document ...
**URL:** https://medium.aiplanet.com/advanced-rag-improving-retrieval-using-hypothetical-document-embeddings-hyde-1421a8ec075a
**Domain:** medium.aiplanet.com
**Score:** 1.2
**Source:** scraped
**Query:** HyDE hypothetical document embeddings implementation

---

[Sitemap](https://medium.aiplanet.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
Follow publication
Ecosystem educating and building AI for All
Follow publication
# Advanced RAG — Improving retrieval using Hypothetical Document Embeddings(HyDE)
Follow
140 min read Nov 4, 2023
Share
Press enter or click to view image in full size
Any Source
## What is HyDE ?
**HyDE** uses a Language Learning Model, like ChatGPT, to create a theoretical document when responding to a query, as opposed to using the query and its computed vector to directly seek in the vector database.
It goes a step further by using an unsupervised encoder learned through contrastive methods. This encoder changes the theoretical document into an embedding vector to locate similar documents in a vector database.
Rather than seeking embedding similarity for questions or queries, it focuses on answer-to-answer embedding similarity.
Its performance is robust, matching well-tuned retrievers in various tasks such as web search, QA, and fact verification.
It is inspired by the paper [Precise Zero-Shot Dense Retrieval without Relevance Labels](https://paperswithcode.com/paper/precise-zero-shot-dense-retrieval-without)
## Why we need LLM to generate a hypothetical answer ?
Occasionally, when faced with a question that lacks specificity or lacks easily identifiable elements to derive an answer from a given context, it can be quite challenging.
For instance, considering the case of the Pizza Hut franchise, it’s commonly known for selling food. However, if someone were to inquire about Pizza Hut’s best item, the question implies a focus on food. The difficulty here lies in the absence of a specified food item. Therefore, searching for insights becomes problematic. To address this, we employ the assistance of LLM (Language Model) to craft a hypothetical answer, which is then transformed into embeddings. These embeddings are then examined within a vector store based on semantic similarity, aiding in the search for relevant information.
Any Source
HyDE creates a “Hypothetical” answer with the help of LLM (GPT3) and then searches the embeddings for a match. Here we are doing answer to answer embedding similarity search as compared to query to answer embedding similar search in traditional RAG retrieval approach.
## Get Plaban Nayak’s stories in your inbox
Join Medium for free to get updates from this writer.
Subscribe
Subscribe
Remember me for faster sign in
However, there’s a drawback to this approach as it may not consistently produce good results. For instance, if the subject being discussed is entirely unfamiliar to the language model, this method is not effective and could lead to increased instances of generating incorrect information.
## Implementation Steps with code
### Install required dependencies
```
!pip -q install langchain huggingface_hub openai chromadb tiktoken faiss-cpu!pip -q install sentence_transformers!pip -q install -U FlagEmbedding!pip -q install -U cohere!pip -q install -U pypdf
```

### Import installed dependencies
```
from langchain.llms import OpenAIfrom langchain.embeddings import OpenAIEmbeddingsfrom langchain.text_splitter import RecursiveCharacterTextSplitterfrom langchain.chains import LLMChain, HypotheticalDocumentEmbedderfrom langchain.prompts import PromptTemplatefrom langchain.vectorstores import FAISSfrom langchain.document_loaders.pdf import PyPDFDirectoryLoaderfrom langchain.document_loaders import TextLoaderfrom langchain.embeddings import HuggingFaceBgeEmbeddingsfrom langchain.chains import RetrievalQAfrom langchain.chat_models import ChatOpenAIimport langchain
```

### Set the required API keys
```
from getpass import getpassos.environ["COHERE_API_KEY"] = getpass("Cohere API Key:")os.environ["OPENAI_API_KEY"] = getpass("OpenAI API Key:") 
```

[Content truncated...]