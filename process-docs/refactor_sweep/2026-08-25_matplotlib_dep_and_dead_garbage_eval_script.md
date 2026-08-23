# matplotlib dependency fix + dead garbage_eval script removal (2026-08-25)

Two independent, small repo-hygiene fixes in one session, surfaced by the prior doccheck worker
pass's pytest baseline (2 pre-existing failures + 1 pre-existing collection error, both flagged as
unrelated-but-real at the time).

## matplotlib missing from requirements.txt and the venv

`src/news/engine/proxy_riding/reporter.py`, `src/news/engine/proxy_pool/janitor.py`, and
`src/news/engine/browser_reporter.py` each lazy-import `matplotlib.pyplot` at the plot-generation
step of their report writers — never at module load, so the gap was invisible until a real job
report tried to render a plot. `dev/news_pipeline/coindesk_proxy_riding/test_sigint_report.py`
caught it: `test_abort_interrupted_sigint`/`_sigterm` assert `cumulative.png` exists after a real
report write, which silently no-ops (WARN-logged, not raised) when the import fails. Confirmed via
`git ls-files`/`grep`: `matplotlib` was never in `requirements.txt` and not importable in the venv
before this fix. Added `matplotlib` to `requirements.txt` (unpinned, matching every other entry in
that file — no package there carries a version pin) and installed it via `./venv/bin/pip install
matplotlib` — this repo's worktrees share one venv via a symlink
(`<worktree>/venv -> .../websearch/venv`), so the install is repo-wide, not worktree-local. Verified:
`test_sigint_report.py` 2/2 passing post-install, real `job.md` + `cumulative.png` written.

## dev/scrape_pipeline/garbage_eval/10_live_garbage_test.py — dead script, deleted not repaired

Imported `log_scrape_failure` from `src/scraper/scrape_url.py`, a symbol removed in the 2026-08-05
content-judgment-removal work (`src/scraper/DOCS.md`'s own Contract section documents that removal).
The script live-tested `is_garbage_content()` against real SearXNG search results and hardcoded edge
cases — a feature this module no longer owns the way the script assumed (content judgment moved to
the calling agent; `is_garbage_content` now only serves `src/crawler/crawl_site.py`'s unattended batch
crawl). Decided with the user: delete rather than repair — the script's premise (an agent-facing live
integration test of automatic garbage verdicts) doesn't map cleanly onto the post-removal contract,
and no other file imports or invokes it (grepped repo-wide before deletion). Removed the file and its
`DOCS.md` module entry + the now-stale "10 runs live integration checks" clause from the `Role`
paragraph; the 3 remaining `garbage_eval` modules (07-09) are unaffected and keep testing
`is_garbage_content()` itself, which is still current.

## Verification

Full suite (`./venv/bin/python -m pytest -q`, no `--ignore` needed once the dead-import collection
error was gone): 228 passed, 0 failed, 0 errors — up from the prior session's 226 passed / 2 failed /
1 collection error baseline, with the delta being exactly these two fixes (2 previously-failing tests
now pass; the 1 broken collection module is gone rather than fixed).
