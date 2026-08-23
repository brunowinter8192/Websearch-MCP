# Overview Sweep Analysis

**Sweep:** `dev/scrape_pipeline/04_overview_sweep/sweep_outputs/20260506_174432`
**Clean-raw baseline:** `dev/scrape_pipeline/03_cleanup/cleaned_outputs/20260506_165915`
**Configs analyzed:** 36

## Cross-Config Ranking (by median F1)

| # | Config | Filter | Source | Selector | Median F1 | Min F1 | Recall | Precision | bytes Δ | Fails | Time |
|---|--------|--------|--------|----------|-----------|--------|--------|-----------|---------|-------|------|
| 1 | `none_cleaned_html_cookies+sphinx` | none | cleaned_html | cookies+sphinx | 0.981 | 0.496 | 0.991 | 0.889 | +1,358 | 0 | 13s |
| 2 | `none_cleaned_html_cookies` | none | cleaned_html | cookies | 0.976 | 0.481 | 0.995 | 0.884 | +1,476 | 0 | 7s |
| 3 | `none_raw_html_cookies` | none | raw_html | cookies | 0.918 | 0.310 | 0.948 | 0.832 | +1,460 | 0 | 5s |
| 4 | `none_raw_html_cookies+sphinx` | none | raw_html | cookies+sphinx | 0.918 | 0.310 | 0.948 | 0.832 | +1,460 | 0 | 5s |
| 5 | `prune_030_cleaned_html_cookies` | prune_030 | cleaned_html | cookies | 0.889 | 0.455 | 0.819 | 0.906 | -713 | 0 | 9s |
| 6 | `prune_030_cleaned_html_cookies+sphinx` | prune_030 | cleaned_html | cookies+sphinx | 0.889 | 0.455 | 0.819 | 0.912 | -713 | 0 | 5s |
| 7 | `prune_030_raw_html_cookies` | prune_030 | raw_html | cookies | 0.844 | 0.290 | 0.785 | 0.857 | -732 | 1 | 12s |
| 8 | `prune_030_raw_html_cookies+sphinx` | prune_030 | raw_html | cookies+sphinx | 0.844 | 0.290 | 0.785 | 0.857 | -732 | 1 | 7s |
| 9 | `prune_048_cleaned_html_cookies+sphinx` | prune_048 | cleaned_html | cookies+sphinx | 0.754 | 0.087 | 0.584 | 0.747 | -2,792 | 2 | 6s |
| 10 | `prune_048_cleaned_html_cookies` | prune_048 | cleaned_html | cookies | 0.748 | 0.087 | 0.584 | 0.745 | -2,792 | 2 | 10s |
| 11 | `prune_048_raw_html_cookies` | prune_048 | raw_html | cookies | 0.748 | 0.087 | 0.586 | 0.731 | -2,918 | 3 | 11s |
| 12 | `prune_048_raw_html_cookies+sphinx` | prune_048 | raw_html | cookies+sphinx | 0.748 | 0.087 | 0.586 | 0.731 | -2,918 | 3 | 5s |
| 13 | `prune_060_cleaned_html_cookies` | prune_060 | cleaned_html | cookies | 0.601 | 0.125 | 0.522 | 0.707 | -4,138 | 3 | 10s |
| 14 | `prune_060_cleaned_html_cookies+sphinx` | prune_060 | cleaned_html | cookies+sphinx | 0.601 | 0.125 | 0.522 | 0.709 | -4,138 | 3 | 9s |
| 15 | `prune_060_raw_html_cookies` | prune_060 | raw_html | cookies | 0.532 | 0.125 | 0.529 | 0.701 | -4,011 | 3 | 28s |
| 16 | `prune_060_raw_html_cookies+sphinx` | prune_060 | raw_html | cookies+sphinx | 0.532 | 0.125 | 0.529 | 0.701 | -4,011 | 3 | 11s |
| 17 | `prune_075_cleaned_html_cookies` | prune_075 | cleaned_html | cookies | 0.471 | 0.131 | 0.423 | 0.678 | -5,035 | 4 | 4s |
| 18 | `prune_075_cleaned_html_cookies+sphinx` | prune_075 | cleaned_html | cookies+sphinx | 0.471 | 0.131 | 0.423 | 0.678 | -5,035 | 4 | 4s |
| 19 | `prune_060_fit_html_cookies` | prune_060 | fit_html | cookies | 0.461 | 0.089 | 0.327 | 0.518 | -6,535 | 8 | 21s |
| 20 | `prune_060_fit_html_cookies+sphinx` | prune_060 | fit_html | cookies+sphinx | 0.461 | 0.089 | 0.327 | 0.518 | -6,535 | 8 | 19s |
| 21 | `prune_048_fit_html_cookies` | prune_048 | fit_html | cookies | 0.450 | 0.087 | 0.349 | 0.511 | -6,373 | 7 | 17s |
| 22 | `prune_048_fit_html_cookies+sphinx` | prune_048 | fit_html | cookies+sphinx | 0.450 | 0.087 | 0.349 | 0.511 | -6,373 | 7 | 9s |
| 23 | `prune_030_fit_html_cookies` | prune_030 | fit_html | cookies | 0.448 | 0.148 | 0.398 | 0.538 | -6,341 | 4 | 16s |
| 24 | `prune_030_fit_html_cookies+sphinx` | prune_030 | fit_html | cookies+sphinx | 0.448 | 0.148 | 0.398 | 0.538 | -6,341 | 4 | 7s |
| 25 | `none_fit_html_cookies` | none | fit_html | cookies | 0.437 | 0.163 | 0.435 | 0.455 | -5,219 | 4 | 7s |
| 26 | `none_fit_html_cookies+sphinx` | none | fit_html | cookies+sphinx | 0.437 | 0.163 | 0.435 | 0.455 | -5,219 | 4 | 11s |
| 27 | `prune_075_raw_html_cookies` | prune_075 | raw_html | cookies | 0.385 | 0.129 | 0.410 | 0.663 | -5,047 | 5 | 6s |
| 28 | `prune_075_raw_html_cookies+sphinx` | prune_075 | raw_html | cookies+sphinx | 0.385 | 0.129 | 0.410 | 0.663 | -5,047 | 5 | 9s |
| 29 | `prune_075_fit_html_cookies` | prune_075 | fit_html | cookies | 0.300 | 0.130 | 0.274 | 0.524 | -7,021 | 8 | 6s |
| 30 | `prune_075_fit_html_cookies+sphinx` | prune_075 | fit_html | cookies+sphinx | 0.300 | 0.130 | 0.274 | 0.524 | -7,021 | 8 | 8s |
| 31 | `bm25_raw_html_cookies` | bm25 | raw_html | cookies | 0.061 | 0.000 | 0.077 | 0.389 | -13,571 | 16 | 21s |
| 32 | `bm25_raw_html_cookies+sphinx` | bm25 | raw_html | cookies+sphinx | 0.061 | 0.000 | 0.077 | 0.389 | -13,571 | 16 | 21s |
| 33 | `bm25_cleaned_html_cookies` | bm25 | cleaned_html | cookies | 0.047 | 0.000 | 0.042 | 0.418 | -14,810 | 16 | 5s |
| 34 | `bm25_cleaned_html_cookies+sphinx` | bm25 | cleaned_html | cookies+sphinx | 0.047 | 0.000 | 0.042 | 0.418 | -14,810 | 16 | 17s |
| 35 | `bm25_fit_html_cookies` | bm25 | fit_html | cookies | 0.041 | 0.000 | 0.036 | 0.370 | -15,558 | 16 | 15s |
| 36 | `bm25_fit_html_cookies+sphinx` | bm25 | fit_html | cookies+sphinx | 0.041 | 0.000 | 0.036 | 0.370 | -15,558 | 16 | 9s |

