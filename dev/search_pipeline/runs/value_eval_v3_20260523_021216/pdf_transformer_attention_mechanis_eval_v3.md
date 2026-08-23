# Value Eval v3 — pdf × transformer attention mechanism

**Mode:** pdf  **Query:** transformer attention mechanism  **Pool (filtered):** 64

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 13 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 2335 |
| M7 C3+InstrPrefix | 2443 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 2586 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 7244 |
| M12 LLM-Selector | 11354 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.111 | 2/10 |
| M2 RRF post-bucket | 0.111 | 2/10 |
| M3 Structural URL | 0.111 | 2/10 |
| M4 BM25 vanilla | 0.111 | 2/10 |
| M5 BM25-Capped | 0.111 | 2/10 |
| M6 C3 Cross-Encoder | 0.176 | 3/10 |
| M7 C3+InstrPrefix | 0.111 | 2/10 |
| M8 RRF+C3 Hybrid | 0.111 | 2/10 |
| M9 SPLADE | 0.053 | 1/10 |
| M10 SPLADE+C3 | 0.053 | 1/10 |
| M11 C3→LLM-Filter | 0.333 | 5/10 |
| M12 LLM-Selector | 0.250 | 4/10 |

## Pool (oracle input — url/title/snippet)

1. http://www.gautamkamath.com/courses/CS480-fa2025-files/lec18.pdf
   Attention and Transformers
   Attention and TransformersGautam Kamathhttp://www.gautamkamath.com › courses › lec18Gautam Kamathhttp://www.gautamkamath.com › courses › lec18PDF• The attention mechanism solves most of these. • …thou

2. https://aclanthology.org/D19-1443/
   Transformer Dissection: An Unified Understanding for
   At the core of the Transformer is the attention mechanism, which concurrently processes all inputs in the streams. ... the Transformer{ }s attention ...

3. https://alexzhang13.github.io/blog/2024/efficient-dl/
   A Meticulous Guide to Advances in Deep Learning Efficiency over the Years
   alexzhang13.github.io

4. https://aman.ai/primers/ai/LLM/#overview
   Overview of Large Language Models
   aman.ai

5. https://andre-martins.github.io/docs/dsl2020/attention-mechanisms.pdf
   Attention Mechanisms
   Attention MechanismsAndré F. T. Martinshttps://andre-martins.github.io › docs › dsl2020André F. T. Martinshttps://andre-martins.github.io › docs › dsl2020PDF2 Dec 2020 — Why attention? Attention is a 

6. https://arxiv.org/abs/2003.04974
   [2003.04974] Transformer++
   Transformer using attention mechanism solely achieved state-of-the-art results in sequence modeling. ... translation based on the attention mechanism ...

7. https://arxiv.org/abs/2604.00965
   Understanding Transformers and Attention Mechanisms
   Web resultsUnderstanding Transformers and Attention MechanismsarXivhttps://arxiv.org › matharXivhttps://arxiv.org › mathby MF Serret · 2026 · Cited by 1 — This document provides a brief introduction t

8. https://arxiv.org/html/2604.00965v1
   Understanding Transformers and Attention Mechanisms: An
   Attention mechanisms, the building blocks of the Transformer architecture [ Vas+17 ] , allow encoding of semantic information between tokens through ...

9. https://arxiv.org/pdf/2312.00752
   Mamba: Linear-Time Sequence Modeling with Selective State Spaces
   arxiv.org

10. https://arxiv.org/pdf/2406.02528
   Scalable MatMul-free Language Modeling
   arxiv.org

11. https://arxiv.org/pdf/2601.03329
   Attention mechanisms in neural networks - arXiv.org
   Applications in natural language processing, computer vision, and multimodal learning demonstrate the versatility of attention mechanisms. We examine language modeling with autoregressive transformers

12. https://cl-illc.github.io/semantics-2023/resources/slides/attention_and_transformers.pdf
   PDF Attention & Transformers - GitHub Pages
   Hierarchical attention networks for document classification. In Proceedings of the 2016 conference of the North American chapter of the association for computational linguistics: human language techno

