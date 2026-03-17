# SearXNG Search

SearXNG API wrapper and configuration for web search functionality.

## search_web.py

**Purpose:** Wrapper for SearXNG JSON API.
**Input:** Query string, category, language, time_range, engines, pageno.
**Output:** Plain text string with numbered list of search results.

### search_web_workflow()

Main orchestrator function. Coordinates fetching raw results from SearXNG API and formatting them into plain text output. Called directly by server.py tool definition. Accepts all search parameters and passes them through to fetch_search_results.

### fetch_search_results()

Performs HTTP GET request to SearXNG search endpoint. Constructs query parameters: q, format, categories, language, pageno. Conditionally adds time_range and engines when provided. Raises exception on HTTP errors. Extracts results array from response and limits to MAX_RESULTS (50). Snippet length per result is 5000 characters (SNIPPET_LENGTH constant) — effectively no truncation, takes whatever engines deliver.

### format_results()

Transforms raw SearXNG response into plain text numbered list. Takes query string and raw results list. Iterates over results and extracts title, url, and content snippet (up to SNIPPET_LENGTH chars). Returns formatted string with result count header and numbered entries.

## settings.yml

**Purpose:** SearXNG instance configuration for local MCP server usage.

Enables JSON output format required for API access. Uses default settings as base (`use_default_settings: true` merges with defaults by engine name). Sets static secret key for local development. Disables rate limiter to avoid throttling during development. Disables image proxy for simpler setup.

Search configuration sets safe search to off, disables autocomplete, and defaults to English language. Enables both HTML and JSON response formats where JSON is critical for programmatic access. Suspension times are reduced from defaults (e.g., CAPTCHA 600s instead of 86400s) so engines recover faster after temporary blocks.

UI configuration uses simple theme with static hash for caching. Enables query in page title. Disables infinite scroll and opening results in new tab for cleaner response handling.

Outgoing request configuration sets default timeout to 5 seconds with maximum of 15 seconds. A Tor SOCKS5 proxy (socks5h://tor:9150) is configured globally for IP rotation. The `using_tor_proxy: true` flag enables Tor verification checks. `extra_proxy_timeout: 10` adds seconds to account for Tor latency. The Tor proxy runs as a separate Docker container (peterdavehello/tor-socks-proxy).

Two custom categories replace SearXNG defaults: `general` (scrapeable web + science engines) and `plugin` (discovery-only for ArXiv, GitHub, Reddit — content via MCP plugins).

General engines (8 active): Google (w2), Bing (w1), Brave (w2), Startpage (w1), Mojeek (w1, patched), Google Scholar (w2), Semantic Scholar (w2), CrossRef (w1). DDG disabled (CAPTCHA, upstream issue #4824). Plugin engines (3): ArXiv (w2), GitHub (w1), Reddit (w1). Mojeek uses a patched engine file (`src/searxng/patches/mojeek.py`) mounted via Docker volume — fixes bot detection triggered by `arc=us` locale combination.

Engine routing uses a split architecture: Brave and Startpage route through Tor (global proxy), while Google, DuckDuckGo, Bing, and Mojeek connect directly (per-engine `proxies: {}` override). This split exists because these engines actively block Tor exit nodes (HTTP 400/403), but work fine with direct connections. Startpage and Brave tolerate Tor and benefit from IP rotation.

Per-engine proxy override requires BOTH `using_tor_proxy: false` AND `proxies: {}`. Setting only `using_tor_proxy: false` disables the Tor verification check but still routes traffic through the global SOCKS5 proxy. The `proxies` config is inherited from outgoing defaults independently of the tor flag. This is a SearXNG network layer behavior (network.py initialize function).

Weight strategy: weight=2 for high-quality proven engines (Google, Brave, Google Scholar, Semantic Scholar, ArXiv), weight=1 for new/redundant/niche engines (Bing, Startpage, Mojeek, CrossRef, GitHub, Reddit). Startpage reduced from weight=2 to weight=1 because it proxies Google results — having both at weight=2 caused multiplicative over-representation of Google URLs in the scoring algorithm. Qwant and DDG are disabled (Qwant: Access Denied without account; DDG: persistent CAPTCHA, upstream issue #4824). MAX_RESULTS increased from 50 to 80 to accommodate more engines producing unique results.

Hostnames plugin configuration prioritizes high-quality domains (GitHub, StackOverflow, StackExchange, Wikipedia, Python docs, MDN, arXiv) and deprioritizes low-quality sources (Pinterest, Quora, W3Schools). Pinterest results are removed entirely.

## patches/mojeek.py

**Purpose:** Patched Mojeek engine for SearXNG. Fixes bot detection triggered by the `arc=us` locale combination in the default engine. Drop-in replacement for SearXNG's built-in Mojeek engine, mounted via Docker volume at `/usr/local/searxng/searx/engines/mojeek.py`.
**Input:** SearXNG engine request (query parameters from search_web).
**Output:** Parsed search results (title, URL, content snippet) returned to SearXNG result aggregator.
