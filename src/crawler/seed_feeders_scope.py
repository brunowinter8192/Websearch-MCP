# INFRASTRUCTURE
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}


# Result of one feeder run — ok=True with an empty urls list is a genuine "found nothing"
# outcome (e.g. no robots.txt, no sitemap); ok=False means the feeder itself could not run
# (e.g. an unparseable seed_url) — a caller must not treat the two the same way. `source` is a
# short, always-populated-on-success tag naming the extraction method that produced `urls`
# ("robots", "sitemap", or, for the navigation-tree feeder, "navtree_tree" vs "navtree_flat" —
# a real recursive tree found by structural shape versus a flat href scan with no tree evidence
# behind it. This is a provenance label only: no filtering or quality threshold is applied here
# or by any feeder — a caller that wants to treat "navtree_flat" as lower-confidence than
# "navtree_tree" makes that call itself, using this field, not by anything dropped upstream.
# `version_keys` is populated ONLY by the navigation-tree feeder, when the site's own payload
# carries a version list (see seed_feeders_navtree.py) — the same key list
# seed_feeders_navtree.canonicalize_version_url already uses internally to union each version's
# tree, surfaced here so discovery.py's traversal can recognize an explicit-version duplicate of
# an already-known canonical page without reimplementing the navtree feeder's own detection.
# None for every other feeder, and for a version-less site (the common case) — never populated by
# a guess, only by what the navtree feeder itself already found on the page it fetched.
@dataclass
class FeederResult:
    urls: list
    ok: bool
    error: str | None = None
    source: str | None = None
    version_keys: list | None = None


# FUNCTIONS

# Canonicalize scheme/host casing, strip the scheme's own default port, collapse an empty path
# to "/", and drop the fragment. Query string, any non-root trailing slash, and a legacy ";params"
# path segment are left exactly as given — any of the three can denote a genuinely different
# resource, and this feeder's worst case for over-merging is a seed that is never fetched at all
# (see DOCS.md Gotchas for the full boundary). Uses urlsplit, not urlparse, specifically so that a
# ";params" segment stays part of path instead of being split into a separate field and silently
# dropped when the URL is rebuilt.
def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    port = parsed.port
    netloc = host if port is None or port == _DEFAULT_PORTS.get(scheme) else f"{host}:{port}"
    path = parsed.path or "/"
    normalized = f"{scheme}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


# Host key used for scope/dedup comparison anywhere in this project — collapses a leading "www."
# (the scope decision's own normalization concern). The literal output URL keeps its original
# host text; only the comparison collapses www./apex, never a rewrite of what gets returned.
# Public (not "_"-prefixed) because src/crawler/discovery.py's own traversal-time scope filter
# needs the identical collapse, for consistency with what the feeders already consider in-scope.
def host_key(host: str) -> str:
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


# Dedup key: a normalized URL with its host collapsed through host_key. Scheme, path (including
# any ";params" segment), and query stay exactly as normalize_url produced them — see
# normalize_url's own docstring for why those are kept distinct.
def _dedup_key(normalized_url: str) -> str:
    parsed = urlsplit(normalized_url)
    collapsed_host = host_key(parsed.hostname or "")
    netloc_key = f"{collapsed_host}:{parsed.port}" if parsed.port else collapsed_host
    return urlunsplit((parsed.scheme, netloc_key, parsed.path, parsed.query, ""))


# Filter to the seed host (www./apex collapsed), normalize, and dedup preserving first-seen
# order. A URL that fails to parse (malformed port, bad IPv6 literal, ...) is dropped silently,
# not raised — this filters untrusted external sitemap/robots content, one bad entry must not
# fail the whole feeder.
def scope_and_dedup(urls: list, seed_host: str) -> list:
    seed_key = host_key(seed_host)
    seen_keys = set()
    result = []
    for raw in urls:
        try:
            normalized = normalize_url(raw)
            parsed = urlsplit(normalized)
        except ValueError:
            continue
        if host_key(parsed.hostname or "") != seed_key:
            continue
        key = _dedup_key(normalized)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        result.append(normalized)
    return result


# Validate seed_url and return its bare host; raises ValueError on unparseable/hostless input.
# Public: shared by every module that needs a caller-supplied seed_url validated the same way
# (seed_feeders.py's three workflows, src/crawler/discovery.py's own orchestrator).
def require_host(seed_url: str) -> str:
    host = urlsplit(seed_url).hostname
    if not host:
        raise ValueError(f"seed_url has no host: {seed_url!r}")
    return host
