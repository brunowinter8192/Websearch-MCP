<!-- source: https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html -->

[Skip to content](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#h1)
  * [ Seirdy’s Home ](https://seirdy.one/)
  * [ **Articles** ](https://seirdy.one/posts/)
  * [ Notes ](https://seirdy.one/notes/)
  * [ Bookmarks ](https://seirdy.one/bookmarks/)
  * [ About ](https://seirdy.one/about/)
  * [ Meta ](https://seirdy.one/meta/)
  * [ Support ](https://seirdy.one/support/)


# A look at search engines with their own indexes
  * Posted 2021-03-10 by [![](https://seirdy.one/favicon.1250396055.png) Seirdy](https://seirdy.one/) on their [Website](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/) and [Gemini capsule](gemini://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/index.gmi). 
  * Last updated 2025-07-01. [Changelog](https://git.sr.ht/~seirdy/seirdy.one/log/master/item/content/posts/search-engines-with-own-indexes.md)
  * About 7 thousand words; a long 37 minute read


* * *
## Preface
This is a cursory review of all the indexing search engines I have been able to find.
The three dominant English search engines with their own indexes[note 1](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:1) are Google, Bing, and Yandex (GBY). Many alternatives to GBY exist, but almost none of them have their own results; instead, they just source their results from GBY.
With that in mind, I decided to test and catalog all the different indexing search engines I could find. I prioritized breadth over depth, and encourage readers to try the engines out themselves if they’d like more information.
This page is a “living document” that I plan on updating indefinitely. Check for updates once in a while if you find this page interesting. Feel free to send me suggestions, updates, and corrections; I’d especially appreciate help from those who speak languages besides English and can evaluate a non-English indexing search engine. Contact info is in the article footer.
I plan on updating the engines in the top two categories with more info comparing the structured/linked data the engines leverage (RDFa vocabularies, microdata, microformats, JSON-LD, etc.) to help authors determine which formats to use.
Toggle table of contents
## Table of Contents
  1. [About the list](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#about-the-list)
  2. [General indexing search-engines](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#general-indexing-search-engines)
    1. [Large indexes, good results](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#large-indexes-good-results)
    2. [Smaller indexes or less relevant results](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#smaller-indexes-or-less-relevant-results)
    3. [Smaller indexes, hit-and-miss](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#smaller-indexes-hit-and-miss)
    4. [Fledgling engines](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fledgling-engines)
    5. [Semi-independent indexes](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#semi-independent-indexes)
  3. [Non-generalist search](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#non-generalist-search)
    1. [Small or non-commercial Web](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#small-or-non-commercial-web)
    2. [Site finders](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#site-finders)
    3. [Other](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#other)
  4. [Other languages](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#other-languages)
    1. [Big indexes](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#big-indexes)
    2. [Smaller indexes](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#smaller-indexes)
  5. [Almost qualified](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#almost-qualified)
  6. [Misc](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#misc)
  7. [Search engines without a web interface](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#search-engines-without-a-web-interface)
  8. [Graveyard](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#graveyard)
  9. [Upcoming engines](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#upcoming-engines)
  10. [Exclusions](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#exclusions)
  11. [Rationale](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#rationale)
    1. [Conflicts of interest](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#conflicts-of-interest)
    2. [Information diversity](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#information-diversity)
  12. [Method­ology](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#methodology)
    1. [Discovery](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#discovery)
    2. [Criteria for inclusion](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#criteria-for-inclusion)
    3. [Evaluation](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#evaluation)
    4. [Unique results without unique indexes](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#unique-results-without-unique-indexes)
    5. [Caveats](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#caveats)
  13. [Findings](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#findings)
  14. [Acknow­ledgements](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#acknowledgements)


## About the list
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#about-the-list)
I discuss my motivation for making this page in the [Rationale section](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#rationale).
I primarily evaluated English-speaking search engines because that’s my primary language. With some difficulty, I could probably evaluate a Spanish one; however, I wasn’t able to find many Spanish-language engines powered by their own crawlers.
I mention details like “allows site submissions” and structured data support where I can only to inform authors about their options, not as points in engines’ favor.
See the [Methodology section](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#methodology) at the bottom to learn how I evaluated each one.
## General indexing search-engines
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#general-indexing-search-engines)
### Large indexes, good results
These are large engines that pass all my standard tests and more. 

Google
    The biggest index. Allows submitting pages and sitemaps for crawling, and [even supports WebSub](https://developers.google.com/search/docs/advanced/sitemaps/build-sitemap#addsitemap) to automate the process. Powers a few other engines: 
  * A former version of [Startpage](https://www.startpage.com/), possibly the most popular Google proxy. Startpage now uses Bing[note 2](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:2)
  * [GMX Search](https://search.gmx.com/web), run by a popular German email provider.
  * (discontinued) Runnaroo
  * [Mullvad Leta](https://leta.mullvad.net/faq)
  * [SAPO](https://www.sapo.pt/) (Portuguese interface, can work with English results)
  * [DSearch](https://www.dsearch.com/)
  * [13TABS](https://www.13tabs.com/)
  * [Zarebin](https://zarebin.ir/) (Persian, can return English results)
  * Ecosia (choose between Google and Bing providers in settings)
  * A host of other engines using [Programmable Search Engine’s](https://developers.google.com/custom-search/) client-side scripts.



Bing
    The runner-up. Allows submitting pages and sitemaps for crawling without login using [the IndexNow API](https://www.indexnow.org/), sharing IndexNow page submissions with Yandex and Seznam. Its index powers many other engines: 
  * Yahoo (and its sibling engine, One­Search)
  * DuckDuck­Go[note 3](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:3) (offers a Tor onion service, a JS-free version, and a TUI-browser-friendly “lite” version making it a good way to use Bing anonymously)
  * AOL
  * Qwant (partial)[note 4](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:4)
  * Ecosia (choose between Google and Bing providers in settings)
  * Ekoru
  * Privado
  * Findx
  * Disconnect Search[note 5](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:5)
  * PrivacyWall
  * Lilo
  * Search­Scene
  * Peekier (not to be confused with Peekr, a metasearch engine with its own index)
  * Oscobo
  * Million Short
  * Yippy search[note 6](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:6)
  * Lycos
  * Givero
  * Swisscows
  * Fireball
  * Netzzappen
  * You.com[note 7](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:7)
  * Vuhuv
  * Partially powers MetaGer by default; this can be turned off
  * ChatGPT Search[note 8](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:8)
  * At this point, I mostly stopped adding Bing-based search engines. There are just too many.



Yandex
    Originally a Russian search engine, it now has an English version. Some Russian results bleed into its English site. It allows submitting pages and sitemaps for crawling using the IndexNow API, sharing IndexNow page submissions with Bing and Seznam. Powers: 
  * Epic Search (went paid-only as of June 2021)
  * Occasionally powers DuckDuck­Go’s link results instead of Bing (update: DuckDuckGo has “paused” its partnership with Yandex, confirmed in [Hearing on “Holding Big Tech Accountable: Legislation to Protect Online Users”](https://energycommerce.house.gov/committee-activity/hearings/hearing-on-holding-big-tech-accountable-legislation-to-protect-online)
  * Petal, for Russian users only.



[Mojeek](https://www.mojeek.com/) 
    Seems privacy-oriented with a large index containing billions of pages. Quality isn’t at GBY’s level, but it’s not bad either. If I had to use Mojeek as my default general search engine, I’d live. Partially powers [eTools.ch](https://www.etools.ch/). At this moment, _I think that Mojeek is the best alternative to GBY_ for general search.
Google, Bing, and Yandex support structured data such as microformats1, microdata, RDFa, Open Graph markup, and JSON-LD. Yandex’s support for microformats1 is limited; for instance, it can parse `h-card` metadata for organizations but not people. Open Graph and Schema.org are the only supported vocabularies I’m aware of. Mojeek is evaluating structured data; it’s interested in Open Graph and Schema.org vocabularies.
### Smaller indexes or less relevant results
These engines pass most of the tests listed in the “methodology” section. All of them seem relatively privacy-friendly. I wouldn’t recommend using these engines to find specific answers; they’re better for learning about a topic by finding interesting pages related to a set of keywords. 

[Stract](https://trystract.com/) 
    **My favorite generalist engine on this page.** Stract supports advanced ranking customization by allowing users to import “optics” files, like a better version of Brave’s “goggles” feature. [Stract is fully open-source](https://github.com/StractOrg/stract), with code released under an AGPL-3.0 license. The index is isn’t massive but it’s big enough to be a useful supplement to more major engines. Stract started with the Common Crawl index, but now uses its own crawler. Plans to add contextual ads and a subscription option for ad-free search. Discovered in my access logs. 

[Right Dao](https://rightdao.com) 
    Very fast, good results. Passes the tests fairly well. It plans on including query-based ads if/when its user base grows.[note 9](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:9) For the past few months, its index seems to have focused more on large, established sites rather than smaller, independent ones. It seems to be a bit lacking in more recent pages. 

[Alexandria](https://www.alexandria.org/) 
    A pretty new “non-profit, ad free” engine, with [freely-licensed code](https://github.com/alexandria-org/alexandria). Surprisingly good at finding recent pages. Its index is built from the Common Crawl; it isn’t as big as Gigablast or Right Dao but its ranking is great. 

[Yep](https://yep.com/) 
    An ambitious engine from Ahrefs, an SEO/backlink-finder company, that “shares ad profit with creators and protects your privacy”. Most engines show results that include keywords from or related to the query; Yep also shows results linked by pages containing the query. In other words, not all results contain relevant keywords. This makes it excellent for less precise searches and discovery of “related sites”, especially with its index of _hundreds of billions of pages._ It’s far worse at finding very specific information or recent events for now, but it will probably improve. It was known as “FairSearch” before its official launch. 

[SeSe Engine](https://sese.yyj.moe/) 
    Although it’s a Chinese engine, its index seems to have a large-enough proportion of English content to fit here. The engine is open-source; see the [SeSe back-end Python code](https://github.com/RimoChan/sese-engine) and [the SeSe-ui Vue-based front-end](https://github.com/YunYouJun/sese-engine-ui). It has surprisingly good results for such a low-budget project. Each result is annotated with detailed ranking metadata such as keyword relevance and backlink weight. Discovered in my access logs. 

[greppr](https://greppr.org/) 
    Its tagline is “Search the Internet with no filters, no tracking, no ads.” At the time of writing, it has over 3 million pages indexed. It’s surprisingly good at finding interesting new results for broad short-tail queries, if you’re willing to scroll far enough down the page. It appears to be good at finding recent pages.
Yep supports Open Graph and some JSON-LD at the moment. A look through the source code for Alexandria and Gigablast didn’t seem to reveal the use of any structured data. The surprising quality of results from SeSe and Right Dao seems influenced by the crawlers’ high-quality starting location: Wikipedia.
### Smaller indexes, hit-and-miss
These engines fail badly at a few important tests. Otherwise, they seem to work well enough for users who’d like some more serendipity in less-specific searches. 

[Peekr (formerly SvMetaSearch, not to be confused with Peekier)](https://peekr.org/) 
    Originally a SearxNG metasearch engine that also included results from its own index, it’s since diverged. It now appears to return all results from its own growing ElasticSearch index. Open source, with an emphasis on self-hostability. 

[seekport](http://www.seekport.com/) 
    The interface is in German but it supports searching in English just fine. The default language is selected by your locale. It’s really good considering its small index; it hasn’t heard of less common terms, but it’s able to find relevant results in other tests. It’s the second-fastest-improving engines in this section. 

[Exalead](https://www.exalead.com/search/) 
    Slow, quality is hit-and-miss. Its indexer claims to crawl the DMOZ directory, which has since shut down and been replaced by the [Curlie](https://curlie.org) directory. No relevant results for “Oppenheimer” and some other history-related queries. Allows submitting individual URLs for indexing, but requires solving a Google reCAPTCHA and entering an email address. 

[ExactSeek](https://www.exactseek.com/) 
    Small index, disproportionately dominated by big sites. Failed multiple tests. Allows submitting individual URLs for crawling, but requires entering an email address and receiving a newsletter. Webmaster tools seem to heavily push for paid SEO options. It also powers SitesOnDisplay and [Blog-search.com](https://www.blog-search.com). 

[Burf.co](https://burf.co/) 
    Very small index, but seems fine at ranking more relevant results higher. Allows site submission without any extra steps. 

[ChatNoir](https://www.chatnoir.eu/) 
    An experimental engine by researchers that uses the [Common Crawl](https://commoncrawl.org/) index. The engine is [open source](https://github.com/chatnoir-eu). See the [announcement](https://groups.google.com/g/common-crawl/c/3o2dOHpeRxo/m/H2Osqz9dAAAJ) on the Common Crawl mailing list (Google Groups). 

[Secret Search Engine Labs](http://www.secretsearchenginelabs.com/) 
    Very small index with very little SEO spam; it toes the line between a “search engine” and a “surf engine”. It’s best for reading about broad topics that would otherwise be dominated by SEO spam, thanks to its [CashRank algorithm](http://www.secretsearchenginelabs.com/tech/cashrank.php). Allows site submission. 

[Gabanza](https://www.gabanza.com/) 
    A search engine from a hosting company. I found few details abou the search engine itself, and the index was small, but it was suitable for discovering new pages related to short broad queries. 

[Jambo](https://jambot.com/) 
    Docs, blog posts, etc. have not been updated since around 2006 but the engine continues to crawl and index new pages. Discovered in my access logs. Has a bias towards older content. 

[search.dxhub.de](http://search.dxhub.de/?c=main) 
    While Gigablast seems dead, a version of it was open-source. This is based on that version of Gigablast. Its index is small but results are still useful for surfing new unseen corners of short-tail queries. Found via my access logs. 

[Fynd](https://fynd.bot/) 
    Does not appear to support full-page search, but does search page titles and description meta-tags. Supports URL submission. Found in my access logs. Currently in a prototype/experimental stage.
### Fledgling engines
Results from these search engines don’t seem particularly relevant; indexes in this category tend to be small. 

[Yessle](https://www.yessle.com/) 
    Seems new; allows page submission by pasting a page into the search box. Index is really small but it crawls new sites quickly. Claims to be private. 

[Bloopish](https://search.aibull.io/) 
    Extremely quick to update its index; site submissions show up in seconds. Unfortunately, its index only contains a few thousand documents (under 100 thousand at the time of writing). It’s growing fast: if you search for a term, it’ll start crawling related pages and grow its index. 

YaCy
    Community-made index; slow. Results are awful/irrelevant, but can be useful for intranet or custom search. 

Scopia
    Only seems to be available via the [MetaGer](https://metager.org) metasearch engine after turning off Bing and news results. Tiny index, very low-quality. As of 2024-09-10, [MetaGer is paid-only after losing its advertising contract with Yahoo](https://suma-ev.de/en/eine-aera-geht-zu-ende/). 

[Artado Search](https://www.artadosearch.com/) 
    Primarily Turkish, but it also seems to support English results. Like Plumb, it uses client-side JS to fetch results from existing engines (Google, Bing, Yahoo, Petal, and others); like MetaGer, it has an option to use its own independent index. Results from its index are almost always empty. Very simple queries (“twitter”, “wikipedia”, “reddit”) give some answers. Supports site submission and crowdsourced instant answers. 

[Active Search Results](https://www.activesearchresults.com) 
    Very poor quality. Results seem highly biased towards commercial sites. 

[Crawlson](https://www.crawlson.com) 
    Young, slow. In this category because its index has a cap of 10 URLs per domain. I initially discovered Crawlson in the seirdy.one access logs. This is often down; if the current downtime persists, I’ll add it to the graveyard. 

[Anoox](https://www.anoox.com/) 
    Results are few and irrelevant; fails to find any results for basic terms. Allows site submission. It’s also a lightweight social network and claims to be powered by its users, letting members vote on listings to alter rankings. 

[Yioop!](https://www.yioop.com) 
    A FLOSS search engine that boasts a very impressive [feature-set](https://www.seekquarry.com/): it can parse sitemaps, feeds, and a variety of markup formats; it can import pre-curated data in forms such as access logs, Usenet posts, and WARC archives; it also supports feed-based news search. Despite the impressive feature set, Yioop’s results are few and irrelevant due to its small index. It allows submitting sites for crawling. Like Meorca, Yioop has social features such as blogs, wikis, and a chat bot API. 

[Spyda](https://spyda.dev/) 
    A small engine made by [James Mills](https://www.prologic.blog/), described in [So I’m a Knucklehead eh?](https://www.prologic.blog/2021/02/14/so-im-a.html). It’s written in Go; check out its [MIT-licensed Spyda source code](https://git.mills.io/prologic/spyda). 

[Slzii.com](https://www.slzii.com/) 
    A new web portal with a search engine. Has a tiny index dominated by SEO spam. Discovered in the seirdy.one access logs. 

[Weblog DataBase](https://www.weblogdb.com/) 
    A metadata search engine for technical blogs. Very small index and ranking seems poor, but it seems to have [different goals from most search engines](https://www.weblogdb.com/about/): it encourages filtering search results iteratively until finding the desired subset of results. The index updates weekly and not all features are implemented yet.
### Semi-independent indexes
Engines in this category fall back to GBY when their own indexes don’t have enough results. As their own indexes grow, some claim that this should happen less often. 

[Brave Search](https://search.brave.com/) 
    Many tests (including all the tests I listed in the “Methodology” section) resulted results identical to Google, revealed by a side-by-side comparison with Google, Startpage, and a Searx instance with only Google enabled. Brave claims that this is due to how Cliqz (the discontinued engine acquired by Brave) used query logs to build its page models and was optimized to match Google.[note 10](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:10) The index is independent, but optimizing against Google resulted in too much similarity for the real benefit of an independent index to show. Furthermore, many queries have Bing results mixed in; users can click an “info” button to see the percentage of results that came from its own index. The independent percentage is typically quite high (often close to 100% independent) but can drop for advanced queries. Update 2023-08-15: Brave’s Bing contract appears to have expired as of April 2023.
I can’t in good conscience recommend using Brave Search, as the company runs cryptocurrency, has [held payments to creators without disclosing that creators couldn’t receive rewards](https://brave.com/rewards-update/), has made dangerously misleading claims about fingerprinting resistance,[note 11](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:11) is run by a CEO who [spent thousands of dollars opposing gay marriage](https://arstechnica.com/information-technology/2014/03/new-mozilla-ceo-issues-statement-expresses-sorrow-for-causing-pain/), and [has rewritten typed URLs with affiliate links](https://www.pcmag.com/news/brave-browser-caught-redirecting-users-through-affiliate-links).
Brave Search offers a Tor onion service and doesn’t require JS. Powers:
  * Ghostery Private Search (identical results in my tests).[note 12](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:12)
  * Partially powers Kagi ([documented in 2023](https://web.archive.org/web/20231105004927/https://help.kagi.com/kagi/search-details/search-sources.html), [unclear after docs removed main sources after 2024-05-01](https://github.com/kagisearch/kagi-docs/commit/6baff1c066db9b3d804653ea19bc9d1c076a710b)).
  * Powers [GOOD Search](https://good-search.org/en/) ([archived homepage](https://web.archive.org/web/20250313144823/https://good-search.org/en/)).



[Plumb](https://plumb.one/) 
    Almost all queries return no results; when this happens, it falls back to Google. It’s fairly transparent about the fallback process, but I’m concerned about _how_ it does this: it loads Google’s Custom Search scripts from `cse.google.com` onto the page to do a client-side Google search. This can be mitigated by using a browser addon to block `cse.google.com` from loading any scripts. Plumb claims that this is a temporary measure while its index grows, and they’re planning on getting rid of this. Allows submitting URLs, but requires solving an hCaptcha. This engine is very new; hopefully as it improves, it could graduate from this section. Its Chief Product Officer [previously founded](https://archive.is/oVAre) the Gibiru search engine which shares the same affiliates and (for now) the same index; the indexes will diverge with time. 

[Qwant](https://www.qwant.com) 
    Qwant claims to use its own index, but it still relies on Bing for most results. It seems to be in a position similar to Neeva. Try a side-by-side comparison to see if or how it compares with Bing. 

[Kagi Search](https://kagi.com/) 
    The most interesting entry in this category, IMO. Like Neeva, it requires an account and limits use without payment. It’s powered by its own Teclis index (Teclis can be used independently; see the [non-commercial section](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#small-or-non-commercial-web) below), and claims to also use results from Google and Bing. The result seems somewhat unique: I’m able to recognize some results from the Teclis index mixed in with the mainstream ones. In addition to Teclis, Kagi’s other products include the [Kagi.ai](https://kagi.ai/) intelligent answer service and the [TinyGem](https://tinygem.org/) social bookmarking service, both of which play a role in Kagi.com in the present or future. Unrelatedly: I’m concerned about the company’s biases, as it seems happy to [use Brave’s commercial API](https://kagifeedback.org/d/2808-reconsider-your-partnership-with-brave) (allowing blatant homophobia in the comments) and [allow its results to recommend suicide methods without intervention](https://kagifeedback.org/d/865-suicide-results-should-probably-have-a-dont-do-that-widget-like-google/50). I reject the idea that avoiding an option that may seem politically biased is the same as being unbiased if such a decision has real political implications. 

[PriEco](https://prieco.net/) 
    A metasearch engine with one option for using its own index. Found in my access logs. All other sources can be turned off, allowing you to see its unique results. At the time of writing, its own index is unfortunately quite tiny.
## Non-generalist search
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#non-generalist-search)
These indexing search engines don’t have a Google-like “ask me anything” endgame; they’re trying to do something different. You aren’t supposed to use these engines the same way you use GBY.
### Small or non-commercial Web 

[Marginalia Search](https://search.marginalia.nu/) 
    _My favorite entry on this page_. It has its own crawler but is strongly biased towards non-commercial, personal, and/or minimal sites. It’s a great response to the increasingly SEO-spam-filled SERPs of GBY. Partially powers Teclis, which in turn partially powers Kagi. Update 2022-05-28: [Marginalia.nu is now open source.](https://memex.marginalia.nu/log/58-marginalia-open-source.gmi) 

[Ichido](https://ichi.do/) 
    An engine that just rolled out its own independent index, with a lot of careful thought put into its ranking algorithm. Like Marginalia, it’s biased towards the non-commercial Web: it downranks ads, CAPTCHAs, trackers, SEO, and obfuscation. [More info about Ichido is in a blog post](https://blog.ichi.do/post/2023/08/20/a-new-ichido/). 

[Teclis](http://teclis.com/) 
    A project by the creator of Kagi search. Uses its own crawler that measures content blocked by uBlock Origin, and extracts content with the open-source article scrapers Trafilatura and Readability.js. This is quite an interesting approach: tracking blocked elements discourages tracking and advertising; using Trafilatura and Readability.js encourages the use of semantic HTML and Semantic Web standards such as [microformats](https://microformats.org/), [microdata](https://html.spec.whatwg.org/multipage/microdata.html), and [RDFa](https://www.w3.org/TR/rdfa-primer/). It claims to also use some results from Marginalia. [The Web interface has been shut down](https://kagifeedback.org/d/1838-teclis-is-broken/2), but its standalone API is still available for Kagi customers. 

[Clew](https://clew.se/) 
    a FOSS new engine with a small index of several thousand pages. It focuses on independent content and downranks ads and trackers; there seems to be a real focus on quality over quantity, which makes it excellent for short-tail searches (especially around technical concepts). Ranking is more egalitarian than other engines, making it better for discovery and surfing than research. It’s designed to be small and lightweight, with a compact index. Discovered in the seirdy.one access logs. 

[Lixia Labs Search](https://search.lixialabs.com/) 
    A new engine that focuses on indexing technical websites and blogs, with a minimal JavaScript-free front-end. Discovered in my access logs. Surprisingly good results for broad technical keyword queries.
### Site finders
These engines try to find a website, typically at the domain-name level. They don’t focus on capturing particular pages within websites. 

[Kozmonavt](https://kozmonavt.ml/) 
    The best in this category. Has a small but growing index of over 8 million sites. If I want to find the website for a certain project, Kozmonavt works well (provided its index has crawled said website). It works poorly for learning things and finding general information. I cannot recommend it for anything serious since it lacks contact information, a privacy policy, or any other information about the org/people who made it. Discovered in the seirdy.one access logs. 

[search.tl](http://www.search.tl/) 
    Generalist search for one TLD at a time (defaults to .com). I’m not sure why you’d want to always limit your searches to a single TLD, but now you can.[note 13](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:13) There isn’t any visible UI for changing the TLD for available results; you need to add/change the `tld` URL parameter. For example, to search .org sites, append `&tld=org` to the URL. It seems to be connected to [Amidalla](http://www.amidalla.de/). Amidalla allows users to manually add URLs to its index and directory; I have yet to see if doing so impacts search.tl results. 

[Thunderstone](https://search.thunderstone.com/) 
    A combined website catalog and search engine that focuses on categorization. Its [about page](https://search.thunderstone.com/texis/websearch19/about.html) claims: "We continuously survey all primary COM, NET, and ORG web-servers and distill their contents to produce this database. This is an index of _sites_ not pages. It is very good at finding companies and organizations by purpose, product, subject matter, or location. If you’re trying to finding things like _‘BillyBob’s personal beer can page on AOL’_ , try Yahoo or Dogpile." This seems to be the polar opposite of the engines in the [“small or non-commercial Web” category](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#small-or-non-commercial-web). 

[sengine.info](https://www.sengine.info/) 
    Only shows domains, not individual pages. Developed by netEstate GmbH, which specializes in content extraction for inprints and job ads. Also has a German-only version available. Discovered in my access logs. 

[Gnomit](https://www.gnomit.com/) 
    Allows single-keyword queries and returns sites that seem to cover a related topic. I actually kind of enjoy using it; results are old (typically from 2009) and a bit random, but make for a nice way to discover something new. For instance, searching for “IRC” helped me discover new IRC networks I’d never heard of.
### Other 

[High Browse](https://highbrow.se/) 
    Uses a non-traditional ranking algorithm which does an excellent job of introducing non-SEO-optimized serendipity into search results. One of my favorite “surf-engines”, as opposed to traditional “search-engines”. 

[Keybot](https://www.keybot.com/) 
    A must-have for anyone who does translation work. It crawls the web looking for multilingual websites. Translators who are unsure about how to translate a given word or phrase can see its usage in two given languages, to learn from other human translators. My parents are fluent English speakers but sometimes struggle to express a given Hindi idiom in English; something like this could be useful to them, since machine translation isn’t nuanced enough for every situation. Part of the [TTN Translation Network](https://www.ttn.ch/). Discovered in my access logs. 

Quor
    Seems to mainly index large news sites. Site is down as of June 2021; originally available at www dot quor dot com. 

[Semantic Scholar](https://www.semanticscholar.org/) 
    A search engine by the Allen Institute for AI focused on academic PDFs, with a couple hundred million papers indexed. Discovered in my access logs. 

[Bonzamate](https://bonzamate.com.au/) 
    A search engine specifically for Australian websites. Boyter wrote [an interesting blog post about Bonzamate](https://boyter.org/posts/abusing-aws-to-make-a-search-engine/). 

[searchcode](https://searchcode.com/) 
    A code-search engine by the developer of Bonzamate. Searches a hand-picked list of code forges for source code, supporting many search operators. 

[StarFinder](https://star-finder.de/?l=en) 
    A search engine that focuses on Open Graph Protocol metadata, searching for domains that have OGP information and rendering link previews for them. A good surf-engine once you grok how to build sufficiently broad queries. Has a large and growing index of 4.8 million sites at the time of writing. Allows site submission.
## Other languages
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#other-languages)
I’m unable to evaluate these engines properly since I don’t speak the necessary languages. English searches on these are a hit-or-miss. I might have made a few mistakes in this category.
### Big indexes
  * Baidu: Chinese. Very large index; it’s a major engine alongside GBY. Offers webmaster tools for site submission.
  * Qihoo 360: Chinese. I’m not sure how independent this one is.
  * Toutiao: Chinese. Not sure how independent this one is either. Its index appears limited outside of its own content distribution platform.
  * Sogou: Chinese
  * Yisou: Chinese, by Yahoo. Appears defunct.
  * [Naver](https://search.naver.com): Korean. Allows submitting sitemaps and feeds. Discovered via some Searx metasearch instances.
  * [Daum](https://www.daum.net/): Korean. Also unsure about this one’s independence.
  * [Seznam](https://www.seznam.cz/): Czech, seems relatively privacy-friendly. Discovered in the seirdy.one access logs. It allows site submission with webmaster tools. [Seznam supports IndexNow](https://blog.seznam.cz/2022/03/mate-novy-obsah-dejte-o-nem-hned-vsem-vedet-pomoci-indexnow/); it shares IndexNow-submitted pages with Bing and Yandex.
  * [Cốc Cốc](https://coccoc.com/search): Vietnamese
  * [go.mail.ru](https://go.mail.ru/): Russian
  * [LetSearch.ru](https://letsearch.ru/): Russian. [Allows URL submission](https://letsearch.ru/bots)


### Smaller indexes
  * [ALibw.com](https://www.alibw.com/): Chinese, found in my access logs.
  * [Vuhuv](https://www.vuhuv.com.tr/): Turkish. [alt domain](https://tr.vuhuv.com/)
  * [search.ch](https://www.search.ch): Regional search engine for Switzerland; users can restrict searches to their local regions.
  * [fastbot](https://www.fastbot.de/): German
  * [SOLOFIELD](https://solofield.net): Japanese
  * [kaz.kz](http://kaz.kz): Kazakh and Russian, with a focus on “Kazakhstan’s segment of the Internet”


## Almost qualified
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#almost-qualified)
These engines come close enough to passing my inclusion criteria that I felt I had to mention them. They all display original organic results that you can’t find on other engines, and maintain their own indexes. Unfortunately, they don’t quite pass because they don’t crawl the Web; most limit themselves to a specific set of sites. 

[wiby.me](https://wiby.me) 


[wiby.org](https://wiby.org) 
    I love this one. It focuses on smaller independent sites that capture the spirit of the “early” web. It’s more focused on “discovering” new interesting pages that match a set of keywords than finding a specific resources. I like to think of Wiby as an engine for surfing, not searching. Runnaroo occasionally featured a hit from Wiby (Runnaroo has since shut down). If you have a small site or blog that isn’t very “commercial”, consider submitting it to the index. Does not qualify because it seems to be powered only by user-submitted sites; it doesn’t try to “crawl the Web”. 

[Mwmbl](https://mwmbl.org/) 
    Like YaCy, it’s an open-source engine whose crawling is community-driven. Users can install a Firefox addon to crawl pages in its backlog. Unfortunately, it doesn’t qualify because it only crawls pages linked by hand-picked sites (e.g. Wikipedia, GitHub, domains that rank well on Hacker News). The crawl-depth is “1”, so it doesn’t crawl the whole Web (yet). 

[Search My Site](https://searchmysite.net) 
    Similar to Marginalia and Teclis, but only indexes user-submitted personal and independent sites. It optionally supports IndieAuth. Its API powers this site’s search results; try it out using the search bar at the bottom of this page. Does not qualify because it’s limited to user-submitted and/or hand-picked sites. 

[Kukei.eu](https://kukei.eu/) 
    A curated search engine for web developers, which crawls [a hand-picked list of sites](https://github.com/Kukei-eu/spider/blob/914b8dfffc10cb3a948561aef2bf86937d3a0b2e/index-sources.js). As it does not index the whole Web, it doesn’t qualify. I still find it interesting. 

[Unobtanium Search](https://unobtanium.rocks/) 
    A fledgling search engine by [Slatian](https://slatecave.net/). At the time of writing, it crawls hand-curated sites: personal, technical, indie wiki, and German hacker community sites. It may eventually crawl government/public-service sites. More documentation will be on its website.
## Misc
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#misc) 

Ask.com
    The site is back. They claim to outsource search results. The results seem similar to Google, Bing, and Yandex; however, I can’t pinpoint exactly where their results are coming from. Also, several sites from the “ask.com network” such as directhit.com, info.com, and kensaq.com have uniqe-looking results. 

[Infinity Search](https://infinitysearch.co) 
    Partially evaluated. Young, small index. It recently split into a paid offering with the main index and [Infinity Decentralized](https://infinitydecentralized.com/), the latter of which allows users to select from community-hosted crawlers. I managed to try it out before it became a paid offering, and it seemed decent; however, I wasn’t able to run the tests listed in the “Methodology” section. Allows submitting URLs and sitemaps into a text box, no other work required.
## Search engines without a web interface
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#search-engines-without-a-web-interface)
Some search engines are integrated into other appliances, but don’t have a web portal.
  * Apple’s search engine is usable in the form of “Siri Suggested Websites”. Its index is built from the Applebot web crawler. If Apple already has working search engine, it’s not much of a stretch to say that they’ll make a web interface for it someday.
  * Amazon bought Alexa Internet (a web traffic analysis company, at the time unrelated to the Amazon Alexa virtual assistant) and discontinued its website ranking product. Amazon still runs the relevant crawlers, and also have [a bot called “Amazonbot”](https://developer.amazon.com/support/amazonbot). While Applebot powers the Siri personal assistant, Amazonbot powers the Alexa personal assistant "to answer even more questions for customers". Crawling the web to answer questions is the basis of a search engine.


## Graveyard
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#graveyard)
These engines were originally included in the article, but have since been discontinued. 

[Petal Search](https://web.archive.org/web/20230118225122/https://www.petalsearch.com/) 
    A search engine by Huawei that recently switched from searching for Android apps to general search in order to reduce dependence on Western search providers. Despite its surprisingly good results, I wouldn’t recommend it due to privacy concerns: its privacy policy describes advanced fingerprinting metrics, and it doesn’t work without JavaScript. Requires an account to submit sites. I discovered this via my access logs. Be aware that in some jurisdictions, it doesn’t use its own index: in Russia and some EU regions it uses Yandex and Qwant, respectively. Inaccessible as of June 2023. 

[Neeva](https://web.archive.org/web/20230528051432/https://neeva.com/blog/may-announcement) 
    Formerly in [the “semi-independent” section](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#semi-independent-indexes). Combined Bing results with results from its own index. Bing normally isn’t okay with this, but Neeva was one of few exceptions. Results were mostly identical to Bing, but original links not found by Bing frequently popped up. Long-tail and esoteric queries were less likely to feature original results. Required signing up with an email address or OAuth to use, and offered a paid tier with additional benefits. Acquired by Snowflake and announced its shut-down in May 2023. 

[Gigablast](https://gigablast.com/) 
    It’s been around for a while and also sports a classic web directory. Searches are a bit slow, and it charges to submit sites for crawling. It powers [Private.sh](https://private.sh). Gigablast was tied with Right Dao for quality. Shut down mid-2023. 

[wbsrch](https://xangis.com/the-wbsrch-experiment/) 
    In addition to its generalist search, it also had many other utilities related to domain name statistics. Failed multiple tests. Its index was a bit dated; it had an old backlog of sites it hadn’t finished indexing. It also had several dedicated per-language indexes. 

[Gowiki](https://web.archive.org/web/20211226043304/https://www.gowiki.com/) 
    Very young, small index, but showed promise. I discovered this in the seirdy.one access logs. It was only available in the US. Seems down as of early 2022. 

[Meorca](https://web.archive.org/web/20220429143153/https://www.meorca.com/search/) 
    A UK-based search engine that claims not to “index pornography or illegal content websites”. It also features an optional social network (“blog”). Discovered in the seirdy.one access logs. 

[Ninfex](https://web.archive.org/web/20220624172257/https://ninfex.com/) 
    A “people-powered” search engine that combines aspects of link aggregators and search. It lets users vote on submissions and it also displays links to forums about submissions. 

[Marlo](https://github.com/isovector/marlo) 
    Another FLOSS engine: Marlo is written in Haskell. Has a small index that’s good enough for surfing broad topics, but not good enough for specific research. Originally available at `marlo.sandymaguire.me`. 

websearchengine.org


tuxdex.com
    Both were run by the same people, powered by their inetdex.com index. Searches are fast, but crawls are a bit shallow. Claims to have an index of 10 million domains, and not to use cookies. The pages are currently down and the domains re-direct to porn sites; I’m not aware of any official notice. 

[Entfer](https://web.archive.org/web/20230810032916/https://entfer.com/) 
    a newcomer that let registered users upvote/downvote search results to customize ranking. Didn’t offer much information about who made it. Its index was small, but it did seem to return results related to the query. 

[Siik](https://web.archive.org/web/20221002041725/https://siik.co/) 
    Lacked contact info, and the ToS and Privacy Policy links were dead. Seemed to have PHP errors in the backend for some of its instant-answer widgets. If you scrolled past all that, you’d find web results powered by what seems to be its own index. These results did tend to be somewhat relevant, but the index seemed too small for more specific queries. 

[Blog Surf](https://blogsurf.io/) 
    A search engine for blogs with RSS/Atom feeds. Originally in “almost qualified”. It did not qualify because all blogs submitted to the index require manual review, but it seemed interesting. Its “MarketRank” algorithm gave it a bias towards sites popular on “Hacker” “News”. 

[Infotiger](https://web.archive.org/web/20250627183504/https://infotiger.com/) 
    Was one of my favorites. It offered advanced result filtering and sports a somewhat large index. It allowed site submission for English and German pages. [Infotiger also had a Tor hidden service](http://infotiger4xywbfq45mvd5drh43jpqeurakg2ya7gqwvjf2bbwnixzqd.onion/).
Dead engines I don’t have an extended description for:
  * [Parsijoo](https://www.parsijoo.ir/): Persian search engine.
  * [Moose.at](https://www.moose.at): German (Austria-based). The site is still up but redirects searches to Brave.


## Upcoming engines
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#upcoming-engines)
  * [Cyberfind/find.tf](https://cyberfind.net/bot.html)
  * [Wepch](https://www.wepch.com/search-engine)
  * [Weblog DataBase](https://www.weblogdb.com/)


## Exclusions
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#exclusions)
Three engines were excluded from this list for having a far-right focus.
One engine was excluded because it seems to be built using cryptocurrency in a way I’d rather not support.
Some fascinating little engines seem like hobbyist proofs-of-concept. I decided not to include them in this list, but watch them with interest to see if they can become something viable.
## Rationale
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#rationale)
Why bother using non-mainstream search engines?
### Conflicts of interest
Google, Microsoft (the company behind Bing), and Yandex aren’t just search engine companies; they’re content and ad companies as well. For example, Google hosts video content on YouTube and Microsoft hosts social media content on LinkedIn. This gives these companies a powerful incentive to prioritize their own content. They are able to do so even if they claim that they treat their own content the same as any other: since they have complete access to their search engines’ inner workings, they can tailor their content pages to better fit their algorithms and tailor their algorithms to work well on their own content. They can also index their own content without limitations but throttle indexing for other crawlers.[note 14](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:14)
One way to avoid this conflict of interest is to _use search engines that aren’t linked to major content providers;_ i.e., use engines with their own independent indexes.
### Information diversity
There’s also a practical, less-ideological reason to try other engines: different providers have different results. Websites that are hard to find on one search engine might be easy to find on another, so using more indexes and ranking algorithms results in access to more content.
No search engine is truly unbiased. Most engines’ ranking algorithms incorporate a method similar to [PageRank](https://en.wikipedia.org/wiki/PageRank), which biases them towards sites with many backlinks. Search engines have to deal with unwanted results occupying the confusing overlap between SEO spam, shock content, and duplicate content. When this content’s manipulation of ranking algos causes it to rank high, engines have to address it through manual action or algorithm refinement. Choosing to address it through either option, or choosing to leave it there for popular queries after receiving user reports, reflects bias. The best solution is to mix different ranking algorithms and indexes instead of using one engine for everything.
## Method­ology
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#methodology)
### Discovery
I find new engines by:
  * Monitoring certain web directories for changes in their search engine listings.
  * Checking other curated lists of “good/bad bots” to spot search engines.
  * Using search engines to discover search engines: searching for the names of less-popular engines often pulls up similar lists.
  * Receiving suggestions from readers
  * Compiling a list of regular expressions for user-agent strings I’m familiar with. Before I delete my server access logs, I extract user-agents that don’t match that list along with the pages they request.
  * Checking the Searx and Searxng projects for new integrations.


### Criteria for inclusion
Engines in this list should have their own indexes powered by web crawlers. Original results should not be limited to a set of websites hand-picked by the engine creators; indexes should be built from sites from across the Web. An engine should discover new interesting places around the Web.
Here’s an oversimplified example to illustrate what I’m looking for: imagine somone self-hosts their own personal or interest-specific website and happens to get some recognition. Could they get _automatically_ discovered by your crawler, indexed, and included in the first page of results for a certain query?
I’m willing to make two exceptions:
  1. Engines in the “semi-independent” section may mix results that do meet the aforementioned criteria with results that do not.
  2. Engines in the “almost qualified” section may use indexes primarily made of user-submitted or hand-picked sites, rather than focusing primarily on sites discovered organically through crawling.


The reason the second exception exists is that while user submissions don’t represent automatic crawling, they do at least inform the engine of new interesting websites that it had not previously discovered; these websites can then be shown to other users. That’s fundamentally what an alternative web index needs to achieve.
I’m not usually willing to budge on my “no hand-picked websites” rule. Hand-picked sites will be ignored, whether your engine fetches content through their APIs or crawls and scrapes their content. It’s fine to use hand-picked websites as starting points for your crawler (Wikipedia is a popular option).
I only consider search engines that focus on link results for webpages. Image search engines are out of scope, though I _might_ consider some other engines for non-generalist search (e.g., Semantic Scholar finds PDFs rather than webpages).
### Evaluation
I focused almost entirely on “organic results” (the classic link results), and didn’t focus too much on (often glaring) privacy issues, “enhanced” or “instant” results (e.g. Wikipedia sidebars, related searches, Stack Exchange answers), or other elements.
I compared results for esoteric queries side-by-side; if the first 20 results were (nearly) identical to another engine’s results (though perhaps in a slightly different order), they were likely sourced externally and not from an independent index.
I tried to pick queries that should have a good number of results and show variance between search engines. An incomplete selection of queries I tested:
  * “vim”, “emacs”, “neovim”, and “nvimrc”: Search engines with relevant results for “nvimrc” typically have a big index. Finding relevant results for the text editors “vim” and “emacs” instead of other topics that share the name is a challenging task.
  * “vim cleaner”: should return results related to a [line of cleaning products](https://en.wikipedia.org/wiki/Vim_%28cleaning_product%29) rather than the Correct Text Editor.
  * “Seirdy”: My site is relatively low-traffic, but my nickname is pretty unique and visible on several of the highest-traffic sites out there.
  * “Project London”: a small movie made with volunteers and FLOSS without much advertising. If links related to small independent projects like this show up, the index has really good coverage of movies.
  * “oppenheimer” versus “J Robert Oppenheimer”: a name that could refer to many things. Without context, it could refer to a high-budget movie or the physicist who led the Manhattan Project in Los Alamos. Other historical queries: “magna carta” (intermediate), “the prince” (very hard).


(Update: I don’t use these queries anymore; I’ve found better tests in recent months).
Some less-mainstream engines have noticed this article, which is great! I’ve had excellent discussions with people who work on several of these engines. Unfortunately, this article’s visibility also incentivizes some engines to optimize specifically for any methodology I describe. I’ve addressed this by keeping a long list of test queries to myself. The simple queries above are a decent starting point for simple quick evaluations, but I also test for common search operators, keyword length, and types of domain-specific jargon. I also use queries designed to pull up specific pages with varying levels of popularity and recency to gauge the size, scope, and growth of an index.
Professional critics often work anonymously because personalization can damage the integrity of their reviews. For similar reasons, I attempt to try each engine anonymously at least once by using a VPN and/or my standard anonymous setup: an amnesiac Whonix VM with the Tor Browser. I also often test using a fresh profile when travelling, or via a Searx instance if it supports a given engine. When avoiding personalization, I use “varied” queries that I don’t repeat verbatim across search engines; this reduces the likelihood of identifying me. I also attempt to spread these tests out over time so admins won’t notice an unusual uptick in unpredictable and esoteric searches. This might seem overkill, but I already regularly employ similar methods for a variety of different scenarios.
### Unique results without unique indexes
Some engines, like Kagi and the Ask.com family of engines, have unique-looking results from external indexes. Unique results alone don’t always imply independence, as an engine could alter ranking or add filters (something that very few engines are permitted to do; Google and Microsoft generally impose a strict ToS forbidding modification).
Another possible indicator I look for is word substitutions. Nearly every engine supports substitutions for verb tense or singular/plural word forms, but more advanced semantic substitutions are less common. Returning the same results for “matza gebrent” and “matzo brei” requires a deep understanding of related food topics. Google and Bing return nearly identical results for the two queries, but engines like Mojeek return entirely different results. I often compare an engine’s word substitutions to see if they’re similar to another engine’s, and see how many results from the top 20 are not present in the top 30-40 on other engines. I have a working list of other word substitutions I test.
### Caveats
I didn’t try to avoid personalization when testing engines that require account creation. Entries in the “hit-and-miss” and “unusable” sections got less attention: I didn’t spend a lot of effort tracking results over time to see how new entries got added to them.
I avoided “natural language” queries like questions, focusing instead on keyword searches and search operators. I also mostly ignored infoboxes (also known as “instant answers”).
## Findings
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#findings)
What I learned by building this list has profoundly changed how I surf.
Using one engine for everything ignores the fact that different engines have different strengths. For example: while Google is focused on being an “answer engine”, other engines are better than Google at discovering new websites related to a broad topic. Fortunately, browsers like Chromium and Firefox make it easy to add many search engine shortcuts for easy switching.
When talking to search engine founders, I found that the biggest obstacle to growing an index is getting blocked by sites. Cloudflare was one of the worst offenders, although [it has since launched a “verified bots” program to improve things](https://blog.cloudflare.com/friendly-bots). Too many sites block perfectly well-behaved crawlers, only allowing major players like Googlebot, BingBot, and TwitterBot; this cements the current duopoly over English search and is harmful to the health of the Web as a whole.
Too many people optimize sites specifically for Google without considering the long-term consequences of their actions. One of many examples is how Google’s JavaScript support rendered the practice of testing a website without JavaScript or images “obsolete”: almost no non-GBY engines on this list are JavaScript-aware.
When building webpages, authors need to consider the barriers to entry for a new search engine. The best engines we can build today shouldn’t replace Google. They should try to be different. We want to see the Web that Google won’t show us, and search engine diversity is an important step in that direction.
Try a “bad” engine from lower in the list. It might show you utter crap. But every garbage heap has an undiscovered treasure. I’m sure that some hidden gems you’ll find will be worth your while. Let’s add some serendipity to the SEO-filled Web.
## Acknow­ledgements
[ Permalink to section ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#acknowledgements)
Some of this content came from the [Search Engine Map](https://www.searchenginemap.com/) and [Search Engine Party](https://searchengine.party/). A few web directories also proved useful.
[Matt Wells](https://web.archive.org/web/20230220000629/https://www.gigablast.com/bio.html) from [Gigablast](https://web.archive.org/web/20230331095814/https://www.gigablast.com/) also gave me some helpful information about GBY which I included in the “Rationale” section. He’s written more about big tech in the [Gigablast blog](https://web.archive.org/web/20230321113801/https://gigablast.com/blog.html).
[A 2021 List of Alternative Search Engines and Search Resources](https://thenewleafjournal.com/a-2021-list-of-alternative-search-engines-and-search-resources/) by [Nicholas Ferrell](https://emucafe.club/channel/naferrell) from [The New Leaf Journal](https://thenewleafjournal.com/) is a great post on alternative search engines. He also gave me some [useful details](https://lists.sr.ht/~seirdy/seirdy.one-comments/%3C20210618031450.rb2twu4ypek6vvl3%40rkumarlappie.attlocal.net%3E) about Seznam, Naver, Baidu, and Goo.
* * *
## Notes
  1. Yes, “indexes” is an acceptable plural form of the word “index”. The word “indices” sounds weird to me outside a math class. 
[ Back to reference 1 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:1)
  2. Update: [A Startpage support article](https://support.startpage.com/hc/en-us/articles/4522435533844-What-is-the-relationship-between-Startpage-and-your-search-partners-like-Google-and-Microsoft-Bing-) updated on 2023-03-08 claims that Startpage uses Microsoft (probably Bing) too. In my own tests, I still see Google results. I’ll update its placement if this changes. 
[ Back to reference 2 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:2)
  3. DuckDuckGo has a crawler called DuckDuckBot. This crawler doesn’t impact the linked results displayed; it just grabs favicons and scrapes data for a few instant answers. DuckDuckGo’s help pages claim that the engine uses over 400 sources; my interpretation is that at least 398 sources don’t impact organic results. I don’t think DuckDuckGo is transparent enough about the fact that their organic results are proxied. Compare DuckDuckGo side-by-side with Bing and Yandex and you’ll see it’s sourcing organic results from one of them (probably Bing). _Update, March 2022:_ DuckDuckGo [has the ability to downrank results on its own](https://web.archive.org/web/20220310222014/https://nitter.pussthecat.org/yegg/status/1501716484761997318); it was previously [working with Bing](https://www.nytimes.com/2022/02/23/technology/duckduckgo-conspiracy-theories.html) to get Bing to remove misinformation and spam. 
[ Back to reference 3 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:3)
  4. Qwant claims to also use its own crawler for results, but it’s still mostly Bing in my experience. See the “semi-independent” section. 
[↩︎](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:4) [Back to reference 4](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref1:4)
  5. Disconnect Search allows users to have results proxied from Bing or Yahoo, but Yahoo sources its results from Bing. 
[ Back to reference 5 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:5)
  6. Yippy claims to be powered by a certain IBM brand (a brand that could correspond to any number of products) and annotates results with the phrase “Yippy Index”, but a side-by-side comparison with Bing and other Bing-based engines revealed results to be nearly identical. 
[ Back to reference 6 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:6)
  7. I’m in the process of re-evaluating You.com. It claims to operate a crawler and index. It seems very much like DuckDuckGo[note 4](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fn:4) to me: organic results look like they’re from Bing, while infoboxes (“apps”) seem to be scraped or queried from hand-picked websites. I’m not currently seeing results from “around the web” like the other engines that do pass my inclusion criteria. I might be wrong! I’m re-evaluating it to see if this isn’t actually the case.
Update: You.com seems to source organic link results from Bing, and only interleaves those results with its own curated infoboxes
Update: during a recent Bing outage, I found some organic link results on You.com that didn’t look like they came from Bing. More research is needed again. 
[ Back to reference 7 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:7)
  8. See [the ChatGPT Search help article](https://help.openai.com/en/articles/9237897-chatgpt-search): "ChatGPT searches based on your prompts and may share disassociated search queries with third-party search providers such as Bing." 
[ Back to reference 8 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:8)
  9. This is based on a statement Right Dao made in [on Reddit](https://reddit.com/comments/k4clx1/_/ge9dwmh/?context=1) ([archived](https://web.archive.org/web/20210320042457/https://i.reddit.com/r/degoogle/comments/k4clx1/right_dao_a_new_independent_search_engine_that/ge9dwmh/?context=1)). 
[ Back to reference 9 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:9)
  10. More information can be found in [this HN subthread](https://news.ycombinator.com/item?id=27593801) and some posts on the Cliqz tech blog ([one](https://0x65.dev/blog/2019-12-06/building-a-search-engine-from-scratch.html), [two](https://0x65.dev/blog/2019-12-10/search-quality-at-cliqz.html)). 
[ Back to reference 10 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:10)
  11. I will explain my thinking in another post later, and then edit this with a link to that post. 
[ Back to reference 11 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:11)
  12. [Ghostery’s documentation at the time of writing](https://web.archive.org/web/20240721030135/https://www.ghostery.com/private-search) is extremely misleading, using clever language that seems to heavily imply the use of an independent index and crawler while not saying so outright: Ghostery says it "gets you objective results from a unique search index" and that it will "crawl it’s [sic] search index." Privacy claims require trust, and word games do little to build it. 
[ Back to reference 12 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:12)
  13. Some search engines support the `site:` search operator to limit searches to subpages or subdomains of a single site or TLD. `site:.one`, for instance, limits searches to websites with the “.one” TLD. 
[ Back to reference 13 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:13)
  14. Matt from Gigablast told me that indexing YouTube or LinkedIn will get you blocked if you aren’t Google or Microsoft. I imagine that you could do so by getting special permission if you’re a megacorporation. 
[ Back to reference 14 ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:14)


* * *
## Interact
You can interact by [sending webmentions](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#webmentions) or by visiting a syndicated copy of this post.
### Web­mentions
This site supports [Webmentions](https://indieweb.org/Webmention), a backlink-based alternative to traditional comment forms.
Send a Webmention Publish a response on your own website, and link back to this page's canonical location. Then share your link here to turn it into a Webmention. URL of page linking here
Toggle 199 Webmentions
Webmentions received for this post appear in the following list after I approve them. I sometimes send Webmentions to myself on behalf of linking sites that don’t support them. I auto-replace broken links with [Wayback Machine](https://web.archive.org/) snapshots, if they exist. 2021-03-11  
     [ activitypub ](https://littr.me/~Seirdy/152df9ce-b78c-4dba-a6aa-79985052685a) 2021-03-12  
     [ A look at search engines with their own indexes - ~tech - Tildes ](https://tildes.net/~tech/vnw/a_look_at_search_engines_with_their_own_indexes) 2021-03-12  
     [ A look at search engines with their own indexes | Hacker News ](https://news.ycombinator.com/item?id=26429942) 2021-03-12  
     [ Boosted: A look at search engines with their own indexes - Seirdy ](https://adhoc.systems/boosts/d2183854-1bb6-49bf-9476-c0b5bdb54e5d) 2021-03-18  
     [ List of Search Engines with their own Indexes March 2021 ](http://th3core.com/talk/traffic/list-of-search-engines-with-their-own-indexes-march-2021/) 2021-03-19  
    [ New Search Engines Added March 2021](https://indieseek.xyz/2021/03/19/new-search-engines-added-march-2021/) by Brad
"I added some new search engines to the directory here.  What makes these worth listing is they all have their own index.  This makes them unique even though the index may currently be small.GoWiki – Small, growing, privacy.Petal Search – New commercial search engine from Huawei.  I think their index is fairly large.  I don’t know if they are using another search engine (maybe Yandex?) for backfill. Assume it is not private.Plumb One – Index is small, growing.  Plumb uses Bing to …" 2021-03-29  
     [ Alternative a Google Search ](https://www.lealternative.net/2019/10/18/alternative-a-google-search/)
"Siete stanchi delle solite ricerche e state cercando delle alternative a Google Search? La quantità di tracker e la capacità di profilazione di Google potrebbe allarmare molti anche perché oltre ad un evidente problema etico e morale nell’essere costantemente seguiti e profilati c’è anche il problema della cosiddetta ‘bolla culturale’. In breve significa che conoscendovi così bene Google vi proporrà principalmente cose che, secondo lui, a voi interessano evitandovi così di ampl…" 2021-04-02  
     [ A look at search engines with their own indexes ](https://searchnews.org/2021/04/02/a-look-at-search-engines-with-their-own-indexes/)
"Rohan Kumar has a list of search engines with their own index. It’s a really useful list and it breaks it into several categories. Such as: Engines with their own crawling and indexing.A list of engines that leverage other engines’ indexes. A list of engines that have their own smaller indexes.Big and small indexes for other languages. These lists are hard to put together. It’s challenging to unwind what’s happening behind the scenes, but this document covers a lot of groun…" 2021-06-17  
     [ Alternative Search Engine Review (2021) · The New Leaf Journal ](https://thenewleafjournal.com/a-2021-list-of-alternative-search-engines-and-search-resources/) 2021-08-16  
     [ Q&A - The Best Private Search Engine - What are you using? | MalwareTips Community ](https://malwaretips.com/threads/the-best-private-search-engine-what-are-you-using.109387) 2021-10-31  
     [ Chemistry in the city ](https://chemistryinthecity.neocities.org/content/entry2110.html#282) 2022-01-30  
     [ Show HN: Searchall – search all major indexes on one page (with iframes) | Hacker News ](https://news.ycombinator.com/item?id=29600619) 2022-01-31  
     [ Firefox Experiment is testing Bing as the default search engine - gHacks Tech News ](https://www.ghacks.net/2021/09/17/firefox-experiment-is-testing-bing-as-the-default-search-engine/) 2022-01-31  
     [ i.reddit.com/r/NoStupidQuestions/co … ](https://i.reddit.com/r/NoStupidQuestions/comments/sdvmpy/is_it_just_me_or_has_googles_search_result/hufk9kl/) 2022-02-08  
     [ Search Choices Enable Freedom to Seek | Official Mojeek Blog ](https://blog.mojeek.com/2022/02/search-choices-enable-freedom-to-seek.html) 2022-02-09  
    [ Brad Enslen](https://ramblinggit.com/2021/03/16/bookmarked-here-is.html) by Brad Enslen
"Bookmarked: Here is a good rundown of search engines that have their own index, including some new ones to me. seirdy.one/2021/03/1…" 2022-02-09  
     [ Daily Authority: 📈 Starlink, Pixel sales - Android Authority ](https://www.androidauthority.com/da-february-2-2022-3100832/) 2022-02-14  
    [ For completeness, at Neeva we're also investing heavily to build out our web index and search capabilities. Beyond the public …](https://brid.gy/comment/reddit/Seirdy/m9hesi/grnu7uq) by ahvee_at_neeva
"For completeness, at Neeva we're also investing heavily to build out our web index and search capabilities. Beyond the public web we already index connected accounts like Dropbox to safely search across personal docs in one place. Keep an eye out for NeevaBot and more if you're a webmaster. ;)" 2022-02-14  
    [ It's interesting, somehow I (exclusively qualitatively) perceive that Qwant gives me better results than Bing/DDG, but after …](https://brid.gy/comment/reddit/Seirdy/m9hesi/grna51w) by PepperJackson
"It's interesting, somehow I (exclusively qualitatively) perceive that Qwant gives me better results than Bing/DDG, but after reading this I put them side by side and it looks like they are similar than I thought! I guess I feel more comfortable using a search engine that's based out of the US though." 2022-02-17  
    [ brid.gy/like/mastodon/@Seirdy@plero …](https://pleroma.envs.net/notice/AGYgEgNubK6AhW7n5U) by Mojeek 2022-02-23  
    [ @odd I would really like for Apple to develop a search engine. It might take a few years for them to make it really work but I …](https://micro.blog/bradenslen/11175648) by bradenslen
"@odd I would really like for Apple to develop a search engine. It might take a few years for them to make it really work but I think it would be good for the web. Same here, I really like DuckDuckGo and Mojeek.com and use those two almost exclusively." 2022-02-23  
    [ This is a really good look at alternative search engines. Something I have been meaning to write for a while but never got …](https://brid.gy/post/twitter/seirdy/1431092779094982658) by boyter
"This is a really good look at alternative search engines. Something I have been meaning to write for a while but never got around to doing. seirdy.one/2021/03/10/sea…" 2022-02-23  
    [ This is a good read. Im noticing changes on my search results. A look at search engines with their own indexes - Seirdy seirdy.one/2021/03/10/sea…](https://brid.gy/post/twitter/seirdy/1487481854005493763) by Rae
"This is a good read. Im noticing changes on my search results. A look at search engines with their own indexes - Seirdy seirdy.one/2021/03/10/sea…" 2022-02-26  
     [ search engine ](https://www.jayeless.net/wiki/search-engine.html)
"Search engines work by building a database of what pages exist on the web (which it does by sending out “spiders” to “crawl” pages, following all the links they find to other pages), analysing them in some way, and using an algorithm to produce what it thinks are the most relevant results for any search term you type in. For English-language sites, the two biggest search engines, which have the resources to do their own crawling, are Google and Microsoft’s Bing. These seem to be the…" 2022-02-27  
     [ I concur. And would add that on Safari and iOS, it suits Google and Microsoft to... | Hacker News ](https://news.ycombinator.com/item?id=30352345) 2022-03-03  
    [ Much more than a cursory review: seirdy.one/2021/03/10/sea…](https://brid.gy/post/twitter/seirdy/1499441860573642756) by SearchEngineMap
"Much more than a cursory review: seirdy.one/2021/03/10/sea…" 2022-03-11  
    [ @Seirdy Surely it's possible to make a search engine that's only biased towards relevant content.](https://pleroma.envs.net/notice/AHHdovaz9VPSieLIiu) by Hyolobrika
This comment may have major formatting errors that could impact screen reader comprehension.
"Surely it's possible to make a search engine that's only biased towards relevant content." 2022-03-15  
    [ Excellent read by @Seirdy A look at search engines with their own indexes: …](https://pleroma.envs.net/notice/AHRtzfm49UzpQIdRRY) by bbbhltz :debian: :thinkpad_tp:
This comment may have major formatting errors that could impact screen reader comprehension.
"Excellent read by @Seirdy A look at search engines with their own indexes: https://seirdy.one/2021/03/10/search-engines-with-own-indexes.htmlMake sure to take a moment to read through some of the references too A look at search engines with their own indexes" 2022-03-17  
     [ Advanced Online Media Use ](https://swprs.org/advanced-online-media-use/) 2022-03-18  
     [ Wikipedia talk:WikiProject Software/Free and open-source software task force - Wikipedia ](https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_Free_Software) 2022-03-19  
    [ A look at search engines with their own indexes | Lobsters](https://lobste.rs/s/szkcf0) by Seirdy 2022-03-19  
    [ A look at search engines with their own indexes: seirdy.one/2021/03/10/sea…](https://brid.gy/post/twitter/seirdy/1505255507946311680) by Thomas Steiner
"A look at search engines with their own indexes: seirdy.one/2021/03/10/sea…" 2022-03-19  
    [ Search engine survey: Comprehensively broad collection of search engines. There's only really 3 for English: Google, Bing, and …](https://brid.gy/post/twitter/seirdy/1505237444635021315) by Nelson Minar
"Search engine survey: Comprehensively broad collection of search engines. There's only really 3 for English: Google, Bing, and Yandex. seirdy.one/2021/03/10/sea… google bing search via:lobsters tootme" 2022-03-22  
     [ Ronan Jouchet - weekly reel ](https://ronan.jouchet.fr/2022/03/20/reel) 2022-03-24  
     [ Alternatives to Google Search – Le Alternative | English ](https://english.nuovosito.lealternative.net/2022/03/23/we-want-you/) 2022-04-01  
    [ March 2022 In Review](https://brainbaking.com/post/2022/04/march-2022/) by Wouter Groeneveld
"March 2022 is no more. I’m starting to feel the same time anxiousness that Winnie Lim wrote about: it feels like yesterday writing “February 2022 is no more”, while this month has three more days than the previous one! Looking back at the March blog posts, they were mostly about music: creating your own streaming server, choosing the right codec, an introduction to hip-hop. I recently extended my self-hosted Docker images with Gitea (and moved a few low-impact and private repositories o…" 2022-04-04  
     [ Duckduckgo censorship - General security & privacy chat - Purism community ](https://forums.puri.sm/t/duckduckgo-censorship/16638/102) 2022-04-05  
     [ News from last month (2022/04 edition) [ehret.me] ](https://ehret.me/news-from-last-month-202204-edition) 2022-04-17  
    [ Did you know @Bing's index helps power these search engines? Yahoo! (& One­Search) DuckDuck­Go AOL Qwant (partial) Ecosia Ekoru …](https://brid.gy/post/twitter/seirdy/1515716388752699397) by Jon Henshaw
"Did you know @Bing's index helps power these search engines? Yahoo! (& One­Search) DuckDuck­Go AOL Qwant (partial) Ecosia Ekoru Privado Findx Disconnect Search PrivacyWall Lilo Search­Scene Peekier Oscobo Million Short Yippy search Lycos Givero & more... seirdy.one/2021/03/10/sea…" 2022-05-04  
     [ Regarding Search Engines - Puppy Linux Discussion Forum ](https://forum.puppylinux.com/viewtopic.php?p=56606) 2022-05-04  
     [ homesteadingtoday.com/threads/great … ](https://www.homesteadingtoday.com/threads/great-article-on-alternative-search-engines.621268/) 2022-05-16  
    [ Indieseek.xyz Directory Additions May 2022](https://indieseek.xyz/2022/05/16/indieseek-xyz-directory-additions-may-2022/) by Brad
"I have added quite a few new listings.  Some are submissions and some are editorial adds. Also added are some new categories:Amtrak: under Recreation > Travel  I added some useful guides for traveling on Amtrak rail.  Because we have to decrease our use of cars and airplanes for travel so be need to start figuring out how we can use Amtrak.Europe: under News  I found these useful and not overly commercial. I also added a couple of search engines to the existing category. Source for the…" 2022-05-16  
     [ >I noted that there had been multiple weeks where not one single real person had... | Hacker News ](https://news.ycombinator.com/item?id=31397912) 2022-05-20  
    [ Rohan Kumar mentioned this Post on seirdy.one.](https://thenewleafjournal.com/a-2021-list-of-alternative-search-engines-and-search-resources/?replytocom=563) by Nicholas A. Ferrell 2022-05-24  
    [ Using one Search Engine (SE) for everything ignores the fact that different engines have different strengths. This report offers …](https://brid.gy/post/twitter/seirdy/1528710772968275969) by TRADECRAFT
"Using one Search Engine (SE) for everything ignores the fact that different engines have different strengths. This report offers a comprehensive overview of various SEs and the algorithms that power them. #OSINT #SearchEngines #OnlineSearch seirdy.one/2021/03/10/sea…" 2022-05-28  
    [ A large overview of search projects that build their own …](https://pleroma.envs.net/notice/AJu8Y1QyWLu9R0tO1w) by Humane Tech Now
This comment may have major formatting errors that could impact screen reader comprehension.
"A large overview of search projects that build their own indexes..https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html A look at search engines with their own indexes" 2022-05-28  
    [ A whole review of search engines seirdy.one/posts/2021/03/…](https://brid.gy/post/twitter/seirdy/1530661351030501376) by ana.
"A whole review of search engines seirdy.one/posts/2021/03/…" 2022-06-03  
    [ DuckDuckGo and Bing](https://seirdy.one/notes/2022/06/02/duckduckgo-and-bing/) by Rohan Kumar
"Reply to how would html.duckduckgo.com fit into this? by @penryn@www.librepunk.club I was referring to crawlers that build indexes for search engines to use. DuckDuckGo does have a crawler—DuckDuckBot—but it’s only used for fetching favicons and scraping certain sites for infoboxes (“instant answers”, the fancy widgets next to/above the classic link results). DuckDuckGo and other engines that use Bing’s commercial API have contractual arrangements that typically inc…" 2022-06-14  
    [ mastodon:: "@Seirdy@pleroma.envs.net if this is the workaroun…" - Coywolf Social](https://coywolf.social/@henshaw/108475945251308870) by Jon Henshaw :mastodon:
"if this is the workaround that Neeva had to come up with that took them an inordinate amount of time and resources, they might need to hire all new engineers 😆> This forces startups to spend inordinate amounts of time and resources coming up with workarounds. For example, Neeva implements a policy of “crawling a site so long as the robots.txt allows GoogleBot and does not specifically disallow Neevabot.”" 2022-06-14  
    [ "Not that Google would go…" - social.coop](https://social.coop/@cstanhope/108475963220607564) by Charles Stanhope
"Not that Google would go for this, but maybe instead of search neutrality we need collective crawling? One co-op crawling body with neutral access terms for that data.And perhaps this could be coupled with a push model instead of a pull model. Websites that want to be included in search can submit new or changed URLs once a day for the crawler to pick up.Then search engines can optimize access to their pool of data without burdening sites.This has been my daily thonk. :thonking:" 2022-06-21  
    [ A look at search engines with their own indexes | Lobsters](https://lobste.rs/s/rpyuic) by h0p3fu1 2022-06-21  
    [ Starts off being a review of search engines, ends up almost a thesis. seirdy.one/posts/2021/03/…](https://brid.gy/post/twitter/seirdy/1539243119937560577) by #WikiParty@michaelgraaf@campaign.openworlds.info
"Starts off being a review of search engines, ends up almost a thesis. seirdy.one/posts/2021/03/…" 2022-06-21  
    Tomáš Jakl [liked](https://nest.jakl.one/likes/2022-06-21-bzk8b/) this  2022-06-21  
     [ A look at search engines with their own indexes (2021) | Hacker News ](https://news.ycombinator.com/item?id=31820149) 2022-06-21  
     [ Search the Web: Maybe Find a Nugget or Two for Intrepid Researchers? : Stephen E. Arnold @ Beyond Search ](https://arnoldit.com/wordpress/2022/06/21/search-the-web-maybe-find-a-nugget-or-two-for-intrepid-researchers/) 2022-06-23  
    [ 搜尋引擎的替代方案清單](https://blog.gslin.org/archives/2022/06/24/10754/%e6%90%9c%e5%b0%8b%e5%bc%95%e6%93%8e%e7%9a%84%e6%9b%bf%e4%bb%a3%e6%96%b9%e6%a1%88%e6%b8%85%e5%96%ae/) by Gea-Suan Lin
"看到「A look at search engines with their own indexes」這篇在介紹各個搜尋引擎，作者設計了一套方法測試，另外在文章裡面也給了很多主觀的意見，算是很有參考價值的，可以試看看裡面提出來的建議。 另外在 Hacker News 上也有討論可以參考：「A look at search engines with their own indexes (2021) (seirdy.one)」。 在文章開頭的「General indexing search-engines」這個章節，先列出三大搜尋引擎 GBY (Google�…" 2022-06-25  
     [ Issue #328 ](https://www.pointer.io/archives/5e342f0e7d/) 2022-06-26  
    [ an exhaustive list of search engines out there](https://the.dailywebthing.com/an-exhaustive-list-of-search-engines-out-there/) by joe jenett 2022-06-27  
    [ 本文作者 Rohan Kumar 發現，搜尋引擎使用的索引很集中，以英語世界來說，大多來自「GBY」（Google, Bing 和 Yandex），他試圖整理各家搜尋引擎和索引，按照自行設計的研究方法去分類。 seirdy.one/posts/2021/03/…](https://brid.gy/post/twitter/seirdy/1541213834215452672) by 三創育成 Star Rocket
"本文作者 Rohan Kumar 發現，搜尋引擎使用的索引很集中，以英語世界來說，大多來自「GBY」（Google, Bing 和 Yandex），他試圖整理各家搜尋引擎和索引，按照自行設計的研究方法去分類。 seirdy.one/posts/2021/03/…" 2022-06-27  
    [ Un article terriblement complet sur les moteurs de recherche actuellement existants. Ca donne un petit vertige ... seirdy.one/posts/2021/03/…](https://brid.gy/post/twitter/seirdy/1541349873034960896) by Nicolas Delsaux
"Un article terriblement complet sur les moteurs de recherche actuellement existants. Ca donne un petit vertige ... seirdy.one/posts/2021/03/…" 2022-06-28  
    [ Different search engines and their primary searching index. - Good to be aware of different search indexes that exist. - Having …](https://brid.gy/post/twitter/seirdy/1539151770622087169) by Tech Article A Day
"Different search engines and their primary searching index. - Good to be aware of different search indexes that exist. - Having diff search engines is helpful to discover different results on different criteria. seirdy.one/posts/2021/03/…" 2022-06-29  
     [ Daum and Naver | revi ](https://blog.revi.xyz/daum-naver-search-independence) 2022-06-30  
    [ New Search Engines Added June 2022](https://indieseek.xyz/2022/06/30/new-search-engines-added-june-2022/) by Brad
"The elves that build search engines are really kicking into high gear, and I’m loving it.  If you have been following my writings for awhile you know that I want a Web with 5 to 8 major search engines and bunches of smaller search engines and hundreds of directories.  The Web is being harmed by having a Google and Bing duopoly controlling the gateways to the Web.  So I’m rooting for all search engines with their own indexes and crawlers and I’m always on the lookout for new contender…" 2022-07-08  
     [ Browser: Add Brave and Mojeek to search engines by Xexxa · Pull Request #14504 · SerenityOS/serenity · GitHub ](https://github.com/SerenityOS/serenity/pull/14504#issuecomment-1177510554) 2022-07-12  
     [ Divorcing Google, Part 2 | It From Bit ](https://blog.rowan.earth/divorcing-google-part-2/) 2022-07-25  
    [ “What I learned by building this list has profoundly changed how I surf. “Using one engine for everything ignores the fact that …](https://brid.gy/post/twitter/seirdy/1551370857322139648) by delan
"“What I learned by building this list has profoundly changed how I surf. “Using one engine for everything ignores the fact that different engines have different strengths.” seirdy.one/posts/2021/03/…" 2022-08-05  
    [ Brad Enslen](https://ramblinggit.com/2022/07/29/i-still-want.html) by Brad Enslen
"I still want at least 8 major English language web search engines with their own indexes. At least there are contenders forming now. Seirdy has the best rundown." 2022-08-06  
     [ Microsoft trackers run afoul of DuckDuckGo, get added to blocklist | Ars Technica ](https://arstechnica.com/gadgets/2022/08/microsoft-trackers-run-afoul-of-duckduckgo-get-added-to-blocklist/?comments=1&post=41130314#comment-41130314) 2022-08-07  
     [ Importance of Bing Indexing For Alt Search · The New Leaf Journal ](https://thenewleafjournal.com/importance-of-bing-indexing-for-alt-search/) 2022-09-20  
    [ Austin Huang ❤ You All: "@freakazoid@retro.social Well, there aren't many …" - Mastodon NZ](https://mastodon.nz/@a/109019295322796955) by Austin Huang ❤ You All
"@freakazoid Well, there aren't many good search *indexes* available (given computation power required), so it's really just either Google or Microsoft. See https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ ." 2022-09-24  
     [ Alternate Search Engines ](https://number1.co.za/alternate-search-engines/)
"Good gigablast.com – results aren’t from some generic source. Bitchute pages were in results. Still some pushing to specific directions. private.sh – Seems ok. neeva.com – Search Free From Corporate Influence. Decent results most times. OK wiby.me – only indexes old school websites, results not relevant at all. petalsearch – The chinese / huawei search engine – actually gives relevant results when you type in controversial search terms. Sites recommended include 4channel.org.…" 2022-10-02  
    [ A look at search engines with their own indexes](https://brid.gy/post/reddit/Seirdy/xswzzr) by VapidCanary 2022-10-02  
    [ A look at search engines with their own indexes](https://brid.gy/post/reddit/Seirdy/xsx3hq) by VapidCanary 2022-10-07  
     [ "A look at search engines with their own indexes" - Privacy - Privacy Guides ](https://discuss.privacyguides.org/t/a-look-at-search-engines-with-their-own-indexes/175) 2022-10-10  
     [ 科技創業週報 #341：誰來告訴我，軟體工程師沒有受到詛咒？ | Star Rocket Blog ](https://blog.starrocket.io/posts/newsletter-2022-06-23/) 2022-10-11  
    [ De plus en plus, il faut tester les moteurs alternatifs à Google, Bing et Yandex : seirdy.one/posts/2021/03/… Dont Brave Search …](https://brid.gy/comment/twitter/seirdy/1579776851618455552/1579776851618455552) by precisement.org
"De plus en plus, il faut tester les moteurs alternatifs à Google, Bing et Yandex : seirdy.one/posts/2021/03/… Dont Brave Search : precisement.org/blog/Brave-Sea…" 2022-11-02  
     [ Liens ](https://mdcdy.be/blog.html) 2022-11-14  
     [ Any opinions on mojeek.com? (privacy-focused search engine) \ stacker news ](https://stacker.news/items/37803) 2022-11-27  
    [ A new mysearch user published an index on Yessle mysearch. break information bubble take a look. yessle.com/mysearch/frind… I …](https://brid.gy/post/twitter/seirdy/1596979417083174912) by Wadim Seminsky
"A new mysearch user published an index on Yessle mysearch. break information bubble take a look. yessle.com/mysearch/frind… I found this : seirdy.one/posts/2021/03/…" 2022-12-09  
    [ Thanks. Duck is pretty much all Bing despite what the comments say. seirdy.one/posts/2021/03/…](https://brid.gy/comment/twitter/seirdy/1601133928990982144/1601133928990982144) by Colin Hayhurst
"Thanks. Duck is pretty much all Bing despite what the comments say. seirdy.one/posts/2021/03/…" 2022-12-13  
    [ @clovis Thanks - this is necessary. I am also building my own index, but have not made my instance public. Unlike "Linux Review" …](https://pleroma.envs.net/notice/AQZbDQyCpLcmowMUzI) by radiocron
This comment may have major formatting errors that could impact screen reader comprehension.
"@clovis Thanks - this is necessary. I am also building my own index, but have not made my instance public. Unlike "Linux Review" I had good luck with searX as a front end, because now Yacy has improved somewhat, especially if you curate. When I consolidate my crawls, I will share a searX site that uses them - in addition to gigablast and others." 2022-12-13  
    [ @clovis THIS project. If you could combine this with drupal, it would rock! I don't think it would be terribly difficult. It …](https://pleroma.envs.net/notice/AQZbDQyCpLcmowMUzI) by radiocron
This comment may have major formatting errors that could impact screen reader comprehension.
"@clovis THIS project. If you could combine this with drupal, it would rock! I don't think it would be terribly difficult. It would take some time, but would have users quickly - especially our news site. https://www.deepl.com/pro#developer" 2022-12-16  
    [ I beg to differ on "real". But don't take it from me: seirdy.one/posts/2021/03/…](https://brid.gy/comment/twitter/seirdy/1603750994093182977/1603750994093182977) by Colin Hayhurst
"I beg to differ on "real". But don't take it from me: seirdy.one/posts/2021/03/…" 2023-01-22  
    [ @Seirdy wow, this was really thought out! thanks for the read, i didnt expect to recieve such nuanced replies when making the …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/ARtTkcfEU5DOGPtL5U/ARtu2f7wf9SDvKaHlQ) by jo!
This comment may have major formatting errors that could impact screen reader comprehension.
"wow, this was really thought out! thanks for the read, i didnt expect to recieve such nuanced replies when making the pollwhat do you think about brave search's goggles? i didnt use brave search for long but i thought these were pretty neat for more specialised search (not having to add "rust lang" every time i look up some docs on smth is nice)one thing i tend to miss about large engines like google is the large amount of instant results like calculators which are often better/cleane…" 2023-01-31  
     [ Newsletter Leaf Journal CXX · The New Leaf Journal ](https://thenewleafjournal.com/letter/120/) 2023-02-08  
    [ Looking forward to playing around with New Search™️ from the makers of Windows™️ and The World's Biggest Advertising Company™️. …](https://brid.gy/post/twitter/seirdy/1623230167794475008) by Richard Young
"Looking forward to playing around with New Search™️ from the makers of Windows™️ and The World's Biggest Advertising Company™️. But then someone pointed me at this, which is an interesting list seirdy.one/posts/2021/03/…" 2023-02-10  
    [ @aurynn @RichardYoung Most decent English generalist engines are just Bing with their own take on infoboxes: …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/ASSlKqMHLv33OTSyzQ/ASSlKqMHLv33OTSyzQ) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@aurynn @RichardYoung Most decent English generalist engines are just Bing with their own take on infoboxes: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/I like the idea of building multiple engines from a single common index such as the Common Crawl. Alexandria is one such example. A look at search engines with their own indexes" 2023-02-10  
    [ @Seirdy @aurynn Mmmm - useful, thank you! DDG solved the Google enshittification problem for me, but better under-the-hood …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/ASSlKqMHLv33OTSyzQ/ASSmK0d3mTbyucTvbk) by Richard Young
This comment may have major formatting errors that could impact screen reader comprehension.
"@aurynn Mmmm - useful, thank you! DDG solved the Google enshittification problem for me, but better under-the-hood performance always welcome.(That said, I'm actually looking forward to experimenting with the AI Bing, even if my long-tem goal is just a nice, stripped back search experience that finds what I'm looking for... like Google did in the early days…)" 2023-02-10  
    [ Search engines and the illusion of choice: A 🧵 I've found this research project that I've been looking for since May. It raises …](https://brid.gy/post/twitter/seirdy/1623977859092996100) by Max
"Search engines and the illusion of choice: A 🧵 I've found this research project that I've been looking for since May. It raises a number of EXTREMELY interesting and genuinely shocking points about search engines, specifically "alternative" ones. seirdy.one/posts/2021/03/… 1/?" 2023-05-25  
     [ Seach index map updates - #2 by Josh - The Mojeek Discourse ](https://community.mojeek.com/t/seach-index-map-updates/576/2?u=seirdy) 2023-07-01  
    [ @Skolliagh Qwant utilise Bing.Les moteurs utilisant leur propre index sont peu nombreux:- Google- Bing - Yandex- Petal Search …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AXFm7DA66Z9YDEueiu) by 9x0rg
This comment may have major formatting errors that could impact screen reader comprehension.
"@Skolliagh Qwant utilise Bing.Les moteurs utilisant leur propre index sont peu nombreux:- Google- Bing - Yandex- Petal Search (Huawei)et...- MojeekPapier très détaillé à ce sujet:**A look at search engines with their own indexes**https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/Thanks @Seirdy for your very detailed post BTW! A look at search engines with their own indexes" 2023-07-06  
    [ @CobaltVelvet @haskal Ok, sampled from my blog post on the topic:Lixia Labs: brand new one that focuses on technical content and …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AXGw4Grb4yupWXSKeG/AXGw4Grb4yupWXSKeG) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@CobaltVelvet @haskal Ok, sampled from my blog post on the topic:Lixia Labs: brand new one that focuses on technical content and blogs.Wiby: mostly user-submitted Web-1.0 pages reminiscent of the “Old Web”.Marginalia Search: My favorite search engine. Penalizes pages with heavy JS, excessive harmful SEO practices, tracking, etc. and uses a weighted PageRank algorithm to prioritize better, simpler pages. Offers an optional ranking algorithm that prioritizes blogs.Kagi offers a “noncommer…" 2023-07-15  
    [ wanna read about search engines with their own indexes? this one is a good one 😉 …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AWYCNTo82yYDbO67f6) by Mojeek
This comment may have major formatting errors that could impact screen reader comprehension.
"wanna read about search engines with their own indexes? this one is a good one 😉 https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2023-07-15  
    [ @Mojeek Fascinating, thank you. One of the best articles Iʼve seen on the subject.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AWYCNTo82yYDbO67f6/AWaI5BxAg4rP3auTqK) by Jack Yan (甄爵恩)
This comment may have major formatting errors that could impact screen reader comprehension.
"@Mojeek Fascinating, thank you. One of the best articles Iʼve seen on the subject." 2023-08-08  
     [ Does DuckDuckGo Want To Search the Web? ](https://www.bookandsword.com/2023/03/18/state-of-web-search/) 2023-08-08  
     [ The Moonspeaker ](https://www.moonspeaker.ca/FoundSubjects/about.html#search) 2023-08-16  
    [ @Seirdy Oh, PSA on Naver, here's a big thread that have done of experience with Naver's atrocious conduct with Zepeto (which …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYm2vlvJsnls2T6WsC/AYm4EMWcda94iuyrdQ) by Keep dreaming 'bout a better world You keep wishing for some clarity Always hoping that a lightning
This comment may have major formatting errors that could impact screen reader comprehension.
"Oh, PSA on Naver, here's a big thread that have done of experience with Naver's atrocious conduct with Zepeto (which they run).https://toots.hwl.li/@jase/110888486598292767Just end of day, tldr, they're a corporation like any other only interested in spitting out corporate jargon and rather tone police than actually do shit.Not that any worse than any other search giant though tbf as they're all shit and wouldn't be any different any of them having control of Zepeto tbf. But yea, Nave…" 2023-08-16  
    [ Nice @Seirdy, Stract seems really cool!](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmOnGgwJgxZqjjDm4) by McSinyx 2023-08-16  
    [ @Seirdy optic is a great idea, i've wanted a search engine that has specific categories you can search in for a good while](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmPJ3ZecfGYQuTjYu) by 'Tired of people's shit', aka Ember
This comment may have major formatting errors that could impact screen reader comprehension.
"optic is a great idea, i've wanted a search engine that has specific categories you can search in for a good while" 2023-08-16  
    [ @Seirdy ooh, stract looks neat](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmP0nkUinK48iqPIW) by 'Tired of people's shit', aka Ember 2023-08-16  
    [ @Seirdy "Chat with an AI assistant that searches the web for you and cites its sources."blobfoxlurkglare​ that's sus tho](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmPaYToy6HvD15tbc) by 'Tired of people's shit', aka Ember
This comment may have major formatting errors that could impact screen reader comprehension.
""Chat with an AI assistant that searches the web for you and cites its sources."blobfoxlurkglare​ that's sus tho" 2023-08-16  
    [ @Ember Kagi is somewhat similar but lacks detailed ranking metadata from third party sources, so personalized ranking …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmPiB79j0Cr3h7yRk) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@Ember Kagi is somewhat similar but lacks detailed ranking metadata from third party sources, so personalized ranking adjustments just adjust a result’s position in a page rather than promoting results buried pages deep to the first page. Mojeek offers customization equivalent to adding a bunch of site: prefixes to your query, and might be working on something more that takes advantage of its own index.The homophobic cryptoshit one was leading in this area with its “goggles” feature off…" 2023-08-16  
    [ @Ember Marginalia has a few pre-set centrality algorithms centered around different types of pages, which is kind of similar. …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmQBKhp8wE1ChBGyW) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@Ember Marginalia has a few pre-set centrality algorithms centered around different types of pages, which is kind of similar. You can select them in a drop-down menu when you search." 2023-08-16  
    [ @Seirdy aw, geez. I hadn’t heard about Gigablast. That’s too bad.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmQb7F3pAJayX1Ndg) by Jason Lefkowitz
This comment may have major formatting errors that could impact screen reader comprehension.
"aw, geez. I hadn’t heard about Gigablast. That’s too bad." 2023-08-16  
    [ @Seirdy It looks like https://www.slzii.com/about describes itself more as some sort of community/social network than a search …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYmSGR4b64HKJ9OTho) by Tinyrabbit ✅
This comment may have major formatting errors that could impact screen reader comprehension.
"It looks like https://www.slzii.com/about describes itself more as some sort of community/social network than a search engine. Does it really belong on the list?" 2023-08-16  
    [ @Seirdy slzii looks like yellow page, not search engine](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYma4Do3OcY7JtLIlk) by 𝟙𝔸 2023-08-16  
    [ @iatendril It does appear to have a crawler and index for the included search engine so I included it for completeness.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYnD6ZeN351BrIvTVI) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@iatendril It does appear to have a crawler and index for the included search engine so I included it for completeness." 2023-08-16  
    [ @Seirdy This is a great resource! Thank you.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AYmNVuI0FpdRUeDpq4/AYnEINBXJqvsd0d3rs) by jeremiah 2023-09-03  
     [ SearXNG où comment avoir son propre metamoteur souverain ](https://dolys.fr/forums/topic/searxng-ou-comment-avoir-son-propre-metamoteur-souverain/)
"l’Almanet doLys Gnu/Linux – Open Source – Entreprises › Forums › L’almanet doLys Open Source › SearXNG où comment avoir son propre metamoteur souverain Mots-clés : moteur de recherche Ce sujet est vide. Log In Register Lost Password Affichage de 1 message (sur 1 au total) Auteur Articles août 15, 2023 à 4:19 #12536 nam1962nam1962Maître des clés J’utilisais j…" 2023-09-07  
    [ @QuietMisdreavus @noracodes While HN has extremely “rich white neoliberal anglo techbro” biases, it does make for an excellent …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AZXIPhOQkkAKuQcqum/AZXIgdm9SJ22c3ncfI) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@QuietMisdreavus @noracodes While HN has extremely “rich white neoliberal anglo techbro” biases, it does make for an excellent seed source for a search engine index (links to many places, easy to crawl, links are often to places that don’t do SEO so would be hard to find otherwise, etc.) so I sympathize with the decision to crawl it. But it shouldn’t receive so much disproportionate attention.I vastly prefer Marginalia’s approach of biasing its index around a few selected blogs and …" 2023-09-13  
     [ Teletexto #012 - Adrianistán ](https://blog.adrianistan.eu/teletexto-012) 2023-09-15  
    [ Oh and anyone who markets their search engine as “unbiased” is lying. An unbiased engine is just biased towards whoever has the biggest SEO budget.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AZmKp2Sgfh0oltE5om/AZmKuXdSCDEyu1t0RU) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"Oh and anyone who markets their search engine as “unbiased” is lying. An unbiased engine is just biased towards whoever has the biggest SEO budget." 2023-10-12  
    [ @davidism i can personally recommend #kagi and have no experience but with ddg, brave, goohgle, but @Seirdy has a great list: …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AahQGqqvUi0qR4g0cy/AahQGqqvUi0qR4g0cy) by Nils Goroll 🤒
This comment may have major formatting errors that could impact screen reader comprehension.
"@davidism i can personally recommend #kagi and have no experience but with ddg, brave, goohgle, but @Seirdy has a great list: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ kagi A look at search engines with their own indexes" 2023-10-20  
    [ @lawlznet @Wolven @Seirdy did a writeup of different search engines with their own …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AaxxJRzWeZwusQ0DvU/AaxxJRzWeZwusQ0DvU) by Pearlescent Ferret :flag_demigirl:
This comment may have major formatting errors that could impact screen reader comprehension.
"@lawlznet @Wolven @Seirdy did a writeup of different search engines with their own indexeshttps://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2023-10-22  
    [ @Seirdy @cybertailor ty! Will be sure to check these out](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Ab2Z4cXVj9Dk8c5tvU/Ab2cJp9lOpeTTVvaNM) by soweli Niko 2023-11-14  
    [ @Seirdy I won’t be able to fit this into the piece I’m finalizing today but this is perfect for a follow-up that I’m writing …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AbmZTasdxHRY8r2b8y/AbmaGlCYN0RCLFnXLU) by Mariya Delano
This comment may have major formatting errors that could impact screen reader comprehension.
"I won’t be able to fit this into the piece I’m finalizing today but this is perfect for a follow-up that I’m writing later in the week!! Again thank you very much" 2023-11-22  
    [ @holly I used mojeek for about 10 minutes before switching back to DDG 😅@Seirdy did a writeup of search engines if you're …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Ac2vGtxl0CyF5691qi/Ac2vGtxl0CyF5691qi) by Pearlescent Ferret :flag_demigirl:
This comment may have major formatting errors that could impact screen reader comprehension.
"@holly I used mojeek for about 10 minutes before switching back to DDG 😅@Seirdy did a writeup of search engines if you're interested.https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2023-11-22  
    [ @PearlescentFerret @holly Kagi mixes Google, Mojeek, and Teclis (its own index) together so you can get Actually Different …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Ac2vGtxl0CyF5691qi/Ac2xz7UIHKj5g4ZlyK) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@PearlescentFerret @holly Kagi mixes Google, Mojeek, and Teclis (its own index) together so you can get Actually Different results that are also Actually Good. But it costs money." 2023-11-28  
     [ About Marginalia Search @ marginalia.nu ](https://www.marginalia.nu/marginalia-search/about/) 2023-12-08  
     [ Cooking Pancakes · Daum and Naver ](https://revi.blog/daum-naver-search-independence)
"Daum and Naver I've stumbled upon this article and found out... Daum: Korean. Also unsure about this one’s independence. While they are not really well known outside South Korea, it has Wikipedia article and is one of the first search engine in Korea. I don't have much insight on how their search index is run, but they run their own index with own webmaster tools, site registration site (Korean only), and robots. They once worked with Google (well, in 2000s) for their non-Korean index but…" 2023-12-13  
    [ I’m working on a “boutique search engine” write-up, so I got a little sources collection going.My favorite bookmark so far is …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AcbXV5Wg6aquwyDwfI) by Jason
This comment may have major formatting errors that could impact screen reader comprehension.
"I’m working on a “boutique search engine” write-up, so I got a little sources collection going.My favorite bookmark so far is this list of search engines with their own indexes by Seirdy. The list is surprisingly comprehensive and wildly helpful. https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2023-12-13  
    [ Rohan Kumar on search engines with their own indexes](https://logicface.co.uk/rohan-kumar-on-search-engines-with-their-own-indexes/) by lukealexdavis
"Google is the lord and emperor of search (regardless of what Microsoft Bing has going on with OpenAI). But its focus on commercially-slanted results means people looking for personal blogs or generally “rough around the edges” content will struggle to find it. That’s where alternative search engines come in, built on top of their own indexes. Rohan Kumar took a deep dive into a list of search engines with his own indexes including the main ones: Google, Bing, Yandex, as well as lesse…" 2023-12-13  
     [ Are you still Googling or are you looking for more? A call for anti-capitalist language use ](https://interregnum.ghost.io/are-you-still-googling-or-are-you-looking-for-more-a-call-for-anti-capitalist-language-use/) 2024-02-08  
     [ 404media.co/this-guy-is-building-an … ](https://www.404media.co/this-guy-is-building-an-open-source-search-engine-in-real-time/) 2024-02-13  
     [ Google fails to downrank junk sites; Bing and Mojeek fare better ](https://jackyan.com/blog/2024/02/google-fails-to-downrank-junk-sites-bing-and-mojeek-fare-better/)
"Understandably, I was bemused but then frustrated with the fake articles out there about the new Google algorithm update being created by me and named for me. (Even Perplexity has picked up this misinformation.) Of all those I found and reached out to, only one author—Shahid Jafar—had the decency to remove his article and apologize. Shahid explained that he had found thousands of articles relating to this and based his on what he read. It’s easy to accept a sincere apology, which he ga…" 2024-02-22  
    [ Today’s find: An amazing listing of existing search engines: those using #Google & Bing’s indexes & many more.“The 3 dominant …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/Af7vy7ek5r9x6EGM3E) by Jeri Dansky
This comment may have major formatting errors that could impact screen reader comprehension.
"Today’s find: An amazing listing of existing search engines: those using #Google & Bing’s indexes & many more.“The 3 dominant English search engines with their own indexes are Google, Bing, & Yandex (GBY). Many alternatives to GBY exist, but almost none of them have their own results; instead, they just source their results from GBY.“With that in mind, I decided to test & catalog all the different indexing search engines I could find.”https://seirdy.one/posts/2021/03/10/search-engin…" 2024-02-28  
     [ Paid search engines: do they work and are they worth it? - google bing paidsearch | Ask MetaFilter ](https://ask.metafilter.com/378482/Paid-search-engines-do-they-work-and-are-they-worth-it#5375246) 2024-02-28  
     [ Folk search engines - by Elan Ullendorff ](https://escapethealgorithm.substack.com/p/folk-search-engines) 2024-02-28  
    [ 検索エンジンをめぐる冒険](https://tybx.jp/2024/02/17/%e6%a4%9c%e7%b4%a2%e3%82%a8%e3%83%b3%e3%82%b8%e3%83%b3%e3%82%92%e3%82%81%e3%81%90%e3%82%8b%e5%86%92%e9%99%ba) by pinacol 2024-02-28  
    [ How To Search The Internet](https://brainbaking.com/post/2024/01/how-to-search-the-internet/) by Wouter Groeneveld
"Thanks to the multi billion dollar advertisement industry, searching for something on the internet has devolved from a joyous Altavista guess-the-keywords activity to a tiring chore where one has to wade through endless pools of generated SEO-optimized crap, hollow company blogs with more social media link embeds than actual content, and Reddit flame wars than ever before. In short: great stuff. Suppose you’re looking for a review of a video game. The first 100 hits will return the expected…" 2024-03-26  
     [ Add more search providers · Issue #27 · webis-de/archive-query-log · GitHub ](https://github.com/webis-de/archive-query-log/issues/27) 2024-04-05  
    [ @lori @omegaprobe @pluralistic there are small independent search engines with their own indexes and some of them deprioritise …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgZy6TRS3WKJYkOMjY/AgZy6TRS3WKJYkOMjY) by jarek 🇺🇦
This comment may have major formatting errors that could impact screen reader comprehension.
"@lori @omegaprobe @pluralistic there are small independent search engines with their own indexes and some of them deprioritise ad-driven and other shitty pages https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2024-04-05  
    [ @jarek @lori @omegaprobe @pluralistic Interesting.Might mean that I have to let the Ahrefs crawler back into my sites again, as …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgZy6TRS3WKJYkOMjY/AgZy6XTj30WS4xUEpk) by Angus McIntyre
This comment may have major formatting errors that could impact screen reader comprehension.
"@jarek @lori @omegaprobe @pluralistic Interesting.Might mean that I have to let the Ahrefs crawler back into my sites again, as it seems to be used to power the Yep search engine, which looks quite good.It's past time that we figured out a way to do an end-run around Google: they've just become too predatory and too useless. That's a bad combo." 2024-04-05  
    [ @jarek I read this and was like "Oh damn I need to find this person and FOLLOW THEM" so I tracked them down and surprise! I already follow @Seirdy 🤣](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgZy6TRS3WKJYkOMjY/AgZyvZqpz90GCsdN8C) by ResearchBuzz
This comment may have major formatting errors that could impact screen reader comprehension.
"@jarek I read this and was like "Oh damn I need to find this person and FOLLOW THEM" so I tracked them down and surprise! I already follow @Seirdy 🤣" 2024-04-05  
    [ @researchbuzz @jarek Things I need to update when I get my laptop working again:Startpage uses Bing now, not Google.Some of …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgZy6TRS3WKJYkOMjY/Aga4lDgU97TyHoEhwu) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"@researchbuzz @jarek Things I need to update when I get my laptop working again:Startpage uses Bing now, not Google.Some of these engines are dead.Mullvad has an engine for members that uses and aggressively caches Google’s commercial API." 2024-04-05  
    [ @rysiek @matt @Mojeek If you're interested in other options then @Seirdy did an excellent piece on the topic that pretty much …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgagnU0SEE4FkI5CO8/AgagnU0SEE4FkI5CO8) by Jeremy Yap
This comment may have major formatting errors that could impact screen reader comprehension.
"@rysiek @matt @Mojeek If you're interested in other options then @Seirdy did an excellent piece on the topic that pretty much covers what's out there for now:https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2024-04-05  
    [ @nus everyone gets to draw the line somewhere. I draw it there. You may draw it elsewhere.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgagnU0SEE4FkI5CO8/Agagx6PYoEHbSkPfGa) by Michał "rysiek" Woźniak · 🇺🇦
This comment may have major formatting errors that could impact screen reader comprehension.
"@nus everyone gets to draw the line somewhere. I draw it there. You may draw it elsewhere." 2024-04-05  
     [ proto's blog - A Brief Survey of Alternative Search Engines ](https://proto.garden/blog/search_engines.html) 2024-04-06  
    [ @PersistentDreamer @crispius @Cal And, as luck would have it, @Seirdy just updated their forever article A look at search …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Agaj8VbBhckIfrPzPM/Agaj8VbBhckIfrPzPM) by Amgine
This comment may have major formatting errors that could impact screen reader comprehension.
"@PersistentDreamer @crispius @Cal And, as luck would have it, @Seirdy just updated their forever article A look at search engines with their own indexes — very recommended. A look at search engines with their own indexes" 2024-04-06  
    [ @amgine @PersistentDreamer @crispius @Cal @Seirdy Oh wow, this page is amazing. Thanks!](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Agaj8VbBhckIfrPzPM/AgcE1sB6e8AGPeUiWW) by Anthony Sorace
This comment may have major formatting errors that could impact screen reader comprehension.
"@amgine @PersistentDreamer @crispius @Cal @Seirdy Oh wow, this page is amazing. Thanks!" 2024-04-09  
     [ ⬜ Beyond the search engine - One Thing ](https://onethingnewsletter.substack.com/p/beyond-the-search-engine) 2024-04-14  
    [ I put this as a comment on the web page, but I'll repeat it here for people who aren't subscribed and might want this …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgbvqyqphJCOkSfUS8/AgbvqyqphJCOkSfUS8) by Anthony
This comment may have major formatting errors that could impact screen reader comprehension.
"I put this as a comment on the web page, but I'll repeat it here for people who aren't subscribed and might want this information:Hate to say it but Kagi looks to me like it's going to full-on enshittify in a few years. Besides the fact that the Kagi people seem like libertarian techbros, this is a standard Silicon Valley startup. Their business model appears to be using your search queries to train their AI so they can sell it back to you (yes they take subscription fees but that's not where…" 2024-04-14  
    [ I can't thank you enough for sharing all these links! I kinda wished that Corey Doctorow did just a tad more research on the …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgbvqyqphJCOkSfUS8/Agcmvdx87Uwax3ipyy) by Robert Kingett, blind
This comment may have major formatting errors that could impact screen reader comprehension.
"I can't thank you enough for sharing all these links! I kinda wished that Corey Doctorow did just a tad more research on the search engine before recommending it, but thank you for all these links! I bookmarked this so don't ever delete it! @abucci" 2024-04-14  
    [ @proto neat writeup! have you read seirdy's piece? https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AgIX3c65uXixBzaioa/AgIX3c65uXixBzaioa) by JJ :blobblackcat:
This comment may have major formatting errors that could impact screen reader comprehension.
"@proto neat writeup! have you read seirdy's piece? https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2024-04-27  
     [ Anthony (@abucci@buc.ci) ](https://buc.ci/abucci/p/1712157873.505318) 2024-05-01  
    [ @strypey that is such a cool list! Good to know there are so many search engines out there, whatever their strengths and weaknesses 💪@Seirdy](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AhRBIKOBeEMQKJhpQG/AhRer9Q1KCkv6nWLGy) by Hippo 🍉
This comment may have major formatting errors that could impact screen reader comprehension.
"@strypey that is such a cool list! Good to know there are so many search engines out there, whatever their strengths and weaknesses 💪@Seirdy" 2024-05-01  
    [ #TIL about #RightDao;"Independent, Uncensored, Private Search"... using its own index, not Goggle, Bing, or …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AhRBIKOBeEMQKJhpQG) by Strypey
This comment may have major formatting errors that could impact screen reader comprehension.
"#TIL about #RightDao;"Independent, Uncensored, Private Search"... using its own index, not Goggle, Bing, or Yandex:https://rightdao.com/#HatTip to @Seirdy for maintaining this page on web search engines;https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#search #WebSearch hattip rightdao search til websearch" 2024-05-01  
    [ @strypey "When talking to search engine founders, I found that the biggest obstacle to growing an index is getting blocked by …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AhRBIKOBeEMQKJhpQG/AhRezRKScPiayOs9y4) by Hippo 🍉
This comment may have major formatting errors that could impact screen reader comprehension.
"@strypey "When talking to search engine founders, I found that the biggest obstacle to growing an index is getting blocked by sites. Cloudflare is one of the worst offenders. Too many sites block perfectly well-behaved crawlers, only allowing major players like Googlebot, BingBot, and TwitterBot; this cements the current duopoly over English search and is harmful to the health of the Web as a whole."#Cloudfare is annoying! It sometimes blocks me too 🙄@Seirdy cloudfare" 2024-05-11  
     [ OpenOrb - a curated RSS and Atom feed search engine - Raphael Kabo ](https://raphael.computer/blog/openorb-curated-search-engine/) 2024-05-21  
    [ Talking about #SearchEngine, I can only recommend @Seirdy's synthesis work on « a look at search engines with their own indexes …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/Ai7QGjU8nRvzim8QZU) by DansLeRuSH ᴱᶰ
This comment may have major formatting errors that could impact screen reader comprehension.
"Talking about #SearchEngine, I can only recommend @Seirdy's synthesis work on « a look at search engines with their own indexes » (Last updated 2024-05-11)› https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ searchengine A look at search engines with their own indexes" 2024-05-22  
     [ kilroy - Wandering ](https://www.chrisritchie.org/kilroy/archive/2024/05/wandering.html) 2024-05-23  
    [ While Bing is down, time to (re)visit @Seirdy excellent post:****A look at search engines with their own …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AiB0Mn7cMrfAYtfTqC) by AGR Risk Intelligence
This comment may have major formatting errors that could impact screen reader comprehension.
"While Bing is down, time to (re)visit @Seirdy excellent post:****A look at search engines with their own indexes**https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/Including **Mojeek** (own index) and **SearxNG** a metasearch engine (list of public instances here: https://searx.space/)#Bing #SearchEngines #Mojeek #SearxNG bing mojeek searchengines searxng A look at search engines with their own indexes" 2024-05-23  
    [ @agr @Seirdy A very comprehensive article.I might make mojeek my primary search.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AiB0Mn7cMrfAYtfTqC/AiB2nZauyDWCKnGsL2) by Mark Burton
This comment may have major formatting errors that could impact screen reader comprehension.
"@agr @Seirdy A very comprehensive article.I might make mojeek my primary search." 2024-05-23  
    [ @agr @Seirdy Bing and DuckDuck down at the same time - is there a connection?🦆🦆](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AiB0Mn7cMrfAYtfTqC/AiB3jXofju0pcDLbkW) by Firehorseart lives!
This comment may have major formatting errors that could impact screen reader comprehension.
"@agr @Seirdy Bing and DuckDuck down at the same time - is there a connection?🦆🦆" 2024-05-23  
     [ A Look at Web Search: Useful for Some OSINT Work : Stephen E. Arnold @ Beyond Search ](https://arnoldit.com/wordpress/2024/02/22/a-look-at-web-search-useful-for-some-osint-work/) 2024-05-24  
    [ @bortzmeyerEffectivement, deux options : ne pas l'utiliser parce que l'index est tout p'tit ou au contraire contribuer à élargir …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AiB0qeR7E05iJO1giO/AiB3wzqcpX7gJmfwa8) by 9x0rg
This comment may have major formatting errors that could impact screen reader comprehension.
"@bortzmeyerEffectivement, deux options : ne pas l'utiliser parce que l'index est tout p'tit ou au contraire contribuer à élargir l'index en l'utilisant. J'aime bien la seconde.(Je parle de Mojeek ici, SearxNG étant quant à lui un méta-moteur). @Daemon" 2024-05-24  
    [ With that Bing outage, it’s may be a good time to read this very good post: “A look at search engines with their own indexes” by …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AiBLcTgmU67jxkR7tg) by Tixie Salander
This comment may have major formatting errors that could impact screen reader comprehension.
"With that Bing outage, it’s may be a good time to read this very good post: “A look at search engines with their own indexes” by Seirdy https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2024-05-24  
    [ @tixie Stract sure seems nice, testing it right now.](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AiBLcTgmU67jxkR7tg/AiBLcUxTlV4htpFyYy) by Longplay Games :pc_color: 🎮 2024-05-24  
    [ While Bing is down, a look at search engines with their own indexes …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AiBlbRyHyz4p9cnR0S) by bookandswordblog
This comment may have major formatting errors that could impact screen reader comprehension.
"While Bing is down, a look at search engines with their own indexes https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2024-05-24  
    [ So, #Bing is down, and everyone just (re-)discovered that their own alternate, artisanal search tool is just Bing under the …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AiBrQlqkKnv5LTYjQW) by Eric the Cerise
This comment may have major formatting errors that could impact screen reader comprehension.
"So, #Bing is down, and everyone just (re-)discovered that their own alternate, artisanal search tool is just Bing under the hood.Here is a page where someone ( Seirdy ) has collected a bunch of search services that use their own indices (not just Google, Bing or Yandex reskinned).I'm already using a few, but several are new to me.https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/Welcome to the Brave New Post-Google Internet! bing A look at search engines with their own indexes" 2024-05-24  
    [ So, #Bing is down, and everyone just (re-)discovered that their own alternate, artisanal search tool is just Bing under the …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AiBrQlqkKnv5LTYjQW/AiCzRL1KZ2oHDVFdx2) by Eric the Cerise
This comment may have major formatting errors that could impact screen reader comprehension.
"So, #Bing is down, and everyone just (re-)discovered that their own alternate, artisanal search tool is just Bing under the hood.Here is a page where someone ( Seirdy ) has collected a bunch of search services that use their own indices (not just Google, Bing or Yandex reskinned).I'm already using a few, but several are new to me.https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/Welcome to the Brave New Post-Google Internet!Edit: It turns out @Seirdy is on the 'Verse (I swea…" 2024-05-24  
     [ Bing outage shows just how little competition Google search really has | Ars Technica ](https://arstechnica.com/gadgets/2024/05/bing-outage-shows-just-how-little-competition-google-search-really-has/2/) 2024-05-24  
     [ A Comprehensive Evaluation of Various Search Engines I've Used | Scribbles 'n Bits ](https://scribbles.jbowdre.lol/post/a-comprehensive-evaluation-of-various-search-engines-i-ve-used) 2024-05-24  
    [ Next steps for my search engine collection](https://seirdy.one/notes/2024/05/24/next-steps-for-my-search-engine-collection/) by Rohan “Seirdy” Kumar
"Reply to A look at search engines with their own indexes by Seirdy My search engine article blew up recently, as yet another major publication linked it (yay! /gen), so I made some fixes: Moved a couple engines to the graveyard. h/t to dequbed for telling me about moose.at’s demise, and to my broken link checker for telling me about Siik being down for a while now. Updated my methodology section to emphasize how I now use word-substitutions to fingerprint an engin…" 2024-05-26  
     [ Thursday's Bing API Outage Took Down DuckDuckGo, Copilot, and ChatGPT Search - Slashdot ](https://slashdot.org/story/24/05/25/0758209/thursdays-bing-api-outage-took-down-duckduckgo-copilot-and-chatgpt-search) 2024-05-28  
     [ Whitelisting independent search crawlers · The New Leaf Journal ](https://thenewleafjournal.com/whitelisting-independent-search-crawlers/) 2024-06-04  
     [ Internet je manjši, kot si predstavljamo @ Slo-Tech ](https://slo-tech.com/novice/t829906) 2024-06-08  
    [ Two very interesting and thought- provoking links from …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/Aij20OE9ZJRCncFyW8) by bm
This comment may have major formatting errors that could impact screen reader comprehension.
"Two very interesting and thought- provoking links from @Seirdy:https://seirdy.one/posts/2021/01/27/whatsapp-and-the-domestication-of-users/> "Allaying data collection concerns by listing data not collected is misleading. WhatsApp doesn’t collect hair samples or retinal scans either; not collecting that information doesn’t mean it respects privacy because it doesn’t change the information WhatsApp *does* collect."andhttps://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/Extr…" 2024-06-12  
     [ A look at search engines with their own indexes (2021) | Hacker News ](https://news.ycombinator.com/item?id=40626011) 2024-07-02  
    [ @kaimacThis article's a great summary of search engines with an independent index: …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AjKMgbxVG39YSqk8Iq/AjKMgbxVG39YSqk8Iq) by Amin Hollon 🏳
This comment may have major formatting errors that could impact screen reader comprehension.
"@kaimacThis article's a great summary of search engines with an independent index: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/There's a "Small or non-commercial Web" section worth looking at A look at search engines with their own indexes" 2024-07-02  
    [ @amin @kaimac Also https://proto.garden/blog/search_engines.html by @proto](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AjKMgbxVG39YSqk8Iq/AjKNAcCiuSVVugAYG8) by Kartik Agaram
This comment may have major formatting errors that could impact screen reader comprehension.
"@amin @kaimac Also https://proto.garden/blog/search_engines.html by @proto" 2024-07-02  
    [ this gigantic catalogue of web search engines is fascinating: …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AimimsXAyFKAF8q0lU) by chris martens
This comment may have major formatting errors that could impact screen reader comprehension.
"this gigantic catalogue of web search engines is fascinating: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#fnref:1 A look at search engines with their own indexes" 2024-07-02  
    [ @mnem Every so often I think about building a search engine (not sure why), but seems to be quite a few out there now: …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AjVa3e9M3Ej1m7l3DM) by David Thomson
This comment may have major formatting errors that could impact screen reader comprehension.
"@mnem Every so often I think about building a search engine (not sure why), but seems to be quite a few out there now: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ - Marginalia looks interesting for finding older pages (written in Java!) A look at search engines with their own indexes" 2024-07-11  
     [ Di chi è l’indice dei motori di ricerca alternativi? ](https://www.goatseo.com/indice/)
"schema usabilità motori di ricerca Negli ultimi 25 anni i motori di ricerca ci hanno abituato a leggere tra una decina di link. Dal 2023 sono arrivate nuove interfacce per i motori di ricerca (Google l’ha chiamata GSE, Generative Search Experience; Bing l’ha chiamata Copilot) che estraggono e rimescolano contenuto prendendolo dall’interno dei siti internet. In teoria i motori di ricerca che usano tecnologie generative ci “risparmiano” un po di tempo di lettura. Anche grazie alla l…" 2024-07-31  
    [ The Web We've (Never) Lost](https://www.bitoff.org/web-we-never-lost/) by Jan Vlnas
"This text is partially a transcript, partially a recollection of a talk I presented on the PragueJS meetup in February 2024.[1] Abstract: Doesn't it feel like the web is getting worse every day? Do you miss the days when Google wasn't a garbage factory, Twitter wasn't a cesspool of Nazis, and you weren't treated like a pair of eyeballs with a wallet? Don't worry, the web of yore is still alive and kicking – in fact, it's thriving. You just need to know where to look. Let's take a dive into…" 2024-08-02  
     [ Week 7: Searching Beyond Google | Pearltrees ](http://www.pearltrees.com/t/search-information-landscape/week-7-searching-beyond-google/id17715439/item624058672) 2024-08-16  
     [ Search Engine NLJ Domain Search Test · The New Leaf Journal ](https://thenewleafjournal.com/search-engine-nlj-domain-search-test/) 2024-09-10  
    [ Linking this again since it seems to be getting attention on Cohost.If you're looking for alternative search options that aren't …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/AlrirsB3pjH1joZZQ0) by Jeremy Yap
This comment may have major formatting errors that could impact screen reader comprehension.
"Linking this again since it seems to be getting attention on Cohost.If you're looking for alternative search options that aren't just using Google's and Bing's indexes, I'd highly recommend this piece.Thanks to @Seirdy for looking into this.https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#search #searchengine #searchengines search searchengine searchengines A look at search engines with their own indexes" 2024-09-25  
     [ Link Roundup 4: Nerd Stuff (of various flavors) | videodante ](https://blog.dante.cool/link-roundup-4-nerd-stuff-of-various-flavors/) 2024-10-23  
     [ #3 ‘Bit of the Universe, Thinking to Itself’ ](https://mikegrindle.com/newsletter/itm-3#searching-for-search-engines) 2024-11-03  
     [ searching for search - ultrasciencelabs ](https://ultrasciencelabs.com/lab-notes/the-web/searching-for-search) 2024-11-25  
    [ it's time to reinvent the wheel](https://benjaminhollon.com/musings/its-time-to-reinvent-the-wheel/) by benjamin hollon
"Things are broken. Everywhere, there are broken things. There are beautiful things in the mix, but so much is broken or built on broken foundations. I’ve never really been one to accept a broken foundation of how the world works. Now is the time to reinvent the wheel, and it always was, no matter the lies you’ve been told. wheels i’ve reinvented Web search is pretty broken. I’m reinventing that wheel via Clew, a fiercely-independent search engine designed to emphasize the voices of in…" 2024-12-01  
    [ “Ecosia supposedly started pulling data from Google recently”@SuperSluether I didn’t know this. Got a link? @fuchsi …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AiBrQlqkKnv5LTYjQW/AiDLYMaVKjEz62SUeO) by Seirdy
This comment may have major formatting errors that could impact screen reader comprehension.
"“Ecosia supposedly started pulling data from Google recently”@SuperSluether I didn’t know this. Got a link? @fuchsi @ErictheCerise Edit: Found this announcement from Ecosia. I’ll run some tests." 2024-12-01  
    [ @Pajo_16 @nixCraft If you're looking for blogs and other personal sites I recommend bookmarking these search engines:- …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Ahcf9SE5EX5edqME6a/Ahcf9SE5EX5edqME6a) by Jeremy Yap
This comment may have major formatting errors that could impact screen reader comprehension.
"@Pajo_16 @nixCraft If you're looking for blogs and other personal sites I recommend bookmarking these search engines:- https://search.marginalia.nu/- https://ichi.do/- https://clew.se/- https://searchmysite.net/- https://wiby.me/Would also recommend checking out this very excellent piece as well for alternative search options: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ Marginalia Search" 2024-12-01  
    [ @5ciFiGirl @ErictheCerise @Pajo_16 @nixCraftYep!It's very similar to Clew in goals (promoting personal, non-commercial websites) …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Ahcf9SE5EX5edqME6a/AhchulyloGFPQIsywK) by Amin Hollon 🏳
This comment may have major formatting errors that could impact screen reader comprehension.
"@5ciFiGirl @ErictheCerise @Pajo_16 @nixCraftYep!It's very similar to Clew in goals (promoting personal, non-commercial websites) and even uses the same ranking function at heart (BM25F) but I did make a number of changes in methodology, for example:Most of my webpage discovery is centered around RSS feeds (which is both a great mature technology and means sites with RSS feeds [often personal sites] are gonna be better-treated by the crawler)Marginalia still indexes big sites like Wikipedia an…" 2024-12-01  
    [ @Pajo_16 @nixCraft If you're looking for blogs and other personal sites I recommend bookmarking these search engines:- …](https://brid.gy/post/mastodon/@seirdy@pleroma.envs.net/Ahcf9SE5EX5edqME6a) by Jeremy Yap
This comment may have major formatting errors that could impact screen reader comprehension.
"@Pajo_16 @nixCraft If you're looking for blogs and other personal sites I recommend bookmarking these search engines:- https://search.marginalia.nu/- https://ichi.do/- https://clew.se/- https://searchmysite.net/- https://wiby.me/Would also recommend checking out this very excellent piece as well for alternative search options: https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ Marginalia Search" 2024-12-01  
    [ @jeruyyap @Pajo_16 @nixCraft I've captured a bunch of search engines and other sites dedicated to exploring the #IndieWeb here …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/Ahcf9SE5EX5edqME6a/AhdSXlbti8PZSqieJc) by shellsharks
This comment may have major formatting errors that could impact screen reader comprehension.
"@jeruyyap @Pajo_16 @nixCraft I've captured a bunch of search engines and other sites dedicated to exploring the #IndieWeb here https://shellsharks.com/indieweb#explore-the-indieweb indieweb IndieWeb Assimilation" 2024-12-01  
     [ Comments - Google Search is obsolete - by Mike Elgan ](https://machinesociety.ai/p/google-search-is-obsolete/comment/48795170) 2024-12-01  
     [ RC Week 2 ](https://gracekwak.me/blog/2024/11/15/rc-week-2) 2024-12-02  
     [ cohost! - "Neat search engines you may not have heard of" ](https://cohost.org/jetsetruri/post/4669844-neat-search-engines) 2024-12-02  
    [ @dan_ballard I've switched to a bunch of search engines with their own indexes and brought back a lot of old-school search …](https://brid.gy/comment/mastodon/@seirdy@pleroma.envs.net/AnyQCoCcv53KmxRBQm/AnyQCoCcv53KmxRBQm) by Jeremy Yap
This comment may have major formatting errors that could impact screen reader comprehension.
"@dan_ballard I've switched to a bunch of search engines with their own indexes and brought back a lot of old-school search habits, and that pretty much works for my needs most of the time with the exception of super-new stuff.Would strongly recommend checking out this piece on the topic for an overview of what options are available:https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/ A look at search engines with their own indexes" 2024-12-07  
     [ It had to happen: the SEO's are building search engines now ](https://th3core.com/talk/traffic/it-had-to-happen-the-seo%27s-are-building-search-engines-now/) 2025-02-18  
    [ Indefensible](https://bobbyhiltz.com/blog/2025/01/indefensible/) by Bobby Hiltz
"People will come to love their oppression, to adore the technologies that undo their capacities to think. —Aldous Huxley Let’s put the cards on the table… The Bosses of the Senate Presidential inauguration 2025 First we have Joseph Keppler’s oft-used cartoon, “The Bosses of the Senate.” Then we see some presidential inauguration guests, including Mark Zuckerberg, Jeff Bezos, Sundar Pichai, and Elon Musk, on 20 January 2025 (photo by Julia Demaree Nikhinson/AP). Those cards…" 2025-03-28  
    [ This is the best coverage of Search engines I have ever found. Great Resource.](https://brid.gy/comment/reddit/seirdy/m9hesi/mk1vyuj) by considerableforsight
"This is the best coverage of Search engines I have ever found. Great Resource." 2025-04-14  
     [ Indefensible ](https://bobbyhiltz.com/posts/2025/01/indefensible/)
"People will come to love their oppression, to adore the technologies that undo their capacities to think. —Aldous Huxley Let’s put the cards on the table… The Bosses of the Senate Presidential inauguration 2025 First we have Joseph Keppler’s oft-used cartoon, “The Bosses of the Senate.” Then we see some presidential inauguration guests, including Mark Zuckerberg, Jeff Bezos, Sundar Pichai, and Elon Musk, on 20 January 2025 (photo by Julia Demaree Nikhinson/AP). Those cards make a…" 2025-04-17  
     [ Low Friction Introduction to Digital Privacy ](https://bobbyhiltz.com/posts/2022/03/guide-privacy/)
"This guide is not meant to be a list of suggestions and recommendations in the traditional “you should do this” sense. It is up to each individual person to contemplate their needs and how far they are willing to go to achieve them. Your privacy, security, and anonymity matter. The decisions to take should not be decided by a stranger on the Internet. When the wording in this guide implies suggestion, it should be understood as “several websites and individuals on the Internet suggest,�…" 2025-06-08  
     [ 2025-03-28 ](https://envs.net/~wheresalice/blog/2025-03-28.html) 2025-06-15  
    [ A Secret Web](https://blog.clew.se/posts/secret-web/) by Benjamin Hollon
"The web is mind-bogglingly massive. So massive, in fact, that it’s nearly impossibly to visualize its true scale. Even if your entire lifetime was spent perusing the web and searching every nook and cranny, you would never reach more than a miniscule fraction of the vast ocean of information available to you. There is so much information in the world that “post-scarcity” is a severe understatement of the scale of our information age. To have any hope of meaningfully browsing the web, we…" 2025-07-01  
    [ they did a long time ago, i hopped off when they announced it.... i like startpage a lot, but this article is good to browse …](https://bsky.brid.gy/convert/web/at://did:plc:yxeqwyh2b2lqlqnxaxjlx3yh/app.bsky.feed.post/3lswbukfo722t%23bridgy-fed-create) by Kip
"they did a long time ago, i hopped off when they announced it.... i like startpage a lot, but this article is good to browse through if youre looking for a new search engine: seirdy.one/posts/2021/0..."
Feel free to contact me directly with feedback; [here’s my contact info](https://seirdy.one/about/#location-seirdy-online)
* * *
## Continue reading
  * Previous post: [Keeping platforms open](https://seirdy.one/posts/2021/02/23/keeping-platforms-open/)
  * Next post: [Misinfo about Permissions Policy and FLoC](https://seirdy.one/posts/2021/04/16/permissions-policy-floc-misinfo/)


This place is not a place of honor. Opinions are those of your employer.
For more information, please re-read.
* * *
You are here: 
  1. [ Articles ](https://seirdy.one/posts/)
  2. [ A look at search engines with their own indexes ](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/)


* * *
Copyright 2025 [![](https://seirdy.one/favicon.1250396055.png) Seirdy](https://seirdy.one/)
  * [ CC BY-SA 4.0 ](https://creativecommons.org/licenses/by-sa/4.0/)
  * [Source code](https://sr.ht/~seirdy/seirdy.one/)
  * [Tor](http://wgq3bd2kqoybhstp77i3wrzbfnsyd27wt34psaja4grqiezqircorkyd.onion/posts/2021/03/10/search-engines-with-own-indexes/)
  * [Privacy](https://seirdy.one/meta/privacy/)
  * [Site design](https://seirdy.one/meta/site-design/)


* * *
[ ![88-by-31 button: my favicon, a white colon and semicolon on a black backround, next to the word Seirdy.](https://seirdy.one/p/b/sticker_88x31.3319174455.png) ](https://seirdy.one/meta/badges/)
  *[GBY]: Google, Bing, Yandex
  *[SEO]: search-engine optimization
  *[TLD]: top-level domain
  *[FLOSS]: Free, Libre, Open-Source Software
