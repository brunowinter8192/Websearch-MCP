<!-- source: https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms -->

Skip to contentHomeAboutArchiveSearch
The Toilet Paper
# Comparing algorithms for extracting content from web pages

Published 
    3 Nov 2024

Written by 
    Chun Fei Lung
This study pits 14 open-source main content extractors against each other and arrives at a somewhat surprising conclusion. 
It’s kind of a scrapeheap challenge
  1. Back to top
  2. Summary


The World Wide Web contains a wealth of information in the form of HTML web pages. Extracting information from web pages using scraping tools is not an easy task. While HTML web pages are technically machine-readable, in practice they often might as well be considered unstructured.
This is because web pages don’t just include the information that you need, but also a lot of secondary information in the form of irrelevant boilerplate content, like headers, footers, navigational links, and advertisements. The distinction between main content and boilerplate content isn’t always clear: depending on your use case, page elements like comments or the “About the article” box below might be considered part of either category.
## About the article  
| Title | An empirical comparison of web content extraction algorithms |  
| --- | --- |  
| Year  | 2023 |  
| Author(s) | 
  1. Janek Bevendorff (Bauhaus-Universität Weimar)
  2. Sanket Gupta (
  3. Johannes Kiesel (
  4. Benno Stein (

 |  
| Venue | International ACM SIGIR Conference on Research and Development in Information Retrieval |  
Many main content extraction systems have been written over the past decades, but the algorithms used generally fall into one of two categories:
  * **Heuristic approaches** use heuristic rules (often in the form of trees) to identify one or more blocks of main content. While these rules are efficient to execute, they rely heavily on human expertise for their design.
Many heuristics are based on the assumption that the markup for main content contains fewer HTML tags than that of boilerplate content, or similar assumptions based on the ratio between words and child nodes.
Systems in this category can often be used on all web pages (albeit with mixed results), like Mozilla’s Readability extractor. Some, like Fundus, are designed to extract main content from specific news websites.
  * **Machine learning approaches** use machine learning to classify regions on a web page as main or boilerplate content. Boilerpipe, the first system to use this approach, used structure, text, and text density features. Newer systems are often based on sequence labeling methods and deep neural networks. Some approaches even render web pages in order to extract visual features!


Although a lot of work has gone into developing better main content extraction systems, relatively limited effort has been spent on developing resources for reproducible experiments. Most systems are only evaluated using small datasets. Systems produced outside of academia are often not evaluated at all and are sometimes ignored entirely in evaluation studies.
The authors of this paper have combined eight common evaluation datasets into one large dataset, which they then used to evaluate 14 main content extraction systems:  
| Extractor  | Language  | Approach |  
| --- | --- | --- |  
| BTE  | Python  | Heuristic: HTML tag distribution |  
| Goose3  | Python  | Heuristic: rule-based |  
| jusText  | Python  | Heuristic: rule-based |  
| Newspaper3k  | Python  | Heuristic: rule-based (for news) |  
| Readability  | JavaScript  | Heuristic: rule-based |  
| Resiliparse  | Python  | Heuristic: rule-based |  
| Trafilatura  | Python  | Heuristic: rule-based |  
| news-please  | Python  | Meta heuristic: rule-based (for news) |  
| Boilerpipe  | Java  | AI: text node classification |  
| Dragnet  | Python  | AI: text node classification |  
| ExtractNet  | Python  | AI: text node classification |  
| Go DOM Distiller  | Go  | AI: text node classification |  
| BoilerNet  | Python (+JS)  | AI: sequence labeling (LSTM) |  
| Web2Text  | Python  | AI: sequence labeling (HMM+CNN) |  
These 14 extractors are also compared with five HTML-to-text conversion tools that simply extract all text from a web page, as a baseline.
The results show that almost all extractors perform reasonably well on simple web pages that largely consist of main content. This is even true for the basic HTML conversion tools due to their near-perfect recall.
The differences between extractors and simple converters become larger on more complex pages. Baseline performance is still pretty high with an F1F_1F1​ score of 0.738, which suggests that most pages in the dataset primarily consist of main content.
No single extractor performs best for all page complexity levels, but there are a few extractors that do slightly better than others. For instance, Readability has the highest median score (0.970) and has the highest level of predictability, while Trafilatura has the best overall mean performance (0.883). Most models have their own strengths and weaknesses. Readability is a notable exception, as it appears to work well with all types of web pages.
Another interesting observation is that heuristic extractors perform the best and are most robust across the board, whereas the performance of large neural models is surprisingly bad – especially on the most complex pages for which they were primarily designed!
To see whether extraction performance could be further improved, the researchers defined three ensembles on top of the individual extraction systems:
  * **Majority vote** : For each token in the HTML, check whether the five tokens to its left and right appear in the extractor’s output. If so, the extractor “votes” for the token. If at least two thirds of systems (including baseline HTML-to-text converters) vote for a token, it is considered to be part of the main content.
  * **Majority vote best** : This ensemble is based on the same principle as the majority vote, except now only the nine best-performing main content extractors are included.
  * **Majority vote best (weighted)** : The same nine content extractors get to vote for tokens, but now votes from the three best extractors (Readability, Trafilatura, and Goose3) count double.


All ensembles outperform the individual extractors, with the weighted vote ensemble achieving the best results. The complete results are shown in the table below:  
| Model  | Mean  | Median |  
| --- | --- | --- |  
| Prec.  | Recall  |   | Prec.  | Recall  |  |  
| _(Best weighted)_  | 0.922  | **0.912**  | **0.899**  | 0.986  | 0.981  | 0.970 |  
|  _(Best only)_  | 0.926  | 0.892  | 0.889  | 0.992  | 0.976  | 0.973 |  
|  _(Majority all)_  | **0.930**  | 0.879  | 0.885  | 0.996  | 0.971  | **0.974** |  
|  Trafilatura  | 0.913  | 0.895  | 0.883  | 0.989  | 0.965  | 0.957 |  
| Readability  | 0.921  | 0.856  | 0.861  | 0.991  | 0.972  | 0.970 |  
| Resiliparse  | 0.863  | 0.901  | 0.859  | 0.940  | **0.993**  | 0.942 |  
| DOM Distiller  | 0.894  | 0.864  | 0.858  | 0.983  | 0.970  | 0.959 |  
| Web2Text  | 0.797  | 0.944  | 0.841  | 0.885  | 0.984  | 0.917 |  
| Boilerpipe  | 0.908  | 0.825  | 0.834  | 0.973  | 0.966  | 0.946 |  
| Dragnet  | 0.901  | 0.810  | 0.823  | 0.980  | 0.950  | 0.943 |  
| BTE  | 0.796  | 0.897  | 0.817  | 0.927  | 0.965  | 0.936 |  
| Newspaper3k  | 0.896  | 0.803  | 0.816  | 0.994  | 0.961  | 0.958 |  
| news-please  | 0.895  | 0.802  | 0.815  | 0.994  | 0.961  | 0.958 |  
| Goose3  | 0.899  | 0.779  | 0.810  | **0.999**  | 0.919  | 0.940 |  
| BoilerNet  | 0.840  | 0.816  | 0.798  | 0.944  | 0.938  | 0.895 |  
| ExtractNet  | 0.858  | 0.773  | 0.791  | 0.963  | 0.915  | 0.911 |  
| jusText  | 0.794  | 0.769  | 0.759  | 0.949  | 0.921  | 0.904 |  
## Summary
  1. No single main content extractor clearly outperforms the others, although Readability appears to do well most of the time
  2. Heuristic models generally outperform neural models, especially on more complex web pages


## More about information science
Evaluating ontological decisions with OntoCleanA look at domain modelling from an academic perspective. Finding the most common words in a set of texts for a word cloudAlternatively: why word counting is nothing like bean counting. What happened to the Semantic Web?2021 is not the year of the Linux desktop, nor is it the year of the Semantic Web. But as a field of research it is still alive and kicking. 
## More about Python
On the usage of Pythonic idiomsWays to ensure that all code is equal and no code is more equal than others. Five things in Python that I only learned this yearMany people learn Python as their first or second programming language, but only few people bother to master it. What is the best programming language for beginners?This study attempts to provide a more nuanced answer than “JavaScript”, from an educator’s perspective. 
## Chuniversiteit
  * About
  * Portfolio
  * Archive
  * RSS feed
  * Blogroll


## Main sections
  * Career & productivity
  * CS & SE paper summaries
  * Software development
  * DevOps (but mostly Ops)
  * Mildly interesting stuff


## People often view
  * Dutch trains in CSS
  * My curriculum vitae ()
  * My book collection
  * Where to pursue a PhD in SE
  * Conway’s Game of Life


© 2018–2026 Chun Fei Lung. Published from the Netherlands. Almost everything (except for third-party logos, names, etc.) licensed under CC BY-NC.
