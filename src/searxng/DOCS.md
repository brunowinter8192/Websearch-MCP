# SearXNG Search

SearXNG API wrapper and configuration for web search functionality.

## search_web.py

**Purpose:** Wrapper for SearXNG JSON API.
**Input:** Query string and category name.
**Output:** Plain text string with numbered list of search results.

### search_web_workflow()

Main orchestrator function. Coordinates fetching raw results from SearXNG API and formatting them into plain text output. Called directly by server.py tool definition.

### fetch_search_results()

Performs HTTP GET request to SearXNG search endpoint. Constructs query parameters including format=json and category filter. Raises exception on HTTP errors. Extracts results array from response and limits to MAX_RESULTS (20).

### format_results()

Transforms raw SearXNG response into plain text numbered list. Takes query string and raw results list. Iterates over results and extracts title, url, and content snippet (first 200 chars). Returns formatted string with result count header and numbered entries.

## settings.yml

**Purpose:** SearXNG instance configuration for local MCP server usage.

Enables JSON output format required for API access. Uses default settings as base. Sets static secret key for local development. Disables rate limiter to avoid throttling during development. Disables image proxy for simpler setup.

Search configuration sets safe search to off, disables autocomplete, and defaults to English language. Enables both HTML and JSON response formats where JSON is critical for programmatic access.

UI configuration uses simple theme with static hash for caching. Enables query in page title. Disables infinite scroll and opening results in new tab for cleaner response handling.

Outgoing request configuration sets default timeout to 3 seconds with maximum of 10 seconds. Controls how long SearXNG waits for upstream search engines to respond.
