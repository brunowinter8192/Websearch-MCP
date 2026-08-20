# INFRASTRUCTURE
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from src.news.platforms.coindesk.config import (
    TIMELINE_BASE,
    COINDESK_BASE,
    TARGET_URL,
    CALL_DELAY,
    REWARM_EVERY,
    CLICKS_WARMUP,
    CLICKS_REWARM,
    MAX_CURSOR_FALLBACKS,
    CHECKPOINT_EVERY,
    DEFAULT_DELTA_DAYS,
    FULL_MODE_FLOOR,
    DISCOVER_DIR,
)
# From browser.py: browser_load_feed(n_clicks) -> (headers, api_url, body)
from src.news.platforms.coindesk.browser import browser_load_feed


# ORCHESTRATOR

# Browser warmup → httpx cursor loop → incremental discover write → entry list.
async def discover(timeframe: str = "30") -> list[dict]:
    stop_date = _parse_stop_date(timeframe)
    print(f"[coindesk] discover timeframe={timeframe!r} stop_date={stop_date}", file=sys.stderr)

    print("[coindesk] Browser warmup …", file=sys.stderr)
    headers, start_url, first_body = await browser_load_feed(CLICKS_WARMUP)
    if first_body is None:
        raise RuntimeError("CoinDesk browser warmup failed — could not capture timeline API response")

    print(f"[coindesk] Warmup done. First URL: {start_url}", file=sys.stderr)

    DISCOVER_DIR.mkdir(parents=True, exist_ok=True)
    seen_urls = load_discover(DISCOVER_DIR)
    print(f"[coindesk] Discover loaded: {len(seen_urls)} existing URLs", file=sys.stderr)

    entries = await cursor_loop(headers, start_url, first_body, stop_date, seen_urls, DISCOVER_DIR)

    new_count = sum(1 for e in entries if e.get("_new"))
    print(
        f"[coindesk] discover → {len(entries)} entries total, {new_count} new to discover",
        file=sys.stderr,
    )
    return [{k: v for k, v in e.items() if k != "_new"} for e in entries]


# FUNCTIONS

# Compute stop-date string from timeframe specifier
def _parse_stop_date(timeframe: str) -> str:
    if timeframe == "full":
        return FULL_MODE_FLOOR
    try:
        n = int(timeframe)
    except ValueError:
        n = DEFAULT_DELTA_DAYS
    floor = datetime.now(timezone.utc).date() - timedelta(days=n)
    return floor.isoformat()


# Parse all articles from response body; extract _id, storyType, pathname, displayDate, title
def parse_articles(body: bytes) -> list[dict]:
    try:
        import json
        data = json.loads(body)
    except Exception:
        return []
    articles = data if isinstance(data, list) else None
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                articles = v
                break
    if not articles:
        return []
    result = []
    for a in articles:
        ad = a.get("articleDates") or {}
        result.append({
            "_id":        a.get("_id") or a.get("id"),
            "storyType":  a.get("storyType"),
            "pathname":   a.get("pathname"),
            "displayDate": (
                ad.get("displayDate") or ad.get("publishedAt")
                or a.get("displayDate") or a.get("publishedAt") or a.get("date")
            ),
            "title": a.get("title") or "",
        })
    return result


# Build pagination cursor URL from lastId + lastDisplayDate
def build_cursor_url(last_id: str, last_date: str) -> str:
    return f"{TIMELINE_BASE}?size=16&lastId={last_id}&lastDisplayDate={last_date}&lang=en"


# Fetch feed HTML page via plain httpx; return HTTP status code
def fetch_feedpage(headers: dict) -> int:
    feed_hdrs = {k: v for k, v in headers.items() if k.lower() in {"user-agent", "accept-language", "accept"}}
    try:
        resp = httpx.get(TARGET_URL, headers=feed_hdrs, follow_redirects=True, timeout=30)
        return resp.status_code
    except OSError as e:
        print(f"[coindesk] fetch_feedpage error: {e}", file=sys.stderr)
        return -1


# Attempt re-warm: httpx feedpage first (cheap), then browser re-warm as fallback
async def try_rewarm(failing_url: str, headers: dict) -> tuple[dict, bytes | None, str]:
    print("[coindesk] [rewarm] Attempting httpx feedpage re-warm …", file=sys.stderr)
    fp_status = fetch_feedpage(headers)
    print(f"[coindesk] [rewarm] httpx feedpage GET → {fp_status}", file=sys.stderr)
    time.sleep(1.0)

    resp = httpx.get(failing_url, headers=headers, follow_redirects=True, timeout=30)
    if resp.status_code == 200:
        print("[coindesk] [rewarm] httpx feedpage re-warm SUCCESS", file=sys.stderr)
        return headers, resp.content, "httpx"

    print(f"[coindesk] [rewarm] httpx failed ({resp.status_code}) → browser re-warm …", file=sys.stderr)
    new_headers, _, _ = await browser_load_feed(CLICKS_REWARM)
    if not new_headers:
        print("[coindesk] [rewarm] browser re-warm produced no headers — fatal", file=sys.stderr)
        return headers, None, "fatal"

    resp2 = httpx.get(failing_url, headers=new_headers, follow_redirects=True, timeout=30)
    if resp2.status_code == 200:
        print("[coindesk] [rewarm] browser re-warm SUCCESS (httpx feedpage insufficient)", file=sys.stderr)
        return new_headers, resp2.content, "browser"

    print(f"[coindesk] [rewarm] browser re-warm also failed ({resp2.status_code}) — fatal", file=sys.stderr)
    return headers, None, "fatal"


