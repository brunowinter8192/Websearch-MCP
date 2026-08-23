<!-- source: https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/ -->

# Trafilatura vs. Readability vs. Newspaper4k — which extracts better in 2026?

```
pip install trafilatura
pip install readability-lxml
pip install newspaper4k
```

Newspaper4k optionally pulls in NLTK for keyword extraction and summarization (`pip install newspaper4k[nlp]`). If you skip the extra, the NLP methods just won't work — the core extraction still runs fine.
Trafilatura needs Python 3.8+. readability-lxml also supports 3.8+. Newspaper4k bumped its minimum to 3.10 as of version 0.9.4, which shipped in November 2025[1](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-newspaper4k-pypi). That caught a few people off guard — keep it in mind if you're stuck on an older runtime.

```
# Trafilatura
import trafilatura

downloaded = trafilatura.fetch_url("https://example.com/article")
text = trafilatura.extract(downloaded)
# or with options:
text = trafilatura.extract(downloaded, output_format="markdown",
                           include_links=True, favor_precision=True)
```


```
# readability-lxml
from readability import Document
import requests

response = requests.get("https://example.com/article")
doc = Document(response.text)
title = doc.title()
html_content = doc.summary()  # returns HTML, not plain text
```

The ScrapingHub Article Extraction Benchmark is the closest thing this space has to a standard test suite. Here are the current numbers[2](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-scrapinghub-benchmark):
| Trafilatura 2.0.0 Trafilatura leads on F1. But look at the precision column — Newspaper4k actually beats it there (0.964 vs. 0.938). That means Newspaper4k is slightly better at not including junk, while Trafilatura is better at not missing content. The gap between those top two is small enough that on any given page you might see either win. The Bevendorff et al. SIGIR 2023 study told a similar story from a different angle[3](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-bevendorff-sigir-2023). Across eight evaluation datasets, Trafilatura had the best overall mean F1 (0.883) while Readability (the JavaScript version — readability.js 0.6.0) had the highest median (0.970). A two-sample t-test found no statistically significant difference between the two on mean F1. So the honest answer is: Trafilatura and Readability are close, and which one "wins" depends on your dataset. The Sandia National Laboratories evaluation from August 2024 confirmed similar rankings, with Trafilatura achieving the highest mean F1 (0.937) and precision (0.978)[4](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-sandia-2024). For[content extraction for LLMs](https://www.contextractor.com/content-extraction-for-llms/), Trafilatura's Markdown output is probably the most useful — LLMs handle Markdown well, and you keep heading structure intact. For archival and academic work, TEI-XML from Trafilatura is hard to beat. For news-specific pipelines where you want author, date, and top image alongside text, Newspaper4k is the more natural fit. **Trafilatura** struggles with very short pages — product pages with two sentences of description and a big image gallery, for instance. The content scoring heuristic expects article-length text, and when there isn't much to work with, it sometimes returns nothing. Setting`favor_recall=True`helps, but then you pick up more noise on other pages. The`fast=True`mode skips the fallback chain (readability-lxml and jusText), which roughly doubles throughput but drops the safety net[6](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-trafilatura-docs). **readability-lxml** falls apart on non-article pages. Forums, product listings, multi-column layouts — anything that doesn't look like a blog post or news article. It was designed for exactly one thing (isolating an article body), and it does that well, but hand it a page with multiple equally-weighted content sections and the output is unpredictable. Also, since it returns HTML, you still need a text extraction step if you want plain text. That's not a bug, it's a design choice — but it does mean more code on your end. None of them handle JavaScript-rendered pages. Single-page apps built with React, Vue, or Angular serve an empty shell; the actual content loads dynamically after JavaScript executes. You need a headless browser like Playwright to render the page first, then pass the resulting HTML to any of these tools. Same for paywalled content — authentication is a separate problem entirely.[Contextractor](https://www.contextractor.com/)solves both of these by running Playwright before Trafilatura. Cookie consent modals don't affect server-side extraction at all — they're JavaScript-driven overlays that only appear in a browser. When you fetch a page with`requests`or Trafilatura's built-in downloader, the underlying HTML usually contains the article text regardless of whether a cookie modal would have blocked it visually. The same goes for most ad containers; they're injected by JavaScript after page load. The exceptions are sites that genuinely gate content server-side based on consent (GDPR-compliant implementations in the EU, mainly). For those, you need a browser session that clicks through the consent flow before extracting. But that's a browser automation problem, not an extraction library problem.
## The extraction benchmark gap
If you're building a pipeline that processes a known type of content (news, blog posts, documentation), test all three on a sample of your actual pages. The benchmark F1 scores are a reasonable starting point, but your specific page structures matter more than aggregate numbers.  | Trafilatura  | `pip install trafilatura` [Contextractor](https://www.contextractor.com/)uses Trafilatura as its extraction engine, paired with Playwright for JavaScript rendering — covering the gap that all three libraries share on their own. ScrapingHub:[Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark). Retrieved March 27, 2026[↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-scrapinghub-benchmark) Janek Bevendorff, Sanket Gupta, Johannes Kiesel, Benno Stein:[An Empirical Comparison of Web Content Extraction Algorithms](https://dl.acm.org/doi/10.1145/3539618.3591920). Proceedings of SIGIR 2023[↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-bevendorff-sigir-2023) Sandia National Laboratories:[An Evaluation of Main Content Extraction Libraries](https://www.osti.gov/servlets/purl/2429881). SAND2024-10208, August 2024[↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-sandia-2024)
