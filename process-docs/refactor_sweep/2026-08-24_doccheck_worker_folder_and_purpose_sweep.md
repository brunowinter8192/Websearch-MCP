# doccheck worker pass — dev/ report-folder discipline + DOCS.md Purpose compression (2026-08-24)

Worker re-run of `iterative-dev-doccheck` on a committed orchestrator-audit state, continuing the
`refactor_sweep` area. Two independent workstreams: (1) `dev/` report/data-folder naming across
`scrape_pipeline`, `news_pipeline`, `search_pipeline`, `explore_pipeline`; (2) DOCS.md Purpose-field
compression (one sentence, salvage the rest) for `src/scraper/`, `src/crawler/`, `src/search/`,
`src/search/engines/`. Zero runtime-behavior changes beyond the output-path string literals the
renames required — verified via full-suite pytest before/after (226 passed both times; the 2 failures
present both times are a pre-existing missing-`matplotlib` dependency in `dev/news_pipeline/
coindesk_proxy_riding/test_sigint_report.py`, untouched by this session; 1 pre-existing collection
error in `dev/scrape_pipeline/garbage_eval/10_live_garbage_test.py` imports a `log_scrape_failure`
symbol removed from `src/scraper/scrape_url.py` in an earlier session, also untouched here).

## Naming decisions for mixed-content-type folders

The dev-reports rule wants DATA in "its own type-named folder... kept separate... never mixed into
md/." Several dirs didn't fit a literal type name cleanly:

**`dev/scrape_pipeline/{01_dual_mode_outputs,02_raw_outputs}` → `{01_dual_mode_data,02_raw_data}`.**
Both are direct siblings of the existing top-level `dev/scrape_pipeline/md/` (used by `07_pipe_scrape_
eval.py`/`06_cloudflare_md_adoption.py` for reports) — renaming either to `md/` would collide with
that existing reports folder. Content is markdown corpora (per-URL scraped `.md`), so a literal
`md_data/` was considered and rejected (redundant/confusing combination of the type name with a
generic "data" suffix). Settled on `*_data` — matching an existing in-repo precedent one directory
over: `07_pipe_scrape_eval.py`'s own `07_pipe_scrape_eval_data/full_run_<ts>/`.

**`dev/scrape_pipeline/03_cleanup/cleaned_outputs` → `cleaned_data`; `04_overview_sweep/sweep_outputs`
→ `sweep_data`.** Same `*_data` pattern for consistency across the area, even though these two nest
under their own subfolder (no top-level `md/` collision risk for them specifically — `md` would have
been viable in isolation, but a mixed convention within one area was judged worse than a uniform one).

**`dev/search_pipeline/data/` → split five ways: `jsonl/`, `txt/`, `png/`, `html/` (new), `runs/`.**
`_capture_sorry.py` writes both `.html` and `.png` per capture (previously both into `data/`) — split
into sibling `PNG_DIR`/`HTML_DIR` constants, each written by its own type folder.
`value_eval_probe.py`/`stage1_pool_fetch.py`/`stage3_method_run*.py`/`stage4_aggregate*.py`/
`clean_pool.py`/`pool_diff_v2_v3.py` all read AND write into the same per-run `value_eval*_<ts>/`
directory by design — `stage4_aggregate.py`'s own docstring states this explicitly: "Output files
written to ts_dir/ (co-located with pool/methods/oracle JSONs)... No `--ts-out` flag (ts embedded in
dir name)." A first attempt split each run folder into `json/value_eval_v2_<ts>/` (pool/methods/oracle
JSON) + `md/value_eval_v2_<ts>/` (eval/engine_report MD) — reverted: every one of the 6 scripts above
takes a single `ts_dir`/`--pool-dir` argument that is BOTH the input-JSON source and the output-MD
destination; genuinely separating the two would require adding a second CLI arg (e.g. `--ts-out`) to
each script and rewiring their internal read/write paths — a real behavior/signature change, out of
this session's "output-path strings only" scope. Settled on `runs/` (single co-located folder per run,
same internal layout as before, just moved out from under the generic `data/` name).

