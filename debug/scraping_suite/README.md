# Scraping Suite

Comprehensive test suite for continuous quality monitoring of the URL scraper.

## Purpose

This test suite provides baseline tracking and regression detection for the scrape_url module. Each time the scraper implementation changes, this suite verifies that content extraction quality remains consistent or improves across diverse web page types.

The suite addresses the challenge of maintaining scraper quality as the codebase grows. Without systematic testing, subtle regressions in content extraction can go unnoticed. This suite makes quality changes visible through automated comparison.

## Test Domains

The suite tests five domains representing different content types and technical challenges.

### Wikipedia (German)
URL: https://de.wikipedia.org/wiki/Biber

Tests complex HTML with multilingual content, extensive formatting, navigation elements, and nested structures. Validates handling of large documents with diverse tag hierarchies.

### SearXNG Documentation
URL: https://docs.searxng.org/admin/settings/settings_engines.html#example-multilingual-search

Tests technical documentation with code examples, YAML snippets, anchor navigation, and structured content sections. Validates code block extraction and heading hierarchy preservation.

### Scikit-learn API Documentation
URL: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html

Tests API documentation with parameter tables, code examples, return value descriptions, and cross-references. Validates table extraction and inline code handling.

### Medium Article
URL: https://medium.com/areas-producers/llms-are-randomized-algorithms-c41e2eddedf4

Tests dynamic article content with images, embedded media, author information, and reading time estimates. Validates JavaScript-rendered content extraction.

### Chroma Documentation
URL: https://docs.trychroma.com/docs/overview/telemetry

Tests modern documentation with JavaScript-rendered content, interactive elements, and dynamic navigation. Validates networkidle wait strategy effectiveness.

### Binance API Documentation
URL: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams

Tests API documentation with WebSocket specifications, streaming data formats, JSON payload examples, and technical protocol details. Validates extraction of structured API reference content with nested code blocks.

## Usage

### Running Baseline Tests

Execute the baseline suite to scrape all test domains and save results.

```bash
python debug/scraping_suite/run_baseline.py
```

This creates a new iteration for each domain in the baselines directory. Each iteration includes the scraped markdown content and metadata with character counts, word counts, and timestamps.

### Comparing Iterations

After running a new baseline, compare it with the previous iteration to detect changes.

```bash
python debug/scraping_suite/compare_iterations.py
```

This analyzes all domains, compares the last two iterations, and generates a detailed report in the reports directory. The console output shows a summary with character and word count differences.

## Workflow

Standard workflow when implementing scraper changes.

1. Implement feature or fix in src/scraper/scrape_url.py
2. Run baseline suite to capture new iteration
3. Run comparison script to analyze differences
4. Review diff report to verify changes are improvements
5. Investigate any unexpected regressions

## Output Structure

### Baselines Directory

The baselines directory contains subdirectories for each test domain. Each domain directory contains numbered iterations with content and metadata files.

```
baselines/
├── wikipedia_biber/
│   ├── iteration_001.md
│   ├── metadata_001.json
│   ├── iteration_002.md
│   └── metadata_002.json
├── searxng_docs/
├── sklearn_docs/
├── medium_article/
├── chroma_docs/
└── binance_docs/
```

Metadata files contain iteration number, timestamp, URL, character count, and word count.

### Reports Directory

The reports directory contains timestamped comparison reports. Each report shows character and word count changes, percentage differences, status classifications, and git-style content diffs for changed domains.

Status classifications indicate the magnitude of change. IDENTICAL means no change detected. MINOR_CHANGE indicates less than five percent change. MODERATE_CHANGE indicates five to twenty percent change. MAJOR_CHANGE indicates over twenty percent change.

## Implementation Notes

The run_baseline.py script calls scrape_url_workflow directly without implementing custom scraping logic. This ensures tests use the actual production scraper code.

The compare_iterations.py script uses Python's difflib module to generate unified diffs similar to git diff output. This makes content changes easy to review.

Both baselines and reports directories are excluded from version control via gitignore. Only the test scripts and domain list are committed to the repository.
