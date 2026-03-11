# Async All the Way: How I Built a High-Concurrency Web Crawler with ...
**URL:** https://python.plainenglish.io/async-all-the-way-how-i-built-a-high-concurrency-web-crawler-with-python-49974a4cc3ef
**Domain:** python.plainenglish.io
**Score:** 5.6
**Source:** scraped
**Query:** python async web scraping tutorial

---

[Sitemap](https://python.plainenglish.io/sitemap/sitemap.xml)
[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)
Sign up
Get app
Sign up
Follow publication
New Python content every day. Follow to join our 3.5M+ monthly readers.
Follow publication
Member-only story
# Async All the Way: How I Built a High-Concurrency Web Crawler with Python
Follow
4 min read Jun 13, 2025
Share
_An in-depth breakdown of using_` _aiohttp_`_,_`_asyncio_`_, and_` _BeautifulSoup_`_to scrape 10,000+ pages without melting my machine—or my mind._
Press enter or click to view image in full size
Photo by [Luca Bravo](https://unsplash.com/@lucabravo?utm_source=medium&utm_medium=referral) on [Unsplash](https://unsplash.com/?utm_source=medium&utm_medium=referral)
I used to think web scraping was easy. Write a script, loop through some URLs, save the data. Done. But once I tried to scrape 10,000 pages in under an hour, I hit a wall.
That’s when I realized: **traditional synchronous code won’t cut it**. What I needed was **non-blocking concurrency**. That’s how this project started — a high-performance, modular, async web crawler built entirely in Python.
If you’re still using `requests` and `for` loops to scrape, buckle up. This article walks through the real-world architecture, async patterns, and error-handling decisions I made to build a web crawler that felt less like a script—and more like a service.
## 1. Why Async: The Problem With Requests-Based Crawling
Here’s how most people scrape the web:
```
import requestsfrom bs4 import BeautifulSoupdef scrape(url):    response = requests.get(url)    soup = BeautifulSoup(response.text, 'html.parser')    return soup.title.string
```

Run that for a few hundred URLs, and your script becomes a bottleneck. It waits for each HTTP response…
## 
Create an account to read the full story.
The author made this story available to Medium members only.If you’re new to Medium, create a new account to read this story on us.
Or, continue in mobile web
Already have an account? 
Follow
## [Published in Python in Plain English](https://python.plainenglish.io/?source=post_page---post_publication_info--49974a4cc3ef---------------------------------------)
[Last published 1 hour ago](https://python.plainenglish.io/9-python-productivity-tricks-every-developer-should-learn-029eddca8d22?source=post_page---post_publication_info--49974a4cc3ef---------------------------------------)
New Python content every day. Follow to join our 3.5M+ monthly readers.
Follow
Follow
## [Written by Suleman Safdar](https://medium.com/@SulemanSafdar?source=post_page---post_author_info--49974a4cc3ef---------------------------------------)
Freelancer IT specialist web developer
Follow
## No responses yet
Write a response
Cancel
Respond
## More from Suleman Safdar and Python in Plain English
## [The Python Automation I Wrote to “Save Time” — and Accidentally Turned Into a Paid Service How a scrappy script for myself evolved into a system clients now pay for every month](https://medium.com/@SulemanSafdar/the-python-automation-i-wrote-to-save-time-and-accidentally-turned-into-a-paid-service-a39c6e3d8893?source=post_page---author_recirc--49974a4cc3ef----0---------------------6adb600a_4faf_4e4e_a421_db3e66c2e126--------------)
Feb 2
[ A clap icon287 A response icon4 ](https://medium.com/@SulemanSafdar/the-python-automation-i-wrote-to-save-time-and-accidentally-turned-into-a-paid-service-a39c6e3d8893?source=post_page---author_recirc--49974a4cc3ef----0---------------------6adb600a_4faf_4e4e_a421_db3e66c2e126--------------)
In
by
## [The Python Skills That Actually Get You Hired in 2026 (And How to Learn Them) Why “Knowing Python” Isn’t Enough Anymore](https://python.plainenglish.io/the-python-skills-that-actually-get-you-hired-in-2026-and-how-to-learn-them-0f0fc4eaf5e0?source=post_page---author_recirc--49974a4cc3ef----1--------

[Content truncated...]