# Declaring the undeclared `curl_cffi` dependency (2026-08-04)

First milestone of a hardening effort on `src/crawler/pipe_scraper.py` (the mass-capture scrape path). Scope: dependency repair only, no logic touched.

Why `curl_cffi` and not `httpx`: the later milestones add a fallback acquisition path for the class of failure where the browser is the WEAKER client than a plain HTTP one (`process-docs/scrape_toolbox/` records that reasoning and why the same fallback was dropped on the ad-hoc path). A fallback only earns its place if it carries a browser TLS fingerprint — `cffi.Session(impersonate="chrome")`. `process-docs/news_pipeline/` holds the measurement behind that: `impersonate=chrome` got 80 of 425 proxies through Cloudflare with HTTP 200, where another client managed 0 of 17202, the isolating variable being the TLS fingerprint alone.

## Problem

`src/news/engine/proxy_pool/fetch.py:3` imports `curl_cffi` (`from curl_cffi import requests as cffi`), consumed downstream by `src/news/engine/proxy_pool/loop.py` and `src/news/platforms/theblock/discover.py`. The package was absent from `requirements.txt` and from the venv. Consequence: `pytest tests/ -q` aborted at collection with `Interrupted: 2 errors during collection` — `tests/test_theblock_clean_pass.py` and `tests/test_theblock_discover.py` both failed to import (`ModuleNotFoundError: No module named 'curl_cffi'`), which blocks collecting the suite as a whole (any single collection error interrupts pytest's full-suite run).

## Pre-existing baseline (must not regress)

With the two theblock modules excluded (`--ignore=tests/test_theblock_clean_pass.py --ignore=tests/test_theblock_discover.py`): 9 failed, 86 passed. The 9 pre-existing failures span `tests/test_proxy_pool.py` (2, `run_loop` refresh/pool-swap behavior) and `tests/test_query_logger.py` (7, `AttributeError`/timing assertions unrelated to `curl_cffi`) — explicitly out of scope for this milestone.

## Fix

Added `curl_cffi` as a bare, unpinned line to `requirements.txt` (matching the file's existing no-pin convention across all 10 other entries) and installed it into the shared venv via `./venv/bin/pip install curl_cffi`. PyPI resolved `curl_cffi==0.16.0` (cp310-abi3, macOS arm64 wheel) — no other manifest/lock file in the repo names a version to match against.

## Verification

Full suite before: 2 collection errors, 0 tests run.
Full suite after: `9 failed, 105 passed in 1.24s`, 0 collection errors.
Diffed the `FAILED` line lists pre/post (baseline run with theblock ignored vs full post-change run) — identical set, byte-for-byte. The 9 pre-existing failures are untouched; 19 new tests now collect and pass (`test_theblock_clean_pass.py` + `test_theblock_discover.py`, run standalone: 19 passed, 0 failed) — 86 + 19 = 105 confirms no other test's outcome shifted.

Separately verified after the merge, since the later fallback path rests on it: a live `cffi.Session(impersonate="chrome")` request against `httpbin.org/user-agent` returned HTTP 200 and reported `Chrome/146.0.0.0` on macOS — no Python-client fingerprint. Noted for whoever wires the fallback: 0.16.0 impersonates Chrome 146 while the real Chrome on this machine was 150.0.7871.187 as of this date. Irrelevant for a pure HTTP client (there is no browser kernel the UA must agree with), but it would matter if browser and fallback ever got mixed inside one acquisition.

## Scope note

`src/crawler/pipe_scraper.py` itself was not touched in this milestone — this was purely clearing the collection blocker so the full suite (which the later hardening milestones will need to run cleanly) is collectible at all.