# Run-wide cursor_loop accumulators — mirrors the per-ride scratch dataclass pattern in rider.py.
@dataclass
class _CursorLoopStats:
    ok_calls:               int  = 0
    fallback_count:         int  = 0
    rewarm_count:           int  = 0
    httpx_rewarm_confirmed: bool | None = None
    oldest_date:            str | None  = None
    last_rewarm_t:          float = field(default_factory=time.monotonic)


# Cursor loop: pages backward to stop_date; writes new URLs incrementally to discover shards.
async def cursor_loop(
    headers: dict,
    start_url: str,
    first_body: bytes,
    stop_date: str,
    seen_urls: set,
    discover_dir: Path,
) -> list[dict]:
    year_files: dict[str, object] = {}
    all_entries: list[dict] = []
    stats = _CursorLoopStats()
    t_start = time.monotonic()
    body = first_body
    last_date = ""

    try:
        while True:
            articles = parse_articles(body)
            if not articles:
                print("[coindesk] Empty response — reached API bottom or parse failure. Stopping.", file=sys.stderr)
                break

            _process_batch(articles, seen_urls, year_files, discover_dir, all_entries, stats)

            oldest_in_batch = (articles[-1].get("displayDate") or "")[:10]
            if oldest_in_batch and oldest_in_batch < stop_date:
                print(f"[coindesk] Reached stop_date floor at {oldest_in_batch}. Stopping.", file=sys.stderr)
                break

            if stats.httpx_rewarm_confirmed and time.monotonic() - stats.last_rewarm_t >= REWARM_EVERY:
                fp = fetch_feedpage(headers)
                print(f"[coindesk] [proactive rewarm] httpx feedpage → {fp}", file=sys.stderr)
                stats.last_rewarm_t = time.monotonic()
                stats.rewarm_count += 1

            next_body, next_url, last_id, last_date = _fetch_next_page(articles, headers, stats)

            if next_body is None and next_url:
                headers, next_body, fatal = await _handle_cursor_exhaustion(next_url, headers, stats)
                if fatal:
                    break

            if next_body is None:
                print("[coindesk] Cursor exhausted with no body. Stopping.", file=sys.stderr)
                break

            body = next_body

            if stats.ok_calls % CHECKPOINT_EVERY == 0:
                wall = int(time.monotonic() - t_start)
                new_in_run = sum(1 for e in all_entries if e.get("_new"))
                print(
                    f"[coindesk] checkpoint call={stats.ok_calls} total={len(all_entries)} "
                    f"new={new_in_run} oldest={stats.oldest_date} pivot={last_date[:10]} "
                    f"wall={wall}s rewarms={stats.rewarm_count} fallbacks={stats.fallback_count}",
                    file=sys.stderr,
                )

    finally:
        for fh in year_files.values():
            try:
                fh.close()
            except OSError as e:
                print(f"[coindesk] year shard close error (non-fatal): {e}", file=sys.stderr)

    wall = int(time.monotonic() - t_start)
    new_total = sum(1 for e in all_entries if e.get("_new"))
    print(
        f"[coindesk] cursor_loop done: calls={stats.ok_calls} total={len(all_entries)} "
        f"new={new_total} oldest={stats.oldest_date} wall={wall}s "
        f"rewarms={stats.rewarm_count} fallbacks={stats.fallback_count}",
        file=sys.stderr,
    )
    return all_entries


# Process and incrementally write this batch: build entries, filter live-blogs, dedup, track oldest_date.
def _process_batch(
    articles:     list[dict],
    seen_urls:    set,
    year_files:   dict,
    discover_dir: Path,
    all_entries:  list[dict],
    stats:        _CursorLoopStats,
) -> None:
    for a in articles:
        entry = _build_entry(a)
        if entry is None:
            continue
        if _is_live_blog(entry["url"]):
            continue
        is_new = entry["url"] not in seen_urls
        if is_new:
            seen_urls.add(entry["url"])
            _append_to_shard(entry, year_files, discover_dir)
        all_entries.append({**entry, "_new": is_new})
        d = entry["publication_date"][:10] if entry["publication_date"] else ""
        if d and (stats.oldest_date is None or d < stats.oldest_date):
            stats.oldest_date = d


