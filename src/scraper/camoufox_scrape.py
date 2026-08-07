# INFRASTRUCTURE
import asyncio
import logging
import plistlib
import sys
import time
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

from camoufox import launch_options
from camoufox.async_api import AsyncCamoufox
from camoufox.exceptions import CamoufoxNotInstalled

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from mcp.types import TextContent
# From src/scraper/scrape_url.py: same config-hash algorithm used across all scrape paths
# (generic, not path-specific — reused rather than re-implemented, same precedent as
# src/crawler/pipe_scraper.py's own reuse of this function)
from src.scraper.scrape_url import hash_config
# From src/scraper/scrape_logger.py: per-URL JSONL log + sidecar content file — the SAME log file
# and functions scrape_url.py's chromium lane uses; "engine" is the field that tells them apart
from src.scraper.scrape_logger import log_scrape, write_sidecar

logger = logging.getLogger(__name__)

# Playwright's own BrowserType.launch() AND Frame.goto() both default to this value (confirmed in
# the installed playwright package's generated stubs, playwright/async_api/_generated.py) — used
# EXPLICITLY here (not left implicit) so the calibration decision is visible, same style as
# scrape_url.py's page_timeout=30000. Per this project's standing rule, a phase cap is not raised
# above the default of the layer that actually executes it without evidence for the raise — no
# Camoufox-specific measurement exists yet (this milestone's own real runs are the first) to
# justify departing from Playwright's own number for either phase.
_PLAYWRIGHT_DEFAULT_TIMEOUT_MS = 30000

# wait_until for page.goto — domcontentloaded, NOT Playwright's own "load" default. A Cloudflare
# challenge page holds the request open and serves its OWN full page while it runs; the real
# destination's "load" event cannot fire until the challenge resolves and the browser navigates
# onward, so "load" hangs until page_timeout — observed live as a 30s Page.goto timeout on
# guenstiger.de. "domcontentloaded" fires once the challenge page's own DOM is ready, letting goto
# return; the post-navigation render wait below (CAMOUFOX_RENDER_WAIT_S) is what actually gives
# the challenge JS time to finish and the browser to land on the real page before capture.
# pipe_scraper.py's engine already uses "domcontentloaded" for its own goto calls.
_GOTO_WAIT_UNTIL = "domcontentloaded"

# Post-navigation render wait, applied via page.wait_for_timeout after goto (this lane has no
# analog to crawl4ai's delay_before_return_html — raw Playwright, not crawl4ai — so the wait is
# applied directly). Same source and same value as scrape_url.py's delay_before_return_html: a
# self-resolving Cloudflare challenge page needs the browser to finish executing the challenge
# JavaScript before the real destination page is captured. Cloudflare's own docs
# (developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/, section
# "Non-Interactive Challenges", page last updated 2026-07-06) state the visitor must wait until
# the browser finishes processing the challenge JavaScript, "typically ... less than five seconds"
# — taken AS-IS, no invented safety margin added on top. Real-page measurement on guenstiger.de
# (2026-08-05) corroborates it (2.0s -> interstitial, 6.0s -> real product page, 12.0s/20.0s ->
# ~50 bytes over 6.0s) but is not itself the basis for this value.
CAMOUFOX_RENDER_WAIT_S = 5.0

# Hard wall-clock budget for the entire Camoufox acquisition — the only outer guard on this path,
# analog to scrape_url.py's TOTAL_SCRAPE_BUDGET_S. Composed of: Camoufox browser launch 30.0s
# (_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, Playwright's own BrowserType.launch() default — no
# Camoufox-specific evidence to lower it) + page navigation 30.0s
# (_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, Playwright's own Frame.goto() timeout — wait_until is
# "domcontentloaded", not Playwright's own "load" default, see _GOTO_WAIT_UNTIL) + post-navigation
# render wait 5.0s (CAMOUFOX_RENDER_WAIT_S, the Cloudflare-documented figure, see its own comment)
# + markdown-conversion browser cold start 1.1s (reused from scrape_url.py's own measured
# chromium/patchright cold-start figure, TOTAL_SCRAPE_BUDGET_S's comment — a legitimate proxy here
# since raw: markdown conversion below ALSO launches a fresh chromium instance via crawl4ai, the
# same class of cost, not a fresh unmeasured guess) = 66.1. Markdown GENERATION itself
# (DefaultMarkdownGenerator's own synchronous CPU work, and page.content()/set_content() parsing a
# potentially large HTML string) gets no reserved share of its own, same honesty caveat as
# TOTAL_SCRAPE_BUDGET_S — it is simply covered by this same outer guard, not separately bounded.
TOTAL_CAMOUFOX_BUDGET_S = 66.1

