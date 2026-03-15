# PyLate: Flexible Training and Retrieval for Late Interaction Models
**URL:** https://arxiv.org/html/2508.03555v1
**Domain:** arxiv.org
**Score:** 16.0
**Source:** scraped
**Query:** ColBERT late interaction retrieval implementation

---

[License: arXiv.org perpetual non-exclusive license](https://info.arxiv.org/help/license/index.html#licenses-available)
arXiv:2508.03555v1 [cs.IR] 05 Aug 2025
# PyLate: Flexible Training and Retrieval for Late Interaction Models
Report issue for preceding element
Antoine Chaffin  antoine.chaffin@lighton.ai LightOnNancyFrance and  Raphaël Sourty  raphael.sourty@lighton.ai LightOnParisFrance
Report issue for preceding element
###### Abstract.
Report issue for preceding element
Neural ranking has become a cornerstone of modern information retrieval. While single vector search remains the dominant paradigm, it suffers from the shortcoming of compressing all the information into a single vector. This compression leads to notable performance degradation in out-of-domain, long-context, and reasoning-intensive retrieval tasks. Multi-vector approaches pioneered by ColBERT aim to address these limitations by preserving individual token embeddings and computing similarity via the MaxSim operator. This architecture has demonstrated superior empirical advantages, including enhanced out-of-domain generalization, long-context handling, and performance in complex retrieval scenarios. Despite these compelling empirical results and clear theoretical advantages, the practical adoption and public availability of late interaction models remain low compared to their single-vector counterparts, primarily due to a lack of accessible and modular tools for training and experimenting with such models. To bridge this gap, we introduce PyLate, a streamlined library built on top of Sentence Transformers to support multi-vector architectures natively, inheriting its efficient training, advanced logging, and automated model card generation while requiring minimal code changes to code templates users are already familiar with. By offering multi-vector-specific features such as efficient indexes, PyLate aims to accelerate research and real-world application of late interaction models, thereby unlocking their full potential in modern IR systems. Finally, PyLate has already enabled the development of state-of-the-art models, including GTE-ModernColBERT and Reason-ModernColBERT, demonstrating its practical utility for both research and production environments.
Report issue for preceding element
††copyright: none††conference: Make sure to enter the correct conference title from your rights confirmation email; ; ††isbn: 978-1-4503-XXXX-X/2018/06
##  1. Introduction
Report issue for preceding element
Information retrieval (IR) has evolved significantly with the integration of pre-trained transformers such as BERT (Devlin et al., [2019](https://arxiv.org/html/2508.03555v1#bib.bib12)) to perform semantical search, overcoming the vocabulary mismatch of lexical approaches. Dense (single vector) search (Karpukhin et al., [2020](https://arxiv.org/html/2508.03555v1#bib.bib18)) employs these transformers-based models to create contextualized representations (embeddings) of the input sequence tokens and then apply a pooling operation such as max, mean or CLS (first token) to aggregates these token-level embeddings into a single fixed-dimensional vector representing the entire sequence. The single vector paradigm facilitates pre-computation and indexing of document embeddings, enabling rapid retrieval by identifying nearest neighbors to a query embedding within a shared vector space using a similarity such as cosine.
Report issue for preceding element
Numerous models have been trained following this simple approach with various training objectives, datasets and sizes of models (Zhang et al., [2024](https://arxiv.org/html/2508.03555v1#bib.bib37); Li et al., [2023b](https://arxiv.org/html/2508.03555v1#bib.bib22); Chen et al., [2024](https://arxiv.org/html/2508.03555v1#bib.bib6); Sturua et al., [2024](https://arxiv.org/html/2508.03555v1#bib.bib32); Nussbaum et al., [2024](https://arxiv.org/html/2508.03555v1#bib.bib26)). However, despite strong performance on various benchmarks, 

[Content truncated...]