13. https://courses.cs.washington.edu/courses/cse543/22sp/schedule/lecture15_transformer.pdf
   Attention Mechanism
   Attention MechanismUW Homepagehttps://courses.cs.washington.edu › schedule › le...UW Homepagehttps://courses.cs.washington.edu › schedule › le...PDF• Transformer: a fully attention-based architecture 

14. https://cs231n.stanford.edu/slides/2025/lecture_8.pdf
   PDF Lecture 8: Attention and Transformers - cs231n.stanford.edu
   Today: Attention + Transformers Attention: A new primitive that Transformer: A neural operates on sets of vectors network architecture that uses attention everywhere Transformers are used everywhere t

15. https://datascience.stackexchange.com/questions/131545/masking-during-transformer-inference
   attention mechanism - Masking during transformer inference? -
   This said, DeepSeek writes that all the attention layers in transformers are bidirectional (so no triangular mask applied) which is not correct as ...

16. https://datasciencedojo.com/blog/understanding-attention-mechanism/
   Revolutionary Attention Mechanism: Power of Transformers
   Transformers have revolutionized natural language processing with their use of self-attention mechanisms. ... Transformer relies entirely on ...

17. https://deeprevision.github.io/posts/001-transformer/
   The Transformer Blueprint: A Holistic Guide to the Transformer Neural Network Architecture
   deeprevision.github.io

18. https://doi.org/10.1007/s10792-026-03966-3
   GDPooled transformer: glaucoma detection using pooled attention based transformer with attention mec
   Bharathi, V. et al. (2026), International Ophthalmology

19. https://doi.org/10.1016/j.aei.2023.102007
   DenseSPH-YOLOv5: An automated damage detection model based on DenseNet and Swin-Transformer predicti
   (Cited 248×)

20. https://doi.org/10.1016/j.knosys.2024.111507
   Transformer-based multivariate time series anomaly detection using inter-variable attention mechanis
   (Cited 116×)

21. https://doi.org/10.1016/j.ymssp.2021.108616
   A novel time–frequency Transformer based on self–attention mechanism and its application in fault di
   (Cited 485×)

22. https://doi.org/10.1093/bib/bbab421
   MDF-SA-DDI: predicting drug–drug interaction events based on multi-source drug fusion, multi-source 
   One of the main problems with the joint use of multiple drugs is that it may cause adverse drug interactions and side effects that damage the body. Therefore, it is important to predict potential drug

23. https://doi.org/10.1109/tim.2022.3181933
   Convolutional Transformer: An Enhanced Attention Mechanism Architecture for Remaining Useful Life Es
   Nowadays, deep learning (DL) methods for prognostic and health management (PHM) have vastly broadened the scope of applications in this field. Numerous approaches based on deep neural networks have be

24. https://doi.org/10.1609/aaai.v35i12.17325
   Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting
   Many real-world applications require the prediction of long sequence time-series, such as electricity consumption planning. Long sequence time-series forecasting (LSTF) demands a high prediction capac

25. https://doi.org/10.21203/rs.3.rs-3545247/v1
   Easy attention: A simple self-attention mechanism for transformer-based time-series reconstruction a
   Abstract To improve the robustness of transformer neural networks used for temporal-dynamics prediction of chaotic systems, we propose a novel attention mechanism called easy attention which we demons

26. https://doi.org/10.21437/interspeech.2022-10066
   Improving Transformer-based Conversational ASR by Inter-Sentential Attention Mechanism
   Wei, K. et al. (2022), Interspeech 2022

27. https://doi.org/10.22541/au.169769165.55793181/v1
   Revolutionizing Wireless Traffic Usage Forecasting: Transformer with Attention Mechanism
   Revolutionizing wireless traffic forecasting empowers proactive resource allocation, optimizing network performance and ensuring efficient utilization of resources in dynamic wireless environments. re

28. https://doi.org/10.22541/au.173772018.80603459/v1
   FCA-Transformer: A Feature Pyramid Time Series Forecasting Model Driven by Cross-Attention Mechanism
   With the swift progression of information technology, time series forecasting has become increasingly vital across various domains including finance, energy, and transportation. Traditional Recurrent 

