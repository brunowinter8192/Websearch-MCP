# INFRASTRUCTURE
import asyncio
import re
from html.parser import HTMLParser
from html import unescape
from playwright.async_api import async_playwright, Browser

DEFAULT_CONCURRENCY = 5
TIMEOUT_MS = 30000
MAX_CONTENT_LENGTH = 15000

SKIP_TAGS = {'nav', 'footer', 'header', 'aside', 'script', 'style', 'noscript', 'iframe', 'svg'}
CONTENT_TAGS = {'main', 'article', 'section', 'div', 'body'}
INLINE_TAGS = {'a', 'strong', 'b', 'em', 'i', 'code', 'span', 'img'}
BLOCK_TAGS = {'p', 'div', 'section', 'article', 'main', 'blockquote'}
HEADING_TAGS = {'h1': '# ', 'h2': '## ', 'h3': '### ', 'h4': '#### ', 'h5': '##### ', 'h6': '###### '}
LIST_TAGS = {'ul', 'ol'}


# ORCHESTRATOR
async def scrape_urls_workflow(urls: list[str], concurrency: int = DEFAULT_CONCURRENCY) -> list[dict]:
    browser = await init_browser()
    semaphore = create_concurrency_semaphore(concurrency)
    tasks = create_scrape_tasks(urls, browser, semaphore)
    raw_results = await gather_results(tasks)
    await cleanup_browser(browser)
    extracted_results = extract_all_content(raw_results)
    return format_results(urls, extracted_results)


# FUNCTIONS

# Initialize headless Chromium browser instance
async def init_browser() -> Browser:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    return browser


# Create semaphore for concurrency control
def create_concurrency_semaphore(concurrency: int) -> asyncio.Semaphore:
    return asyncio.Semaphore(concurrency)


# Create list of scrape tasks for all URLs
def create_scrape_tasks(urls: list[str], browser: Browser, semaphore: asyncio.Semaphore) -> list:
    return [scrape_single_url(url, browser, semaphore) for url in urls]


# Execute all tasks and gather results
async def gather_results(tasks: list) -> list:
    return await asyncio.gather(*tasks, return_exceptions=True)


# Scrape single URL with semaphore-controlled concurrency
async def scrape_single_url(url: str, browser: Browser, semaphore: asyncio.Semaphore) -> str:
    async with semaphore:
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        content = await page.content()
        await context.close()
        return content


# Release browser resources
async def cleanup_browser(browser: Browser) -> None:
    await browser.close()


# Extract content from all raw HTML results
def extract_all_content(raw_results: list) -> list:
    extracted = []
    for result in raw_results:
        if isinstance(result, Exception):
            extracted.append(result)
        else:
            extracted.append(extract_single_content(result))
    return extracted


# Parse and convert single HTML to markdown
def extract_single_content(html: str) -> str:
    parsed = parse_html(html)
    filtered = filter_content(parsed)
    markdown = to_markdown(filtered)
    return markdown


# Transform raw results into structured output
def format_results(urls: list[str], results: list) -> list[dict]:
    formatted = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            formatted.append({
                "url": url,
                "content": "",
                "success": False,
                "error": str(result)
            })
        else:
            formatted.append({
                "url": url,
                "content": result,
                "success": True,
                "error": None
            })
    return formatted


# Parse HTML into structured representation
def parse_html(html: str) -> dict:
    parser = HTMLContentParser()
    parser.feed(html)
    return parser.get_result()


# Filter parsed content to extract main content
def filter_content(parsed: dict) -> list:
    nodes = parsed.get("nodes", [])
    filtered = remove_skip_tags(nodes)
    main_content = extract_main_content(filtered)
    return main_content


# Convert filtered nodes to markdown string
def to_markdown(nodes: list) -> str:
    raw_markdown = convert_nodes_to_markdown(nodes)
    cleaned = clean_whitespace(raw_markdown)
    truncated = truncate_content(cleaned, MAX_CONTENT_LENGTH)
    return truncated


# HTMLParser subclass that builds structured representation
class HTMLContentParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.result = []
        self.tag_stack = []
        self.current_attrs = {}

    # Handle opening tags
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        self.current_attrs[tag] = dict(attrs)
        self.result.append({
            "type": "start",
            "tag": tag,
            "attrs": dict(attrs)
        })

    # Handle closing tags
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        self.result.append({
            "type": "end",
            "tag": tag
        })

    # Handle text content between tags
    def handle_data(self, data):
        text = unescape(data.strip())
        if text:
            self.result.append({
                "type": "text",
                "content": text,
                "parent_tags": list(self.tag_stack)
            })

    # Handle self-closing tags
    def handle_startendtag(self, tag, attrs):
        self.result.append({
            "type": "self_closing",
            "tag": tag,
            "attrs": dict(attrs)
        })

    # Return parsed structure
    def get_result(self) -> dict:
        return {
            "nodes": self.result,
            "tag_stack": self.tag_stack
        }


