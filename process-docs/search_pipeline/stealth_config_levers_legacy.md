# Pydoll Stealth Configuration — Lever Inventory (undated legacy snapshot)

**Provenance:** consolidated from a stray `src/search/STEALTH_CONFIG.md` file found during a doc-structure audit; no session date was recorded in the original file. Internal content (generic `browser.py` pydoll setup, references to "earlier SearXNG N-request run") places it in the pre-engine-cut era (before 2026-04-15). Kept for two findings not otherwise recorded — the Client-Hints auto-sync discovery and the specific proposed-patch list below. Not a current-state document; check `src/search/browser.py` for what is actually implemented today.

## 1. Browser Launch Options (ChromiumOptions)

Set in `browser.py` → `build_options()`. Applied at Chrome startup.

| Lever | Value at time of writing | What it does |
|-------|--------------|-------------|
| `--user-agent=...` | Chrome 146 Mac UA | Sets UA string in HTTP headers |
| `--disable-blink-features=AutomationControlled` | ON | Removes `navigator.webdriver=true` flag |
| `--window-size=1920,1080` | ON | Sets viewport, affects fingerprint |
| `webrtc_leak_protection` | ON | Blocks WebRTC IP leak via `disable_non_proxied_udp` |
| `headless` | ON (env override) | Headless vs headed. Headless has detection vectors |
| `--user-data-dir=...` | `~/.searxng-mcp/browser-session` | Persistent session (cookies, localStorage) |
| `block_popups` | ON | Blocks popup windows |
| `block_notifications` | ON | Blocks notification prompts |
| `--proxy-server=...` | NOT SET | Proxy with optional credential auth |
| `page_load_state` | COMPLETE | When to consider page loaded |
| `browser_preferences` | profile, safebrowsing, autofill, search, credentials | Make Chrome profile look like real user |

## 2. JS Fingerprint Patches (injected per tab)

Set in `browser.py` → `JS_FINGERPRINT_PATCHES`, via `Page.addScriptToEvaluateOnNewDocument`.

| Lever | Value at time of writing | What it does |
|-------|--------------|-------------|
| `screen.width/height` | 1920x1080 | Override screen dimensions |
| `screen.colorDepth/pixelDepth` | 30 | Mac Retina values |
| `window.devicePixelRatio` | 2 | Retina Mac |
| `window.outerWidth/outerHeight` | innerWidth / innerHeight+85 | Simulates browser chrome |
| `getComputedStyle` patch | Proxy on color | Fixes headless CSS color detection |

Not implemented at time of writing: `navigator.languages`, `navigator.platform`, `navigator.hardwareConcurrency`, `navigator.deviceMemory`, `Permissions.query` override, WebGL vendor/renderer override, Canvas fingerprint noise.

## Key Finding: Pydoll Auto-Syncs Client Hints

Pydoll automatically syncs UA + Client Hints when `--user-agent=` is set:
1. Parses `--user-agent` arg to extract OS, browser, version.
2. Calls CDP `Emulation.setUserAgentOverride()` with full metadata.
3. Generates proper `Sec-CH-UA*` Client Hints matching the UA.
4. Injects JS property overrides for `navigator.vendor`, `navigator.appVersion`.
5. Applies to initial tab AND all new tabs.

Conclusion at the time: Client Hints mismatch was ruled out as the cause of a then-open Google/Bing 0-results investigation (root cause not resolved in this file; superseded by later engine-specific work in this folder).

## Proposed Patches Not Yet Applied (at time of writing)

```python
# Launch options
options.add_argument('--lang=en-US')
options.add_argument('--no-first-run')
options.add_argument('--no-default-browser-check')

# Browser preferences
options.browser_preferences = {
    'profile': {
        'created_by_version': '146.0.7680.154',
        'creation_time': str(int(time.time()) - 60*86400),
        'exit_type': 'Normal',
        'exited_cleanly': True,
    },
    'safebrowsing': {'enabled': True},
    'autofill': {'enabled': True},
    'search': {'suggest_enabled': True},
    'enable_do_not_track': False,
    'credentials_enable_service': True,
    'intl': {'accept_languages': 'en-US,en'},
}
```

Additional JS patches proposed: `navigator.languages = ["en-US", "en"]`, `navigator.platform = "MacIntel"`, `navigator.hardwareConcurrency = 10`, `navigator.deviceMemory = 8`.

Per-engine context isolation proposed: use `browser.new_context()` instead of `browser.new_tab()` for isolated cookie jars per engine, to prevent cross-engine tracking.