# Short descriptions for the acquisition-error states this lane can render, same pattern and same
# two entries as scrape_url.py's _ACQUISITION_ERROR_MESSAGES ("exception" has no entry there either
# — its detail already goes to cli.log via logger.warning, not worth guessing a message for it).
_CAMOUFOX_ACQUISITION_ERROR_MESSAGES = {
    "browser_missing": "camoufox browser binary missing — run `./venv/bin/python -m camoufox fetch` to install it",
    "budget_exhausted": f"camoufox acquisition exceeded the total time budget ({TOTAL_CAMOUFOX_BUDGET_S}s)",
}


# ORCHESTRATOR
# Runs the Camoufox lane end to end for one URL: acquisition, JSONL logging (SAME log file/schema
# as scrape_url.py's chromium lane, "engine" is the discriminator), sidecar content, rendered
# acquisition-facts block. Mirrors scrape_url_workflow's shape exactly. See _format_camoufox_output
# for why this lane gets its own renderer rather than reusing _format_scrape_output.
async def scrape_url_camoufox_workflow(url: str, block_images: bool = False) -> list[TextContent]:
    t_total = time.perf_counter()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    domain = (urlparse(url).hostname or "").removeprefix("www.")
    logger.info("Scraping via camoufox: %s", url)

    content, meta = await try_scrape_camoufox(url, block_images=block_images)
    total_wall = round((time.perf_counter() - t_total) * 1000)

    # outcome: same three acquisition_error states as the chromium lane, same "ok"-if-content-came-
    # back-else-"empty" fallback. A markdown-conversion failure is NOT its own outcome value:
    # outcome describes whether ACQUISITION produced a result, and raw HTML IS a result that came
    # back — see content_is_raw_html/markdown_conversion_error for that separate, categorically
    # different fact.
    outcome = meta.get("acquisition_error") or ("ok" if content else "empty")
    # mode: reuses the EXISTING field (scrape_logger.py's schema), describing what kind of content
    # is in the log/sidecar — "markdown" normally, "raw_html" when conversion failed and the
    # captured HTML is what's actually stored (see try_scrape_camoufox's content_is_raw_html).
    mode = "raw_html" if meta.get("content_is_raw_html") else "markdown"
    content_path = write_sidecar(url, ts, content, outcome, mode)
    log_scrape({
        "ts": ts, "url": url, "domain": domain, "mode": mode, "outcome": outcome,
        "engine": "camoufox",
        "timings_ms": {"total_wall": total_wall},
        "http_status": meta.get("status_code"),
        "bytes_returned": len(content.encode("utf-8")) if content else 0,
        "bytes_raw_markdown": meta.get("raw_markdown_bytes", 0),
        "content_path": content_path,
        "landed_url": meta.get("landed_url"),
        "markdown_conversion_error": meta.get("markdown_conversion_error"),
        "content_is_raw_html": meta.get("content_is_raw_html", False),
        # config_hash computed ONCE, inside try_scrape_camoufox itself (unlike the chromium lane,
        # where the workflow computes it) — read back here, never re-hashed, so this record's hash
        # always matches the one try_scrape_camoufox's own caller (tests, future callers) would see.
        "config_hash": meta.get("config_hash"), "config": meta.get("config"),
    })
    logger.info("Camoufox scrape complete: %s (%d chars, outcome=%s)", url, len(content), outcome)
    return [TextContent(type="text", text=_format_camoufox_output(url, content, meta))]


# FUNCTIONS

