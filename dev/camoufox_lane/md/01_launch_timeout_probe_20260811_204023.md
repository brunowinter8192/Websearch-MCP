# Camoufox Launch-Timeout Enforcement Probe — 20260811_204023

LOW run: timeout=1ms through the production chain (kwargs -> camoufox.launch_options -> AsyncCamoufox(from_options=...)). CONTROL run: same chain, timeout=30000ms (the production default, _PLAYWRIGHT_DEFAULT_TIMEOUT_MS in src/scraper/camoufox_scrape.py).

## Results

| Run | timeout_ms | outcome | wall time | exception type |
|---|---|---|---|---|
| LOW (1ms) | 1 | exception | 0.293s | TimeoutError |
| CONTROL (30000ms, production default) | 30000 | launched | 1.465s | None |

## LOW run — verbatim traceback

```
Traceback (most recent call last):
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/camoufox-budget/dev/camoufox_lane/01_launch_timeout_probe.py", line 66, in attempt_launch
    async with AsyncCamoufox(from_options=resolved) as browser:
               ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/venv/lib/python3.14/site-packages/camoufox/async_api.py", line 41, in __aenter__
    self.browser = await AsyncNewBrowser(_playwright, **self.launch_options)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/venv/lib/python3.14/site-packages/camoufox/async_api.py", line 125, in AsyncNewBrowser
    browser = await playwright.firefox.launch(**from_options)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/venv/lib/python3.14/site-packages/playwright/async_api/_generated.py", line 16307, in launch
    await self._impl_obj.launch(
    ...<17 lines>...
    )
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py", line 98, in launch
    await self._channel.send(
        "launch", TimeoutSettings.launch_timeout, params
    )
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/venv/lib/python3.14/site-packages/playwright/_impl/_connection.py", line 69, in send
    return await self._connection.wrap_api_call(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/venv/lib/python3.14/site-packages/playwright/_impl/_connection.py", line 559, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.TimeoutError: BrowserType.launch: Timeout 1ms exceeded.

```

## CONTROL run

outcome=launched, wall=1.465s