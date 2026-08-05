#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Ensure src.* imports resolve regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from logging.handlers import TimedRotatingFileHandler
from src.log_janitor import get_retention_days

# Central logging config — daily-rotating handler, no StreamHandler.
# Placed before src.* imports: module-load-time log calls route to file, not stderr.
# basicConfig with explicit handlers= never installs the default StreamHandler.
_log_path = Path(__file__).parent / "src" / "logs" / "cli.log"
_log_path.parent.mkdir(parents=True, exist_ok=True)
_handler = TimedRotatingFileHandler(
    _log_path, when="midnight", interval=1,
    backupCount=get_retention_days(), encoding="utf-8",
)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[_handler],
)
logger = logging.getLogger(__name__)

import argparse
import asyncio
import atexit

from src.search.search_web import search_web_workflow
from src.search.browser import kill_stale_chrome
from src.search.cache import cache_key, cache_read, format_engine_pool
from urllib.parse import urlparse

from src.scraper.scrape_url import scrape_url_workflow

atexit.register(kill_stale_chrome)


def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="websearch CLI — search_web, search_engine_drilldown, scrape_url."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── search_web ────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "search_web",
        help="Search across 9 engines. Returns engine breakdown table — use search_engine_drilldown to see URLs per engine."
    )
    p.add_argument("query", help="Search query (2-5 keywords)")
    mode_sw = p.add_mutually_exclusive_group()
    mode_sw.add_argument("--books", action="store_true",
                   help="Restrict to book-domain whitelist (+book modifier). Mutually exclusive with --pdf / --docs")
    mode_sw.add_argument("--pdf", action="store_true",
                   help="Restrict to PDF-domain whitelist (+pdf modifier). Mutually exclusive with --books / --docs")
    mode_sw.add_argument("--docs", action="store_true",
                   help="Noise-blacklist filter (+documentation modifier). Mutually exclusive with --books / --pdf")

    # ── search_engine_drilldown ───────────────────────────────────────────────
    p = sub.add_parser(
        "search_engine_drilldown",
        help="Show URL list for a specific engine from cached search results (or re-runs search on cache miss)."
    )
    p.add_argument("query", help="Search query (must match a prior search_web call)")
    p.add_argument("--engine", required=True,
                   help="Engine name: google, duckduckgo, mojeek, lobsters, semantic_scholar, "
                        "openalex, crossref, stack_exchange, open_library")
    mode_edd = p.add_mutually_exclusive_group()
    mode_edd.add_argument("--books", action="store_true",
                   help="Must match original search_web call (part of cache key)")
    mode_edd.add_argument("--pdf", action="store_true",
                   help="Must match original search_web call (part of cache key)")
    mode_edd.add_argument("--docs", action="store_true",
                   help="Must match original search_web call (part of cache key)")

    # ── scrape_url ────────────────────────────────────────────────────────────
    p = sub.add_parser("scrape_url", help="Scrape URL to filtered markdown (PruningContentFilter, full content, no length cap) plus acquisition facts.")
    p.add_argument("url", help="URL to scrape")

    # ── Dispatch ──────────────────────────────────────────────────────────────
    args = parser.parse_args()

    if args.cmd == "search_web":
        result = asyncio.run(search_web_workflow(
            args.query, "en", None, None,
            books=args.books, pdf=args.pdf, docs=args.docs,
        ))

    elif args.cmd == "search_engine_drilldown":
        mode = "books" if args.books else ("pdf" if args.pdf else ("docs" if args.docs else None))
        key = cache_key(args.query, "en", None, None, modifier_id=mode)
        hit = cache_read(key)
        if hit is None:
            asyncio.run(search_web_workflow(
                args.query, "en", None, None,
                books=args.books, pdf=args.pdf, docs=args.docs,
            ))
            hit = cache_read(key)
        if hit is None:
            print(f'# search_engine_drilldown: cache write failed for "{args.query}"')
            return
        pools = hit.get("pools", {})
        if args.engine not in pools:
            avail = ", ".join(sorted(pools.keys())) or "(none)"
            print(f"Engine '{args.engine}' not in cached pools. Available: {avail}")
            return
        print(format_engine_pool(pools[args.engine], args.engine, args.query))
        return

    elif args.cmd == "scrape_url":
        url = args.url
        if urlparse(url).path.lower().endswith(".pdf"):
            print(f"PDF must be downloaded by the user: {url}")
            return
        result = asyncio.run(scrape_url_workflow(url))

    print(result[0].text)


if __name__ == "__main__":
    main()