## Per-Shape Median F1 (top 10 configs)

Shape rows × top-10 configs cols. Catches per-shape config differences (e.g. best for Blog ≠ best for Forum).

| Shape | #1 | #2 | #3 | #4 | #5 | #6 | #7 | #8 | #9 | #10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Blog | 0.98 | 0.98 | 0.97 | 0.97 | 0.86 | 0.86 | 0.86 | 0.86 | 0.80 | 0.79 |
| Forum-Thread | 0.99 | 0.99 | 0.87 | 0.87 | 0.98 | 0.98 | 0.86 | 0.86 | 0.11 | 0.11 |
| Index-Aggregator | 0.97 | 0.96 | 0.85 | 0.85 | 0.89 | 0.89 | 0.75 | 0.75 | 0.54 | 0.54 |
| Paper-Landing | 0.88 | 0.91 | 0.88 | 0.88 | 0.93 | 0.93 | 0.91 | 0.91 | 0.79 | 0.79 |
| Repo-Heavy-Chrome | 0.87 | 0.87 | 0.87 | 0.87 | 0.96 | 0.96 | 0.96 | 0.96 | 0.94 | 0.94 |

Top-10 column legend:
- **#1** = `none_cleaned_html_cookies+sphinx`
- **#2** = `none_cleaned_html_cookies`
- **#3** = `none_raw_html_cookies`
- **#4** = `none_raw_html_cookies+sphinx`
- **#5** = `prune_030_cleaned_html_cookies`
- **#6** = `prune_030_cleaned_html_cookies+sphinx`
- **#7** = `prune_030_raw_html_cookies`
- **#8** = `prune_030_raw_html_cookies+sphinx`
- **#9** = `prune_048_cleaned_html_cookies+sphinx`
- **#10** = `prune_048_cleaned_html_cookies`

## Diff Drill-Down — Top 3 Configs

### Config: `none_cleaned_html_cookies+sphinx`
Filter: none | Source: cleaned_html | Selector: cookies+sphinx
Median F1: 0.981 | Recall: 0.991 | Precision: 0.889

#### Paper-Landing — `https://arxiv.org/abs/2410.19771`
F1: 0.874 | recall: 0.926 | precision: 0.829 | bytes Δ: +888