# Single-call Camoufox (Playwright-Firefox, fingerprint spoofing compiled in at C++ level)
# acquisition; return (raw_markdown, meta). A SECOND, parallel acquisition lane beside crawl4ai's
# chromium path (src/scraper/scrape_url.py) — not a fallback, no trigger logic lives here or
# anywhere else. The calling agent (ad-hoc) or run operator (pipe) chooses this lane deliberately;
# CLI wiring for both is later milestones, not this module. No content judgment, no verdicts —
# same fact-reporting contract as the rest of the scrape surface since 2026-08-05 (see
# process-docs/scrape_pipeline/content_judgment_removal_2026-08-05.md); returns whatever came
# back, unconditionally. Fail-soft throughout: any exception degrades to ("", meta with
# acquisition_error set), never a raise to the caller.
#
# meta keys: acquisition_error (None | "budget_exhausted" | "browser_missing" | "exception" — ONLY
#            set when ACQUISITION itself produced no result at all (no HTML ever captured), never
#            a content verdict AND never set for a markdown-conversion failure — see
#            markdown_conversion_error below for that, a categorically different state),
#            status_code (Playwright Response.status, the FIRST hop's status is not separately
#            tracked here — Playwright's own goto() already resolves multi-hop redirects to one
#            Response for the final hop, unlike crawl4ai's own multi-hop tracking),
#            landed_url (Playwright Page.url after goto — RAW, no comparison, no verdict, same
#            posture as the landed-URL surface elsewhere in this project: both URLs are facts, the
#            agent compares them if it wants to),
#            raw_markdown_bytes (byte length of raw_markdown itself — 0 when conversion failed,
#            literally true; NOT the byte length of whatever `content` this function returns, see
#            content_is_raw_html below),
#            markdown_conversion_error (str | None — set when acquisition SUCCEEDED (real HTML was
#            captured) but crawl4ai's raw: pipeline failed to convert it to markdown; carries
#            crawl4ai's own error_message verbatim, an OBSERVATION not a verdict, same posture as
#            crawl4ai_error_message elsewhere in this project. Still reachable for other crawl4ai
#            conversion failures — only the "[" trigger below is closed:
#            crawl4ai's OWN internal urlparse() call on a raw://<html> pseudo-URL raises "Invalid
#            IPv6 URL" whenever the HTML contains a bare "[" before the first "/" in the document
#            (e.g. an early inline <script> with a JS array literal, found via a real run against
#            idealo.de) — the "//" is what makes urlparse expect a netloc at all. crawl4ai treats
#            "raw:" and "raw://" as equivalent prefixes (async_webcrawler.py's _is_raw_url check,
#            async_crawler_strategy.py's raw-html branch, upstream's own
#            test_raw_html_browser.py::test_raw_prefix_variations) so _html_to_markdown below uses
#            "raw:" — no netloc parsing is attempted for that form, closing this trigger without a
#            crawl4ai patch or a hand-rolled converter. Same fix applies to
#            src/crawler/pipe_scraper.py's _own_fallback_rescue, which reuses the exact same call),
#            content_is_raw_html (bool — True when markdown_conversion_error is set and `content`
#            below is therefore the RAW CAPTURED HTML, not markdown; the contract "returns whatever
#            came back, unconditionally" means the real HTML already in hand is never silently
#            discarded as "" just because the markdown step failed — the caller still gets the
#            captured page, in whichever format is actually available, with an explicit flag
#            saying which),
#            config (launch-option stamp — see _build_camoufox_kwargs/_extract_camoufox_config_stamp),
#            config_hash (hash_config(config) — computed HERE, unlike scrape_url.py's try_scrape
#            where the caller/workflow computes it; this module has no calling workflow yet, so
#            the hash is computed inline to be available to this milestone's own tests/real runs)
async def try_scrape_camoufox(url: str, block_images: bool = False) -> tuple[str, dict]:
    kwargs = _build_camoufox_kwargs(block_images)
    _empty_meta: dict = {
        "acquisition_error": None, "status_code": None, "landed_url": None,
        "raw_markdown_bytes": 0, "markdown_conversion_error": None, "content_is_raw_html": False,
        "config": {"config_incomplete": True}, "config_hash": None,
    }

    # Guarded span: launch-option resolution (where CamoufoxNotInstalled actually surfaces, see
    # comment below) through markdown conversion. Mirrors try_scrape's _acquire() shape.
    async def _acquire() -> tuple[str, dict]:
        # Resolved ONCE, ourselves, via the SAME function AsyncCamoufox would otherwise call
        # internally (camoufox.launch_options) — then handed back via from_options= below so
        # AsyncCamoufox does NOT re-resolve (and therefore does NOT re-generate a SECOND, DIFFERENT
        # random BrowserForge fingerprint). This is also where CamoufoxNotInstalled actually raises
        # (launch_path(), called at the end of launch_options() to resolve executable_path) — it
        # surfaces here, before any browser is launched, not inside AsyncCamoufox itself once
        # from_options is already provided.
        resolved = await asyncio.get_event_loop().run_in_executor(
            None, partial(launch_options, **kwargs)
        )
        await asyncio.get_event_loop().run_in_executor(
            None, _ensure_no_focus_steal, resolved.get("executable_path")
        )
        config_stamp = _extract_camoufox_config_stamp(kwargs, resolved)
        meta: dict = {**_empty_meta, "config": config_stamp, "config_hash": hash_config(config_stamp)}

        async with AsyncCamoufox(from_options=resolved) as browser:
            page = await browser.new_page()
            response = await page.goto(
                url, timeout=_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, wait_until=_GOTO_WAIT_UNTIL
            )
            await page.wait_for_timeout(CAMOUFOX_RENDER_WAIT_S * 1000)
            landed_url = page.url
            status_code = response.status if response else None
            html = await page.content()
        # Camoufox's browser (headed, real Firefox process — the memory-footprint field evidence
        # this module's calibration weighed) is closed above before markdown conversion starts,
        # not held open any longer than needed for a second, unrelated browser launch below.
        #
        # try/except here (in addition to _html_to_markdown's own internal one) is deliberate
        # defense in depth, not paranoia: it guarantees ANY failure at the conversion layer —
        # whether crawl4ai swallows it internally (the observed idealo.de shape) or something else
        # raises outright — is funneled into markdown_conversion_error/content_is_raw_html, NEVER
        # into acquisition_error. Acquisition already succeeded by this point (real HTML in `html`)
        # — a downstream conversion failure must never be reported as if nothing was acquired.
        try:
            raw_markdown, conversion_error = await _html_to_markdown(html)
        except Exception as e:
            raw_markdown, conversion_error = "", str(e)

        if conversion_error:
            logger.warning("Camoufox markdown conversion failed for %s: %s", url, conversion_error)
            content, content_is_raw_html = html, True
        else:
            content, content_is_raw_html = raw_markdown, False

        meta.update({
            "status_code": status_code, "landed_url": landed_url,
            "raw_markdown_bytes": len(raw_markdown.encode("utf-8")),
            "markdown_conversion_error": conversion_error,
            "content_is_raw_html": content_is_raw_html,
        })
        return content, meta

    try:
        return await asyncio.wait_for(_acquire(), timeout=TOTAL_CAMOUFOX_BUDGET_S)
    except asyncio.TimeoutError:
        logger.warning("Camoufox acquisition budget exhausted (%.1fs): %s", TOTAL_CAMOUFOX_BUDGET_S, url)
        return "", {**_empty_meta, "acquisition_error": "budget_exhausted"}
    except CamoufoxNotInstalled as e:
        logger.error(
            "Camoufox browser binary missing for %s — run "
            "`./venv/bin/python -m camoufox fetch` to install it: %s", url, e,
        )
        return "", {**_empty_meta, "acquisition_error": "browser_missing"}
    except Exception as e:
        logger.warning("Failed to scrape %s via camoufox: %s", url, e)
        return "", {**_empty_meta, "acquisition_error": "exception"}


