# Stealth Layer 1: Browser-Fingerprint

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**ON:**
- `--disable-blink-features=AutomationControlled` — entfernt `navigator.webdriver=true` Flag
- `screen_dimensions` patch — überschreibt `screen.width/height/availWidth/availHeight/colorDepth/pixelDepth` (1920×1080, colorDepth=30)
- `device_pixel_ratio` patch — setzt `window.devicePixelRatio = 2`
- `outer_dimensions` patch — setzt `window.outerWidth = innerWidth`, `window.outerHeight = innerHeight + 85`
- `css_active_text` patch — `getComputedStyle` Proxy maskiert headless-typischen CSS-Color-Wert (rgb(255,0,0) → rgb(0,102,204))
- User-Agent: Chrome 147 via `--user-agent=` CLI-Argument
- `webrtc_leak_protection: true` (pydoll-Attribut)
- Alle 4 JS-Patches via `PageCommands.add_script_to_evaluate_on_new_document` — injiziert sowohl beim Browserstart (initial tab) als auch per neuem Tab in `run_query()`

**OFF:**
- `patch_webgl` — WebGL vendor/renderer Override nicht konfiguriert
- `patch_canvas_noise` — Canvas-Fingerprint-Randomisierung nicht konfiguriert
- `patch_permissions` — Permissions.query Override nicht konfiguriert

**NICHT IMPLEMENTIERT:**
- chrome.runtime Object Masking (kein `window.chrome.runtime` Spoof)
- navigator.plugins Spoofing (leere Plugin-Liste in headless bleibt sichtbar)
- navigator.userAgentData brands Override (`Chromium` vs `Google Chrome`)

### Detection Surface

Was Layer 1 prüft:

| Signal | Was erkannt wird | Unser Control |
|--------|-----------------|---------------|
| `navigator.webdriver` | `true` in headless | ✅ AutomationControlled entfernt es |
| Screen-Dimensionen | `screen.width/height = 0` in headless | ✅ Patch auf 1920×1080 |
| devicePixelRatio | 1.0 in headless (statt 2.0 auf Retina) | ✅ Patch auf 2 |
| outerWidth/outerHeight | Fehlt Titlebar-Offset | ✅ Patch +85px outer height |
| CSS active text color | rgb(255,0,0) headless-Artefakt | ✅ Proxy-Patch |
| WebGL vendor/renderer | `Google SwiftShader` = starkes headless-Signal | ❌ kein Patch |
| Canvas Hash | Deterministisch in headless | ❌ kein Rauschen |
| navigator.plugins | Leer in headless | ❌ kein Spoof |
| chrome.runtime | Fehlt in headless | ❌ kein Masking |
| Permissions API | `.query({name:'notifications'})` returns `denied` sofort | ❌ kein Override |
| Error.stack CDP trap | pydoll: `CDP Runtime.enable` detektierbar via Error.stack Getter | ❌ nicht gefixt |
| navigator.userAgentData | `brands: ["Chromium"]` statt `["Google Chrome"]` | ❌ kein Override |

## Evidenz

### Brave Stealth-Patch-Matrix (2026-04-09)

| Stack / Patch | X/30 | Erste Failure | Delta vs Baseline |
|---------------|------|---------------|-------------------|
| pydoll Baseline (settle=0.0, proxy=None) | 3/30 | Query 3 | — |
| pydoll + patch_webgl=True | 10/30 | Query 11 | +7 |
| pydoll + patch_canvas_noise=True | 6/30 | Query 7 | +3 |
| pydoll + patch_permissions=True | 0/30 | Query 1 | -3 (kontraproduktiv) |
| pydoll + chrome.runtime + navigator.plugins | 0/30 | Query 1 | -3 (kontraproduktiv) |
| pydoll + alle Patches kombiniert | 0/30 | Query 1 | -3 (schlechte Patches dominieren) |
| Patchright (Chromium Binary) | 0/30 | Query 1 | -3 (Slider CAPTCHA statt PoW) |
| Camoufox (Firefox, headless) | 7/30 | Query 8 | +4 |

Erkenntnis: WebGL-Fingerprint ist das stärkste Einzelsignal. Permissions- und plugin-Patches sind bei Brave kontraproduktiv — Brave detektiert JS-Overrides dieser APIs direkt.

### Brave Detection-Signale (2026-04-09, Reverse-Engineering)

- CDP `Runtime.enable` + `Error.stack` Getter Trap — pydoll betroffen, Patchright fixt es
- `navigator.userAgentData.brands`: `"Chromium"` statt `"Google Chrome"` (Patchright mit Chromium-Binary betroffen)
- `__playwright_evaluation_script__` in `Function.prototype.toString`
- `navigator.webdriver = true`
- WebGL SwiftShader Renderer (starkes Signal — WebGL-Patch bringt +7)
- `navigator.brave.isBrave` fehlt (Soft-Signal)

### puppeteer-extra-plugin-stealth Vergleich (2026-04-07)

Fehlende Patches vs. puppeteer-extra:
- chrome.runtime Masking — nachträglich implementiert, kontraproduktiv bei Brave (0/30)
- navigator.plugins Spoofing — nachträglich implementiert, kontraproduktiv bei Brave (0/30)

Erkenntnis: Patches die bei Puppeteer Brave schlagen, sind bei pydoll ineffektiv oder schaden — vermutlich weil pydoll zusätzliche CDP-Leak-Signale hat.

## Recommendation (SOLL)

Pending — wird durch Stress-Test-Iterationen bestimmt. Aktuelle Baseline erreicht 30/30 (Google, Run 1, kein Load). SOLL wird nach erstem Break verfeinert.

Kandidaten für nächste Iteration (nach Stress-Break):
- WebGL-Patch (bringt +7 bei Brave — zu testen ob bei Google Effekt neutral oder positiv)
- Canvas-Noise (bringt +3 bei Brave — gleich testen)
- **NICHT** Permissions/plugins/chrome.runtime (kontraproduktiv bei Brave, unklar bei Google)

## Offene Fragen

- Brave: Werden JS-Overrides von Permissions/plugins direkt über CDP detektiert oder über Behavioral-Abweichung?
- Brave: Patchright mit echtem Chrome Binary (nicht Chromium) — wurde nie korrekt getestet (`patchright install chrome` + `channel="chrome"`)
- Google: Verhält sich WebGL-Patch neutral oder positiv bei 30/30-Runs? (Brave-Evidenz zeigt +7, Google könnte anders reagieren)
- navigator.userAgentData Override: Pydoll-Fähigkeit unklar — CDP `Emulation.setUserAgentOverride` mit `userAgentMetadata` wäre der Weg
