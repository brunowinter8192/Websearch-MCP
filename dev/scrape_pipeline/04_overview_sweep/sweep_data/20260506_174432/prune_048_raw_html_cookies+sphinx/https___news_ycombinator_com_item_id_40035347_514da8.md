<!-- source: https://news.ycombinator.com/item?id=40035347 -->

|   
 | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomments) | [ask](https://news.ycombinator.com/ask) | [show](https://news.ycombinator.com/show) | [jobs](https://news.ycombinator.com/jobs) | [submit](https://news.ycombinator.com/submit) |  |  
| --- | --- |  
 |  
|   
 | [screye](https://news.ycombinator.com/user?id=screye) [on April 14, 2024](https://news.ycombinator.com/item?id=40035347) | [parent](https://news.ycombinator.com/item?id=40033490) | [context](https://news.ycombinator.com/item?id=40033490#40035347) | [favorite](https://news.ycombinator.com/fave?id=40035347&auth=2505d90644bb16ef9a5f86de5764312284bcdd6a) | on: [Show HN: I made a tool to clean and convert any we...](https://news.ycombinator.com/item?id=40033490 "Show HN: I made a tool to clean and convert any webpage to Markdown") Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall)2. Dropping all the ads/auxilliary content (high precision)3. And getting the correct layout/section types (formatting)For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job.Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings. |  
| --- |  
|   
 | [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40037718) Thoroughly scraping is challenging, especially in an environment where you don’t have (or want) a JavaScript runtime.For content extraction, I found the approach the Postlight library takes quite neat. It scores individual html nodes based on some heuristics (text length, link density, css classes). It the selects the nodes with the highest score. [1] I ported it to Swift for a personal read later app.[1] <https://github.com/postlight/parser> |  
| --- |  
 |  
|   
 | [Kikobeats](https://news.ycombinator.com/user?id=Kikobeats) [on April 20, 2024](https://news.ycombinator.com/item?id=40101653) For getting the HTML, you can use microlink, just passing the URL to <https://html.microlink.io/{url}>, like <https://html.microlink.io/https://example.com> |  
| --- |  
 |  
|   
 | [justech](https://news.ycombinator.com/user?id=justech) [on April 15, 2024](https://news.ycombinator.com/item?id=40038016) This is pretty cool. Care to share your Swift port? |  
| --- |  
 |  
|   
 | [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40038118) Not planning to. It’s my first Swift/iOS project. I neither want to polish it nor maintain it publicly. Happy to share it privately, email is in the bio. I’m planning on a blog post describing the general approach though! |  
| --- |  
 |  
|   
 | [rismay](https://news.ycombinator.com/user?id=rismay) [on April 15, 2024](https://news.ycombinator.com/item?id=40045130) Care to share the Swift port? |  
| --- |  
 |  
|   
 | [msp26](https://news.ycombinator.com/user?id=msp26) [on April 15, 2024](https://news.ycombinator.com/item?id=40038447) Thanks for the links I had no idea those existed.For my article web scraper (wip) the current steps are:- Navigate with playwright + adblocker- Run mozilla's readability on the page- LLM checks readability outputIf check failed- Trim whole page HTML context- Convert to markdown with pandoc- LLM extracts from markdown |  
| --- |  
 |  
|   
 | [privatenumber](https://news.ycombinator.com/user?id=privatenumber) [on April 15, 2024](https://news.ycombinator.com/item?id=40041158) Mozilla has released Readability as a standalone package so you can avoid spinning up a browser entirely: <https://github.com/mozilla/readability> |  
| --- |  
 |  
|   
 | [msp26](https://news.ycombinator.com/user?id=msp26) [on April 15, 2024](https://news.ycombinator.com/item?id=40042259) I still wanted the browser for UBlock Origin and handling sites with heavy JS. I was using the standalone Readability script already but today I ended up dropping it for Trafilatura. It works a lot better.The inefficiency of using a browser rather than just taking the html doesn't really matter because the limiting factor is the LLM here.And yes the LLM is essential for getting clean data. None of the existing methods are flexible enough for all cases even if people say "you don't need AI to do this". |  
| --- |  
 |  
|   
 | [asadalt](https://news.ycombinator.com/user?id=asadalt) [on April 15, 2024](https://news.ycombinator.com/item?id=40041459) you would still need to run. For js based websites. |  
| --- |  
 |  
|   
 | [cchance](https://news.ycombinator.com/user?id=cchance) [on April 15, 2024](https://news.ycombinator.com/item?id=40037017) Those are pretty damn cool i didnt know those even existed. |  
| --- |  
 |  
 |  
|  [Guidelines](https://news.ycombinator.com/newsguidelines.html) | [FAQ](https://news.ycombinator.com/newsfaq.html) | [Lists](https://news.ycombinator.com/lists) | [API](https://github.com/HackerNews/API) | [Security](https://news.ycombinator.com/security.html) | [Legal](https://www.ycombinator.com/legal/) | [Apply to YC](https://www.ycombinator.com/apply/) | Contact  |
