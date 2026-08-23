<!-- source: https://justtothepoint.com/code/scrape/ -->

# Scraping Web Page Content with Python: Trafilatura, Readability, Newspaper3k & Playwright
> Behind this mask there is more than just flesh. Beneath this mask there is an idea… and ideas are bulletproof, Alan Moore
Scraping the main content from web pages is a common task for collecting articles, building datasets, or feeding information into various applications. However, not all web pages are created equal —some serve static HTML while others rely on JavaScript or PHP to render content dynamically— a single scraping method rarely suffices.
In this article, we explore four different Python libraries and techniques for extracting the main content from a webpage: Trafilatura, readability-lxml, Newspaper3k, and Playwright.
  1. Trafilatura is a Python library designed specifically for pulling out the main text from web pages. Trafilatura was created as a “command-line tool designed to gather text on the Web. It includes discovery, extraction and text processing components. Its main applications are web crawling, downloads, scraping, and extraction of main texts, metadata and comments.” **Trafilatura is quite robust and often succeeds on well-formed HTML pages. It’s an all-Python solution, doesn’t need a browser, and doesn’t require us to know the structure of the page beforehand so it’s relatively fast and lightweight**.
  2. Readability (readability-lxml) excels at cleansing a page of everything except the primary content. It is a Python package that allows developers to extract the main content of a web page, removing any unnecessary or unwanted elements, such as ads, navigation, and sidebars. Readability-lxml is also pure Python, lightweight, and quite fast for static HTML content.
  3. Newspaper3k is a popular Python library specifically for news article scraping and curation. It provides a high-level interface to get article text, authors, publish date, top image, and more from news sites. It is **a Python package that allows developers to easily extract text, images, and videos from articles on the web. It is designed to be fast, easy to use, and compatible with a wide variety of websites, using advanced algorithms to extract relevant information and metadata from articles**.
  4. Playwright is a browser automation framework that allows you to control a real web browser via code. It’s often used for end-to-end testing, but it’s extremely useful for web scraping when you encounter pages that load data dynamically with JavaScript. It can actually render the page like a normal user’s browser would, including waiting for network calls, executing scripts, etc. In this way, it can retrieve content that static HTML scrapers would miss.


### Trafilatura Key Features
  * **Crawling & Scraping**: Automatically follows sitemaps, RSS/Atom feeds, and HTML links — while avoiding traps like infinite loops or duplicate pages.
  * **Input Handling** : Works with live URLs, local HTML files, or pre-parsed BeautifulSoup objects.
  * **Extraction Engine** : Converts raw HTML into clean, usable text by stripping away non-essential elements like repetitive headers, footers, navigation links, and other noise.
  * **Inclusion of Metadata** : Preserves author names, publication dates, and relevant META tags whenever available.
  * **Output Formats** : Supports multiple formats including TXT, Markdown, CSV, JSON, HTML, XML, and TEI XML.
  * Others: Actively maintained with regular updates, new features, and optimizations. Comprehensive documentation available online. Widely used in academia and by companies and organizations.
  * **Installation:** Via `pip` (`pip install trafilatura`).


nvim myscrape.py:

