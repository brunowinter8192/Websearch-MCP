#!/usr/bin/env python3
"""Date-availability probe — Milestone 2 measurement for the 8 DOM-scraped web engines
(google, duckduckgo, mojeek, startpage, brave, bing, yandex, lobsters).

Question: does the live result page carry a date, and if so how (dedicated element vs
snippet-text-only vs nowhere)? Not a feature change — no src/ touched, no wiring.

Self-contained: does NOT import src/ (dev-script isolation, matches 25/26/28/29/30_*_probe.py) —
the pydoll Chrome session setup and each engine's navigation/wait/diagnose logic below are an
inline copy of the CURRENT shape in src/search/browser.py + src/search/engines/*.py, not a
shared import — the probe keeps measuring even if src/ changes underneath it later.

Evidence capture, one JS pass per container (covers case 1 and case 2 together):
  - <time> elements (tag + datetime attribute + text) -> dedicated-element evidence
  - class/id tokens matching a WORD-BOUNDARY regex for date/time/age/publish/when/ago
    (not a raw substring — substring would false-positive on 'update'/'candidate'/'validate')
  - full container text (600 chars) -> snippet-text-only date-prefix evidence
  - outerHTML head (3000 chars) -> structural context

Pacing: self-imposed politeness gap between requests to the SAME engine — this script does NOT
go through src/search/rate_limiter.py at all (self-contained), so there is no quota being
respected here, just avoiding a rapid-fire burst against a live server. If an engine is non-OK
across ALL primary queries, one retry follows a MINUTES-scale cooldown (not seconds) — a short
gap cannot distinguish a probe-induced block from an engine that was already in a cooled-down
state from unrelated earlier activity this session. google, duckduckgo, and brave are flagged
up front as having returned 0 results in an EARLIER live run this session (unrelated to this
probe) — a repeat non-OK on those three is annotated as pre-existing, not attributed to the probe.
"""

# INFRASTRUCTURE
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, parse_qs, urlparse

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import PageCommands, TargetCommands
from pydoll.commands.network_commands import NetworkCommands
from pydoll.protocol.network.types import CookieSameSite

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"

# Inline copy of the CURRENT src/search/browser.py session shape
SESSION_DIR = str(Path.home() / ".websearch" / "browser-session")
REAL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.7680.154 Safari/537.36"
)
JS_FINGERPRINT_PATCHES = """
(function() {
    Object.defineProperty(screen, 'width', { get: () => 1920 });
    Object.defineProperty(screen, 'height', { get: () => 1080 });
    Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
    Object.defineProperty(screen, 'availHeight', { get: () => 1057 });
    Object.defineProperty(screen, 'colorDepth', { get: () => 30 });
    Object.defineProperty(screen, 'pixelDepth', { get: () => 30 });
    Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 });
    Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
    Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight + 85 });
})();
(function() {
    var _origGCS = window.getComputedStyle;
    window.getComputedStyle = function(element, pseudoElt) {
        var style = _origGCS.apply(this, arguments);
        return new Proxy(style, {
            get: function(target, name) {
                var value = target[name];
                if (name === 'color' && value === 'rgb(255, 0, 0)') { return 'rgb(0, 102, 204)'; }
                return typeof value === 'function' ? value.bind(target) : value;
            }
        });
    };
})();
"""

# Self-imposed politeness gap — NOT derived from src/search/rate_limiter.py (this script never
# goes through it). 20s between the 3 primary queries to the same engine; a MINUTES-scale gap
# (not seconds) before a retry, since a short gap cannot tell a probe-induced block apart from a
# pre-existing cooldown from earlier unrelated activity this session.
INTER_QUERY_DELAY_S = 20.0
INTER_ENGINE_DELAY_S = 3.0
RETRY_COOLDOWN_S = 180.0

# Flagged from an EARLIER live run this session (search_web across all 14 engines) — these three
# returned 0 results THEN, unrelated to this probe. A repeat non-OK here is annotated, not fresh.
PRE_FLAGGED_EMPTY_EARLIER = {"google", "duckduckgo", "brave"}

CONTAINER_LIMIT = 3

