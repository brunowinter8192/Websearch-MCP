# Headed vs headless for a general-purpose search/scrape tool — external evidence (2026-08-02)

Research pass triggered by the question whether driving a real, visible browser (optionally signed into a
Google account) would defeat what Google throws at us. No code changed in this session; the outcome is
two issues and this entry.

## Why measurement was rejected as the decision basis

The obvious move — probe all 9 browser engines headless vs headed and compare — was considered and
dropped. A single-IP, single-day comparison measures our own IP's wear on that day, not the mode. The
2026-07-21 Brave headed-lane probe in this area is the cautionary case: it read as "headed is worse"
(2/10 clean vs the headless run's 4/10) but its own entry records the comparison as confounded — the same
IP had already been probed against Brave three times that day before the headed run started. Any repeat of
that design would reproduce the same confound. External sources with a broad experience base are the
better evidence here, the same way the htmldate benchmark was preferred over a self-run accuracy test
earlier in this session.

## The two layers, and which one headed touches

Everything in the sources sorts into one of two detection layers, and conflating them is the main source of
bad conclusions:

- **Fingerprint layer** — what the browser environment looks like (rendering stack, navigator flags,
  canvas/WebGL/audio signals, header casing). Headed removes a whole class of these at the root.
- **IP / reputation layer** — how the address and its subnet have behaved historically. Headed does
  nothing here.

Evidence for the split, from `reddit-cli-posts`:
- A Playwright user on premium rotating residential proxies against Cloudflare: *"I'm using a headless
  browser but even setting headless=false shows cloudflare."* Mode changed nothing; the community reply
  attributes it to ML-scored IP reputation across the proxy provider's pool.
- On a hardening ladder stalling at step 2: *"the reason your ladder stalls at step 2 is probably IP
  reputation scoring, not just detection of automation … sites that run aggressive anti-bot don't just check
  if the IP is residential — they score it based on how many automated requests that subnet has seen
  historically."*
- Antidetect-browser overview: those tools change the device fingerprint and explicitly provide no IP;
  running them over a home connection gets profiles linked immediately.

## Evidence that headed wins on the fingerprint layer

- Patchright maintainer (`github_issues` patchright#113, recorded in this area's
  `hard_engine_headed_lane_research_2026-07-21.md`): *"It is not possible to be undetected headless without
  a custom chromium fork."* Patchright officially recommends headful (patchright#103).
- r/scrapingtheweb, 2026-07-02, a thread asking exactly this question ("Has anyone actually measured the
  difference between headless and headful lately?"). The substantive reply: on a Cloudflare-protected retail
  site over residential proxies, plain headless hit the "checking your browser" wall on ~half of requests;
  swapping proxies changed nothing; the same script switched to headful dropped blocks to almost none.
- r/webscraping, 2025-12-02: the CI/CD fix for Cloudflare/Turnstile detection is Xvfb + Chrome in headed
  mode inside the virtual display — *"the issue usually isn't your code, it's the lack of an X server.
  Anti-bot systems fingerprint the rendering stack and see you don't have a monitor."* (Xvfb is Linux-only
  and irrelevant on a Mac with a real display — headed simply renders to the screen.)

## The counter-argument, and why it does not transfer to this project

The same 2026-07-02 reply continues: after properly hardening the headless setup, the block rate fell back
close to headful — *"headful still edged it, but the gap went from half my requests dying to a few percent."*
Read alone, this suggests hardening substitutes for headed.

It does not transfer here, because **that hardening was per-domain**. One target, one detection system, tune
until it matches. This project has no such fixed target:

- the drilldown pipe runs 9 engines with 9 different detection systems sharing ONE Chrome profile and one
  set of JS patches — a patch tuned for one engine is an untested variable for the other eight;
- the scrape path hits constantly changing third-party domains, unknown in advance.

So the "properly hardened headless" state the reply describes is structurally unreachable for a
general-purpose tool. What remains available is the intersection: measures that help across targets, or at
minimum never hurt. Headed belongs to that class because it removes a signal class at the root rather than
masking it per target.

## State of the three surfaces as of this session

| Surface | File | Browser posture |
|---|---|---|
| 9 DOM search engines | `src/search/browser.py` | headless (`options.headless = not os.environ.get("WEBSEARCH_HEADED")`, unset); shared profile `~/.websearch/browser-session`; JS fingerprint patches present, one of them explicitly patching a headless-only CSS artifact |
| single-URL scrape | `src/scraper/scrape_url.py` | headless + `enable_stealth=True` + `UndetectedAdapter` |
| pipe scraper (capture flow) | `src/crawler/pipe_scraper.py` | `BrowserConfig(headless=True, verbose=False)` — nothing else |

The 5 HTTP engines (crossref, openalex, open_library, stack_exchange, marginalia) have no browser and are
outside this question entirely.

A headed switch already exists (`WEBSEARCH_HEADED`) but only turns headless off — it starts a normal
foreground window. Background launch without focus theft is a separate mechanism, proven working in
`dev/search_pipeline/27_brave_headed_lane_probe.py` (macOS `open -g -n` through a custom pydoll
`process_creator`, isolated profile, verified clean teardown), and lives only in that probe.

## Observation from this session's capture run

A capture run took **0/23 on crossref.org** — every URL empty at ~15s (the page-load ceiling), no HTTP
status recorded at all — while the same run took **78/78 on api.stackexchange.com**. A plain `curl` on one
of the failing crossref URLs returned HTTP 200, 79274 bytes, 7.2s, with the target content fully present.
The wall stands against the unhardened headless browser, not against the host or the scraper as such. The
run was rescued by fetching those 23 pages over plain HTTP instead — viable only because crossref.org
serves static HTML; a JS-rendered target behind the same wall would have had no such escape.

Related gap: the capture-and-index skill's coverage gate names *stealth* among the iteration levers a
worker should try after a systemic scrape failure, but `pipe_scraper.py` exposes no such lever — its CLI
flags only pace requests. The worker correctly stopped and reported rather than improvising, and asked
whether such a mode existed; it does not.

## Google specifically

Google's cookie wall is already handled — `google.py` injects a SOCS consent cookie per tab. What we hit is
the `/sorry/` path, which by every description in the sources sits on the IP/reputation layer. Headed is
therefore not expected to fix Google, and framing it as a general unblocker would overstate the evidence.

A signed-in Google account was raised and rejected: it does not address the cookie wall (already bypassed),
Google's terms forbid automated queries, and attaching automated traffic to a personal account moves the
failure mode from "IP briefly hot" to "account flagged" — in a profile shared by 8 other engines.
