# Value Eval v3 — docs × contrastive learning self-supervised representations

**Mode:** docs  **Query:** contrastive learning self-supervised representations  **Pool (filtered):** 47

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 15 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1664 |
| M7 C3+InstrPrefix | 1744 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1184 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 7826 |
| M12 LLM-Selector | 10409 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.111 | 2/10 |
| M2 RRF post-bucket | 0.111 | 2/10 |
| M3 Structural URL | 0.111 | 2/10 |
| M4 BM25 vanilla | 0.053 | 1/10 |
| M5 BM25-Capped | 0.111 | 2/10 |
| M6 C3 Cross-Encoder | 0.250 | 4/10 |
| M7 C3+InstrPrefix | 0.176 | 3/10 |
| M8 RRF+C3 Hybrid | 0.111 | 2/10 |
| M9 SPLADE | 0.333 | 5/10 |
| M10 SPLADE+C3 | 0.333 | 5/10 |
| M11 C3→LLM-Filter | 0.267 | 4/10 |
| M12 LLM-Selector | 0.053 | 1/10 |

## Pool (oracle input — url/title/snippet)

1. http://ai.googleblog.com/2021/01/google-research-looking-back-at-2020.html
   Google Research: Looking Back at 2020, and Forward to 2021
   ai.googleblog.com

2. http://keg.cs.tsinghua.edu.cn/jietang/publications/TKDE21-Liu-et-al-Self-supervised-Learning-Generative-or-Contrastive.pdf
   PDF Self-supervised Learning: Generative or Contrastive
   Self-supervised representation learning leverages input data itself as supervision and benefits almost all types of downstream tasks. In this survey, we take a look into new self-supervised learning m

3. https://aclanthology.org/2021.findings-emnlp.3/
   Self-supervised Contrastive Cross-Modality Representation
   ... we propose novel training schemes for spoken question answering with a self-supervised training stage and a contrastive representation learning stage.

4. https://aclanthology.org/2025.ccl-1.61.pdf
   Self-Supervised Contrastive Learning for Content-Centric ...
   Self-Supervised Contrastive Learning for Content-Centric ...ACL Anthologyhttps://aclanthology.org › 2025.ccl-1.61.pdfACL Anthologyhttps://aclanthology.org › 2025.ccl-1.61.pdfPDFby J Li · 2025 — To add

5. https://ankeshanand.com/blog/2020/01/26/contrative-self-supervised-learning.html
   Contrastive Self-Supervised Learning
   Contrastive Self-Supervised LearningAnkesh Anandhttps://ankeshanand.com › blog › 2020/01/26 › contrativ...Ankesh Anandhttps://ankeshanand.com › blog › 2020/01/26 › contrativ...26 Jan 2020 — Contrastiv

