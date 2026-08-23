# Value Eval v3 — books × transformer attention mechanism

**Mode:** books  **Query:** transformer attention mechanism  **Pool (filtered):** 66

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 12 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 2499 |
| M7 C3+InstrPrefix | 2653 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1932 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 7177 |
| M12 LLM-Selector | 12317 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.176 | 3/10 |
| M2 RRF post-bucket | 0.176 | 3/10 |
| M3 Structural URL | 0.111 | 2/10 |
| M4 BM25 vanilla | 0.111 | 2/10 |
| M5 BM25-Capped | 0.111 | 2/10 |
| M6 C3 Cross-Encoder | 0.111 | 2/10 |
| M7 C3+InstrPrefix | 0.176 | 3/10 |
| M8 RRF+C3 Hybrid | 0.176 | 3/10 |
| M9 SPLADE | 0.176 | 3/10 |
| M10 SPLADE+C3 | 0.176 | 3/10 |
| M11 C3→LLM-Filter | 0.333 | 5/10 |
| M12 LLM-Selector | 0.176 | 3/10 |

## Pool (oracle input — url/title/snippet)

1. https://alexzhang13.github.io/blog/2024/efficient-dl/
   A Meticulous Guide to Advances in Deep Learning Efficiency over the Years
   alexzhang13.github.io

2. https://aman.ai/primers/ai/LLM/#overview
   Overview of Large Language Models
   aman.ai

3. https://arxiv.org/abs/1706.03762
   [1706.03762] Attention Is All You Need - arXiv.org
   The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and d

4. https://arxiv.org/html/2302.07730v4
   Transformer models: an introduction and catalog
   A key aspect of this attention mechanism in Transformers is that each token flows through its own computation path, thus lending itself to parallel ...

5. https://arxiv.org/pdf/2312.00752
   Mamba: Linear-Time Sequence Modeling with Selective State Spaces
   arxiv.org

6. https://arxiv.org/pdf/2406.02528
   Scalable MatMul-free Language Modeling
   arxiv.org

7. https://chargedmagazine.org/2023/03/chatgpts-auto-biography/
   ChatGPT's Auto-Biography - Charged Magazine
   ... is rooted in the fields of artificial intelligence and machine learning, and specifically in the use of transformers and self-attention mechanisms ...

8. https://d2l.ai/chapter_attention-mechanisms-and-transformers/
   11. Attention Mechanisms and Transformers
   11. Attention Mechanisms and TransformersDive into Deep Learninghttps://d2l.ai › chapter_attention-mechanisms-and-transfo...Dive into Deep Learninghttps://d2l.ai › chapter_attention-mechanisms-and-tra

9. https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html
   11. Attention Mechanisms and Transformers — Dive into Deep ... - D2L
   11. Attention Mechanisms and Transformers The earliest years of the deep learning boom were driven primarily by results produced using the multilayer perceptron, convolutional network, and recurrent n

10. https://datasciencedojo.com/blog/understanding-attention-mechanism/
   Revolutionary Attention Mechanism: Power of Transformers
   Transformers have revolutionized natural language processing with their use of self-attention mechanisms. ... Transformer relies entirely on ...

11. https://datasciencedojo.com/newsletter/transformers-attention-mechanisms/
   An Introduction to Transformers and Attention Mechanisms
   Newsletter / Beginner ’ s Guide to Transformers and Attention Mechanisms ... The transformers use a special type of attention called ...

12. https://deeprevision.github.io/posts/001-transformer/
   The Transformer Blueprint: A Holistic Guide to the Transformer Neural Network Architecture
   deeprevision.github.io

13. https://discuss.huggingface.co/t/attention-mechanism/162672
   Attention mechanism - 🤗TransformersHugging Face Forums · 10 months ago
   

14. https://doi.org/10.1007/s10792-026-03966-3
   GDPooled transformer: glaucoma detection using pooled attention based transformer with attention mec
   Bharathi, V. et al. (2026), International Ophthalmology

15. https://doi.org/10.1016/j.aei.2023.102007
   DenseSPH-YOLOv5: An automated damage detection model based on DenseNet and Swin-Transformer predicti
   (Cited 248×)

