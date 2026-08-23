# Dual-Mode Scrape Report — Q24: trafilatura vs readability content extraction

**Source:** `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/searxng/dev/search_pipeline/01_reports/pipeline_smoke_20260505_180433.md`  
**Query:** Q24 — trafilatura vs readability content extraction  
**Output dir:** `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/searxng/.claude/worktrees/scrape-prep/dev/scrape_pipeline/01_dual_mode_outputs/20260505_185247`  
**URLs:** 20  
**Started:** 2026-05-05T18:52:47  
**Finished:** 2026-05-05T18:53:54  
**Runtime:** 67s  

---
## Summary Table

| # | Class | URL | M1 status | M1 bytes | M2 status | M2 bytes | M2 garbage |
|---|-------|-----|-----------|----------|-----------|----------|------------|
| 1 | GENERAL | https://github.com/adbar/trafilatura/issues/25 | plugin_routed | 0 | plugin_routed | 303 | plugin_routed |
| 2 | GENERAL | https://chuniversiteit.nl/papers/comparison-of-web-content-e… | ok | 14,185 | ok | 7,507 | — |
| 3 | GENERAL | https://downloads.webis.de/publications/slides/bevendorff_20… | no_content | 0 | ok | 87 | — |
| 4 | GENERAL | https://trafilatura.readthedocs.io/en/latest/evaluation.html | ok | 19,447 | ok | 15,122 | — |
| 5 | GENERAL | https://www.contextractor.com/trafilatura-vs-readability-vs-… | ok | 19,500 | ok | 15,177 | — |
| 6 | GENERAL | https://www.libhunt.com/r/trafilatura | ok | 25,168 | ok | 11,531 | — |
| 7 | GENERAL | https://webscraping.fyi/lib/compare/python-readability-vs-py… | ok | 14,450 | ok | 3,277 | — |
| 8 | GENERAL | https://www.libhunt.com/r/htmldate | ok | 19,933 | ok | 6,471 | — |
| 9 | GENERAL | https://justtothepoint.com/code/scrape/ | ok | 16,934 | ok | 14,442 | — |
| 10 | GENERAL | https://news.ycombinator.com/item?id=44067409 | ok | 51,079 | ok | 15,114 | — |
| 11 | GENERAL | https://adrien.barbaresi.eu/blog/tag/data-mining.html | ok | 10,915 | ok | 8,074 | — |
| 12 | GENERAL | https://news.ycombinator.com/item?id=40035347 | ok | 9,408 | ok | 5,663 | — |
| 13 | ACADEMIC | https://doi.org/10.18653/v1/2023.semeval-1.317 | ok | 17,750 | ok | 14,578 | — |
| 14 | ACADEMIC | https://searchstudies.org/wp-content/uploads/2025/02/Thesis_… | no_content | 0 | ok | 100 | — |
| 15 | ACADEMIC | https://doi.org/10.1145/1526709.1526911 | ok | 27,756 | ok | 11,413 | — |
| 16 | ACADEMIC | https://doi.org/10.18653/v1/2023.acl-long.169 | ok | 16,035 | ok | 12,841 | — |
| 17 | QA | https://seirdy.one/posts/2020/11/23/website-best-practices/ | ok | 228,672 | ok | 13,936 | — |
| 18 | QA | https://seirdy.one/2021/03/10/search-engines-with-own-indexe… | ok | 147,960 | ok | 15,178 | — |
| 19 | ACADEMIC | https://arxiv.org/abs/2410.19771 | plugin_routed | 0 | plugin_routed | 237 | plugin_routed |
| 20 | ACADEMIC | https://doi.org/10.32388/9a17f4 | ok | 24,419 | ok | 15,256 | — |

---
## Per-URL Details

### URL 1: https://github.com/adbar/trafilatura/issues/25

**Full URL:** https://github.com/adbar/trafilatura/issues/25  
**Class:** GENERAL | Position: 1  

**Mode 1 (raw):**  
- Status: `plugin_routed`  
- Bytes: 0  
- First content lines: `_(none)_`  

