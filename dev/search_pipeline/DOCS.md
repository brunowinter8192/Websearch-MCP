# Search Pipeline

Test suite for evaluating and tuning SearXNG search result quality with profile-based parameter testing.

## Shared Config (pipeline root)

### profiles.yml

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

### queries.txt

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

## engines_eval/ → decisions/search01_engines

### 01_engines.py

**Purpose:** Run all test queries against SearXNG API with profile-based parameters and generate markdown report.
**Input:** queries.txt + profiles.yml (in pipeline root).
**Output:** Markdown report in `01_reports/` with timestamp.

#### CLI

```bash
# Standard run (each query uses its assigned profile)
./venv/bin/python dev/search_pipeline/engines_eval/01_engines.py

# A/B compare mode (non-general queries run twice: profile + general)
./venv/bin/python dev/search_pipeline/engines_eval/01_engines.py --compare
```

#### Key Functions

- `load_queries()` — Parses queries.txt with `@profile:` directives, returns `list[dict]` with `{query, profile}`
- `load_profiles()` — Reads profiles.yml
- `run_query(query, profile)` — Executes query with profile parameters (category, engines, language, time_range). Paginates across MAX_PAGES (3) pages per query, deduplicates by URL, returns up to TOP_K (30) results
- `build_report()` — Summary + per-query tables showing profile, score, engines, domain, URL, snippet. In compare mode: comparison tables per query with result count, avg score, domain overlap.
- `compute_settings_hash()` — MD5 hash of settings.yml for config identification

## engines_eval/ → decisions/search02_routing (fingerprint investigation)

### 20_tls_fingerprint.py

**Purpose:** Probe external JA3 fingerprint services to measure the TLS fingerprint of SearXNG-style httpx requests.
**Input:** No CLI args. Queries tls.browserleaks.com and ja3er.com.
**Output:** Markdown report in `20_reports/` with JA3 hash, TLS version, cipher count, User-Agent.

```bash
./venv/bin/python dev/search_pipeline/engines_eval/20_tls_fingerprint.py
```

### 21_cipher_shuffle_verify.py

**Purpose:** Verify that SearXNG's cipher shuffling (`shuffle_ciphers()`) produces distinct JA3 hashes across requests — confirms fingerprint diversification is active.
**Input:** No CLI args. Sends 12 requests to tls.browserleaks.com with fresh SSL context per request.
**Output:** Markdown report in `20_reports/` with per-request JA3 hash table and verdict (unique count / total).

```bash
./venv/bin/python dev/search_pipeline/engines_eval/21_cipher_shuffle_verify.py
```

### 22_header_inspection.py

**Purpose:** Inspect which HTTP headers SearXNG-style requests send, as seen by the server.
**Input:** No CLI args. Sends 3 requests to httpbin.org/headers.
**Output:** Markdown report in `20_reports/` with per-request header tables and consistency analysis.

```bash
./venv/bin/python dev/search_pipeline/engines_eval/22_header_inspection.py
```

### 23_suspension_threshold.py

**Purpose:** Measure at which query rate each engine gets suspended by SearXNG's internal suspension mechanism. Tests 8 engines across 4 phases (10s / 5s / 2s / 1s intervals, 6 queries each).
**Input:** No CLI args. Queries local SearXNG at `http://localhost:8080`.
**Output:** Markdown report in `20_reports/` with suspension threshold per engine and per-phase detail tables.

```bash
./venv/bin/python dev/search_pipeline/engines_eval/23_suspension_threshold.py
```

### 23_google_retest.py

**Purpose:** One-shot retest of Google after `suspension_times=0` and `ban_time_on_fail=0` were set. Verifies SearXNG no longer pre-emptively blocks Google.
**Input:** No CLI args. Runs same 4-phase protocol as `23_suspension_threshold.py`, Google only.
**Output:** Markdown report in `20_reports/` with verdict (suspension flag present/absent) and per-request results.

```bash
./venv/bin/python dev/search_pipeline/engines_eval/23_google_retest.py
```

### 24_engine_health_check.py

**Purpose:** Phase-1-only health check for 6 previously-suspended engines after SearXNG 2026.4.3 update. Confirms engines are returning results at conservative query rate (10s × 6 queries).
**Input:** No CLI args. Tests: Brave, Mojeek, Startpage, Google Scholar, Semantic Scholar, CrossRef.
**Output:** Markdown report in `20_reports/` with summary table (clean/flagged/status per engine) and per-engine detail.

