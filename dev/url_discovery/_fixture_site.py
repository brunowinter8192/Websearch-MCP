"""Deterministic local fixture site for verifying src/crawler/discovery.py's three seed feeders
(robots.txt, sitemap, navtree) and its link-graph traversal — the instrument
process-docs/url_discovery/2026-08-28_validation_against_live_sites_was_the_wrong_unit.md argues
for: ground truth stated in code (ground_truth(), below) rather than a number someone once
measured on a live host, so a discrepancy is either a real bug or a real fixture change, never an
unresolvable "did the site drift" question.

Every page/robots.txt/sitemap this module serves is GENERATED from the same source lists
ground_truth() reads its own numbers from (NAVTREE_CANONICAL_PAGES, SITEMAP_BLOG_PAGES, ...) — the
statement drives the pages, not the other way around.

Site shape (seed_url = seed_url(port), i.e. /docs/guide):
- Navtree (Pages Router __NEXT_DATA__, the shape src/crawler/seed_feeders_navtree.py's tier-1
  tree walk + version union both need): 3 versions of one doc tree (current/v2/v1), 2 pages that
  exist only in v1 (NAVTREE_V1_ONLY_PAGES) — the version-exclusive case.
- A separate, deliberately UNLINKED "/rsc-demo" island exercises the OTHER payload shape
  (self.__next_f.push RSC stream) directly via navtree_feeder_workflow — it is never part of the
  main site graph and never counted in ground_truth()'s totals.
- Sitemap: a TWO-LEVEL nested <sitemapindex> (sitemap_index.xml -> sitemap-docs-group.xml, itself
  an index -> two leaf <urlset> documents) — exercises resolve_sitemap_urls's recursion, not just
  one level of it.
- robots.txt: 2 Disallow + 1 Allow path, all collected as seeds regardless (the seed_feeders_robots
  decision this fixture must let happen, not prevent) — one of the three
  (ROBOTS_EMPTY_404_PATHS) is a genuine empty-body 404, the one case that DOES read as a real
  crawl4ai fetch failure (see the Gotcha below on why an ordinary 404 does not).
- Orphans: reachable by link alone, absent from every feeder's own output.
- Two additional traversal-only pages test behaviors already on record in src/crawler/DOCS.md's
  own Gotchas, not covered by a plain orphan: REVISIT_TEST_PAGE links to a URL a feeder ALREADY
  delivered (tests _build_resume_state's "visited" pre-population — the already-known URL must
  stay attributed to its feeder, not be re-tagged "traversal" or double-counted).
  VERSION_DUP_TEST_PAGE links to an explicit-version duplicate of an already-delivered canonical
  navtree page (tests the CLOSED item: discovery.py's traversal now runs a discovered link through
  seed_feeders_navtree.canonicalize_version_url via the version keys FeederResult.version_keys
  surfaces, so this duplicate is recognized as an alias of the canonical page — DiscoveredURL.
  canonical_url is set on it, its own source/fetched stay whatever its own real fetch observed,
  and the canonical page's own entry is never touched).

Failure modes are switched via /_control/* GET requests, never random, always resettable — see
_STATE. Thin-body-200 is a simple on/off toggle. 429 is a genuine SLIDING WINDOW ("at most `limit`
requests within the trailing `window` seconds", /_control/rate_limit?limit=M&window=T) rather than
an absolute counter that trips once and never recovers — a window is what lets a caller that spaces
its own requests stay under it indefinitely, and lets a bursty one recover once it slows down,
which is the property real per-domain pacing needs to be checked against (process-docs/
url_discovery/2026-09-05_pacing_measurement.md).
"""
# INFRASTRUCTURE
import http.server
import json
import threading
import time
from urllib.parse import parse_qs, urljoin, urlsplit

DEFAULT_HOST = "127.0.0.1"

# --- Navtree: 3 versions of one doc tree, current = the literal seed_url ---
CURRENT_VERSION = "current"
ALL_VERSIONS = ("current", "v2", "v1")
SEED_PATH = "/docs/guide"
SEED_CONTENT_PATH = "/guide"  # currentPathWithoutLanguage: seed_path with the "/docs" lang prefix stripped

# root, intro, configuration, configuration/advanced, api — present in every version
NAVTREE_CANONICAL_PAGES = (
    "/docs/guide",
    "/docs/guide/intro",
    "/docs/guide/configuration",
    "/docs/guide/configuration/advanced",
    "/docs/guide/api",
)
# present ONLY in the v1 tree — the version-exclusive case
NAVTREE_V1_ONLY_PAGES = (
    "/docs/guide/legacy-plugin-api",
    "/docs/guide/legacy-theme-format",
)

