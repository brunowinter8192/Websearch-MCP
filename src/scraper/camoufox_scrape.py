# INFRASTRUCTURE
import asyncio
import logging
from functools import partial

from camoufox import launch_options
from camoufox.async_api import AsyncCamoufox
from camoufox.exceptions import CamoufoxNotInstalled

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# From src/scraper/scrape_url.py: same config-hash algorithm used across all scrape paths
# (generic, not path-specific — reused rather than re-implemented, same precedent as
# src/crawler/pipe_scraper.py's own reuse of this function)
from src.scraper.scrape_url import hash_config

logger = logging.getLogger(__name__)

# Playwright's own BrowserType.launch() AND Frame.goto() both default to this value (confirmed in
# the installed playwright package's generated stubs, playwright/async_api/_generated.py) — used
# EXPLICITLY here (not left implicit) so the calibration decision is visible, same style as
# scrape_url.py's page_timeout=30000. Per this project's standing rule, a phase cap is not raised
# above the default of the layer that actually executes it without evidence for the raise — no
# Camoufox-specific measurement exists yet (this milestone's own real runs are the first) to
# justify departing from Playwright's own number for either phase.
_PLAYWRIGHT_DEFAULT_TIMEOUT_MS = 30000

# Hard wall-clock budget for the entire Camoufox acquisition — the only outer guard on this path,
# analog to scrape_url.py's TOTAL_SCRAPE_BUDGET_S. Composed of: Camoufox browser launch 30.0s
# (_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, Playwright's own BrowserType.launch() default — no
# Camoufox-specific evidence to lower it) + page navigation 30.0s
# (_PLAYWRIGHT_DEFAULT_TIMEOUT_MS, Playwright's own Frame.goto() default, wait_until="load" is
# also left at Playwright's own default — no evidence to override) + markdown-conversion browser
# cold start 1.1s (reused from scrape_url.py's own measured chromium/patchright cold-start figure,
# TOTAL_SCRAPE_BUDGET_S's comment — a legitimate proxy here since raw:// markdown conversion below
# ALSO launches a fresh chromium instance via crawl4ai, the same class of cost, not a fresh
# unmeasured guess) = 61.1. Markdown GENERATION itself (DefaultMarkdownGenerator's own synchronous
# CPU work, and page.content()/set_content() parsing a potentially large HTML string) gets no
# reserved share of its own, same honesty caveat as TOTAL_SCRAPE_BUDGET_S — it is simply covered
# by this same outer guard, not separately bounded.
TOTAL_CAMOUFOX_BUDGET_S = 61.1


# ORCHESTRATOR
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
#            captured) but crawl4ai's raw:// pipeline failed to convert it to markdown; carries
#            crawl4ai's own error_message verbatim, an OBSERVATION not a verdict, same posture as
#            crawl4ai_error_message elsewhere in this project. Found via a real run against idealo.de:
#            crawl4ai's OWN internal urlparse() call on the raw://<html> pseudo-URL raises
#            "Invalid IPv6 URL" whenever the HTML contains a bare "[" before the first "/" in the
#            document (e.g. an early inline <script> with a JS array literal) — crawl4ai swallows
#            this internally and returns success=False/markdown=None rather than raising; a
#            pre-existing crawl4ai robustness bug, not fixed here (no crawl4ai patch, no
#            hand-rolled markdown — out of this module's scope) and NOT unique to Camoufox: it
#            equally affects src/crawler/pipe_scraper.py's already-shipped _own_fallback_rescue,
#            which reuses the exact same raw:// call and has never been exercised against HTML
#            with this shape),
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
        config_stamp = _extract_camoufox_config_stamp(kwargs, resolved)
        meta: dict = {**_empty_meta, "config": config_stamp, "config_hash": hash_config(config_stamp)}

        async with AsyncCamoufox(from_options=resolved) as browser:
            page = await browser.new_page()
            response = await page.goto(url, timeout=_PLAYWRIGHT_DEFAULT_TIMEOUT_MS)
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


# FUNCTIONS

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


# HTML -> markdown via crawl4ai's own raw:// pipeline — reused EXACTLY as
# src/crawler/pipe_scraper.py's _own_fallback_rescue does (raw:// URLs run through the same
# DefaultMarkdownGenerator, exempted from anti-bot/fallback machinery entirely; no hand-rolled
# HTML-to-markdown, no new library). Uses raw_markdown, not fit_markdown — no content filter is
# configured, matching _own_fallback_rescue's own shape exactly (no content SELECTION here either,
# consistent with this module's "no content judgment" contract). Launches its own throwaway
# AsyncWebCrawler (a second, unrelated chromium instance via crawl4ai/patchright) since this
# module has no long-lived crawler to reuse the way pipe_scraper's shared instance does — that
# per-call cost is exactly what TOTAL_CAMOUFOX_BUDGET_S's 1.1s cold-start summand accounts for.
#
# Returns (raw_markdown, error_message). error_message is None on success. Internally fail-soft
# (never raises) — a real, observed failure shape (idealo.de): crawl4ai's OWN internal urlparse()
# call on the raw://<html> pseudo-URL raises "Invalid IPv6 URL" whenever the HTML contains a bare
# "[" before the first "/" in the document; crawl4ai's own _crawl_web wrapper catches this
# internally and returns success=False/markdown=None rather than raising, so the ONLY way the
# caller (_acquire) can tell markdown genuinely came back empty from "conversion crashed on this
# HTML" is by reading error_message here. A pre-existing crawl4ai robustness bug, not fixed here —
# see try_scrape_camoufox's own meta-keys comment for the full finding and its blast radius
# (also affects pipe_scraper.py's _own_fallback_rescue, untouched in this milestone).
async def _html_to_markdown(html: str) -> tuple[str, str | None]:
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(),
        verbose=False,
    )
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=f"raw://{html}", config=run_config)
    except Exception as e:
        return "", str(e)
    if result.markdown and result.markdown.raw_markdown:
        return result.markdown.raw_markdown, None
    return "", (getattr(result, "error_message", None) or "crawl4ai raw:// conversion produced no markdown")
