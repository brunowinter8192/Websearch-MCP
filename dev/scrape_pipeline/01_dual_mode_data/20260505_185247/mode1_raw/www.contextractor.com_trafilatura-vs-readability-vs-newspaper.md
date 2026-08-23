<!-- source: https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/ -->

[![Contextractor](https://www.contextractor.com/_next/static/media/logo.941c533e.svg)](https://www.contextractor.com/)
# Trafilatura vs. Readability vs. Newspaper4k — which extracts better in 2026?
If you need to pull clean article text out of a web page using Python, you've got three realistic choices: **[Trafilatura](https://www.contextractor.com/trafilatura/)** , **readability-lxml** , and **Newspaper4k**. There are others (goose3, jusText, boilerpipe's Python bindings), but these three are the ones that are actively maintained, installable without pain, and actually used in production.
They don't do the same thing, though. That's the part most comparison posts get wrong — treating them as interchangeable when they have quite different design goals. Trafilatura is a general-purpose [content extraction](https://www.contextractor.com/content-extraction/) pipeline with a fallback chain. readability-lxml is a minimal HTML cleaner descended from Firefox's Reader View. Newspaper4k is a news article processor with built-in NLP. Same problem space, different tools.
## Getting them running
All three install with pip. No compiled extensions, no browser dependencies.

```
pip install trafilatura
pip install readability-lxml
pip install newspaper4k

```

Newspaper4k optionally pulls in NLTK for keyword extraction and summarization (`pip install newspaper4k[nlp]`). If you skip the extra, the NLP methods just won't work — the core extraction still runs fine.
Trafilatura needs Python 3.8+. readability-lxml also supports 3.8+. Newspaper4k bumped its minimum to 3.10 as of version 0.9.4, which shipped in November 2025[1](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-newspaper4k-pypi). That caught a few people off guard — keep it in mind if you're stuck on an older runtime.
## The API contrast
This is where the design philosophies become obvious. Same page, three different ways to get the text:

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

```
# Newspaper4k
from newspaper import Article

article = Article("https://example.com/article")
article.download()
article.parse()
print(article.text)       # plain text
print(article.authors)    # list of author names
print(article.publish_date)
article.nlp()             # optional — needs nltk
print(article.keywords)
print(article.summary)

```

Notice the difference. Trafilatura takes raw HTML and gives you text (or Markdown, or XML, or JSON — seven formats total). readability-lxml takes HTML and gives you back _cleaned_ HTML — not plain text. You need to strip the tags yourself or pipe it through another tool. Newspaper4k wraps the entire download-parse-analyze cycle into a single object and adds NLP on top.
For most [content extraction](https://www.contextractor.com/content-extraction/) use cases — feeding text into an LLM, building a search index, populating a RAG pipeline — Trafilatura's API is the most direct path. You hand it HTML, you get text. Done. Newspaper4k's object-oriented approach makes more sense if you're building a news aggregator where you need author names, publish dates, and top images together. readability-lxml is the odd one out because you get HTML fragments, not text, which is exactly what you want if you're building a reader mode or need to preserve formatting.
## Benchmark numbers
[![Feature comparison matrix for Trafilatura, readability-lxml, and Newspaper4k](https://www.contextractor.com/_next/static/media/feature-comparison-matrix.9d234934.svg)Feature comparison across extraction accuracy, output formats, language support, and more](https://www.contextractor.com/_next/static/media/feature-comparison-matrix.9d234934.svg "Feature comparison across extraction accuracy, output formats, language support, and more")
The ScrapingHub Article Extraction Benchmark is the closest thing this space has to a standard test suite. Here are the current numbers[2](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-scrapinghub-benchmark):  
| Tool  | F1  | Precision  | Recall  |  
| --- | --- | --- | --- |  
| Trafilatura 2.0.0  | 0.958  | 0.938  | 0.978  |  
| Newspaper4k 0.9.3.1  | 0.949  | 0.964  | 0.934  |  
| readability-lxml 0.8.4.1  | 0.922  | 0.913  | 0.931  |  
| goose3 3.1.20  | 0.896  | 0.940  | 0.856  |  
| jusText 3.0.2  | 0.804  | 0.858  | 0.756  |  
Trafilatura leads on F1. But look at the precision column — Newspaper4k actually beats it there (0.964 vs. 0.938). That means Newspaper4k is slightly better at not including junk, while Trafilatura is better at not missing content. The gap between those top two is small enough that on any given page you might see either win.
The Bevendorff et al. SIGIR 2023 study told a similar story from a different angle[3](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-bevendorff-sigir-2023). Across eight evaluation datasets, Trafilatura had the best overall mean F1 (0.883) while Readability (the JavaScript version — readability.js 0.6.0) had the highest median (0.970). A two-sample t-test found no statistically significant difference between the two on mean F1. So the honest answer is: Trafilatura and Readability are close, and which one "wins" depends on your dataset.
The Sandia National Laboratories evaluation from August 2024 confirmed similar rankings, with Trafilatura achieving the highest mean F1 (0.937) and precision (0.978)[4](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-sandia-2024).
One thing I want to flag: readability-lxml (the Python port) scores lower than readability.js (the JavaScript original) in every benchmark I've seen. The Python port is based on an older version of the algorithm and hasn't kept pace with the JavaScript implementation's improvements[5](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-readability-lxml-sync). If you can run Node.js, the JS version is measurably better. But for Python-only environments, readability-lxml is still solid.
## Output formats and metadata
This is where the differences really matter for practical use.
**Trafilatura** gives you seven output formats: plain text, Markdown, cleaned HTML, XML, XML-TEI (for academic corpus work), JSON with metadata fields, and CSV[6](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-trafilatura-docs). The TEI output is why it's popular in digital humanities — TEI is the de facto standard for encoded texts in that field. The JSON output bundles the extracted text with metadata (title, author, date, categories, tags, site name) in a single structure, which is convenient for pipeline work.
**readability-lxml** outputs HTML. That's it. One format. You get a `summary()` method that returns cleaned HTML wrapped in a `<body>` tag, and a `title()` method. No date, no author (well, version 0.8.2 added basic author extraction), no categories[7](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-readability-lxml-pypi). It's deliberately minimal.
**Newspaper4k** outputs plain text and gives you structured access to metadata through object properties: `article.text`, `article.authors`, `article.publish_date`, `article.top_image`, `article.movies`. With the NLP extra installed, it also generates `article.keywords` and `article.summary`[8](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-newspaper4k-docs). The CLI supports JSON and CSV export. It handles over 80 languages with auto-detection and language-specific tokenization for CJK scripts[9](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-newspaper4k-github).
For [content extraction for LLMs](https://www.contextractor.com/content-extraction-for-llms/), Trafilatura's Markdown output is probably the most useful — LLMs handle Markdown well, and you keep heading structure intact. For archival and academic work, TEI-XML from Trafilatura is hard to beat. For news-specific pipelines where you want author, date, and top image alongside text, Newspaper4k is the more natural fit.
## Where each one fails
I've run all three against a few hundred pages over the past year, and they each have predictable failure modes.
**Trafilatura** struggles with very short pages — product pages with two sentences of description and a big image gallery, for instance. The content scoring heuristic expects article-length text, and when there isn't much to work with, it sometimes returns nothing. Setting `favor_recall=True` helps, but then you pick up more noise on other pages. The `fast=True` mode skips the fallback chain (readability-lxml and jusText), which roughly doubles throughput but drops the safety net[6](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-trafilatura-docs).
**readability-lxml** falls apart on non-article pages. Forums, product listings, multi-column layouts — anything that doesn't look like a blog post or news article. It was designed for exactly one thing (isolating an article body), and it does that well, but hand it a page with multiple equally-weighted content sections and the output is unpredictable. Also, since it returns HTML, you still need a text extraction step if you want plain text. That's not a bug, it's a design choice — but it does mean more code on your end.
**Newspaper4k** is news-focused by design, and that shows. Give it a technical documentation page or a research paper and the extraction quality drops noticeably compared to Trafilatura. It also has more heavyweight dependencies — NLTK, lxml, Pillow for image handling — and the download/parse/nlp three-step API means you can't just hand it pre-downloaded HTML as easily. (You can, through `article.set_html()`, but it's less ergonomic than Trafilatura's `extract(html_string)` approach.)
None of them handle JavaScript-rendered pages. Single-page apps built with React, Vue, or Angular serve an empty shell; the actual content loads dynamically after JavaScript executes. You need a headless browser like Playwright to render the page first, then pass the resulting HTML to any of these tools. Same for paywalled content — authentication is a separate problem entirely. [Contextractor](https://www.contextractor.com/) solves both of these by running Playwright before Trafilatura.
## Cookie walls and ad-heavy pages
Cookie consent modals don't affect server-side extraction at all — they're JavaScript-driven overlays that only appear in a browser. When you fetch a page with `requests` or Trafilatura's built-in downloader, the underlying HTML usually contains the article text regardless of whether a cookie modal would have blocked it visually. The same goes for most ad containers; they're injected by JavaScript after page load.
The exceptions are sites that genuinely gate content server-side based on consent (GDPR-compliant implementations in the EU, mainly). For those, you need a browser session that clicks through the consent flow before extracting. But that's a browser automation problem, not an extraction library problem.
## Maintenance and community
As of March 2026:
**Trafilatura** — 5,596 GitHub stars, actively maintained by Adrien Barbaresi (BBAW research scientist). Version 2.0.0 shipped December 2024. Regular releases throughout 2024 (six releases that year). License switched from GPLv3 to Apache 2.0 at version 1.8.0. Used by HuggingFace, IBM, Microsoft Research, Stanford, and the Allen Institute[10](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-trafilatura-pypi)[11](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-barbaresi-acl-2021).
**readability-lxml** — 2,895 stars, maintained by Yuri Baburov. Version 0.8.4.1 released May 2025. Slower release cadence — a few releases per year. The codebase is small and stable, which means less need for constant updates, but it also means the algorithm hasn't tracked improvements in the JavaScript Readability.js it was originally ported from[7](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-readability-lxml-pypi).
**Newspaper4k** — 1,062 stars, maintained by Andrei Paraschiv. Forked from the original newspaper3k by codelucas, which hadn't been updated since September 2020[9](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fn-newspaper4k-github). Latest release 0.9.5 in February 2026. Active development with multiple releases per year and steady feature additions. MIT licensed.
The newspaper3k-to-Newspaper4k transition is worth knowing about. The original `newspaper` package on PyPI (newspaper3k) is effectively abandoned. If you see old tutorials referencing `pip install newspaper3k`, point them to `newspaper4k` instead — it's API-compatible and actually receives bug fixes.
## The extraction benchmark gap
The [benchmark numbers](https://www.contextractor.com/content-extraction-benchmark/) tell one story. Real-world pages tell another.
Benchmarks test on curated datasets of mostly well-structured news articles. They don't test on the weird stuff: government forms converted to HTML, email newsletters displayed in a web archive, Substack posts with heavy embeds, academic preprints rendered as HTML, or dynamically paginated content. In my experience, Trafilatura's fallback chain handles these edge cases better than the other two because it can try multiple strategies and pick the best result. Newspaper4k is the opposite — it's optimized for news and that's where it performs best.
If you're building a pipeline that processes a known type of content (news, blog posts, documentation), test all three on a sample of your actual pages. The benchmark F1 scores are a reasonable starting point, but your specific page structures matter more than aggregate numbers.
[![Decision flowchart for choosing between extraction tools](https://www.contextractor.com/_next/static/media/decision-flowchart.5244e35f.svg)Which extractor to pick based on your use case](https://www.contextractor.com/_next/static/media/decision-flowchart.5244e35f.svg "Which extractor to pick based on your use case")
## Quick reference  
|   | Trafilatura  | readability-lxml  | Newspaper4k  |  
| --- | --- | --- | --- |  
| **Best for**  | General extraction, corpora, LLM pipelines  | Reader modes, HTML preservation  | News aggregation, NLP features  |  
| **Install**  | `pip install trafilatura`  | `pip install readability-lxml`  | `pip install newspaper4k`  |  
| **Input**  | HTML string or URL  | HTML string  | URL (or HTML via `set_html()`)  |  
| **Output**  | Text, MD, HTML, XML, TEI, JSON, CSV  | HTML only  | Text + structured metadata  |  
| **CLI**  | Yes  | No  | Yes  |  
| **Speed**  | Fast (single-digit ms on cached HTML)  | Very fast (lxml only)  | Slower (download + parse + optional NLP)  |  
| **F1**  | 0.958  | 0.922  | 0.949  |  
| **License**  | Apache 2.0  | Apache 2.0  | MIT  |  
[Contextractor](https://www.contextractor.com/) uses Trafilatura as its extraction engine, paired with Playwright for JavaScript rendering — covering the gap that all three libraries share on their own.
  1. Newspaper4k: [PyPI package page](https://pypi.org/project/newspaper4k/). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-newspaper4k-pypi)
  2. ScrapingHub: [Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-scrapinghub-benchmark)
  3. Janek Bevendorff, Sanket Gupta, Johannes Kiesel, Benno Stein: [An Empirical Comparison of Web Content Extraction Algorithms](https://dl.acm.org/doi/10.1145/3539618.3591920). Proceedings of SIGIR 2023 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-bevendorff-sigir-2023)
  4. Sandia National Laboratories: [An Evaluation of Main Content Extraction Libraries](https://www.osti.gov/servlets/purl/2429881). SAND2024-10208, August 2024 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-sandia-2024)
  5. GitHub: [New port of readability.js? Issue #604](https://github.com/adbar/trafilatura/issues/604). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-readability-lxml-sync)
  6. Trafilatura: [Documentation](https://trafilatura.readthedocs.io/en/latest/). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-trafilatura-docs) [↩2](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-trafilatura-docs-2)
  7. readability-lxml: [PyPI package page](https://pypi.org/project/readability-lxml/). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-readability-lxml-pypi) [↩2](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-readability-lxml-pypi-2)
  8. Newspaper4k: [Documentation](https://newspaper4k.readthedocs.io/en/latest/). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-newspaper4k-docs)
  9. AndyTheFactory: [Newspaper4k GitHub repository](https://github.com/AndyTheFactory/newspaper4k). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-newspaper4k-github) [↩2](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-newspaper4k-github-2)
  10. Trafilatura: [PyPI package page](https://pypi.org/project/trafilatura/). Retrieved March 27, 2026 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-trafilatura-pypi)
  11. Adrien Barbaresi: [Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction](https://aclanthology.org/2021.acl-demo.15/). Proceedings of ACL-IJCNLP 2021: System Demonstrations, pp. 122-131 [↩](https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/#user-content-fnref-barbaresi-acl-2021)


Updated: March 26, 2026
[Home](https://www.contextractor.com/)[About](https://www.contextractor.com/about/)[Press kit](https://www.contextractor.com/press-kit/)[Library](https://www.contextractor.com/library/)[Help](https://www.contextractor.com/help/)[GitHub](https://github.com/contextractor/contextractor "Contextractor on GitHub")[Terms](https://www.contextractor.com/terms/)[Privacy](https://www.contextractor.com/privacy/)
