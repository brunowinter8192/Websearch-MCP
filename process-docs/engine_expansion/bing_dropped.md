# Bing Dropped (2026-05-04)

**Engine:** `src/search/engines/bing.py` (deleted 2026-05-04); `BingEngine` import + ENGINES entry removed from `src/search/search_web.py`
**Dropped by:** Bruno verdict

**Reason:** No added value over DuckDuckGo. DDG's web index IS Bing — DDG queries Bing under the hood and re-ranks with its own snippet generation. Adding Bing-direct gave us only snippet-and-ranking variation on the same URL set, not actual coverage. Plus Bing's selector `#b_results .b_algo` had drifted (DOM change since the engine was wired) and required a repair effort that didn't pay back. DDG remains as the Bing-index access path; a Bing-direct re-eval can be revisited later if a clear use case emerges (own snippet quality vs. DDG, Bing News / Images sub-pipelines).
