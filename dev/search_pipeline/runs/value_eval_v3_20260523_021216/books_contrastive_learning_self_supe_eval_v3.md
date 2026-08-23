# Value Eval v3 — books × contrastive learning self-supervised representations

**Mode:** books  **Query:** contrastive learning self-supervised representations  **Pool (filtered):** 47

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 13 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1677 |
| M7 C3+InstrPrefix | 1754 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1187 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 8158 |
| M12 LLM-Selector | 10712 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.053 | 1/10 |
| M2 RRF post-bucket | 0.053 | 1/10 |
| M3 Structural URL | 0.111 | 2/10 |
| M4 BM25 vanilla | 0.053 | 1/10 |
| M5 BM25-Capped | 0.053 | 1/10 |
| M6 C3 Cross-Encoder | 0.250 | 4/10 |
| M7 C3+InstrPrefix | 0.333 | 5/10 |
| M8 RRF+C3 Hybrid | 0.111 | 2/10 |
| M9 SPLADE | 0.333 | 5/10 |
| M10 SPLADE+C3 | 0.333 | 5/10 |
| M11 C3→LLM-Filter | 0.250 | 4/10 |
| M12 LLM-Selector | 0.176 | 3/10 |

## Pool (oracle input — url/title/snippet)

1. http://ai.googleblog.com/2021/01/google-research-looking-back-at-2020.html
   Google Research: Looking Back at 2020, and Forward to 2021
   ai.googleblog.com

2. http://keg.cs.tsinghua.edu.cn/jietang/publications/TKDE21-Liu-et-al-Self-supervised-Learning-Generative-or-Contrastive.pdf
   PDF Self-supervised Learning: Generative or Contrastive
   Self-supervised representation learning leverages input data itself as supervision and benefits almost all types of downstream tasks. In this survey, we take a look into new self-supervised learning m

3. https://aclanthology.org/2025.ccl-1.61.pdf
   Self-Supervised Contrastive Learning for Content-Centric ...
   Self-Supervised Contrastive Learning for Content-Centric ...ACL Anthologyhttps://aclanthology.org › 2025.ccl-1.61.pdfACL Anthologyhttps://aclanthology.org › 2025.ccl-1.61.pdfPDFby J Li · 2025 — To add

4. https://arxiv.org/html/2406.00262v2
   Contrastive Learning Via Equivariant Representation
   ... the ECL framework and the DDCL method in detail and propose our novel ECL framework, Contrastive Learning Via Equivariant Representation (CLeVER).

5. https://arxiv.org/html/2507.04554v2
   Self-supervised learning of speech representations with Dutch
   Concretely, we ask the following research questions regarding self-supervised speech representation learning, and in particular, the contrastive ...

6. https://arxiv.org/pdf/2304.12210
   A Cookbook of Self-Supervised Learning
   A Cookbook of Self-Supervised LearningarXivhttps://arxiv.org › pdfarXivhttps://arxiv.org › pdfPDFby R Balestriero · 2023 · Cited by 594 — Self-supervised learning, dubbed “the dark matter of intellige

7. https://arxiv.org/pdf/2510.10572
   Understanding Self-supervised Contrastive Learning through Supervised ...
   Our derivation naturally introduces the concepts of prototype representation bias and a balanced contrastive loss, which help explain and improve the behavior of self-supervised learning algorithms. W

8. https://collab.dvb.bayern/download/attachments/73379800/DLMA_Topic8_Manuel_Schreiber_07_%20July_2022.pdf?version=1&modificationDate=1657188497420&api=v2
   Topic 8: Contrastive Learning/Trends in Self- Supervised ...
   Topic 8: Contrastive Learning/Trends in Self- Supervised ...BayernCollabhttps://collab.dvb.bayern › download › attachmentsBayernCollabhttps://collab.dvb.bayern › download › attachmentsPDF6 Jul 2022 — 

9. https://cs229.stanford.edu/notes2021spring/notes2021spring/cs229_lecture_selfsupervision_final.pdf
   PDF Self-Supervised Learning - Stanford University
   Benefits of Self-Supervised Learning ü Like supervised pretraining, can learn general-purpose feature representations for downstream tasks ü Reduces expense of hand-labeling large datasets ü Can lever

