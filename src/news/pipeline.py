# INFRASTRUCTURE
import dataclasses
import json
import logging
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from src.news.platform import Platform
from src.news.engine.dedup import filter_new_entries
from src.news.engine.scrape import scrape_entries, RegwallGuardError
from src.news.engine.proxy_pool import box_lock
from src.news.engine.proxy_pool.janitor import Janitor
from src.news.engine.proxy_pool.logger import AcquireLogger
from src.news.engine.proxy_pool.scrape import scrape_entries_proxy
from src.news.engine.scrape_job import scrape_chunks_raw, _append_to_raw_manifest, _update_blocked_urls
from src.news.engine.browser_reporter import write_scrape_report
from src.news.engine.proxy_riding.scrape import scrape_entries_riding, RidingScrapeConfig
from src.news.engine.proxy_riding.reporter import write_riding_report
from src.news.engine.publish import pub_date_str

PROJECT_ROOT = Path(__file__).parent.parent.parent   # websearch/

LOG_DIR = PROJECT_ROOT / "src" / "logs"
DATA_ROOT = PROJECT_ROOT / "data" / "news"

PRECONDITION_TIMEOUT = 10
SCRAPE_CHUNK_SIZE = 200   # URLs per scrape chunk; controls crash-loss window


# ORCHESTRATOR

# Discover + discover-update only — no dedup/scrape/clean/publish. CoinDesk standalone job.
async def run_discover_only(platform: Platform) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = _setup_logging(platform.name)
    log.info(f"=== {platform.name} discover-only started ===")
    if not _check_internet(platform, log):
        log.error("Internet check failed — aborting.")
        sys.exit(1)
    entries = await platform.discover()
    log.info(f"discover → {len(entries)} entries")
    if getattr(platform, "uses_master_list", False):
        master_path = DATA_ROOT / platform.name / "discover" / "master_urls.txt"
        _persist_master_list(entries, master_path, log)
    _write_marker(platform.name, log)
    log.info(f"=== {platform.name} discover-only complete ===")


