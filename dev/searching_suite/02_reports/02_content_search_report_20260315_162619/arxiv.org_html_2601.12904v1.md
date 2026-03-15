# Accelerating LLM Inference in Retrieval-Augmented Generation
**URL:** https://arxiv.org/html/2601.12904v1
**Domain:** arxiv.org
**Score:** 2.0
**Source:** scraped
**Query:** LLM generated context prefix per chunk retrieval

---

[License: CC BY 4.0](https://info.arxiv.org/help/license/index.html#licenses-available)
arXiv:2601.12904v1 [cs.CL] 19 Jan 2026
\setcctype
by
Report issue for preceding element
# From Prefix Cache to Fusion RAG Cache: Accelerating LLM Inference in Retrieval-Augmented Generation
Report issue for preceding element
Jiahao Wang  202241050020@hdu.edu.cn Hangzhou Dianzi UniversityHangzhouChina Approaching.AIChina ,  Weiyu Xie  xwy21@mails.tsinghua.edu.cn Tsinghua UniversityBeijingChina ,  Mingxing Zhang  zhang_mingxing@mail.tsinghua.edu.cn Tsinghua UniversityBeijingChina ,  Boxing Zhang  zhangbx24@mails.tsinghua.edu.cn Tsinghua UniversityBeijingChina ,  Jianwei Dong  dongjw24@mails.tsinghua.edu.cn Tsinghua UniversityBeijingChina ,  Yuening Zhu  Tsinghua UniversityBeijingChina ,  Chen Lin  lin-c24@mails.tsinghua.edu.cn Tsinghua UniversityBeijingChina ,  Jinqi Tang  azure@approaching.ai Approaching.AIChina ,  Yaochen Han  ailililisi@approaching.ai Approaching.AIChina ,  Zhiyuan Ai  awake@approaching.ai Approaching.AIChina ,  Xianglin Chen  chenxl6436@outlook.com Approaching.AIChina ,  Yongwei Wu  wuyw@tsinghua.edu.cn Tsinghua UniversityBeijingChina and  Congfeng Jiang  Hangzhou Dianzi UniversityHangzhouChina
Report issue for preceding element
###### Abstract.
Report issue for preceding element
Retrieval-Augmented Generation enhances Large Language Models by integrating external knowledge, which reduces hallucinations but increases prompt length. This increase leads to higher computational costs and longer Time to First Token. To mitigate this issue, existing solutions aim to reuse the preprocessed KVCache of each retrieved chunk to accelerate RAG. However, the lack of cross-chunk contextual information leads to a significant drop in generation quality, leaving the potential benefits of KVCache reuse largely unfulfilled.
Report issue for preceding element
The challenge lies in how to reuse the precomputed KVCache chunk while preserving generation quality. We propose FusionRAG, a novel inference framework that optimizes both the preprocessing and reprocessing stages of RAG. In the offline preprocessing stage, we embed information from other related text chunks into each chunk, while in the online reprocessing stage, we recompute the KVCache for tokens that the model focuses on. As a result, we achieve a better trade-off between generation quality and efficiency. According to our experiments, FusionRAG significantly improves generation quality at the same recomputation ratio compared to previous state-of-the-art solutions. By recomputing fewer than 15% of the tokens, FusionRAG achieves up to 70% higher normalized-F1 scores than baselines and reduces TTFT by 2.66-9.39×\times compared to Full Attention.
Report issue for preceding element
Large Language Models; Retrieval-Augmented Generation; KVCache; Prefix Caching; Inference Acceleration; Cache Management 
††copyright: cc††journal: PACMMOD††journalyear: 2026††journalvolume: 4††journalnumber: 1 (SIGMOD)††article: 41††publicationmonth: 2††doi: 10.1145/3786655††ccs: Computing methodologies Natural language processing
##  1. Introduction
Report issue for preceding element
###  1.1. Motivation
Report issue for preceding element
Retrieval-Augmented Generation(RAG) (Lewis et al., [2020](https://arxiv.org/html/2601.12904v1#bib.bib4 "Retrieval-augmented generation for knowledge-intensive nlp tasks"); Lin et al., [2025](https://arxiv.org/html/2601.12904v1#bib.bib3 "TeleRAG: efficient retrieval-augmented generation inference with lookahead retrieval")) is a widely used technique to supplement background knowledge during Large Language Models(LLMs) inference, thereby reducing hallucinations. Recent studies on the inference scaling law of RAG (Yue et al., [2024](https://arxiv.org/html/2601.12904v1#bib.bib41 "Inference scaling for long-context retrieval augmented generation")) show that retrieving more document chunks and performing more retrieval iterations both improve generation results. However, app

[Content truncated...]