# SearXNG Configuration

Configuration files for local SearXNG metasearch engine instance.

## settings.yml

**Purpose:** SearXNG instance configuration for local MCP server usage.

Enables JSON output format required for API access. Uses default settings as base. Sets static secret key for local development. Disables rate limiter to avoid throttling during development. Disables image proxy for simpler setup.

Search configuration sets safe search to off, disables autocomplete, and defaults to English language. Enables both HTML and JSON response formats where JSON is critical for programmatic access.

UI configuration uses simple theme with static hash for caching. Enables query in page title. Disables infinite scroll and opening results in new tab for cleaner response handling.

Outgoing request configuration sets default timeout to 3 seconds with maximum of 10 seconds. Controls how long SearXNG waits for upstream search engines to respond.