# Date-filtered scrape job: discover → raw-diff → chunked scrape → raw persist.
# No cleanup, no publish — raw bodies land in data/news/{name}/raw/{hash}.md.
# manifest.jsonl + regwall_urls.txt/empty_urls.txt updated per chunk.
# RegwallGuardError: ok files recovered via raw_dir scan; regwall_abort set, loop stops.
# skip_index param kept for CLI compat but is a no-op (no indexing in this path).
async def run_scrape_only(
    platform: Platform,
    year: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
    skip_index: bool = False,
    n_browsers: int | None = None,
    n_slots: int | None = None,
    cooldown_policy: str | None = None,
    page_timeout_ms: int | None = None,
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = _setup_logging(platform.name)
    job_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filter_desc = (
        f"year={year}" if year
        else f"from={from_date} to={to_date}" if (from_date or to_date)
        else "all"
    )
    log.info(f"=== {platform.name} scrape-only started job_id={job_id} filter={filter_desc} ===")
    if not _check_internet(platform, log):
        log.error("Internet check failed — aborting.")
        sys.exit(1)
    if not hasattr(platform, "load_scrape_entries"):
        log.error(f"--scrape-only not supported for {platform.name} (no load_scrape_entries)")
        sys.exit(1)

    entries = platform.load_scrape_entries(year=year, from_date=from_date, to_date=to_date, limit=limit)
    log.info(f"discover → {len(entries)} candidate URL(s) after filter")
    if not entries:
        log.info("No entries in date range — done.")
        _write_marker(platform.name, log)
        return

    raw_dir = DATA_ROOT / platform.name / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_ext = ".html" if platform.scrape_engine == "proxy_riding" else ".md"
    new_entries, n_skip, _ = filter_new_entries(entries, raw_dir, platform.name, mode="raw", raw_ext=raw_ext)
    log.info(f"dedup → {len(entries)} total, {n_skip} already in raw, {len(new_entries)} new")
    if not new_entries:
        log.info("All already in raw — done.")
        _write_marker(platform.name, log)
        return

    if platform.scrape_engine == "proxy_riding":
        # Proxy-riding path: bypass chunking — engine owns concurrency, watchdog, requeue.
        riding_cfg = getattr(platform, "riding_scrape_config", None) or RidingScrapeConfig()
        overrides = {k: v for k, v in (("n_browsers", n_browsers), ("n_slots", n_slots), ("cooldown_policy", cooldown_policy), ("page_timeout_ms", page_timeout_ms)) if v is not None}
        if overrides:
            riding_cfg = dataclasses.replace(riding_cfg, **overrides)
        t_job_start = datetime.now(timezone.utc)
        platform_dir = DATA_ROOT / platform.name
        job_dir = DATA_ROOT / platform.name / "scrape_jobs" / job_id
        manifest, state = await scrape_entries_riding(new_entries, platform_dir, riding_cfg, job_dir)
        n_ok = sum(1 for e in manifest if e["status"] == "ok")
        n_failed = sum(1 for e in manifest if e["status"] == "failed")
        wall_s = (datetime.now(timezone.utc) - t_job_start).total_seconds()
        log.info(
            f"=== scrape-only done (proxy_riding): ok={n_ok} failed={n_failed} wall={wall_s:.0f}s ==="
        )
        entries_by_url = {e["url"]: e for e in new_entries}
        ok_manifest_entries = [
            {
                "hash": e["hash"],
                "url": e["url"],
                "publication_date": entries_by_url.get(e["url"], {}).get("publication_date", ""),
            }
            for e in manifest if e.get("status") == "ok"
        ]
        _append_to_raw_manifest(raw_dir, ok_manifest_entries)
        write_riding_report(state, job_dir, t_job_start)
        log.info(f"Job report written to {job_dir}")
    else:
        # Browser path: chunk into 200-URL batches
        chunks = [new_entries[i:i + SCRAPE_CHUNK_SIZE] for i in range(0, len(new_entries), SCRAPE_CHUNK_SIZE)]
        log.info(f"chunked plan: {len(new_entries)} URLs → {len(chunks)} chunk(s) of {SCRAPE_CHUNK_SIZE}")

        t_job_start = datetime.now(timezone.utc)
        totals, job_records, regwall_abort = await scrape_chunks_raw(
            chunks, raw_dir, platform, log
        )

        wall_s = (datetime.now(timezone.utc) - t_job_start).total_seconds()
        rw_rate = totals["regwall"] / max(sum(totals.values()), 1)
        log.info(
            f"=== scrape-only done: ok={totals['ok']} regwall={totals['regwall']}({rw_rate:.1%}) "
            f"empty={totals['empty']} failed={totals['failed']} wall={wall_s:.0f}s"
            + (" [REGWALL ABORT]" if regwall_abort else "") + " ==="
        )
        job_dir = DATA_ROOT / platform.name / "scrape_jobs" / job_id
        write_scrape_report(job_dir, job_records, t_job_start, len(new_entries), filter_desc, regwall_abort)
        log.info(f"Job report written to {job_dir}")
    _write_marker(platform.name, log)
    log.info(f"=== {platform.name} scrape-only complete job_id={job_id} ===")


# Run the full news pipeline for the given platform in-process.
# proxy_pool path (TheBlock): discover → dedup → scrape(raw) → clean-pass → collection_dir. Indexing decoupled.
# browser path (CoinDesk): raw-only — scrape → raw_dir; no cleanup, no publish.
# dedup: mode="raw" (file existence check in data/news/{name}/raw/).
# proxy_pool: persist dead/failed to dead_urls.txt/failed_urls.txt; browser: regwall/empty_urls.txt.
# Janitor lifecycle preserved for proxy_pool (box_lock, start_job, end_job, AcquireLogger).
# skip_index kept for CLI compat — no-op (no indexing in this path).
async def run_pipeline(platform: Platform, skip_index: bool = False) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = _setup_logging(platform.name)
    log.info(f"=== {platform.name} pipeline started ===")

    if not _check_internet(platform, log):
        log.error("Internet check failed — aborting.")
        sys.exit(1)

    platform_dir = DATA_ROOT / platform.name
    discover_dir = platform_dir / "discover"
    raw_dir      = platform_dir / "raw"

    discover_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    if platform.scrape_engine == "proxy_pool":
        # Proxy-pool path: unified job lifecycle spans discover + dedup + scrape.
        # start_job BEFORE AcquireLogger so Janitor wipes log_dir before the JSONL is opened.
        log_dir    = platform_dir / "proxy_pool_logs"
        report_dir = platform_dir / "proxy_pool_reports"
        jobs_dir   = platform_dir / "proxy_pool_jobs"
        job_id     = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        manifest: list[dict] = []
        new_entries: list[dict] = []
        n_ok = 0

        with box_lock.acquire(job_id, f"{platform.name} discover+scrape"):
            j      = Janitor(jobs_dir, log_dir, report_dir)
            j.start_job(job_id)
            logger = AcquireLogger(total_urls=0, log_dir=log_dir)
            try:
                # Stage 1 — discover (proxy_pool)
                log.info("STAGE discover …")
                entries = await platform.discover(logger=logger)
                if not entries:
                    log.error("discover returned 0 articles — aborting.")
                    _write_marker(platform.name, log)
                    return
                if getattr(platform, "uses_master_list", False):
                    master_path = DATA_ROOT / platform.name / "discover" / "master_urls.txt"
                    _persist_master_list(entries, master_path, log)
                else:
                    discover_snapshot = _write_discover_snapshot(entries, discover_dir)
                    log.info(f"discover → {len(entries)} articles → {discover_snapshot.name}")

                # Stage 2 — dedup against raw (exclude known-dead + known-failed URLs permanently)
                log.info("STAGE dedup …")
                failure_urls: set[str] = set()
                for _fname in ("dead_urls.txt", "failed_urls.txt"):
                    _p = discover_dir / _fname
                    if _p.exists():
                        failure_urls |= {u for u in _p.read_text(encoding="utf-8").splitlines() if u}
                new_entries, n_skip_raw, n_excluded = filter_new_entries(
                    entries, raw_dir, platform.name, mode="raw",
                    exclude_urls=failure_urls if failure_urls else None,
                )
                log.info(
                    f"dedup → {len(entries)} total, {n_skip_raw} already in raw, "
                    f"{n_excluded} known-failures excluded, {len(new_entries)} new"
                )
                if not new_entries:
                    log.info("Nothing new to scrape — pipeline complete.")
                    _write_marker(platform.name, log)
                    return

                # Stage 3 — scrape (proxy_pool) into raw_dir
                log.info(f"STAGE scrape ({len(new_entries)} URLs) …")
                manifest = scrape_entries_proxy(new_entries, raw_dir, platform.proxy_scrape_config, logger)
                n_ok = sum(1 for e in manifest if e["status"] == "ok")
                n_dead = sum(1 for e in manifest if e["status"] == "dead")
                n_failed = sum(1 for e in manifest if e["status"] == "failed")
                log.info(f"scrape → {n_ok} ok, {n_dead} dead, {n_failed} failed")

            finally:
                logger.close()
                j.end_job(job_id, logger._jsonl_path, len(new_entries), n_ok)

        # Persist raw manifest + blocked-URL lists (after Janitor lifecycle closes)
        entries_by_url = {e["url"]: e for e in new_entries}
        ok_manifest_entries = [
            {
                "hash": e["hash"],
                "url": e["url"],
                "publication_date": entries_by_url.get(e["url"], {}).get("publication_date", ""),
            }
            for e in manifest if e.get("status") == "ok"
        ]
        _append_to_raw_manifest(raw_dir, ok_manifest_entries)
        _update_blocked_urls(discover_dir, manifest, {"dead": "dead_urls.txt", "failed": "failed_urls.txt"})

        # Stage 4 — clean-pass (proxy_pool / TheBlock only): raw → clean MD in collection_dir
        if n_ok > 0:
            log.info(f"STAGE clean ({n_ok} ok entries) …")
            collection_dir = PROJECT_ROOT.parent / "rag-cli" / "data" / "documents" / platform.collection
            stats = _run_clean_pass(platform, ok_manifest_entries, raw_dir, collection_dir, log)
            log.info(
                f"clean → {stats['n_cleaned']} cleaned, {stats['n_bodyless']} body-less, "
                f"{stats['total']} total → {collection_dir}"
            )

    else:
        # Browser path: discover → dedup(raw) → scrape(raw) → persist
        log.info("STAGE discover …")
        entries = await platform.discover()
        if not entries:
            log.error("discover returned 0 articles — aborting.")
            _write_marker(platform.name, log)
            return
        discover_snapshot = _write_discover_snapshot(entries, discover_dir)
        log.info(f"discover → {len(entries)} articles → {discover_snapshot.name}")

        log.info("STAGE dedup …")
        new_entries, n_skip, _ = filter_new_entries(entries, raw_dir, platform.name, mode="raw")
        log.info(f"dedup → {len(entries)} total, {n_skip} already in raw, {len(new_entries)} new")
        if not new_entries:
            log.info("Nothing new to scrape — pipeline complete.")
            _write_marker(platform.name, log)
            return

        log.info(f"STAGE scrape ({len(new_entries)} URLs) …")
        manifest: list[dict] = []
        try:
            manifest = await scrape_entries(
                new_entries, raw_dir, platform.regwall_signals, platform.scrape_config
            )
        except RegwallGuardError as exc:
            manifest = exc.manifest
            log.error(f"STAGE scrape aborted — RegwallGuardError: {exc}")

        # Persist raw manifest + blocked-URL lists
        entries_by_url = {e["url"]: e for e in new_entries}
        ok_manifest_entries = [
            {
                "hash": e["hash"],
                "url": e["url"],
                "publication_date": entries_by_url.get(e["url"], {}).get("publication_date", ""),
            }
            for e in manifest if e.get("status") == "ok"
        ]
        _append_to_raw_manifest(raw_dir, ok_manifest_entries)
        _update_blocked_urls(raw_dir, manifest, {"regwall": "regwall_urls.txt", "empty": "empty_urls.txt"})
        n_ok = sum(1 for e in manifest if e.get("status") == "ok")
        log.info(f"scrape → {n_ok} ok, raw files persisted")

    log.info(f"=== {platform.name} pipeline complete ===")
    _write_marker(platform.name, log)


# FUNCTIONS

# Configure file + stderr logging; return logger
def _setup_logging(name: str) -> logging.Logger:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    log_file = LOG_DIR / f"news_{name}_{today}.log"
    fmt = "[%(asctime)s] %(levelname)s %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    log = logging.getLogger(f"news.{name}")
    log.info(f"Log file: {log_file}")
    return log


# Check internet reachability via platform.precondition_url
def _check_internet(platform: Platform, log: logging.Logger) -> bool:
    try:
        with urllib.request.urlopen(platform.precondition_url, timeout=PRECONDITION_TIMEOUT):
            log.info(f"  [OK] Internet reachable ({platform.precondition_url})")
            return True
    except Exception as e:
        log.error(f"  [FAIL] Internet unreachable: {e}")
        return False


# Persist single master URL list (YYYY-MM-DD\t<url>), set-union append, sorted+deduped.
# Uses lastmod[:10] for date; skips entries without lastmod or url.
# TheBlock-specific: called when platform.uses_master_list is True.
def _persist_master_list(entries: list[dict], master_path: Path, log: logging.Logger) -> None:
    master_path.parent.mkdir(parents=True, exist_ok=True)
    new_lines: set[str] = set()
    for e in entries:
        lastmod = e.get("lastmod", "")
        if not lastmod or len(lastmod) < 10:
            continue
        url = e.get("url", "")
        if not url:
            continue
        new_lines.add(f"{lastmod[:10]}\t{url}")
    existing: set[str] = set()
    if master_path.exists():
        for line in master_path.read_text(encoding="utf-8").splitlines():
            if line:
                existing.add(line)
    merged = existing | new_lines
    master_path.write_text("\n".join(sorted(merged)) + "\n", encoding="utf-8")
    log.info(
        f"master_urls.txt → {len(merged)} lines ({len(new_lines - existing)} new) → {master_path}"
    )


# Write discover snapshot JSON; return path
def _write_discover_snapshot(entries: list[dict], discover_dir: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = discover_dir / f"discover_{ts}.json"
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# Clean ok entries: read raw/{hash}.md → platform.cleanup() → write theblock__{pubdate}__{hash}.md
# to collection_dir. body-less (cleanup → ""): log + append URL to raw_dir.parent/clean/bodyless_urls.txt
# (set-union, sorted). Read-only on raw/. collection_dir created if absent.
# Progress logged every 200 entries. Returns {"n_cleaned", "n_bodyless", "total"}.
def _run_clean_pass(
    platform: Platform,
    ok_entries: list[dict],
    raw_dir: Path,
    collection_dir: Path,
    log: logging.Logger,
) -> dict:
    if not ok_entries:
        return {"n_cleaned": 0, "n_bodyless": 0, "total": 0}
    collection_dir.mkdir(parents=True, exist_ok=True)
    bodyless_path = raw_dir.parent / "clean" / "bodyless_urls.txt"
    bodyless_urls: list[str] = []
    n_cleaned = 0
    total = len(ok_entries)
    for i, entry in enumerate(ok_entries, start=1):
        h = entry["hash"]
        raw_path = raw_dir / f"{h}.md"
        if not raw_path.exists():
            log.warning(f"clean_pass: raw file missing — {raw_path}")
        else:
            raw_html = raw_path.read_text(encoding="utf-8")
            clean_md = platform.cleanup(raw_html, entry)
            if not clean_md:
                log.info(f"clean_pass: body-less — {entry['url']}")
                bodyless_urls.append(entry["url"])
            else:
                pubdate = pub_date_str(entry)
                out_path = collection_dir / f"theblock__{pubdate}__{h}.md"
                out_path.write_text(clean_md, encoding="utf-8")
                n_cleaned += 1
        if i % 200 == 0:
            log.info(f"clean progress {i}/{total} — {n_cleaned} cleaned, {len(bodyless_urls)} body-less")
    n_bodyless = len(bodyless_urls)
    if bodyless_urls:
        bodyless_path.parent.mkdir(parents=True, exist_ok=True)
        existing = set(bodyless_path.read_text(encoding="utf-8").splitlines()) if bodyless_path.exists() else set()
        merged = (existing | set(bodyless_urls)) - {""}
        bodyless_path.write_text("\n".join(sorted(merged)) + "\n", encoding="utf-8")
    log.info(f"clean_pass: {n_cleaned} cleaned / {n_bodyless} body-less / {total} total")
    return {"n_cleaned": n_cleaned, "n_bodyless": n_bodyless, "total": total}


# Write timestamp to last-run marker file
def _write_marker(name: str, log: logging.Logger) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = LOG_DIR / f"news_{name}_last_run.txt"
    marker.write_text(ts + "\n", encoding="utf-8")
    log.info(f"Last run marker: {ts}")