# --- App Router RSC-stream demo island: isolated, never linked, not part of ground_truth() ---
RSC_DEMO_ROOT = "/rsc-demo"
RSC_DEMO_CHILDREN = ("/rsc-demo/alpha", "/rsc-demo/beta")

# --- Sitemap: two-level nested sitemapindex ---
SITEMAP_INDEX_PATH = "/sitemap_index.xml"
SITEMAP_GROUP_PATH = "/sitemap-docs-group.xml"  # the SECOND nesting level (itself an index)
SITEMAP_BLOG_LEAF_PATH = "/sitemap-blog.xml"
SITEMAP_LEGAL_LEAF_PATH = "/sitemap-legal.xml"
SITEMAP_BLOG_PAGES = ("/blog/post-1", "/blog/post-2", "/blog/post-3")
SITEMAP_LEGAL_PAGES = ("/legal/privacy", "/legal/terms")

# --- robots.txt: Allow/Disallow paths, collected as seeds regardless of what they permit ---
ROBOTS_DISALLOW_PATHS = ("/internal/admin", "/internal/staging-notes")
ROBOTS_ALLOW_PATHS = ("/internal/public-notice",)
ROBOTS_REAL_PATHS = ("/internal/admin", "/internal/public-notice")
ROBOTS_EMPTY_404_PATHS = ("/internal/staging-notes",)  # genuine empty-body 404 -> real fetch failure

# --- Orphans: link-only, absent from every feeder's own output ---
ORPHAN_CHAIN = ("/orphan/changelog", "/orphan/changelog/2024")

# --- "visited" pre-population case: links to an ALREADY-DELIVERED feeder URL ---
REVISIT_TEST_PAGE = "/docs/guide/related-links"
REVISIT_TEST_TARGET = SITEMAP_BLOG_PAGES[0]

# --- version-canonicalization-gap case (deliberately unfixed, see module docstring) ---
VERSION_DUP_TEST_PAGE = "/docs/guide/see-versions"
VERSION_DUP_TARGET = "/docs/v1/guide/intro"
VERSION_DUP_CANONICAL = NAVTREE_CANONICAL_PAGES[1]  # "/docs/guide/intro" — the already-known page

THIN_BODY_HTML = '<html><body><div id="app"></div></body></html>'  # ~50 bytes: 0 visible chars,
# 0 content elements -> 2 structural anti-bot signals, same shape as the real 168-byte case
# recorded in src/crawler/DOCS.md's Gotchas.

_ROUTES: dict = {}
_STATE_LOCK = threading.Lock()
# rate_limit_limit/rate_limit_window_s: a SLIDING WINDOW, not an absolute counter that trips once
# and never recovers. The absolute-counter shape this replaced (process-docs/url_discovery/
# 2026-09-05_pacing_measurement.md) could not distinguish a well-paced crawler from a badly-paced
# one — both eventually send N total requests and both trip it identically, with no way back.
# A window lets a caller that spaces its requests stay under the limit indefinitely, and lets one
# that bursts recover once it slows down — the actual property real per-domain pacing needs to be
# checked against. _REQUEST_TIMESTAMPS holds one monotonic timestamp per non-control request
# admitted or checked while the window is armed; pruned to the trailing window on every check.
_STATE = {"request_count": 0, "rate_limit_limit": None, "rate_limit_window_s": None, "thin_body": False}
_REQUEST_TIMESTAMPS: list = []


# FUNCTIONS

# Absolute seed_url for a fixture server bound to the given port
def seed_url(port: int, host: str = DEFAULT_HOST) -> str:
    return f"http://{host}:{port}{SEED_PATH}"


# path -> its version-prefixed form (e.g. "/docs/guide/intro" + "v1" -> "/docs/v1/guide/intro"),
# or path unchanged for CURRENT_VERSION (the default version carries no URL prefix at all)
def _version_path(path: str, version: str) -> str:
    if version == CURRENT_VERSION:
        return path
    return path.replace("/docs/", f"/docs/{version}/", 1)


