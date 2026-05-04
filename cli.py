#!/usr/bin/env python3
import os
import sys

# Ensure src.* imports resolve regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import asyncio
import atexit

from src.routing import check_plugin_routed
from src.search.search_web import search_web_workflow, search_batch_workflow
from src.search.browser import close_browser, kill_stale_chrome
from src.search.cache import cache_key, cache_read, format_cached_slice
from src.scraper.scrape_url import scrape_url_workflow
from src.scraper.scrape_url_raw import scrape_url_raw_workflow
from src.scraper.explore_site import explore_site_workflow
from src.scraper.download_pdf import download_pdf_workflow
from mcp.types import TextContent

atexit.register(kill_stale_chrome)


def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="SearXNG Web Research CLI — search, scrape, explore, download PDF."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── search_web ────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "search_web",
        help="Search the web across 8 engines (Google, DDG, Mojeek, Lobsters, Scholar, CrossRef, OpenAlex, StackExchange)."
    )
    p.add_argument("query", help="Search query (2-5 keywords)")
    p.add_argument("--language", default="en", help="ISO language code (e.g. 'de')")
    p.add_argument("--time-range", dest="time_range", choices=["day", "month", "year"], default=None)
    p.add_argument("--engines", default=None,
                   help="Comma-separated engine list (e.g. 'google,duckduckgo' or 'google scholar,crossref')")

    # ── search_batch ──────────────────────────────────────────────────────────
    p = sub.add_parser(
        "search_batch",
        help="Search multiple queries in one warm-Chrome session."
    )
    p.add_argument("queries", nargs="+", help="One or more search queries")
    p.add_argument("--language", default="en", help="ISO language code (e.g. 'de')")
    p.add_argument("--time-range", dest="time_range", choices=["day", "month", "year"], default=None)
    p.add_argument("--engines", default=None,
                   help="Comma-separated engine list (e.g. 'google,duckduckgo')")

    # ── search_more ───────────────────────────────────────────────────────────
    p = sub.add_parser(
        "search_more",
        help="Get next batch of URLs from cached search results (must follow a search_web call with the same query)."
    )
    p.add_argument("query", help="Search query (must match prior search_web call).")
    p.add_argument("--count", type=int, default=10, help="How many additional URLs to return (default 10).")
    p.add_argument("--language", default="en")
    p.add_argument("--engines", default=None)
    p.add_argument("--time-range", dest="time_range", choices=["day", "month", "year"], default=None)

    # ── scrape_url ────────────────────────────────────────────────────────────
    p = sub.add_parser("scrape_url", help="Scrape URL to filtered markdown (PruningContentFilter).")
    p.add_argument("url", help="URL to scrape")
    p.add_argument("--max-content-length", dest="max_content_length", type=int, default=15000)

    # ── scrape_url_raw ────────────────────────────────────────────────────────
    p = sub.add_parser("scrape_url_raw", help="Scrape URL to raw markdown file (for RAG indexing).")
    p.add_argument("url", help="URL to scrape")
    p.add_argument("output_dir", help="Directory to save the .md file (created if not exists)")

    # ── explore_site ──────────────────────────────────────────────────────────
    p = sub.add_parser("explore_site", help="Explore website structure via sitemap + BFS.")
    p.add_argument("url", help="Root URL to explore")
    p.add_argument("--max-pages", dest="max_pages", type=int, default=200)
    p.add_argument("--url-pattern", dest="url_pattern", default=None,
                   help="Regex pattern to filter discovered URLs")

    # ── download_pdf ──────────────────────────────────────────────────────────
    p = sub.add_parser("download_pdf", help="Download PDF file from URL.")
    p.add_argument("url", help="URL of the PDF to download")
    p.add_argument("--output-dir", dest="output_dir", default="/tmp",
                   help="Directory to save the PDF (default: /tmp)")

    # ── Dispatch ──────────────────────────────────────────────────────────────
    args = parser.parse_args()

    if args.cmd == "search_web":
        result = asyncio.run(search_web_workflow(
            args.query, args.language, args.time_range, args.engines
        ))

    elif args.cmd == "search_batch":
        results = asyncio.run(search_batch_workflow(
            args.queries, args.language, args.time_range, args.engines
        ))
        print("\n---\n".join(r[0].text for r in results))
        return

    elif args.cmd == "search_more":
        key = cache_key(args.query, args.language, args.engines, args.time_range)
        hit = cache_read(key)
        if hit is not None:
            urls = hit.get("urls", [])
            sliced = urls[20: 20 + args.count]
            if not sliced:
                print("# search_more: no further URLs in cached pool")
                return
            header = "# search_more (cached)\n"
            print(header + format_cached_slice(sliced, 20))
            return
        else:
            # Cache miss or expired — run fresh search, cache is written as side effect
            fresh = asyncio.run(search_web_workflow(
                args.query, args.language, args.time_range, args.engines
            ))
            hit2 = cache_read(key)
            if hit2:
                sliced = hit2.get("urls", [])[:args.count]
                header = "# search_more (cache miss — fresh ranking, only first {} shown)\n".format(args.count)
                print(header + format_cached_slice(sliced, 0))
            else:
                # fallback: show what search_web returned
                print("# search_more (cache miss — fresh ranking)\n")
                print(fresh[0].text)
            return

    elif args.cmd == "scrape_url":
        if blocked := check_plugin_routed(args.url):
            result = blocked
        else:
            result = asyncio.run(scrape_url_workflow(args.url, args.max_content_length))

    elif args.cmd == "scrape_url_raw":
        if blocked := check_plugin_routed(args.url):
            result = blocked
        else:
            result = asyncio.run(scrape_url_raw_workflow(args.url, args.output_dir))

    elif args.cmd == "explore_site":
        result = asyncio.run(explore_site_workflow(args.url, args.max_pages, args.url_pattern))

    elif args.cmd == "download_pdf":
        result = download_pdf_workflow(args.url, args.output_dir)

    else:
        parser.error(f"Unknown command: {args.cmd}")

    print(result[0].text)


if __name__ == "__main__":
    main()
