# colbert-ir/colbertv2.0 · Hugging Face
**URL:** https://huggingface.co/colbert-ir/colbertv2.0
**Domain:** huggingface.co
**Score:** 8.0
**Source:** scraped
**Query:** ColBERT late interaction retrieval implementation

---

#  ColBERT (v2) 
###  ColBERT is a _fast_ and _accurate_ retrieval model, enabling scalable BERT-based search over large text collections in tens of milliseconds. 
**Figure 1:** ColBERT's late interaction, efficiently scoring the fine-grained similarity between a queries and a passage. 
As Figure 1 illustrates, ColBERT relies on fine-grained **contextual late interaction** : it encodes each passage into a **matrix** of token-level embeddings (shown above in blue). Then at search time, it embeds every query into another matrix (shown in green) and efficiently finds passages that contextually match the query using scalable vector-similarity (`MaxSim`) operators.
These rich interactions allow ColBERT to surpass the quality of _single-vector_ representation models, while scaling efficiently to large corpora. You can read more in our papers:
  * [**ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT**](https://arxiv.org/abs/2004.12832) (SIGIR'20).
  * [**Relevance-guided Supervision for OpenQA with ColBERT**](https://arxiv.org/abs/2007.00814) (TACL'21).
  * [**Baleen: Robust Multi-Hop Reasoning at Scale via Condensed Retrieval**](https://arxiv.org/abs/2101.00436) (NeurIPS'21).
  * [**ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction**](https://arxiv.org/abs/2112.01488) (NAACL'22).
  * [**PLAID: An Efficient Engine for Late Interaction Retrieval**](https://arxiv.org/abs/2205.09707) (CIKM'22).


##  🚨 **Announcements**
  * (1/29/23) We have merged a new index updater feature and support for additional Hugging Face models! These are in beta so please give us feedback as you try them out.
  * (1/24/23) If you're looking for the **DSP** framework for composing ColBERTv2 and LLMs, it's at: <https://github.com/stanfordnlp/dsp>


##  ColBERTv1 
The ColBERTv1 code from the SIGIR'20 paper is in the [`colbertv1` branch](https://github.com/stanford-futuredata/ColBERT/tree/colbertv1). See [here](https://huggingface.co/colbert-ir/colbertv2.0#branches) for more information on other branches.
##  Installation 
ColBERT requires Python 3.7+ and Pytorch 1.9+ and uses the [Hugging Face Transformers](https://github.com/huggingface/transformers) library.
We strongly recommend creating a conda environment using the commands below. (If you don't have conda, follow the official [conda installation guide](https://docs.anaconda.com/anaconda/install/linux/#installation).)
We have also included a new environment file specifically for CPU-only environments (`conda_env_cpu.yml`), but note that if you are testing CPU execution on a machine that includes GPUs you might need to specify `CUDA_VISIBLE_DEVICES=""` as part of your command. Note that a GPU is required for training and indexing.
```
conda env create -f conda_env[_cpu].yml
conda activate colbert

```

If you face any problems, please [open a new issue](https://github.com/stanford-futuredata/ColBERT/issues) and we'll help you promptly!
##  Overview 
Using ColBERT on a dataset typically involves the following steps.
**Step 0: Preprocess your collection.** At its simplest, ColBERT works with tab-separated (TSV) files: a file (e.g., `collection.tsv`) will contain all passages and another (e.g., `queries.tsv`) will contain a set of queries for searching the collection.
**Step 1: Download the[pre-trained ColBERTv2 checkpoint](https://downloads.cs.stanford.edu/nlp/data/colbert/colbertv2/colbertv2.0.tar.gz).** This checkpoint has been trained on the MS MARCO Passage Ranking task. You can also _optionally_ [train your own ColBERT model](https://huggingface.co/colbert-ir/colbertv2.0#training).
**Step 2: Index your collection.** Once you have a trained ColBERT model, you need to [index your collection](https://huggingface.co/colbert-ir/colbertv2.0#indexing) to permit fast retrieval. This step encodes all passages into matrices, stores them on disk, and builds data structures for efficient search.
**Step 3: Search the collection with your queries.*

[Content truncated...]