```diff
--- cleanraw
+++ candidate
@@ -1,5 +1,25 @@
 <!-- source: https://arxiv.org/abs/2410.19771 -->
 
+[Skip to main content](https://arxiv.org/abs/2410.19771#content)
+[![Cornell University](https://arxiv.org/static/browse/0.3.4/images/icons/cu/cornell-reduced-white-SMALL.svg)](https://www.cornell.edu/)
+[Learn about arXiv becoming an independent nonprofit.](https://tech.cornell.edu/arxiv/)
+We gratefully acknowledge support from the Simons Foundation, [member institutions](https://info.arxiv.org/about/ourmembers.html), and all contributors. [Donate](https://info.arxiv.org/about/donate.html)
+[](https://arxiv.org/IgnoreMe)
+[![arxiv logo](https://arxiv.org/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)](https://arxiv.org/) > [cs](https://arxiv.org/list/cs/recent) > arXiv:2410.19771 
+[Help](https://info.arxiv.org/help) | [Advanced Search](https://arxiv.org/search/advanced)
+All fields Title Author Abstract Comments Journal reference ACM classification MSC classification Report number arXiv identifier DOI ORCID arXiv author ID Help pages Full text
+Search
+[![arXiv logo](https://arxiv.org/static/browse/0.3.4/images/arxiv-logomark-small-white.svg)](https://arxiv.org/)
+[ ![Cornell University Logo](https://arxiv.org/static/browse/0.3.4/images/icons/cu/cornell-reduced-white-SMALL.svg) ](https://www.cornell.edu/)
+GO
+## quick links
+  * [Login](https://arxiv.org/login)
+  * [Help Pages](https://info.arxiv.org/help)
+  * [About](https://info.arxiv.org/about)
 
+
+# Computer Science > Information Retrieval
+**arXiv:2410.19771** (cs) 
+[Submitted on 13 Oct 2024]
 #  Title:Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles
 Authors:[Sriharsha Hatwar](https://arxiv.org/search/cs?searchtype=author&query=Hatwar,+S), [Virginia Partridge](https://arxiv.org/search/cs?searchtype=author&query=Partridge,+V), [Rahul Bhargava](https://arxiv.org/search/cs?searchtype=author&query=Bhargava,+R), [Fernando Bermejo](https://arxiv.org/search/cs?searchtype=author&query=Bermejo,+F)
@@ -101,16 +121,2 @@
 Have an idea for a project that will add value for arXiv's community? [**Learn more about arXivLabs**](https://info.arxiv.org/labs/index.html).
 [Which authors of this paper are endorsers?](https://arxiv.org/auth/show-endorsers/2410.19771) | [Disable MathJax](javascript:setMathjaxCookie\(\)) ([What is MathJax?](https://info.arxiv.org/help/mathjax.html)) 
-  * [About](https://info.arxiv.org/about)
-  * [Help](https://info.arxiv.org/help)
-
-
-  * contact arXiv Click here to contact arXiv [ Contact](https://info.arxiv.org/help/contact.html)
-  * subscribe to arXiv mailings Click here to subscribe [ Subscribe](https://info.arxiv.org/help/subscribe)
-
-
-  * [Copyright](https://info.arxiv.org/help/license/index.html)
-  * [Privacy Policy](https://info.arxiv.org/help/policies/privacy_policy.html)
-
-
-  * [Web Accessibility Assistance](https://info.arxiv.org/help/web_accessibility.html)
-  * [arXiv Operational Status ](https://status.arxiv.org)
```

#### Index-Aggregator — `https://adrien.barbaresi.eu/blog/tag/data-mining.html`
F1: 1.000 | recall: 1.000 | precision: 1.000 | bytes Δ: -1

```diff
--- cleanraw
+++ candidate
@@ -1,4 +1,3 @@
 <!-- source: https://adrien.barbaresi.eu/blog/tag/data-mining.html -->
-
 
 ## [An easy way to save time and resources: content-aware URL filtering](https://adrien.barbaresi.eu/blog/easy-content-aware-url-filtering.html)
```

#### Blog — `https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms`
F1: 0.986 | recall: 1.000 | precision: 0.972 | bytes Δ: +509

```diff
--- cleanraw
+++ candidate
@@ -1,5 +1,7 @@
 <!-- source: https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms -->
 
-
+[![Chuniversiteit logomark](https://chuniversiteit.nl/images/static/logomark.png)![Chuniversiteit.nl](https://chuniversiteit.nl/images/static/logotype.png)](https://chuniversiteit.nl/ "Home")
+[Skip to content](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms#main)[Home](https://chuniversiteit.nl/)[About](https://chuniversiteit.nl/about)[Archive](https://chuniversiteit.nl/archive)[Search](https://chuniversiteit.nl/search)
+[The Toilet Paper](https://chuniversiteit.nl/papers)
 # Comparing algorithms for extracting content from web pages 
 
```

#### Forum-Thread — `https://news.ycombinator.com/item?id=40035347`
F1: 0.984 | recall: 1.000 | precision: 0.968 | bytes Δ: +572

```diff
--- cleanraw
+++ candidate
@@ -1,5 +1,10 @@
 <!-- source: https://news.ycombinator.com/item?id=40035347 -->
 
-
+|   
+ | [![](https://news.ycombinator.com/y18.svg)](https://news.ycombinator.com)  | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomments) | [ask](https://news.ycombinator.com/ask) | [show](https://news.ycombinator.com/show) | [jobs](https://news.ycombinator.com/jobs) | [submit](https://news.ycombinator.com/submit)  | [login](https://news.ycombinator.com/login?goto=item%3Fid%3D40035347)  |  
+| --- | --- | --- |  
+ |  
+ |  
+|   
  |   | [](https://news.ycombinator.com/vote?id=40035347&how=up&goto=item%3Fid%3D40035347)  |  [screye](https://news.ycombinator.com/user?id=screye) [on April 14, 2024](https://news.ycombinator.com/item?id=40035347) | [parent](https://news.ycombinator.com/item?id=40033490) | [context](https://news.ycombinator.com/item?id=40033490#40035347) | [favorite](https://news.ycombinator.com/fave?id=40035347&auth=2505d90644bb16ef9a5f86de5764312284bcdd6a) | on: [Show HN: I made a tool to clean and convert any we...](https://news.ycombinator.com/item?id=40033490 "Show HN: I made a tool to clean and convert any webpage to Markdown")   
 Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall) 2. Dropping all the ads/auxilliary content (high precision) 3. And getting the correct layout/section types (formatting) For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job. Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings.  |  
```


### Config: `none_cleaned_html_cookies`
Filter: none | Source: cleaned_html | Selector: cookies
Median F1: 0.976 | Recall: 0.995 | Precision: 0.884

#### Paper-Landing — `https://arxiv.org/abs/2410.19771`
F1: 0.913 | recall: 1.000 | precision: 0.839 | bytes Δ: +1,476