QUERIES = [
    ("openai gpt-5 release reaction", "news-en"),
    ("federal reserve interest rate decision 2026", "news-en"),
    ("Photosynthese Prozess pflanzliche Zellatmung", "reference-de"),
]

BLOCK_MARKERS = [
    "captcha", "unusual traffic", "verify you are human", "are you a robot",
    "access denied", "checking your browser", "temporarily blocked",
    "too many requests", "rate limit exceeded", "automated queries",
    "schieberegler ziehen", "drag the slider", "proof of work",
    "ungewöhnlichen datenverkehr", "roboter", "bestätigen sie, dass sie ein mensch",
    "confirm you are not a robot", "unusual activity", "smartcaptcha",
    "подтвердите, что запросы", "подозрительн", "ты робот",
]

SOCS_NAME = "SOCS"
SOCS_VALUE = "CAISHAgCEhJnd3NfMjAyNjA0MDctMCAgIBgEIAEaBgiA_fC8Bg"
SOCS_DOMAIN = ".google.com"
GOOGLE_CONSENT_DOMAIN = "consent.google.com"
GOOGLE_CAPTCHA_PATH = "/sorry/"
DDG_CAPTCHA_SELECTOR = "form#challenge-form"
STARTPAGE_HOME_URL = "https://www.startpage.com/"
YANDEX_BLOCK_MARKERS = ("showcaptcha", "checkcaptcha", "/captcha")

# engine -> container selector used both for the wait-poll and the date-evidence dump
CONTAINER_SELECTOR = {
    "google":     "div.MjjYud",
    "duckduckgo": "#links > div.web-result",
    "mojeek":     "ul.results-standard > li",
    "startpage":  "div.result",
    "brave":      'div[data-type="web"]',
    "bing":       "li.b_algo",
    "yandex":     "li.serp-item",
    "lobsters":   "li.story",
}

_browser = None


# ORCHESTRATOR

async def run_probe() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        for engine in CONTAINER_SELECTOR:
            print(f"=== {engine} ===", file=sys.stderr)
            engine_records = []
            for qi, (query, axis) in enumerate(QUERIES):
                print(f"  [{qi + 1}/{len(QUERIES)}] ({axis}) {query}", file=sys.stderr)
                rec = await run_engine_query(engine, query, axis, retry=False)
                engine_records.append(rec)
                print(f"    -> {rec['status']} containers={rec['container_count']}", file=sys.stderr)
                if qi < len(QUERIES) - 1:
                    await asyncio.sleep(INTER_QUERY_DELAY_S)
            if all(r["status"] != "OK" for r in engine_records):
                print(f"  all {len(QUERIES)} primary queries non-OK — cooling down {RETRY_COOLDOWN_S:.0f}s before retry", file=sys.stderr)
                await asyncio.sleep(RETRY_COOLDOWN_S)
                retry_rec = await run_engine_query(engine, QUERIES[0][0], QUERIES[0][1], retry=True)
                print(f"    retry -> {retry_rec['status']} containers={retry_rec['container_count']}", file=sys.stderr)
                engine_records.append(retry_rec)
            records.extend(engine_records)
            await asyncio.sleep(INTER_ENGINE_DELAY_S)
    finally:
        await close_browser()

    report_path = write_report(records)
    print(f"\nReport: {report_path}", file=sys.stderr)


# FUNCTIONS

# --- Chrome session (inline copy of src/search/browser.py shape) ---

def _kill_stale_chrome():
    subprocess.run(["pkill", "-f", f"user-data-dir={SESSION_DIR}"], capture_output=True)


def _build_options() -> ChromiumOptions:
    options = ChromiumOptions()
    options.headless = not os.environ.get("WEBSEARCH_HEADED")
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.block_popups = True
    options.block_notifications = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.webrtc_leak_protection = True
    options.add_argument(f"--user-agent={REAL_USER_AGENT}")
    options.add_argument("--window-size=1920,1080")
    return options


async def _apply_fingerprint_patches(tab):
    await tab._execute_command(
        PageCommands.add_script_to_evaluate_on_new_document(source=JS_FINGERPRINT_PATCHES, run_immediately=True)
    )