16. https://doi.org/10.1016/j.knosys.2024.111507
   Transformer-based multivariate time series anomaly detection using inter-variable attention mechanis
   (Cited 116×)

17. https://doi.org/10.1016/j.ymssp.2021.108616
   A novel time–frequency Transformer based on self–attention mechanism and its application in fault di
   (Cited 485×)

18. https://doi.org/10.1093/bib/bbab421
   MDF-SA-DDI: predicting drug–drug interaction events based on multi-source drug fusion, multi-source 
   One of the main problems with the joint use of multiple drugs is that it may cause adverse drug interactions and side effects that damage the body. Therefore, it is important to predict potential drug

19. https://doi.org/10.1109/tim.2022.3181933
   Convolutional Transformer: An Enhanced Attention Mechanism Architecture for Remaining Useful Life Es
   Nowadays, deep learning (DL) methods for prognostic and health management (PHM) have vastly broadened the scope of applications in this field. Numerous approaches based on deep neural networks have be

20. https://doi.org/10.1609/aaai.v35i12.17325
   Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting
   Many real-world applications require the prediction of long sequence time-series, such as electricity consumption planning. Long sequence time-series forecasting (LSTF) demands a high prediction capac

21. https://doi.org/10.1609/aaai.v36i2.20142
   When Shift Operation Meets Vision Transformer: An Extremely Simple Alternative to Attention Mechanis
   Attention mechanism has been widely believed as the key to success of vision transformers (ViTs), since it provides a flexible and powerful way to model spatial relationships. However, is the attentio

22. https://doi.org/10.21203/rs.3.rs-3545247/v1
   Easy attention: A simple self-attention mechanism for transformer-based time-series reconstruction a
   Abstract To improve the robustness of transformer neural networks used for temporal-dynamics prediction of chaotic systems, we propose a novel attention mechanism called easy attention which we demons

23. https://doi.org/10.21203/rs.3.rs-3741963/v1
   Improving Sentiment Analysis in Online Course Reviews with BERT and Transformer Attention Mechanism
   Abstract In the field of text mining, sentiment analysis has grown significantly in importance for understanding user reactions. This knowledge contributes to improving several features of given goods

24. https://doi.org/10.21437/interspeech.2022-10066
   Improving Transformer-based Conversational ASR by Inter-Sentential Attention Mechanism
   Wei, K. et al. (2022), Interspeech 2022

25. https://doi.org/10.22541/au.169769165.55793181/v1
   Revolutionizing Wireless Traffic Usage Forecasting: Transformer with Attention Mechanism
   Revolutionizing wireless traffic forecasting empowers proactive resource allocation, optimizing network performance and ensuring efficient utilization of resources in dynamic wireless environments. re

26. https://doi.org/10.22541/au.173772018.80603459/v1
   FCA-Transformer: A Feature Pyramid Time Series Forecasting Model Driven by Cross-Attention Mechanism
   With the swift progression of information technology, time series forecasting has become increasingly vital across various domains including finance, energy, and transportation. Traditional Recurrent 

27. https://doi.org/10.31219/osf.io/m6gcn
   Attention Mechanism, Transformers, BERT, and GPT: Tutorial and Survey
   This is a tutorial and survey paper on the attention mechanism, transformers, BERT, and GPT. We first explain attention mechanism, sequence-to-sequence model without and with attention, self-attention

28. https://doi.org/10.31224/2476
   Generalized Attention Mechanism and Relative Position for Transformer
   Pandya, R. (2022)

29. https://doi.org/10.32614/cran.package.transformer
   transformer: Implementation of Transformer Deep Neural Network with Vignettes
   Quast, B. (2023), CRAN: Contributed Packages

30. https://doi.org/10.3390/biology12071033
   Transformer Architecture and Attention Mechanisms in Genome Data Analysis: A Comprehensive Review
   The emergence and rapid development of deep learning, specifically transformer-based architectures and attention mechanisms, have had transformative implications across several domains, including bioi

31. https://doi.org/10.3390/rs14122861
   Swin-Transformer-Enabled YOLOv5 with Attention Mechanism for Small Object Detection on Satellite Ima
   Object detection has made tremendous progress in natural images over the last decade. However, the results are hardly satisfactory when the natural image object detection algorithm is directly applied

