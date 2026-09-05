# INFRASTRUCTURE
import asyncio
import json
import re
from urllib.parse import urljoin, urlsplit

import httpx

# From src/crawler/seed_feeders_constants.py: shared HTTP timeout, User-Agent, fetch concurrency
from src.crawler.seed_feeders_constants import HTTP_TIMEOUT_S, USER_AGENT, NAVTREE_FETCH_CONCURRENCY

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)
_RSC_PUSH_RE = re.compile(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)')
_RSC_ROW_ID_RE = re.compile(r'^[0-9a-f]+$')

_URL_KEYS = ("href", "url")
_CHILD_KEYS = ("childpages", "children", "items", "pages", "navigation", "nav", "subitems")
_VERSION_LIST_KEY_HINT = "version"
_CURRENT_VERSION_KEY_HINT = "currentversion"
_PATH_WITHOUT_LANGUAGE_KEY_HINT = "pathwithoutlanguage"


# FUNCTIONS

# Extract the classic Next.js Pages Router payload: a single JSON blob in a __NEXT_DATA__ script
# tag. Returns [the parsed blob], or [] if the signature is not present in this HTML at all.
def _extract_next_data_payloads(html: str) -> list:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return []
    try:
        return [json.loads(match.group(1))]
    except json.JSONDecodeError:
        return []


# Extract the current Next.js App Router payload: a React Server Components stream, delivered as
# a series of self.__next_f.push([1, "<row>..."]) calls rather than one blob. Every decoded chunk
# is concatenated before splitting into "<hexId>:<value>" rows, since a single row's content is
# not guaranteed to end on a push-call boundary. Returns every row whose value parses as JSON (an
# "I[...]"/"HL[...]" import/hint row fails to parse and is skipped, not an error — it never
# carries page data), or [] if no push call is present in this HTML at all.
def _extract_rsc_stream_payloads(html: str) -> list:
    matches = _RSC_PUSH_RE.findall(html)
    if not matches:
        return []
    full_stream = "".join(json.loads(m) for m in matches)
    rows = re.split(r'\n(?=[0-9a-f]+:)', full_stream)
    payloads = []
    for row in rows:
        row_id, _, value = row.partition(":")
        if not _RSC_ROW_ID_RE.match(row_id):
            continue
        try:
            payloads.append(json.loads(value))
        except json.JSONDecodeError:
            continue
    return payloads


# Detection dispatch: try each known payload shape in order, use the first one present in this
# HTML. A further framework's payload shape is added by appending one function to this tuple —
# no restructuring of anything downstream, which only ever sees the resulting payload list.
def extract_payloads(html: str) -> list:
    for extractor in (_extract_next_data_payloads, _extract_rsc_stream_payloads):
        payloads = extractor(html)
        if payloads:
            return payloads
    return []


# True if obj is a dict with a non-empty list-of-dicts under one of the known "children" key
# names — the structural shape a navigation-tree node always has, checked by shape rather than by
# which exact key name a given site happens to use. A list whose items are NOT all dicts (e.g. a
# serialized React element's own DOM "children", which are further ["$", tag, key, props] element
# lists, not plain data dicts) does not match — this is what keeps a rendered element tree from
# being mistaken for navigation data. Returns the matching key name, or None.
def _child_key_of(obj) -> str | None:
    if not isinstance(obj, dict):
        return None
    for key, value in obj.items():
        if (key.lower() in _CHILD_KEYS and isinstance(value, list) and value
                and all(isinstance(c, dict) for c in value)):
            return key
    return None


# Recursively collect href/url values of a confirmed tree node and every descendant reachable
# through its own children list.
def _collect_tree_hrefs(node) -> list:
    hrefs = []
    if not isinstance(node, dict):
        return hrefs
    for key in _URL_KEYS:
        value = node.get(key)
        if isinstance(value, str) and value:
            hrefs.append(value)
            break
    child_key = _child_key_of(node)
    if child_key:
        for child in node[child_key]:
            hrefs.extend(_collect_tree_hrefs(child))
    return hrefs


# Find every tree-root candidate anywhere in payload — any dict matching _child_key_of's shape,
# regardless of where it lives or what its own key is called in the parent.
def _find_tree_candidates(payload, out: list | None = None) -> list:
    if out is None:
        out = []
    if isinstance(payload, dict):
        if _child_key_of(payload):
            out.append(payload)
        for value in payload.values():
            _find_tree_candidates(value, out)
    elif isinstance(payload, list):
        for item in payload:
            _find_tree_candidates(item, out)
    return out


# Tier 2: every href/url string value anywhere in payload, regardless of container shape — the
# fallback for a payload that carries links but no recursive tree-of-dicts structure at all (a
# page rendered as plain DOM with no separate nav-data prop).
def _collect_flat_hrefs(payload, out: list) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in _URL_KEYS and isinstance(value, str):
                out.append(value)
            else:
                _collect_flat_hrefs(value, out)
    elif isinstance(payload, list):
        for item in payload:
            _collect_flat_hrefs(item, out)


