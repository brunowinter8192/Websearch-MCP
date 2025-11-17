# Scraper Module

Web search and URL scraping tools for SearXNG MCP server.

## search_web.py

**Purpose:** Wrapper for SearXNG JSON API.
**Input:** Query string and category name.
**Output:** Dictionary containing query, category, and list of result objects.

### search_web_workflow()

Main orchestrator function. Coordinates fetching raw results from SearXNG API and formatting them into clean output structure. Called directly by server.py tool definition.

### fetch_search_results()

Performs HTTP GET request to SearXNG search endpoint. Constructs query parameters including format=json and category filter. Raises exception on HTTP errors. Extracts results array from response and limits to MAX_RESULTS (20).

### format_results()

Transforms raw SearXNG response into standardized output. Iterates over raw results and extracts title, url, and content fields. Returns dictionary with query metadata and cleaned results list.

## scrape_urls.py

**Purpose:** URL scraper with JavaScript rendering and HTML to markdown conversion.
**Input:** List of URLs and concurrency limit.
**Output:** List of dictionaries containing url, markdown content, success status, and error.

### scrape_urls_workflow()

Main orchestrator function. Coordinates browser initialization, concurrent URL scraping, content extraction, and result formatting. Manages browser lifecycle and ensures cleanup. Called directly by server.py tool definition.

### init_browser()

Initializes headless Chromium browser instance using Playwright. Returns browser object for reuse across multiple page scrapes.

### create_concurrency_semaphore()

Creates asyncio semaphore to control maximum parallel requests. Prevents overwhelming target servers with too many concurrent connections.

### create_scrape_tasks()

Creates list of coroutine tasks for all URLs. Each task represents a single URL scrape operation with shared browser and semaphore.

### gather_results()

Executes all scrape tasks concurrently using asyncio.gather. Returns exceptions as results rather than raising them to handle partial failures gracefully.

### scrape_single_url()

Scrapes single URL with semaphore-controlled concurrency. Creates isolated browser context, navigates to URL with timeout, extracts page HTML content, and closes context. Returns raw HTML string.

### cleanup_browser()

Releases browser resources by closing the browser instance. Ensures proper cleanup even on errors.

### extract_all_content()

Processes all raw HTML results. Preserves exceptions from failed scrapes. Converts successful HTML results to markdown using extract_single_content.

### extract_single_content()

Converts single HTML string to markdown. Orchestrates parsing, filtering, and markdown conversion pipeline.

### format_results()

Transforms raw results into structured output. Pairs URLs with their results. Handles both successful markdown content and error cases with appropriate status flags.

### parse_html()

Parses HTML string into structured representation using HTMLContentParser. Returns dictionary with nodes array and tag stack state.

### filter_content()

Filters parsed content to extract main content. Removes navigation, footer, script, and other non-content elements. Extracts content from main or article tags when present.

### to_markdown()

Converts filtered nodes to markdown string. Orchestrates node conversion, whitespace cleaning, and content truncation.

### HTMLContentParser

Custom HTMLParser subclass that builds structured representation of HTML document. Tracks tag hierarchy and extracts text content with parent tag context. Handles opening tags, closing tags, text data, and self-closing tags.

### remove_skip_tags()

Removes all nodes belonging to skip tags like nav, footer, header, script, style. Tracks nesting depth to handle nested skip tags correctly.

### extract_main_content()

Extracts content from main or article tags when present. Returns all nodes if no main content container found. Prioritizes main tag over article tag.

### find_content_tag_start()

Finds index of first content tag (main or article) in nodes list. Returns -1 if not found.

### find_matching_end()

Finds index of matching end tag for given start tag. Tracks nesting depth to handle nested same-name tags correctly.

### convert_nodes_to_markdown()

Converts parsed nodes to markdown string. Handles headings, paragraphs, lists, links, images, code blocks, blockquotes, and inline formatting. Maintains list stack for proper nesting and link href for anchor tags.

### clean_whitespace()

Removes excessive whitespace from markdown text. Collapses multiple newlines, removes multiple spaces, and trims leading/trailing whitespace.

### truncate_content()

Truncates content if exceeding maximum length. Attempts to break at paragraph boundary for clean truncation. Appends truncation notice when content is cut.