32. https://doi.org/10.5220/0012014800003633
   Combining Transformer and Reverse Attention Mechanism for Polyp Segmentation
   Lin, J. et al. (2022), Proceedings of the 4th International Conference on Biotechnology and Biomedicine

33. https://doi.org/10.5244/c.35.86
   PS-Transformer: Learning Sparse Photometric Stereo Network using Self-Attention Mechanism
   Ikehata, S. (2021), Proceedings of the British Machine Vision Conference 2021

34. https://doi.org/10.65215/2q58a426
   Attention Is All You Need
   The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and d

35. https://doi.org/10.7717/peerj-cs.3536/fig-5
   Figure 5: Architectural diagram of the vision transformer and attention mechanism within the hybrid 
   

36. https://e2eml.school/transformers.html
   Transformers from Scratch
   e2eml.school

37. https://en.wikipedia.org/wiki/Attention_Is_All_You_Need
   Attention Is All You Need - Wikipedia
   " Attention Is All You Need " [1] is a 2017 research paper in machine learning authored by eight scientists and engineers working at Google. The paper introduced a new deep learning architecture known

38. https://faculty.ist.psu.edu/vhonavar/Courses/dsmethods/transformer.pdf
   PDF Attention Mechanism, Transformers, BERT, and GPT: Tutorial and Survey
   We explained attention mechanism, the sequence-to-sequence model with and without atten-tion, and self-attention. The different parts of encoder and decoder of a transformer were explained.

39. https://jalammar.github.io/illustrated-transformer/
   The Illustrated Transformer
   The Illustrated TransformerJay Alammarhttps://jalammar.github.io › illustrated-transformerJay Alammarhttps://jalammar.github.io › illustrated-transformer27 Jun 2018 — Self-attention is the method the 

40. https://lilianweng.github.io/posts/2018-06-24-attention/
   Attention? Attention
   lilianweng.github.io

41. https://link.springer.com/chapter/10.1007/978-3-032-10738-1_9
   Attention Mechanism and Transformers | Springer Nature Link
   The chapter begins by introducing the attention mechanism as a data-weighting strategy and explains its role in enhancing the performance of deep learning models, particularly in sequence modeling. A 

42. https://ljvmiranda921.github.io/notebook/2021/08/08/clip-vqgan/
   The Illustrated VQGAN
   ljvmiranda921.github.io

43. https://lucalp.dev/bitter-lesson-tokenization-and-blt
   The Bitter Lesson is coming for Tokenization
   lucalp.dev

44. https://machinelearningmastery.com/the-transformer-attention-mechanism/
   The Transformer Attention Mechanism - MachineLearningMastery.com
   Hi Luc … The transformer attention mechanism can indeed be a bit tricky to follow, but let ’ s break it down step-by-step to clarify the ...

45. https://medium.com/@nitinmittapally/understanding-attention-in-transformers-a-visual-guide-df416bfe495a
   Understanding Attention in Transformers: A Visual Guide
   Attention mechanisms are the cornerstone of transformer models, enabling them to process sequential data with remarkable efficiency. In this post, we'll dive deep into how attention works and ...

46. https://openlibrary.org/works/OL12439399W
   Cartesian meditations
   Edmund Husserl (1960) — 13 eds, ebook: no_ebook

47. https://openlibrary.org/works/OL15311250W
   The origin of ideas
   Antonio Rosmini (1883) — 7 eds, ebook: public

48. https://openlibrary.org/works/OL1618262W
   History of the World's Fair
   Benjamin Cummings Truman (1893) — 5 eds, ebook: public

49. https://openlibrary.org/works/OL18481636W
   Understanding events
   Jeffrey M. Zacks (2007) — 3 eds, ebook: borrowable

50. https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf
   PDF Attention Is All You Need - NeurIPS
   The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dis

51. https://research.google/pubs/attention-is-all-you-need/
   Attention is All You Need
   Web resultsAttention is All You NeedResearch at Googlehttps://research.google › pubs › attention-is-all-you-needResearch at Googlehttps://research.google › pubs › attention-is-all-you-needWe propose a