async def _new_tab():
    global _browser
    if _browser is None:
        _kill_stale_chrome()
        _browser = Chrome(_build_options())
        await _browser.start()
    tab = await _browser.new_tab()
    await _apply_fingerprint_patches(tab)
    return tab


async def _kill_tab(tab) -> None:
    global _browser
    target_id = getattr(tab, "_target_id", None)
    if _browser is None or target_id is None:
        return
    try:
        await asyncio.wait_for(_browser._execute_command(TargetCommands.close_target(target_id)), timeout=5.0)
    except Exception as e:
        logging.warning("kill_tab failed (target_id=%s): %s", target_id, e)
    finally:
        _browser._tabs_opened.pop(target_id, None)


async def close_browser() -> None:
    global _browser
    if _browser is not None:
        await _browser.stop()
        _browser = None


def _extract_value(result):
    try:
        return result["result"]["result"]["value"]
    except (KeyError, TypeError):
        return None


async def _wait_for(tab, selector: str, cycles: int, interval: float) -> bool:
    js = f"return document.querySelectorAll('{selector}').length"
    for _ in range(cycles):
        val = _extract_value(await tab.execute_script(js))
        if val and int(val) > 0:
            return True
        await asyncio.sleep(interval)
    return False


_JS_GENERIC_DIAGNOSE = """
var body = document.body ? document.body.innerText.toLowerCase() : '';
var title = document.title.toLowerCase();
var markers = %s;
var hit = null;
for (var i = 0; i < markers.length; i++) {
    if (body.indexOf(markers[i]) !== -1 || title.indexOf(markers[i]) !== -1) { hit = markers[i]; break; }
}
return JSON.stringify({marker: hit, url: window.location.href, ready_state: document.readyState, title: document.title});
""" % json.dumps(BLOCK_MARKERS)


async def _generic_diagnose(tab) -> dict:
    val = _extract_value(await tab.execute_script(_JS_GENERIC_DIAGNOSE))
    if not val:
        return {"marker": None, "url": "", "ready_state": "", "title": ""}
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return {"marker": None, "url": "", "ready_state": "", "title": ""}


# --- Per-engine navigation (inline copy of each src/search/engines/<engine>.py flow) ---