29. https://doi.org/10.31219/osf.io/m6gcn
   Attention Mechanism, Transformers, BERT, and GPT: Tutorial and Survey
   This is a tutorial and survey paper on the attention mechanism, transformers, BERT, and GPT. We first explain attention mechanism, sequence-to-sequence model without and with attention, self-attention

30. https://doi.org/10.31224/2476
   Generalized Attention Mechanism and Relative Position for Transformer
   Pandya, R. (2022)

31. https://doi.org/10.32614/cran.package.transformer
   transformer: Implementation of Transformer Deep Neural Network with Vignettes
   Quast, B. (2023), CRAN: Contributed Packages

32. https://doi.org/10.3390/biology12071033
   Transformer Architecture and Attention Mechanisms in Genome Data Analysis: A Comprehensive Review
   The emergence and rapid development of deep learning, specifically transformer-based architectures and attention mechanisms, have had transformative implications across several domains, including bioi

33. https://doi.org/10.3390/rs14122861
   Swin-Transformer-Enabled YOLOv5 with Attention Mechanism for Small Object Detection on Satellite Ima
   Object detection has made tremendous progress in natural images over the last decade. However, the results are hardly satisfactory when the natural image object detection algorithm is directly applied

34. https://doi.org/10.5220/0012014800003633
   Combining Transformer and Reverse Attention Mechanism for Polyp Segmentation
   Lin, J. et al. (2022), Proceedings of the 4th International Conference on Biotechnology and Biomedicine

35. https://doi.org/10.5244/c.35.86
   PS-Transformer: Learning Sparse Photometric Stereo Network using Self-Attention Mechanism
   Ikehata, S. (2021), Proceedings of the British Machine Vision Conference 2021

36. https://doi.org/10.65215/2q58a426
   Attention Is All You Need
   The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and d

37. https://doi.org/10.7717/peerj-cs.3536/fig-5
   Figure 5: Architectural diagram of the vision transformer and attention mechanism within the hybrid 
   

38. https://e2eml.school/transformers.html
   Transformers from Scratch
   e2eml.school

39. https://engineering.purdue.edu/DeepLearn/pdf-kak/Transformers.pdf
   PDF Transformers: Learning with Purely Attention Based Networks
   Now that you understand the basics of the attention mechanism in a transformer, it is time to jump to a higher perspective on the overall architecture of a transformer.

40. https://faculty.ist.psu.edu/vhonavar/Courses/dsmethods/transformer.pdf
   PDF Attention Mechanism, Transformers, BERT, and GPT: Tutorial and Survey
   Abstract This is a tutorial and survey paper on the atten-tion mechanism, transformers, BERT, and GPT. We first explain attention mechanism, sequence-to-sequence model without and with attention, self

41. https://fenix.tecnico.ulisboa.pt/downloadFile/1970943312377766/lecture_10.pdf
   PDF Lecture 10: Attention Mechanisms and Transformers - ULisboa
   Lecture 10: Attention Mechanisms and Transformers Andre Martins, Francisco Melo, Mario Figueiredo Deep Learning Course, Winter 2022-2023

42. https://hal.science/hal-04637647v1/document
   Attention Mechanism, Transformers, BERT, and GPT
   Attention Mechanism, Transformers, BERT, and GPTArchive ouverte HALhttps://hal.science › documentArchive ouverte HALhttps://hal.science › documentPDFby B Ghojogh · 2020 · Cited by 157 — This is a tuto

43. https://jalammar.github.io/illustrated-transformer/
   The Illustrated Transformer (2018)
   jalammar.github.io

44. https://lilianweng.github.io/posts/2018-06-24-attention/
   Attention? Attention
   lilianweng.github.io

45. https://lucalp.dev/bitter-lesson-tokenization-and-blt
   The Bitter Lesson is coming for Tokenization
   lucalp.dev

46. https://machinelearningmastery.com/the-transformer-attention-mechanism/
   The Transformer Attention Mechanism - MachineLearningMastery.com
   Hi Luc … The transformer attention mechanism can indeed be a bit tricky to follow, but let ’ s break it down step-by-step to clarify the ...

