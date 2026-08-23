[FETCH]... ↓ https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html 
| ✓ | ⏱: 1.53s 
[SCRAPE].. ◆ https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html 
| ✓ | ⏱: 0.15s 
[COMPLETE] ● https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html 
| ✓ | ⏱: 1.69s 
# Content from: https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html

## Preface
This is a cursory review of all the indexing search engines I have been able to find.
The three dominant English search engines with their own indexes are Google, Bing, and Yandex (GBY). Many alternatives to GBY exist, but almost none of them have their own results; instead, they just source their results from GBY.
With that in mind, I decided to test and catalog all the different indexing search engines I could find. I prioritized breadth over depth, and encourage readers to try the engines out themselves if they’d like more information.
This page is a “living document” that I plan on updating indefinitely. Check for updates once in a while if you find this page interesting. Feel free to send me suggestions, updates, and corrections; I’d especially appreciate help from those who speak languages besides English and can evaluate a non-English indexing search engine. Contact info is in the article footer.
I plan on updating the engines in the top two categories with more info comparing the structured/linked data the engines leverage (RDFa vocabularies, microdata, microformats, JSON-LD, etc.) to help authors determine which formats to use.
Toggle table of contents
## About the list
I discuss my motivation for making this page in the [Rationale section](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#rationale).
I primarily evaluated English-speaking search engines because that’s my primary language. With some difficulty, I could probably evaluate a Spanish one; however, I wasn’t able to find many Spanish-language engines powered by their own crawlers.
I mention details like “allows site submissions” and structured data support where I can only to inform authors about their options, not as points in engines’ favor.
See the [Methodology section](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#methodology) at the bottom to learn how I evaluated each one.
## General indexing search-engines
### Large indexes, good results
These are large engines that pass all my standard tests and more. 

Google
    The biggest index. Allows submitting pages and sitemaps for crawling, and [even supports WebSub](https://developers.google.com/search/docs/advanced/sitemaps/build-sitemap#addsitemap) to automate the process. Powers a few other engines: 
  * A former version of [Startpage](https://www.startpage.com/), possibly the most popular Google proxy. Startpage now uses Bing
  * [GMX Search](https://search.gmx.com/web), run by a popular German email provider.
  * (discontinued) Runnaroo
  * [Mullvad Leta](https://leta.mullvad.net/faq)
  * [SAPO](https://www.sapo.pt/) (Portuguese interface, can work with English results)
  *   *   * [Zarebin](https://zarebin.ir/) (Persian, can return English results)
  * Ecosia (choose between Google and Bing providers in settings)
  * A host of other engines using [Programmable Search Engine’s](https://developers.google.com/custom-search/) client-side scripts.



Bing
    The runner-up. Allows submitting pages and sitemaps for crawling without login using [the IndexNow API](https://www.indexnow.org/), sharing IndexNow page submissions with Yandex and Seznam. Its index powers many other engines: 
  * Yahoo (and its sibling engine, One­Search)
  * DuckDuck­Go (offers a Tor onion service, a JS-free version, and a TUI-browser-friendly “lite” version making it a good way to use Bing anonymously)
  * AOL
  * Qwant (partial) 
  * Ecosia (choose between Google and Bing providers in settings)
  * Ekoru
  * Privado
  * Findx
  * Disconnect Search 
  * PrivacyWall
  * Lilo
  * Search­Scene
  * Peekier (not to be confused with Peekr, a metasearch engine with its own index)
  * Oscobo
  * Million Short
  * Yippy search 
  * Lycos
  * Givero
  * Swisscows
  * Fireball
  * Netzzappen
  * You.com 
  * Vuhuv
  * Partially powers MetaGer by default; this can be turned off
  * ChatGPT Search 
  * At this point, I mostly stopped adding Bing-based search engines. There are just too many.



Yandex
    Originally a Russian search engine, it now has an English version. Some Russian results bleed into its English site. It allows submitting pages and sitemaps for crawling using the IndexNow API, sharing IndexNow page submissions with Bing and Seznam. Powers: 
  * Epic Search (went paid-only as of June 2021)
  * Occasionally powers DuckDuck­Go’s link results instead of Bing (update: DuckDuckGo has “paused” its partnership with Yandex, confirmed in [Hearing on “Holding Big Tech Accountable: Legislation to Protect Online Users”](https://energycommerce.house.gov/committee-activity/hearings/hearing-on-holding-big-tech-accountable-legislation-to-protect-online)
  * Petal, for Russian users only.

    Seems privacy-oriented with a large index containing billions of pages. Quality isn’t at GBY’s level, but it’s not bad either. If I had to use Mojeek as my default general search engine, I’d live. Partially powers [eTools.ch](https://www.etools.ch/). At this moment, _I think that Mojeek is the best alternative to GBY_ for general search.
Google, Bing, and Yandex support structured data such as microformats1, microdata, RDFa, Open Graph markup, and JSON-LD. Yandex’s support for microformats1 is limited; for instance, it can parse `h-card` metadata for organizations but not people. Open Graph and Schema.org are the only supported vocabularies I’m aware of. Mojeek is evaluating structured data; it’s interested in Open Graph and Schema.org vocabularies.
### Smaller indexes or less relevant results
These engines pass most of the tests listed in the “methodology” section. All of them seem relatively privacy-friendly. I wouldn’t recommend using these engines to find specific answers; they’re better for learning about a topic by finding interesting pages related to a set of keywords.      **My favorite generalist engine on this page.** Stract supports advanced ranking customization by allowing users to import “optics” files, like a better version of Brave’s “goggles” feature. [Stract is fully open-source](https://github.com/StractOrg/stract), with code released under an AGPL-3.0 license. The index is isn’t massive but it’s big enough to be a useful supplement to more major engines. Stract started with the Common Crawl index, but now uses its own crawler. Plans to add contextual ads and a subscription option for ad-free search. Discovered in my access logs.     Very fast, good results. Passes the tests fairly well. It plans on including query-based ads if/when its user base grows. For the past few months, its index seems to have focused more on large, established sites rather than smaller, independent ones. It seems to be a bit lacking in more recent pages.     A pretty new “non-profit, ad free” engine, with [freely-licensed code](https://github.com/alexandria-org/alexandria). Surprisingly good at finding recent pages. Its index is built from the Common Crawl; it isn’t as big as Gigablast or Right Dao but its ranking is great.     An ambitious engine from Ahrefs, an SEO/backlink-finder company, that “shares ad profit with creators and protects your privacy”. Most engines show results that include keywords from or related to the query; Yep also shows results linked by pages containing the query. In other words, not all results contain relevant keywords. This makes it excellent for less precise searches and discovery of “related sites”, especially with its index of _hundreds of billions of pages._ It’s far worse at finding very specific information or recent events for now, but it will probably improve. It was known as “FairSearch” before its official launch.     Although it’s a Chinese engine, its index seems to have a large-enough proportion of English content to fit here. The engine is open-source; see the [SeSe back-end Python code](https://github.com/RimoChan/sese-engine) and [the SeSe-ui Vue-based front-end](https://github.com/YunYouJun/sese-engine-ui). It has surprisingly good results for such a low-budget project. Each result is annotated with detailed ranking metadata such as keyword relevance and backlink weight. Discovered in my access logs.     Its tagline is “Search the Internet with no filters, no tracking, no ads.” At the time of writing, it has over 3 million pages indexed. It’s surprisingly good at finding interesting new results for broad short-tail queries, if you’re willing to scroll far enough down the page. It appears to be good at finding recent pages.
Yep supports Open Graph and some JSON-LD at the moment. A look through the source code for Alexandria and Gigablast didn’t seem to reveal the use of any structured data. The surprising quality of results from SeSe and Right Dao seems influenced by the crawlers’ high-quality starting location: Wikipedia.
### Smaller indexes, hit-and-miss
These engines fail badly at a few important tests. Otherwise, they seem to work well enough for users who’d like some more serendipity in less-specific searches. 

[Peekr (formerly SvMetaSearch, not to be confused with Peekier)](https://peekr.org/) 
    Originally a SearxNG metasearch engine that also included results from its own index, it’s since diverged. It now appears to return all results from its own growing ElasticSearch index. Open source, with an emphasis on self-hostability.     The interface is in German but it supports searching in English just fine. The default language is selected by your locale. It’s really good considering its small index; it hasn’t heard of less common terms, but it’s able to find relevant results in other tests. It’s the second-fastest-improving engines in this section.     Slow, quality is hit-and-miss. Its indexer claims to crawl the DMOZ directory, which has since shut down and been replaced by the [Curlie](https://curlie.org) directory. No relevant results for “Oppenheimer” and some other history-related queries. Allows submitting individual URLs for indexing, but requires solving a Google reCAPTCHA and entering an email address.     Small index, disproportionately dominated by big sites. Failed multiple tests. Allows submitting individual URLs for crawling, but requires entering an email address and receiving a newsletter. Webmaster tools seem to heavily push for paid SEO options. It also powers SitesOnDisplay and [Blog-search.com](https://www.blog-search.com).     Very small index, but seems fine at ranking more relevant results higher. Allows site submission without any extra steps.     An experimental engine by researchers that uses the [Common Crawl](https://commoncrawl.org/) index. The engine is [open source](https://github.com/chatnoir-eu). See the [announcement](https://groups.google.com/g/common-crawl/c/3o2dOHpeRxo/m/H2Osqz9dAAAJ) on the Common Crawl mailing list (Google Groups). 

[Secret Search Engine Labs](http://www.secretsearchenginelabs.com/) 
    Very small index with very little SEO spam; it toes the line between a “search engine” and a “surf engine”. It’s best for reading about broad topics that would otherwise be dominated by SEO spam, thanks to its [CashRank algorithm](http://www.secretsearchenginelabs.com/tech/cashrank.php). Allows site submission.     A search engine from a hosting company. I found few details abou the search engine itself, and the index was small, but it was suitable for discovering new pages related to short broad queries.     Docs, blog posts, etc. have not been updated since around 2006 but the engine continues to crawl and index new pages. Discovered in my access logs. Has a bias towards older content.     While Gigablast seems dead, a version of it was open-source. This is based on that version of Gigablast. Its index is small but results are still useful for surfing new unseen corners of short-tail queries. Found via my access logs.     Does not appear to support full-page search, but does search page titles and description meta-tags. Supports URL submission. Found in my access logs. Currently in a prototype/experimental stage.
### Fledgling engines
Results from these search engines don’t seem particularly relevant; indexes in this category tend to be small.     Seems new; allows page submission by pasting a page into the search box. Index is really small but it crawls new sites quickly. Claims to be private.     Extremely quick to update its index; site submissions show up in seconds. Unfortunately, its index only contains a few thousand documents (under 100 thousand at the time of writing). It’s growing fast: if you search for a term, it’ll start crawling related pages and grow its index. 

YaCy
    Community-made index; slow. Results are awful/irrelevant, but can be useful for intranet or custom search. 

Scopia
    Only seems to be available via the [MetaGer](https://metager.org) metasearch engine after turning off Bing and news results. Tiny index, very low-quality. As of 2024-09-10, [MetaGer is paid-only after losing its advertising contract with Yahoo](https://suma-ev.de/en/eine-aera-geht-zu-ende/).     Primarily Turkish, but it also seems to support English results. Like Plumb, it uses client-side JS to fetch results from existing engines (Google, Bing, Yahoo, Petal, and others); like MetaGer, it has an option to use its own independent index. Results from its index are almost always empty. Very simple queries (“twitter”, “wikipedia”, “reddit”) give some answers. Supports site submission and crowdsourced instant answers. 

[Active Search Results](https://www.activesearchresults.com) 
    Very poor quality. Results seem highly biased towards commercial sites.     Young, slow. In this category because its index has a cap of 10 URLs per domain. I initially discovered Crawlson in the seirdy.one access logs. This is often down; if the current downtime persists, I’ll add it to the graveyard.     Results are few and irrelevant; fails to find any results for basic terms. Allows site submission. It’s also a lightweight social network and claims to be powered by its users, letting members vote on listings to alter rankings.     A FLOSS search engine that boasts a very impressive [feature-set](https://www.seekquarry.com/): it can parse sitemaps, feeds, and a variety of markup formats; it can import pre-curated data in forms such as access logs, Usenet posts, and WARC archives; it also supports feed-based news search. Despite the impressive feature set, Yioop’s results are few and irrelevant due to its small index. It allows submitting sites for crawling. Like Meorca, Yioop has social features such as blogs, wikis, and a chat bot API.      A small engine made by [James Mills](https://www.prologic.blog/), described in [So I’m a Knucklehead eh?](https://www.prologic.blog/2021/02/14/so-im-a.html). It’s written in Go; check out its [MIT-licensed Spyda source code](https://git.mills.io/prologic/spyda).     A new web portal with a search engine. Has a tiny index dominated by SEO spam. Discovered in the seirdy.one access logs. 

[Content truncated...]
