<!-- source: https://trafilatura.readthedocs.io/en/latest/evaluation.html -->

**Private docs hosting** for any Docs as Code tool.**Get started**
# Evaluation#
Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. Should the tooling be adapted to particular news outlets or blogs that are targeted (which often amounts to the development of web scraping tools) or should the extraction be as generic as possible to provide opportunistic ways of gathering information?
The extraction focuses on the main content, which is usually the part displayed centrally, without the left or right bars, the header or the footer, but including potential titles and (optionally) comments. This task is also known as web scraping, boilerplate removal, DOM-based content extraction, main content identification, or web page cleaning.
Hint
To run the evaluation with the latest data and packages see the corresponding readme .
## External evaluations
  * Most efficient open-source library in _ScrapingHub_ ’s article extraction benchmark
  * Best overall tool according to Bien choisir son outil d’extraction de contenu à partir du Web (Lejeune & Barbaresi 2020)
  * Comparison on a small sample of Polish news texts and forums (now integrated in the internal benchmark, Trafilatura has improved since)
  * Best single tool by ROUGE-LSum Mean F1 Page Scores in An Empirical Comparison of Web Content Extraction Algorithms (Bevendorff et al. 2023)


## Alternatives
Although a few corresponding Python packages are not actively maintained the following alternatives exist.
These packages keep the structure intact but do not focus on main text extraction:
  * html2text converts HTML pages to Markup language
  * html_text converts HTML code to plain text
  * inscriptis converts HTML to text with a particular emphasis on nested tables


These packages focus on main text extraction:
  * boilerpy3 is a Python version of the boilerpipe algorithm for boilerplate removal and fulltext extraction
  * _dragnet_ is not maintained anymore, it is provided for reference only (in older evaluations)
  * goose3 can extract information for embedded content but doesn’t preserve markup
  * jusText is designed to preserve mainly text containing full sentences along with some markup, it has been explicitly developed to create linguistic resources
  * newspaper3k is mostly geared towards newspaper texts, provides additional functions but no structured text or comment extraction
  * news-please is a news crawler that extracts structured information
  * readability-lxml cleans the page and preserves some markup
  * readabilipy contains a Python wrapper for Mozilla’s Node.js package, as well as article extraction routines written in pure Python
  * trafilatura is the library documented here, several options are tested regarding main text extraction only, without metadata or comments


