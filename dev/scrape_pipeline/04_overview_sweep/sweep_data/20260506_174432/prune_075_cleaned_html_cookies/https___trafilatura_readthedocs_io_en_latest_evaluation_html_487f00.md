<!-- source: https://trafilatura.readthedocs.io/en/latest/evaluation.html -->

Back to top
Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. Should the tooling be adapted to particular news outlets or blogs that are targeted (which often amounts to the development of web scraping tools) or should the extraction be as generic as possible to provide opportunistic ways of gathering information?
The extraction focuses on the main content, which is usually the part displayed centrally, without the left or right bars, the header or the footer, but including potential titles and (optionally) comments. This task is also known as web scraping, boilerplate removal, DOM-based content extraction, main content identification, or web page cleaning.
Hint
To run the evaluation with the latest data and packages see the [corresponding readme](https://github.com/adbar/trafilatura/blob/master/tests/README.rst) .
## External evaluations[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#external-evaluations "Link to this heading")
  * Most efficient open-source library in _ScrapingHub_ ’s [article extraction benchmark](https://github.com/scrapinghub/article-extraction-benchmark)
  * Best overall tool according to [Bien choisir son outil d’extraction de contenu à partir du Web](https://hal.archives-ouvertes.fr/hal-02768510v3/document) (Lejeune & Barbaresi 2020)
  * Comparison on a small [sample of Polish news texts and forums](https://github.com/tsolewski/Text_extraction_comparison_PL) (now integrated in the internal benchmark, Trafilatura has improved since)
  * Best single tool by ROUGE-LSum Mean F1 Page Scores in [An Empirical Comparison of Web Content Extraction Algorithms](https://webis.de/downloads/publications/papers/bevendorff_2023b.pdf) (Bevendorff et al. 2023)


Although a few corresponding Python packages are not actively maintained the following alternatives exist.
These packages keep the structure intact but do not focus on main text extraction:
  * [html2text](https://github.com/Alir3z4/html2text) converts HTML pages to Markup language
  * [html_text](https://github.com/TeamHG-Memex/html-text) converts HTML code to plain text
  * [inscriptis](https://github.com/weblyzard/inscriptis) converts HTML to text with a particular emphasis on nested tables


These packages focus on main text extraction:
  * [boilerpy3](https://github.com/jmriebold/BoilerPy3) is a Python version of the boilerpipe algorithm for boilerplate removal and fulltext extraction
  * _dragnet_ is not maintained anymore, it is provided for reference only (in older evaluations)
  * [goose3](https://github.com/goose3/goose3) can extract information for embedded content but doesn’t preserve markup
  * [jusText](https://github.com/miso-belica/jusText) is designed to preserve mainly text containing full sentences along with some markup, it has been explicitly developed to create linguistic resources
  * [newspaper3k](https://github.com/codelucas/newspaper) is mostly geared towards newspaper texts, provides additional functions but no structured text or comment extraction
  * [news-please](https://github.com/fhamborg/news-please) is a news crawler that extracts structured information
  * [readability-lxml](https://github.com/buriy/python-readability) cleans the page and preserves some markup
  * [readabilipy](https://github.com/alan-turing-institute/ReadabiliPy) contains a Python wrapper for Mozilla’s Node.js package, as well as article extraction routines written in pure Python
  * [trafilatura](https://github.com/adbar/trafilatura) is the library documented here, several options are tested regarding main text extraction only, without metadata or comments


The tools are compared to the raw page source and to a meaningful baseline consisting of extracting the raw text contained in the JSON article element or in a combination of paragraph, code and quote elements.
**Test set** : The experiments below are run on a collection of documents which are either typical for Internet articles (news outlets, blogs). Some are harder to process due to mixed content (lists, tables) or not fully valid HTML code. They are selected from [large collections of web pages in German](https://www.dwds.de/d/k-web), for the sake of completeness documents in other languages are added (notably English, French, other European languages, Chinese and Arabic, about 20-30% of the total).
**Evaluation** : Decisive document segments are singled out which are not statistically representative but very significant in the perspective of working with the texts, most notably left/right columns, additional header, author or footer information such as imprints or addresses, as well as affiliated and social network links, in short boilerplate. Raw text segments are expected which is also a way to evaluate the quality of HTML extraction in itself.
**Time** : The execution time is provided as an indication. As the baseline extraction is simple and fast, it is used for the benchmark. Certain packages are noticeably slower than the rest: _goose3_ and _newspaper_ , while _news-please_ ’s execution time isn’t comparable because of operations unrelated to text extraction. ReadabiliPy is very slow for unclear reasons.
**Errors** : The _boilerpy3_ , _newspaper3k_ , and _readabilipy_ modules do not work without errors on every HTML file in the test set, probably because of malformed HTML, encoding or parsing bugs. These errors are ignored in order to complete the benchmark.
**Results** : The baseline beats a few systems, showing its interest. _justext_ is highly configurable and tweaking its configuration (as it is done here) can lead to better performance than its generic settings. _goose3_ is the most precise algorithm, albeit at a significant cost in terms of recall. The packages focusing on raw text extraction _html_text_ and _inscriptis_ are roughly comparable and achieve the best recall as they try to extract all the text. Rule-based approaches such as _trafilatura_ ’s obtain balanced results despite a lack of precision. Combined with an algorithmic approach they perform significantly better than the other tested solutions. Trafilatura consistently outperforms other open-source libraries, showcasing its efficiency and accuracy in extracting web content.
**Roadmap** : Further evaluations will be run, including additional tools and languages. Comment extraction still has to be evaluated, although most libraries don not offer this functionality.
The evaluation script is available on the project repository: [tests/README.rst](https://github.com/adbar/trafilatura/blob/master/tests/). To reproduce the tests just clone the repository, install all necessary packages and run the evaluation script with the data provided in the _tests_ directory.
## Results (2022-05-18)[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#results-2022-05-18 "Link to this heading")  
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
### Older results (2021-06-07)[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#older-results-2021-06-07 "Link to this heading")  
| 500 documents, 1487 text and 1496 boilerplate segments  |  
| --- |  
| Python Package  | Precision  |  
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
### Older results (2020-11-06)[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#older-results-2020-11-06 "Link to this heading")  
| 500 documents, 1487 text and 1496 boilerplate segments  |  
| --- |  
| Python Package  | Precision  |  
| html2text 2020.1.16  |  
| html_text 0.5.2  |  
| inscriptis 1.1 (html to txt)  |  
| justext 2.2.0 (tweaked)  |  
| newspaper3k 0.2.8  |  
| goose3 3.1.6  |  
| boilerpy3 1.0.2 (article mode)  |  
| _baseline (text markup)_  |  
| dragnet 2.0.4  |  
| readability-lxml 0.8.1  |  
| news-please 1.5.13  |  
| trafilatura 0.6.0  |  
| trafilatura 0.6.0 (+ fallbacks)  |  
### Older results (2020-07-16)[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#older-results-2020-07-16 "Link to this heading")  
| 400 documents, 1186 text and 1198 boilerplate segments  |  
| --- |  
| Python Package  | Precision  |  
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
### Older results (2020-03-19)[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#older-results-2020-03-19 "Link to this heading")  
| 300 documents, 869 text and 878 boilerplate segments  |  
| --- |  
| Python Package  | Precision  |  
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
### Older results (2020-01-29)[#](https://trafilatura.readthedocs.io/en/latest/evaluation.html#older-results-2020-01-29 "Link to this heading")  
| 100 documents, 266 text and 294 boilerplate segments  |  
| --- |  
| Python Package  | Precision  |  
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
