# SearXNG Search

SearXNG API wrapper and configuration for web search functionality.

## search_web.py

**Purpose:** Wrapper for SearXNG JSON API.
**Input:** Query string, category, language, time_range, engines, pageno.
**Output:** Plain text string with numbered list of search results.

### search_web_workflow()

Main orchestrator function. Coordinates fetching raw results from SearXNG API and formatting them into plain text output. Called directly by server.py tool definition. Accepts all search parameters and passes them through to fetch_search_results.

### fetch_search_results()

Performs HTTP GET request to SearXNG search endpoint. Constructs query parameters: q, format, categories, language, pageno. Conditionally adds time_range and engines when provided. Raises exception on HTTP errors. Extracts results array from response and limits to MAX_RESULTS (20). Snippet length per result is 500 characters (SNIPPET_LENGTH constant).

### format_results()

Transforms raw SearXNG response into plain text numbered list. Takes query string and raw results list. Iterates over results and extracts title, url, and content snippet (first 500 chars). Returns formatted string with result count header and numbered entries.

## settings.yml

**Purpose:** SearXNG instance configuration for local MCP server usage.

Enables JSON output format required for API access. Uses default settings as base (`use_default_settings: true` merges with defaults by engine name). Sets static secret key for local development. Disables rate limiter to avoid throttling during development. Disables image proxy for simpler setup.

Search configuration sets safe search to off, disables autocomplete, and defaults to English language. Enables both HTML and JSON response formats where JSON is critical for programmatic access. Suspension times are reduced from defaults (e.g., CAPTCHA 600s instead of 86400s) so engines recover faster after temporary blocks.

UI configuration uses simple theme with static hash for caching. Enables query in page title. Disables infinite scroll and opening results in new tab for cleaner response handling.

Outgoing request configuration sets default timeout to 5 seconds with maximum of 15 seconds. A Tor SOCKS5 proxy (socks5h://tor:9150) is configured globally for IP rotation. The `using_tor_proxy: true` flag enables Tor verification checks. `extra_proxy_timeout: 10` adds seconds to account for Tor latency. The Tor proxy runs as a separate Docker container (peterdavehello/tor-socks-proxy).

Engine routing uses a split architecture: Brave and Startpage route through Tor (global proxy), while Google and DuckDuckGo connect directly (per-engine `proxies: {}` override). This split exists because Google and DDG actively block Tor exit nodes (HTTP 400/403), but work fine with direct connections. Startpage and Brave tolerate Tor and benefit from IP rotation.

Per-engine proxy override requires BOTH `using_tor_proxy: false` AND `proxies: {}`. Setting only `using_tor_proxy: false` disables the Tor verification check but still routes traffic through the global SOCKS5 proxy. The `proxies` config is inherited from outgoing defaults independently of the tor flag. This is a SearXNG network layer behavior (network.py initialize function).

Engine weights override default weight=1. Google, Brave, and Startpage set to weight=2 for higher result ranking. DuckDuckGo stays at weight=1 as supplementary source. Google Scholar is enabled (disabled by default) with weight=2 for academic/science searches. Qwant is explicitly disabled (Access Denied on both API and web-lite endpoints).

Hostnames plugin configuration prioritizes high-quality domains (GitHub, StackOverflow, StackExchange, Wikipedia, Python docs, MDN, arXiv) and deprioritizes low-quality sources (Pinterest, Quora, W3Schools). Pinterest results are removed entirely.