# Walk up from a bundle-internal executable path (.../Foo.app/Contents/MacOS/bin) to the .app root.
# None if executable_path isn't inside a bundle (e.g. a non-macOS layout).
def _find_app_bundle(executable_path: str) -> Path | None:
    for parent in Path(executable_path).parents:
        if parent.suffix == ".app":
            return parent
    return None


# MANDATORY requirement, resolved this session (deferred from milestone 1): the chrome lane solves
# no-focus-steal via macOS `open -g -n -a` (src/search/browser.py) — launching the app bundle
# through LaunchServices with the "don't activate" flag. That mechanism has NO equivalent here:
# Playwright launches the browser process from inside its own internal Node.js driver, which
# exposes no hook to substitute our own subprocess/`open -g` launcher (confirmed: no
# process_creator-style parameter anywhere in the installed playwright package's launch path,
# unlike pydoll's BrowserProcessManager, which is what makes `open -g` possible for the chrome
# lane at all). Camoufox's fetched build IS a real macOS .app bundle though (verified:
# launch_path() resolves to ".../Camoufox.app/Contents/MacOS/camoufox", a genuine bundle, not a
# bare binary) — which makes LSUIElement the right lever: a property of the APP ITSELF, read by
# macOS at NSApplication startup, independent of how the process was spawned (unlike `open -g`,
# which only suppresses LaunchServices' OWN activate-on-open behavior).
#
# Verified empirically, not assumed: a real run (this session) polling the frontmost application
# via `osascript`/System Events every 250ms during a live try_scrape_camoufox call — WITHOUT
# LSUIElement, "camoufox" became frontmost for ~1.2s of a 1.8s run (focus genuinely stolen from the
# calling terminal); WITH LSUIElement=true set on the same bundle, frontmost stayed the calling
# terminal for the ENTIRE run, same URL, same code path. Idempotent (checked before written) and
# cheap (one plist read, a write only the first time per cached browser version) — safe to call on
# every launch. Applied here so BOTH lanes (ad-hoc via scrape_url_camoufox_workflow, and the pipe
# engine switch below) get it for free, per the task's own instruction. macOS only — this project's
# whole Camoufox posture is macOS-first, same as src/search/browser.py's own `open -g` mechanism;
# a silent no-op elsewhere (there is no bundle to patch on a non-macOS layout in the first place).
def _ensure_no_focus_steal(executable_path: str | None) -> None:
    if sys.platform != "darwin" or not executable_path:
        return
    app_path = _find_app_bundle(executable_path)
    if app_path is None:
        return
    plist_path = app_path / "Contents" / "Info.plist"
    try:
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        if data.get("LSUIElement") is True:
            return
        data["LSUIElement"] = True
        with open(plist_path, "wb") as f:
            plistlib.dump(data, f)
    except Exception as e:
        logger.warning("Could not set LSUIElement on %s (no-focus-steal not applied): %s", plist_path, e)