The tools are compared to the raw page source and to a meaningful baseline consisting of extracting the raw text contained in the JSON article element or in a combination of paragraph, code and quote elements.
## Description
**Test set** : The experiments below are run on a collection of documents which are either typical for Internet articles (news outlets, blogs). Some are harder to process due to mixed content (lists, tables) or not fully valid HTML code. They are selected from large collections of web pages in German, for the sake of completeness documents in other languages are added (notably English, French, other European languages, Chinese and Arabic, about 20-30% of the total).
**Evaluation** : Decisive document segments are singled out which are not statistically representative but very significant in the perspective of working with the texts, most notably left/right columns, additional header, author or footer information such as imprints or addresses, as well as affiliated and social network links, in short boilerplate. Raw text segments are expected which is also a way to evaluate the quality of HTML extraction in itself.
**Time** : The execution time is provided as an indication. As the baseline extraction is simple and fast, it is used for the benchmark. Certain packages are noticeably slower than the rest: _goose3_ and _newspaper_ , while _news-please_ ’s execution time isn’t comparable because of operations unrelated to text extraction. ReadabiliPy is very slow for unclear reasons.
**Errors** : The _boilerpy3_ , _newspaper3k_ , and _readabilipy_ modules do not work without errors on every HTML file in the test set, probably because of malformed HTML, encoding or parsing bugs. These errors are ignored in order to complete the benchmark.
**Results** : The baseline beats a few systems, showing its interest. _justext_ is highly configurable and tweaking its configuration (as it is done here) can lead to better performance than its generic settings. _goose3_ is the most precise algorithm, albeit at a significant cost in terms of recall. The packages focusing on raw text extraction _html_text_ and _inscriptis_ are roughly comparable and achieve the best recall as they try to extract all the text. Rule-based approaches such as _trafilatura_ ’s obtain balanced results despite a lack of precision. Combined with an algorithmic approach they perform significantly better than the other tested solutions. Trafilatura consistently outperforms other open-source libraries, showcasing its efficiency and accuracy in extracting web content.
**Roadmap** : Further evaluations will be run, including additional tools and languages. Comment extraction still has to be evaluated, although most libraries don not offer this functionality.
The evaluation script is available on the project repository: tests/README.rst. To reproduce the tests just clone the repository, install all necessary packages and run the evaluation script with the data provided in the _tests_ directory.
## Results (2022-05-18)  
| 750 documents, 2236 text & 2250 boilerplate segments, Python 3.8  |  
| --- |  
| Python Package  | Precision  |  
| html2text 2020.1.16  |  
| html_text 0.5.2  |  
| inscriptis 2.2.0 (html to txt)  |  
| newspaper3k 0.2.8  |  
| justext 3.0.0 (custom)  |  
| boilerpy3 1.0.6 (article mode)  |  
| _baseline (text markup)_  |  
| readability-lxml 0.8.1  |  
| news-please 1.5.22  |  
| readabilipy 0.2.0  |  
| trafilatura 1.2.2 (fast)  |  
| trafilatura 1.2.2 (precision)  |  
| trafilatura 1.2.2 (standard)  |  
## Older results
### Older results (2021-06-07)  
| 500 documents, 1487 text and 1496 boilerplate segments  |  
| --- |  
| html2text 2020.1.16  |  
| html_text 0.5.2  |  
| inscriptis 1.1 (html to txt)  |  
| justext 2.2.0 (custom)  |  
| newspaper3k 0.2.8  |  
| boilerpy3 1.0.2 (article mode)  |  
| goose3 3.1.9  |  
| _baseline (text markup)_  |  
| dragnet 2.0.4  |  
| readability-lxml 0.8.1  |  
| news-please 1.5.21  |  
| trafilatura 0.8.2 (fast)  |  
| trafilatura 0.8.2  |  
### Older results (2020-11-06)  
| justext 2.2.0 (tweaked)  |  
| --- |  
| goose3 3.1.6  |  
| boilerpy3 1.0.2 (article mode)  |  
| news-please 1.5.13  |  
| trafilatura 0.6.0  |  
| trafilatura 0.6.0 (+ fallbacks)  |  
### Older results (2020-07-16)  
| 400 documents, 1186 text and 1198 boilerplate segments  |  
| --- |  
| html2text 2020.1.16  |  
| html_text 0.5.1  |  
| inscriptis 1.0 (html to txt)  |  
| newspaper3k 0.2.8  |  
| justext 2.2.0 (tweaked)  |  
| goose3 3.1.6  |  
| _baseline (text markup)_  |  
| boilerpy3 1.0.2 (article mode)  |  
| dragnet 2.0.4  |  
| readability-lxml 0.8.1  |  
| news-please 1.4.25  |  
| trafilatura 0.5.1  |  
| trafilatura 0.5.1 (+ fallbacks)  |  
### Older results (2020-03-19)  
| 300 documents, 869 text and 878 boilerplate segments  |  
| --- |  
| _baseline (text markup)_  |  
| html2text 2020.1.16  |  
| inscriptis 1.0 (html to txt)  |  
| justext 2.2.0 (German stoplist)  |  
| newspaper 0.2.8  |  
| goose3 3.1.6  |  
| boilerpy3 1.0.2 (article mode)  |  
| dragnet 2.0.4  |  
| readability-lxml 0.7.1  |  
| news-please 1.4.25  |  
| trafilatura 0.3.1 (rule-based)  |  
| trafilatura 0.3.1 (+ justext)  |  
| trafilatura 0.4  |  
| trafilatura 0.4 (+ fallback)  |  
### Older results (2020-01-29)  
| 100 documents, 266 text and 294 boilerplate segments  |  
| --- |  
| inscriptis 1.0 (html to txt)  |  
| justext 2.2.0 (German stoplist)  |  
| goose3 3.1.6  |  
| newspaper 0.2.8  |  
| boilerpy3 1.0.2 (default mode)  |  
| dragnet 2.0.4  |  
| readability-lxml 0.7.1  |  
| news-please 1.4.25  |  
| trafilatura 0.3.1 (rule-based)  |  
| trafilatura 0.3.1 (+ justext)  |