```
import requests
import trafilatura
from readability import Document
# To use readability-lxml, install it: pip install readability-lxml
from newspaper import Article
# To install Newspaper3k: pip install newspaper3k
from playwright.sync_api import sync_playwright
# To use Playwright in Python, install it with pip install playwright.
# And then install a browser, e.g., playwright install chromium
from trafilatura.settings import use_config
from util import display_text_color, display_alarm_color, display_log_color
from colorama import Fore
from pathlib import Path
from utilollama import summarize
MIN_CONTENT_LENGTH = 200 # Minimum content length for successful scraping
# ------------------------------------------------------------------
# Fallback scrapers
# ------------------------------------------------------------------
def mytrafilatura(url: str, timeout: int = 10) -> str | None:
    Scrape the main content from the provided URL using Trafilatura.
    Trafilatura is a Python package and command-line tool designed to gather text on the Web.
    It includes discovery, extraction and text processing components.
    Its main applications are web crawling, downloads, scraping, and extraction of main texts, metadata and comments.
        url (str): The URL to scrape.
        timeout (int): The timeout duration for the request.
    Returns:
        str | None: Extracted content or None if no content is available.
    # Set the extraction timeout to 0 (infinite)
    config = use_config()
    config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
    # Fetch and extract content from the provided URL
    # This two-step process fetches the raw HTML and then extracts the main content
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return f"No content available at {url}"
    # By default, extract() will return a text string of the article content
    # We configure Trafilatura with no timeout on extraction and allow it to include links in the output (so that hyperlink texts aren’t lost).
    # This is done by setting include_links=True
    content = trafilatura.extract(
        downloaded,
        include_formatting=False,
        include_links=True,
        config=config
    return content
def readability(url: str, timeout: int = 10) -> str | None:
    Scrape content from the provided URL using Readability.
    python-readability is a python package that allows developers to extract the main content of a web page,
    removing any unnecessary or unwanted elements, such as ads, navigation, and sidebars.
        url (str): The URL from which to scrape content.
        timeout (int, optional): The maximum time (in seconds) to wait for an HTTP response.
                                 Default is 10 seconds.
    Returns:
        str | None: Returns the summarized content as a string. If the content cannot be retrieved
                     or an error occurs, returns None.
    # Since we manually fetch the page with requests, we added a standard User-Agent header in our code.
    # This is to avoid simple anti-scraping blocks.
    # By imitating a browser with "Mozilla/5.0", we improve our chances of success.
    # It's not perfect, but it's a start.
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    # Check if the content type is HTML
    if 'text/html' not in resp.headers.get('Content-Type', ''):
        return None
    resp.raise_for_status() # It ensures we only proceed if the HTTP response was successful (200 OK).
    # Otherwise, it will throw an exception, and our wrapper will catch it and move to the next method
    doc = Document(resp.text) # Parse the HTML
    return doc.summary().strip()
    # doc.summary() get the HTML snippet of the page’s main content.
    # We call .strip() on it just to remove any leading/trailing whitespace.
def newspaper(url: str) -> str | None:
    Scrape and extract the main content from a specified URL using the Newspaper3k library.
    Newspaper is an amazing python library for extracting & curating articles
    from news websites. It simplifies the process of gathering and processing article content.
        url (str): The URL of the article to scrape.
    Returns:
        str | None: Returns the main text of the article as a string. If the article cannot be
                     found or an error occurs, returns None.
    # Download and parse the article
    # Newspaper3k has its own Article class that handles downloading and parsing.
    # We passed language="en" in our code to hint that we expect English content.
    # We also set fetch_images=False since we only care about text here.
    art = Article(url, language="en", fetch_images=False)
        # Attempt to download and parse the article
        art.download() # Download the article content
        art.parse() # Parse the article content
    except Exception as e:
        # If an error occurs, print an error message
        print(f"Error fetching content from {url}: {e}")
        return None
    # Extract and return the main text
    return art.text.strip() if art.text else None # Return the main text or None
    # After parse(), attributes like art.text give us the main content
def playwright(url: str) -> str | None:
    Scrape content from a JavaScript-heavy site using Playwright.
    Playwright is a powerful browser automation toolkit that enables scraping of dynamic web content
    or web applications. This function is particularly useful for extracting content from pages
    that rely heavily on JavaScript for rendering.
        url (str): The URL of the page to scrape.
    Returns:
        str | None: Returns the main content of the loaded page as a string. If an error occurs
                     or the content cannot be retrieved, returns None.
    # Initialize Playwright
    with sync_playwright() as p:
        # We can choose either a Headful (With GUI) or Headless mod
        # Launch a headless browser for scraping
        browser = p.chromium.launch(headless=True)
        # Create page (aka a new browser tab) which we can navigate
        page = browser.new_page()
        page.goto(url) # Navigate to the specified URL
        # Wait for the network to become idle so that the page is fully loaded
        page.wait_for_load_state("networkidle")
        # Retrieve or grab the page's final HTML content.
        html = page.content()
        # Close the browser tab to free up resources.
        browser.close()
    # Run the HTML through readability to extract the main content and strip boilerplate
    return Document(html).summary()
# Combining Methods with a Fallback Strategy
# Ordered list of tuples: each has a name and the scraper to call
SCRAPERS = [
    ("trafilatura", mytrafilatura),
    ("readability", readability),
    ("newspaper3k", newspaper),
    ("playwright",  playwright),
# ------------------------------------------------------------------
# Public wrapper
# ------------------------------------------------------------------
def scrape_web_content(url: str) -> str:
    Scrape content from the given URL using a fallback strategy across multiple scrapers.
    The function attempts to extract and summarize content (Ollama) using various engines,
    returning the first successful result. Trafilatura's output is returned as-is.
        url (str): The URL to scrape.
    Returns:
        str: Extracted content or an empty string on failure.
    # Check if the URL is valid
    if not url.startswith(("http://", "https://")):
        display_text_color("Invalid URL format", Fore.RED)
        return ""
    # Display a log message
    display_log_color(f"Scraping: {url}")
    # The idea is to try each method in order, advancing to the next method if the current one fails
    # If one yields a good result, return it
    # If all methods fail, return an empty string
    for engine_name, fn in SCRAPERS:
            text = fn(url) # Call the scraping function
            if text and len(text)  MIN_CONTENT_LENGTH: # Check for sufficient content
            # This is a simple heuristic to decide if we probably got real content or just a short error message/empty result.
                # In our implementation, when using readability or the next methods, we also pass the content to a summarization function for additional processing.
                if engine_name != "trafilatura":
                    return summarize(text)
                    # If the method was Trafilatura (which likely already returns a clean summary of the text),
                    # we skipped the AI summarization and instead just displayed the raw content as-is.
                    display_text_color(f"Content from {url} as it is {text}")
                    return text
        except Exception as e:
            # If an exception is raised (for example, a network error or a parsing issue),...
            # it catches it, logs a message, and then tries the next one.
            display_alarm_color(f"[{engine_name}] failed: {e}")
            # Continue to the next scraper on failure
            continue
        # If we exit the loop without any method returning sufficient content, we log an error
        display_text_color("Could not extract meaningful content", Fore.RED)
        return ""
if __name__ == "__main__":
    scrape_web_content("https://gusiol.medium.com/nginx-proxy-and-portainer-multiple-applications-in-one-domain-d82efec0750f")

```

Scraping web pages can be challenging given the variety of site designs and the rise of client-side rendering. By leveraging a combination of tools, we can cover a wide spectrum of web pages. In our Python solution, we attempt a lightweight text-extraction (Trafilatura), then a reader-mode approach (readability-lxml), then a news article parser (Newspaper3k), and finally a headless browser (Playwright) to leave no stone unturned.
It gives us a very robust scraper that can handle almost everything from a simple blog post to a modern single-page app.
Bitcoin donation
[JustToThePoint](https://justtothepoint.com/) Copyright © 2011 - 2026 Anawim. ALL RIGHTS RESERVED. Bilingual e-books, articles, and videos to help your child and your entire family succeed, develop a healthy lifestyle, and have a lot of fun. [Social Issues](https://justtothepoint.com/en/library/social/), [Join us.](https://justtothepoint.com/en/library/contact/)
This website uses cookies to improve your navigation experience. By continuing, you are consenting to our use of cookies, in accordance with our [Cookies Policy](https://justtothepoint.com/contact/cookies-policy/) and [Website Terms and Conditions of use.](https://justtothepoint.com/contact/terms-and-conditions/)