```diff
--- cleanraw
+++ candidate
@@ -1,5 +1,25 @@
 <!-- source: https://arxiv.org/abs/2410.19771 -->
 
+[Skip to main content](https://arxiv.org/abs/2410.19771#content)
+[![Cornell University](https://arxiv.org/static/browse/0.3.4/images/icons/cu/cornell-reduced-white-SMALL.svg)](https://www.cornell.edu/)
+[Learn about arXiv becoming an independent nonprofit.](https://tech.cornell.edu/arxiv/)
+We gratefully acknowledge support from the Simons Foundation, [member institutions](https://info.arxiv.org/about/ourmembers.html), and all contributors. [Donate](https://info.arxiv.org/about/donate.html)
+[](https://arxiv.org/IgnoreMe)
+[![arxiv logo](https://arxiv.org/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)](https://arxiv.org/) > [cs](https://arxiv.org/list/cs/recent) > arXiv:2410.19771 
+[Help](https://info.arxiv.org/help) | [Advanced Search](https://arxiv.org/search/advanced)
+All fields Title Author Abstract Comments Journal reference ACM classification MSC classification Report number arXiv identifier DOI ORCID arXiv author ID Help pages Full text
+Search
+[![arXiv logo](https://arxiv.org/static/browse/0.3.4/images/arxiv-logomark-small-white.svg)](https://arxiv.org/)
+[ ![Cornell University Logo](https://arxiv.org/static/browse/0.3.4/images/icons/cu/cornell-reduced-white-SMALL.svg) ](https://www.cornell.edu/)
+GO
+## quick links
+  * [Login](https://arxiv.org/login)
+  * [Help Pages](https://info.arxiv.org/help)
+  * [About](https://info.arxiv.org/about)
 
+
+# Computer Science > Information Retrieval
+**arXiv:2410.19771** (cs) 
+[Submitted on 13 Oct 2024]
 #  Title:Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles
 Authors:[Sriharsha Hatwar](https://arxiv.org/search/cs?searchtype=author&query=Hatwar,+S), [Virginia Partridge](https://arxiv.org/search/cs?searchtype=author&query=Partridge,+V), [Rahul Bhargava](https://arxiv.org/search/cs?searchtype=author&query=Bhargava,+R), [Fernando Bermejo](https://arxiv.org/search/cs?searchtype=author&query=Bermejo,+F)
@@ -114,3 +134,6 @@
 
   * [Web Accessibility Assistance](https://info.arxiv.org/help/web_accessibility.html)
-  * [arXiv Operational Status ](https://status.arxiv.org)
+  * [arXiv Operational Status ](https://status.arxiv.org)  
+
+
+
```

#### Index-Aggregator — `https://adrien.barbaresi.eu/blog/tag/data-mining.html`
F1: 0.976 | recall: 1.000 | precision: 0.953 | bytes Δ: +366

```diff
--- cleanraw
+++ candidate
@@ -1,3 +1,8 @@
 <!-- source: https://adrien.barbaresi.eu/blog/tag/data-mining.html -->
+
+Toggle navigation [ Bits of Language: corpus linguistics, NLP and text analytics ](https://adrien.barbaresi.eu/blog/)
+  * [Corpus Linguistics](https://adrien.barbaresi.eu/blog/category/corpora.html)
+  * [Tutorials](https://adrien.barbaresi.eu/blog/category/tutorial.html)
+  * [Text Complexity](https://adrien.barbaresi.eu/blog/category/complexity-readability.html)
 
 
```

#### Blog — `https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms`
F1: 0.986 | recall: 1.000 | precision: 0.972 | bytes Δ: +509

```diff
--- cleanraw
+++ candidate
@@ -1,5 +1,7 @@
 <!-- source: https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms -->
 
-
+[![Chuniversiteit logomark](https://chuniversiteit.nl/images/static/logomark.png)![Chuniversiteit.nl](https://chuniversiteit.nl/images/static/logotype.png)](https://chuniversiteit.nl/ "Home")
+[Skip to content](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms#main)[Home](https://chuniversiteit.nl/)[About](https://chuniversiteit.nl/about)[Archive](https://chuniversiteit.nl/archive)[Search](https://chuniversiteit.nl/search)
+[The Toilet Paper](https://chuniversiteit.nl/papers)
 # Comparing algorithms for extracting content from web pages 
 
```

#### Forum-Thread — `https://news.ycombinator.com/item?id=40035347`
F1: 0.984 | recall: 1.000 | precision: 0.968 | bytes Δ: +572

```diff
--- cleanraw
+++ candidate
@@ -1,5 +1,10 @@
 <!-- source: https://news.ycombinator.com/item?id=40035347 -->
 
-
+|   
+ | [![](https://news.ycombinator.com/y18.svg)](https://news.ycombinator.com)  | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomments) | [ask](https://news.ycombinator.com/ask) | [show](https://news.ycombinator.com/show) | [jobs](https://news.ycombinator.com/jobs) | [submit](https://news.ycombinator.com/submit)  | [login](https://news.ycombinator.com/login?goto=item%3Fid%3D40035347)  |  
+| --- | --- | --- |  
+ |  
+ |  
+|   
  |   | [](https://news.ycombinator.com/vote?id=40035347&how=up&goto=item%3Fid%3D40035347)  |  [screye](https://news.ycombinator.com/user?id=screye) [on April 14, 2024](https://news.ycombinator.com/item?id=40035347) | [parent](https://news.ycombinator.com/item?id=40033490) | [context](https://news.ycombinator.com/item?id=40033490#40035347) | [favorite](https://news.ycombinator.com/fave?id=40035347&auth=2505d90644bb16ef9a5f86de5764312284bcdd6a) | on: [Show HN: I made a tool to clean and convert any we...](https://news.ycombinator.com/item?id=40033490 "Show HN: I made a tool to clean and convert any webpage to Markdown")   
 Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall) 2. Dropping all the ads/auxilliary content (high precision) 3. And getting the correct layout/section types (formatting) For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job. Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings.  |  
```


### Config: `none_raw_html_cookies`
Filter: none | Source: raw_html | Selector: cookies
Median F1: 0.918 | Recall: 0.948 | Precision: 0.832

#### Paper-Landing — `https://arxiv.org/abs/2410.19771`
F1: 0.874 | recall: 0.957 | precision: 0.804 | bytes Δ: +1,460

