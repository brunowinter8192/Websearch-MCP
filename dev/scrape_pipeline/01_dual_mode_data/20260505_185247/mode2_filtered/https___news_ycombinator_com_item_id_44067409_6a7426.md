[FETCH]... ↓ https://news.ycombinator.com/item?id=44067409                      
| ✓ | ⏱: 1.88s 
[SCRAPE].. ◆ https://news.ycombinator.com/item?id=44067409                      
| ✓ | ⏱: 0.21s 
[COMPLETE] ● https://news.ycombinator.com/item?id=44067409                      
| ✓ | ⏱: 2.09s 
# Content from: https://news.ycombinator.com/item?id=44067409

|   
 | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomments) | [ask](https://news.ycombinator.com/ask) | [show](https://news.ycombinator.com/show) | [jobs](https://news.ycombinator.com/jobs) | [submit](https://news.ycombinator.com/submit)  |   |  
| --- | --- |  
 |  
|   
 | [Show HN: Defuddle, an HTML-to-Markdown alternative to Readability](https://github.com/kepano/defuddle)  |  
| --- |  
| 418 points by [kepano](https://news.ycombinator.com/user?id=kepano) [hide](https://news.ycombinator.com/hide?id=44067409&goto=item%3Fid%3D44067409) | [past](https://hn.algolia.com/?query=Show%20HN%3A%20Defuddle%2C%20an%20HTML-to-Markdown%20alternative%20to%20Readability&type=story&dateRange=all&sort=byDate&storyText=false&prefix&page=0) | [favorite](https://news.ycombinator.com/fave?id=44067409&auth=f0d17df20fc5401f175d9d69802bd16ba374959f) | [68 comments](https://news.ycombinator.com/item?id=44067409)  |  
| Defuddle is an open-source JS library I built to parse and extract the main content and metadata from web pages. It can also return the content as Markdown.I built Defuddle while working on Obsidian Web Clipper[1] (also MIT-licensed) because Mozilla's Readability[2] appears to be mostly abandoned, and didn't work well for many sites. It's still very much a work in progress, but I thought I'd share it today, in light of the announcement that Mozilla is shutting down Pocket. This library could be helpful to anyone building a read-it-later app. Defuddle is also available as a CLI: <https://github.com/kepano/defuddle-cli> [1] <https://github.com/obsidianmd/obsidian-clipper> [2] <https://github.com/mozilla/readability>  |  
|   
 |  [tmpfs](https://news.ycombinator.com/user?id=tmpfs) Interesting as I was researching this recently and certainly not impressed with the quality of the Readability implementations in various languages. Although Readability.js was clearly the best, it being Javascript didn't suit my project.In the end I found the python trifatura library to extract the best quality content with accurate meta data. You might want to compare your implementation to trifatura to see if there is room for improvement.  |  
| --- |  
 |  
|   
 |  [acrophobic](https://news.ycombinator.com/user?id=acrophobic) > ...it being Javascript didn't suit my project.If you're using Go, I maintain Go ports of Readability[0] and Trafilatura[1]. They're actively maintained, and for Trafilatura, the extraction performance is comparable to the Python version. [0]: <https://github.com/go-shiori/go-readability> [1]: <https://github.com/markusmobius/go-trafilatura>  |  
| --- |  
 |  
|   
 |  [derekperkins](https://news.ycombinator.com/user?id=derekperkins) We've been active users of go-trafilatura and love it  |  
| --- |  
 |  
|   
 |  [breadchris](https://news.ycombinator.com/user?id=breadchris) this is what i came here to see, thanks!  |  
| --- |  
 |  
|   
 |  [fabmilo](https://news.ycombinator.com/user?id=fabmilo) reference to the library: <https://trafilatura.readthedocs.io/en/latest/>for the curious: Trafilatura means "extrusion" in Italian. | This method creates a porous surface that distinguishes pasta trafilata for its extraordinary way of holding the sauce. search maccheroni trafilati vs maccheroni lisci :) (btw I think you meant trafilatura not trifatura)  |  
| --- |  
 |  
|   
 |  [thm](https://news.ycombinator.com/user?id=thm) Been using it since day one but development has stalled quite a bit since 2.0.0.  |  
| --- |  
 |  
|   
 |  [winddude](https://news.ycombinator.com/user?id=winddude) It's a bit old, but I bench marked a number of the web extraction tools years ago, <https://github.com/Nootka-io/wee-benchmarking-tool>, resiliparse-plain was my clear winner at the time.  |  
| --- |  
 |  
|   
 |  [creakingstairs](https://news.ycombinator.com/user?id=creakingstairs) I was just looking at obsidian web-clipper's source code because I've been quite impressed at its markdown conversion results and came across Defuddle in there. I'll be using for my bespoke read-it-later/ knowledge-base app, so thank you in advance :D  |  
| --- |  
 |  
|   
 |  [Tsarp](https://news.ycombinator.com/user?id=Tsarp) Been using the obsidian clipper since it was out and this is a really neat. The per website profile based extraction is awesome.Even if you are not a obsidian user, the markdown extraction quality is the most reliable Ive seen.  |  
| --- |  
 |  
|   
 |  [audessuscest](https://news.ycombinator.com/user?id=audessuscest) thanks for the tip!  |  
| --- |  
 |  
|   
 |  [jeanlucas](https://news.ycombinator.com/user?id=jeanlucas) Obsidian Web Clipper is a great tool to turn chatGPT conversations in markdown, or to just print it (believe me, it is a user case)  |  
| --- |  
 |  
|   
 |  [emaro](https://news.ycombinator.com/user?id=emaro) Not sure about other clients, but Kagi Assistant directly offers to save a conversation as Markdown. Using Obsidian's web-clipper is a good idea too though.  |  
| --- |  
 |  
|   
 |  [T0Bi](https://news.ycombinator.com/user?id=T0Bi) I just ask ChatGPT to provide the summary or whatever I need as a markdown file.  |  
| --- |  
 |  
|   
 |  [kouru225](https://news.ycombinator.com/user?id=kouru225) Is that a paid plugin?  |  
| --- |  
 |  
|   
 |  [jeanlucas](https://news.ycombinator.com/user?id=jeanlucas) It is free and open source: <https://github.com/obsidianmd/obsidian-clipper>  |  
| --- |  
 |  
|   
 |  [binarymax](https://news.ycombinator.com/user?id=binarymax) Really nice work. I appreciate the example with JSDOM as that’s exactly how I use readability, and this looks like a nice drop-in replacement.Question: How did you validate this? You say it works better than readability but I don’t see any tests or datasets in the repo to evaluate accuracy or coverage. Would it be possible to share that as well?  |  
| --- |  
 |  
|   
 |  [kepano](https://news.ycombinator.com/user?id=kepano) Currently I am relying on manual testing and user feedback, but yes, I'd like to add tests.Defuddle works quite differently from Readability. Readability tends to be overly conservative and tends to remove useful content because it tests blocks to find the beginning and end of the "main" content. Defuddle is able to run multiple passes and detect if it returned no content to try and expand its results. It also uses a greater variety of techniques to clean the content — for example, by using a page's mobile styles to detect content that can be hidden. Lastly, Defuddle is not only extracting the content but also standardizing the output (which Readability doesn't do). For example footnotes and code blocks all aim to output a single format, whereas Readability keeps the original DOM intact.  |  
| --- |  
 |  
|   
 |  [honodk123](https://news.ycombinator.com/user?id=honodk123) This looks great!I would love to give Defuddle a try as a Readability replacement. However, for my use case I want to do in a Chrome extension background script (service worker). I have not been able to get Defuddle to work, while readability does (when combining with linkedom). So basically, while this works: 
```
  import { parseHTML } from 'linkedom';
  ...
  private extractArticleWithReadability(html: string) {
      const { document } = parseHTML(html);
      const reader = new Readability(document);
      return reader.parse();
  }

```
This does not:
```
  import { parseHTML } from 'linkedom';
  ...
  private async extractArticleWithDefuddle(html: string) {
      const { document } = parseHTML(html);
      const result = new Defuddle(document);
      result.parse();
      return result;
  }


```
I get errors like:- Error in findExtractor: TypeError: Failed to construct 'URL': Invalid URL - Defuddle: Error evaluating media queries: TypeError: undefined is not iterable (cannot read property Symbol(Symbol.iterator)) - Defuddle Error processing document: TypeError: b.getComputedStyle is not a function Is there a way to run Defuddle in a chrome extension background script/service worker? Or do you have any plans of adding support for that?  |  
| --- |  
 |  
|   
 |  [shrinks99](https://news.ycombinator.com/user?id=shrinks99) I've been super happy with Obsidian Web Clipper! It's worked really well for me with the one exception of importing publish dates (which is more than forgivable !)  |  
| --- |  
 |  
|   
 |  [acrophobic](https://news.ycombinator.com/user?id=acrophobic) Is Mozilla's Readability really abandoned? The latest release (v0.6.0) is just 2 months ago, and its maintainer (Gijs) is pretty active on responding issues.  |  
| --- |  
 |  
|   
 |  [khasan222](https://news.ycombinator.com/user?id=khasan222) That codebase definitely leaves much to be desired, I’ve already had to fork it for work in order to fix some bugs.1 such bug, find a foreign language with commas in between numbers instead of periods, like Dutch(I think), and a lot of prices on the page. It’ll think all the numbers are relevant text. And of course I tried to open a pr and get it merged, but they require tests, and of course the tests don’t work on the page Im testing. It’s just very snafu imho  |  
| --- |  
 |  
|   
 |  [fabrice_d](https://news.ycombinator.com/user?id=fabrice_d) This seems to be [https://github.com/mozilla/readability/pull/853#issuecomment...](https://github.com/mozilla/readability/pull/853#issuecomment-2377435563) and I think their expectations are pretty reasonable.  |  
| --- |  
 |  
|   
 |  [khasan222](https://news.ycombinator.com/user?id=khasan222) Meh, maybe I'm standing too close to the problem, Idk. It is always frustrating trying to use a tool, and it not work though. I know it's free and all, but then I feel like helping people make good contributions is paramount in maintaining and fixing bugs.Clearly the comma thing is a bug, it's the lack of wanting to fix it actually that is a bit disheartening, and why I think it is a deadish repo  |  
| --- |  
 |  
|   
 |  [fabrice_d](https://news.ycombinator.com/user?id=fabrice_d) I don't know how you can interpret "we'd really like to make sure that the patch works and that we don't break it in the future" as "lack of wanting to fix it", but you do you.  |  
| --- |  
 |  
|   
 |  [rcarmo](https://news.ycombinator.com/user?id=rcarmo) The Python analogues seem to be well maintained. I did my own implementation of the Readability algorithm years ago and dropped it in favor them, and I have a few scrapers going strong with regular updates.  |  
| --- |  
 |  
|   
 |  [kepano](https://news.ycombinator.com/user?id=kepano) Are there any in particular you can recommend?  |  
| --- |  
 |  
|   
 |  [khimaros](https://news.ycombinator.com/user?id=khimaros) not parent, but this one looks maintained <https://github.com/buriy/python-readability>  |  
| --- |  
 |  
|   
 |  [novoreorx](https://news.ycombinator.com/user?id=novoreorx) I built a similar project called Substance [^0]. Unlike most readability tools that try to solve the problem once and for all, it takes a different approach. It provides a framework to define how each website should be handled, ensuring better results for each website covered.[^0]: <https://substance.reorx.com/>  |  
| --- |  
 |  
|   
 |  [Andr2Andr](https://news.ycombinator.com/user?id=Andr2Andr) Serious question - who and why would be using this tool? What is the use case? In other comments I have only seen exporting ChatGPT conversations to md  |  
| --- |  
 |  
|   
 |  [rollcat](https://news.ycombinator.com/user?id=rollcat) This is a library, not a tool. You can use it for a number of purposes:- Providing "reader mode" for your visitors - Using it in a browser extension to add reader mode - Scrapping - Plugging it into a [reverse] proxy that automatically removes unnecessary bloat from pages, for e.g. easier access on retro hardware <[https://web.archive.org/web/20240621144514/https://humungus....](https://web.archive.org/web/20240621144514/https://humungus.tedunangst.com/r/medium-rare)> (archive.org link, because the website goes down regularly)  |  
| --- |  
 |  
|   
 |  [degosuke](https://news.ycombinator.com/user?id=degosuke) I use LogSeq a lot - and having the option to scrape a website with only the text in MD seems like a great fit.  |  
| --- |  
 |  
|   
 |  [jonplackett](https://news.ycombinator.com/user?id=jonplackett) Does anyone know why readers don’t work for some websites where it looks like they should - ie normal article with lots of text.You just get a completely white page (on the iPhone reader). Usually it’s a news website. Is this the website intentionally obscuring the content to ensure they can serve their ads? If so how do they go about it?  |  
| --- |  
 |  
|   
 |  [miki123211](https://news.ycombinator.com/user?id=miki123211) Cookie and "we care about your privacy" banners are often the cause here, especially if you're in the EU / UK / possibly California[1].On some websites, those are just modals that obscure the content, something that reader mode can usually deal with just fine, but on others, they're implemented as redirects or rendered server-side. If reader mode doesn't work, dismiss those first and try again.  |  
| --- |  
 |  
|   
 |  [severusdd](https://news.ycombinator.com/user?id=severusdd) This is very cool! Given how messy and busy many websites have become, we really need a robust markdown converter that lets readers focus on reading the content. Nice to see something stepping up where Readability left off.Thank you for picking up this work :-)  |  
| --- |  
 |  
|   
 |  [busymom0](https://news.ycombinator.com/user?id=busymom0) In the playground, after I enter a url, I can't seem to figure out how to submit it to fetch the url? I tried pressing the return key on iOS keyboard but it didn't do anything. Am I missing something?  |  
| --- |  
 |  
|   
 |  [kepano](https://news.ycombinator.com/user?id=kepano) The input is there to test the url option — which I admit is a bit confusing, so I have removed it for now. I haven't found a good and free way to proxy requests from a GitHub page (yet).  |  
| --- |  
 |  
|   
 |  [ricardonunez](https://news.ycombinator.com/user?id=ricardonunez) I’ll give it a try. I’m not happy with my current setup for markdown to HTML on the wysiwyg editor I’m using, this may provide better results if I go with my own tool bar and editor.  |  
| --- |  
 |  
|   
 |  [ulrischa](https://news.ycombinator.com/user?id=ulrischa) I have build something similar:<https://devkram.de/markydown> but with php. Easy for self hosting  |  
| --- |  
 |  
|   
 |  [inhumantsar](https://news.ycombinator.com/user?id=inhumantsar) can confirm that readability seems to be on life support. I used it slurp, an obsidian plugin which serves the same basic purpose as web clipper, and always had a hard time getting PRs reviewed and merged.i started workin

[Content truncated...]
