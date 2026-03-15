# Evaluating and Training Contextual Document Embeddings
**URL:** https://huggingface.co/blog/manu/conteb
**Domain:** huggingface.co
**Score:** 2.0
**Source:** scraped
**Query:** contextual chunking prepend context before embedding

---

#  _Context Is Gold to Find the Gold Passage_ : Evaluating and Training Contextual Document Embeddings 
[Community Article](https://huggingface.co/blog/community) Published June 2, 2025
[Manuel Faysse Follow ](https://huggingface.co/manu)
[Max Conti mlconti Follow ](https://huggingface.co/mlconti)
_Traditional embedding methods (right, top) produce embeddings that do not include essential contextual information. Our light-weight training recipe (InSeNT) trains Contextualized Embedding Models that are**aware** of document-wide context when encoding a passage (right, bottom) and can integrate document-wide information in individual chunk representations, augmenting embedding relevance and improving downstream retrieval performance without increasing inference cost._
##  TL;DR 
Dense retrievers typically embed each passage in isolation. When the relevant clues spill across passages, those models mis-rank results. **ConTEB** (the Contextual Text Embedding Benchmark) quantifies this weakness; **InSeNT** + **late-chunking pooling** is a promising way to fix it, with a minor fine-tuning phase and almost no runtime overhead, delivering large gains on ConTEB.
###  Why does context matter ? 
Search applications rarely deal with tweet-length texts. Technical manuals, contracts, scientific papers, and support tickets easily run into thousands of tokens. Users, however, still expect an answer at the passage level. When the decisive evidence sits partially outside the passage boundary, a model that “sees” only a single chunk is likely to fail. Context can help resolve ambiguity, such as distinguishing between multiple meanings of a word or resolving pronouns and entity references. It is also crucial when documents have a structured format, commonly found in legal or scientific texts for instance, and knowing where the passage is within the table of content is essential to understanding.
_In the example above, embedding the sentence in bold "They extended [...]" without leveraging document context will be ambiguous: are we talking about Napoleonic armies or Brazilian football?_
###  How retrieval systems _actually_ chunk documents 
Before embedding, virtually every production pipeline breaks each document into smaller, model and reader-friendly units. Common strategies include:
Strategy | Typical parameters | Rationale & trade-offs  
---|---|---  
**Fixed-length sliding window** |  `k ≈ 128–1024` tokens, some overlap | Simple to implement; overlap reduces boundary effects but multiplies index size.  
**Structure-aware blocks** | Headings, paragraphs, list items | Preserves semantic units but yields highly variable lengths.  
**Hybrid** | Fixed window inside structural blocks | Combines predictability with some respect for discourse structure.  
Designers must balance (i) respecting the Transformer’s maximum input, (ii) keeping enough context for downstream reading comprehension, and (iii) controlling index growth and latency. In practice, no chunking scheme can guarantee that every question’s evidence is entirely self-contained.
##  ConTEB: a benchmark that penalises context blindness 
ConTEB introduces eight retrieval tasks where answering _requires_ information beyond any single chunk. Some datasets are synthetic and controlled (e.g. _Football_ , _Geography_); others are derived from realistic RAG workloads such as NarrativeQA or Covid-QA. A “sanity test” (NanoBEIR) ensures that improvements do not come at the expense of traditional self-contained tasks.
##  Getting into the gist of it: How can we add context to embeddings ? 
Early results on ConTEB showcase context standard retrieval methods struggle in settings in which context is key! Our approach attempts to integrate contextual information through two key components: the recently proposed [Late Chunking](https://arxiv.org/abs/2409.04701) technique, and a custom training recipe we call **InSeNT**.
###  Late chunking: pooling _after_ embedding the full document 
As previously stated, de

[Content truncated...]