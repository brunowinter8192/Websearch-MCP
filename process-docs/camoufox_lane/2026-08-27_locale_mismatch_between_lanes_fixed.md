# The two lanes requested different languages from the same URL — fixed by resolving the system locale at runtime (2026-08-27)

Continues the `camoufox_lane` area. Unrelated to the focus-steal work above — this is the lane's
language/fingerprint configuration, not its window-activation behavior.

## The evidence

`olat.server.uni-frankfurt.de`, scraped 12 seconds apart through the same CLI: chromium returned
`# Willkommen in OLAT`, camoufox returned `# Welcome to OLAT`. Both lanes hit the same URL, same
machine, same session — the only difference was the acquisition engine.

## Root cause

`_build_camoufox_kwargs` passed `os="macos"` but no `locale`. Per the Camoufox vendor docs
(`locale:language`/`locale:region`/`locale:all` under fingerprint/geolocation; `navigator.language`
and `Accept-Language` follow them), an unset `locale` falls back to `en-US` regardless of the host
OS. The chromium lane sets nothing locale-related at all and therefore inherits whatever the real
OS locale is — on this machine, German — so the two lanes diverged by construction, not by chance.

## Why the fix reads `AppleLocale`, not `LANG` or Python's own `locale` module

The first instinct — resolve the locale via Python's stdlib `locale.getlocale()` — was checked
against the real value and rejected. On this machine: `LANG=en_US.UTF-8` (the shell/Python view,
`locale.getlocale()` → `('en_US', 'UTF-8')`) vs. `defaults read -g AppleLocale` → `de_DE` (the real
macOS System Settings language). These disagree. Chromium's rendered German heading proves it
follows the real OS-level locale, not the shell's `LANG` env var — a headed browser reads the
user's actual System Settings language via CoreFoundation, independent of whatever `LANG` a
terminal session happens to export. Using `locale.getlocale()` alone would have reproduced the
exact bug this fix closes, just with a different constant baked in. `defaults read -g AppleLocale`
is therefore the primary source; Python's `locale` module is kept only as an off-macOS/
command-failure fallback, since the project's browser-launch code is already macOS-only throughout
(`_ensure_no_focus_steal`, the `sys.platform == "darwin"` gates).

## The fix

`src/scraper/camoufox_scrape.py`: new `_resolve_system_locale()`, called fresh on every scrape
inside `_build_camoufox_kwargs` (no caching — deliberately resolved at runtime, not hardcoded, so a
future change to the host's own locale is picked up without a code change). Converts the
`defaults`-style `de_DE` (underscore) to Camoufox's expected BCP-47 `de-DE` (hyphen), verified
against the installed `camoufox.locales.verify_locale`/`handle_locale` (backed by the
`language_tags` package) which parses it into `Locale(language='de', region='DE', script='Latn')`
without error. Because `_extract_camoufox_config_stamp` already spreads the input kwargs
(`{**kwargs, ...}`), adding `"locale"` to the kwargs dict was sufficient to make it appear in the
logged config stamp with no separate wiring — `config.locale` in `scrape_log.jsonl`.

## Verification

Real CLI runs (`venv/bin/python cli.py`, this worktree, never the `websearch` PATH wrapper) against
`https://olat.server.uni-frankfurt.de`, after the fix:

- chromium: `# Willkommen in OLAT` (unchanged from before the fix).
- camoufox: `# Willkommen in OLAT` (was `# Welcome to OLAT` before).
- The real log record on disk (`src/logs/scrape_log.jsonl`, this worktree): camoufox's
  `config.locale = "de-DE"`; chromium's `config` has no `locale` key at all, confirming the
  chromium lane was untouched.

## Chromium was deliberately left alone

The task's own instruction: don't change chromium's behavior, and if it needs an explicit setting
to be provably equal, report that instead of doing it. The live run above already shows both lanes
agreeing (`Willkommen in OLAT`, both lanes) with chromium setting nothing — there is no live
evidence chromium's OS-inherited locale ever diverges from Camoufox's new explicit one, so no
explicit chromium-side setting was added. If a future case surfaces where they disagree again, that
is new evidence and a new decision, not a revival of this one.