# Build next cursor; fall back to N-1, N-2 articles on 403. Return (body, url, last_id, last_date).
def _fetch_next_page(
    articles: list[dict], headers: dict, stats: _CursorLoopStats,
) -> tuple[bytes | None, str, str, str]:
    next_body = None
    next_url = ""
    last_id = last_date = ""
    for fb in range(min(MAX_CURSOR_FALLBACKS, len(articles))):
        anchor = articles[-(1 + fb)]
        last_id = anchor.get("_id") or ""
        last_date = anchor.get("displayDate") or ""
        if not last_id or not last_date:
            continue
        next_url = build_cursor_url(last_id, last_date)

        time.sleep(CALL_DELAY)
        resp = httpx.get(next_url, headers=headers, follow_redirects=True, timeout=30)

        if resp.status_code == 200:
            if fb > 0:
                stats.fallback_count += 1
                print(
                    f"[coindesk]   call {stats.ok_calls + 1}: 200 FALLBACK-{fb} "
                    f"anchor={last_id[:8]} pivot={last_date[:10]}",
                    file=sys.stderr,
                )
            next_body = resp.content
            stats.ok_calls += 1
            break

        snippet = resp.content[:80].decode("utf-8", errors="replace")
        print(
            f"[coindesk]   call {stats.ok_calls + 1}: {resp.status_code} fb={fb} "
            f"pivot={last_date[:10]} {snippet}",
            file=sys.stderr,
        )

    return next_body, next_url, last_id, last_date


# All cursor fallbacks exhausted → try re-warm. Return (headers, body, fatal) — fatal=True means stop.
async def _handle_cursor_exhaustion(
    next_url: str, headers: dict, stats: _CursorLoopStats,
) -> tuple[dict, bytes | None, bool]:
    new_headers, rewarm_body, method = await try_rewarm(next_url, headers)
    if method == "fatal" or rewarm_body is None:
        print("[coindesk] FATAL: re-warm failed. Stopping.", file=sys.stderr)
        return headers, None, True
    stats.rewarm_count += 1
    stats.last_rewarm_t = time.monotonic()
    stats.ok_calls += 1
    if method == "httpx" and stats.httpx_rewarm_confirmed is None:
        stats.httpx_rewarm_confirmed = True
    elif method == "browser" and stats.httpx_rewarm_confirmed is None:
        stats.httpx_rewarm_confirmed = False
    return new_headers, rewarm_body, False


# Build output entry dict from raw article dict; return None if pathname or date missing
def _build_entry(a: dict) -> dict | None:
    pathname = a.get("pathname") or ""
    display_date = (a.get("displayDate") or "")[:10]
    if not pathname or len(display_date) < 10:
        return None
    url = COINDESK_BASE + pathname
    iso = f"{display_date}T00:00:00+00:00"
    return {
        "url":              url,
        "lastmod":          iso,
        "publication_date": iso,
        "title":            a.get("title") or "",
        "section":          _extract_section(pathname),
    }


# Extract first path segment as section (e.g. /markets/2024/... → markets)
def _extract_section(pathname: str) -> str:
    parts = pathname.strip("/").split("/")
    return parts[0] if parts else "unknown"


# Return True if URL is a CoinDesk live-blog: slug starts with "live-"
def _is_live_blog(url: str) -> bool:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    return slug.startswith("live-")


# Append one entry line to the appropriate per-year discover shard (streaming, line-buffered)
def _append_to_shard(entry: dict, year_files: dict, discover_dir: Path) -> None:
    date_str = entry["publication_date"][:10]
    year = date_str[:4]
    if year not in year_files:
        p = discover_dir / f"coindesk_{year}.txt"
        year_files[year] = open(p, "a", encoding="utf-8", buffering=1)
    year_files[year].write(f"{date_str}\t{entry['url']}\n")


# Read all per-year discover shards; return set of known URLs
def load_discover(discover_dir: Path) -> set[str]:
    seen: set[str] = set()
    if not discover_dir.exists():
        return seen
    for shard in discover_dir.glob("coindesk_*.txt"):
        with open(shard, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if "\t" in line:
                    seen.add(line.split("\t", 1)[1])
    return seen


# Read discover shards filtered by year or date range; return [{url, publication_date}].
def load_discover_filtered(
    discover_dir: Path,
    year: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    if not discover_dir.exists():
        return []
    if year is not None:
        shards = [discover_dir / f"coindesk_{year}.txt"]
        shards = [s for s in shards if s.exists()]
    else:
        shards = sorted(discover_dir.glob("coindesk_*.txt"))
    entries: list[dict] = []
    for shard in shards:
        with open(shard, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if "\t" not in line:
                    continue
                date_col, url = line.split("\t", 1)
                if from_date and date_col < from_date:
                    continue
                if to_date and date_col > to_date:
                    continue
                entries.append({
                    "url": url,
                    "publication_date": f"{date_col}T00:00:00+00:00",
                })
                if limit is not None and len(entries) >= limit:
                    return entries
    return entries
