# Passage Segmentation of Documents for Extractive Question ... - arXiv
**URL:** https://arxiv.org/html/2501.09940v1
**Domain:** arxiv.org
**Score:** 2.0
**Source:** scraped
**Query:** parent child chunking retrieval augmented generation

---

[License: CC BY 4.0](https://info.arxiv.org/help/license/index.html#licenses-available)
arXiv:2501.09940v1 [cs.CL] 17 Jan 2025
11institutetext: Ecole Polytechnique, France 22institutetext: BNP Paribas CIB, France 33institutetext: Paris Elite Institute of Technology, Shanghai Jiao Tong University, China 33email: zuhong.liu@polytechnique.edu {charles-elie.simon,fabien.caspani}@bnpparibas.com
# Passage Segmentation of Documents for Extractive Question Answering
Report issue for preceding element
Zuhong Liu1,2,3111This work was done during an internship at BNP Paribas CIB, France Charles-Elie Simon2 Fabien Caspani2
Report issue for preceding element
###### Abstract
Report issue for preceding element
Retrieval-Augmented Generation (RAG) has proven effective in open-domain question answering. However, the chunking process, which is essential to this pipeline, often receives insufficient attention relative to retrieval and synthesis components. This study emphasizes the critical role of chunking in improving the performance of both dense passage retrieval and the end-to-end RAG pipeline. We then introduce the Logits-Guided Multi-Granular Chunker (LGMGC), a novel framework that splits long documents into contextualized, self-contained chunks of varied granularity. Our experimental results, evaluated on two benchmark datasets, demonstrate that LGMGC not only improves the retrieval step but also outperforms existing chunking methods when integrated into a RAG pipeline.
Report issue for preceding element
###### Keywords: 
Report issue for preceding elementPassage Segmentation Dense Retrieval Retrieval-Augmented Generation (RAG) 
##  1 Introduction
Report issue for preceding element
Open-Domain Question Answering (ODQA), which involves extracting a precise answer to a question from the content of a given document, has seen significant advancements with the advent of Retrieval-Augmented Generation (RAG) models . These models leverage large-scale pre-trained language models and retrieval systems to enhance the generation of accurate and contextually relevant answers. In a classical RAG pipeline, documents are initially split into independent chunks, and a retrieval process is applied to identify the relevant chunks to a given query. The retrieved chunks with the query are then passed as the prompt to the synthesizer LLM to get the desired response. Subsequent researches have concentrated on improving the two main aspects of RAG: retrieval and synthesis . However, few studies focus on investigating optimal solutions for document chunking and segmentation. The granularity and semantics intuitively play a significant role in precision during the retrieval stage. Besides, the absence of contextual information, as well as excessive irrelevant information within retrieved chunks can hinder the synthesizer LLM’s ability to extract accurate key information despite the retriever’s good performance. 
Report issue for preceding element
In order to address the aforementioned challenges, we propose a new Logits-Guided Multi-Granular Chunker framework. It integrates two chunking modules: Logits-Guided Chunker and Multi-Granular Chunker within a unified framework shown in Figure . The process begins by segmenting the documents into semantically and contextually coherent units, utilizing logits information derived from a smaller-scale LLM. Subsequently, these elementary units, referred to as parent chunks, are further divided into child chunks of varying granularity by the Multi-Granular Chunker in response to different types of query. Our results demonstrate that our approach performs favorably compared to current chunking methods on both passage retrieval and downstream question answering tasks.
Report issue for preceding element
##  2 Related Work
Report issue for preceding element
Several early works have explored chunk optimization for information retrieval. Recursive Chunking segments text using a hierarchy of separators into units based on a predefi

[Content truncated...]