47. https://momath.org/wp-content/uploads/2023/06/Rohan_Mehta_compressed.pdf
   The Attention Mechanism Demystified
   The Attention Mechanism DemystifiedNational Museum of Mathematics (MoMath)https://momath.org › Rohan_Mehta_compressedNational Museum of Mathematics (MoMath)https://momath.org › Rohan_Mehta_compressedP

48. https://myrtle.ai/resources/blogs/leo-1-low-earth-orbit-satellites/
   Vision Transformers 1: Low Earth Orbit Satellites - myrtle.ai
   ... focuses on the theory behind attention and the application of Vision Transformer ... Central to all transformer models is the attention mechanism.

49. https://openlibrary.org/works/OL12439399W
   Cartesian meditations
   Edmund Husserl (1960) — 13 eds, ebook: no_ebook

50. https://openlibrary.org/works/OL15311250W
   The origin of ideas
   Antonio Rosmini (1883) — 7 eds, ebook: public

51. https://openlibrary.org/works/OL1618262W
   History of the World's Fair
   Benjamin Cummings Truman (1893) — 5 eds, ebook: public

52. https://openlibrary.org/works/OL18481636W
   Understanding events
   Jeffrey M. Zacks (2007) — 3 eds, ebook: borrowable

53. https://research.colfax-intl.com/wp-content/uploads/2024/03/intro-to-transformers.pdf
   PDF Attention and the Transformer Architecture
   At the time, the attention mechanism was introduced in conjunction with RNNs to model large-scale dependencies within data. A key insight of "Attention Is All You Need" was to dispense with recurrence

54. https://stackoverflow.com/questions/54232350/how-to-manipulate-encoder-state-in-a-multi-layer-bidirectional-with-attention-me
   How to manipulate encoder state in a multi-layer bidirectional with Attention Mechanism
   I am implementing a Seq2Seq model with multi-layer bidirectional rnn and attention mechanism and while following this tutorial https://github.com/tensorflow/nmt I got confused about how to manipulate 

55. https://stackoverflow.com/questions/55491752/workaround-for-using-tf-matmul-with-two-non-constant-inputs
   Workaround for using tf.matmul with two non-constant inputs
   We are currently trying to convert a transformer model to a tensorflow-lite graph but it seems that the problem is the self-attention mechanism. We're not able to process the graph. Looking into tf-li

56. https://stackoverflow.com/questions/58007391/attention-text-generation-in-character-by-character-fashion
   Attention Text Generation in Character-by-Character fashion
   I am searching the web for a couple of days for any text generation model that would use only attention mechanisms. The Transformer architecture that made waves in the context of Seq-to-Seq models is 

57. https://stackoverflow.com/questions/58855564/how-is-the-self-attention-mechanism-in-transformers-able-to-learn-how-the-words
   How is the self-attention mechanism in Transformers able to learn how the words are related to each 
   Given the sentence The animal didn't cross the street because it was too tired , how the self-attention is able to map with a higher score the word aninal intead of the word street ? I'm wondering if 

58. https://stackoverflow.com/questions/65543593/why-doesnt-the-transformer-use-positional-encoding-in-every-layer
   Why doesn't the transformer use positional encoding in every layer?
   Positional encoding is added to the input before it is passed into the transformer model, because otherwise the attention mechanism would be order invariant. However, both the encoder and decoder are 

59. https://stackoverflow.com/questions/70271797/how-to-implement-hierarchical-transformer-for-document-classification-in-keras
   How to implement hierarchical Transformer for document classification in Keras?
   Hierarchical attention mechanism for document classification has been presented by Yang et al. https://www.cs.cmu.edu/~./hovy/papers/16HLT-hierarchical-attention-networks.pdf Its implementation is ava

60. https://stackoverflow.com/questions/72567409/one-head-attention-mechanism-pytorch
   one head attention mechanism pytorch
   I am trying to implement the attention mechanism using the CIFAR10 dataset. The idea is to implement the attention layer considering only one head. Therefore, I took as reference the multi-head implem

61. https://stackoverflow.com/questions/75224660/visualisation-attentions-transformer-based-architecture
   Visualisation Attentions Transformer-based Architecture
   I have a transformer based architecture, specifically I have both an encoder using Vision Transformers and a decoder using Language Models based on Transformers. We know that Transformers have a speci