# Build a __NEXT_DATA__-shaped sidebarTree: root + intro + configuration(+nested advanced) + api,
# plus any further hrefs appended as flat extra children (the v1-only pages)
def _sidebar_tree(hrefs: tuple) -> dict:
    root, intro, configuration, configuration_advanced, api, *extra = hrefs
    children = [
        {"href": intro, "childPages": []},
        {"href": configuration, "childPages": [{"href": configuration_advanced, "childPages": []}]},
        {"href": api, "childPages": []},
    ]
    children += [{"href": h, "childPages": []} for h in extra]
    return {"href": root, "childPages": children}


# A __NEXT_DATA__ page: sidebarTree always present; version metadata (allVersions/currentVersion/
# currentPathWithoutLanguage) only on the DEFAULT version's own page — the only one
# resolve_navigation_tree ever reads those fields from
def _next_data_page_html(tree: dict, title: str, with_version_meta: bool = False,
                         extra_links: tuple = ()) -> str:
    main_context = {"sidebarTree": tree}
    if with_version_meta:
        main_context.update({
            "allVersions": {v: {"version": v} for v in ALL_VERSIONS},
            "currentVersion": CURRENT_VERSION,
            "currentPathWithoutLanguage": SEED_CONTENT_PATH,
        })
    payload = {"props": {"pageProps": {"mainContext": main_context}}}
    links_html = "".join(f'<p><a href="{href}">{href}</a></p>' for href in extra_links)
    return (
        f"<html><head><title>{title}</title></head><body>"
        f"<h1>{title}</h1>"
        f"<p>Fixture documentation page with real visible text, so it is never mistaken for a "
        f"thin anti-bot shell by crawl4ai's own structural check.</p>"
        f"{links_html}"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        f"</body></html>"
    )


# A plain leaf content page — real visible text, optional outbound <a> links
def _leaf_page_html(title: str, links: tuple = ()) -> str:
    links_html = "".join(f'<p><a href="{href}">{href}</a></p>' for href in links)
    return (
        f"<html><head><title>{title}</title></head><body>"
        f"<h1>{title}</h1>"
        f"<p>Fixture content page for the url_discovery test site. This paragraph exists so the "
        f"page carries enough visible text to never read as an anti-bot block page.</p>"
        f"{links_html}"
        f"</body></html>"
    )


# The isolated RSC (self.__next_f.push) demo page — a genuine structured tree, App Router shape,
# never linked from the main site graph
def _rsc_demo_html() -> str:
    tree = {"type": "root", "name": "RSC Demo", "children": [
        {"type": "page", "name": "Alpha", "url": RSC_DEMO_CHILDREN[0]},
        {"type": "page", "name": "Beta", "url": RSC_DEMO_CHILDREN[1]},
    ]}
    row = f"1:{json.dumps({'tree': tree})}"
    return (
        "<html><head><title>RSC demo</title></head><body>"
        "<h1>RSC demo (App Router payload shape)</h1>"
        "<p>Isolated demo page, deliberately never linked from the main site graph — exists "
        "solely to exercise the self.__next_f.push RSC-stream extractor directly, since "
        "discover_urls_workflow only ever calls the navtree feeder once, against the main site's "
        "own Pages-Router shape.</p>"
        f"<script>self.__next_f.push([1,{json.dumps(row)}])</script>"
        "</body></html>"
    )


# robots.txt text: 2 Disallow + 1 Allow (collected as seeds regardless — the deliberate behavior
# this fixture must let be observed) + a Sitemap: line pointing at the top of the nested index
def _robots_txt(base_url: str) -> str:
    lines = ["User-agent: *"]
    lines += [f"Disallow: {p}" for p in ROBOTS_DISALLOW_PATHS]
    lines += [f"Allow: {p}" for p in ROBOTS_ALLOW_PATHS]
    lines.append(f"Sitemap: {urljoin(base_url, SITEMAP_INDEX_PATH)}")
    return "\n".join(lines) + "\n"


# <sitemapindex> listing absolute <loc> URLs for each sub_path (index entries MUST be absolute —
# scope_and_dedup drops a relative <loc>'s empty host as "foreign")
def _sitemapindex_xml(base_url: str, sub_paths: tuple) -> str:
    entries = "".join(f"<sitemap><loc>{urljoin(base_url, p)}</loc></sitemap>" for p in sub_paths)
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</sitemapindex>')


# <urlset> listing absolute <loc> URLs for each page path
def _urlset_xml(base_url: str, paths: tuple) -> str:
    entries = "".join(f"<url><loc>{urljoin(base_url, p)}</loc></url>" for p in paths)
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>')


