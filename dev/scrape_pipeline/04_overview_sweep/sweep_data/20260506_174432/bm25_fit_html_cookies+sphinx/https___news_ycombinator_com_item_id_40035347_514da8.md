<!-- source: https://news.ycombinator.com/item?id=40035347 -->

1. Throughly scraping the content of page (high recall)  
2. Dropping all the ads/auxilliary content (high precision)
- Run mozilla's readability on the page
- LLM checks readability output
- LLM extracts from markdown
Mozilla has released Readability as a standalone package so you can avoid spinning up a browser entirely:https://github.com/mozilla/readability
