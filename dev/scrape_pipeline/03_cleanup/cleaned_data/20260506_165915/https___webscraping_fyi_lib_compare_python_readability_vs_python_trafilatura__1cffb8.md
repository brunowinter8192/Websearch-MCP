<!-- source: https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/ -->


#  [readability](https://webscraping.fyi/lib/python/readability/)vs[trafilatura](https://webscraping.fyi/lib/python/trafilatura/)
[python](https://webscraping.fyi/lib/language/python) [scraper](https://webscraping.fyi/lib/tag/scraper)[html-extractor](https://webscraping.fyi/lib/tag/html-extractor)
[python](https://webscraping.fyi/lib/language/python) [scraper](https://webscraping.fyi/lib/tag/scraper)[html-extractor](https://webscraping.fyi/lib/tag/html-extractor)
Apache-2.0 37 5 [2,894](https://github.com/buriy/python-readability)
1.6 million (month) Jun 30 2011 [0.8.4.1](https://pypi.org/project/readability-lxml/)(1 years ago)
[5,650](https://github.com/adbar/trafilatura) 4 107 Apache-2.0
Jul 17 2019 5.2 million (month) [2.0.0](https://pypi.org/project/trafilatura/)(1 years ago)
* * *
python-readability is a python package that allows developers to extract the main content of a web page, removing any unnecessary or unwanted elements, such as ads, navigation, and sidebars. 
It is based on the algorithm used by the popular web-based service, Readability, and it uses the beautifulsoup4 package to parse the HTML and extract the main content.
Readability is similar to Newspaper in terms that it's extracting HTML data
Trafilatura is a Python package and command-line tool designed to gather text on the Web. It includes discovery, extraction and text processing components. Its main applications are web crawling, downloads, scraping, and extraction of main texts, metadata and comments. It aims at staying handy and modular: no database is required, the output can be converted to various commonly used formats.
Going from raw HTML to essential parts can alleviate many problems related to text quality, first by avoiding the noise caused by recurring elements (headers, footers, links/blogroll etc.) and second by including information such as author and date in order to make sense of the data. The extractor tries to strike a balance between limiting noise (precision) and including all valid parts (recall). It also has to be robust and reasonably fast, it runs in production on millions of documents.
This tool can be useful for quantitative research in corpus linguistics, natural language processing, computational social science and beyond: it is relevant to anyone interested in data science, information extraction, text mining, and scraping-intensive use cases like search engine optimization, business analytics or information security.
### Example Use
* * *
```python import requests from readability import document response = requests.get('http://example.com') doc = document(response.content) doc.title() 'example domain' doc.summary() """
\n
\n 
# example domain
\n 
this domain is established to be used for illustrative examples in documents. you may use this\n domain in examples without prior coordination or asking for permission.
\n 
[more information...](http://www.iana.org/domains/example)
\n
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
* * *
[html2text](https://webscraping.fyi/lib/python/html2text/)
[2,140](https://github.com/Alir3z4/html2text) [compare](https://webscraping.fyi/lib/compare/python-html2text-vs-python-readability/)
[trafilatura](https://webscraping.fyi/lib/python/trafilatura/)
[5,650](https://github.com/adbar/trafilatura) [compare](https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/)
[newspaper](https://webscraping.fyi/lib/python/newspaper/)
[15,018](https://github.com/codelucas/newspaper) [compare](https://webscraping.fyi/lib/compare/python-newspaper-vs-python-readability/)
[extruct](https://webscraping.fyi/lib/python/extruct/)
[961](https://github.com/scrapinghub/extruct) [compare](https://webscraping.fyi/lib/compare/python-extruct-vs-python-readability/)
[sumy](https://webscraping.fyi/lib/python/sumy/)
[3,670](https://github.com/miso-belica/sumy) [compare](https://webscraping.fyi/lib/compare/python-readability-vs-python-sumy/)
[gofeed](https://webscraping.fyi/lib/go/gofeed/)
[2,824](https://github.com/mmcdole/gofeed) [compare](https://webscraping.fyi/lib/compare/go-gofeed-vs-python-readability/)
[photon](https://webscraping.fyi/lib/python/photon/)
[12,807](https://github.com/s0md3v/Photon) [compare](https://webscraping.fyi/lib/compare/python-photon-vs-python-readability/)
[extractnet](https://webscraping.fyi/lib/python/extractnet/)
[297](https://github.com/currentslab/extractnet) [compare](https://webscraping.fyi/lib/compare/python-extractnet-vs-python-readability/)
[html2text](https://webscraping.fyi/lib/python/html2text/)
[2,140](https://github.com/Alir3z4/html2text) [compare](https://webscraping.fyi/lib/compare/python-html2text-vs-python-trafilatura/)
[readability](https://webscraping.fyi/lib/python/readability/)
[2,894](https://github.com/buriy/python-readability) [compare](https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/)
[newspaper](https://webscraping.fyi/lib/python/newspaper/)
[15,018](https://github.com/codelucas/newspaper) [compare](https://webscraping.fyi/lib/compare/python-newspaper-vs-python-trafilatura/)
[extruct](https://webscraping.fyi/lib/python/extruct/)
[961](https://github.com/scrapinghub/extruct) [compare](https://webscraping.fyi/lib/compare/python-extruct-vs-python-trafilatura/)
[youtube-dl](https://webscraping.fyi/lib/python/youtube-dl/)
[140,026](https://github.com/ytdl-org/youtube-dl) [compare](https://webscraping.fyi/lib/compare/python-trafilatura-vs-python-youtube-dl/)
[sumy](https://webscraping.fyi/lib/python/sumy/)
[3,670](https://github.com/miso-belica/sumy) [compare](https://webscraping.fyi/lib/compare/python-sumy-vs-python-trafilatura/)
[gofeed](https://webscraping.fyi/lib/go/gofeed/)
[2,824](https://github.com/mmcdole/gofeed) [compare](https://webscraping.fyi/lib/compare/go-gofeed-vs-python-trafilatura/)
[you-get](https://webscraping.fyi/lib/python/you-get/)
[56,813](https://github.com/soimort/you-get) [compare](https://webscraping.fyi/lib/compare/python-trafilatura-vs-python-you-get/)
[embed](https://webscraping.fyi/lib/php/embed/)
[2,103](https://github.com/oscarotero/Embed) [compare](https://webscraping.fyi/lib/compare/php-embed-vs-python-trafilatura/)
[embera](https://webscraping.fyi/lib/php/embera/)
[353](https://github.com/mpratt/Embera) [compare](https://webscraping.fyi/lib/compare/php-embera-vs-python-trafilatura/)
[photon](https://webscraping.fyi/lib/python/photon/)
[12,807](https://github.com/s0md3v/Photon) [compare](https://webscraping.fyi/lib/compare/python-photon-vs-python-trafilatura/)
[essence](https://webscraping.fyi/lib/php/essence/)
[769](https://github.com/essence/essence) [compare](https://webscraping.fyi/lib/compare/php-essence-vs-python-trafilatura/)
[extractnet](https://webscraping.fyi/lib/python/extractnet/)
[297](https://github.com/currentslab/extractnet) [compare](https://webscraping.fyi/lib/compare/python-extractnet-vs-python-trafilatura/)
Was this page helpful? 
Thanks for your feedback! 
Thanks for your feedback! Feel free to email suggestions to hello@webscraping.fyi