# Homepage: plain human-readable description, deliberately linked from nowhere — never appears in
# any discovery run regardless of content, kept purely for a human/agent curling the base URL
def _homepage_html() -> str:
    return (
        "<html><head><title>url_discovery fixture site</title></head><body>"
        "<h1>url_discovery fixture site</h1>"
        "<p>Deterministic fixture for src/crawler/discovery.py. This page is never linked from "
        "anywhere and never appears in any discovery run. See dev/url_discovery/_fixture_site.py "
        "for the ground truth and GET /_control/status for live failure-mode state.</p>"
        "</body></html>"
    )


# Build every route this site serves, as {path: (status, content_type, body_bytes)} — everything
# generated from the module's own source lists, called once per server start once base_url (which
# needs the real bound port for absolute sitemap <loc> URLs) is known
def _build_routes(base_url: str) -> dict:
    routes = {}

    def add(path, content_type, body):
        routes[path] = (200, content_type, body.encode("utf-8"))

    add("/", "text/html; charset=utf-8", _homepage_html())

    current_tree = _sidebar_tree(NAVTREE_CANONICAL_PAGES)
    add(SEED_PATH, "text/html; charset=utf-8", _next_data_page_html(
        current_tree, title="Guide (current)", with_version_meta=True,
        extra_links=(ORPHAN_CHAIN[0], REVISIT_TEST_PAGE, VERSION_DUP_TEST_PAGE)))
    for path in NAVTREE_CANONICAL_PAGES[1:]:
        add(path, "text/html; charset=utf-8", _leaf_page_html(title=f"Guide: {path}"))
    for path in NAVTREE_V1_ONLY_PAGES:
        add(path, "text/html; charset=utf-8", _leaf_page_html(title=f"Guide (v1-only): {path}"))

    v2_hrefs = tuple(_version_path(p, "v2") for p in NAVTREE_CANONICAL_PAGES)
    add(_version_path(SEED_PATH, "v2"), "text/html; charset=utf-8", _next_data_page_html(
        _sidebar_tree(v2_hrefs), title="Guide (v2)"))
    v1_hrefs = (tuple(_version_path(p, "v1") for p in NAVTREE_CANONICAL_PAGES)
                + tuple(_version_path(p, "v1") for p in NAVTREE_V1_ONLY_PAGES))
    add(_version_path(SEED_PATH, "v1"), "text/html; charset=utf-8", _next_data_page_html(
        _sidebar_tree(v1_hrefs), title="Guide (v1)"))

    add(VERSION_DUP_TARGET, "text/html; charset=utf-8",
        _leaf_page_html(title="Guide: intro (v1 explicit-version duplicate)"))

    add(ORPHAN_CHAIN[0], "text/html; charset=utf-8",
        _leaf_page_html(title="Changelog (orphan)", links=(ORPHAN_CHAIN[1],)))
    add(ORPHAN_CHAIN[1], "text/html; charset=utf-8", _leaf_page_html(title="Changelog 2024 (orphan)"))
    add(REVISIT_TEST_PAGE, "text/html; charset=utf-8",
        _leaf_page_html(title="Related links", links=(REVISIT_TEST_TARGET,)))
    add(VERSION_DUP_TEST_PAGE, "text/html; charset=utf-8",
        _leaf_page_html(title="See other versions", links=(VERSION_DUP_TARGET,)))

    for path in SITEMAP_BLOG_PAGES + SITEMAP_LEGAL_PAGES:
        add(path, "text/html; charset=utf-8", _leaf_page_html(title=f"Blog/legal: {path}"))
    for path in ROBOTS_REAL_PATHS:
        add(path, "text/html; charset=utf-8", _leaf_page_html(title=f"Internal: {path}"))

    add("/robots.txt", "text/plain; charset=utf-8", _robots_txt(base_url))
    add(SITEMAP_INDEX_PATH, "application/xml; charset=utf-8",
        _sitemapindex_xml(base_url, (SITEMAP_GROUP_PATH,)))
    add(SITEMAP_GROUP_PATH, "application/xml; charset=utf-8",
        _sitemapindex_xml(base_url, (SITEMAP_BLOG_LEAF_PATH, SITEMAP_LEGAL_LEAF_PATH)))
    add(SITEMAP_BLOG_LEAF_PATH, "application/xml; charset=utf-8", _urlset_xml(base_url, SITEMAP_BLOG_PAGES))
    add(SITEMAP_LEGAL_LEAF_PATH, "application/xml; charset=utf-8", _urlset_xml(base_url, SITEMAP_LEGAL_PAGES))

    add(RSC_DEMO_ROOT, "text/html; charset=utf-8", _rsc_demo_html())
    for path in RSC_DEMO_CHILDREN:
        add(path, "text/html; charset=utf-8", _leaf_page_html(title=f"RSC demo: {path}"))

    return routes


