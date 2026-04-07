"""Declarative selector config for all 9 search engines used in stealth tests.

Engines: google, bing, brave, startpage, mojeek, google scholar  → pydoll (browser-based)
         duckduckgo, semantic scholar, crossref                   → httpx (no browser needed)

All parse_js strings use bare 'JSON.stringify(...)' expressions (no outer 'return').
pydoll's has_return_outside_function() mishandles scripts with '//' inside string literals,
so we avoid the outer 'return' entirely. The bare expression is sent via Runtime.evaluate
and extracted via _extract_nested (raw["result"]["result"]["value"]).
"""

# INFRASTRUCTURE
from urllib.parse import quote_plus

# HTTPX engines — no browser, no selectors needed
HTTPX_ENGINES = {"duckduckgo", "semantic scholar", "crossref"}


# Build URL helpers
def _google_url(q):
    return f"https://www.google.com/search?q={quote_plus(q)}&hl=en&num=10"

def _scholar_url(q):
    return f"https://scholar.google.com/scholar?q={quote_plus(q)}&hl=en&num=10"

def _bing_url(q):
    return f"https://www.bing.com/search?q={quote_plus(q)}&setlang=en&count=10"

def _brave_url(q):
    return f"https://search.brave.com/search?q={quote_plus(q)}&source=web"

def _startpage_url(q):
    return f"https://www.startpage.com/sp/search?query={quote_plus(q)}&language=en"

def _mojeek_url(q):
    return f"https://www.mojeek.com/search?q={quote_plus(q)}&arc=none"


ENGINE_SELECTORS = {

    "google": {
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

    "brave": {
        "url_fn": _brave_url,
        "wait": "poll",
        "wait_js": "return document.querySelectorAll('div.snippet').length",
        "captcha_detect_js": """
(function() {
    var dlg = document.querySelector('dialog .captcha-card, div.captcha-card');
    return dlg ? true : false;
})()
""",
        "parse_js": """
JSON.stringify((function() {
    var snippets = document.querySelectorAll('div.snippet');
    var out = [];
    for (var i = 0; i < snippets.length; i++) {
        var el = snippets[i];
        var a = el.querySelector('a[href^="http"]');
        if (!a || a.href.includes('brave.com')) continue;
        var snip = el.querySelector('p');
        var rawText = (a.innerText || a.textContent || '').trim();
        var lines = rawText.split('\\n').map(function(s) { return s.trim(); }).filter(Boolean);
        var title = lines.length > 1 ? lines[lines.length - 1] : rawText;
        out.push({
            url: a.href,
            title: title,
            snippet: snip ? (snip.textContent || '').trim() : ''
        });
    }
    return out;
})())
""",
    },

    "startpage": {
        "url_fn": _startpage_url,
        "wait": "poll",
        "wait_js": "return document.querySelectorAll('div.result').length",
        "parse_js": """
JSON.stringify((function() {
    var results = document.querySelectorAll('div.result');
    var out = [];
    for (var i = 0; i < results.length; i++) {
        var el = results[i];
        var a = el.querySelector(':scope > a[href^="http"]');
        if (!a || a.href.includes('startpage.com')) continue;
        var snip = el.querySelector('p') || el.querySelector('[class*="description"]');
        out.push({
            url: a.href,
            title: (a.textContent || '').trim().split('\\n')[0],
            snippet: snip ? (snip.textContent || '').trim() : ''
        });
    }
    return out;
})())
""",
    },

    "mojeek": {
        "url_fn": _mojeek_url,
        "wait": "poll",
        "wait_js": "return document.querySelectorAll('ul.results-standard li').length",
        "parse_js": """
JSON.stringify((function() {
    var items = document.querySelectorAll('ul.results-standard li');
    var out = [];
    for (var i = 0; i < items.length; i++) {
        var el = items[i];
        var titleA = el.querySelector('h2 a');
        var urlA = el.querySelector('a.ob') || titleA;
        var snip = el.querySelector('p.s');
        if (!urlA) continue;
        out.push({
            url: urlA.href,
            title: titleA ? (titleA.textContent || '').trim() : (urlA.textContent || '').trim(),
            snippet: snip ? (snip.textContent || '').trim() : ''
        });
    }
    return out;
})())
""",
    },

    # HTTPX engines — type marker only, no browser selectors
    "duckduckgo": {"type": "httpx"},
    "semantic scholar": {"type": "httpx"},
    "crossref": {"type": "httpx"},
}