```diff
--- cleanraw
+++ candidate
@@ -1,6 +1,26 @@
 <!-- source: https://arxiv.org/abs/2410.19771 -->
 
+[Skip to main content](https://arxiv.org/abs/2410.19771#content)
+[![Cornell University](https://arxiv.org/static/browse/0.3.4/images/icons/cu/cornell-reduced-white-SMALL.svg)](https://www.cornell.edu/)
+[Learn about arXiv becoming an independent nonprofit.](https://tech.cornell.edu/arxiv/)
+We gratefully acknowledge support from the Simons Foundation, [member institutions](https://info.arxiv.org/about/ourmembers.html), and all contributors. [Donate](https://info.arxiv.org/about/donate.html)
+[](https://arxiv.org/IgnoreMe)
+[![arxiv logo](https://arxiv.org/static/browse/0.3.4/images/arxiv-logo-one-color-white.svg)](https://arxiv.org/) > [cs](https://arxiv.org/list/cs/recent) > arXiv:2410.19771 
+[Help](https://info.arxiv.org/help) | [Advanced Search](https://arxiv.org/search/advanced)
+All fields Title Author Abstract Comments Journal reference ACM classification MSC classification Report number arXiv identifier DOI ORCID arXiv author ID Help pages Full text
+Search
+[![arXiv logo](https://arxiv.org/static/browse/0.3.4/images/arxiv-logomark-small-white.svg)](https://arxiv.org/)
+[ ![Cornell University Logo](https://arxiv.org/static/browse/0.3.4/images/icons/cu/cornell-reduced-white-SMALL.svg) ](https://www.cornell.edu/)
+GO
+## quick links
+  * [Login](https://arxiv.org/login)
+  * [Help Pages](https://info.arxiv.org/help)
+  * [About](https://info.arxiv.org/about)
 
-#  Title:Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles
+
+# Computer Science > Information Retrieval
+**arXiv:2410.19771** (cs) 
+[Submitted on 13 Oct 2024]
+# Title:Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles
 Authors:[Sriharsha Hatwar](https://arxiv.org/search/cs?searchtype=author&query=Hatwar,+S), [Virginia Partridge](https://arxiv.org/search/cs?searchtype=author&query=Partridge,+V), [Rahul Bhargava](https://arxiv.org/search/cs?searchtype=author&query=Bhargava,+R), [Fernando Bermejo](https://arxiv.org/search/cs?searchtype=author&query=Bermejo,+F)
 View a PDF of the paper titled Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles, by Sriharsha Hatwar and 3 other authors
@@ -10,6 +30,6 @@
 | --- | --- |  
 | Cite as:  | [arXiv:2410.19771](https://arxiv.org/abs/2410.19771) [cs.IR]  |  
-|   | (or  [arXiv:2410.19771v1](https://arxiv.org/abs/2410.19771v1) [cs.IR] for this version)   |  
-|   |  <https://doi.org/10.48550/arXiv.2410.19771> Focus to learn more  |  
+|    | (or  [arXiv:2410.19771v1](https://arxiv.org/abs/2410.19771v1) [cs.IR] for this version)   |  
+|    |  <https://doi.org/10.48550/arXiv.2410.19771> Focus to learn more arXiv-issued DOI via DataCite  |  
 ## Submission history
 From: Sriharsha Hatwar Mr [[view email](https://arxiv.org/show-email/5118146c/2410.19771)]   
@@ -31,5 +51,5 @@
 ### Current browse context:
 cs.IR
-[< prev](https://arxiv.org/prevnext?id=2410.19771&function=prev&context=cs.IR "previous in cs.IR \(accesskey p\)") |  [next >](https://arxiv.org/prevnext?id=2410.19771&function=next&context=cs.IR "next in cs.IR \(accesskey n\)")   
+[< prev](https://arxiv.org/prevnext?id=2410.19771&function=prev&context=cs.IR "previous in cs.IR \(accesskey p\)")   |   [next >](https://arxiv.org/prevnext?id=2410.19771&function=next&context=cs.IR "next in cs.IR \(accesskey n\)")   
 
 [new](https://arxiv.org/list/cs.IR/new) |  [recent](https://arxiv.org/list/cs.IR/recent) | [2024-10](https://arxiv.org/list/cs.IR/2024-10)
@@ -50,5 +70,5 @@
 Data provided by: 
 ### Bookmark
-[ ![BibSonomy](https://arxiv.org/static/browse/0.3.4/images/icons/social/bibsonomy.png) ](http://www.bibsonomy.org/BibtexHandler?requTask=upload&url=https://arxiv.org/abs/2410.19771&description=Author%20Unknown:%20Evaluating%20Performance%20of%20Author%20Extraction%20Libraries%20on%20Global%20Online%20News%20Articles "Bookmark on BibSonomy") [ ![Reddit](https://arxiv.org/static/browse/0.3.4/images/icons/social/reddit.png) ](https://reddit.com/submit?url=https://arxiv.org/abs/2410.19771&title=Author%20Unknown:%20Evaluating%20Performance%20of%20Author%20Extraction%20Libraries%20on%20Global%20Online%20News%20Articles "Bookmark on Reddit")
+[ ![BibSonomy](https://arxiv.org/static/browse/0.3.4/images/icons/social/bibsonomy.png) ](http://www.bibsonomy.org/BibtexHandler?requTask=upload&url=https://arxiv.org/abs/2410.19771&description=Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles "Bookmark on BibSonomy") [ ![Reddit](https://arxiv.org/static/browse/0.3.4/images/icons/social/reddit.png) ](https://reddit.com/submit?url=https://arxiv.org/abs/2410.19771&title=Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles "Bookmark on Reddit")
 Bibliographic Tools
 # Bibliographic and Citation Tools
@@ -105,6 +125,6 @@
 
 
-  * contact arXiv Click here to contact arXiv [ Contact](https://info.arxiv.org/help/contact.html)
-  * subscribe to arXiv mailings Click here to subscribe [ Subscribe](https://info.arxiv.org/help/subscribe)
+  * contact arXivClick here to contact arXiv [ Contact](https://info.arxiv.org/help/contact.html)
+  * subscribe to arXiv mailingsClick here to subscribe [ Subscribe](https://info.arxiv.org/help/subscribe)
... [diff truncated, showing first 60 lines] ...
```

