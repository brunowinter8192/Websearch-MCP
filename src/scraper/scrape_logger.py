# INFRASTRUCTURE
import json
import logging
import os
import re
from pathlib import Path

# From src/log_janitor.py: lazy 14-day prune on write
from src.log_janitor import maybe_prune_jsonl, maybe_prune_sidecars

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path(__file__).parent.parent.parent / "src" / "logs" / "scrape_log.jsonl"

# Record schema (one record per scrape_url call):
# {
#   "ts": str (ISO-8601 UTC, millisecond precision),
#   "url": str,
#   "domain": str,
#   "mode": "filtered" (chromium engine, PruningContentFilter fit/raw selection) |
#           "markdown" | "raw_html" (camoufox engine — no content-filter selection on that lane;
#           "raw_html" means content_is_raw_html was set, see camoufox_scrape.py),
#   "outcome": "ok" (content came back) | "empty" (browser succeeded, page had nothing) |
#              "budget_exhausted" | "browser_missing" | "exception" (acquisition itself produced
#              no result — never a content-judgment category; see scrape_url.py meta["acquisition_error"]
#              on the chromium engine, camoufox_scrape.py's try_scrape_camoufox on the camoufox one),
#   "engine": "chromium" | "camoufox" — FIRST-CLASS discriminator between the two acquisition lanes
#             sharing this one log file (scrape_url.py's crawl4ai/chromium path vs
#             camoufox_scrape.py's Camoufox/Firefox path, not a fallback of each other — the agent/
#             operator chooses the lane deliberately). The config stamp already differs
#             structurally between the two (different key sets entirely), but this field exists so
#             a reader filtering the log never has to infer engine from config shape. ABSENT on
#             every record written before this field existed — same convention as every prior field
#             addition (read absence as "predates the field," never as "chromium by default").
#   "timings_ms": {"total_wall": int},
#   "http_status": int | null,            # a fact, not a verdict — status alone no longer gates content
#   "content_type": str | null,           # chromium engine only — camoufox's acquisition path
#                                          # (Playwright's raw Response object) does not expose a
#                                          # convenient content-type header the way crawl4ai's
#                                          # result.headers does; absent (key never written) on
#                                          # "engine": "camoufox" records, not null — a genuinely
#                                          # different fact surface between the two engines, not a
#                                          # missing value on this one
#   "bytes_returned": int | null,
#   "bytes_raw_markdown": int | null,
#   "fallback_to_raw": bool,               # chromium engine only (fit_markdown was too thin, raw_markdown
#                                          # used instead — PruningContentFilter's own fallback, not a
#                                          # garbage check); absent (key never written), not false, on
#                                          # "engine": "camoufox" records — that lane has no fit/raw
#                                          # selection to report on at all
#   "content_path": str | null,           # relative path under log dir, e.g. "scrape_content/<file>.md"
#   "published_date": str | null,         # ISO day precision (YYYY-MM-DD), htmldate-extracted, only on
#                                          # "ok" outcome — chromium engine only. ABSENT (key never
#                                          # written), not null, on every "engine": "camoufox" record:
#                                          # that lane never attempts htmldate extraction at all — same
#                                          # "absent means the concept doesn't apply to this engine,
#                                          # not a missed value" treatment as content_type/
#                                          # fallback_to_raw above and the crawl4ai_* fields below.
#   "markdown_conversion_error": str | null,  # camoufox engine ONLY — crawl4ai's raw:// pipeline's own
#             error_message, verbatim, an OBSERVATION not a verdict, when it failed to convert
#             captured HTML to markdown (see camoufox_scrape.py's try_scrape_camoufox for the real,
#             observed failure shape and its cross-module implication for pipe_scraper.py). Absent
#             (key never written) on "engine": "chromium" records — that lane has no raw:// step of
#             its own to report on.
#   "content_is_raw_html": bool,           # camoufox engine ONLY — True when markdown_conversion_error
#             is set and the logged/sidecar content is therefore the RAW CAPTURED HTML, not markdown
#             (the real page is never silently discarded just because conversion failed). Absent (key
#             never written) on "engine": "chromium" records.
#   "crawl4ai_success": bool | null,      # chromium engine only (crawl4ai's own result.success; null
#                                          # only when the call raised before a result existed).
#                                          # ABSENT (key never written) on "engine": "camoufox"
#                                          # records — crawl4ai is involved there only incidentally,
#                                          # for the raw:// markdown-conversion step, and that step's
#                                          # own diagnosis is not what this field describes
#   "crawl4ai_error_message": str | null, # crawl4ai's own result.error_message verbatim (e.g. "Blocked by anti-bot protection: <reason>"); an OBSERVATION, NOT a verdict — the library's own detector has documented false positives (e.g. reports "Cloudflare JS challenge" on guenstiger.de even when the full product page came back) — never acted on here, and now also surfaced to the caller (scrape_url.py's _format_scrape_output), which must present it the same way. Chromium engine only, same absent-on-camoufox treatment as crawl4ai_success above.
#   "crawl4ai_attempts": int | null,      # result.crawl_stats["attempts"] — total browser attempts across proxies/retries. Chromium engine only.
#   "crawl4ai_resolved_by": str | null,   # result.crawl_stats["resolved_by"]: "direct" | "proxy" | "fallback_fetch" | null. Chromium engine only.
#   "crawl4ai_fallback_fetch_used": bool | null,  # result.crawl_stats["fallback_fetch_used"]. Chromium engine only.
#   "landed_url": str | null,              # BOTH engines. Chromium: crawl4ai's result.redirected_url.
#                                           # Camoufox: Playwright's page.url after goto. Either way
#                                           # RAW/unnormalized — exactly as the engine reported it, no
#                                           # comparison rule applied at write time. Any rule (current
#                                           # or future) can be applied later by whoever reads "url"
#                                           # and "landed_url" together — this log stores the two
#                                           # facts, not a conclusion derived from them. null on any
#                                           # call that never obtained a result object
#                                           # (browser_missing/exception/budget_exhausted before
#                                           # acquisition completed) — present-but-null here (unlike
#                                           # the engine-specific fields above), since landed_url is a
#                                           # concept BOTH engines share, just sometimes unpopulated.
#   "config_hash": str,                    # first 10 hex chars of sha256(sort_keys JSON of "config") — cheap "same config" grouping key. BOTH engines, but never comparable to each other — see "config" below.
#   "config": {                            # BOTH engines, but a STRUCTURALLY DIFFERENT key set per
#                                           # engine (this IS the config-shape difference "engine"
#                                           # above exists so a reader doesn't have to detect it
#                                           # manually). Chromium shape below; camoufox's own shape
#                                           # (headless, os, block_images, timeout, executable_path,
#                                           # total_budget_s — no PruningContentFilter/adapter keys
#                                           # at all) is documented in camoufox_scrape.py's
#                                           # _build_camoufox_kwargs/_extract_camoufox_config_stamp.
#     "headless": bool, "enable_stealth": bool, "adapter": str, "crawler_strategy": str,
#     "magic": bool, "wait_until": str, "page_timeout_ms": int,
#     "delay_before_return_html_s": float,  # explicit render wait before HTML capture, see scrape_url.py comment at its CrawlerRunConfig construction
#     "max_retries": int,
#     "cache_mode": str, "content_filter": str, "content_filter_threshold": float,
#     "content_filter_preserve_tags": list[str],  # HTML tags exempted from pruning recursion — e.g. ["code", "pre"] guards syntax-highlighted code from whitespace-span decomposition (crawl4ai issue #2110)
#     "excluded_selector_hash": str,       # first 8 hex chars of sha256(excluded_selector) — the 426-char selector itself is source-visible, not worth repeating per record
#     "remove_consent_popups": bool,       # crawl4ai's own CMP click-dismissal, alongside (not instead of) excluded_selector; unconditional ~1s cost per scrape, see scrape_url.py comment at its CrawlerRunConfig construction
#     "total_budget_s": float,             # TOTAL_SCRAPE_BUDGET_S — outer wall-clock guard around try_scrape's acquisition (browser call + date extraction + content selection); bounds network/browser hangs only, NOT synchronous CPU inside crawl4ai (markdown gen) — see constant's comment in scrape_url.py
#     "min_content_threshold": int         # fit->raw content-selection fallback threshold, NOT a garbage-verdict threshold
#     # OR, only if try_scrape's config invariant ever breaks: {"config_incomplete": true}
#   }
# }
#
# Historical fields (appear ONLY on records written before the ad-hoc path stopped judging
# content; absent by design on every record from that change onward, not a logging bug):
# "garbage_type" (str|null), "truncated" (bool), "consent_stripped" (bool).
#
# "landed_url" is the reverse case: ABSENT on every record written before this schema added it,
# present on every one from then onward — read its absence on an old record as "this call predates
# the field," not as "no redirect happened."
#
# "same_target" (bool) is historical in BOTH directions — a narrow-window field, not an
# ongoing one: ABSENT before it was introduced alongside "landed_url", PRESENT on records written
# while this scraper still computed a stored same/different verdict, ABSENT again from the date
# that verdict was removed (this scraper reports facts, not conclusions derived from them — an
# agent reading a record has both "url" and "landed_url" already and can compare them itself; see
# process-docs/scrape_pipeline/content_judgment_removal_2026-08-05.md for the same reasoning
# applied to content judgment). A record from that window carrying `same_target` is not broken and
# not a fact this scraper still computes — it is a conclusion this scraper used to compute and no
# longer does.
# Historical "outcome"/"garbage_type" values that no longer occur going forward — a content-verdict
# category, not an acquisition-failure category: "http_error", "cookie_wall", "login_wall",
# "cloudflare", "nav_dump", "minimal_content", "crawl4ai_error". Read an aggregate spanning this
# change as: those categories stopped being PRODUCED (the classifier that emitted them was
# removed), not that those failure modes stopped happening on the live web.
#
# Log path: WEBSEARCH_SCRAPE_LOG_PATH env var → DEFAULT_LOG_PATH fallback.
# Sidecar path: <log_dir>/scrape_content/<ts_safe>_<url_slug>.md