6. https://arxiv.org/html/2509.11316v1
   Contrastive Network Representation Learning
   Contrastive learning is a self-supervised approach that learns meaningful representations by teaching models to distinguish between similar (positive ...

7. https://arxiv.org/html/2603.06180v1
   Contrastive-to-Self-Supervised: A Two-Stage Framework for
   2.0.2 Contrastive and Self-Supervised Representation Learning. ... Contrastive-to-Self-Supervised: A Two-Stage Framework for Script Similarity ...

8. https://arxiv.org/pdf/2510.10572
   Understanding Self-supervised Contrastive Learning through Supervised ...
   Our derivation naturally introduces the concepts of prototype representation bias and a balanced contrastive loss, which help explain and improve the behavior of self-supervised learning algorithms. W

9. https://collab.dvb.bayern/download/attachments/73379800/DLMA_Topic8_Manuel_Schreiber_07_%20July_2022.pdf?version=1&modificationDate=1657188497420&api=v2
   Topic 8: Contrastive Learning/Trends in Self- Supervised ...
   Topic 8: Contrastive Learning/Trends in Self- Supervised ...BayernCollabhttps://collab.dvb.bayern › download › attachmentsBayernCollabhttps://collab.dvb.bayern › download › attachmentsPDF6 Jul 2022 — 

10. https://deepai.org/publication/multi-view-contrastive-self-supervised-learning-of-accounting-data-representations-for-downstream-audit-tasks
   Multi-view Contrastive Self-Supervised Learning of Accounting
   Multi-view Contrastive Self-Supervised Learning of Accounting Data Representations for Downstream Audit Tasks ... contrastive self- supervised ...

11. https://dell.scholars.harvard.edu/publications/linking-representations-multimodal-contrastive-learning
   Linking Representations with Multimodal Contrastive Learning |
   ... and language bi-encoders, aligned through contrastive language-image pre-training, to learn a metric space where the pooled image-text representation ...

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

25. https://doi.org/10.36227/techrxiv.16828363
   SELF-SUPERVISED ACOUSTIC ANOMALY DETECTION VIA CONTRASTIVE LEARNING
   We propose an acoustic anomaly detection algorithm based on the framework of contrastive learning. Contrastive learning is a recently proposed self-supervised approach that has shown promising results

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
   

31. https://encord.com/blog/guide-to-contrastive-learning/
   Full Guide to Contrastive Learning
   Web resultsFull Guide to Contrastive LearningEncordhttps://encord.com › blog › guide-to-contrastive-learningEncordhttps://encord.com › blog › guide-to-contrastive-learning14 Jul 2023 — Contrastive lea

32. https://eugeneyan.com/writing/llm-patterns/
   Patterns for Building LLM-based Systems & Products
   eugeneyan.com

33. https://github.com/RezaJahanii/Self-Supervised-Learning
   RezaJahanii/Self-Supervised-Learning - GitHub
   Self-Supervised Contrastive Learning for Visual Representation Overview This project implements and compares self-supervised learning (SSL) methods for visual representation learning. Two frameworks a

34. https://github.com/topics/representation-learning
   representation-learning · GitHub Topics · GitHub
   computer-vision representation-learning unsupervised-learning self-supervised-learning simclr contrastive-learning simclrv2

35. https://github.com/zziz/pwc
   Papers with Code
   github.com/zziz

36. https://ieeexplore.ieee.org/document/9711402
   Contrasting Contrastive Self-Supervised Representation Learning ...
   In the past few years, we have witnessed remarkable breakthroughs in self-supervised representation learning. Despite the success and adoption of representations learned through this paradigm, much is

37. https://jonathanbgn.com/2021/10/30/hubert-visually-explained.html
   HuBERT: How to Apply BERT to Speech, Visually Explained
   jonathanbgn.com

38. https://keras.io/examples/vision/nnclr/
   Self-supervised contrastive learning with NNCLR
   Introduction Self-supervised learning Self-supervised representation learning aims to obtain robust representations of samples from raw data without expensive labels or annotations. Early methods in t

39. https://keras.io/examples/vision/simsiam/
   Self-supervised contrastive learning with SimSiam
   ... Learning Image classification with ... Self-supervised learning (SSL) is an interesting branch of study in the field of representation learning.

40. https://lightning.ai/docs/pytorch/1.8.1/notebooks/course_UvA-DL/13-contrastive-learning.html
   Tutorial 13: Self-Supervised Contrastive Learning with SimCLR
   In this tutorial, we will take a closer look at self-supervised contrastive learning. Self-supervised learning, or also sometimes called unsupervised learning, describes the scenario where we have giv

41. https://lilianweng.github.io/posts/2021-05-31-contrastive/
   Contrastive Representation Learning
   Contrastive Representation LearningLil'Loghttps://lilianweng.github.io › 2021-05-31-contrastiveLil'Loghttps://lilianweng.github.io › 2021-05-31-contrastive31 May 2021 — The goal of contrastive represe

42. https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/
   Prompt Engineering
   lilianweng.github.io

43. https://medium.com/@myscale/an-in-depth-guide-to-contrastive-learning-techniques-models-and-applications-909828f65f20
   An In-Depth Guide to Contrastive Learning: Techniques, ...
   An In-Depth Guide to Contrastive Learning: Techniques, ...Medium · MyScale50+ likes  ·  1 year agoMedium · MyScale50+ likes  ·  1 year agoContrastive learning centers around a simple concept of choosi

44. https://milvus.io/ai-quick-reference/how-do-contrastive-learning-and-selfsupervised-learning-work-together
   How do contrastive learning and self-supervised ...
   How do contrastive learning and self-supervised ...Milvushttps://milvus.io › ai-quick-reference › how-do-contrast...Milvushttps://milvus.io › ai-quick-reference › how-do-contrast...Contrastive learnin

45. https://openaccess.thecvf.com/content/ICCV2021/papers/Kotar_Contrasting_Contrastive_Self-Supervised_Representation_Learning_Pipelines_ICCV_2021_paper.pdf
   PDF Contrasting Contrastive Self-Supervised Representation Learning Pipelines
   In this paper, we analyze contrastive approaches as one of the most successful and popular variants of self-supervised representation learning. We perform this analysis from the perspective of the tra

46. https://openai.com/blog/image-gpt/
   Image GPT: model trained on pixel sequences can generate coherent image completions
   openai.com

47. https://people.idsia.ch/~juergen/deep-learning-history.html
   Annotated history of modern AI and deep neural networks
   people.idsia.ch

48. https://pli.princeton.edu/blog/2024/self-supervised-reinforcement-learning-contrastive-representations
   Self-Supervised Reinforcement Learning with Contrastive Representations
   Chongyi Zheng, Benjamin EysenbachUnsupervised learning is really powerful. It lies at the heart of large language models (just predict the next token), generative image models (predict what noise to r

49. https://pubmed.ncbi.nlm.nih.gov/42153366/
   Comprehensive Review of Contrastive and Generative Self-Supervised ...
   We begin by detailing the essential public databases and benchmarks that support modern research, then conduct an in-depth analysis of contrastive and generative methodologies, first as they apply to 

50. https://scholar.google.de/scholar?q=contrastive+learning+self-supervised+representations+documentation&hl=en&as_sdt=0&as_vis=1&oi=scholart
   Scholarly articles for contrastive learning self-supervised representations documentation
   Scholarly articles for contrastive learning self-supervised representations documentation… : Self-supervised document representation learning - ‎Li - Cited by 239Self-supervised representation learnin

51. https://scholarworks.utrgv.edu/etd/1218/
   "Self-Supervised Representation Learning for Motion Time
   In addition, we will describe how the newest and most efficient self-supervised learning framework for visual representations to this date works ...

52. https://sigport.org/documents/contrastive-separative-coding-self-supervised-representation-learning
   CONTRASTIVE SEPARATIVE CODING FOR SELF-SUPERVISED
   ...  ... Available at: https://sigport.org/documents/contrastive-separative-coding-self-supervised-representation-learning.

53. https://uvadlc-notebooks.readthedocs.io/en/latest/tutorial_notebooks/tutorial17/SimCLR.html
   Tutorial 17: Self-Supervised Contrastive Learning with SimCLR
   Tutorial 17: Self-Supervised Contrastive Learning with SimCLRuvadlc-notebookshttps://uvadlc-notebooks.readthedocs.io › latest › SimCLRuvadlc-notebookshttps://uvadlc-notebooks.readthedocs.io › latest ›

54. https://www.nature.com/articles/s41586-023-06004-9
   Faster sorting algorithms discovered using deep reinforcement learning
   nature.com

55. https://www.researchsquare.com/article/rs-5058251/v1
   Self-supervised representation learning for clinical decision
   The widespread adoption of Electronic Health Records (EHRs) and deep learning, particularly through Self-Supervised Representation Learning (SSRL ...

56. https://www.sciencedirect.com/science/article/pii/S0167865522000502
   Self-supervised representation learning for time series
   Self-supervised representation learning for time seriesScienceDirect.comhttps://www.sciencedirect.com › science › article › piiScienceDirect.comhttps://www.sciencedirect.com › science › article › piib

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
   

67. https://www.youtube.com/watch?v=aW9rCWVJcig
   Self-Supervised Learning - Contrastive Representation Learning
   Self-Supervised Learning - Contrastive Representation LearningYouTube · EO College540+ views  ·  1 year agoYouTube · EO College540+ views  ·  1 year ago8:09The idea is all these augmented images shoul