# The pre-traversal seed set discover_urls_workflow's own _assemble_seeds would build: literal
# seed first, then robots/sitemap/navtree in that fixed order, first-write-wins — mirrors
# discovery.py's own merge priority so a URL present in two lists (the navtree root == the
# literal seed) is counted once, under "seed", exactly like the real docs.github.com run on record.
def _pre_traversal_seeds() -> list:
    order = []
    seen = set()

    def add(paths, tag):
        for p in paths:
            if p not in seen:
                seen.add(p)
                order.append((p, tag))

    add((SEED_PATH,), "seed")
    add(ROBOTS_DISALLOW_PATHS + ROBOTS_ALLOW_PATHS, "robots")
    add(SITEMAP_BLOG_PAGES + SITEMAP_LEGAL_PAGES, "sitemap")
    add(NAVTREE_CANONICAL_PAGES + NAVTREE_V1_ONLY_PAGES, "navtree_tree")
    return order


# The fixture's stated ground truth, computed from the same source lists that generate the served
# pages — never hand-typed. total_urls/pages_fetched/pages_failed are what a real
# discover_urls_workflow(seed_url(port)) run is expected to report, against a freshly-reset server.
def ground_truth() -> dict:
    seeds = _pre_traversal_seeds()
    by_source = {}
    for _, tag in seeds:
        by_source[tag] = by_source.get(tag, 0) + 1
    traversal_only = ORPHAN_CHAIN + (REVISIT_TEST_PAGE, VERSION_DUP_TEST_PAGE, VERSION_DUP_TARGET)
    by_source["traversal"] = len(traversal_only)
    total_urls = len(seeds) + len(traversal_only)
    pages_failed = len(ROBOTS_EMPTY_404_PATHS)
    return {
        "seed_path": SEED_PATH,
        "total_urls": total_urls,
        "by_source": by_source,
        "pages_fetched_expected": total_urls - pages_failed,
        "pages_failed_expected": pages_failed,
        "expected_stop_reason": "frontier_exhausted",
        # Every pre-traversal seed is injected into resume_state's "pending" at depth 0 (see
        # discovery.py's _build_resume_state), so they are all fetched as ONE single BFS level —
        # this is the real ceiling a small max_pages override lands on, since max_pages is checked
        # only BETWEEN levels (src/crawler/DOCS.md's Gotchas). Any caller measuring the
        # BFS-level-granularity overshoot property against this fixture reads it from here, not
        # from a count re-derived (or worse, hand-typed) a second time elsewhere.
        "pre_traversal_seed_count": len(seeds),
        "navtree": {
            "total": len(set(NAVTREE_CANONICAL_PAGES) | set(NAVTREE_V1_ONLY_PAGES)),
            "canonical": len(NAVTREE_CANONICAL_PAGES),
            "version_exclusive": len(NAVTREE_V1_ONLY_PAGES),
            "version_exclusive_pages": list(NAVTREE_V1_ONLY_PAGES),
        },
        "sitemap": {"listed": len(SITEMAP_BLOG_PAGES) + len(SITEMAP_LEGAL_PAGES)},
        "robots": {
            "listed": len(ROBOTS_DISALLOW_PATHS) + len(ROBOTS_ALLOW_PATHS),
            "real": len(ROBOTS_REAL_PATHS),
            "unfetchable": len(ROBOTS_EMPTY_404_PATHS),
            "unfetchable_paths": list(ROBOTS_EMPTY_404_PATHS),
        },
        "orphans": {"count": len(ORPHAN_CHAIN), "pages": list(ORPHAN_CHAIN)},
        "revisit_test": {
            "page": REVISIT_TEST_PAGE, "already_known_target": REVISIT_TEST_TARGET,
            "expected": "target stays attributed to its own feeder, not re-tagged traversal, not double-fetched",
        },
        "version_duplicate_test": {
            "page": VERSION_DUP_TEST_PAGE, "duplicate_target": VERSION_DUP_TARGET,
            "canonical_original": VERSION_DUP_CANONICAL,
            "expected_behavior":
                "duplicate_target is still its own DiscoveredURL entry (total_urls/by_source do "
                "NOT change — it was already counted before this fix, only its shape changes now), "
                "source='traversal', fetched=True (a real fetch still happens — this closes the "
                "canonicalization gap, it does not prevent the fetch), and canonical_url equals "
                "canonical_original's own URL. canonical_original's own entry is untouched: "
                "source='navtree_tree', canonical_url=None.",
        },
        "rsc_demo": {
            "root": RSC_DEMO_ROOT, "children": list(RSC_DEMO_CHILDREN),
            "note": "isolated island, never linked, NOT included in total_urls",
        },
    }


