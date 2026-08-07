# raw:// urlsplit crash fixed by switching to raw: — 2026-08-06

## Context

Prior entries in this area documented crawl4ai's
`raw://<html>` pseudo-URL crashing on HTML containing a bare `[` before the first `/` (e.g. an early
inline `<script>` with a JS array literal) as an observed-but-unfixed crawl4ai robustness bug, present
at both `camoufox_scrape.py`'s `_html_to_markdown` and `pipe_scraper.py`'s `_own_fallback_rescue`. This
session closed it.

## Root cause, isolated

`crawler.arun(url=f"raw://{html}", ...)` fails because crawl4ai internally calls
`urllib.parse.urlsplit()` on the pseudo-URL, and Python 3.14's `_check_bracketed_netloc` rejects a
`[` before the first `/` as an invalid IPv6-literal netloc — raised as `ValueError: Invalid IPv6 URL`.
crawl4ai's own `_crawl_web` wrapper swallows this internally and returns `success=False`/`markdown=None`
rather than propagating, so the caller sees an empty conversion with no exception, only the
`error_message` field naming it.

Isolated directly: `urlsplit("raw://" + html)` raises on the trigger HTML; `urlsplit("raw:" + html)`
does not. The `//` is what makes `urlsplit` expect a netloc at all — `raw:` has none, so no netloc
parsing (bracketed or otherwise) is ever attempted.

## Real-page measurement (2026-08-06, crawl4ai 0.9.2, Python 3.14)

Same captured idealo.de product HTML, same `CrawlerRunConfig` (`DefaultMarkdownGenerator`, no content
filter), only the pseudo-URL prefix varied:

| prefix   | success | raw_markdown bytes | error              |
|----------|---------|---------------------|---------------------|
| `raw://` | False   | 0                   | `Invalid IPv6 URL`  |
| `raw:`   | True    | 106342              | none                |

Without the fix, production returned ~950 KB of raw captured HTML on this page (the fail-soft
`content_is_raw_html=True` path) instead of ~106 KB of markdown.

## Why `raw:` is safe to use — not a crawl4ai patch, not a workaround

crawl4ai treats `raw:` and `raw://` as equivalent, documented forms of the same pseudo-URL contract:
`async_webcrawler.py`'s `_is_raw_url = url.startswith("raw:") or url.startswith("raw://")`,
`async_crawler_strategy.py`'s raw-html branch checks both forms identically, and upstream ships its own
`tests/test_raw_html_browser.py::test_raw_prefix_variations` asserting both work. Switching the prefix
at both call sites is therefore a same-contract substitution, not a workaround around unsupported
behavior.

## Fix

`camoufox_scrape.py::_html_to_markdown` and `pipe_scraper.py::_own_fallback_rescue` both changed
`crawler.arun(url=f"raw://{html}", ...)` to `crawler.arun(url=f"raw:{html}", ...)`. No other behavior
changed: `markdown_conversion_error`/`content_is_raw_html` stay as fields and keep firing for any OTHER
crawl4ai conversion failure — only this one urlsplit trigger is closed.

## Verification

Regression tests in `tests/test_camoufox_scrape.py`
(`test_html_to_markdown_survives_bracket_before_first_slash`) and `tests/test_pipe_scraper.py`
(`test_own_fallback_rescue_survives_bracket_before_first_slash`) feed HTML with a JS array literal
before the first `/` through a fake `AsyncWebCrawler.arun` that performs the REAL
`urllib.parse.urlsplit(url)` call crawl4ai makes internally — the actual failure point, not a mocked
outcome — and assert no exception and real content returned. Both test files pass in full (61 tests)
after the change; 9 pre-existing failures in `tests/test_proxy_pool.py`/`tests/test_query_logger.py`
(unrelated `src.search.search_web` API drift) were confirmed present before this change too via
`git stash` and left untouched, out of scope.