10. https://danmackinlay.name/notebook/contrastive_learning.html
   Noise contrastive estimation — The Dan MacKinlay stable of
   ... Contrastive Estimation of Unnormalized Statistical Models, with ... Contrastive Representation Learning: A Framework and Review .” IEEE Access .

11. https://dl.acm.org/doi/book/10.5555/AAI29392284
   Towards Understanding Self-Supervised Representation Learning | Guide books
   The framework is applied to methods like contrastive learning, auto-regressive language modeling and self-prediction based methods. Central to the framework is the idea that pre-training helps learn l

12. https://doi.org/10.1007/978-3-031-43907-0_58
   vox2vec: A Framework for Self-supervised Contrastive Learning of Voxel-Level Representations in Medi
   

13. https://doi.org/10.1016/j.sigpro.2021.108310
   Negative sampling strategies for contrastive self-supervised learning of graph representations
   Hafidi, H. et al. (2022), Signal Processing

14. https://doi.org/10.1038/s42256-022-00447-x
   Molecular contrastive learning of representations via graph neural networks
   (Cited 781×)

15. https://doi.org/10.1101/2020.09.04.283929
   Self-Supervised Contrastive Learning of Protein Representations By Mutual Information Maximization
   Abstract Pretrained embedding representations of biological sequences which capture meaningful properties can alleviate many problems associated with supervised learning in biology. We apply the princ

16. https://doi.org/10.1109/cvprw53098.2021.00129
   Self-Supervised Learning of Remote Sensing Scene Representations Using Contrastive Multiview Coding
   Stojnic, V. et al. (2021), 2021 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)

17. https://doi.org/10.1109/iccv48922.2021.00784
   Contrast and Order Representations for Video Self-supervised Learning
   This paper studies the problem of learning self-supervised representations on videos. In contrast to image modality that only requires appearance information on objects or scenes, video needs to furth

18. https://doi.org/10.1109/iccv48922.2021.01000
   Self-Supervised Visual Representations Learning by Contrastive Mask Prediction
   Advanced self-supervised visual representation learning methods rely on the instance discrimination (ID) pretext task. We point out that the ID task has an implicit semantic consistency (SC) assumptio

19. https://doi.org/10.1109/slt54892.2023.10022552
   CCC-WAV2VEC 2.0: Clustering AIDED Cross Contrastive Self-Supervised Learning of Speech Representatio
   Lodagala, V. et al. (2023), 2022 IEEE Spoken Language Technology Workshop (SLT)

20. https://doi.org/10.2139/ssrn.4967469
   Self-Supervised Contrastive Learning of Multiple Molecular Graph Representations for Molecular Prope
   yunwu, l. et al. (2024)

21. https://doi.org/10.2139/ssrn.5095806
   Contrastive Learning with Only Positive Pairs for Enhancing Content Representations of Self-Supervis
   Meghanani, A. et al. (2025)

22. https://doi.org/10.21437/interspeech.2022-11141
   Non-contrastive self-supervised learning of utterance-level speech representations
   Cho, J. et al. (2022), Interspeech 2022

23. https://doi.org/10.32470/uqprhu8
   Human-aligned Universal Audio Representations with Contrastive-Equivariant Self-Supervised Learning
   Griffith, I. et al. (2026), Proceedings of Cognitive Computational Neuroscience 2026

24. https://doi.org/10.3390/technologies9010002
   A Survey on Contrastive Self-Supervised Learning
   Self-supervised learning has gained popularity because of its ability to avoid the cost of annotating large-scale datasets. It is capable of adopting self-defined pseudolabels as supervision and use t

25. https://doi.org/10.36227/techrxiv.12308378.v1
   CERT: Contrastive Self-supervised Learning for Language Understanding
   Pretrained language models such as BERT, GPT have shown great effectiveness in language understanding. The auxiliary predictive tasks in existing pretraining approaches are mostly defined on tokens, t

26. https://doi.org/10.48550/arxiv.2002.05709
   A Simple Framework for Contrastive Learning of Visual Representations
   This paper presents SimCLR: a simple framework for contrastive learning of visual representations. We simplify recently proposed contrastive self-supervised learning algorithms without requiring speci

