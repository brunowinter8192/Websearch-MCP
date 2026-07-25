# 57 — The Block in-pipe clean-pass

**Date:** 2026-07-06. **Branch:** `theblock-clean-pass`.
**Prior art:** the raw-only decoupling entry, the cleaner extension over the 22,995-file corpus.

---

## What was wired

`run_pipeline` proxy_pool branch (TheBlock-only by construction — only TheBlock sets
`scrape_engine="proxy_pool"`) gained **Stage 4 — clean-pass**, inserted after the existing
`_append_to_raw_manifest` + `_update_blocked_urls` calls.

Stage 4 derives `collection_dir` from `PROJECT_ROOT` (already defined in `pipeline.py`):

```python
collection_dir = PROJECT_ROOT.parent / "rag-cli" / "data" / "documents" / platform.collection
```

`PROJECT_ROOT = Path(__file__).parent.parent.parent` → `searxng-cli/`.
`PROJECT_ROOT.parent` → `cli/` (sibling directory).
`platform.collection == "theblock"` → final path: `cli/rag-cli/data/documents/theblock`.
This is where the existing 22,930 clean docs already live. No absolute path hardcoded anywhere.

---

## Where the helper lives

`_run_clean_pass()` in `pipeline.py` FUNCTIONS section.

**Signature:**
```python
def _run_clean_pass(
    platform: Platform,
    ok_entries: list[dict],
    raw_dir: Path,
    collection_dir: Path,
    log: logging.Logger,
) -> dict:
```
Returns `{"n_cleaned": int, "n_bodyless": int, "total": int}`.

`collection_dir` is a parameter so the test can inject a tmp dir. `run_pipeline` computes
the sibling-relative real path and passes it in.

---

## Per-entry logic

For each `ok` manifest entry `{hash, url, publication_date}`:

1. Read `raw_dir/{hash}.md` (read-only).
2. `platform.cleanup(raw_html, entry)` — TheBlock's `cleanup.py` parses JSON-LD `NewsArticle`,
   extracts `articleBody`, converts to Markdown, applies `_post_clean()`, and **mutates
   `entry["publication_date"]` from `datePublished`**. Returns `""` on no JSON-LD or empty body.
3. Empty result → `log.info("clean_pass: body-less …")` + URL appended to body-less list. No clean file.
4. Non-empty result → `pub_date_str(entry)` (from `engine/publish.py`) → write
   `collection_dir/theblock__{pubdate}__{hash}.md`.

`pub_date_str` is called **after** `cleanup()` because TheBlock's `publication_date` is
post-fetch (set from JSON-LD) — it is not present in the discover entry.

---

## Body-less URL list

Path: `raw_dir.parent / "clean" / "bodyless_urls.txt"` = `data/news/theblock/clean/bodyless_urls.txt`.
Convention: same as `_update_blocked_urls` — read existing, set-union, strip empty, write sorted +
trailing newline. Persisted once at end of the pass (not per-entry write).

---

## Live logging (visibility at scale)

Three logging surfaces:

1. **Per body-less** — `log.info("clean_pass: body-less — {url}")` — shows up in the pipeline log
   stream as each body-less URL is encountered (in addition to `cleanup.py`'s existing stderr line).
2. **Progress every 200 entries** — `log.info("clean progress {i}/{total} — {n_cleaned} cleaned, {n_bodyless} body-less")` — prevents silent multi-thousand-entry runs.
3. **Final stats** — `log.info("clean_pass: {n_cleaned} cleaned / {n_bodyless} body-less / {total} total")`.

---

## Raw retention guarantee

`_run_clean_pass` only calls `raw_path.read_text()` on each raw file. Zero writes, moves, or
deletes on anything under `raw_dir/`. No code in the pipeline deleted raw files before this task;
this task adds no such capability. Test asserts byte-for-byte equality of both raw fixtures before
and after the pass.

---

## Indexing stays decoupled

`_run_clean_pass` only writes `.md` files to `collection_dir`. No `rag-cli index` call, no
`publish.py:run_rag_index`, no `publish.py:publish_articles`. The actual index run remains a
separate manual step (`rag-cli index --collection theblock`).

---

## Stale docstring fixed

`src/news/engine/proxy_pool/scrape.py` docstring referenced `_run_cleanup in pipeline.py`
(never existed — removed in the raw-only decoupling stage). Updated to `_run_clean_pass in pipeline.py`.

---

## Test approach

`tests/test_theblock_clean_pass.py` — 6 tests, synthetic HTML fixtures, no corpus, no network.

Uses real `TheBlockPlatform.cleanup()` (crawl4ai available in venv) — tests the wiring, not
the cleaner rules (those were proven over the 22,995-file corpus in the cleaner extension entry).

| Test | What it verifies |
|---|---|
| `test_good_article_clean_file_written` | Correct `theblock__{date}__{hash}.md` written with non-empty content |
| `test_bodyless_no_clean_file_url_recorded` | No clean file; URL in `bodyless_urls.txt` |
| `test_raw_files_unchanged_after_pass` | byte-for-byte raw identity after pass |
| `test_stats_correct` | `{"n_cleaned":1, "n_bodyless":1, "total":2}` returned |
| `test_empty_entries_returns_zero_stats` | Empty input → zero stats; `collection_dir` not created |
| `test_bodyless_urls_union_merged` | Second run union-merges URLs, file stays sorted |

All 6 pass (0.45 s).

---

## Files changed

- `src/news/pipeline.py` — import `pub_date_str`, update `run_pipeline` header comment, add Stage 4 call, add `_run_clean_pass` function
- `src/news/engine/proxy_pool/scrape.py` — stale docstring fix
- `tests/test_theblock_clean_pass.py` — new test file (6 tests)
- `src/news/DOCS.md` — Flow + Role updated
- `src/news/platforms/theblock/DOCS.md` — `cleanup.py` Called-by updated
