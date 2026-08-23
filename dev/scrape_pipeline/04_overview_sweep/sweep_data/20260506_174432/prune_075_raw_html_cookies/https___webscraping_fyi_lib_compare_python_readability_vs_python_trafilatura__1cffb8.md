<!-- source: https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/ -->

# 
python-readability is a python package that allows developers to extract the main content of a web page, removing any unnecessary or unwanted elements, such as ads, navigation, and sidebars. 
It is based on the algorithm used by the popular web-based service, Readability, and it uses the beautifulsoup4 package to parse the HTML and extract the main content.
Readability is similar to Newspaper in terms that it's extracting HTML data
Trafilatura is a Python package and command-line tool designed to gather text on the Web. It includes discovery, extraction and text processing components. Its main applications are web crawling, downloads, scraping, and extraction of main texts, metadata and comments. It aims at staying handy and modular: no database is required, the output can be converted to various commonly used formats.
Going from raw HTML to essential parts can alleviate many problems related to text quality, first by avoiding the noise caused by recurring elements (headers, footers, links/blogroll etc.) and second by including information such as author and date in order to make sense of the data. The extractor tries to strike a balance between limiting noise (precision) and including all valid parts (recall). It also has to be robust and reasonably fast, it runs in production on millions of documents.
This tool can be useful for quantitative research in corpus linguistics, natural language processing, computational social science and beyond: it is relevant to anyone interested in data science, information extraction, text mining, and scraping-intensive use cases like search engine optimization, business analytics or information security.
### Example Use
```python import requests from readability import document response = requests.get('http://example.com') doc = document(response.content) doc.title() 'example domain' doc.summary() """
\n
\n 
# example domain
\n 
this domain is established to be used for illustrative examples in documents. you may use this\n domain in examples without prior coordination or asking for permission.
\n \n
\n\n
""" ```
```python
# it can be used to clean HTML files
from trafilatura import clean_html
html = '
My Title
This is some **bold** text.
' cleaned_html = clean_html(html) print(cleaned_html) 
# can strip away tags:
clean_html(html, tags_to_remove=["title"])
# or attributes
clean_html(html, attributes_to_remove=["title"]) ```
### Alternatives / Similar