async def nav_google(tab, query: str):
    await tab._execute_command(NetworkCommands.set_cookie(
        name=SOCS_NAME, value=SOCS_VALUE, domain=SOCS_DOMAIN, path="/",
        secure=True, same_site=CookieSameSite.LAX,
    ))
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&num=10"
    await tab.go_to(url, timeout=3.0)
    current = await tab.current_url
    inline_consent = _extract_value(await tab.execute_script(
        "var b = document.body ? document.body.innerText : ''; "
        "return b.indexOf('Before you continue') !== -1 || b.indexOf('cookies and data') !== -1;"
    ))
    if GOOGLE_CONSENT_DOMAIN in current or inline_consent:
        await tab.execute_script(
            "var btn = document.querySelector('button[jsname=\"b3VHJd\"]') || "
            "document.querySelector('.lssxud') || "
            "document.querySelector('form[action*=\"consent\"] button[type=\"submit\"]') || "
            "document.querySelector('button[aria-label*=\"Accept\"]'); "
            "if (btn) { btn.click(); return true; } return false;"
        )
        await tab.go_to(url, timeout=3.0)
        current = await tab.current_url
    if GOOGLE_CAPTCHA_PATH in current:
        return False, {"marker": "captcha_path_redirect", "url": current, "ready_state": "", "title": ""}
    if not await _wait_for(tab, CONTAINER_SELECTOR["google"], 3, 0.2):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_duckduckgo(tab, query: str):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&kl=wt-wt"
    await tab.go_to(url, timeout=3.0)
    captcha_count = _extract_value(await tab.execute_script(
        f"return document.querySelectorAll('{DDG_CAPTCHA_SELECTOR}').length"
    ))
    if captcha_count and int(captcha_count) > 0:
        current = await tab.current_url
        return False, {"marker": "challenge-form", "url": current, "ready_state": "", "title": ""}
    if not await _wait_for(tab, CONTAINER_SELECTOR["duckduckgo"], 3, 0.2):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_mojeek(tab, query: str):
    url = f"https://www.mojeek.com/search?q={quote_plus(query)}&safe=1"
    await tab.go_to(url, timeout=3.0)
    if not await _wait_for(tab, "ul.results-standard > li > a.ob", 3, 0.2):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_startpage(tab, query: str):
    await tab.go_to(STARTPAGE_HOME_URL, timeout=10.0)
    await asyncio.sleep(1.5)
    js_set = f"""
    var inp = document.querySelector('#q');
    var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeSetter.call(inp, {json.dumps(query)});
    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
    """
    await tab.execute_script(js_set)
    await asyncio.sleep(0.3)
    await tab.execute_script("document.querySelector('button.search-btn').click();")
    if not await _wait_for(tab, CONTAINER_SELECTOR["startpage"], 25, 0.3):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_brave(tab, query: str):
    url = f"https://search.brave.com/search?q={query.replace(' ', '+')}"
    await tab.go_to(url, timeout=10.0)
    await asyncio.sleep(1.5)
    diag = await _generic_diagnose(tab)
    pow_link = _extract_value(await tab.execute_script(
        'return !!document.querySelector(\'a[href*="pow-captcha"]\');'
    ))
    if diag.get("marker") or pow_link:
        diag["pow_link"] = bool(pow_link)
        return False, diag
    if not await _wait_for(tab, CONTAINER_SELECTOR["brave"], 20, 0.3):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_bing(tab, query: str):
    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
    await tab.go_to(url, timeout=10.0)
    if not await _wait_for(tab, CONTAINER_SELECTOR["bing"], 20, 0.3):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_yandex(tab, query: str):
    url = f"https://yandex.com/search/?text={query.replace(' ', '+')}"
    await tab.go_to(url, timeout=10.0)
    current = await tab.current_url
    if any(m in current.lower() for m in YANDEX_BLOCK_MARKERS):
        return False, {"marker": "block_url_redirect", "url": current, "ready_state": "", "title": ""}
    if not await _wait_for(tab, CONTAINER_SELECTOR["yandex"], 20, 0.3):
        return False, await _generic_diagnose(tab)
    return True, None


async def nav_lobsters(tab, query: str):
    url = f"https://lobste.rs/search?q={quote_plus(query)}&what=stories&order=relevance"
    await tab.go_to(url, timeout=3.0)
    if not await _wait_for(tab, CONTAINER_SELECTOR["lobsters"], 3, 0.2):
        return False, await _generic_diagnose(tab)
    return True, None


NAV_FUNCS = {
    "google": nav_google, "duckduckgo": nav_duckduckgo, "mojeek": nav_mojeek,
    "startpage": nav_startpage, "brave": nav_brave, "bing": nav_bing,
    "yandex": nav_yandex, "lobsters": nav_lobsters,
}


# --- Date evidence dump ---

def _build_date_dump_js(container_selector: str, limit: int) -> str:
    escaped = container_selector.replace("'", "\\'")
    return f"""
var _cs = document.querySelectorAll('{escaped}');
var _out = [];
var _n = Math.min(_cs.length, {limit});
var _rx = /(^|[-_\\s])(date|time|age|publish(ed)?|when|ago)([-_\\s]|$)/i;
for (var _i = 0; _i < _n; _i++) {{
    var _c = _cs[_i];
    var _timeEls = _c.querySelectorAll('time');
    var _times = [];
    for (var _t = 0; _t < _timeEls.length; _t++) {{
        _times.push({{datetime: _timeEls[_t].getAttribute('datetime') || '', text: _timeEls[_t].textContent.trim()}});
    }}
    var _cand = _c.querySelectorAll('[class],[id]');
    var _hits = [];
    for (var _d = 0; _d < _cand.length; _d++) {{
        var _el = _cand[_d];
        var _cls = (_el.className || '').toString();
        var _id = _el.id || '';
        if (_rx.test(_cls) || _rx.test(_id)) {{
            _hits.push({{tag: _el.tagName.toLowerCase(), cls: _cls.slice(0, 80), id: _id.slice(0, 40), text: (_el.textContent || '').trim().slice(0, 150)}});
        }}
    }}
    var _text = (_c.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 600);
    _out.push({{
        time_els: _times,
        date_like_els: _hits.slice(0, 10),
        text: _text,
        html_head: _c.outerHTML.slice(0, 3000)
    }});
}}
return JSON.stringify({{count: _cs.length, samples: _out}});
"""


