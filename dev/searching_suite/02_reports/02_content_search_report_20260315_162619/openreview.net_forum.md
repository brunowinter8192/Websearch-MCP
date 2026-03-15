# Long-Context Inference with Retrieval-Augmented Speculative Decoding
**URL:** https://openreview.net/forum?id=73mDARqOtQ
**Domain:** openreview.net
**Score:** 2.7
**Source:** scraped
**Query:** LLM generated context prefix per chunk retrieval

---

### BibTeX Record
_Click anywhere on the box above to highlight complete record_
Done
[Go to **ICML 2025 Conference** homepage](https://openreview.net/group?id=ICML.cc/2025/Conference "Venue Homepage")
## RAPID: Long-Context Inference with Retrieval-Augmented Speculative Decoding
### [Guanzheng Chen](https://openreview.net/profile?id=~Guanzheng_Chen1), [Qilong Feng](https://openreview.net/profile?id=~Qilong_Feng2), [Jinjie Ni](https://openreview.net/profile?id=~Jinjie_Ni1), [Xin Li](https://openreview.net/profile?id=~Xin_Li40), [Michael Qizhe Shieh](https://openreview.net/profile?id=~Michael_Qizhe_Shieh1)
**Abstract:**
The emergence of long-context large language models (LLMs) offers a promising alternative to traditional retrieval-augmented generation (RAG) for processing extensive documents. However, the computational overhead of long-context inference presents significant efficiency challenges. While Speculative Decoding (SD) traditionally accelerates inference using smaller draft models, its effectiveness diminishes substantially in long-context scenarios due to memory-bound KV cache operations. We introduce Retrieval-Augmented Speculative Decoding (RAPID), which leverages RAG for both accelerating and enhancing generation quality in long-context inference. RAPID introduces the RAG drafter—a draft LLM operating on shortened retrieval contexts—to speculate on the generation of long-context target LLMs. Our approach enables a new paradigm where same-scale or even larger LLMs can serve as RAG drafters while maintaining computational efficiency. To fully leverage the potentially superior capabilities from stronger RAG drafters, we develop an inference-time knowledge transfer that enriches the target distribution by RAG. Extensive experiments on the LLaMA-3.1 and Qwen2.5 backbones demonstrate that RAPID effectively integrates the strengths of both RAG and long-context LLMs, achieving significant performance improvements (e.g., from 39.33 to 42.83 on InfiniteBench for LLaMA-3.1-8B) with more than 2 speedups for long-context inference. Our analyses also reveal the robustness of RAPID across various context lengths and retrieval quality.
**Lay Summary:**
Large language models (LLMs) excel at answering questions from huge documents like books or reports, but processing every word makes them painfully slow. Our solution, Retrieval-Augmented Speculative Decoding (RAPID), acts like a sharp librarian and expert editor working together. RAPID swiftly pinpoints key passages relevant to the question, then another LLM drafts potential answers using only those snippets. The main LLM, like a skilled editor, verifies these drafts in parallel against the full document, quickly correcting or improving them instead of generating answers step by step. This teamwork makes RAPID over twice as fast while often producing better answers than traditional methods. Its speed and accuracy open new doors for efficiently analyzing complex texts like legal cases, scientific papers, or lengthy reports, transforming how we use powerful LLMs in real-world tasks.
**Link To Code:** <https://github.com/NUS-TRAIL/RAPID>
**Primary Area:** Deep Learning->Large Language Models
**Keywords:** Speculative Decoding, Long-Context LLM, RAG
**Submission Number:** 10999
#### **Paper Decision**
Copy URL of note 9VO1TWjaLc
Decisionby Program Chairs
**Decision:** Accept (spotlight poster)
**Comment:**
The paper introduces RAPID, a novel integration of Retrieval-Augmented Generation (RAG) with Speculative Decoding (SD) for efficient long-context inference in LLMs. All reviewers found the problem timely and the method promising. The authors provided extensive empirical evidence on multiple model families and benchmarks, demonstrating improvements in both performance and efficiency. The theoretical justifications were also sound.
Several reviewers initially raised concerns about baselines, overhead, and novelty relative to prior work like TRIFORCE and REST. The authors provided a v

[Content truncated...]