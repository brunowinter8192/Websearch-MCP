# Scraper Module

URL scraping tool with JavaScript rendering for SearXNG MCP server.

## scrape_url.py

**Purpose:** Main orchestrator for single URL scraping with JavaScript rendering. Coordinates HTML parsing, content filtering, and markdown conversion.
**Input:** Single URL string and optional maximum content length.
**Output:** Plain markdown content string wrapped in TextContent, or error message string on failure.

### scrape_url_workflow()

Main orchestrator function. Coordinates browser initialization, URL content fetching, and content extraction. Manages browser lifecycle and ensures cleanup. Returns plain markdown directly in TextContent on success, or error message on failure. Called directly by server.py tool definition. Uses networkidle wait strategy for complete JavaScript rendering.

### extract_single_content()

Converts single HTML string to markdown. Orchestrates parsing (html_parser), filtering (content_filter), and markdown conversion (markdown_converter) pipeline with configurable maximum content length.

### init_browser()

Initializes headless Chromium browser instance using Playwright. Returns browser object for page scraping.

### fetch_url_content()

Fetches HTML content from URL using Playwright with networkidle wait strategy. Creates isolated browser context, navigates to URL with timeout, waits for all network activity to settle before extracting page HTML content, and closes context. Returns raw HTML string or exception on failure.

### cleanup_browser()

Releases browser resources by closing the browser instance. Ensures proper cleanup even on errors.

### truncate_content()

Truncates content if exceeding maximum length. Attempts to break at paragraph boundary for clean truncation. Appends truncation notice when content is cut.

## html_parser.py

**Purpose:** Parses raw HTML into structured node representation with whitespace metadata preservation.
**Input:** HTML string.
**Output:** Dictionary with structured nodes array and tag stack state.

### parse_html()

Main orchestrator. Parses HTML string into structured representation using HTMLContentParser. Returns dictionary with nodes array and tag stack state.

### HTMLContentParser

Custom HTMLParser subclass that builds structured representation of HTML document. Tracks tag hierarchy, extracts text content with parent tag context, and preserves whitespace metadata. Handles pre-block depth tracking to preserve literal whitespace in code blocks. Text nodes inside pre blocks get in_pre flag and preserve all whitespace including standalone newlines. Text nodes outside pre blocks get has_leading_space and has_trailing_space metadata for intelligent spacing in markdown conversion.

## content_filter.py

**Purpose:** Filters parsed HTML nodes to extract main content while removing navigation, scripts, and other non-content elements.
**Input:** Parsed nodes dictionary from html_parser.
**Output:** Filtered list of nodes containing only main content.

### filter_content()

Main orchestrator. Filters parsed content to extract main content. Removes navigation, footer, script, and other non-content elements. Extracts content from main or article tags when present.

### remove_skip_tags()

Removes all nodes belonging to skip tags like aside, script, style, noscript, iframe, svg, nav, footer. Tracks nesting depth to handle nested skip tags correctly.

### remove_navigation_attributes()

Removes navigation elements by analyzing HTML attributes. Filters div, section, aside, ul, ol, li, span, label, button, input, form elements with navigation-related class, id, or role attributes. Uses pattern matching against common navigation identifiers like vector-, mw-portlet, navigation, sidebar, menu.

### extract_main_content()

Extracts content from main, article, or section tags when present. Returns all nodes if no main content container found. Prioritizes main tag, then article tag, then section tags with content-related class or id attributes.

### find_content_tag_start()

Finds index of first content tag with improved priority detection. Searches for main, article, or section tags. For section tags, checks class and id attributes for content-related keywords like content, main, or article.

### find_matching_end()

Finds index of matching end tag for given start tag. Tracks nesting depth to handle nested same-name tags correctly.

## markdown_converter.py

**Purpose:** Converts filtered HTML nodes to clean markdown with proper whitespace boundaries and code block preservation.
**Input:** Filtered nodes list from content_filter and maximum content length.
**Output:** Clean markdown string with normalized whitespace.

### to_markdown()

Main orchestrator. Converts filtered nodes to markdown string with configurable maximum length. Orchestrates node conversion, artifact cleaning, and whitespace normalization. The workflow executes three steps: converts HTML nodes to raw markdown, removes Wikipedia-specific artifacts like citations and broken links, and normalizes whitespace patterns while preserving code blocks.

### convert_nodes_to_markdown()

Converts parsed nodes to markdown string. Handles headings, paragraphs, lists, links, images, code blocks, blockquotes, and inline formatting. Maintains list stack for proper nesting and link href for anchor tags. Uses whitespace boundary detection helpers to insert spaces around bold, italic, code, and link markers when needed. Preserves literal whitespace in pre blocks by checking in_pre flag on text nodes.

### should_add_space_before()

Helper function to check if space should be added before inline tag marker. Examines last text node's has_trailing_space metadata and previous element type to determine if boundary space is needed before bold, italic, code, or link opening markers.

### find_next_node()

Helper function to find next node in list. Returns None if current node is last.

### should_add_space_after()

Helper function to check if space should be added after inline tag marker. Examines next text node's has_leading_space metadata to determine if boundary space is needed after bold, italic, code, or link closing markers.

### clean_markdown_artifacts()

Removes Wikipedia-specific artifacts from markdown output to improve readability and LLM processing quality. Strips citation references in bracket notation, removes inline image tags that disrupt text flow, eliminates empty wiki links, converts Wikipedia relative links to plain text while preserving link text, and decodes URL-encoded characters common in German Wikipedia.

### clean_whitespace()

Normalizes whitespace patterns in markdown text while preserving code blocks. Detects code fence markers and applies different rules inside vs outside code blocks. Outside code blocks collapses multiple consecutive spaces to single space, limits newlines to maximum of two, removes leading and trailing spaces around newlines. Inside code blocks preserves all whitespace literally including indentation.