# Build the plain kwargs this module hands to camoufox.launch_options()/AsyncCamoufox — the
# calibrated core parameter surface, every value justified below. Every parameter NOT listed here
# (fonts, addons, exclude_addons, screen, window, fingerprint_preset, ff_version, main_world_eval,
# disable_coop, block_webrtc, webgl_config, firefox_user_prefs, args, env, browser,
# executable_path, debug, virtual_display, persistent_context, fingerprint, config) is left at
# its library default DELIBERATELY, on one blanket rule: Camoufox/BrowserForge's own defaults are
# built to mimic the real statistical distribution of device characteristics (camoufox.com/stealth
# — "Camoufox will make your browser look like a Linux user 5% of the time..."); hand-setting any
# of them without a specific measured reason re-introduces exactly the kind of inconsistent,
# non-representative fingerprint the stealth doc warns is what gets Camoufox detected. The
# `config` dict specifically must NEVER be hand-populated — camoufox.com/python/config: "This
# isn't recommended, as Camoufox will populate this data for you automatically."
def _build_camoufox_kwargs(block_images: bool) -> dict:
    return {
        # Fixed decision (made with the user): a visible window during scrapes is accepted.
        # Field evidence (r/webscraping, 2025-2026): headless (true and virtual) is the
        # most-detected posture; headed is strongest.
        "headless": False,
        # Fixed to the REAL host OS (this machine), not left at Camoufox's own default (random
        # choice among windows/macos/linux). Reasoning: this module runs headed with a REAL
        # visible window on a REAL screen — camoufox.com/python/browserforge notes headful mode
        # generates its max screen size from the ACTUAL monitor dimensions regardless of which OS
        # is spoofed. Spoofing "windows" or "linux" while the real, visible rendering surface is
        # macOS risks exactly the kind of internal fingerprint inconsistency the stealth doc
        # (camoufox.com/stealth) says gets Camoufox flagged ("a MacOS user agent with a Windows
        # DirectX renderer... will be flagged") — os=list-random makes sense for many
        # headless/datacenter instances at scale; for one deliberate local headed instance,
        # matching the real host OS is the only choice with no plausible mismatch.
        "os": "macos",
        # Left OFF (library default), NOT because it is not on the calibration surface, but for a
        # concrete reason: this module's flow is goto() + content() only, no mouse-driven
        # interaction (no click/hover/scroll). humanize's cursor-movement algorithm
        # (camoufox.com/fingerprint/cursor-movement) only fires on explicit Playwright mouse
        # actions this module never performs — enabling it would add up to its own maxTime
        # (default 1.5s per the docs) of wall time for a benefit that does not apply to this
        # interaction shape. Revisit if a later milestone adds click-driven interaction (e.g.
        # consent-wall dismissal).
        # "humanize": not set
        #
        # Left OFF (library default), a DELIBERATE reversal of the earlier probe (which ran with
        # geoip=True) after reading the installed source (camoufox/ip.py, camoufox/utils.py):
        # without a proxy, geoip=True calls camoufox's public_ip() SYNCHRONOUSLY during option
        # resolution — a real, previously-invisible network round-trip against up to 6 third-party
        # IP-echo services (api.ipify.org, checkip.amazonaws.com, ...) at timeout=5s each, a
        # genuine (if unlikely) worst case of 30s added to EVERY acquisition before the browser
        # even launches. geoip's documented core value is proxy-IP matching
        # (camoufox.com/python/geoip: "heavily recommended if you are using proxies") — this
        # project has no proxy (fixed decision). The secondary benefit (aligning spoofed
        # timezone/locale/WebRTC-IP with our REAL residential egress IP) is real but unverified in
        # magnitude, and per the task's own field evidence, Akamai's detection of Camoufox is tied
        # to datacenter IPs, not residential ones — meaning the earlier probe's pass against
        # idealo's Akamai wall cannot be specifically attributed to geoip=True rather than to
        # running from a residential IP at all. Given a concrete, newly-discovered cost (a new
        # external network dependency, unbounded up to 30s, on every single acquisition) against
        # an unverified benefit, this module leaves it off. Revisit if this project ever adds
        # proxy support (where geoip's documented core benefit actually applies).
        # "geoip": not set
        #
        "block_images": block_images,
        # WebGL/GPU stays ON — fixed decision (made with the user): do NOT set block_webgl.
        # camoufox.com/python/usage's own warning: "To prevent leaks, only use this for special
        # cases." Same posture as the chromium path (scrape_url.py's enable_stealth deliberately
        # avoids the GPU-disable flags for the same leak-risk reason).
        # "block_webgl": not set
        #
        # Left OFF (library default) — this module does one single-page fetch per call, no
        # page.go_back()/go_forward(), no benefit from caching across requests; enabling costs
        # more memory (camoufox.com/python/usage: "Disabled by default as it uses more memory"),
        # and Camoufox's memory footprint is already field-reported as notably higher than
        # patchright/undetected-chromium — no reason to add to it for zero benefit here.
        # "enable_cache": not set
        #
        # locale: left unset (library default — BrowserForge picks one consistent with the
        # generated fingerprint's OS/region distribution). Hand-picking a fixed locale would be the
        # same class of non-representative override the stealth doc warns against, with no
        # measured reason to override it here (no geoip, so there is no target-IP locale to match
        # against in the first place).
        #
        # No proxy parameter at all — fixed decision: this project scrapes from a residential IP
        # and throttles instead of scaling.
        "timeout": _PLAYWRIGHT_DEFAULT_TIMEOUT_MS,
    }


