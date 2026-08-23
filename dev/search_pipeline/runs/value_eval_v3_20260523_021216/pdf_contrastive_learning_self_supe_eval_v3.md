# Value Eval v3 — pdf × contrastive learning self-supervised representations

**Mode:** pdf  **Query:** contrastive learning self-supervised representations  **Pool (filtered):** 47

## Method Latencies

| Method | ms |
|--------|-----|
| M1 C1 Overlap-Count | 0 |
| M2 RRF post-bucket | 0 |
| M3 Structural URL | 0 |
| M4 BM25 vanilla | 15 |
| M5 BM25-Capped | 1 |
| M6 C3 Cross-Encoder | 1673 |
| M7 C3+InstrPrefix | 1748 |
| M8 RRF+C3 Hybrid | 0 |
| M9 SPLADE | 1286 |
| M10 SPLADE+C3 | 0 |
| M11 C3→LLM-Filter | 8774 |
| M12 LLM-Selector | 10943 |

## Jaccard vs Oracle (v3clean)

| Method | Jaccard | Oracle captured |
|--------|---------|-----------------|
| M1 C1 Overlap-Count | 0.111 | 2/10 |
| M2 RRF post-bucket | 0.111 | 2/10 |
| M3 Structural URL | 0.250 | 4/10 |
| M4 BM25 vanilla | 0.053 | 1/10 |
| M5 BM25-Capped | 0.053 | 1/10 |
| M6 C3 Cross-Encoder | 0.111 | 2/10 |
| M7 C3+InstrPrefix | 0.176 | 3/10 |
| M8 RRF+C3 Hybrid | 0.176 | 3/10 |
| M9 SPLADE | 0.333 | 5/10 |
| M10 SPLADE+C3 | 0.333 | 5/10 |
| M11 C3→LLM-Filter | 0.333 | 5/10 |
| M12 LLM-Selector | 0.111 | 2/10 |

## Pool (oracle input — url/title/snippet)

1. http://ai.googleblog.com/2021/01/google-research-looking-back-at-2020.html
   Google Research: Looking Back at 2020, and Forward to 2021
   ai.googleblog.com

2. http://keg.cs.tsinghua.edu.cn/jietang/publications/TKDE21-Liu-et-al-Self-supervised-Learning-Generative-or-Contrastive.pdf
   PDF Self-supervised Learning: Generative or Contrastive
   Self-supervised representation learning leverages input data itself as supervision and benefits almost all types of downstream tasks. In this survey, we take a look into new self-supervised learning m

3. http://proceedings.mlr.press/v119/chen20j.html
   A Simple Framework for Contrastive Learning of Visual
   We simplify recently proposed contrastive self-supervised learning algorithms without requiring specialized architectures or a memory bank.

4. https://aclanthology.org/2021.findings-emnlp.3.pdf
   Self-supervised Contrastive Cross-Modality ...
   Self-supervised Contrastive Cross-Modality ...ACL Anthologyhttps://aclanthology.org › 2021.findings-emnlp.3...ACL Anthologyhttps://aclanthology.org › 2021.findings-emnlp.3...PDFby C You · 2021 · Cited

5. https://aclanthology.org/2021.findings-emnlp.3/
   Self-supervised Contrastive Cross-Modality Representation
   ... we propose novel training schemes for spoken question answering with a self-supervised training stage and a contrastive representation learning stage.

6. https://arxiv.org/abs/2004.11362
   [2004.11362] Supervised Contrastive Learning
   Abstract: Contrastive learning applied to self-supervised representation learning has seen a resurgence in recent years, leading to state of the art ...

7. https://arxiv.org/abs/2103.14005
   Contrasting Contrastive Self-Supervised Representation ...
   Web resultsContrasting Contrastive Self-Supervised Representation ...arXivhttps://arxiv.org › csarXivhttps://arxiv.org › csby K Kotar · 2021 · Cited by 66 — In this paper, we analyze contrastive appro

8. https://arxiv.org/abs/2203.07004
   [2203.07004] Rethinking Minimal Sufficient Representation in
   Abstract: Contrastive learning between different views of the data achieves outstanding success in the field of self-supervised representation ...

9. https://arxiv.org/pdf/2510.10572
   Understanding Self-supervised Contrastive Learning through Supervised ...
   Our derivation naturally introduces the concepts of prototype representation bias and a balanced contrastive loss, which help explain and improve the behavior of self-supervised learning algorithms. W