**Mode 2 (filtered):**  
- Status: `plugin_routed`  
- Bytes: 303  
- Garbage type: `plugin_routed`  
- Preview: PLUGIN_ROUTE_REQUIRED: Cannot scrape github.com — scraping returns broken HTML, not content.
Use instead: GitHub Research plugin — use mcp__plugin_github-research_github__get_file_content(owner, repo,  

### URL 2: https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-

**Full URL:** https://chuniversiteit.nl/papers/comparison-of-web-content-extraction-algorithms  
**Class:** GENERAL | Position: 2  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 14,185  
- First content lines: `[![Chuniversiteit logomark](https://chuniversiteit.nl/images/static/logomark.png)![Chuniversiteit.nl](https://chuniversi`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 7,507  
- Garbage type: `—`  
- Preview: The World Wide Web contains a wealth of information in the form of HTML web pages. Extracting information from web pages using scraping tools is not an easy task. While HTML web pages are technically  

### URL 3: https://downloads.webis.de/publications/slides/bevendorff_2023b.pdf

**Full URL:** https://downloads.webis.de/publications/slides/bevendorff_2023b.pdf  
**Class:** GENERAL | Position: 3  

**Mode 1 (raw):**  
- Status: `no_content`  
- Bytes: 0  
- First content lines: `_(none)_`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 87  
- Garbage type: `—`  
- Preview:   

### URL 4: https://trafilatura.readthedocs.io/en/latest/evaluation.html

**Full URL:** https://trafilatura.readthedocs.io/en/latest/evaluation.html  
**Class:** GENERAL | Position: 4  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 19,447  
- First content lines: `[Skip to main content](https://trafilatura.readthedocs.io/en/latest/evaluation.html#main-content) | Back to top `⌘`+`K` `  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 15,122  
- Garbage type: `—`  
- Preview: [Skip to main content](https://trafilatura.readthedocs.io/en/latest/evaluation.html#main-content)
Back to top
Light Dark System Settings
  * [ GitHub](https://github.com/adbar/trafilatura)


[**Enterp  

### URL 5: https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/

**Full URL:** https://www.contextractor.com/trafilatura-vs-readability-vs-newspaper/  
**Class:** GENERAL | Position: 5  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 19,500  
- First content lines: `[![Contextractor](https://www.contextractor.com/_next/static/media/logo.941c533e.svg)](https://www.contextractor.com/) |`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 15,177  
- Garbage type: `—`  
- Preview: # Trafilatura vs. Readability vs. Newspaper4k — which extracts better in 2026?
If you need to pull clean article text out of a web page using Python, you've got three realistic choices: , **readabilit  

### URL 6: https://www.libhunt.com/r/trafilatura

**Full URL:** https://www.libhunt.com/r/trafilatura  
**Class:** GENERAL | Position: 6  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 25,168  
- First content lines: `[ ![LibHunt logo](https://cdn-b.libhunt.com/assets/logo/logo-square-59c7e305a0cf44062d1ee926560b6384cfb5b175590450cf104d`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 11,531  
- Garbage type: `—`  
- Preview: ##  trafilatura 
Python & Command-line tool to gather text and metadata on the Web: Crawling, scraping, extraction, output as CSV, JSON, HTML, MD, TXT, XML (by adbar) 
[Web Content Extracting](https:/  

### URL 7: https://webscraping.fyi/lib/compare/python-readability-vs-python-trafi

**Full URL:** https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/  
**Class:** GENERAL | Position: 7  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 14,450  
- First content lines: `[ Skip to content ](https://webscraping.fyi/lib/compare/python-readability-vs-python-trafilatura/#readabilityvstrafilatu`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 3,277  
- Garbage type: `—`  
- Preview: #  [readability](https://webscraping.fyi/lib/python/readability/)vs[trafilatura](https://webscraping.fyi/lib/python/trafilatura/)
[python](https://webscraping.fyi/lib/language/python) [scraper](https:  

### URL 8: https://www.libhunt.com/r/htmldate

**Full URL:** https://www.libhunt.com/r/htmldate  
**Class:** GENERAL | Position: 8  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 19,933  
- First content lines: `[ ![LibHunt logo](https://cdn-b.libhunt.com/assets/logo/logo-square-59c7e305a0cf44062d1ee926560b6384cfb5b175590450cf104d`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 6,471  
- Garbage type: `—`  
- Preview: ##  htmldate 
Fast and robust date extraction from web pages, with Python or on the command-line (by adbar) 
[Web Content Extracting](https://www.libhunt.com/l/python/topic/web-content-extracting) [me  

### URL 9: https://justtothepoint.com/code/scrape/

**Full URL:** https://justtothepoint.com/code/scrape/  
**Class:** GENERAL | Position: 9  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 16,934  
- First content lines: `|  [ ![JustToThePoint](https://justtothepoint.com/myImages/logotipoMagotipoCabecera.png) ](https://justtothepoint.com/in`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 14,442  
- Garbage type: `—`  
- Preview: # Scraping Web Page Content with Python: Trafilatura, Readability, Newspaper3k & Playwright
> Behind this mask there is more than just flesh. Beneath this mask there is an idea… and ideas are bulletpr  

### URL 10: https://news.ycombinator.com/item?id=44067409

**Full URL:** https://news.ycombinator.com/item?id=44067409  
**Class:** GENERAL | Position: 10  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 51,079  
- First content lines: `|    |  | [![](https://news.ycombinator.com/y18.svg)](https://news.ycombinator.com)  | **[Hacker News](https://news.ycom`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 15,114  
- Garbage type: `—`  
- Preview: |   
 | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomment  

### URL 11: https://adrien.barbaresi.eu/blog/tag/data-mining.html

**Full URL:** https://adrien.barbaresi.eu/blog/tag/data-mining.html  
**Class:** GENERAL | Position: 11  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 10,915  
- First content lines: `Toggle navigation [ Bits of Language: corpus linguistics, NLP and text analytics ](https://adrien.barbaresi.eu/blog/) | `  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 8,074  
- Garbage type: `—`  
- Preview: Toggle navigation [ Bits of Language: corpus linguistics, NLP and text analytics ](https://adrien.barbaresi.eu/blog/)


## [An easy way to save time and resources: content-aware URL filtering](https:/  

### URL 12: https://news.ycombinator.com/item?id=40035347

**Full URL:** https://news.ycombinator.com/item?id=40035347  
**Class:** GENERAL | Position: 12  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 9,408  
- First content lines: `|    |  | [![](https://news.ycombinator.com/y18.svg)](https://news.ycombinator.com)  | **[Hacker News](https://news.ycom`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 5,663  
- Garbage type: `—`  
- Preview: |   
 | **[Hacker News](https://news.ycombinator.com/news)**[new](https://news.ycombinator.com/newest) | [past](https://news.ycombinator.com/front) | [comments](https://news.ycombinator.com/newcomment  

### URL 13: https://doi.org/10.18653/v1/2023.semeval-1.317

**Full URL:** https://doi.org/10.18653/v1/2023.semeval-1.317  
**Class:** ACADEMIC | Position: 13  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 17,750  
- First content lines: `[![ACL Logo](https://aclanthology.org/images/acl-logo.svg) ACL Anthology ](https://aclanthology.org/) |   * [News(curren`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 14,578  
- Garbage type: `—`  
- Preview: ## [SemEval-2023 Task 3: Detecting the Category, the Framing, and the Persuasion Techniques in Online News in a Multi-lingual Setup](https://aclanthology.org/2023.semeval-1.317.pdf)
[Jakub Piskorski](  

### URL 14: https://searchstudies.org/wp-content/uploads/2025/02/Thesis_Template_U

**Full URL:** https://searchstudies.org/wp-content/uploads/2025/02/Thesis_Template_UDE__1_.pdf  
**Class:** ACADEMIC | Position: 14  

**Mode 1 (raw):**  
- Status: `no_content`  
- Bytes: 0  
- First content lines: `_(none)_`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 100  
- Garbage type: `—`  
- Preview:   

### URL 15: https://doi.org/10.1145/1526709.1526911

**Full URL:** https://doi.org/10.1145/1526709.1526911  
**Class:** ACADEMIC | Position: 15  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 27,756  
- First content lines: `[skip to main content](https://dl.acm.org/doi/10.1145/1526709.1526911#skip-to-main-content) | ## ACM is now Open Access `  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 11,413  
- Garbage type: `—`  
- Preview: [skip to main content](https://dl.acm.org/doi/10.1145/1526709.1526911#skip-to-main-content)
## ACM is now Open Access
As part of the Digital Library's transition to [Open Access](https://dl.acm.org/ac  

### URL 16: https://doi.org/10.18653/v1/2023.acl-long.169

**Full URL:** https://doi.org/10.18653/v1/2023.acl-long.169  
**Class:** ACADEMIC | Position: 16  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 16,035  
- First content lines: `[![ACL Logo](https://aclanthology.org/images/acl-logo.svg) ACL Anthology ](https://aclanthology.org/) |   * [News(curren`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 12,841  
- Garbage type: `—`  
- Preview: ## [Multilingual Multifaceted Understanding of Online News in Terms of Genre, Framing, and Persuasion Techniques](https://aclanthology.org/2023.acl-long.169.pdf)
[Jakub Piskorski](https://aclanthology  

### URL 17: https://seirdy.one/posts/2020/11/23/website-best-practices/

**Full URL:** https://seirdy.one/posts/2020/11/23/website-best-practices/  
**Class:** QA | Position: 17  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 228,672  
- First content lines: `[Skip to content](https://seirdy.one/posts/2020/11/23/website-best-practices/#h1) |   * [ Seirdy’s Home ](https://seirdy`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 13,936  
- Garbage type: `—`  
- Preview: ## Before you begin
The following applies to minimal websites that focus primarily on text. It does not apply to websites that have a lot of non-textual content. It also does not apply to websites tha  

### URL 18: https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html

**Full URL:** https://seirdy.one/2021/03/10/search-engines-with-own-indexes.html  
**Class:** QA | Position: 18  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 147,960  
- First content lines: `[Skip to content](https://seirdy.one/posts/2021/03/10/search-engines-with-own-indexes/#h1) |   * [ Seirdy’s Home ](https`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 15,178  
- Garbage type: `—`  
- Preview: ## Preface
This is a cursory review of all the indexing search engines I have been able to find.
The three dominant English search engines with their own indexes are Google, Bing, and Yandex (GBY). Ma  

### URL 19: https://arxiv.org/abs/2410.19771

**Full URL:** https://arxiv.org/abs/2410.19771  
**Class:** ACADEMIC | Position: 19  

**Mode 1 (raw):**  
- Status: `plugin_routed`  
- Bytes: 0  
- First content lines: `_(none)_`  

**Mode 2 (filtered):**  
- Status: `plugin_routed`  
- Bytes: 237  
- Garbage type: `plugin_routed`  
- Preview: PLUGIN_ROUTE_REQUIRED: Cannot scrape arxiv.org — scraping returns broken HTML, not content.
Use instead: RAG plugin — use mcp__rag__search_hybrid or /rag:pdf-convert to index the paper
URL attempted:   

### URL 20: https://doi.org/10.32388/9a17f4

**Full URL:** https://doi.org/10.32388/9a17f4  
**Class:** ACADEMIC | Position: 20  

**Mode 1 (raw):**  
- Status: `ok`  
- Bytes: 24,419  
- First content lines: `[![Qeios](https://www.qeios.com/images/brand/Qeios.svg) ![Qeios](https://www.qeios.com/images/brand/Q.svg)](https://www.`  

**Mode 2 (filtered):**  
- Status: `ok`  
- Bytes: 15,256  
- Garbage type: `—`  
- Preview: Cite
### Field
Computer Science
### Subfield
Artificial Intelligence
### Open Peer Review
Preprint
**0** peer reviewers 
Review this Article Review it
Research Article Apr 11, 2025
CC BY
<https://doi.  
---
## Aggregate

**Mode 1 (raw) success:** 16/20  
**Mode 2 (filtered) success:** 18/20  

**Mode 2 failure breakdown:**  

- `plugin_routed`: 2  

**Mode 1 byte-size distribution (successes only):**  
- Min: 9,408  
- Median: 19,474  
- Max: 228,672  