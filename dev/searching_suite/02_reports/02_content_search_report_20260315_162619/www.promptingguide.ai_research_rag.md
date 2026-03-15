# Retrieval Augmented Generation (RAG) for LLMs
**URL:** https://www.promptingguide.ai/research/rag
**Domain:** www.promptingguide.ai
**Score:** 2.4
**Source:** scraped
**Query:** LLM generated context prefix per chunk retrieval

---

🚀 Learn to build apps with Claude Code! Use **PROMPTING** for 20% off [Enroll now →](https://academy.dair.ai/courses/build-apps-with-claude-code)
[LLM Research Findings](https://www.promptingguide.ai/research)
RAG for LLMs
# Retrieval Augmented Generation (RAG) for LLMs
There are many challenges when working with LLMs such as domain knowledge gaps, factuality issues, and hallucination. Retrieval Augmented Generation (RAG) provides a solution to mitigate some of these issues by augmenting LLMs with external knowledge such as databases. RAG is particularly useful in knowledge-intensive scenarios or domain-specific applications that require knowledge that's continually updating. A key advantage of RAG over other approaches is that the LLM doesn't need to be retrained for task-specific applications. RAG has been popularized recently with its application in conversational agents.
In this summary, we highlight the main findings and practical insights from the recent survey titled [Retrieval-Augmented Generation for Large Language Models: A Survey (opens in a new tab)](https://arxiv.org/abs/2312.10997) (Gao et al., 2023). In particular, we focus on the existing approaches, state-of-the-art RAG, evaluation, applications and technologies surrounding the different components that make up a RAG system (retrieval, generation, and augmentation techniques).
## Introduction to RAG 
As better introduced [here (opens in a new tab)](https://www.promptingguide.ai/techniques/rag), RAG can be defined as:
> RAG takes input and retrieves a set of relevant/supporting documents given a source (e.g., Wikipedia). The documents are concatenated as context with the original input prompt and fed to the text generator which produces the final output. This makes RAG adaptive for situations where facts could evolve over time. This is very useful as LLMs's parametric knowledge is static. RAG allows language models to bypass retraining, enabling access to the latest information for generating reliable outputs via retrieval-based generation.
In short, the retrieved evidence obtained in RAG can serve as a way to enhance the accuracy, controllability, and relevancy of the LLM's response. This is why RAG can help reduce issues of hallucination or performance when addressing problems in a highly evolving environment.
While RAG has also involved the optimization of pre-training methods, current approaches have largely shifted to combining the strengths of RAG and powerful fine-tuned models like [ChatGPT (opens in a new tab)](https://www.promptingguide.ai/models/chatgpt) and [Mixtral (opens in a new tab)](https://www.promptingguide.ai/models/mixtral). The chart below shows the evolution of RAG-related research:
_[Figure Source (opens in a new tab)](https://arxiv.org/abs/2312.10997)_
Below is a typical RAG application workflow:
_[Figure Source (opens in a new tab)](https://arxiv.org/abs/2312.10997)_
We can explain the different steps/components as follows:
  * **Input:** The question to which the LLM system responds is referred to as the input. If no RAG is used, the LLM is directly used to respond to the question.
  * **Indexing:** If RAG is used, then a series of related documents are indexed by chunking them first, generating embeddings of the chunks, and indexing them into a vector store. At inference, the query is also embedded in a similar way.
  * **Retrieval:** The relevant documents are obtained by comparing the query against the indexed vectors, also denoted as "Relevant Documents".
  * **Generation:** The relevant documents are combined with the original prompt as additional context. The combined text and prompt are then passed to the model for response generation which is then prepared as the final output of the system to the user.


[Content truncated...]