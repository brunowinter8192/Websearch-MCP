<!-- source: https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/ -->

Skip to content 
Web Scraping FYI 
Comparison of python readability vs trafilatura libraries 
Type to start searching


  * What is Web Scraping 
  * How to Scrape 
  * Tools & Technologies 
  * Libraries 
  * Scrapers 


Web Scraping FYI 
  * What is Web Scraping 
    * What is Web Scraping? 
    * Web Scraping vs Web Crawling 
    * Is Web Scraping Legal? 
  * How to Scrape 
    * Scrape Static Pages 
    * Parse HTML Data 
    * Find Hidden Data 
    * Scrape Dynamic Pages 
    * Automate Browsers 
    * Avoid Getting Blocked 
    * Scale Your Scraper 
  * Tools & Technologies 
    * Languages & HTTP Clients 
    * Scraping Frameworks 
    * Browser Automation 
    * Browser Libraries 
    * Anti-Bot Protections 
    * Scraping APIs 
    * Developer Tools 
    * How HTTP Works 
    * How HTML Works 
    * How JavaScript Works 
    * How JSON Works 
    * Popular Tools 
    * Communities 
  * Libraries 
    * Python 
    * Javascript 
    * Php 
    * Go 
    * Ruby 
    * R 
  * Scrapers 
    * E-Commerce 
      * How to Scrape Amazon 
      * How to Scrape Walmart 
      * How to Scrape eBay 
      * How to Scrape Etsy 
      * How to Scrape AliExpress 
      * How to Scrape Best Buy 
      * How to Scrape StockX 
      * How to Scrape Nordstrom 
      * How to Scrape Goat 
      * How to Scrape Fashionphile 
      * How to Scrape Vestiaire Collective 
      * How to Scrape Allegro 
    * Real Estate 
      * How to Scrape Zillow 
      * How to Scrape Realtor.com 
      * How to Scrape Redfin 
      * How to Scrape Zoopla 
      * How to Scrape Rightmove 
      * How to Scrape Realestate.com.au 
      * How to Scrape Idealista 
      * How to Scrape ImmobilienScout24 
      * How to Scrape Immowelt 
      * How to Scrape Homegate 
      * How to Scrape SeLoger 
      * How to Scrape Leboncoin 
    * Social Media 
      * How to Scrape Instagram 
      * How to Scrape TikTok 
      * How to Scrape Twitter/X 
      * How to Scrape Reddit 
      * How to Scrape Threads 
      * How to Scrape YouTube 
    * Jobs & Business 
      * How to Scrape LinkedIn 
      * How to Scrape Indeed 
      * How to Scrape Glassdoor 
      * How to Scrape Wellfound 
      * How to Scrape ZoomInfo 
      * How to Scrape Crunchbase 
      * How to Scrape G2 
    * Reviews & Travel 
      * How to Scrape Trustpilot 
      * How to Scrape Yelp 
      * How to Scrape YellowPages 
      * How to Scrape TripAdvisor 
      * How to Scrape Booking.com 
    * Search & Other 
      * How to Scrape Google 
      * How to Scrape Bing 
      * How to Scrape SimilarWeb 
      * How to Scrape Domain.com 


  * Example Use 


#  readabilityvstrafilatura
python scraperhtml-extractor
Apache-2.0 37 5 2,894
1.6 million (month) Jun 30 2011 0.8.4.1(1 years ago)
5,650 4 107
Jul 17 2019 5.2 million (month) 2.0.0
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
more information...
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
html2text
2,140 compare
trafilatura
newspaper
15,018
extruct
961
sumy
3,670
gofeed
2,824
photon
12,807
extractnet
297
readability
youtube-dl
140,026
you-get
56,813
embed
2,103
embera
353
essence
769
Was this page helpful? 
Thanks for your feedback! 
Thanks for your feedback! Feel free to email suggestions to hello@webscraping.fyi 
