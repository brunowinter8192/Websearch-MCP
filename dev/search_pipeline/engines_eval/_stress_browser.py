"""Pydoll browser/tab operations for 28_stress_test.py."""

# INFRASTRUCTURE
import asyncio
import json
import time
from pathlib import Path

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.types import CookieSameSite

from stealth_config import StealthConfig
from _stealth_builders import build_chrome_args, build_js_patches
from engine_selectors import ENGINE_SELECTORS
from _stress_types import QueryResult

SESSION_BASE = str(Path.home() / ".searxng-mcp" / "stress-test")


# Build browser with engine-specific session dir, proxy, and consent cookies
async def start_browser(engine: str, config: StealthConfig):
    eng_cfg = ENGINE_SELECTORS[engine]["config"]
    engine_slug = engine.replace(" ", "_")
    session_dir = f"{SESSION_BASE}/{engine_slug}"

    options = ChromiumOptions()
    options.headless = config.headless
    options.add_argument(f"--user-data-dir={session_dir}")
    options.block_popups = True
    options.block_notifications = True
    options.webrtc_leak_protection = config.webrtc_leak_protection
    options.browser_preferences = config.browser_preferences

    if eng_cfg["proxy"]:
        options.add_argument(f"--proxy-server={eng_cfg['proxy']}")

    for arg in build_chrome_args(config):
        options.add_argument(arg)

    browser = Chrome(options)
    tab = await browser.start()
    await inject_consent_cookies(tab)
    return browser


# Set Google/Scholar SOCS consent cookie via CDP
async def inject_consent_cookies(tab) -> None:
    cookie = ENGINE_SELECTORS["google"]["consent_cookie"]
    await tab._execute_command(NetworkCommands.set_cookie(
        name=cookie["name"],
        value=cookie["value"],
        domain=cookie["domain"],
        path=cookie["path"],
        secure=cookie["secure"],
        same_site=CookieSameSite.LAX,
    ))


# Open tab (or isolated context), navigate, handle captcha, parse — return QueryResult
async def run_one_tab(browser, query: str, engine: str, config: StealthConfig) -> QueryResult:
    cfg = ENGINE_SELECTORS[engine]
    eng_cfg = cfg["config"]
    start = time.monotonic()
    tab = None
    context_id = None

    try:
        if eng_cfg["use_context"]:
            context_id = await browser.create_browser_context()
            tab = await browser.new_tab(browser_context_id=context_id)
        else:
            tab = await browser.new_tab()

        js = build_js_patches(config)
        await tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=js,
                run_immediately=True,
            )
        )

        url = cfg["url_fn"](query)
        await tab.go_to(url, timeout=30)
        current = await tab.current_url

        if cfg.get("captcha_path") and cfg["captcha_path"] in current:
            elapsed = time.monotonic() - start
            return QueryResult(query, engine, 0, elapsed, "CAPTCHA", "")

        if cfg.get("consent_domain") and cfg["consent_domain"] in current:
            elapsed = time.monotonic() - start
            return QueryResult(query, engine, 0, elapsed, "consent_redirect", "")

        if eng_cfg["captcha_detect_js"]:
            raw = await tab.execute_script(eng_cfg["captcha_detect_js"])
            detected = _extract_nested(raw)
            if detected:
                elapsed = time.monotonic() - start
                return QueryResult(query, engine, 0, elapsed, "slider_captcha", "")

        await asyncio.sleep(eng_cfg["settle_seconds"])
        items = await parse_results(tab, cfg)
        elapsed = time.monotonic() - start
        first_title = items[0].get("title", "")[:60] if items else ""
        return QueryResult(query, engine, len(items), elapsed, None, first_title)

    except Exception as e:
        elapsed = time.monotonic() - start
        return QueryResult(query, engine, 0, elapsed, str(e)[:120], "")

    finally:
        if eng_cfg["use_context"] and context_id:
            try:
                await browser.delete_browser_context(context_id)
            except Exception:
                pass
        elif tab:
            try:
                await tab.close()
            except Exception:
                pass


# Execute parse_js and return list of result dicts
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