62. https://stackoverflow.com/questions/77449999/pytorch-runtimeerror-invalid-shape-during-reshaping-for-multi-head-attention
   PyTorch RuntimeError: Invalid Shape During Reshaping for Multi-Head Attention
   I'm implementing a multi-head self-attention mechanism in PyTorch which is part of Text2Image model that I am trying to build and I'm encountering a runtime error when trying to reshape the output of 

63. https://stackoverflow.com/questions/77718720/changing-the-attention-layer-of-a-transformer
   Changing the Attention Layer of a Transformer
   I would like to test my own formulation of the attention mechanism for a transformer. To that end I would like to find an existing pre trained transformer that is easy to read through and that uses no

64. https://www.cse.iitk.ac.in/users/piyush/courses/ml-autumn23/slides/Lecture-25.pdf
   Attention Mechanism and Transformers
   Attention Mechanism and TransformersCSE - IIT Kanpurhttps://www.cse.iitk.ac.in › slides › Lecture-25CSE - IIT Kanpurhttps://www.cse.iitk.ac.in › slides › Lecture-25PDFby P Rai · Cited by 4 — Attention

65. https://www.deeplearningdaily.com/implementation-of-attention-mechanism-for-caption-generation-on-transformers-using-tensorflow/
   Implementation of Attention Mechanism for Caption Generation on
   In this article, let’s see how you can implement the Attention Mechanism for Caption Generation with Transformers using TensorFlow.

66. https://www.deeplearningdaily.com/the-transformer-attention-mechanism/
   The Transformer Attention Mechanism – Deep Learning Daily
   We will first focus on the Transformer attention mechanism in this tutorial and subsequently review the Transformer model in a separate one.

67. https://www.gwern.net/GPT-3
   GPT-3 Creative Fiction
   gwern.net

68. https://www.math.utah.edu/~bwang/mathds/Lecture14.pdf
   Lecture 14. Self-attention Mechanism and Transformers
   Lecture 14. Self-attention Mechanism and TransformersThe University of Utahhttps://www.math.utah.edu › ~bwang › mathdsThe University of Utahhttps://www.math.utah.edu › ~bwang › mathdsPDFBERT involves 

69. https://www.researchgate.net/publication/347623569_Attention_Mechanism_Transformers_BERT_and_GPT_Tutorial_and_Survey
   (PDF) Attention Mechanism, Transformers, BERT, and GPT ... - ResearchGate
   PDF | This is a tutorial and survey paper on the attention mechanism, transformers, BERT, and GPT. We first explain attention mechanism,... | Find, read and cite all the research you need on ...

70. https://www.researchgate.net/publication/399571920_Attention_Mechanisms_in_Transformers_A_Comparative_Survey_and_Structural_Enhancements_to_Linear_Attention
   (PDF) Attention Mechanisms in Transformers
   (PDF) Attention Mechanisms in TransformersResearchGatehttps://www.researchgate.net › publication › 39957192...ResearchGatehttps://www.researchgate.net › publication › 39957192...9 Jan 2026 — Transform

71. https://www.semanticscholar.org/paper/A-Novel-Transformer-Network-with-a-CNN-Enhanced-for-Wang-Sun/a28c06106a9a03942ef93fef9eb21ae82e140cc4
   A Novel Transformer Network with a CNN-Enhanced Cross-Attention Mechanism for Hyperspectral Image Cl
   TLDRA novel transformer network with a CNN-enhanced cross-attention (TNCCA) mechanism for HSI classification that utilizes different scales of HSI input data to extract shallow spatial–spectral featur

72. https://www.semanticscholar.org/paper/A-PV-cell-defect-detector-combined-with-transformer-Lang-Lv/ef8d75f1de8d16411fef405c34c77639a2d266b1
   A PV cell defect detector combined with transformer and attention mechanism
   TLDRThis paper presents a novel PV defect detection algorithm that leverages the YOLO architecture, integrating an attention mechanism and the Transformer module, and introduces a polarized self-atten

