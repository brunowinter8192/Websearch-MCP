# Hand-maintained COOKIE_CONSENT_SELECTOR dropped for crawl4ai's own consent clicker (2026-08-22)

Removes `COOKIE_CONSENT_SELECTOR` (a ~19-entry hand-maintained CSS list) and its
`excluded_selector` kwarg from `src/scraper/scrape_url.py`. The second of the ad-hoc chromium lane's
two ungrounded config values (the first, `MIN_CONTENT_THRESHOLD`, removed the same day — see this
area's `2026-08-22_min_content_threshold_removed_on_log_evidence.md`). Continues the
content/consent-handling lineage of this area's `content_judgment_removal_2026-08-05.md`. Consent
handling now rests solely on `remove_consent_popups=True`, which `try_scrape` already passed.

## What it was, and why it was the wrong shape

`COOKIE_CONSENT_SELECTOR` went into crawl4ai's `excluded_selector` (a genuine CrawlerRunConfig
param, applied in `content_scraping_strategy.py` — it `cssselect`s the list against the captured
HTML and removes matching nodes before markdown generation). It only HID nodes. It was grown from
2026-03 session findings (CookieYes, OneTrust, Cookiebot, plus generic `gdpr`/`cookie-banner`
patterns) and was known-incomplete — a new or bespoke CMP overlay slips straight through. It is
exactly the kind of hand-maintained filter list this project's course rejects (domain/vendor-specific
lists are the hamster wheel: add a pattern for site A, site B regresses).

## GitHub landscape (research pass, not built on)

Searched GitHub for consent-removal solutions. The gold standard is `duckduckgo/autoconsent` (MPLv2,
pushed same day as this entry, crowd/DDG-maintained) — a rules library that DETECTS CMPs and CLICKS
opt-in/opt-out, used in DuckDuckGo's own browser apps. But it is a TypeScript/JS library integrated
via a content script injected into a live Playwright/Puppeteer page plus a background config hook — in
this project's Python/crawl4ai stack, where crawl4ai owns the page, that is a heavy integration whose
value duplicates what we already have (below). The filter-list alternatives (e.g.
`wanhose/cookie-dialog-monster`) are stale — 451 days without a push at the time of this entry, the
exact maintenance rot the switch is meant to escape. Conclusion: no external dependency is worth
taking on.

## Why the answer was already in-stack: crawl4ai's remove_consent_popups is a strict superset

`try_scrape` already passed `remove_consent_popups=True`, running crawl4ai's own vendor-maintained
`js_snippet/remove_consent_popups.js` on the LIVE page before HTML capture. Read that snippet
directly: 301 selectors across 5 phases (click "Accept All" market-share-ordered → CMP JS APIs →
remove CMP containers → remove CMP iframes → restore body scroll). It CLICKS the accept button
(properly dismissing the popup), stronger than the hide-only `excluded_selector`. Verified it covers
the exact CookieYes case the hand-list was added for (the 12K-char `cky-modal` motivating case, per
the old DOCS Gotcha): phase 1 clicks `.cky-btn-accept`/`[data-cky-tag="accept-button"]`, phase 3
removes `.cky-consent-container`/`.cky-overlay`, phase 5 clears `cky-modal-open` on body. The
hand-list was a weaker, redundant duplicate of a vendor-maintained feature already active in our own
stack — so the grounded move is to delete the list, not to replace it with another (external) one.

## Change + verification

Removed the constant, the `excluded_selector` kwarg from `_build_run_config`, and the
`excluded_selector_hash` field from `extract_config_stamp` (a stamp-shape change — `config_hash`
won't group across the boundary, same accepted kind as the same-day `min_content_threshold` and the
2026-08-05 `max_content_length` drops). `remove_consent_popups=True` untouched. Repo-wide grep
confirmed the constant lived only in `scrape_url.py` + its own test file — no shared import, no other
lane affected. Live `cli.py scrape_url` run on guenstiger.de (this project's own documented
Cloudflare/consent test page): HTTP 200, 38538 filtered / 73615 raw bytes of real product content,
the full output grepped for cookie/consent text with zero matches — `remove_consent_popups=True`
alone handles the banner with no leftover wall text. Full suite 225 passed / 0 failed.

## Historical evidence that already pointed here

The DOCS Gotcha history recorded (from when both layers coexisted) that on azubiyo.de,
`excluded_selector` ALONE let ~3400 chars of German CMP banner text through into `raw_markdown` while
`remove_consent_popups=True` removed it cleanly (`bytes_raw_markdown` 41583→37988) — i.e.
`remove_consent_popups` was already doing the real work before this removal, and `excluded_selector`
was not even catching what it was nominally responsible for. The removal formalizes what the
operational evidence already showed.