#### Index-Aggregator — `https://adrien.barbaresi.eu/blog/tag/data-mining.html`
F1: 0.928 | recall: 0.951 | precision: 0.906 | bytes Δ: +396

```diff
--- cleanraw
+++ candidate
@@ -1,3 +1,9 @@
 <!-- source: https://adrien.barbaresi.eu/blog/tag/data-mining.html -->
+
+Toggle navigation [ Bits of Language: corpus linguistics, NLP and text analytics ](https://adrien.barbaresi.eu/blog/)
+  * [Corpus Linguistics](https://adrien.barbaresi.eu/blog/category/corpora.html)
+  * [Tutorials](https://adrien.barbaresi.eu/blog/category/tutorial.html)
+  * [Text Complexity](https://adrien.barbaresi.eu/blog/category/complexity-readability.html)
+
 
 
@@ -78,7 +84,7 @@
 Welcome to my academic blog about web corpora, text mining, computational linguistics and digital humanities. 
   * #### Social
-    * [](https://www.twitter.com/adbarbaresi)
-    * [](https://www.linkedin.com/in/adrienbarbaresi)
-    * [](https://github.com/adbar/)
+    * [__Twitter](https://www.twitter.com/adbarbaresi)
+    * [__LinkedIn](https://www.linkedin.com/in/adrienbarbaresi)
+    * [__GitHub](https://github.com/adbar/)
   * #### [Tags](https://adrien.barbaresi.eu/blog/)
     * [code snippet](https://adrien.barbaresi.eu/blog/tag/code-snippet.html)
@@ -102,3 +108,3 @@
 © 2021 Adrien Barbaresi · Powered by [pelican-bootstrap3](https://github.com/getpelican/pelican-themes/tree/master/pelican-bootstrap3), [Pelican](http://docs.getpelican.com/), [Bootstrap](http://getbootstrap.com)
 [![Creative Commons License](https://i.creativecommons.org/l/by-sa/4.0/80x15.png)](https://creativecommons.org/licenses/by-sa/4.0/deed.en) Content licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/deed.en), except where indicated otherwise. 
-[Back to top](https://adrien.barbaresi.eu/blog/tag/data-mining.html#)
+__[Back to top](https://adrien.barbaresi.eu/blog/tag/data-mining.html#)
```

#### Blog — `https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms`
F1: 0.953 | recall: 0.971 | precision: 0.935 | bytes Δ: +627

```diff
--- cleanraw
+++ candidate
@@ -1,9 +1,11 @@
 <!-- source: https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms -->
 
-
-# Comparing algorithms for extracting content from web pages 
+[![Chuniversiteit logomark](https://chuniversiteit.nl/images/static/logomark.png)![Chuniversiteit.nl](https://chuniversiteit.nl/images/static/logotype.png)](https://chuniversiteit.nl/ "Home")
+[Skip to content](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms#main)[Home](https://chuniversiteit.nl/)[About](https://chuniversiteit.nl/about)[Archive](https://chuniversiteit.nl/archive)[Search](https://chuniversiteit.nl/search)
+[The Toilet Paper](https://chuniversiteit.nl/papers)
+# Comparing algorithms for extracting content from web pages
 
 Published 
-    3 Nov 2024 
+    3 Nov 2024
 
 Written by 
@@ -19,8 +21,8 @@
 ## About the article
 [ ![Link](https://chuniversiteit.nl/images/static/link.svg)](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms#about-the-article "Copy link to heading")  
-| Title  | [An empirical comparison of web content extraction algorithms](https://doi.org/10.1145/3539618.3591920)  |  
+| Title | [An empirical comparison of web content extraction algorithms](https://doi.org/10.1145/3539618.3591920) |  
 | --- | --- |  
-| Year  | 2023  |  
-| Author(s)  | 
+| Year  | 2023 |  
+| Author(s) | 
   1. Janek Bevendorff (![de](https://chuniversiteit.nl/images/static/flags/de.svg)[Bauhaus-Universität Weimar](https://www.uni-weimar.de/en))
   2. Sanket Gupta (![de](https://chuniversiteit.nl/images/static/flags/de.svg)[Bauhaus-Universität Weimar](https://www.uni-weimar.de/en))
@@ -29,5 +31,5 @@
 
  |  
-| Venue  | [International ACM SIGIR Conference on Research and Development in Information Retrieval](https://sigir.org/sigir2023/)  |  
+| Venue | [International ACM SIGIR Conference on Research and Development in Information Retrieval](https://sigir.org/sigir2023/) |  
 Many main content extraction systems have been written over the past decades, but the algorithms used generally fall into one of two categories:
   * **Heuristic approaches** use heuristic rules (often in the form of trees) to identify one or more blocks of main content. While these rules are efficient to execute, they rely heavily on human expertise for their design.
@@ -39,20 +41,20 @@
 Although a lot of work has gone into developing better main content extraction systems, relatively limited effort has been spent on developing resources for reproducible experiments. Most systems are only evaluated using small datasets. Systems produced outside of academia are often not evaluated at all and are sometimes ignored entirely in evaluation studies.
 The authors of this paper have combined eight common evaluation datasets into one large dataset, which they then used to evaluate 14 main content extraction systems:  
-| Extractor  | Language  | Approach  |  
+| Extractor  | Language  | Approach |  
 | --- | --- | --- |  
-| [BTE](https://github.com/aidanf/BTE)  | Python  | Heuristic: HTML tag distribution  |  
-| [Goose3](https://pypi.org/project/goose3/)  | Python  | Heuristic: rule-based  |  
-| [jusText](https://pypi.org/project/jusText/)  | Python  | Heuristic: rule-based  |  
-| [Newspaper3k](https://newspaper.readthedocs.io/en/latest/)  | Python  | Heuristic: rule-based (for news)  |  
-| [Readability](https://github.com/mozilla/readability)  | JavaScript  | Heuristic: rule-based  |  
-| [Resiliparse](https://resiliparse.chatnoir.eu/en/stable/)  | Python  | Heuristic: rule-based  |  
-| [Trafilatura](https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms)  | Python  | Heuristic: rule-based  |  
-| [news-please](https://github.com/fhamborg/news-please)  | Python  | Meta heuristic: rule-based (for news)  |  
-| [Boilerpipe](https://code.google.com/archive/p/boilerpipe/)  | Java  | AI: text node classification  |  
-| [Dragnet](https://github.com/dragnet-org/dragnet)  | Python  | AI: text node classification  |  
-| [ExtractNet](https://pypi.org/project/extractnet/)  | Python  | AI: text node classification  |  
-| [Go DOM Distiller](https://github.com/markusmobius/go-domdistiller)  | Go  | AI: text node classification  |  
-| [BoilerNet](https://github.com/mrjleo/boilernet)  | Python (+JS)  | AI: sequence labeling (LSTM)  |  
-| [Web2Text](https://github.com/dalab/web2text)  | Python  | AI: sequence labeling (HMM+CNN)  |  
+| [BTE](https://github.com/aidanf/BTE)  | Python  | Heuristic: HTML tag distribution |  
+| [Goose3](https://pypi.org/project/goose3/)  | Python  | Heuristic: rule-based |  
+| [jusText](https://pypi.org/project/jusText/)  | Python  | Heuristic: rule-based |  
+| [Newspaper3k](https://newspaper.readthedocs.io/en/latest/)  | Python  | Heuristic: rule-based (for news) |  
... [diff truncated, showing first 60 lines] ...
```

