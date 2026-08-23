<!-- source: https://trafilatura.readthedocs.io/en/latest/evaluation.html -->

[Skip to main content](https://trafilatura.readthedocs.io/en/latest/evaluation.html#main-content)
Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. Should the tooling be adapted to particular news outlets or blogs that are targeted (which often amounts to the development of web scraping tools) or should the extraction be as generic as possible to provide opportunistic ways of gathering information?
The extraction focuses on the main content, which is usually the part displayed centrally, without the left or right bars, the header or the footer, but including potential titles and (optionally) comments. This task is also known as web scraping, boilerplate removal, DOM-based content extraction, main content identification, or web page cleaning.
Most efficient open-source library in _ScrapingHub_ ’s[article extraction benchmark](https://github.com/scrapinghub/article-extraction-benchmark)
Comparison on a small[sample of Polish news texts and forums](https://github.com/tsolewski/Text_extraction_comparison_PL)(now integrated in the internal benchmark, Trafilatura has improved since)
Best single tool by ROUGE-LSum Mean F1 Page Scores in[An Empirical Comparison of Web Content Extraction Algorithms](https://webis.de/downloads/publications/papers/bevendorff_2023b.pdf)(Bevendorff et al. 2023)
[boilerpy3](https://github.com/jmriebold/BoilerPy3)is a Python version of the boilerpipe algorithm for boilerplate removal and fulltext extraction
[goose3](https://github.com/goose3/goose3)can extract information for embedded content but doesn’t preserve markup
[newspaper3k](https://github.com/codelucas/newspaper)is mostly geared towards newspaper texts, provides additional functions but no structured text or comment extraction
[news-please](https://github.com/fhamborg/news-please)is a news crawler that extracts structured information
[readabilipy](https://github.com/alan-turing-institute/ReadabiliPy)contains a Python wrapper for Mozilla’s Node.js package, as well as article extraction routines written in pure Python
[trafilatura](https://github.com/adbar/trafilatura)is the library documented here, several options are tested regarding main text extraction only, without metadata or comments
trafilatura 1.2.2 (fast)
trafilatura 1.2.2 (precision)
trafilatura 1.2.2 (standard)
trafilatura 0.8.2 (fast)
trafilatura 0.8.2
trafilatura 0.6.0
trafilatura 0.6.0 (+ fallbacks)
trafilatura 0.5.1
trafilatura 0.5.1 (+ fallbacks)
trafilatura 0.3.1 (rule-based)
trafilatura 0.3.1 (+ justext)
trafilatura 0.4
trafilatura 0.4 (+ fallback)
