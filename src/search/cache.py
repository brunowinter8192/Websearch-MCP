# INFRASTRUCTURE
import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path

from src.search.result import SearchResult

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".cache" / "searxng"
DEFAULT_TTL = 3600  # 1 hour


# FUNCTIONS

# SHA-256 hex of canonical input string, first 16 chars
def cache_key(query: str, language: str, engines: str | None, time_range: str | None) -> str:
    canonical = f"{query.lower().strip()}|{language}|{engines or ''}|{time_range or ''}"
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ~/.cache/searxng/<key>.json
def cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


# Atomic write via temp file + rename
def cache_write(
    key: str,
    ranked: list[SearchResult],
    query: str,
    language: str,
    engines: str | None,
    time_range: str | None,
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": query,
        "language": language,
        "engines": engines,
        "time_range": time_range,
        "timestamp": int(time.time()),
        "returned_count": len(ranked),
        "urls": [
            {
                "url": r.url,
                "title": r.title,
                "snippet": r.snippet,
                "engines": r.engines,
                "snippets": r.snippets,
            }
            for r in ranked
        ],
    }
    target = cache_path(key)
    fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, target)
        logger.debug("Cache written: %s (%d urls)", target, len(ranked))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# Read cache if exists and not expired (mtime-based). Returns dict or None on miss/expiry.
def cache_read(key: str, ttl_seconds: int = DEFAULT_TTL) -> dict | None:
    path = cache_path(key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > ttl_seconds:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Cache read error %s: %s", path, e)
        return None


# Format a slice of cached url-dicts as a numbered plain-text list
def format_cached_slice(urls: list[dict], start_index: int) -> str:
    lines = []
    for i, entry in enumerate(urls, start_index + 1):
        lines.append(f"{i}. {entry['title']}")
        lines.append(f"   URL: {entry['url']}")
        snippet = entry.get("snippet", "")
        if snippet:
            lines.append(f"   Snippet: {snippet[:5000]}")
        lines.append("")
    return "\n".join(lines)
