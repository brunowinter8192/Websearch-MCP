# Searching Suite

Test suite for evaluating and tuning SearXNG search result quality.

## queries.txt

**Purpose:** Test queries for search quality evaluation.

One query per line. Lines starting with # are comments. Grouped by use-case type (metasearch, trading/finance, general tech). Add or modify queries to match actual search patterns.

## 01_run_search.py

**Purpose:** Run all test queries against SearXNG API and generate markdown report.
**Input:** queries.txt (one query per line).
**Output:** Markdown report in 01_reports/ with timestamp.

### run_search_suite()

Main orchestrator. Loads queries, runs each against SearXNG API, builds and saves report.

### load_queries()

Reads queries.txt, filters comments and empty lines, returns list of query strings.

### compute_settings_hash()

Computes MD5 hash (first 8 chars) of settings.yml for config identification across reports.

### run_query()

Executes single query against SearXNG API at localhost:8080. Returns top 10 results as list of dicts. Uses requests directly (no MCP dependency).

### extract_domain()

Extracts netloc from URL for domain classification.

### build_report()

Builds full markdown report. Summary section includes total queries, avg results, multi-engine percentage, high-priority percentage, avg score, and top 10 domains. Per-query section shows ranked table with score, priority, engines, domain, and title.

### save_report()

Writes report to 01_reports/ with timestamped filename.

## Workflow

1. Edit queries.txt with test queries
2. Run: `./venv/bin/python dev/searching_suite/01_run_search.py`
3. Read report in 01_reports/
4. Change config in src/searxng/settings.yml
5. Restart: `docker compose restart searxng`
6. Run again, compare reports
