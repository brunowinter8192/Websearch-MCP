# pydoll_noncoop_teardown — Phase 1: Teardown Design

## Problem

`search_ms=65005ms` observed for `semantic_scholar` (watchdog=5.0s) with status
`TIMEOUT_NONCOOP`. Engine correctly returns 0 results/TIMEOUT to the caller, but:
- The whole `asyncio.gather` batch hangs for 65s while the engine's cleanup runs.
- Chrome renderer process remains alive for that duration (potential CPU leak).

## Code Analysis

### Hang chain (verified from source)

Files read: `src/search/search_web.py`, `src/search/browser.py`, all 5 pydoll engine files,
`pydoll/browser/tab.py`, `pydoll/browser/chromium/base.py`,
`pydoll/commands/target_commands.py`, `pydoll/connection/connection_handler.py`.

**Step-by-step:**

1. `asyncio.wait_for(engine.search_with_reason(...), timeout=5.0)` in `_engine_with_timing`.
2. Engine at `await tab.go_to(...)` or `await tab.execute_script(...)` — Chrome renderer
   is hung (page never fully loads, JS never returns, etc.).
3. 5s watchdog fires → `task.cancel()` → `CancelledError` raised inside pydoll's
   `ConnectionHandler.execute_command` at `await asyncio.wait_for(future, timeout=60)`.
   `CancelledError` propagates up through `execute_script` / `go_to` to the engine's
   `try/finally` block.
4. **`finally: await tab.close()` runs.**
   - `tab.close()` calls `tab._execute_command(PageCommands.close())`.
   - `tab._execute_command` → `ConnectionHandler(port, target_id).execute_command(cmd)`.
   - This is the **tab-specific** WebSocket connection — the same channel Chrome isn't
     responding on.
   - `Page.close` sent → Chrome renderer is still busy → no response for 60s (pydoll's
     internal `asyncio.wait_for(future, timeout=60)` fires → `CommandExecutionTimeout`).
5. `tab.close()` raises `CommandExecutionTimeout` → propagates out of engine task.
6. `asyncio.wait_for` sees the inner task is done → raises `TimeoutError` to
   `_engine_with_timing`.
7. **Total wall time: 5s watchdog + ~60s pydoll `Page.close` fallback = ~65s.**

**Connection architecture (verified):**

| Channel | Constructor | Used by |
|---|---|---|
| Tab connection | `ConnectionHandler(port, target_id)` | `tab._execute_command` / `tab.close()` |
| Browser connection | `ConnectionHandler(port)` | `_browser._execute_command` |

`_browser._execute_command(TargetCommands.close_target(target_id))` goes over the
**browser connection** — a separate WebSocket to the Chrome browser process. Chrome's
browser process handles `Target.closeTarget` by terminating the renderer process, regardless
of renderer state. Confirmed: `TargetCommands.close_target()` is in `pydoll.commands`
(exported by `__init__.py`); `_browser._execute_command` calls
`self._connection_handler.execute_command(command, timeout=60)` on the browser-level handler.

Tab target_id is always populated: `tab._target_id` is set at `Tab.__init__` and is non-None
after any `new_tab()` call.

## Option A vs B

### Option A — change the engine `finally` block

Replace `await tab.close()` with `await kill_tab(tab)` in all 5 pydoll engine
`search_with_reason()` methods. `kill_tab()` lives in `browser.py`.

- `kill_tab` calls `_browser._execute_command(TargetCommands.close_target(target_id))` +
  cleans `_browser._tabs_opened`.
- Browser connection → Chrome browser process → renderer terminated in <100ms.
- Both problems solved in one change: (a) orphaned renderer eliminated, (b) 65s hang
  eliminated — the `finally` block completes in ~watchdog + <100ms instead of watchdog + 60s.
- No separate tracking needed: `tab` is available in the `finally` block.

### Option B — gathered teardown after `asyncio.gather()`

Kill orphaned tabs after `gather()` returns. Problem: `gather()` does NOT return until all
tasks settle. A NONCOOP engine's task won't settle until its `finally: await tab.close()`
completes — which is exactly the 60s hang. Option B defers the kill until AFTER the hang.

Any surgical Option B that avoids the hang requires tracking which tab each engine opened in
a shared dict and calling `Target.closeTarget` from `_engine_with_timing`'s
`except asyncio.TimeoutError` block. This is more invasive than Option A with identical effect.

**Decision: Option A.** The `finally` block is the canonical cleanup site and has direct
access to `tab`. Changing one function call per engine is minimal scope.

## kill_tab Design

```python
async def kill_tab(tab) -> None:
    global _browser
    target_id = getattr(tab, '_target_id', None)
    if _browser is None or target_id is None:
        return
    try:
        await asyncio.wait_for(
            _browser._execute_command(TargetCommands.close_target(target_id)),
            timeout=5.0,
        )
    except Exception as e:
        logger.warning("kill_tab close_target failed (target_id=%s): %s", target_id, e)
    finally:
        if _browser is not None:
            _browser._tabs_opened.pop(target_id, None)
```

### 5s cap on close_target

The browser-level connection is a separate WebSocket and the browser process handles
`Target.closeTarget` without involving the renderer. In practice this returns in <100ms.

The 5s cap guards against an extreme edge case: Chrome process itself unresponsive
(OOM kill, kernel hang). Without the cap, `_browser._execute_command` would wait 60s
(its internal default). With the cap: worst case = watchdog + 5s instead of watchdog + 60s.
If the 5s cap fires, the `finally` block still runs and cleans `_tabs_opened`. The renderer
may still be alive in this extreme case — `kill_stale_chrome()` (pkill on session-dir)
remains the nuclear OS-level fallback.

## Verification

`dev/search_pipeline/24_pydoll_teardown_verify.py` — three tests, all PASS
(`teardown_verify_20260531_201523.md`):

**Hang simulation:** `about:blank` + `execute_script("return new Promise(function() {})",
await_promise=True)`. Renderer waits for a never-resolving Promise; browser process stays
fully responsive → `close_target` over browser connection completes in <100ms after cancel.
`chrome://hang` was rejected: it stalls Chrome IPC to the hung tab, which also slows
`close_target` on the browser connection — not the production scenario.

**T1 — single hung tab:** wall=5002ms (vs old ~65000ms), registry clean → PASS
**T2 — normal tab:** wall=43ms, registry clean → PASS
**T3 — parallel batch (5× hung via `asyncio.gather`):** mirrors production 5-engine fanout.
Measured via `_browser.get_targets()` (CDP `Target.getTargets`, type=page).
wall=5002ms (vs old 5×65s=325s), CDP targets Δ=+0 (no orphans), registry clean → PASS