# Walk every payload document for the largest tree-shaped structure (tier 1: a real recursive
# tree found by structural shape). If none has any href at all, fall back to a flat href/url scan
# across all payload documents (tier 2), filtered to drop empty/fragment-only values and Next.js's
# own internal build-asset paths. Returns (hrefs, tier, source_payload) — source_payload is the
# top-level document the winning tree came from (needed for the version-union field lookup), or
# None when tier 2 was used (there is no single coherent "source" for a flat scan).
def find_navigation_tree(payloads: list) -> tuple:
    best_hrefs = []
    best_source = None
    for payload in payloads:
        for candidate in _find_tree_candidates(payload):
            hrefs = _collect_tree_hrefs(candidate)
            if len(hrefs) > len(best_hrefs):
                best_hrefs = hrefs
                best_source = payload
    if best_hrefs:
        return best_hrefs, "tree", best_source

    flat_hrefs = []
    for payload in payloads:
        _collect_flat_hrefs(payload, flat_hrefs)
    flat_hrefs = [h for h in flat_hrefs if h and not h.startswith("#") and "/_next/" not in h]
    return flat_hrefs, "flat", None


# Generic recursive search for the first value anywhere in payload whose key matches
# key_predicate and whose value matches value_predicate.
def _find_field(payload, key_predicate, value_predicate):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key_predicate(key) and value_predicate(value):
                return value
        for value in payload.values():
            found = _find_field(value, key_predicate, value_predicate)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_field(item, key_predicate, value_predicate)
            if found is not None:
                return found
    return None


# The site's version-list field: any dict with 2+ entries whose own values are each a dict too
# (a {version_id: {...metadata...}} map), under a key whose name contains "version". Structural,
# not the literal name "allVersions" — verified against exactly one real site (docs.github.com);
# see DOCS.md Gotchas for that honesty note.
def _find_version_list(payload) -> dict | None:
    return _find_field(
        payload,
        lambda k: _VERSION_LIST_KEY_HINT in k.lower(),
        lambda v: isinstance(v, dict) and len(v) >= 2 and all(isinstance(x, dict) for x in v.values()),
    )


# The site's own identifier for which version the CURRENT page belongs to.
def _find_current_version(payload) -> str | None:
    return _find_field(
        payload,
        lambda k: k.lower() == _CURRENT_VERSION_KEY_HINT,
        lambda v: isinstance(v, str) and v,
    )


# The current page's path with the language prefix already stripped — may still include an
# explicit version segment when the current page itself is a non-default version (see
# _build_version_urls, which strips that too before use).
def _find_path_without_language(payload) -> str | None:
    return _find_field(
        payload,
        lambda k: _PATH_WITHOUT_LANGUAGE_KEY_HINT in k.lower(),
        lambda v: isinstance(v, str) and v,
    )


# Derive {version_key: version_url} for every OTHER version the site exposes (the current
# version's own tree is already in hand from the seed fetch, so it is not rebuilt/refetched).
# Returns {} if any of the three fields is missing, or if the derived content path is not
# actually a suffix of seed_url's own path — a graceful "no version union" outcome, not an error,
# since an unversioned site simply will not carry these fields at all.
def _build_version_urls(seed_url: str, all_versions: dict | None, current_version: str | None,
                        path_without_language: str | None) -> dict:
    if not all_versions or not current_version or path_without_language is None:
        return {}

    # lang_prefix MUST be derived from the ORIGINAL (language-only-stripped) path, not from the
    # version-stripped content_path below — the version segment, if present, sits BETWEEN the
    # language prefix and the content path (".../de/v2/guide"), so stripping it first would leave
    # lang_prefix still carrying it too. Caught live: docs.github.com's own default page has no
    # explicit version segment so this distinction never showed up until a seed-is-a-non-default-
    # version case (a synthetic test, no live site exercises it) exposed it.
    seed_path = urlsplit(seed_url).path
    if not seed_path.endswith(path_without_language):
        return {}
    lang_prefix = (seed_path[: len(seed_path) - len(path_without_language)]
                   if path_without_language else seed_path)

    content_path = path_without_language
    version_prefix = f"/{current_version}"
    if content_path == version_prefix:
        content_path = ""
    elif content_path.startswith(version_prefix + "/"):
        content_path = content_path[len(version_prefix):]

    parts = urlsplit(seed_url)
    base = f"{parts.scheme}://{parts.netloc}"
    return {
        version_key: f"{base}{lang_prefix.rstrip('/')}/{version_key}{content_path}"
        for version_key in all_versions
        if version_key != current_version
    }