73. https://www.semanticscholar.org/paper/Eye-Tracking-Response-Modeling-and-Design-Method-on-Lu-Kim/a1724d788b107246e604c2b5085a2afabc25c9e3
   Eye-Tracking Response Modeling and Design Optimization Method for Smart Home Interface Based on Tran
   TLDRA smart home interface eye-tracking response optimization model based on spatio-temporal Transformer and gate control cross-attention that adapts the physiological characteristics of eye-tracking 

74. https://www.semanticscholar.org/paper/Multiple-paddy-disease-recognition-methods-based-on-Zhang-Dong/8f4b90c336a005978606d4c3eb8e8ca71ceca467
   Multiple paddy disease recognition methods based on deformable transformer attention mechanism in co
   TLDRA precise object detection framework to address the challenges of severe overlap, multi-disease detection, morphological irregularities,Multi-scale object classification, and complex scenarios in 

75. https://www.semanticscholar.org/paper/Research-on-sentiment-analysis-model-improved-based-Ji/c8a544d0463e16cab475c8365f27b618d93bbf77
   Research on sentiment analysis model improved based on Transformer attention mechanism
   TLDRThis model effectively handles multidimensional emotional expression and domain specific language and provides a new path for the field of sentiment analysis and has important value in scenarios s

76. https://www.semanticscholar.org/paper/ST-DAAE%3A-An-Enhanced-Swin-Transformer-Attention-for-Madhavi-Singh/7e109394990a54e7cb915f7ec891045bdeeab4c5
   ST-DAAE: An Enhanced Swin Transformer Attention Mechanism for Leaf Disease Classification
   TLDRA novel dual-technique method that uses Drop Attention for regularization and Attention Entropy Loss for optimization in the Swin Transformer framework to improve leaf disease classification and s

77. https://www.semanticscholar.org/paper/Speech-Emotion-Recognition-via-CNN-Transformer-and-Tang-Huang/719273b24e82cefab64b51e7f4488127d9b0d221
   Speech Emotion Recognition via CNN-Transformer and multidimensional attention mechanism
   TLDRA Speech Emotion Recognition network based on CNN-Transformer and multi-dimensional attention mechanisms is proposed, which significantly improves the performance over the state-of-the-art methods

78. https://www.semanticscholar.org/paper/Transformer-based-multivariate-time-series-anomaly-Kang-Kang/9624170045b3c659a524f3a2461c49399c53a6ea
   Transformer-based multivariate time series anomaly detection using inter-variable attention mechanis
   

79. https://www.semanticscholar.org/paper/Unsupervised-Word-Sense-Disambiguation-Using-Ion-Pais/7ef322ab846ce64873a2f8434076c61bfe0a8508
   Unsupervised Word Sense Disambiguation Using Transformer's Attention Mechanism
   TLDRUsing the Transformer’s attention mechanism, a word sense disambiguation (WSD) algorithm can now construct a more faithful vectorial representation of the context of a word to be disambiguated.Exp

80. https://www.semanticscholar.org/paper/YOLOV5-CBAM-C3TR%3A-an-optimized-model-based-on-and-Lv-Su/2ab33fc5282f88767cc0dc9bf60e770cbda53c50
   YOLOV5-CBAM-C3TR: an optimized model based on transformer module and attention mechanism for apple l
   TLDRThe YOLOV5-CBAM-C3TR model proposed in this paper has been applied to the detection of apple leaf diseases for the first time, and also showed strong recognition ability in identifying similar dis

81. https://www.slideshare.net/slideshow/attention-is-all-you-need-pdf-attention-is-all-you-need-pdfattention-is-all-you-need-pdf/274757188
   attention is all you need.pdf attention is all you
   We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions ...

82. https://yildizoglu.fr/resources/IREF-M1-AI/Appendix-Explanation-self-attention-Transformers.pdf
   Explanation of the Self-Attention Mechanism in the ...
   Explanation of the Self-Attention Mechanism in the ...Murat Yildizogluhttps://yildizoglu.fr › resources › IREF-M1-AIMurat Yildizogluhttps://yildizoglu.fr › resources › IREF-M1-AIPDF10 Feb 2025 — The s
