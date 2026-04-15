"""Builder functions that convert StealthConfig into runtime artifacts."""

# INFRASTRUCTURE
from stealth_config import StealthConfig


# Convert StealthConfig into list of Chrome CLI arguments
def build_chrome_args(config: StealthConfig) -> list[str]:
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


# Generate JS fingerprint patch script from config
def build_js_patches(config: StealthConfig) -> str:
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


# Return dict of CDP settings to apply per tab at runtime
def build_cdp_config(config: StealthConfig) -> dict:
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
