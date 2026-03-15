# ColBERT: Contextualized Late Interaction BERT explained with a tutorial
**URL:** https://athekunal.medium.com/colbert-contextualized-late-interaction-bert-explained-with-a-tutorial-2ae72a7aa055
**Domain:** athekunal.medium.com
**Score:** 12.0
**Source:** scraped
**Query:** ColBERT late interaction retrieval implementation

---

[Sitemap](https://athekunal.medium.com/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
# ColBERT: Contextualized Late Interaction BERT explained with a tutorial
Follow
30 min read Mar 9, 2024
Share
In this article, we will go over the Colbert architecture, both [v1](https://arxiv.org/abs/2004.12832) and [v2](https://arxiv.org/abs/2112.01488). It is a neural Information Retrieval technique that can help us build RAG applications with LLMs. I will show you a tutorial on how you can build an end-to-end RAG system with data on SEC Filings and earnings call
Let’s start with the ColBERT architecture
Tutorial Link
## [Google Colaboratory Colbert Tutorial colab.research.google.com ](https://colab.research.google.com/drive/1lsT9j6TqayIRilAOlBDZxDlxK1lc8Ksi?usp=sharing&source=post_page-----2ae72a7aa055---------------------------------------)
## ColBERT v1
  * An information retriever fetches semantically similar passages from our dataset. The Colbert architecture is a neural IR technique which does late-stage interaction between each query token and each token in a passage in the dataset.


Press enter or click to view image in full size
  * In architecture (a), we have a BERT-based encoder and the query and a document (it is the same as the passage mentioned above) make one forward pass each, and the final output is sent into a similarity function like cosine similarity to measure the similarity, and we can select the top-k documents that are the most similar. **However, here we need to compress the representation of the entire query and document into a single vector, which lacks expressivity. Also, there is very limited query-document interaction, as the interaction only occurs after the dimensionality has been compressed into a single vector.**
  * In architecture (b), we have a query document interaction by a similarity function at the token level, and it is a very sparse matrix that goes into a downstream neural model to predict the similarity
  * It bears some semblance to another SOTA neural IR called SPLADEv2. **Here instead of having a sparse matrix between query and document, we have a sparse matrix between the query and entire vocabulary, and the document and entire vocabulary. After that, they are combined to compute the similarity.**


Press enter or click to view image in full size
Taken from this YouTube [video](https://youtu.be/EDVqG86AT0Q?si=SgSlzLWuJRMRj7JS&t=1019) by Chris Potts
  * In architecture (c), here we concatenate the query and document into a single document for a forward pass, initialize with a task prediction special token, and initialize special tokens for the query and document.


### **[SIM] + [Q] + Query text + [D] Document text**
  * Here the [SIM] special token will instruct the model to predict the similarity score, [Q] is for the start of the Query texts and [D] is for the start of the document texts. Now we send this concatenated text after tokenization to a BERT-base encoder to output the similarity score after one forward pass. The model has been trained by showing it positive examples of query and its relevant document and the objective is to predict 1, and the query with its non-relevant document (negative hard mining objective) to predict -1. However, it is a very expensive operation as for each document in our dataset we need to do a forward pass to get the similarity score, hence this does not scale well.
  * The architecture (d) is the colbert architecture of late-stage interaction. It addresses the shortcomings of low expressivity of single vector representations by having a representation at the token level and it does query-document interaction without doing an expensive forward pass each time with every new query.
  * I found another diagram that better explains Colbert. Below you can see that Colbe

[Content truncated...]