# FUNCTIONS

# Sanitize ISO timestamp for filesystem: replace `:` with `-`
def _sanitize_ts(ts: str) -> str:
    return ts.replace(":", "-")


# Derive URL slug: strip protocol, replace non-alphanumeric with `-`, collapse runs, cap 80 chars
def _url_slug(url: str) -> str:
    slug = re.sub(r'^https?://', '', url)
    slug = re.sub(r'[^a-zA-Z0-9]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')[:80]


# Write sidecar .md to <log_dir>/scrape_content/; return relative path or None on empty/error
def write_sidecar(url: str, ts: str, content: str, outcome: str, mode: str) -> str | None:
    if not content:
        return None
    env = os.environ.get("WEBSEARCH_SCRAPE_LOG_PATH")
    log_path = Path(env) if env else DEFAULT_LOG_PATH
    sidecar_dir = log_path.parent / "scrape_content"
    filename = f"{_sanitize_ts(ts)}_{_url_slug(url)}.md"
    header = (
        f"<!-- url: {url} -->\n"
        f"<!-- ts: {ts} -->\n"
        f"<!-- outcome: {outcome} -->\n"
        f"<!-- bytes: {len(content.encode('utf-8'))} -->\n"
        f"<!-- mode: {mode} -->\n"
    )
    try:
        sidecar_dir.mkdir(parents=True, exist_ok=True)
        (sidecar_dir / filename).write_text(header + "\n" + content, encoding="utf-8")
        maybe_prune_sidecars(sidecar_dir)
        return f"scrape_content/{filename}"
    except Exception as e:
        logger.warning("scrape_logger sidecar write failed: %s", e)
        return None


# Append one JSONL record; path from WEBSEARCH_SCRAPE_LOG_PATH env var; fail-soft
def log_scrape(record: dict) -> None:
    env = os.environ.get("WEBSEARCH_SCRAPE_LOG_PATH")
    log_path = Path(env) if env else DEFAULT_LOG_PATH
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        maybe_prune_jsonl(log_path)
    except Exception as e:
        logger.warning("scrape_log write failed: %s", e)
