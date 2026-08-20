# pipeline.py split (2026-08-20)

`src/news/pipeline.py` (428 LOC, over the 400-LOC ceiling) split into 3 modules under `src/news/`.
Pure refactor — zero behavior/log-line/exit-code/manifest-shape change, verified by pytest baseline
parity + entry-point smoke (see Verification). Same discipline as the `proxy_riding/rider.py` split
(area: `news_pipeline`) — concern-based cut + mandatory function-size extraction + comment triage.

## Module cut

| Module | Owns |
|---|---|
| `pipeline.py` (entry, unchanged import path) | `run_pipeline`, `run_scrape_only`, `run_discover_only` (orchestrators) + 5 engine-arm helpers + `_build_ok_manifest_entries` |
| `pipeline_support.py` (new sibling) | `_setup_logging`, `_check_internet`, `_persist_master_list`, `_write_discover_snapshot`, `_write_marker` + `PROJECT_ROOT`/`LOG_DIR`/`PRECONDITION_TIMEOUT` |
| `clean_pass.py` (new sibling) | `_run_clean_pass` |

`_run_clean_pass` was NOT folded into `pipeline_support.py` despite the prompt listing it alongside
the other 5 "utility helpers": it's stage-specific business logic (reads raw MD, calls
`platform.cleanup()`, writes to the RAG collection dir, maintains `bodyless_urls.txt`) with its own
independent test file (`tests/test_theblock_clean_pass.py`), categorically different from the other
five which are pure run-bookkeeping (logging setup, connectivity probe, 3 tiny state-file writers)
with zero platform-specific logic. Lumping it in would have made `pipeline_support.py` a
concern-mixed dumping ground rather than a coherent "generic infra" module.

Constants placement: `PROJECT_ROOT`/`LOG_DIR` moved to `pipeline_support.py` (not left in
`pipeline.py`) because BOTH modules need `LOG_DIR` (`pipeline.py`'s 3 orchestrators call
`LOG_DIR.mkdir(...)`; `pipeline_support.py`'s `_setup_logging`/`_write_marker` build paths under it)
— defining it in `pipeline.py` and importing into `pipeline_support.py` would create a cycle, since
`pipeline.py` already imports the 5 functions FROM `pipeline_support.py`. `DATA_ROOT`/
`SCRAPE_CHUNK_SIZE` stayed in `pipeline.py` (module-specific, only its own orchestrators/arms use
them); `PRECONDITION_TIMEOUT` stayed in `pipeline_support.py` (only `_check_internet` uses it).

## Behavior-preservation finding: early-return sentinel for run_pipeline's arms

`run_pipeline`'s two arms each contain internal early `return`s ("discover returned 0 articles",
"nothing new to scrape") that call `_write_marker` inline THEN return — which, in the pre-split
function, meant returning from `run_pipeline` itself, skipping its trailing
`log.info("=== complete ===")` + a SECOND `_write_marker` call that only ran on normal completion.
Extracting each arm as a plain `async def` helper and unconditionally running that trailing wrap-up
in `run_pipeline` afterward would have introduced a spurious extra "complete" log line + a duplicate
marker write on every early-abort run — a real behavior change, not caught by casual code reading.
Fix: `_run_pipeline_proxy_pool`/`_run_pipeline_browser` return `bool` — `True` on completion (caller
does the trailing wrap-up), `False` on early abort (marker already written inline by the arm, caller
skips the wrap-up entirely). `run_scrape_only`'s two arms were checked for the same pattern and have
NO internal early return (confirmed by reading both blocks in full before extraction) — they were
extracted as plain `async def` helpers with no sentinel, since both orchestrator's remaining
"validate → dispatch → unconditional wrap-up" shapes always reach the trailing code regardless of
which arm ran.

## Helper extraction

`run_pipeline` (148→19 code lines): `_run_pipeline_proxy_pool` (box_lock+Janitor lifecycle +
discover/dedup/scrape, 60 code lines — kept as one function per the same reasoning as the
`rider.py` milestone's `_run_slot`: the try/finally interleaves early-returns with Janitor
start/end-job bookkeeping, and splitting the try-body out risks altering when `finally` observes
partially-initialized `new_entries`/`n_ok`) + `_persist_proxy_pool_results` (manifest/blocked-list
persist + conditional clean-pass dispatch, runs AFTER the box_lock context exits — a second,
genuinely separable coherent step, 20 code lines) + `_run_pipeline_browser` (discover→dedup→scrape
with `RegwallGuardError` recovery → persist, 36 code lines).

