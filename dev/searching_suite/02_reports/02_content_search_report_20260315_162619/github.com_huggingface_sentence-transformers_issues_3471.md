# ColBERT-style token-level retrieval vs sentence embeddings for modern ...
**URL:** https://github.com/huggingface/sentence-transformers/issues/3471
**Domain:** github.com
**Score:** 16.0
**Source:** scraped
**Query:** ColBERT vs dense retrieval benchmark recall comparison

---

[Skip to content](https://github.com/huggingface/sentence-transformers/issues/3471#start-of-content)
You signed in with another tab or window. [Reload](https://github.com/huggingface/sentence-transformers/issues/3471) to refresh your session. You signed out in another tab or window. [Reload](https://github.com/huggingface/sentence-transformers/issues/3471) to refresh your session. You switched accounts on another tab or window. [Reload](https://github.com/huggingface/sentence-transformers/issues/3471) to refresh your session. Dismiss alert
/ **[sentence-transformers](https://github.com/huggingface/sentence-transformers) ** Public
  * You must be signed in to change notification settings
  * [ Star  18.4k ](https://github.com/login?return_to=%2Fhuggingface%2Fsentence-transformers)


#  ColBERT-style token-level retrieval vs sentence embeddings for modern RAG tasks (esp. multimodal like ColPali) #3471
Copy link
Copy link
[ColBERT-style token-level retrieval vs sentence embeddings for modern RAG tasks (esp. multimodal like ColPali)](https://github.com/huggingface/sentence-transformers/issues/3471#top)#3471
Copy link
## Description
opened [on Jul 28, 2025](https://github.com/huggingface/sentence-transformers/issues/3471#issue-3268499670)
Contributor
Issue body actions
Hi all,
Thank you for your amazing work on `sentence-transformers` — it's been extremely helpful in my research on retrieval-augmented generation (RAG). Recently, I’ve been working on RAG systems where the knowledge base consists of PDF documents that include not just text, but also tables and images. So far, I’ve been relying purely on text and using sentence embedding (Qwen3-embedding, etc.) models for retrieval.
This led me to explore ColPali, which integrates ColBERT with a multimodal encoder and shows strong performance on such complex inputs. Naturally, I went back to study ColBERT itself to understand the retrieval component more deeply.
From what I’ve understood so far (please correct me if I’m wrong):
  * ColBERT computes **token-level contextualized embeddings** , i.e., the hidden states **before any pooling (e.g., [CLS], <eos>, avg, max)** is applied.
  * Retrieval is done via **Late Interaction** , using a MaxSim function between each query token and document tokens.
  * The ColBERT paper mentions that the model needs to be **fine-tuned** for better late interaction performance, e.g., on MS MARCO or similar retrieval data.


On the other hand, modern sentence embedding models are pre-finetuned and can often be used off-the-shelf, which makes them very convenient and fast to deploy in production.
That brings me to my main questions:
  1. **Is my understanding of ColBERT’s architecture and difference from sentence embeddings accurate?**
  2. **Why do ColBERT(-style) models seem less represented in benchmarks like MTEB?**
     * MTEB seems to primarily evaluate sentence-level models. Is that because interaction-based models like ColBERT are fundamentally incompatible with MTEB’s architecture or evaluation protocol?
     * Are there other public benchmarks that evaluate token-level or late-interaction retrievers like ColBERT in a standardized way?
  3. **In 2025, do ColBERT-style models still offer meaningful advantages in RAG or IR tasks?**
     * Or have sentence embedding models become so powerful that, in most use cases, they are the default — even without additional fine-tuning?


Additionally, I have a follow-up related to **ColPali** :
From what I’ve gathered, ColPali appears to use paligemma (and specifically SigLIP) as its vision-language encoder, which is then integrated with the ColBERT retrieval head. Given that, I’m also wondering:
  * Now that models like Gemma 3 combine a vision tower with an LLM, is it possible to use them for retrieval-augmented tasks in a plug-and-play way?
  * Outside of ColPali and ColQwen, are there any other open-source efforts where vision-language models have been explicitly fine-tuned for multimodal RAG?


[Content truncated...]