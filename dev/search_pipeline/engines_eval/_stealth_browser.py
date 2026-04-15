"""Browser execution functions for 27_stealth_test.py."""

# INFRASTRUCTURE
import asyncio
import json
from pathlib import Path

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.types import CookieSameSite

from stealth_config import StealthConfig
from _stealth_builders import build_chrome_args, build_js_patches
from engine_selectors import ENGINE_SELECTORS

SESSION_DIR = str(Path.home() / ".searxng-mcp" / "stealth-test-session")
MAX_WAIT_CYCLES = 15
WAIT_INTERVAL = 1.0
SLEEP_WAIT = 3.0


# Build ChromiumOptions from config and start browser, return (browser, tab)
async def start_browser(config: StealthConfig, engine_cfg: dict):
    options = ChromiumOptions()
    options.headless = config.headless
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.block_popups = True
    options.block_notifications = True
    options.webrtc_leak_protection = config.webrtc_leak_protection
    options.browser_preferences = config.browser_preferences

    for arg in build_chrome_args(config):
        options.add_argument(arg)

    browser = Chrome(options)
    tab = await browser.start()
    await apply_js_patches(tab, config)
    await inject_consent_cookie(tab, engine_cfg)
    return browser, tab


# Inject consent cookie from engine config via CDP if present
async def inject_consent_cookie(tab, engine_cfg: dict) -> None:
    cookie = engine_cfg.get("consent_cookie")
    if not cookie:
        return
    await tab._execute_command(NetworkCommands.set_cookie(
        name=cookie["name"],
        value=cookie["value"],
        domain=cookie["domain"],
        path=cookie["path"],
        secure=cookie["secure"],
        same_site=CookieSameSite.LAX,
    ))


# Inject fingerprint patch script via Page.addScriptToEvaluateOnNewDocument
async def apply_js_patches(tab, config: StealthConfig) -> None:
    js = build_js_patches(config)
    await tab._execute_command(
        PageCommands.add_script_to_evaluate_on_new_document(
            source=js,
            run_immediately=True,
        )
    )


# Navigate engine, handle consent, wait for results, parse
async def run_engine(tab, query: str, cfg: dict, detection: dict) -> tuple[list, dict]:
    import sys
    url = cfg["url_fn"](query)

    await tab.go_to(url, timeout=30)
    current = await tab.current_url

    if cfg.get("consent_domain") and cfg["consent_domain"] in current:
        detection["consent"] = True
        print(f"CONSENT PAGE detected — cookie injection may have failed", file=sys.stderr)

    if cfg.get("captcha_path") and cfg["captcha_path"] in current:
        detection["captcha"] = True
        print(f"CAPTCHA detected", file=sys.stderr)
        return [], detection

    found = await wait_for_results(tab, cfg)
    if not found:
        print(f"Timeout — no results loaded", file=sys.stderr)

    results = await parse_results(tab, cfg)
    if not results:
        detection["zero_results"] = True

    return results, detection


# Wait for results using engine's strategy (JS poll or fixed sleep)
async def wait_for_results(tab, cfg: dict) -> bool:
    if cfg["wait"] == "sleep":
        await asyncio.sleep(SLEEP_WAIT)
        return True

    for _ in range(MAX_WAIT_CYCLES):
        raw = await tab.execute_script(cfg["wait_js"])
        count = _extract_nested(raw)
        if count and int(count) > 0:
            return True
        await asyncio.sleep(WAIT_INTERVAL)
    return False


# Run parse JS and return list of result dicts
async def parse_results(tab, cfg: dict) -> list[dict]:
    raw = await tab.execute_script(cfg["parse_js"])
    value = _extract_nested(raw)
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# Extract value from nested CDP result structure
def _extract_nested(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None