27. https://doi.org/10.48550/arxiv.2007.08025
   GraphCL: Contrastive Self-Supervised Learning of Graph Representations
   We propose Graph Contrastive Learning (GraphCL), a general framework for learning node representations in a self supervised manner. GraphCL learns node embeddings by maximizing the similarity between 

28. https://doi.org/10.57702/iuuvgtaz
   A simple framework for contrastive learning of visual representations
   This paper presents SimCLR: a simple framework for contrastive learning of visual representations. We simplify recently proposed contrastive self-supervised learning algorithms without requiring speci

29. https://doi.org/10.59275/j.melba.2022-f9a1
   Learning Representations with Contrastive Self-Supervised Learning for Histopathology Applications
   Unsupervised learning has made substantial progress over the last few years, especially by means of contrastive self-supervised learning. The dominating dataset for benchmarking self-supervised learni

30. https://doi.org/10.7717/peerjcs.1045/table-5
   Table 5: Summary of contrastive self-supervised learning methods in medical imaging.
   

31. https://doras.dcu.ie/25121/1/ACCESS3031549.pdf
   Contrastive Representation Learning: A Framework and Review
   Contrastive Representation Learning: A Framework and ReviewDublin City University | DCUhttps://doras.dcu.ie › ACCESS3031549Dublin City University | DCUhttps://doras.dcu.ie › ACCESS3031549PDFby PH Le-K

32. https://eugeneyan.com/writing/llm-patterns/
   Patterns for Building LLM-based Systems & Products
   eugeneyan.com

33. https://github.com/asheeshcric/awesome-contrastive-self-supervised-learning
   asheeshcric/awesome-contrastive-self-supervised-learning
   2023 2023: Improving multimodal sentiment analysis: Supervised angular margin-based contrastive learning for enhanced fusion representation 2023: Inter-Instance Similarity Modeling for Contrastive Lea

34. https://github.com/zziz/pwc
   Papers with Code
   github.com/zziz

35. https://ieeexplore.ieee.org/document/9462394
   Self-Supervised Learning: Generative or Contrastive
   Self-supervised representation learning leverages input data itself as supervision and benefits almost all types of downstream tasks. In this survey, we take a look into new self-supervised learning m

36. https://jonathanbgn.com/2021/10/30/hubert-visually-explained.html
   HuBERT: How to Apply BERT to Speech, Visually Explained
   jonathanbgn.com

37. https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/
   Prompt Engineering
   lilianweng.github.io

38. https://link.springer.com/chapter/10.1007/978-981-95-2725-0_1
   Self-supervised Contrastive Learning for Content-Centric Speech ...
   To address this issue, we propose a Self-Supervised Contrastive Representation Learning method (SSCRL), which effectively disentangles paralinguistic information from speech content by aligning simila

39. https://neurips.cc/virtual/2025/poster/116198
   Self-Supervised Contrastive Learning is Approximately ...
   Self-Supervised Contrastive Learning is Approximately ...NeurIPS 2026https://neurips.cc › virtual › posterNeurIPS 2026https://neurips.cc › virtual › poster5 Dec 2025 — How does self-supervised contras

40. https://nips.cc/media/neurips-2021/Slides/21895.pdf
   Self-Supervised Learning - Self-Prediction and Contrastive ...
   Self-Supervised Learning - Self-Prediction and Contrastive ...NeurIPS 2026https://nips.cc › media › neurips-2021 › SlidesNeurIPS 2026https://nips.cc › media › neurips-2021 › SlidesPDFSelf-Supervised L

41. https://openai.com/blog/image-gpt/
   Image GPT: model trained on pixel sequences can generate coherent image completions
   openai.com

42. https://people.idsia.ch/~juergen/deep-learning-history.html
   Annotated history of modern AI and deep neural networks
   people.idsia.ch

43. https://scholar.google.de/scholar?q=contrastive+learning+self-supervised+representations+book&hl=en&as_sdt=0&as_vis=1&oi=scholart
   Scholarly articles for contrastive learning self-supervised representations book
   Scholarly articles for contrastive learning self-supervised representations bookSelf-supervised learning: Generative or contrastive - ‎Liu - Cited by 3037Self-supervised representation learning: Intro

