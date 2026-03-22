# INFRASTRUCTURE
import logging
from urllib.parse import urlparse
from mcp.types import TextContent

logger = logging.getLogger(__name__)

PLUGIN_ROUTED_DOMAINS = {
    "github.com": "GitHub Research plugin — use mcp__plugin_github-research_github__get_file_content(owner, repo, path) or get_repo_tree(owner, repo)",
    "raw.githubusercontent.com": "GitHub Research plugin — use mcp__plugin_github-research_github__get_file_content(owner, repo, path)",
    "reddit.com": "Reddit plugin — use mcp__plugin_reddit_reddit__search_posts or search_subreddit",
    "arxiv.org": "RAG plugin — use mcp__rag__search_hybrid or /rag:pdf-convert to index the paper",
    "youtube.com": "not supported — video content cannot be scraped meaningfully",
    "youtu.be": "not supported — video content cannot be scraped meaningfully",
}


# FUNCTIONS

# Return error TextContent if URL belongs to a plugin-routed domain, else None
def check_plugin_routed(url: str) -> list[TextContent] | None:
    try:
        host = urlparse(url).hostname or ""
    except Exception as e:
        logger.warning("Failed to parse URL %s: %s", url, e)
        return None
    host = host.removeprefix("www.")
    for domain, instruction in PLUGIN_ROUTED_DOMAINS.items():
        if host == domain or host.endswith("." + domain):
            return [TextContent(
                type="text",
                text=(
                    f"PLUGIN_ROUTE_REQUIRED: Cannot scrape {domain} — scraping returns broken HTML, not content.\n"
                    f"Use instead: {instruction}\n"
                    f"URL attempted: {url}"
                )
            )]
    return None