52. https://scholar.google.de/scholar?q=transformer+attention+mechanism+book&hl=en&as_sdt=0&as_vis=1&oi=scholart
   Scholarly articles for transformer attention mechanism book
   Scholarly articles for transformer attention mechanism bookAttention Mechanism and Transformers - ‎Ghojogh - Cited by 157Attention mechanism in neural networks: where it  … - ‎Soydaner - Cited by 548T

53. https://sebastianraschka.com/blog/2023/self-attention-from-scratch.html
   Understanding and Coding the Self-Attention Mechanism ...
   Understanding and Coding the Self-Attention Mechanism ...Sebastian Raschka, PhDhttps://sebastianraschka.com › self-attention-from-scratchSebastian Raschka, PhDhttps://sebastianraschka.com › self-atten

54. https://simple.wikipedia.org/wiki/Transformer_(machine_learning_model)
   Transformer (machine learning model) - Simple English
   Transformers were introduced in a 2017 paper "Attention Is All You Need" by a Google Brain team. ... Parallel Attention Mechanisms in Neural Machine ...

55. https://stackoverflow.com/questions/54232350/how-to-manipulate-encoder-state-in-a-multi-layer-bidirectional-with-attention-me
   How to manipulate encoder state in a multi-layer bidirectional with Attention Mechanism
   I am implementing a Seq2Seq model with multi-layer bidirectional rnn and attention mechanism and while following this tutorial https://github.com/tensorflow/nmt I got confused about how to manipulate 

56. https://stackoverflow.com/questions/55491752/workaround-for-using-tf-matmul-with-two-non-constant-inputs
   Workaround for using tf.matmul with two non-constant inputs
   We are currently trying to convert a transformer model to a tensorflow-lite graph but it seems that the problem is the self-attention mechanism. We're not able to process the graph. Looking into tf-li

57. https://stackoverflow.com/questions/58007391/attention-text-generation-in-character-by-character-fashion
   Attention Text Generation in Character-by-Character fashion
   I am searching the web for a couple of days for any text generation model that would use only attention mechanisms. The Transformer architecture that made waves in the context of Seq-to-Seq models is 

58. https://stackoverflow.com/questions/58855564/how-is-the-self-attention-mechanism-in-transformers-able-to-learn-how-the-words
   How is the self-attention mechanism in Transformers able to learn how the words are related to each 
   Given the sentence The animal didn't cross the street because it was too tired , how the self-attention is able to map with a higher score the word aninal intead of the word street ? I'm wondering if 

59. https://stackoverflow.com/questions/65543593/why-doesnt-the-transformer-use-positional-encoding-in-every-layer
   Why doesn't the transformer use positional encoding in every layer?
   Positional encoding is added to the input before it is passed into the transformer model, because otherwise the attention mechanism would be order invariant. However, both the encoder and decoder are 

60. https://stackoverflow.com/questions/70213109/valueerror-shapes-none-5-and-none-15-5-are-incompatible
   ValueError: Shapes (None, 5) and (None, 15, 5) are incompatible
   I want to implement a Hierarchical attention mechanism for document classification presented by Yang. But I want to replace LSTM with Transformer. I used Apoorv Nandan's text classification with Trans

61. https://stackoverflow.com/questions/70271797/how-to-implement-hierarchical-transformer-for-document-classification-in-keras
   How to implement hierarchical Transformer for document classification in Keras?
   Hierarchical attention mechanism for document classification has been presented by Yang et al. https://www.cs.cmu.edu/~./hovy/papers/16HLT-hierarchical-attention-networks.pdf Its implementation is ava

62. https://stackoverflow.com/questions/72567409/one-head-attention-mechanism-pytorch
   one head attention mechanism pytorch
   I am trying to implement the attention mechanism using the CIFAR10 dataset. The idea is to implement the attention layer considering only one head. Therefore, I took as reference the multi-head implem

63. https://stackoverflow.com/questions/75224660/visualisation-attentions-transformer-based-architecture
   Visualisation Attentions Transformer-based Architecture
   I have a transformer based architecture, specifically I have both an encoder using Vision Transformers and a decoder using Language Models based on Transformers. We know that Transformers have a speci

