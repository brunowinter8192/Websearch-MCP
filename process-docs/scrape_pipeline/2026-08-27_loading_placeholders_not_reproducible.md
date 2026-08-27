# Loading-placeholder page class: not reproducible with the current setup (2026-08-27)

Continues the `scrape_pipeline` area. The 2026-08-02 entry recorded 13 pages of one domain
(`platform.claude.com/docs/en/api/messages/*`, `api/models/*`) scraping to nav chrome plus 51
occurrences of the literal string `Loading` while the funnel counted them `ok`. This entry records
a reproduction attempt against the same URLs with the setup as of 2026-08-27, and its negative
result, which retired the line of work.

## Reproduction attempt, both lanes, same URLs

Two of the originally affected URLs (`api/messages/create`, `api/models/list`) were scraped live:

| Lane | Config at test time | `Loading` count | Raw markdown | Body present |
|---|---|---|---|---|
| ad-hoc chromium (`cli.py scrape_url_chromium`) | `delay_before_return_html=5.0` | 0 / 0 | 75,138 B / 27,270 B | full parameter tables, curl examples |
| pipe (`scrape_urls_workflow`, chromium engine) | `DELAY_BEFORE_RETURN_HTML=0.5` | 0 / 0 | 75,104 B / 27,232 B | full parameter tables, curl examples |

Both lanes returned HTTP 200 with the complete rendered body, including the exact elements the
2026-08-02 capture never saw (h1, parameter tables, request/response examples).

## Reading: the page template changed, not (only) our waits

The ad-hoc lane's render wait was raised to 5.0s on 2026-08-06 (after the original observation),
which alone could have explained a clean ad-hoc result. The pipe lane, however, still captures
after only 0.5s and produced byte-near-identical full markdown (75,104 vs 75,138 B on the same
page). A client-side-hydrating template of the 2026-08-02 kind cannot deliver its full body within
0.5s and match a 5.0s capture — so the better-supported reading is that the site now serves the
body server-rendered, and the failing template no longer exists in the form that produced the
observation. That is a property of the target site, not of this project's configuration.

## What this retires, and what it does not

- Retired: the mitigation work for this page class (post-scrape content assertion, escalation
  retry with a longer bounded wait). Without a live reproduction there is nothing to calibrate
  against, and building detection against a synthetic reconstruction of a vanished template would
  be tuning against a guess.
- NOT retired, recorded as a standing caveat: the structural gap itself is unchanged. A page that
  ships placeholders with HTTP 200 and a plausible byte count would still be counted `ok` by both
  lanes today, and the failure would again surface only downstream (the 2026-08-02 run's only
  signal was the cleaner's `no h1` rejection). If the signature re-appears on any domain, the
  2026-08-02 entry's mitigation 3 (a domain-agnostic content assertion at the scrape stage, where
  escalation is still possible) remains the sanctioned direction — `wait_for`-style event waits
  stay inadmissible per the 2026-08-04 config rules (R3).

## Verification boundary

Live CLI runs on 2 of the 13 originally affected URLs, one run each per lane, 2026-08-27. Not
re-tested: the remaining 11 URLs (same template, same domain — the two chosen cover both affected
sections), and any other domain carrying a comparable hydration template.