44. https://speakerdeck.com/nzw0301/understanding-negative-samples-in-instance-discriminative-self-supervised-representation-learning
   Understanding Negative Samples in Instance Discriminative
   NeurIPS Japan meetup 2021 talk] Understanding Negative Samples in Instance Discriminative Self-supervised Representation Learning

45. https://theaisummer.com/self-supervised-representation-learning-computer-vision/
   Grokking self-supervised (representation) learning: how it
   In a self-supervised learning setup, we imply that the loss function is minimized in the space where the representations live: the feature space ...

46. https://towardsdatascience.com/wav2vec-2-0-a-framework-for-self-supervised-learning-of-speech-representations-7d3728688cae/
   Wav2Vec 2.0: A Framework for Self-Supervised Learning of Speech
   Wav2Vec 2.0 a model for Speech Recognition which takes advantage of self-supervised training and contrastive learning.

47. https://www.deepchecks.com/question/is-contrastive-learning-unsupervised-or-self-supervised/
   Is Contrastive Learning Unsupervised or Self-supervised?
   Often used in self-supervised learning, contrastive learning helps create compact representations from high-dimensional spaces by distinguishing ...

48. https://www.deeplearningdaily.com/a-detailed-study-of-self-supervised-contrastive-loss-and-supervised-contrastive-loss/
   A Detailed Study of Self Supervised Contrastive Loss and
   ... Contrastive Learning paper claims a big deal about supervised learning and cross-entropy loss vs supervised contrastive loss for better image ...

49. https://www.deeplearningdaily.com/speech-resynthesis-from-discrete-disentangled-self-supervised-representations/
   Speech Resynthesis from Discrete Disentangled Self-Supervised
   We analyze various state-of-the-art, self-supervised representation learning methods and shed light on the advantages of each method while ...

50. https://www.emergentmind.com/topics/contrastive-self-supervised-representation-learning
   Contrastive Self-Supervised Representation Learning
   Contrastive Self-Supervised Representation LearningEmergent Mindhttps://www.emergentmind.com › topics › contrastive-s...Emergent Mindhttps://www.emergentmind.com › topics › contrastive-s...10 Nov 2025

51. https://www.intechopen.com/chapters/81791
   Self-Supervised Contrastive Representation Learning in ...
   Self-Supervised Contrastive Representation Learning in ...IntechOpenhttps://www.intechopen.com › chaptersIntechOpenhttps://www.intechopen.com › chaptersby Y Bastanlar · 2022 · Cited by 23 — In this st

52. https://www.mdpi.com/2220-9964/12/2/64
   Self-Supervised Representation Learning for Geographical
   Sciforum MDPI Books Preprints.org ... Feature papers represent the most advanced research with significant potential for high impact in the field.

53. https://www.nature.com/articles/s41586-023-06004-9
   Faster sorting algorithms discovered using deep reinforcement learning
   nature.com

54. https://www.researchgate.net/publication/360867376_Self-Supervised_Contrastive_Representation_Learning_in_Computer_Vision
   (PDF) Self-Supervised Contrastive Representation Learning in Computer ...
   Abstract Although its origins date a few decades back, contrastive learning has recently gained popularity due to its achievements in self-supervised learning, especially in computer vision.

55. https://www.sciencedirect.com/science/article/pii/S0167865522000502
   Self-supervised representation learning for time series
   Web resultsSelf-supervised representation learning for time seriesScienceDirect.comhttps://www.sciencedirect.com › science › article › piiScienceDirect.comhttps://www.sciencedirect.com › science › art

56. https://www.sciencedirect.com/science/article/pii/S0925231224014164
   A comprehensive survey on contrastive learning - ScienceDirect
   Contrastive Learning is self-supervised representation learning by training a model to differentiate between similar and dissimilar samples. It has been shown to be effective and has gained significan

57. https://www.semanticscholar.org/paper/A-Simple-Framework-for-Contrastive-Learning-of-Chen-Kornblith/7af72a461ed7cda180e7eab878efd5f35d79bbf4
   A Simple Framework for Contrastive Learning of Visual Representations
   TLDRIt is shown that composition of data augmentations plays a critical role in defining effective predictive tasks, and introducing a learnable nonlinear transformation between the representation and

