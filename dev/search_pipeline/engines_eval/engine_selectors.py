"""Declarative selector config for active search engines used in stealth tests.

Active pydoll engines: google, bing, google scholar
Active httpx engines:  crossref

Parked (not in production): brave — see DOCS.md "Parked: Brave & Dropped Engines"
Dropped (removed): startpage, mojeek, duckduckgo, semantic scholar

All parse_js strings use bare 'JSON.stringify(...)' expressions (no outer 'return').
pydoll's has_return_outside_function() mishandles scripts with '//' inside string literals,
so we avoid the outer 'return' entirely. The bare expression is sent via Runtime.evaluate
and extracted via _extract_nested (raw["result"]["result"]["value"]).

Each pydoll engine has a 'config' dict:
  proxy           — proxy URL or None (e.g. "socks5://127.0.0.1:9050" for Tor)
  settle_seconds  — DOM settle sleep after navigation (0.0 if engine is fast enough)
  use_context     — create fresh browser context per query for cookie isolation
  captcha_detect_js — JS returning truthy if a captcha is present (None if not needed)
"""

# INFRASTRUCTURE
from urllib.parse import quote_plus

# HTTPX engines — no browser, no selectors needed
HTTPX_ENGINES = {"crossref"}


# Build URL helpers
def _google_url(q):
    return f"https://www.google.com/search?q={quote_plus(q)}&hl=en&num=10"

def _scholar_url(q):
    return f"https://scholar.google.com/scholar?q={quote_plus(q)}&hl=en&num=10"

def _bing_url(q):
    return f"https://www.bing.com/search?q={quote_plus(q)}&setlang=en&count=10"

# PARKED — brave engine config preserved for future testing, see DOCS.md
# def _brave_url(q):
#     return f"https://search.brave.com/search?q={quote_plus(q)}&source=web"


ENGINE_SELECTORS = {

    "google": {
        "config": {
            "proxy": None,
            "settle_seconds": 0.0,
            "use_context": False,
            "captcha_detect_js": None,
        },
        "url_fn": _google_url,
        "wait": "poll",
        "wait_js": "return document.querySelectorAll('#rso h3').length",
        "parse_js": """
JSON.stringify((function() {
    var h3s = document.querySelectorAll('#rso h3');
    var out = [];
    for (var i = 0; i < h3s.length; i++) {
        var h3 = h3s[i];
        var block = h3.closest('.MjjYud') || h3.closest('#rso > div') || h3.parentElement;
        var a = block.querySelector('a[href^="http"]') || h3.closest('a');
        if (!a) continue;
        var snip = block.querySelector('.wHYlTd') ||
                   block.querySelector('.VwiC3b') ||
                   block.querySelector('[data-sncf]') ||
                   block.querySelector('.lEBKkf');
        out.push({
            url: a.href,
            title: h3.textContent.trim(),
            snippet: snip ? snip.textContent.trim() : ''
        });
    }
    return out;
})())
""",
        "consent_cookie": {
            "name": "SOCS",
            "value": "CAISHAgCEhJnd3NfMjAyNjA0MDctMCAgIBgEIAEaBgiA_fC8Bg",
            "domain": ".google.com",
            "path": "/",
            "secure": True,
            "same_site": "Lax",
        },
        "captcha_path": "/sorry/",
        "consent_domain": "consent.google.com",
    },

    "google scholar": {
        "config": {
            "proxy": None,
            "settle_seconds": 0.0,
            "use_context": False,
            "captcha_detect_js": None,
        },
        "url_fn": _scholar_url,
        "wait": "poll",
        "wait_js": "return document.querySelectorAll('div.gs_r.gs_or.gs_scl').length",
        "parse_js": """
JSON.stringify((function() {
    var nodes = document.querySelectorAll('div.gs_r.gs_or.gs_scl');
    var out = [];
    for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        var a = el.querySelector('h3.gs_rt a');
        var snip = el.querySelector('div.gs_rs');
        if (!a) continue;
        out.push({
            url: a.href,
            title: a.textContent.trim(),
            snippet: snip ? snip.textContent.trim() : ''
        });
    }
    return out;
})())
""",
        "consent_cookie": {
            "name": "SOCS",
            "value": "CAISHAgCEhJnd3NfMjAyNjA0MDctMCAgIBgEIAEaBgiA_fC8Bg",
            "domain": ".google.com",
            "path": "/",
            "secure": True,
            "same_site": "Lax",
        },
        "captcha_path": "/sorry/",
        "consent_domain": "consent.google.com",
    },

    "bing": {
        "config": {
            "proxy": None,
            "settle_seconds": 0.0,
            "use_context": False,
            "captcha_detect_js": None,
        },
        "url_fn": _bing_url,
        "wait": "poll",
        "wait_js": "return document.querySelectorAll('li.b_algo').length",
        "parse_js": """
JSON.stringify((function() {
    var items = document.querySelectorAll('li.b_algo');
    var out = [];
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        var a = el.querySelector('h2 a');
        var snip = el.querySelector('p.b_lineclamp2') || el.querySelector('.b_caption p');
        if (!a) continue;
        out.push({
            url: a.href,
            title: (a.textContent || '').trim(),
            snippet: snip ? (snip.textContent || '').trim() : ''
        });
    }
    return out;
})())
""",
    },

    # PARKED — brave dropped from production, config preserved for future testing
    # See decisions/stealth01_detection_layers.md and DOCS.md for details.
    # To resume: un-comment this block and _brave_url above, un-comment PYDOLL_ENGINES entry in 28_stress_test.py
    # "brave": {
    #     "config": {
    #         "proxy": "socks5://127.0.0.1:9050",
    #         "settle_seconds": 2.0,
    #         "use_context": False,
    #         "captcha_detect_js": """
    # (function() {
    #     var dlg = document.querySelector('dialog .captcha-card, div.captcha-card');
    #     return dlg ? true : false;
    # })()
    # """,
    #     },
    #     "url_fn": _brave_url,
    #     "wait": "poll",
    #     "wait_js": "return document.querySelectorAll('div.snippet').length",
    #     "parse_js": """
    # JSON.stringify((function() {
    #     var snippets = document.querySelectorAll('div.snippet');
    #     var out = [];
    #     for (var i = 0; i < snippets.length; i++) {
    #         var el = snippets[i];
    #         var a = el.querySelector('a[href^="http"]');
    #         if (!a || a.href.includes('brave.com')) continue;
    #         var snip = el.querySelector('p');
    #         var rawText = (a.innerText || a.textContent || '').trim();
    #         var lines = rawText.split('\\n').map(function(s) { return s.trim(); }).filter(Boolean);
    #         var title = lines.length > 1 ? lines[lines.length - 1] : rawText;
    #         out.push({
    #             url: a.href,
    #             title: title,
    #             snippet: snip ? (snip.textContent || '').trim() : ''
    #         });
    #     }
    #     return out;
    # })())
    # """,
    # },

    # HTTPX engines — type marker only, no browser selectors
    "crossref": {"type": "httpx"},
}