```bash
./venv/bin/python dev/search_pipeline/engines_eval/24_engine_health_check.py
```

## ranking_eval/ → decisions/search03_ranking

### 03_ranking.py

**Purpose:** Compare two search reports to identify which configuration produced better results.
**Input:** Two report files from `engines_eval/01_reports/` (CLI args or auto-selects latest two).
**Output:** Comparison report in `03_reports/` with timestamp.

#### CLI

```bash
# Compare latest two reports
./venv/bin/python dev/search_pipeline/ranking_eval/03_ranking.py

# Compare specific reports
./venv/bin/python dev/search_pipeline/ranking_eval/03_ranking.py engines_eval/01_reports/report_A.md engines_eval/01_reports/report_B.md
```

#### Metrics

- Results count per query
- Average score per query
- Domain overlap (shared/total)
- Winner (A/B/=) by avg score
- New/lost URLs per query (detail section)

## weights_eval/ → decisions/search04_weights

### 10_engine_consensus.py

**Purpose:** Evaluate engine weight calibration via consensus analysis. Queries SearXNG as a whole (aggregated) and measures how often each engine's results are corroborated by other engines.
**Input:** Hardcoded test queries (13 queries, mix of technical, scientific, German-language).
**Output:** Markdown report in `10_reports/` with per-engine consensus metrics.

```bash
./venv/bin/python dev/search_pipeline/weights_eval/10_engine_consensus.py
```

### 11_engine_isolation.py

**Purpose:** Query each engine INDIVIDUALLY for the same set of queries. Produces per-engine URL lists and an overlap analysis across all engines. Unlike 10_engine_consensus.py, this isolates engines to see what each one contributes independently.
**Input:** 30 hardcoded test queries (Tech/Code EN, Science EN, German, Niche, Broad). 9 engines tested.
**Output:** `11_reports/overlap_matrix.md` (summary + Jaccard matrix) + one `engine_<name>.md` per engine (top 10 URLs per query).

```bash
./venv/bin/python dev/search_pipeline/weights_eval/11_engine_isolation.py
```

Rate limiting: 5s between engine calls, 10s between queries. Full run: ~35 minutes.

### 13_export_csv.py

**Purpose:** Parse `11_reports/engine_*.md` files and export structured CSVs for analysis.
**Input:** `11_reports/engine_*.md` files.
**Output:** 5 CSVs in `11_reports/eval/`:

| CSV | Content |
|-----|---------|
| `engine_urls.csv` | One row per engine × query × URL (raw data) |
| `engine_summary.csv` | Per-engine aggregated metrics (total, unique, consensus rate) |
| `overlap_pairwise.csv` | Jaccard similarity for every engine pair |
| `query_coverage.csv` | Per engine × query breakdown (num_urls, consensus, unique) |
| `query_unique_urls.csv` | Per query: total unique URLs + per-engine exclusive counts |

```bash
./venv/bin/python dev/search_pipeline/weights_eval/13_export_csv.py
```

### 14_tiered_ranking.py

**Purpose:** Prototype for tiered ranking by engine count. Instead of SearXNG's score-based ranking, URLs are deduplicated and ranked by how many engines found them. Results split into 3 tiers: Top 20 (≥2 engines), Extended Consensus, Unique (1 engine only).
**Input:** Query as CLI argument. Queries all 9 engines individually.
**Output:** Markdown report in `14_reports/<sanitized_query>.md` with tiered URL tables.

```bash
./venv/bin/python dev/search_pipeline/weights_eval/14_tiered_ranking.py "python asyncio best practices"
```

## Workflow

### Engine Evaluation
1. Run engine isolation: `./venv/bin/python dev/search_pipeline/weights_eval/11_engine_isolation.py` (~35 min)
2. Export CSVs: `./venv/bin/python dev/search_pipeline/weights_eval/13_export_csv.py`
3. Analyze overlap in `11_reports/eval/` CSVs
4. Test tiered ranking: `./venv/bin/python dev/search_pipeline/weights_eval/14_tiered_ranking.py "your query"`

### Ranking Comparison (A/B)
1. Run search with config A: `./venv/bin/python dev/search_pipeline/engines_eval/01_engines.py`
2. Change config in settings.yml, restart Docker
3. Run again, compare: `./venv/bin/python dev/search_pipeline/ranking_eval/03_ranking.py`

### Engine Health Check (post-update)
1. After `docker compose pull`: `./venv/bin/python dev/search_pipeline/engines_eval/24_engine_health_check.py`
