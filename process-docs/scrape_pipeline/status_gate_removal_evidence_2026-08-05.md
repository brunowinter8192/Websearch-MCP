# The evidence that removed the ad-hoc path's content judgment (2026-08-05)

Orchestrator-side record of the measurements that produced the `scrape_url` contract inversion. The
change itself is recorded in `content_judgment_removal_2026-08-05.md` (same area, worker entry); this
records the runs that made the case, including the ones that changed what the change was supposed to be.

## Starting point: two issues, both about the ad-hoc path failing

Two open issues described ad-hoc scrape failures — price-comparison portals returning HTTP 403
(idealo, guenstiger, trustpilot) and client-side-rendered API reference pages returning `Loading...`
placeholders counted as success. Both were recorded under the config in force at the time.

First check: had they ever been re-run under the current config? The scrape log answered no. Of 171
records, 163 carried no `config_hash` at all (predating the config stamp) and the newest five ran under
`371d434adf`. Every problem record predated the hardening. So the first action was simply to re-run the
recorded URLs — not a domain sweep for calibration, but checking whether documented failures still
reproduce.

## Re-run under the current config, and what it showed

| URL | before | 2026-08-05 |
|---|---|---|
| idealo product page | `http_error` 403 | HTTP 200, 405 bytes, "Sorry! Something has gone wrong" |
| idealo category page | `ok`, 138 bytes | HTTP 200, 401 bytes, same Sorry page |
| guenstiger | `http_error` 403 | HTTP 403, Cloudflare interstitial |
| trustpilot | `http_error` 403 | HTTP 403, 1.1 MB HTML |
| platform.claude.com | `ok` + `Loading...` placeholders | `budget_exhausted` at 41.8s |
| docs.anthropic.com | `http_error` 301 | HTTP 301, domain moved to platform.claude.com |

The idealo case had moved from an honest rejection to a silent false success: HTTP 200, a courtesy page,
`is_garbage_content` returning None. Getting through the wall made the outcome *worse* by the project's
own ordering of failure kinds (correct content > honest failure > silently-delivered wrong content).

## The finding that inverted the framing: 403 with real content

Probing the two 403s directly for anti-bot markers (`challenge-platform`, `__cf_chl`, `turnstile`,
`cf-error-code`, `_pxAppId`, `captcha-delivery`) separated them cleanly:

- **trustpilot**: zero markers, `<title>Bewertungen zu ENTEGA Plus GmbH …</title>`, 1.1 MB. The real
  review page, served under a 403 status. Running it through the full ad-hoc config with the status gate
  bypassed: 42707 bytes raw markdown, 27721 after the filter, `is_garbage_content` → None. The scraper
  had been discarding a complete page and returning "HTTP error page (404/403)" — a false statement.
- **guenstiger**: every marker present, `<title>Just a moment...</title>`. A genuine Cloudflare challenge.

So the status gate was not protecting against anything. A real 403 yields no content, which the content
check catches anyway; a 403 with 40KB of article text is a server using status codes unusually.

## guenstiger: the challenge resolves itself, we were capturing too early

Varying only `delay_before_return_html` on guenstiger:

| delay | wall | status | html bytes | title |
|---|---|---|---|---|
| 2.0s | 2.8s | 403 | 171862 | `Just a moment...` |
| 6.0s | 6.9s | 403 | 244126 | `AEG VX9-2.ÖKO Preisvergleich \| guenstiger.de` |
| 12.0s | 12.8s | 403 | 244170 | (same) |
| 20.0s | 20.9s | 403 | 244172 | (same) |

Knee below 6s, flat above it — the same saturation shape crawl4ai issue #1665 shows and from which the
current 2.0s was derived. Two things stay broken independent of timing: the status remains 403 even once
the real page is present (crawl4ai keeps the first response's status), and `challenge-platform` remains
in the HTML after the challenge resolved, so marker-matching cannot distinguish solved from unsolved.

Cost side, measured on an ordinary page (rfc-editor.org, static): 2.0s and 6.0s returned byte-identical
markdown (804593 both), wall time 5.8s → 10.0s. The raise buys nothing where nothing stalls. Left
unchanged: 6.0 would be a number derived from one domain, which this project's calibration method
rejects, and the render wait is a counted summand of the 39.4s budget. Deferred as its own question.

## Consequence for the contract

Three of the four cases were our own evaluation being wrong, not a reachability limit:
trustpilot (status gate discarding a complete page), guenstiger (same gate, plus capturing too early),
idealo (content classifier passing a courtesy page as clean). Only idealo's wall is real.

That is what moved the decision from "fix the classifier" to "remove the judgment": the classifier was
wrong in both directions on the same four URLs, and the caller — an agent with the page text in front of
it and a user to report to — is better placed to judge than a keyword list. crawl4ai's own diagnosis
already carried the useful sentence ("Blocked by anti-bot protection: Cloudflare JS challenge") and went
only to the log, invisible to the caller.

One caveat that had to survive into the implementation: that diagnosis is an observation, not a verdict.
On guenstiger at 6.0s the full product page comes back AND crawl4ai still reports the Cloudflare
challenge. Presented as a status claim it would just swap one bad automatic judgement for another.

## Also found, not acted on

- **docs.anthropic.com returns 301** to platform.claude.com and the scraper does not follow it, logging
  `http_error` while `crawl4ai_success` is True. A separate defect.
- **htmldate returned today's date** as `published_date` for the trustpilot review page — no meaningful
  publication date exists for that page class. Pre-existing, consistent with the known weakness recorded
  in `src/scraper/DOCS.md`'s Gotchas.
