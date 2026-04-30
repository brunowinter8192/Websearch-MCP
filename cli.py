#!/usr/bin/env python3
import os
import sys

# Ensure src.* imports resolve regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import asyncio
import atexit

from src.routing import check_plugin_routed
from src.search.search_web import search_web_workflow
from src.search.browser import close_browser
from src.scraper.scrape_url import scrape_url_workflow
from src.scraper.scrape_url_raw import scrape_url_raw_workflow
from src.scraper.explore_site import explore_site_workflow
from src.scraper.download_pdf import download_pdf_workflow

atexit.register(lambda: asyncio.run(close_browser()))


def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="SearXNG Web Research CLI — search, scrape, explore, download PDF."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── search_web ────────────────────────────────────────────────────────────
    p = sub.add_parser("search_web", help="Search the web across 4 engines (Google, Bing, Scholar, CrossRef).")
    p.add_argument("query", help="Search query (2-5 keywords)")
    p.add_argument("--category", choices=["general", "news", "it", "science"], default="general")
    p.add_argument("--language", default="en", help="ISO language code (e.g. 'de')")
    p.add_argument("--time-range", dest="time_range", choices=["day", "month", "year"], default=None)
    p.add_argument("--engines", default=None,
                   help="Comma-separated engine list (e.g. 'google,bing' or 'google scholar,crossref')")
    p.add_argument("--pages", type=int, default=3,
                   help="Result pages to fetch and combine (default 3 = ~150 results)")

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
            args.query, args.category, args.language,
            args.time_range, args.engines, args.pages
        ))

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