## Purpose-field compression — what was cut vs kept

Compressed every module `**Purpose:**` field in the four target DOCS.md files to one sentence,
verified programmatically (regex sentence-count check across all four files, re-run until zero
false-negatives). The cut material split two ways:

- **Genuine dated-derivation/provenance narrative** (superseded config values, "as of DATE" change
  history, measured-vs-assumed distinctions) — salvaged verbatim-condensed into one new dated entry
  per affected area: `process-docs/scrape_pipeline/2026-08-24_docs_format_salvage.md`,
  `process-docs/camoufox_lane/2026-08-24_docs_format_salvage.md` (camoufox_scrape.py's cuts, kept
  separate per the module's own strand), `process-docs/pipe_scraper/2026-08-24_docs_format_salvage.md`,
  `process-docs/search_pipeline/2026-08-24_docs_format_salvage.md` (covers both `src/search/DOCS.md`
  and `src/search/engines/DOCS.md` cuts — one area, two DOCS.md surfaces).
- **Current-state behavior detail with no dated history** (CSS selectors, extraction mechanisms,
  field-schema enumerations) — mostly already duplicated in each file's own Gotchas section (the
  Purpose paragraphs had grown into restating what Gotchas already said more concisely); left in
  Gotchas, not salvaged, since it's still-current documentation, not process history.

First pass left a trailing "Full X derivation: `process-docs/<area>/<date>_docs_format_salvage.md`."
sentence in each compressed Purpose as a pointer — caught by the same sentence-count script (a pointer
sentence is still a second sentence) and by user review of `src/scraper/DOCS.md`'s Gotchas making the
same mistake (pinning a dated salvage filename instead of the area). Both fixed: Purpose-field
pointers removed entirely (per the skill's own note that "RAG makes the salvaged content findable" —
no in-DOCS pointer is required at all), and the three Gotchas-level references in `src/scraper/
DOCS.md` generalized from the specific dated filename to the area directory (`process-docs/
scrape_pipeline/`, `process-docs/camoufox_lane/`) — a DOCS.md may reference a process-docs AREA, never
a specific dated entry file (the entry-vs-area distinction applies to any surface pointing into
process-docs, not just process-docs-to-process-docs cross-references).

## gitignore staleness found in the same pass

`browser_eval`/`garbage_eval`/`filter_eval`'s `*_reports/` glob patterns and `search_pipeline`'s
`01_reports/` path prefix were leftover from an EARLIER rename (both areas already write to `md/` per
their current scripts) — the patterns no longer matched anything, so per-run reports in those folders
were silently NOT gitignored despite `browser_eval/DOCS.md`'s Gotcha claiming otherwise. Corrected the
Gotcha claim (checked `git ls-files`: `garbage_eval/md/*.md` reports ARE tracked/committed examples,
`browser_eval/01_baselines/` is the only actually-gitignored piece there) and updated the four stale
`dev/search_pipeline/01_reports/*` gitignore lines to `dev/search_pipeline/md/*`. Added matching
gitignore entries for this session's own renames (`dev/news_pipeline/{01_json,02b_data,03_data,
04_json,exploration/05_data}/`) so the rename didn't silently un-ignore previously-ignored output
dirs. `dev/scrape_pipeline/07_pipe_scrape_eval.py`'s `07_pipe_scrape_eval_data/full_run_*/` and
`dev/search_pipeline`'s `01_reports/{pipeline_smoke,engine_distribution,snippet_selection,
snippet_quality}_*.md` staleness (an old `A_pipe_scrape_eval_reports` area-rename artifact) were
identified but NOT fixed — outside this session's explicit rename scope, left as a follow-up note
rather than scope-creeping into an unrelated area's `.gitignore` history.