# Remove nodes that belong to skip tags
def remove_skip_tags(nodes: list) -> list:
    result = []
    skip_depth = 0
    current_skip_tag = None

    for node in nodes:
        if node["type"] == "start" and node["tag"] in SKIP_TAGS:
            if skip_depth == 0:
                current_skip_tag = node["tag"]
            skip_depth += 1
            continue

        if node["type"] == "end" and skip_depth > 0:
            if node["tag"] == current_skip_tag:
                skip_depth -= 1
                if skip_depth == 0:
                    current_skip_tag = None
            continue

        if skip_depth == 0:
            result.append(node)

    return result


# Extract content from main/article tags or return all
def extract_main_content(nodes: list) -> list:
    main_start = find_content_tag_start(nodes)
    if main_start == -1:
        return nodes

    main_end = find_matching_end(nodes, main_start)
    if main_end == -1:
        return nodes

    return nodes[main_start:main_end + 1]


# Find index of first content tag
def find_content_tag_start(nodes: list) -> int:
    for priority_tag in ['main', 'article']:
        for i, node in enumerate(nodes):
            if node["type"] == "start" and node["tag"] == priority_tag:
                return i
    return -1


# Find matching end tag index
def find_matching_end(nodes: list, start_idx: int) -> int:
    if start_idx == -1:
        return -1

    tag = nodes[start_idx]["tag"]
    depth = 1

    for i in range(start_idx + 1, len(nodes)):
        node = nodes[i]
        if node["type"] == "start" and node["tag"] == tag:
            depth += 1
        elif node["type"] == "end" and node["tag"] == tag:
            depth -= 1
            if depth == 0:
                return i

    return -1


# Convert parsed nodes to markdown string
def convert_nodes_to_markdown(nodes: list) -> str:
    result = []
    list_stack = []
    link_href = None

    for node in nodes:
        if node["type"] == "start":
            tag = node["tag"]
            attrs = node.get("attrs", {})

            if tag in HEADING_TAGS:
                result.append("\n\n" + HEADING_TAGS[tag])
            elif tag == "p":
                result.append("\n\n")
            elif tag == "br":
                result.append("\n")
            elif tag == "strong" or tag == "b":
                result.append("**")
            elif tag == "em" or tag == "i":
                result.append("*")
            elif tag == "code":
                result.append("`")
            elif tag == "pre":
                result.append("\n\n```\n")
            elif tag == "a":
                link_href = attrs.get("href", "")
                result.append("[")
            elif tag == "img":
                alt = attrs.get("alt", "image")
                src = attrs.get("src", "")
                result.append(f"![{alt}]({src})")
            elif tag == "ul":
                list_stack.append("ul")
                result.append("\n")
            elif tag == "ol":
                list_stack.append("ol")
                result.append("\n")
            elif tag == "li":
                indent = "  " * (len(list_stack) - 1)
                if list_stack and list_stack[-1] == "ol":
                    result.append(f"{indent}1. ")
                else:
                    result.append(f"{indent}- ")
            elif tag == "blockquote":
                result.append("\n\n> ")
            elif tag in BLOCK_TAGS:
                result.append("\n\n")

        elif node["type"] == "end":
            tag = node["tag"]

            if tag in HEADING_TAGS:
                result.append("\n")
            elif tag == "strong" or tag == "b":
                result.append("**")
            elif tag == "em" or tag == "i":
                result.append("*")
            elif tag == "code":
                result.append("`")
            elif tag == "pre":
                result.append("\n```\n\n")
            elif tag == "a":
                result.append(f"]({link_href})")
                link_href = None
            elif tag == "li":
                result.append("\n")
            elif tag == "ul" or tag == "ol":
                if list_stack:
                    list_stack.pop()
                result.append("\n")
            elif tag in BLOCK_TAGS:
                result.append("\n")

        elif node["type"] == "text":
            result.append(node["content"])

        elif node["type"] == "self_closing":
            tag = node["tag"]
            attrs = node.get("attrs", {})

            if tag == "br":
                result.append("\n")
            elif tag == "img":
                alt = attrs.get("alt", "image")
                src = attrs.get("src", "")
                result.append(f"![{alt}]({src})")
            elif tag == "hr":
                result.append("\n\n---\n\n")

    return "".join(result)


# Remove excessive whitespace
def clean_whitespace(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)
    text = text.strip()
    return text


# Truncate content if too long
def truncate_content(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n\n')
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[Content truncated...]"
