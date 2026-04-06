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
        "brave": {"max_requests": 8, "window_seconds": 60},
        "startpage": {"max_requests": 10, "window_seconds": 60},
        "mojeek": {"max_requests": 10, "window_seconds": 60},
        "duckduckgo": {"max_requests": 10, "window_seconds": 60},
        "semantic scholar": {"max_requests": 6, "window_seconds": 60},
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


def build_chrome_args(config: StealthConfig) -> list[str]:
    """Convert StealthConfig into list of Chrome CLI arguments."""
    args = [
        f"--user-agent={config.user_agent}",
        f"--window-size={config.window_size}",
        f"--lang={config.lang}",
        f"--accept-lang={config.accept_lang}",
    ]
    if config.disable_blink_features:
        args.append(f"--disable-blink-features={config.disable_blink_features}")
    if config.disable_features:
        args.append(f"--disable-features={','.join(config.disable_features)}")
    if config.no_first_run:
        args.append("--no-first-run")
    if config.no_default_browser_check:
        args.append("--no-default-browser-check")
    if config.use_gl:
        args.append(f"--use-gl={config.use_gl}")
    if config.disable_reading_from_canvas:
        args.append("--disable-reading-from-canvas")
    if config.headless and config.headless_new:
        args.append("--headless=new")
    if config.proxy_server:
        args.append(f"--proxy-server={config.proxy_server}")
    if config.disable_gpu:
        args.append("--disable-gpu")
    if config.no_sandbox:
        args.append("--no-sandbox")
    if config.user_data_dir:
        args.append(f"--user-data-dir={config.user_data_dir}")
    return args


def build_js_patches(config: StealthConfig) -> str:
    """Generate JS fingerprint patch script from config."""
    avail_height = config.screen_height - 23
    languages_json = str(config.navigator_languages).replace("'", '"')

    parts = [
        "(function() {",
        f"    Object.defineProperty(screen, 'width', {{ get: () => {config.screen_width} }});",
        f"    Object.defineProperty(screen, 'height', {{ get: () => {config.screen_height} }});",
        f"    Object.defineProperty(screen, 'availWidth', {{ get: () => {config.screen_width} }});",
        f"    Object.defineProperty(screen, 'availHeight', {{ get: () => {avail_height} }});",
        f"    Object.defineProperty(screen, 'colorDepth', {{ get: () => {config.color_depth} }});",
        f"    Object.defineProperty(screen, 'pixelDepth', {{ get: () => {config.pixel_depth} }});",
        f"    Object.defineProperty(window, 'devicePixelRatio', {{ get: () => {config.device_pixel_ratio} }});",
        f"    Object.defineProperty(window, 'outerWidth', {{ get: () => window.innerWidth }});",
        f"    Object.defineProperty(window, 'outerHeight', {{ get: () => window.innerHeight + {config.toolbar_height} }});",
        f"    Object.defineProperty(navigator, 'platform', {{ get: () => '{config.navigator_platform}' }});",
        f"    Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {config.navigator_hardware_concurrency} }});",
        f"    Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {config.navigator_device_memory} }});",
        f"    Object.defineProperty(navigator, 'languages', {{ get: () => {languages_json} }});",
    ]

    if config.patch_computed_style:
        parts += [
            "    var _origGCS = window.getComputedStyle;",
            "    window.getComputedStyle = function(element, pseudoElt) {",
            "        var style = _origGCS.apply(this, arguments);",
            "        return new Proxy(style, {",
            "            get: function(target, name) {",
            "                var value = target[name];",
            "                if (name === 'color' && value === 'rgb(255, 0, 0)') {",
            "                    return 'rgb(0, 102, 204)';",
            "                }",
            "                return typeof value === 'function' ? value.bind(target) : value;",
            "            }",
            "        });",
            "    };",
        ]

    if config.patch_webgl:
        vendor = config.webgl_vendor.replace("'", "\\'")
        renderer = config.webgl_renderer.replace("'", "\\'")
        parts += [
            "    var _origGetParam = WebGLRenderingContext.prototype.getParameter;",
            "    WebGLRenderingContext.prototype.getParameter = function(parameter) {",
            "        if (parameter === 37445) return '" + vendor + "';",
            "        if (parameter === 37446) return '" + renderer + "';",
            "        return _origGetParam.call(this, parameter);",
            "    };",
            "    var _origGetParam2 = WebGL2RenderingContext.prototype.getParameter;",
            "    WebGL2RenderingContext.prototype.getParameter = function(parameter) {",
            "        if (parameter === 37445) return '" + vendor + "';",
            "        if (parameter === 37446) return '" + renderer + "';",
            "        return _origGetParam2.call(this, parameter);",
            "    };",
        ]

    if config.patch_canvas_noise:
        parts += [
            "    var _origToDataURL = HTMLCanvasElement.prototype.toDataURL;",
            "    HTMLCanvasElement.prototype.toDataURL = function(type) {",
            "        var context = this.getContext('2d');",
            "        if (context) {",
            "            var imageData = context.getImageData(0, 0, this.width, this.height);",
            "            for (var i = 0; i < imageData.data.length; i += 100) {",
            "                imageData.data[i] ^= Math.floor(Math.random() * 2);",
            "            }",
            "            context.putImageData(imageData, 0, 0);",
            "        }",
            "        return _origToDataURL.apply(this, arguments);",
            "    };",
        ]

    if config.patch_permissions:
        parts += [
            "    var _origQuery = navigator.permissions.query.bind(navigator.permissions);",
            "    navigator.permissions.query = function(parameters) {",
            "        if (parameters.name === 'notifications') {",
            "            return Promise.resolve({ state: Notification.permission });",
            "        }",
            "        return _origQuery(parameters);",
            "    };",
        ]

    parts.append("})();")
    return "\n".join(parts)


def build_cdp_config(config: StealthConfig) -> dict:
    """Return dict of CDP settings to apply per tab at runtime."""
    return {
        "set_useragent_override": config.set_useragent_override,
        "extra_http_headers": config.extra_http_headers,
        "block_urls": config.block_urls,
        "disable_cache": config.disable_cache,
        "emulate_network": config.emulate_network,
        "network_latency": config.network_latency,
        "network_download": config.network_download,
        "network_upload": config.network_upload,
    }