64. https://stackoverflow.com/questions/77449999/pytorch-runtimeerror-invalid-shape-during-reshaping-for-multi-head-attention
   PyTorch RuntimeError: Invalid Shape During Reshaping for Multi-Head Attention
   I'm implementing a multi-head self-attention mechanism in PyTorch which is part of Text2Image model that I am trying to build and I'm encountering a runtime error when trying to reshape the output of 

65. https://stackoverflow.com/questions/77718720/changing-the-attention-layer-of-a-transformer
   Changing the Attention Layer of a Transformer
   I would like to test my own formulation of the attention mechanism for a transformer. To that end I would like to find an existing pre trained transformer that is easy to read through and that uses no

66. https://vitalflux.com/attention-mechanism-in-transformers-examples/
   Attention Mechanism in Transformers: Examples
   Attention mechanisms in transformer models rely on a concept called Query, Keys, and Values to decide where to look for the key information or where ...

67. https://vitalflux.com/attention-mechanism-workflow-example/
   Attention Mechanism Workflow & Transformer: Examples
   The attention mechanism in transformers, crucial for tasks like machine translation and text summarization , follows a multi-step workflow to enhance ...

68. https://web.stanford.edu/~jurafsky/slp3/8.pdf
   8 Transformers
   8 TransformersStanford Universityhttps://web.stanford.edu › ~jurafsky › slp3 › 8.pdfStanford Universityhttps://web.stanford.edu › ~jurafsky › slp3 › 8.pdfPDFAttention is the mechanism in the transform

69. https://web.stanford.edu/~jurafsky/slp3/slides/transformer24aug.pdf
   PDF Introduction to Transformers Transformers - Stanford University
   Figure 9.6 The architecture of a transformer block showing the residual stream. figure shows the prenorm version of the architecture, in which the layer norms happen the attention and feedforward laye

70. https://www.amazon.com/Science-Attention-Exploring-Workings-Transformers-ebook/dp/B0C73PY48Y
   The Science of Attention : Exploring the Inner Workings ...
   The Science of Attention : Exploring the Inner Workings ...Amazon.comhttps://www.amazon.com › Science-Attention-Explorin...Amazon.comhttps://www.amazon.com › Science-Attention-Explorin...At the heart 

71. https://www.billparker.ai/2024/10/transformer-attention-simple-guide-to-q.html
   Transformer Attention: A Guide to the Q, K, and V Matrices
   Understanding the Transformer Attention Mechanism Transformers have revolutionized the way machines process language and other sequential data. At the heart of the Transformer architecture is a powerf

72. https://www.deeplearningdaily.com/the-transformer-attention-mechanism/
   The Transformer Attention Mechanism – Deep Learning Daily
   We will first focus on the Transformer attention mechanism in this tutorial and subsequently review the Transformer model in a separate one.

73. https://www.gwern.net/GPT-3
   GPT-3 Creative Fiction
   gwern.net

74. https://www.machinelearningmastery.com/transformer-models-with-attention/
   Building Transformer Models with Attention
   Building Transformer Models with AttentionMachine Learning Masteryhttps://www.machinelearningmastery.com › transformer...Machine Learning Masteryhttps://www.machinelearningmastery.com › transformer...

75. https://www.oreilly.com/library/view/python-deep-learning/9781837638505/B19627_07.xhtml
   Python Deep Learning - Third Edition
   Web resultsPython Deep Learning - Third EditionO'Reilly bookshttps://www.oreilly.com › library › view › python-deep...O'Reilly bookshttps://www.oreilly.com › library › view › python-deep...In this cha

76. https://www.reddit.com/r/deeplearning/comments/1gmpqjy/any_recommendations_for_materials_for_attention/
   any recommendations for materials for attention ...
   Web resultsany recommendations for materials for attention ...Reddit · r/deeplearning10+ comments  ·  1 year agoReddit · r/deeplearning10+ comments  ·  1 year agoany recommendations for materials for 

