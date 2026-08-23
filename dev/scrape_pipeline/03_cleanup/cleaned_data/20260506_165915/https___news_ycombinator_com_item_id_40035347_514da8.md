<!-- source: https://news.ycombinator.com/item?id=40035347 -->


 |   | [](https://news.ycombinator.com/vote?id=40035347&how=up&goto=item%3Fid%3D40035347)  |  [screye](https://news.ycombinator.com/user?id=screye) [on April 14, 2024](https://news.ycombinator.com/item?id=40035347) | [parent](https://news.ycombinator.com/item?id=40033490) | [context](https://news.ycombinator.com/item?id=40033490#40035347) | [favorite](https://news.ycombinator.com/fave?id=40035347&auth=2505d90644bb16ef9a5f86de5764312284bcdd6a) | on: [Show HN: I made a tool to clean and convert any we...](https://news.ycombinator.com/item?id=40033490 "Show HN: I made a tool to clean and convert any webpage to Markdown")   
Converting websites to markdown comes with 3 distinct problems:1. Throughly scraping the content of page (high recall) 2. Dropping all the ads/auxilliary content (high precision) 3. And getting the correct layout/section types (formatting) For #2 and #3 - Trafilatura, Newspaper4k and python-readability based solutions work best out of the box. For #1, any scraping service + selenium is going to do a great job. Could you elaborate on what your tool does different or better? The area has been stagnant for a while. So curious to hear your learnings.  |  
| --- | --- | --- |  
|   |   |  
  
  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40037718&how=up&goto=item%3Fid%3D40035347)  |  [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40037718) | [next](https://news.ycombinator.com/item?id=40035347#40038447) [[–]](javascript:void\(0\))   
Thoroughly scraping is challenging, especially in an environment where you don’t have (or want) a JavaScript runtime.For content extraction, I found the approach the Postlight library takes quite neat. It scores individual html nodes based on some heuristics (text length, link density, css classes). It the selects the nodes with the highest score. [1] I ported it to Swift for a personal read later app. [1] <https://github.com/postlight/parser>  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40101653&how=up&goto=item%3Fid%3D40035347)  |  [Kikobeats](https://news.ycombinator.com/user?id=Kikobeats) [on April 20, 2024](https://news.ycombinator.com/item?id=40101653) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [next](https://news.ycombinator.com/item?id=40035347#40038016) [[–]](javascript:void\(0\))   
For getting the HTML, you can use microlink, just passing the URL to [https://html.microlink.io/{url}](https://html.microlink.io/%7Burl%7D), like <https://html.microlink.io/https://example.com>  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40038016&how=up&goto=item%3Fid%3D40035347)  |  [justech](https://news.ycombinator.com/user?id=justech) [on April 15, 2024](https://news.ycombinator.com/item?id=40038016) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [prev](https://news.ycombinator.com/item?id=40035347#40101653) | [next](https://news.ycombinator.com/item?id=40035347#40045130) [[–]](javascript:void\(0\))   
This is pretty cool. Care to share your Swift port?  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40038118&how=up&goto=item%3Fid%3D40035347)  |  [scary-size](https://news.ycombinator.com/user?id=scary-size) [on April 15, 2024](https://news.ycombinator.com/item?id=40038118) | [root](https://news.ycombinator.com/item?id=40035347#40037718) | [parent](https://news.ycombinator.com/item?id=40035347#40038016) | [next](https://news.ycombinator.com/item?id=40035347#40045130) [[–]](javascript:void\(0\))   
Not planning to. It’s my first Swift/iOS project. I neither want to polish it nor maintain it publicly. Happy to share it privately, email is in the bio. I’m planning on a blog post describing the general approach though!  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40045130&how=up&goto=item%3Fid%3D40035347)  |  [rismay](https://news.ycombinator.com/user?id=rismay) [on April 15, 2024](https://news.ycombinator.com/item?id=40045130) | [parent](https://news.ycombinator.com/item?id=40035347#40037718) | [prev](https://news.ycombinator.com/item?id=40035347#40038016) | [next](https://news.ycombinator.com/item?id=40035347#40038447) [[–]](javascript:void\(0\))   
Care to share the Swift port?  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40038447&how=up&goto=item%3Fid%3D40035347)  |  [msp26](https://news.ycombinator.com/user?id=msp26) [on April 15, 2024](https://news.ycombinator.com/item?id=40038447) | [prev](https://news.ycombinator.com/item?id=40035347#40037718) | [next](https://news.ycombinator.com/item?id=40035347#40037017) [[–]](javascript:void\(0\))   
Thanks for the links I had no idea those existed.For my article web scraper (wip) the current steps are: - Navigate with playwright + adblocker - Run mozilla's readability on the page - LLM checks readability output If check failed - Trim whole page HTML context - Convert to markdown with pandoc - LLM extracts from markdown  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40041158&how=up&goto=item%3Fid%3D40035347)  |  [privatenumber](https://news.ycombinator.com/user?id=privatenumber) [on April 15, 2024](https://news.ycombinator.com/item?id=40041158) | [parent](https://news.ycombinator.com/item?id=40035347#40038447) | [next](https://news.ycombinator.com/item?id=40035347#40037017) [[–]](javascript:void\(0\))   
Mozilla has released Readability as a standalone package so you can avoid spinning up a browser entirely: <https://github.com/mozilla/readability>  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40042259&how=up&goto=item%3Fid%3D40035347)  |  [msp26](https://news.ycombinator.com/user?id=msp26) [on April 15, 2024](https://news.ycombinator.com/item?id=40042259) | [root](https://news.ycombinator.com/item?id=40035347#40038447) | [parent](https://news.ycombinator.com/item?id=40035347#40041158) | [next](https://news.ycombinator.com/item?id=40035347#40041459) [[–]](javascript:void\(0\))   
I still wanted the browser for UBlock Origin and handling sites with heavy JS. I was using the standalone Readability script already but today I ended up dropping it for Trafilatura. It works a lot better.The inefficiency of using a browser rather than just taking the html doesn't really matter because the limiting factor is the LLM here. And yes the LLM is essential for getting clean data. None of the existing methods are flexible enough for all cases even if people say "you don't need AI to do this".  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40041459&how=up&goto=item%3Fid%3D40035347)  |  [asadalt](https://news.ycombinator.com/user?id=asadalt) [on April 15, 2024](https://news.ycombinator.com/item?id=40041459) | [root](https://news.ycombinator.com/item?id=40035347#40038447) | [parent](https://news.ycombinator.com/item?id=40035347#40041158) | [prev](https://news.ycombinator.com/item?id=40035347#40042259) | [next](https://news.ycombinator.com/item?id=40035347#40037017) [[–]](javascript:void\(0\))   
you would still need to run. For js based websites.  |  
| --- | --- | --- |  
 |  
|   
 | ![](https://news.ycombinator.com/s.gif)  | [](https://news.ycombinator.com/vote?id=40037017&how=up&goto=item%3Fid%3D40035347)  |  [cchance](https://news.ycombinator.com/user?id=cchance) [on April 15, 2024](https://news.ycombinator.com/item?id=40037017) | [prev](https://news.ycombinator.com/item?id=40035347#40038447) | [next](https://news.ycombinator.com/item?id=40035347#40036530) [[–]](javascript:void\(0\))   
Those are pretty damn cool i didnt know those even existed.  |  
| --- | --- | --- |  
 |  
  
  
 |  
|  ![](https://news.ycombinator.com/s.gif)  
 |  |  
| --- |  
  
[Guidelines](https://news.ycombinator.com/newsguidelines.html) | [FAQ](https://news.ycombinator.com/newsfaq.html) | [Lists](https://news.ycombinator.com/lists) | [API](https://github.com/HackerNews/API) | [Security](https://news.ycombinator.com/security.html) | [Legal](https://www.ycombinator.com/legal/) | [Apply to YC](https://www.ycombinator.com/apply/) | Contact  
  
Search:   |
