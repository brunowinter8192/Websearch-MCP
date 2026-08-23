<!-- source: https://news.ycombinator.com/item?id=40035347 -->

|   
 |  |  
| --- |  
 |  
|   
 | screye | parent | context | favorite | on: Show HN: I made a tool to clean and convert any we...Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall)2. Dropping all the ads/auxilliary content (high precision)3. And getting the correct layout/section types (formatting)For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job.Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings. |  
| --- |  
|   
 | Thoroughly scraping is challenging, especially in an environment where you don’t have (or want) a JavaScript runtime.For content extraction, I found the approach the Postlight library takes quite neat. It scores individual html nodes based on some heuristics (text length, link density, css classes). It the selects the nodes with the highest score. [1] I ported it to Swift for a personal read later app.[1] https://github.com/postlight/parser |  
| --- |  
 |  
|   
 | For getting the HTML, you can use microlink, just passing the URL to https://html.microlink.io/{url}, like https://html.microlink.io/https://example.com |  
| --- |  
 |  
|   
 | This is pretty cool. Care to share your Swift port? |  
| --- |  
 |  
|   
 | Not planning to. It’s my first Swift/iOS project. I neither want to polish it nor maintain it publicly. Happy to share it privately, email is in the bio. I’m planning on a blog post describing the general approach though! |  
| --- |  
 |  
|   
 | Thanks for the links I had no idea those existed.For my article web scraper (wip) the current steps are:- Navigate with playwright + adblocker- Run mozilla's readability on the page- LLM checks readability outputIf check failed- Trim whole page HTML context- Convert to markdown with pandoc- LLM extracts from markdown |  
| --- |  
 |  
|   
 | Mozilla has released Readability as a standalone package so you can avoid spinning up a browser entirely: https://github.com/mozilla/readability |  
| --- |  
 |  
|   
 | I still wanted the browser for UBlock Origin and handling sites with heavy JS. I was using the standalone Readability script already but today I ended up dropping it for Trafilatura. It works a lot better.The inefficiency of using a browser rather than just taking the html doesn't really matter because the limiting factor is the LLM here.And yes the LLM is essential for getting clean data. None of the existing methods are flexible enough for all cases even if people say "you don't need AI to do this". |  
| --- |  
 |  
|   
 | you would still need to run. For js based websites. |  
| --- |  
 |  
|   
 | Those are pretty damn cool i didnt know those even existed. |  
| --- |  
 |  
 |  
|  |