async def _dump_date_evidence(tab, engine: str) -> dict:
    js = _build_date_dump_js(CONTAINER_SELECTOR[engine], CONTAINER_LIMIT)
    val = _extract_value(await tab.execute_script(js))
    if not val:
        return {"count": 0, "samples": []}
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return {"count": 0, "samples": []}


# Run one (engine, query) end-to-end: new tab -> navigate -> wait/diagnose -> dump evidence -> kill tab
async def run_engine_query(engine: str, query: str, axis: str, retry: bool) -> dict:
    record: dict = {
        "engine": engine, "query": query, "axis": axis, "retry": retry,
        "status": "EMPTY", "diag": None, "container_count": 0, "samples": [],
    }
    tab = await _new_tab()
    t0 = time.monotonic()
    try:
        ok, diag = await NAV_FUNCS[engine](tab, query)
        if ok:
            evidence = await _dump_date_evidence(tab, engine)
            record["container_count"] = evidence["count"]
            record["samples"] = evidence["samples"]
            record["status"] = "OK" if evidence["count"] > 0 else "EMPTY"
        else:
            record["diag"] = diag
            record["status"] = "BLOCKED" if (diag or {}).get("marker") else "EMPTY"
    except Exception as e:
        record["status"] = "ERROR"
        record["error"] = f"{type(e).__name__}: {str(e)[:160]}"
    finally:
        record["elapsed_ms"] = int((time.monotonic() - t0) * 1000)
        await _kill_tab(tab)
    return record


# --- Report ---

def write_report(records: list[dict]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"date_availability_probe_{ts}.md"

    lines = [
        f"# Date-Availability Probe (Milestone 2) — {ts}",
        "",
        "Raw evidence dump for the 8 DOM-scraped web engines. Measurement only — no src/ touched, "
        "no wiring. Queries: " + ", ".join(f"`{q}` ({a})" for q, a in QUERIES) + ". "
        "One retry (query 1, after a "
        f"{RETRY_COOLDOWN_S:.0f}s cooldown) only for engines non-OK on all 3 primary queries.",
        "",
        "## Classification",
        "",
        "*(filled in by hand after reading the raw evidence below — see chat report)*",
        "",
        "## Raw Evidence",
        "",
    ]

    by_engine: dict[str, list[dict]] = {}
    for r in records:
        by_engine.setdefault(r["engine"], []).append(r)

    for engine, recs in by_engine.items():
        lines.append(f"### {engine}")
        lines.append("")
        pre_flag = " — **pre-flagged: returned 0 results in an earlier live run this session, unrelated to this probe**" if engine in PRE_FLAGGED_EMPTY_EARLIER else ""
        lines.append(f"Pre-flag: {'yes' + pre_flag if engine in PRE_FLAGGED_EMPTY_EARLIER else 'no'}")
        lines.append("")
        for r in recs:
            tag = " (RETRY)" if r["retry"] else ""
            lines.append(f"#### [{r['axis']}]{tag} `{r['query']}` — status={r['status']} containers={r['container_count']} elapsed={r['elapsed_ms']}ms")
            lines.append("")
            if r.get("error"):
                lines.append(f"- **Error:** {r['error']}")
                lines.append("")
            if r.get("diag"):
                lines.append(f"- **Diagnosis:** `{json.dumps(r['diag'], ensure_ascii=False)}`")
                lines.append("")
            for si, s in enumerate(r["samples"], 1):
                lines.append(f"**Container {si}**")
                lines.append("")
                lines.append(f"- time elements: `{json.dumps(s['time_els'], ensure_ascii=False)}`")
                lines.append(f"- date-like class/id elements: `{json.dumps(s['date_like_els'], ensure_ascii=False)}`")
                lines.append(f"- container text (600c): `{s['text']}`")
                lines.append("- html head:")
                lines.append("```html")
                lines.append(s["html_head"])
                lines.append("```")
                lines.append("")
        lines.append("---")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    asyncio.run(run_probe())
