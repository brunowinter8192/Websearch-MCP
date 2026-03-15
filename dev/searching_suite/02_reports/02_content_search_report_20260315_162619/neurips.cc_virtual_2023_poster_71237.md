# Rethinking the Role of Token Retrieval in Multi-Vector Retrieval
**URL:** https://neurips.cc/virtual/2023/poster/71237
**Domain:** neurips.cc
**Score:** 6.7
**Source:** scraped
**Query:** ColBERT vs dense retrieval benchmark recall comparison

---

Poster
# Rethinking the Role of Token Retrieval in Multi-Vector Retrieval
Jinhyuk Lee · Zhuyun Dai · Sai Meher Karthik Duddu · Tao Lei · Iftekhar Naim · Ming-Wei Chang · Vincent Zhao 
2023 Poster
[[ Paper](https://proceedings.neurips.cc/paper_files/paper/2023/hash/31d997278ee9069d6721bc194174bb4c-Abstract-Conference.html "Paper")]  [[ Slides](https://neurips.cc/media/neurips-2023/Slides/71237_AYHERu1.pdf "Slides")]  [[ Poster](https://neurips.cc/media/PosterPDFs/NeurIPS%202023/71237.png?t=1701734071.462841 "Poster")]  [[ OpenReview](https://openreview.net/forum?id=ZQzm0Z47jz "OpenReview")] 
###  Abstract 
Multi-vector retrieval models such as ColBERT [Khattab et al., 2020] allow token-level interactions between queries and documents, and hence achieve state of the art on many information retrieval benchmarks. However, their non-linear scoring function cannot be scaled to millions of documents, necessitating a three-stage process for inference: retrieving initial candidates via token retrieval, accessing all token vectors, and scoring the initial candidate documents. The non-linear scoring function is applied over all token vectors of each candidate document, making the inference process complicated and slow. In this paper, we aim to simplify the multi-vector retrieval by rethinking the role of token retrieval. We present XTR, ConteXtualized Token Retriever, which introduces a simple, yet novel, objective function that encourages the model to retrieve the most important document tokens first. The improvement to token retrieval allows XTR to rank candidates only using the retrieved tokens rather than all tokens in the document, and enables a newly designed scoring stage that is two-to-three orders of magnitude cheaper than that of ColBERT. On the popular BEIR benchmark, XTR advances the state-of-the-art by 2.8 nDCG@10 without any distillation. Detailed analysis confirms our decision to revisit the token retrieval stage, as XTR demonstrates much better recall of the token retrieval stage compared to ColBERT.
Show more
###  Video 
Chat is not available.
Successful Page Load