10. https://collab.dvb.bayern/download/attachments/73379800/DLMA_Topic8_Manuel_Schreiber_07_%20July_2022.pdf?version=1&modificationDate=1657188497420&api=v2
   Topic 8: Contrastive Learning/Trends in Self- Supervised ...
   Topic 8: Contrastive Learning/Trends in Self- Supervised ...BayernCollabhttps://collab.dvb.bayern › download › attachmentsBayernCollabhttps://collab.dvb.bayern › download › attachmentsPDF6 Jul 2022 — 

11. https://doi.org/10.1007/978-3-031-43907-0_58
   vox2vec: A Framework for Self-supervised Contrastive Learning of Voxel-Level Representations in Medi
   

12. https://doi.org/10.1016/j.sigpro.2021.108310
   Negative sampling strategies for contrastive self-supervised learning of graph representations
   Hafidi, H. et al. (2022), Signal Processing

13. https://doi.org/10.1038/s42256-022-00447-x
   Molecular contrastive learning of representations via graph neural networks
   (Cited 781×)

14. https://doi.org/10.1101/2020.09.04.283929
   Self-Supervised Contrastive Learning of Protein Representations By Mutual Information Maximization
   Abstract Pretrained embedding representations of biological sequences which capture meaningful properties can alleviate many problems associated with supervised learning in biology. We apply the princ

15. https://doi.org/10.1109/cvprw53098.2021.00129
   Self-Supervised Learning of Remote Sensing Scene Representations Using Contrastive Multiview Coding
   Stojnic, V. et al. (2021), 2021 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)

16. https://doi.org/10.1109/iccv48922.2021.00784
   Contrast and Order Representations for Video Self-supervised Learning
   This paper studies the problem of learning self-supervised representations on videos. In contrast to image modality that only requires appearance information on objects or scenes, video needs to furth

17. https://doi.org/10.1109/iccv48922.2021.01000
   Self-Supervised Visual Representations Learning by Contrastive Mask Prediction
   Advanced self-supervised visual representation learning methods rely on the instance discrimination (ID) pretext task. We point out that the ID task has an implicit semantic consistency (SC) assumptio

18. https://doi.org/10.1109/slt54892.2023.10022552
   CCC-WAV2VEC 2.0: Clustering AIDED Cross Contrastive Self-Supervised Learning of Speech Representatio
   Lodagala, V. et al. (2023), 2022 IEEE Spoken Language Technology Workshop (SLT)

19. https://doi.org/10.2139/ssrn.4967469
   Self-Supervised Contrastive Learning of Multiple Molecular Graph Representations for Molecular Prope
   yunwu, l. et al. (2024)

20. https://doi.org/10.2139/ssrn.5095806
   Contrastive Learning with Only Positive Pairs for Enhancing Content Representations of Self-Supervis
   Meghanani, A. et al. (2025)

21. https://doi.org/10.21437/interspeech.2022-11141
   Non-contrastive self-supervised learning of utterance-level speech representations
   Cho, J. et al. (2022), Interspeech 2022

22. https://doi.org/10.32470/uqprhu8
   Human-aligned Universal Audio Representations with Contrastive-Equivariant Self-Supervised Learning
   Griffith, I. et al. (2026), Proceedings of Cognitive Computational Neuroscience 2026

23. https://doi.org/10.3390/technologies9010002
   A Survey on Contrastive Self-Supervised Learning
   Self-supervised learning has gained popularity because of its ability to avoid the cost of annotating large-scale datasets. It is capable of adopting self-defined pseudolabels as supervision and use t

24. https://doi.org/10.36227/techrxiv.16828363
   SELF-SUPERVISED ACOUSTIC ANOMALY DETECTION VIA CONTRASTIVE LEARNING
   We propose an acoustic anomaly detection algorithm based on the framework of contrastive learning. Contrastive learning is a recently proposed self-supervised approach that has shown promising results

25. https://doi.org/10.48550/arxiv.2002.05709
   A Simple Framework for Contrastive Learning of Visual Representations
   This paper presents SimCLR: a simple framework for contrastive learning of visual representations. We simplify recently proposed contrastive self-supervised learning algorithms without requiring speci

26. https://doi.org/10.48550/arxiv.2007.08025
   GraphCL: Contrastive Self-Supervised Learning of Graph Representations
   We propose Graph Contrastive Learning (GraphCL), a general framework for learning node representations in a self supervised manner. GraphCL learns node embeddings by maximizing the similarity between 

