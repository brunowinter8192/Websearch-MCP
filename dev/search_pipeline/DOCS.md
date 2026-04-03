# Search Pipeline

Test suite for evaluating and tuning SearXNG search result quality with profile-based parameter testing.

## profiles.yml

**Purpose:** Define parameter sets for different query types. Each profile maps to SearXNG API parameters.

**Format:**
```yaml
profile_name:
  category: general|science|it|news
  language: en|de|all
  time_range: null|day|month|year
  engines: null|"engine1,engine2"  # null = use category defaults
```

**Built-in profiles:**
- `general` — Default web search (all general-category engines, no time filter)
- `science` — Academic papers (Google Scholar + Semantic Scholar + CrossRef, last year)
- `it` — Technical content (general category, last year)
- `research` — All general-category engines, no time filter (best for broad discovery)
- `recent` — Recent content (general, last month)

## queries.txt

**Purpose:** Test queries with profile assignments.

One query per line. Lines starting with `#` are comments. `@profile: <name>` sets the profile for subsequent queries until the next `@profile` directive.

**Format:**
```
# --- Section Name ---
@profile: research
query one
query two

@profile: general
query three
```

## 01_engines.py

**Purpose:** Run all test queries against SearXNG API with profile-based parameters and generate markdown report.
**Input:** queries.txt + profiles.yml.
**Output:** Markdown report in 01_reports/ with timestamp.

### CLI

```bash
# Standard run (each query uses its assigned profile)
./venv/bin/python dev/search_pipeline/01_engines.py

# A/B compare mode (non-general queries run twice: profile + general)
./venv/bin/python dev/search_pipeline/01_engines.py --compare
```

### Key Functions

- `load_queries()` — Parses queries.txt with `@profile:` directives, returns `list[dict]` with `{query, profile}`
- `load_profiles()` — Reads profiles.yml
- `run_query(query, profile)` — Executes query with profile parameters (category, engines, language, time_range). Paginates across MAX_PAGES (3) pages per query, deduplicates by URL, returns up to TOP_K (30) results
- `build_report()` — Summary + per-query tables showing profile, score, engines, domain, URL, snippet. In compare mode: comparison tables per query with result count, avg score, domain overlap.
- `compute_settings_hash()` — MD5 hash of settings.yml for config identification

## 04_content_eval.py

**Purpose:** Scrape top URLs from a search report and evaluate content quality. Uses the same scraping pipeline as the MCP scrape_url tool.
**Input:** Latest search report from 01_reports/ (or path via CLI argument).
**Output:** Summary report in 04_reports/ plus individual .md files per URL in 04_content_<report_stem>/.

Imports `scrape_url_workflow` from `src/scraper/scrape_url` to ensure identical scraping behavior as the MCP tool. Scrapes top 5 URLs per query (TOP_N_PER_QUERY) with 2s delay. Content truncated to 50000 chars at paragraph boundary (EXCERPT_LENGTH) — effectively no truncation.

Fallback chain: scrape_url_workflow → SearXNG snippet → error marker. Each result tagged with source (scraped, snippet, failed). Garbage detection for cookie banners, cloudflare, login walls.

## 03_ranking.py

**Purpose:** Compare two search reports to identify which configuration produced better results.
**Input:** Two report files from 01_reports/ (CLI args or auto-selects latest two).
**Output:** Comparison report in 03_reports/ with timestamp.

### CLI

```bash
# Compare latest two reports
./venv/bin/python dev/search_pipeline/03_ranking.py

# Compare specific reports
./venv/bin/python dev/search_pipeline/03_ranking.py 01_reports/report_A.md 01_reports/report_B.md
```

### Metrics

- Results count per query
- Average score per query
- Domain overlap (shared/total)
- Winner (A/B/=) by avg score
- New/lost URLs per query (detail section)

## 10_engine_consensus.py

**Purpose:** Evaluate engine weight calibration via consensus analysis. Measures how often each engine's results are corroborated by other engines.
**Input:** Hardcoded test queries (13 queries, mix of technical, scientific, German-language).
**Output:** Markdown report in 10_reports/ with per-engine consensus metrics.

### CLI

```bash
./venv/bin/python dev/search_pipeline/10_engine_consensus.py
```

### Metrics per Engine

- **Total URLs**: Unique URLs returned across all queries
- **Consensus Rate**: % of engine's URLs also found by ≥1 other engine (higher = better signal quality)
- **Unique URLs**: URLs found exclusively by this engine (discovery value)
- **Avg Position**: Mean combined-ranking position across all results
- **Top-20 Coverage**: URLs contributed to the top-20 consensus results per query

### Usage

1. Run script (takes ~30s for 13 queries with 2s delay)
2. Read report in 10_reports/
3. Paste results into `decisions/search04_weights.md` Evidenz section
4. Calibrate weights based on consensus rate vs. unique value trade-off

## Workflow

1. Edit queries.txt with test queries and `@profile:` assignments
2. Optionally edit profiles.yml to add/modify parameter sets
3. Run: `./venv/bin/python dev/search_pipeline/01_engines.py`
4. Read report in 01_reports/
5. Optionally compare: `./venv/bin/python dev/search_pipeline/01_engines.py --compare`
6. For content quality: `./venv/bin/python dev/search_pipeline/04_content_eval.py`
7. Read content report in 04_reports/ and individual files in 04_content_*/
8. To tune SearXNG config: edit src/searxng/settings.yml, restart Docker, run again
9. Compare reports: `./venv/bin/python dev/search_pipeline/03_ranking.py`