#### Forum-Thread — `https://news.ycombinator.com/item?id=40035347`
F1: 0.820 | recall: 0.833 | precision: 0.806 | bytes Δ: +460

```diff
--- cleanraw
+++ candidate
@@ -1,59 +1,64 @@
 <!-- source: https://news.ycombinator.com/item?id=40035347 -->
 
-
- |   | [](https://news.ycombinator.com/vote?id=40035347&how=up&goto=item%3Fid%3D40035347)  |  [screye](https://news.ycombinator.com/user?id=screye) [on April 14, 2024](https://news.ycombinator.com/item?id=40035347) | [parent](https://news.ycombinator.com/item?id=40033490) | [context](https://news.ycombinator.com/item?id=40033490#40035347) | [favorite](https://news.ycombinator.com/fave?id=40035347&auth=2505d90644bb16ef9a5f86de5764312284bcdd6a) | on: [Show HN: I made a tool to clean and convert any we...](https://news.ycombinator.com/item?id=40033490 "Show HN: I made a tool to clean and convert any webpage to Markdown")   
-Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall) 2. Dropping all the ads/auxilliary content (high precision) 3. And getting the correct layout/section types (formatting) For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job. Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings.  |  
+|   
+ | [![](https://news.ycombinator.com/y18.svg)](https://news.ycombinator.com) | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomments) | [ask](https://news.ycombinator.com/ask) | [show](https://news.ycombinator.com/show) | [jobs](https://news.ycombinator.com/jobs) | [submit](https://news.ycombinator.com/submit) | [login](https://news.ycombinator.com/login?goto=item%3Fid%3D40035347) |  
 | --- | --- | --- |  
-|   |   |  
+ |  
+ |  
+|   
+ |  | [](https://news.ycombinator.com/vote?id=40035347&how=up&goto=item%3Fid%3D40035347) | [screye](https://news.ycombinator.com/user?id=screye) [on April 14, 2024](https://news.ycombinator.com/item?id=40035347) | [parent](https://news.ycombinator.com/item?id=40033490) | [context](https://news.ycombinator.com/item?id=40033490#40035347) | [favorite](https://news.ycombinator.com/fave?id=40035347&auth=2505d90644bb16ef9a5f86de5764312284bcdd6a) | on: [Show HN: I made a tool to clean and convert any we...](https://news.ycombinator.com/item?id=40033490 "Show HN: I made a tool to clean and convert any webpage to Markdown")  
+Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall)2. Dropping all the ads/auxilliary content (high precision)3. And getting the correct layout/section types (formatting)For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job.Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings. |  
+| --- | --- | --- |  
+|  |  |  
   
   
 |   
- | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40037718&how=up&goto=item%3Fid%3D40035347)  |  [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40037718) | [next](https://news.ycombinator.com/item?id=40035347#40038447) [[–]](javascript:void\(0\))   
-Thoroughly scraping is challenging, especially in an environment where you don’t have (or want) a JavaScript runtime.For content extraction, I found the approach the Postlight library takes quite neat. It scores individual html nodes based on some heuristics (text length, link density, css classes). It the selects the nodes with the highest score. [1] I ported it to Swift for a personal read later app. [1] <https://github.com/postlight/parser>  |  
+ | ![](https://news.ycombinator.com/s.gif) | [](https://news.ycombinator.com/vote?id=40037718&how=up&goto=item%3Fid%3D40035347) | [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40037718) | [next](https://news.ycombinator.com/item?id=40035347#40038447) [[–]](javascript:void\(0\))  
+Thoroughly scraping is challenging, especially in an environment where you don’t have (or want) a JavaScript runtime.For content extraction, I found the approach the Postlight library takes quite neat. It scores individual html nodes based on some heuristics (text length, link density, css classes). It the selects the nodes with the highest score. [1] I ported it to Swift for a personal read later app.[1] <https://github.com/postlight/parser> |  
 | --- | --- | --- |  
  |  
 |   
- | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40101653&how=up&goto=item%3Fid%3D40035347)  |  [Kikobeats](https://news.ycombinator.com/user?id=Kikobeats) [on April 20, 2024](https://news.ycombinator.com/item?id=40101653) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [next](https://news.ycombinator.com/item?id=40035347#40038016) [[–]](javascript:void\(0\))   
-For getting the HTML, you can use microlink, just passing the URL to [https://html.microlink.io/{url}](https://html.microlink.io/%7Burl%7D), like <https://html.microlink.io/https://example.com>  |  
+ | ![](https://news.ycombinator.com/s.gif) | [](https://news.ycombinator.com/vote?id=40101653&how=up&goto=item%3Fid%3D40035347) | [Kikobeats](https://news.ycombinator.com/user?id=Kikobeats) [on April 20, 2024](https://news.ycombinator.com/item?id=40101653) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [next](https://news.ycombinator.com/item?id=40035347#40038016) [[–]](javascript:void\(0\))  
+For getting the HTML, you can use microlink, just passing the URL to <https://html.microlink.io/{url}>, like <https://html.microlink.io/https://example.com> |  
 | --- | --- | --- |  
  |  
 |   
- | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40038016&how=up&goto=item%3Fid%3D40035347)  |  [justech](https://news.ycombinator.com/user?id=justech) [on April 15, 2024](https://news.ycombinator.com/item?id=40038016) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [prev](https://news.ycombinator.com/item?id=40035347#40101653) | [next](https://news.ycombinator.com/item?id=40035347#40045130) [[–]](javascript:void\(0\))   
-This is pretty cool. Care to share your Swift port?  |  
+ | ![](https://news.ycombinator.com/s.gif) | [](https://news.ycombinator.com/vote?id=40038016&how=up&goto=item%3Fid%3D40035347) | [justech](https://news.ycombinator.com/user?id=justech) [on April 15, 2024](https://news.ycombinator.com/item?id=40038016) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [prev](https://news.ycombinator.com/item?id=40035347#40101653) | [next](https://news.ycombinator.com/item?id=40035347#40045130) [[–]](javascript:void\(0\))  
+This is pretty cool. Care to share your Swift port? |  
 | --- | --- | --- |  
  |  
 |   
- | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40038118&how=up&goto=item%3Fid%3D40035347)  |  [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40038118) | [root](https://news.ycombinator.com/item?id=40035347#40037718) | [parent](https://news.ycombinator.com/item?id=40035347#40038016) | [next](https://news.ycombinator.com/item?id=40035347#40045130) [[–]](javascript:void\(0\))   
-Not planning to. It’s my first Swift/iOS project. I neither want to polish it nor maintain it publicly. Happy to share it privately, email is in the bio. I’m planning on a blog post describing the general approach though!  |  
+ | ![](https://news.ycombinator.com/s.gif) | [](https://news.ycombinator.com/vote?id=40038118&how=up&goto=item%3Fid%3D40035347) | [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40038118) | [root](https://news.ycombinator.com/item?id=40035347#40037718) | [parent](https://news.ycombinator.com/item?id=40035347#40038016) | [next](https://news.ycombinator.com/item?id=40035347#40045130) [[–]](javascript:void\(0\))  
+Not planning to. It’s my first Swift/iOS project. I neither want to polish it nor maintain it publicly. Happy to share it privately, email is in the bio. I’m planning on a blog post describing the general approach though! |  
 | --- | --- | --- |  
  |  
 |   
- | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40045130&how=up&goto=item%3Fid%3D40035347)  |  [rismay](https://news.ycombinator.com/user?id=rismay) [on April 15, 2024](https://news.ycombinator.com/item?id=40045130) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [prev](https://news.ycombinator.com/item?id=40035347#40038016) | [next](https://news.ycombinator.com/item?id=40035347#40038447) [[–]](javascript:void\(0\))   
-Care to share the Swift port?  |  
+ | ![](https://news.ycombinator.com/s.gif) | [](https://news.ycombinator.com/vote?id=40045130&how=up&goto=item%3Fid%3D40035347) | [rismay](https://news.ycombinator.com/user?id=rismay) [on April 15, 2024](https://news.ycombinator.com/item?id=40045130) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [prev](https://news.ycombinator.com/item?id=40035347#40038016) | [next](https://news.ycombinator.com/item?id=40035347#40038447) [[–]](javascript:void\(0\))  
+Care to share the Swift port? |  
 | --- | --- | --- |  
  |  
 |   
- | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40038447&how=up&goto=item%3Fid%3D40035347)  |  [msp26](https://news.ycombinator.com/user?id=msp26) [on April 15, 2024](https://news.ycombinator.com/item?id=40038447) | [prev](https://news.ycombinator.com/item?id=40035347#40037718) | [next](https://news.ycombinator.com/item?id=40035347#40037017) [[–]](javascript:void\(0\))   
-Thanks for the links I had no idea those existed.For my article web scraper (wip) the current steps are: - Navigate with playwright + adblocker - Run mozilla's readability on the page - LLM checks readability output If check failed - Trim whole page HTML context - Convert to markdown with pandoc - LLM extracts from markdown  |  
+ | ![](https://news.ycombinator.com/s.gif) | [](https://news.ycombinator.com/vote?id=40038447&how=up&goto=item%3Fid%3D40035347) | [msp26](https://news.ycombinator.com/user?id=msp26) [on April 15, 2024](https://news.ycombinator.com/item?id=40038447) | [prev](https://news.ycombinator.com/item?id=40035347#40037718) | [next](https://news.ycombinator.com/item?id=40035347#40037017) [[–]](javascript:void\(0\))  
... [diff truncated, showing first 60 lines] ...
```