58. https://www.semanticscholar.org/paper/Conditional-Contrastive-Learning%3A-Removing-in-Tsai-Ma/c03a3dc40550a8075d233a827fd184d62b93b274
   Conditional Contrastive Learning: Removing Undesirable Information in Self-Supervised Representation
   TLDRThis paper develops conditional contrastive learning to remove undesirable information in self-supervised representations, and introduces Conditional InfoNCE (C-InfoNCE), and its computationally c

59. https://www.semanticscholar.org/paper/CrossPoint%3A-Self-Supervised-Cross-Modal-Contrastive-Afham-Dissanayake/0fd08c1237f80d96a6618d93cb1292b45b9f09fc
   CrossPoint: Self-Supervised Cross-Modal Contrastive Learning for 3D Point Cloud Understanding
   TLDRCrossPoint is a simple cross-modal contrastive learning approach to learn transferable 3D point cloud representations that enables a 3D-2D correspondence of objects by maximizing agreement between

60. https://www.semanticscholar.org/paper/Dual-stream-Multiple-Instance-Learning-Network-for-Li-Li/fc3a214aa4da4a4407c071f056d945bc41893875
   Dual-stream Multiple Instance Learning Network for Whole Slide Image Classification with Self-superv
   TLDRThis work proposes a MIL-based method for WSI classification and tumor detection that does not require localized annotations, and introduces a novel MIL aggregator that models the relations of the

61. https://www.semanticscholar.org/paper/Learning-Self-Supervised-Representations-from-and-Kerr-Huang/64d9b1e3ccb2d3b35efa201d6ef058eabb402a25
   Learning Self-Supervised Representations from Vision and Touch for Active Sliding Perception of Defo
   TLDRA mechanism which enables a robot to autonomously collect spatially aligned visual and tactile data, a key property for downstream tasks, is designed and a step toward task-agnostic visuo-tactile 

62. https://www.semanticscholar.org/paper/Mixing-Up-Contrastive-Learning%3A-Self-Supervised-for-Wickstr%C3%B8m-Kampffmeyer/7f36d87c89afa1eb39554bc21d125b4b2609262b
   Mixing Up Contrastive Learning: Self-Supervised Representation Learning for Time Series
   TLDRThis work proposes an unsupervised contrastive learning framework that is motivated from the perspective of label smoothing and uses a novel contrastive loss that naturally exploits a data augment

63. https://www.semanticscholar.org/paper/Self-Supervised-Transformer-based-Contrastive-for-Koukoulis-Syrigos/4d946ae06762ff3fbbb93f660c0f484be81cfe2a
   Self-Supervised Transformer-based Contrastive Learning for Intrusion Detection Systems
   TLDRThis paper proposes a novel self-supervised contrastive learning approach based on transformer encoders, specifically tailored for generalizable intrusion detection on raw packet sequences, signif

64. https://www.semanticscholar.org/paper/Supervised-Contrastive-Learning-Khosla-Teterwak/38643c2926b10f6f74f122a7037e2cd20d77c0f1
   Supervised Contrastive Learning
   TLDRA novel training methodology that consistently outperforms cross entropy on supervised learning tasks across different architectures and data augmentations is proposed, and the batch contrastive l

65. https://www.semanticscholar.org/paper/vox2vec%3A-A-Framework-for-Self-supervised-Learning-Goncharov-Soboleva/7ec0cbbe2d920727d8e862e1981e1f8351d8f639
   vox2vec: A Framework for Self-supervised Contrastive Learning of Voxel-level Representations in Medi
   

66. https://www.semanticscholar.org/paper/wav2vec-2.0%3A-A-Framework-for-Self-Supervised-of-Baevski-Zhou/49a049dc85e2380dde80501a984878341dd8efdf
   wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations
   

67. https://www.youtube.com/watch?v=7YBwnc9D2d4
   Yonglong Tian - Contrastive Learning: A General Self ...
   Yonglong Tian - Contrastive Learning: A General Self ...YouTube · Vision & Graphics Seminar at MIT19,3K+ views  ·  5 years agoYouTube · Vision & Graphics Seminar at MIT19,3K+ views  ·  5 years ago59:1
