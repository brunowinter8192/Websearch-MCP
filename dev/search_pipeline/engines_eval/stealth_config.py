"""Stealth configuration for search engine testing.
All pydoll levers in one place — tune here, test with 27_stealth_test.py"""

from dataclasses import dataclass, field


@dataclass
class StealthConfig:
    # --- Browser Launch Args ---
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.7680.154 Safari/537.36"
    )
    window_size: str = "1920,1080"
    headless: bool = True           # False for debugging
    headless_new: bool = True       # --headless=new (modern, harder to detect)
    lang: str = "en-US"
    accept_lang: str = "en-US,en;q=0.9"
    disable_blink_features: str = "AutomationControlled"
    disable_features: list[str] = field(default_factory=lambda: [
        "IsolateOrigins", "site-per-process"
    ])
    webrtc_leak_protection: bool = True
    use_gl: str | None = None       # "swiftshader" for software WebGL, None for real GPU
    no_first_run: bool = False      # pydoll adds --no-first-run by default; avoid duplicate
    no_default_browser_check: bool = False  # pydoll adds --no-default-browser-check by default
    disable_reading_from_canvas: bool = False  # canvas fingerprint mitigation
    proxy_server: str | None = None            # --proxy-server=...
    disable_gpu: bool = False                  # --disable-gpu (headless stability)
    no_sandbox: bool = False                   # --no-sandbox (Linux only)
    page_load_state: str = "complete"          # complete, domcontentloaded, interactive
    user_data_dir: str | None = None           # --user-data-dir=... (persistent session)

    # --- Browser Preferences ---
    browser_preferences: dict = field(default_factory=lambda: {
        "profile": {
            "exit_type": "Normal",
            "exited_cleanly": True,
        },
        "safebrowsing": {"enabled": True},
        "autofill": {"enabled": True},
        "search": {"suggest_enabled": True},
        "enable_do_not_track": False,
        "credentials_enable_service": True,
        "credentials_enable_autosignin": True,
        "dns_prefetching": {"enabled": True},
    })

    # --- JS Fingerprint Patches ---
    screen_width: int = 1920
    screen_height: int = 1080
    color_depth: int = 30
    pixel_depth: int = 30
    device_pixel_ratio: float = 2.0
    toolbar_height: int = 85
    navigator_languages: list[str] = field(default_factory=lambda: ["en-US", "en"])
    navigator_platform: str = "MacIntel"
    navigator_hardware_concurrency: int = 10
    navigator_device_memory: int = 8
    patch_computed_style: bool = True   # fix headless CSS color detection
    patch_webgl: bool = False           # WebGL vendor/renderer override
    webgl_vendor: str = "Google Inc. (Apple)"
    webgl_renderer: str = "ANGLE (Apple, ANGLE Metal Renderer: Apple M1 Pro, Unspecified Version)"
    patch_canvas_noise: bool = False    # subtle canvas fingerprint randomization
    patch_permissions: bool = False     # Permissions.query override for notifications

    # --- CDP Network Commands (per-tab, runtime) ---
    set_useragent_override: bool = False        # CDP Network.setUserAgentOverride
    extra_http_headers: dict | None = None      # Network.setExtraHTTPHeaders headers dict
    block_urls: list[str] | None = None         # URLs to block (tracking/analytics)
    disable_cache: bool = False                 # Network.setCacheDisabled

    # --- CDP Emulation (per-tab, runtime) ---
    emulate_network: bool = False       # whether to emulate network conditions
    network_latency: int = 0            # ms
    network_download: int = -1          # bytes/s (-1 = unlimited)
    network_upload: int = -1            # bytes/s

    # --- Context / Interaction ---
    use_contexts: bool = False          # browser.new_context() for cookie isolation
    humanize_click: bool = False        # element.click(humanize=True)
    humanize_type: bool = False         # element.type_text(humanize=True)
    humanize_scroll: bool = False       # scroll with easing/jitter

    # --- Rate Limiter (per-engine overrides) ---
    rate_limits: dict = field(default_factory=lambda: {
        "google": {"max_requests": 5, "window_seconds": 60},
        "google scholar": {"max_requests": 3, "window_seconds": 60},
        "bing": {"max_requests": 10, "window_seconds": 60},
        # PARKED — brave config retained for future dev testing via 27_stealth_test.py
        "brave": {"max_requests": 8, "window_seconds": 60},
        "crossref": {"max_requests": 10, "window_seconds": 60},
    })

    # --- Request delay between engines in test scripts ---
    delay_between_engines: float = 3.0
    delay_between_queries: float = 5.0

    # --- Test Script Constants ---
    max_wait_cycles: int = 15       # polling rounds for result wait
    wait_interval: float = 1.0      # pause between polls (seconds)
    sleep_wait: float = 3.0         # fixed wait for sleep-based engines (seconds)


# Singleton default config
DEFAULT_CONFIG = StealthConfig()

# Builder functions (build_chrome_args, build_js_patches, build_cdp_config) live in _stealth_builders.py