27. https://doi.org/10.57702/iuuvgtaz
   A simple framework for contrastive learning of visual representations
   This paper presents SimCLR: a simple framework for contrastive learning of visual representations. We simplify recently proposed contrastive self-supervised learning algorithms without requiring speci

28. https://doi.org/10.59275/j.melba.2022-f9a1
   Learning Representations with Contrastive Self-Supervised Learning for Histopathology Applications
   Unsupervised learning has made substantial progress over the last few years, especially by means of contrastive self-supervised learning. The dominating dataset for benchmarking self-supervised learni

29. https://doi.org/10.7717/peerjcs.1045/table-5
   Table 5: Summary of contrastive self-supervised learning methods in medical imaging.
   

30. https://eprints.gla.ac.uk/293121/
   Focalized contrastive view-invariant learning for
   ... self-supervised framework called Focalized Contrastive View-invariant Learning (FoCoViL), which significantly suppresses the view-specific information ...

31. https://eugeneyan.com/writing/llm-patterns/
   Patterns for Building LLM-based Systems & Products
   eugeneyan.com

32. https://feichtenhofer.github.io/eccv2022-ssl-tutorial/Tutorial_files/slides/contrastive-learning-ECCV-tutorial_ting_Chen.pdf
   contrastive learning (ECCV tutorial)
   contrastive learning (ECCV tutorial)GitHubhttps://feichtenhofer.github.io › slides › contrastiv...GitHubhttps://feichtenhofer.github.io › slides › contrastiv...PDF○ Contrastive learning is a family of

33. https://github.com/zziz/pwc
   Papers with Code
   github.com/zziz

34. https://ieeexplore.ieee.org/document/9462394
   Self-Supervised Learning: Generative or Contrastive
   Self-supervised representation learning leverages input data itself as supervision and benefits almost all types of downstream tasks. In this survey, we take a look into new self-supervised learning m

35. https://ieeexplore.ieee.org/iel7/9709627/9709628/09711402.pdf
   Contrasting Contrastive Self-Supervised Representation ...
   Contrasting Contrastive Self-Supervised Representation ...IEEEhttps://ieeexplore.ieee.org › iel7IEEEhttps://ieeexplore.ieee.org › iel7by K Kotar · 2021 · Cited by 66 — In this paper, we analyze contra

36. https://jonathanbgn.com/2021/10/30/hubert-visually-explained.html
   HuBERT: How to Apply BERT to Speech, Visually Explained
   jonathanbgn.com

37. https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/
   Prompt Engineering
   lilianweng.github.io

38. https://link.springer.com/content/pdf/10.1007/s13735-022-00245-6.pdf
   PDF Contrastive Self-supervised Learning: Review, Progress, Challenges ...
   With the help of self-supervised methods, deep learning progresses with-out expensive annotations and learns feature representation where data serve as supervision. Autoencoders and exten-sions, Deep 

39. https://marslanm.github.io/assets/pdf/Contrastive_Self-Supervised_Learning_A_Survey_on_Different_Architectures.pdf
   PDF Contrastive Self-Supervised Learning: A Survey on Different Architectures
   Recently the research community shifted to integrated method of generative and contrastive techniques known as Self-Supervised Learning (SSL) [3]. Generally, SSL based approaches mitigate the challeng

40. https://nips.cc/media/neurips-2021/Slides/21895.pdf
   Self-Supervised Learning - Self-Prediction and Contrastive ...
   Self-Supervised Learning - Self-Prediction and Contrastive ...NeurIPS 2026https://nips.cc › media › neurips-2021 › SlidesNeurIPS 2026https://nips.cc › media › neurips-2021 › SlidesPDFSelf-Supervised L

41. https://ojs.aaai.org/index.php/AAAI/article/view/17556
   Self-supervised Pre-training and Contrastive Representation
   Self-supervised Pre-training and Contrastive Representation Learning for Multiple-choice Video QA  ... self-supervised pre-training stage and a ...

42. https://openaccess.thecvf.com/content/CVPR2024/papers/Li_Self-Supervised_Representation_Learning_from_Arbitrary_Scenarios_CVPR_2024_paper.pdf
   PDF Self-Supervised Representation Learning from Arbitrary Scenarios
   Abstract Current self-supervised methods can primarily be cate-gorized into contrastive learning and masked image mod-eling. Extensive studies have demonstrated that combining these two approaches can