`run_scrape_only` (95→51 code lines): `_run_scrape_only_riding` (34 code lines) + `_run_scrape_only_browser`
(22 code lines) extracted; the orchestrator itself sits at 51 code lines (setup/validation: job_id,
filter_desc, internet check, `load_scrape_entries` capability check, entries load, dedup — one
coherent "validate & prepare" story with 2 early returns of its own, both BEFORE the arm dispatch so
unaffected by the arm split). 51 is marginally over the 50-line soft threshold; no further coherent
sub-helper was identified without re-splitting the validation sequence across an early-return
boundary for no real cohesion gain — same class of judgment call as `rider.py`'s
`_apply_fetch_result` (53 code lines).

`_build_ok_manifest_entries(new_entries, manifest) -> list[dict]`: the 9-line list-comprehension
block was confirmed byte-identical across its 3 original call sites (`run_scrape_only`'s
proxy_riding arm, `run_pipeline`'s proxy_pool arm, `run_pipeline`'s browser arm) before extraction —
diffed by eye, no discrepancy found. All 3 call sites remained inside `pipeline.py` after the split,
so the helper needed no cross-module import.

## Comment triage

File was comment-light as expected. Two multi-line headers condensed:

| Original | Verdict |
|---|---|
| `_run_clean_pass`'s 4-line header (raw/.md read, collection_dir write, bodyless log, progress-every-200, return shape) | condensed to 1 line; full detail moved to `clean_pass.py`'s new `DOCS.md` module entry (not previously documented at function-body granularity — `src/news/DOCS.md` only listed it as a generic helper name before this sweep) |
| `_persist_master_list`'s 3-line header (format spec, lastmod/url skip rule, TheBlock-specific gate) | condensed to 1 line; format/skip-rule/TheBlock-gate detail moved to `pipeline_support.py`'s new `DOCS.md` module entry (same — not previously documented beyond a helper-name mention) |

Two NEW 1-line headers were authored (not salvaged) for `_run_pipeline_proxy_pool`/
`_run_pipeline_browser` documenting their `bool` return contract — kept to one line each; the full
early-return-sentinel rationale (this entry's own finding above) went to `src/news/DOCS.md`'s Gotchas
section, not process-docs, since it's the CURRENT contract of a function that exists now, not a
historical investigation trail.

Zero comments were deleted-as-covered (none existed at that redundancy level in this file) and zero
required genuinely new process-docs substance beyond the module-cut rationale and the early-return
sentinel finding recorded above.

## Verification

Full suite (`pytest tests/`): 182 passed, 10 failed (8 `test_query_logger.py` + 2 `test_proxy_pool.py`)
— identical to the standing baseline, 0 new failures. `tests/test_theblock_clean_pass.py`: 6/6 passed
(baseline: 6/6, unchanged) after re-pointing its import to `src.news.clean_pass`.
Entry-point level: `python -m src.news --help` exits 0 with the unchanged CLI surface — proves
`__main__.py`'s `from src.news.pipeline import run_pipeline, run_discover_only, run_scrape_only`
resolves through the full new import chain (`pipeline.py` → `pipeline_support.py` + `clean_pass.py`)
without a circular-import or missing-symbol failure.
NOT verified: a live `run_pipeline`/`run_scrape_only` execution against real network/platform data
(would require live CoinDesk/TheBlock access) — the early-return-sentinel and `RegwallGuardError`
paths are verified by code-construction (each early `return` traced 1:1 from the original file to
its extracted location) and by the unaffected pytest baseline, not by an end-to-end run.
Repo-wide grep for every moved symbol (`_setup_logging`, `_check_internet`, `_persist_master_list`,
`_write_discover_snapshot`, `_write_marker`, `_run_clean_pass`) confirmed zero stale references
outside `pipeline.py`'s own re-imports; `tests/test_theblock_clean_pass.py`'s import was the only
external reference and was re-pointed. `src/news/engine/proxy_pool/scrape.py`'s docstring (naming
`_run_clean_pass in pipeline.py` and `pipeline.py:run_pipeline` as the Janitor lifecycle owner) was
also corrected to `clean_pass.py` / `pipeline.py:_run_pipeline_proxy_pool` — not a live import, but a
stale prose pointer to the moved symbol's new location.