# Read the config stamp back off the REAL resolved launch_options() output plus this module's own
# input kwargs — never re-declared. `kwargs` is what THIS module explicitly tuned (the calibration
# surface); `executable_path` is read off `resolved` (the REAL object launch_options() built,
# naming which Camoufox browser build actually ran) — the rest of `resolved` (fingerprint config,
# generated seeds, env vars) is DELIBERATELY excluded: it is randomized PER LAUNCH by design
# (BrowserForge), so hashing it would make config_hash unique on every call and defeat its own
# purpose as a "same config" grouping key — same principle as scrape_url.py's extract_config_stamp
# limiting itself to the kwargs this module explicitly tunes, not the full options surface.
def _extract_camoufox_config_stamp(kwargs: dict, resolved: dict) -> dict:
    return {
        **kwargs,
        "executable_path": resolved.get("executable_path"),
        "total_budget_s": TOTAL_CAMOUFOX_BUDGET_S,
    }


# HTML -> markdown via crawl4ai's own raw: pipeline — reused EXACTLY as
# src/crawler/pipe_scraper.py's _own_fallback_rescue does (raw: URLs run through the same
# DefaultMarkdownGenerator, exempted from anti-bot/fallback machinery entirely; no hand-rolled
# HTML-to-markdown, no new library). Uses raw_markdown, not fit_markdown — no content filter is
# configured, matching _own_fallback_rescue's own shape exactly (no content SELECTION here either,
# consistent with this module's "no content judgment" contract). Launches its own throwaway
# AsyncWebCrawler (a second, unrelated chromium instance via crawl4ai/patchright) since this
# module has no long-lived crawler to reuse the way pipe_scraper's shared instance does — that
# per-call cost is exactly what TOTAL_CAMOUFOX_BUDGET_S's 1.1s cold-start summand accounts for.
#
# Uses the "raw:" prefix, not "raw://" — crawl4ai's own urlparse() call on a raw://<html>
# pseudo-URL raises "Invalid IPv6 URL" whenever the HTML contains a bare "[" before the first "/"
# in the document (the "//" makes urlparse expect a netloc at all); "raw:" carries no netloc and
# hits none of that parsing. Both prefixes are equivalent in crawl4ai's own contract
# (async_webcrawler.py's _is_raw_url check, async_crawler_strategy.py's raw-html branch, upstream's
# test_raw_html_browser.py::test_raw_prefix_variations) — see try_scrape_camoufox's own meta-keys
# comment for the full finding and its blast radius (also fixed the same way in
# pipe_scraper.py's _own_fallback_rescue).
#
# Returns (raw_markdown, error_message). error_message is None on success. Internally fail-soft
# (never raises) — result.error_message still surfaces whatever crawl4ai's own pipeline fails on
# for OTHER reasons (this only closes the "[" trigger above), so the caller (_acquire) can still
# tell markdown genuinely came back empty from "conversion failed on this HTML" by reading
# error_message here.
async def _html_to_markdown(html: str) -> tuple[str, str | None]:
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(),
        verbose=False,
    )
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw:{html}", config=run_config)
    except Exception as e:
        return "", str(e)
    if result.markdown and result.markdown.raw_markdown:
        return result.markdown.raw_markdown, None
    return "", (getattr(result, "error_message", None) or "crawl4ai raw: conversion produced no markdown")


