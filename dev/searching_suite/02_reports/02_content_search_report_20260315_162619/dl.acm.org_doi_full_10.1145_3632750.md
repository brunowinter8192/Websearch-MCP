# Exploring Dense Retrieval for Dialogue Response Selection
**URL:** https://dl.acm.org/doi/full/10.1145/3632750
**Domain:** dl.acm.org
**Score:** 2.9
**Source:** scraped
**Query:** ColBERT vs dense retrieval benchmark recall comparison

---

[skip to main content](https://dl.acm.org/doi/full/10.1145/3632750#skip-to-main-content)
## ACM is now Open Access
As part of the Digital Library's transition to [Open Access](https://dl.acm.org/action/clickThrough?id=108180&url=%2Fopenaccess&loc=%2Fdoi%2Ffull%2F10.1145%2F3632750&pubId=60359303&placeholderId=101025&productId=108179 "Follow link to the ACM DL Open Access information page"), new features for researchers are available in the _Premium Edition_. [Click here to learn more](https://dl.acm.org/action/clickThrough?id=108180&url=%2Fpremium&loc=%2Fdoi%2Ffull%2F10.1145%2F3632750&pubId=60359303&placeholderId=101025&productId=108179 "More information about Premium Edition").
**You are currently in the Basic Edition. Features requiring a subscription appear in grey.**
## Export Citations
Several features on this page require Premium Access.
Contents
  * Information & Contributors
  * Bibliometrics & Citations


## Abstract
### Abstract
Recent progress in deep learning has continuously improved the accuracy of dialogue response selection. However, in real-world scenarios, the high computation cost forces existing dialogue response selection models to rank only a small number of candidates, recalled by a coarse-grained model, precluding many high-quality candidates. To overcome this problem, we present a novel and efficient response selection model and a set of tailor-designed learning strategies to train it effectively. The proposed model consists of a dense retrieval module and an interaction layer, which could directly select the proper response from a large corpus. We conduct re-rank and full-rank evaluations on widely used benchmarks to evaluate our proposed model. Extensive experimental results demonstrate that our proposed model notably outperforms the state-of-the-art baselines on both re-rank and full-rank evaluations. Moreover, human evaluation results show that the response quality could be improved further by enlarging the candidate pool with nonparallel corpora. In addition, we also release high-quality benchmarks that are carefully annotated for more accurate dialogue response selection evaluation. All source codes, datasets, model parameters, and other related resources have been publicly available. 
### AI Summary
### AI-Generated Summary (Experimental)
This summary was generated using automated tools and was not authored or reviewed by the article's author(s). It is provided to support discovery, help readers assess relevance, and assist readers from adjacent research areas in understanding the work. It is intended to complement the author-supplied abstract, which remains the primary summary of the paper. The full article remains the authoritative version of record. [Click here to learn more](https://dl.acm.org/generative-ai/summarizations "Learn more about ACM AI summaries").
Click here to comment on the accuracy, clarity, and usefulness of this summary. Doing so will help inform refinements and future regenerated versions.
To view this AI-generated plain language summary, you must have Premium access.
## 1 Introduction
Recently, dialogue response selection has attracted increasing attention. The task is to select proper responses given a multi-turn dialogue history and a set of response candidates. So far, most researchers employ the coarse-to-fine recall-then-rerank framework for the dialogue response selection task, which consists of two kinds of models [[4](https://dl.acm.org/doi/full/10.1145/3632750#Bib0004), [8](https://dl.acm.org/doi/full/10.1145/3632750#Bib0008)]: the fast recall model and the cross-encoder rerank model. The fast recall model is used to compute the similarities between the multi-turn conversation context and the candidate in a coarse-grained way. It can select a small number of the candidate set with higher similarity with context very fast. For example, the bag-of-words retrieval function (e.g., BM25 and docT5query [[5](https://dl.acm.org/doi/full/10.1145/3632750#Bib0005), [38](https

[Content truncated...]