77. https://www.semanticscholar.org/paper/A-Novel-Transformer-Network-with-a-CNN-Enhanced-for-Wang-Sun/a28c06106a9a03942ef93fef9eb21ae82e140cc4
   A Novel Transformer Network with a CNN-Enhanced Cross-Attention Mechanism for Hyperspectral Image Cl
   TLDRA novel transformer network with a CNN-enhanced cross-attention (TNCCA) mechanism for HSI classification that utilizes different scales of HSI input data to extract shallow spatial–spectral featur

78. https://www.semanticscholar.org/paper/A-PV-cell-defect-detector-combined-with-transformer-Lang-Lv/ef8d75f1de8d16411fef405c34c77639a2d266b1
   A PV cell defect detector combined with transformer and attention mechanism
   TLDRThis paper presents a novel PV defect detection algorithm that leverages the YOLO architecture, integrating an attention mechanism and the Transformer module, and introduces a polarized self-atten

79. https://www.semanticscholar.org/paper/Energy-efficient-tugboat-scheduling%3A-A-hybrid-and-Pitakaso-Sethanan/40205636069c955aadd1688a43ef86cf2bd160fb
   Energy-efficient tugboat scheduling: A hybrid transformer-attention mechanism and artificial multipl
   

80. https://www.semanticscholar.org/paper/Eye-Tracking-Response-Modeling-and-Design-Method-on-Lu-Kim/a1724d788b107246e604c2b5085a2afabc25c9e3
   Eye-Tracking Response Modeling and Design Optimization Method for Smart Home Interface Based on Tran
   TLDRA smart home interface eye-tracking response optimization model based on spatio-temporal Transformer and gate control cross-attention that adapts the physiological characteristics of eye-tracking 

81. https://www.semanticscholar.org/paper/Research-on-sentiment-analysis-model-improved-based-Ji/c8a544d0463e16cab475c8365f27b618d93bbf77
   Research on sentiment analysis model improved based on Transformer attention mechanism
   TLDRThis model effectively handles multidimensional emotional expression and domain specific language and provides a new path for the field of sentiment analysis and has important value in scenarios s

82. https://www.semanticscholar.org/paper/ST-DAAE%3A-An-Enhanced-Swin-Transformer-Attention-for-Madhavi-Singh/7e109394990a54e7cb915f7ec891045bdeeab4c5
   ST-DAAE: An Enhanced Swin Transformer Attention Mechanism for Leaf Disease Classification
   TLDRA novel dual-technique method that uses Drop Attention for regularization and Attention Entropy Loss for optimization in the Swin Transformer framework to improve leaf disease classification and s

83. https://www.semanticscholar.org/paper/Speech-Emotion-Recognition-via-CNN-Transformer-and-Tang-Huang/719273b24e82cefab64b51e7f4488127d9b0d221
   Speech Emotion Recognition via CNN-Transformer and multidimensional attention mechanism
   TLDRA Speech Emotion Recognition network based on CNN-Transformer and multi-dimensional attention mechanisms is proposed, which significantly improves the performance over the state-of-the-art methods

84. https://www.semanticscholar.org/paper/Transformer-based-multivariate-time-series-anomaly-Kang-Kang/9624170045b3c659a524f3a2461c49399c53a6ea
   Transformer-based multivariate time series anomaly detection using inter-variable attention mechanis
   

85. https://www.semanticscholar.org/paper/Unsupervised-Word-Sense-Disambiguation-Using-Ion-Pais/7ef322ab846ce64873a2f8434076c61bfe0a8508
   Unsupervised Word Sense Disambiguation Using Transformer's Attention Mechanism
   TLDRUsing the Transformer’s attention mechanism, a word sense disambiguation (WSD) algorithm can now construct a more faithful vectorial representation of the context of a word to be disambiguated.Exp

86. https://www.semanticscholar.org/paper/YOLOV5-CBAM-C3TR%3A-an-optimized-model-based-on-and-Lv-Su/2ab33fc5282f88767cc0dc9bf60e770cbda53c50
   YOLOV5-CBAM-C3TR: an optimized model based on transformer module and attention mechanism for apple l
   TLDRThe YOLOV5-CBAM-C3TR model proposed in this paper has been applied to the detection of apple leaf diseases for the first time, and also showed strong recognition ability in identifying similar dis