# Render acquisition facts + full content into one text block — SAME fixed-shape philosophy as
# scrape_url.py's _format_scrape_output (facts always, unconditionally, before a fixed "## Content"
# delimiter; landed URL unconditional, same rule as that lane since this session), but a SIBLING
# function rather than a shared one: the two lanes' fact vocabularies diverge too much to share one
# renderer without conditional logic that would itself violate "always the same shape" — this lane
# has no content_type, no crawl4ai diagnosis, no fallback_to_raw (no fit/raw content SELECTION at
# all here), and has two facts the chromium lane has no concept of at all
# (markdown_conversion_error/content_is_raw_html). Writing a sibling keeps BOTH renderers honest
# about their own actual fact set instead of one function papering over the difference.
def _format_camoufox_output(url: str, content: str, meta: dict) -> str:
    lines = [
        f"# Content from: {url}", "",
        "## Acquisition facts",
        "- Engine: camoufox",
        f"- HTTP status: {meta.get('status_code')}",
        # Unconditional, same rule as the chromium lane since this session — matches, differs, or
        # absent (None, rendered literally) all render the same way; nothing here decides which of
        # these the agent gets to see.
        f"- Landed URL (the URL the browser actually returned content from): {meta.get('landed_url')}",
        f"- Bytes (raw markdown from crawl4ai's raw: conversion): {meta.get('raw_markdown_bytes', 0)}",
        f"- Bytes (content below): {len(content.encode('utf-8')) if content else 0}",
    ]
    # Present ONLY when there is something to say (same conditional-presence precedent as the
    # "Acquisition error" line below and in _format_scrape_output) — but stated PLAINLY, not
    # buried: the agent must know it is reading raw HTML, not markdown, and why.
    if meta.get("content_is_raw_html"):
        lines.append(
            "- Content format: RAW HTML, NOT markdown — the markdown-conversion step failed "
            "(an OBSERVATION off crawl4ai's own raw: pipeline, not a verdict on this page; the "
            f"page already captured is returned as-is rather than discarded): "
            f"{meta.get('markdown_conversion_error')}"
        )
    if meta.get("acquisition_error"):
        reason = _CAMOUFOX_ACQUISITION_ERROR_MESSAGES.get(meta["acquisition_error"], meta["acquisition_error"])
        lines.append(f"- Acquisition error: {reason}")
    lines += ["", "## Content", "", content if content else "(no content returned)"]
    return "\n".join(lines)
