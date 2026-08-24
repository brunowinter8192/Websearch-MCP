# Relocation: tests/ -> dev/tests/, bare-pytest collection wiring (milestone 2, 2026-08-24)

Follow-up to this area's catching-power triage entry (same date): relocated the 208 kept tests
from `tests/` to `dev/tests/` and made the suite collectible by the bare `pytest` entry script
(no `python -m`, no cwd-injection reliance) from the repo root.

## Change

- `git mv tests/ dev/tests/` — 13 test modules + `__init__.py`, no content changes beyond the one
  fix below.
- New root `pytest.ini`, exactly three options:
  - `testpaths = dev/tests`
  - `pythonpath = .` — required because `rootdir` alone does NOT touch `sys.path`; without it,
    `from src...` imports fail under the bare `pytest` binary (only `python -m pytest` would work,
    since `-m` adds cwd to `sys.path` itself).
  - `norecursedirs = .* *.egg _darcs build CVS dist node_modules venv {arch} upstream` — the
    pytest built-in defaults written out explicitly (setting `norecursedirs` REPLACES the
    defaults, it does not extend them) plus `upstream`. `norecursedirs` matches directory
    BASENAMES, not full paths, so a single `upstream` entry guards any vendored clone at that
    basename anywhere under the tree — concretely, the jhao104 probe's vendored clone at
    `dev/news_pipeline/theblock/jhao104/upstream/` (materialized by that probe's own `setup.sh`,
    not committed) would otherwise break bare-pytest collection if it were ever walked.

## Bug surfaced by the move: repo-root path depth

`test_query_logger.py::test_log_drilldown_all_cache_status_and_pool_combinations` spawns a
subprocess that imports `cli` from the repo root, located via `Path(__file__).parent.parent` —
correct when the file was one level below root (`tests/`), broken once it became two levels below
root (`dev/tests/`): the subprocess raised `ModuleNotFoundError: No module named 'cli'`. Fixed by
adding one `.parent` (three total). Treated as collection-wiring repair (a mechanical depth
correction forced by the move itself), not a test-logic change — no assertion was touched.

## Verification

`./venv/bin/pytest` (bare entry script, run from repo root, no args) — chosen deliberately over
`python -m pytest` because `-m` adds the invocation cwd to `sys.path` itself and would have
masked a broken `pythonpath` option. Result: **208 passed, 0 failed**, 0 collection errors.
Header: `rootdir: <repo>/.claude/worktrees/test-triage`, `configfile: pytest.ini`,
`testpaths: dev/tests`. The vendored `upstream/` clone was not materialized on disk during this
session (created lazily by `jhao104/setup.sh`), so its exclusion could not be observed directly by
a collection run against a present directory — the guard is structural (`norecursedirs` matches
by basename regardless of location; `testpaths` also scopes collection to `dev/tests` alone), not
verified against a live instance of that directory in this session.

## Follow-up flagged

Any future relocation of `dev/tests/` must re-check every file for `Path(__file__).parent`-style
repo-root resolution — the depth is baked into the chain, not derived from a fixture or constant.
Noted as a `dev/tests/DOCS.md` Gotcha for discoverability at the file level.