# Serves the fixture site: normal content routes, the two switchable failure modes, and the
# /_control/* state endpoints — see the module docstring for the site shape.
class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/_control/"):
            self._serve_control()
        else:
            self._serve_content()

    # Read/mutate failure-mode state; never counted against the rate-limit window itself
    def _serve_control(self):
        global _REQUEST_TIMESTAMPS
        parsed = urlsplit(self.path)
        action = parsed.path[len("/_control/"):]
        params = parse_qs(parsed.query)
        with _STATE_LOCK:
            if action == "reset":
                _STATE.update(request_count=0, rate_limit_limit=None, rate_limit_window_s=None, thin_body=False)
                _REQUEST_TIMESTAMPS = []
            elif action == "rate_limit":
                _STATE["rate_limit_limit"] = int(params.get("limit", ["0"])[0])
                _STATE["rate_limit_window_s"] = float(params.get("window", ["1"])[0])
                _REQUEST_TIMESTAMPS = []
            elif action == "thin_body":
                _STATE["thin_body"] = params.get("on", ["true"])[0].lower() == "true"
            elif action != "status":
                self._respond(404, b"unknown control action", "text/plain")
                return
            reportable = dict(_STATE)
            reportable["requests_in_window"] = len(_REQUEST_TIMESTAMPS)
            body = json.dumps(reportable).encode("utf-8")
        self._respond(200, body, "application/json")

    # Normal content path: apply failure modes first (both override any real route), else serve
    # the built route or a genuine 404 (empty-body for ROBOTS_EMPTY_404_PATHS, a normal small body
    # for anything else unmapped)
    def _serve_content(self):
        with _STATE_LOCK:
            _STATE["request_count"] += 1
            limit = _STATE["rate_limit_limit"]
            window = _STATE["rate_limit_window_s"]
            thin_body = _STATE["thin_body"]
            over_limit = False
            if limit is not None:
                now = time.monotonic()
                cutoff = now - window
                while _REQUEST_TIMESTAMPS and _REQUEST_TIMESTAMPS[0] < cutoff:
                    _REQUEST_TIMESTAMPS.pop(0)
                if len(_REQUEST_TIMESTAMPS) >= limit:
                    over_limit = True
                else:
                    _REQUEST_TIMESTAMPS.append(now)

        if over_limit:
            self._respond(429, b"Too Many Requests", "text/plain")
            return
        if thin_body:
            self._respond(200, THIN_BODY_HTML.encode("utf-8"), "text/html")
            return
        if self.path in ROBOTS_EMPTY_404_PATHS:
            self._respond(404, b"", "text/html")
            return
        route = _ROUTES.get(self.path)
        if route is None:
            self._respond(404, b"not found", "text/plain")
            return
        status, content_type, body = route
        self._respond(status, body, content_type)

    def _respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)


# Start the fixture on an OS-assigned free port (port=0) or a given one; builds every route fresh
# (base_url needs the real bound port for absolute sitemap <loc> URLs) and resets failure-mode
# state. Returns (server, thread, bound_port). Only ONE fixture server is meant to run per process
# at a time — routes/state are module-level, not per-instance (see Gotchas in DOCS.md).
def start_fixture_server(host: str = DEFAULT_HOST, port: int = 0):
    global _ROUTES, _REQUEST_TIMESTAMPS
    server = http.server.ThreadingHTTPServer((host, port), _FixtureHandler)
    bound_port = server.server_address[1]
    base_url = f"http://{host}:{bound_port}/"
    _ROUTES = _build_routes(base_url)
    with _STATE_LOCK:
        _STATE.update(request_count=0, rate_limit_limit=None, rate_limit_window_s=None, thin_body=False)
        _REQUEST_TIMESTAMPS = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, bound_port


# Shut the fixture server down cleanly
def stop_fixture_server(server: http.server.ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    thread.join(timeout=5)