# Strip a matching version_key path SEGMENT (any version_key known for this site, wherever it
# falls in the path — e.g. after a language prefix like "/de/enterprise-cloud@latest/rest") from
# url, bringing a version-explicit URL harvested from that version's own tree back to the
# canonical, version-implicit form the default version's own tree already uses — this is what
# lets the union dedup a page instead of counting it once per version. Framework-specific by
# design; deliberately not pushed into seed_feeders_scope.normalize_url, which keeps such
# segments intact for every other caller (see src/crawler/DOCS.md). Public (not "_"-prefixed)
# because discovery.py's own traversal calls this directly too, to recognize an explicit-version
# duplicate of an already-known canonical page discovered mid-crawl — the same rule, not a
# reimplementation, imported across the module boundary rather than duplicated (see DOCS.md
# Gotchas for why re-detecting it independently or deriving it without this exact function was
# rejected).
def canonicalize_version_url(url: str, version_keys) -> str:
    parts = urlsplit(url)
    segments = parts.path.split("/")
    for version_key in version_keys:
        if version_key in segments:
            idx = segments.index(version_key)
            new_path = "/".join(segments[:idx] + segments[idx + 1:]) or "/"
            canonical = f"{parts.scheme}://{parts.netloc}{new_path}"
            return f"{canonical}?{parts.query}" if parts.query else canonical
    return url


# Fetch a URL's HTML; None on any non-200/network error — a normal outcome (a version root that
# fails to load) for the same reason a missing robots.txt/sitemap is normal elsewhere in this
# package.
async def _fetch_html(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url, timeout=HTTP_TIMEOUT_S,
                                    headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return response.text


# One version's own contribution to the union: fetch its root, detect+extract its own tree (or
# flat href list), resolve to absolute, canonicalize back to the default version's URL shape.
async def _resolve_one_version(client: httpx.AsyncClient, version_url: str, all_version_keys: list) -> list:
    html = await _fetch_html(client, version_url)
    if html is None:
        return []
    hrefs, _tier, _source = find_navigation_tree(extract_payloads(html))
    absolute = (urljoin(version_url, href) for href in hrefs)
    return [canonicalize_version_url(url, all_version_keys) for url in absolute]


# Fetch seed_url, detect its payload shape, walk its navigation tree (or fall back to a flat href
# scan), then union in every other version the SAME payload declares, each version's own tree
# canonicalized back to the default version's URL shape before the union. Returns (urls, tier,
# version_keys); tier reflects how the DEFAULT tree itself was obtained ("tree"/"flat") — a version
# fetched during the union that happens to land on the other tier does not change the overall tag
# (see DOCS.md Gotchas for why a single tag per result, not one per URL, was the deliberate
# choice). version_keys is the site's own version-key list (see _find_version_list) whenever one
# was found on the page — None for a version-less site or a flat-tier result, regardless of
# whether a full version union was actually built (a caller needing the keys for canonicalization
# elsewhere, e.g. discovery.py's traversal, does not need a successful union, only the key list).
#
# Raises RuntimeError if seed_url itself cannot be fetched — deliberately NOT treated as a normal
# empty outcome the way a version root's own fetch failure is (see _resolve_one_version). The seed
# is the target of the whole run, not an optional resource like robots.txt/a sitemap/one version
# among several; failing to fetch it means the feeder never got to look at anything, which is a
# failed run, not "this site has no navigation tree". The caller (navtree_feeder_workflow) already
# converts an unexpected exception into FeederResult(ok=False, ...) via the same path _require_host
# uses for an invalid seed_url — both are preconditions for the feeder to do any work at all.
async def resolve_navigation_tree(client: httpx.AsyncClient, seed_url: str) -> tuple:
    html = await _fetch_html(client, seed_url)
    if html is None:
        raise RuntimeError(f"could not fetch seed_url: {seed_url!r}")

    payloads = extract_payloads(html)
    hrefs, tier, source_payload = find_navigation_tree(payloads)
    absolute = [urljoin(seed_url, href) for href in hrefs]

    if source_payload is None:
        return absolute, tier, None

    all_versions = _find_version_list(source_payload)
    current_version = _find_current_version(source_payload)
    path_without_language = _find_path_without_language(source_payload)
    version_urls = _build_version_urls(seed_url, all_versions, current_version, path_without_language)
    all_version_keys = list(all_versions.keys()) if all_versions else None
    if not version_urls:
        return absolute, tier, all_version_keys

    canonical_default = [canonicalize_version_url(url, all_version_keys) for url in absolute]

    semaphore = asyncio.Semaphore(NAVTREE_FETCH_CONCURRENCY)

    async def _bounded(version_url: str) -> list:
        async with semaphore:
            return await _resolve_one_version(client, version_url, all_version_keys)

    per_version_results = await asyncio.gather(*[_bounded(u) for u in version_urls.values()])

    union = list(canonical_default)
    for urls in per_version_results:
        union.extend(urls)
    return union, tier, all_version_keys