43. https://openaccess.thecvf.com/content/ICCV2021/papers/Kotar_Contrasting_Contrastive_Self-Supervised_Representation_Learning_Pipelines_ICCV_2021_paper.pdf
   Contrasting Contrastive Self-Supervised Representation ...
   Web resultsContrasting Contrastive Self-Supervised Representation ...The Computer Vision Foundationhttps://openaccess.thecvf.com › content › papersThe Computer Vision Foundationhttps://openaccess.thec

44. https://openai.com/blog/image-gpt/
   Image GPT: model trained on pixel sequences can generate coherent image completions
   openai.com

45. https://people.idsia.ch/~juergen/deep-learning-history.html
   Annotated history of modern AI and deep neural networks
   people.idsia.ch

46. https://proceedings.mlr.press/v119/chen20j.html
   A Simple Framework for Contrastive Learning of Visual
   We simplify recently proposed contrastive self-supervised learning algorithms without requiring specialized architectures or a memory bank.

47. https://proceedings.mlr.press/v119/chen20j/chen20j.pdf
   PDF A Simple Framework for Contrastive Learning of Visual Representations
   Abstract This paper presents SimCLR: a simple framework for contrastive learning of visual representations. We simplify recently proposed contrastive self-supervised learning algorithms without requir

48. https://proceedings.neurips.cc/paper_files/paper/2020/file/d89a66c7c80a29b1bdbab0f2a1a94af8-Paper.pdf
   Supervised Contrastive Learning
   Supervised Contrastive LearningNeurIPS 2026https://proceedings.neurips.cc › paper › fileNeurIPS 2026https://proceedings.neurips.cc › paper › filePDFby P Khosla · 2020 · Cited by 8538 — Contrastive lea

49. https://scholar.google.de/scholar?q=contrastive+learning+self-supervised+representations+pdf&hl=en&as_sdt=0&as_vis=1&oi=scholart
   Scholarly articles for contrastive learning self-supervised representations pdf
   Scholarly articles for contrastive learning self-supervised representations pdfSelf-supervised learning: Generative or contrastive - ‎Liu - Cited by 3037A survey on contrastive self-supervised learnin

50. https://sigport.org/documents/contrastive-separative-coding-self-supervised-representation-learning
   CONTRASTIVE SEPARATIVE CODING FOR SELF-SUPERVISED
   ... CONTRASTIVE SEPARATIVE CODING FOR ... TY - DATA T1 - CONTRASTIVE SEPARATIVE CODING FOR SELF-SUPERVISED REPRESENTATION LEARNING AU - Jun Wang; Max W.

51. https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1225312/pdf
   Contrastive self-supervised representation learning without negative ...
   In this paper, a novel and eective multi -modal feature representation and contrastive self-supervised learning framework is proposed to improve the action recognition performance of models and the ge

52. https://www.ijcai.org/proceedings/2024/0712.pdf
   Contrastive Representation Learning for Self-Supervised ...
   Contrastive Representation Learning for Self-Supervised ...IJCAIhttps://www.ijcai.org › proceedingsIJCAIhttps://www.ijcai.org › proceedingsPDFby Y Niu · Cited by 9 — We propose CoSTC, a contrastive le

53. https://www.media.mit.edu/publications/contrastive-representation-learning-for-electroencephalogram-classification/
   Contrastive Representation Learning for Electroencephalogram
   We present a framework for learning representations from EEG signals via contrastive learning. ... supervised models on SEED and SleepEDF and self ...

54. https://www.melba-journal.org/papers/2022:023.html
   MELBA – Learning Representations with Contrastive
   Using SimCLR and H& stained images as a representative setting for contrastive self-supervised learning in histopathology, we bring forward a number ...

55. https://www.nature.com/articles/s41586-023-06004-9
   Faster sorting algorithms discovered using deep reinforcement learning
   nature.com

56. https://www.researchgate.net/publication/360867376_Self-Supervised_Contrastive_Representation_Learning_in_Computer_Vision
   (PDF) Self-Supervised Contrastive Representation ...
   (PDF) Self-Supervised Contrastive Representation ...ResearchGatehttps://www.researchgate.net › ... › LearningResearchGatehttps://www.researchgate.net › ... › LearningContrastive learning, a self-super

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
   
