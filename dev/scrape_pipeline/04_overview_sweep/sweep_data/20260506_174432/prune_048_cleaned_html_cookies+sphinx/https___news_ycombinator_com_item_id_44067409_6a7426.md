<!-- source: https://news.ycombinator.com/item?id=44067409 -->

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
 |  [inhumantsar](https://news.ycombinator.com/user?id=inhumantsar) can confirm that readability seems to be on life support. I used it slurp, an obsidian plugin which serves the same basic purpose as web clipper, and always had a hard time getting PRs reviewed and merged.i started working on my own alternative but life (and web clipper) derailed the work. it's funny. somehow slurp keeps gaining new users even though web clipper exists. so i might have to refactor it to use your library sometime soon even though I don't use slurp myself anymore.  |  
| --- |  
 |  
|   
 |  [billconan](https://news.ycombinator.com/user?id=billconan) Are you using ai models behind the scenes? I saw Gemini and others in the code. I am asking mainly to understand the cost of using yours vs. readability. Thank!  |  
| --- |  
 |  
|   
 |  [kepano](https://news.ycombinator.com/user?id=kepano) No it's all rules-based. I think the code you're referring to is "extractors", which are website-specific rules that I'm working on to standardize the output from sites with comments threads (e.g. HN, Reddit) and conversational chats (ChatGPT, Claude, Gemini).  |  
| --- |  
 |  
|   
 |  [pugio](https://news.ycombinator.com/user?id=pugio) I would love something which reliably extracted a markdown back/forth from all the main LLM providers. I tried `defuddle` on a shared Gemini URL and it returned nothing but the "Sign In" link. Maybe I'm using your extractor wrong? How are you managing to get the rendered conversation HTML?  |  
| --- |  
 |  
|   
 |  [bambax](https://news.ycombinator.com/user?id=bambax) I think most LLM APIs return markdown and the conversion md->html happens after; so if you query the API directly you get markdown "for free".  |  
| --- |  
 |  
|   
 |  [ahsd1](https://news.ycombinator.com/user?id=ahsd1) Cool. Im looking for something similar but for stripping signatures and boilerplate disclaimers from html email. Could this work for that?  |  
| --- |  
 |  
|   
 |  [timdeve](https://news.ycombinator.com/user?id=timdeve) Looks good, I'm gonna try to swap readability in my RSS reader with this.And with Pocket going away I might have to add save it later to it...  |  
| --- |  
 |  
|   
 |  [90s_dev](https://news.ycombinator.com/user?id=90s_dev) Neat. With ~3 more lines of code, you could get a URL and render it in simpler HTML and be a full fledged replacement.  |  
| --- |  
 |  
|   
 |  [infogulch](https://news.ycombinator.com/user?id=infogulch) Since it's written in javascript is there any chance it could be packaged as a bookmarklet?  |  
| --- |  
 |  
|   
 |  [khaki54](https://news.ycombinator.com/user?id=khaki54) seems pretty much perfect including obsidian clipper. Thanks!  |  
| --- |  
 |  
|   
 |  [revskill](https://news.ycombinator.com/user?id=revskill) Interesting that Markdown does not support form element.  |  
| --- |  
 |  
|   
 |  [miketromba](https://news.ycombinator.com/user?id=miketromba) Excellent work. A modern alternative to readability was much needed. This is especially useful for building clean web context for LLMs. Thanks for open-sourcing this!  |  
| --- |  
 |  
|   
 |  [elcritch](https://news.ycombinator.com/user?id=elcritch) I found LLMs are really good at taking a web page and transforming it to markdown. Well rather commercial LLMs like Claude and Gemini are.Unfortunately I tried a bunch of hugging face mode on a I could run on my MacBook and all of them ignored my prompts despite trying every variation I could think of. Half the time they just tried summarizing it and describing what JavaScript was. :/  |  
| --- |  
 |  
|   
 |  [ioma8](https://news.ycombinator.com/user?id=ioma8) Tried it on some webpages, doesnt work well.  |  
| --- |  
 |  
|   
 |  [input_sh](https://news.ycombinator.com/user?id=input_sh) A bit off-topic, but I'm very excited to see the launch of Bases! I've obsessively followed the roadmap for like a year awaiting this day and have been frequently disappointed to still see it stuck somewhere under "planned".Not that I didn't already implement a read-it-later solution with Obsidian+Dataview, but this definitely makes things simpler!  |  
| --- |  
 |  
|   
 |  [jeanlucas](https://news.ycombinator.com/user?id=jeanlucas) Didn't it release just some days ago?  |  
| --- |  
 |  
|   
 |  [sn0n](https://news.ycombinator.com/user?id=sn0n) Bases?  |  
| --- |  
 |  
|   
 |  [input_sh](https://news.ycombinator.com/user?id=input_sh) <https://help.obsidian.md/bases>Note that I'm using a preview (catalyst) version, it will reach stable soon. I'm assuming kepano will submit it here then.  |  
| --- |  
 |  
|   
 |  [fkfyshroglk](https://news.ycombinator.com/user?id=fkfyshroglk) For those not in the know: [Readability](<https://github.com/mozilla/readability>)  |  
| --- |  
 |  
|   
 |  [andrethegiant](https://news.ycombinator.com/user?id=andrethegiant) [flagged]  |  
| --- |  
 |  
|   
 |  [simpaticoder](https://news.ycombinator.com/user?id=simpaticoder) Interesting. How do you avoid users misusing such a tool? How do users know you won't misuse the tool against users? On a technical note, do you rotate IP's on each request, even for sub-resources of the same page?  |  
| --- |  
 |  
|   
 |  [ghilston](https://news.ycombinator.com/user?id=ghilston) Interesting! Your website does not explain what the free tier limits are. Can you explain those?  |  
| --- |  
 |  
|   
 |  [andrethegiant](https://news.ycombinator.com/user?id=andrethegiant) Free tier (i.e. using API keys but without a paid subscription) is rate-limited to 10 requests per minute. <https://pure.md/docs/#section/Rate-limits>  |  
| --- |  
 |  
|   
 |  [ghilston](https://news.ycombinator.com/user?id=ghilston) Thanks!  |  
| --- |  
 |  
|   
 |  [latchkey](https://news.ycombinator.com/user?id=latchkey) [flagged]  |  
| --- |  
 |  
|   
 |  [kepano](https://news.ycombinator.com/user?id=kepano) Feel free to help :)  |  
| --- |  
 |  
|   
 |  [latchkey](https://news.ycombinator.com/user?id=latchkey) As an open source developer for 3 decades now, I used to have this flippant attitude. Trust me when I say, it doesn't work.Build the framework for tests and then require anyone who wants to help build the product to write tests with their PRs. You can't just push some code out there and expect people to "feel free to help", it doesn't happen, and is quite a turnoff. To the downvoters, this is what I see as valid feedback to a rather flippant response.  |  
| --- |  
 |  
|   
 |  [jeanlucas](https://news.ycombinator.com/user?id=jeanlucas) You just wanted to complain and not add anything? Not really getting your point at all  |  
| --- |  
 |  
|   
 |  [latchkey](https://news.ycombinator.com/user?id=latchkey) Sorry you're not getting my point. It isn't a complaint. I'm responding to a rather flippant "feel free to help" with some advice from someone who's been doing this a long time.I've got a project that has been going for 6 years now and attracted 500 stars and gets 49k downloads a month. It works because it has comprehensive unit tests and people can rely on it. When I was just starting out on that project, I didn't tell people to feel free to help. I put the effort in. It is important to lay the groundwork beyond just writing the utility.  |  
| --- |  
 |  
|   
 |  [m0zzie](https://news.ycombinator.com/user?id=m0zzie) Apologies if you already know this, but I noticed you’re getting flagged so thought I’d add some context: the author is the CEO of Obsidian and has a few successful projects, so bragging about your 500 stars and saying things like “when I was just starting out, I didn't tell people to feel free to help. I put the effort in” is probably rubbing people the wrong way.  |  
| --- |  
 |  
|   
 |  [latchkey](https://news.ycombinator.com/user?id=latchkey) Clarified "starting out on that project". I've been doing this for 30 years and I'm also a CEO. I've had multiple successful projects, like starting Java@Apache and open sourcing Tomcat.I made a lot of mistakes along the way and one of them was being flippant on my responses to people like that. Just sharing my insights.  |  
| --- |  
 |  
|   
 |  [m0zzie](https://news.ycombinator.com/user?id=m0zzie) Your follow up post and edits help with clarifying the tone, hopefully readers see that.  |  
| --- |  
 |  
 |  
|  [Consider applying for YC's Summer 2026 batch! Applications are open till May 4](https://www.ycombinator.com/apply/) [Guidelines](https://news.ycombinator.com/newsguidelines.html) | [FAQ](https://news.ycombinator.com/newsfaq.html) | [Lists](https://news.ycombinator.com/lists) | [API](https://github.com/HackerNews/API) | [Security](https://news.ycombinator.com/security.html) | [Legal](https://www.ycombinator.com/legal/) | [Apply to YC](https://www.ycombinator.com/apply/) | Contact  |
