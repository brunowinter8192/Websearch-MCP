# The Akamai boundary, a Camoufox probe, and a product ID that moved (2026-08-05)

Orchestrator-side record: external research plus probes run in the chat, no worker counterpart. Follows
the re-run recorded in `status_gate_removal_evidence_2026-08-05.md` (same area), which left exactly one
of four problem URLs as a genuine reachability wall: idealo.

## Identifying the wall: Akamai, not Cloudflare

Plain `curl` with a Chrome UA against the idealo product URL:

```
HTTP/2 403
server: AkamaiGHost
content-length: 3888
```

Body: the same "Sorry! Something has gone wrong … reference ID …" page the browser scrape receives — but
under 403 via curl and under 200 via the browser. Akamai Bot Manager, and the reference-ID page is its
standard rejection.

Notable by absence: no `_abck`, `bm_sz` or `ak_bmsc` cookies in the response. Those are Bot Manager's
sensor cookies — we were being rejected before reaching the sensor stage at all.

## External research: r/webscraping, 2025-05 through 2026-01

Subreddit discovery on "akamai bot detection" / "bot mitigation bypass" returned only anti-spam
communities (`StopBots`, `BanTheBots`) — the wrong side of the topic. Used the subreddits that had
already produced usable material earlier in the session (`webscraping` 100k members, `scrapingtheweb`,
`WebScrapingInsider`) instead of reformulating further.

Five threads, consistent across eight months. Reported as NOT sufficient: Puppeteer headless and headed,
undetected_chromedriver, playwright-stealth, residential proxies with sticky sessions, header
replication, artificial delays. One user reports under 5% success with Playwright; another that three
separate proxy vendors made no difference.

The mechanism described consistently, and it matches the curl finding exactly: the first page load sets
tier-1 cookies (`ak_bmsc`, `bm_sv`), a JS sensor then posts fingerprint and behavioural telemetry, and
only after validation does `_abck` flip from `~0~` (unvalidated) to `~-1~` (validated). Without it,
protected endpoints stay closed.

What reportedly does work is never a single setting: Camoufox with humanize to harvest a valid `_abck`,
then plain HTTP requests carrying that cookie — or patched Chrome with modified TLS parameters plus
residential IPs on stable sessions. One commenter names curl_cffi with `impersonate` as covering "90% of
anti-bot protections, except interactive challenges" — Akamai's sensor is exactly that exception.

## The Camoufox probe

Camoufox is an open-source Firefox fork with fingerprint spoofing at build level (what patchright is for
Chromium); `humanize` generates real mouse movement. Installed as a dev probe only — deliberately NOT
added to `requirements.txt`. Note on the earlier framing: the paid part in those Reddit reports is the
proxy, not Camoufox, and it was raised because THEIR IP reputation was the problem. This project runs
from a normal residential IP. Its own public-proxy pool (`src/news/engine/proxy_pool/`) would be a
downgrade here, not a help — public lists have the worst reputation there is.

Result, headless, humanize on, geoip on, NO proxy: HTTP 200, 894774 bytes, no Sorry page, 105 `€` signs,
~15s wall. Akamai cookies `ak_bmsc` and `bm_mi` set; `_abck` never appeared at all — the sensor
validation stage was never triggered, i.e. Camoufox looked unremarkable enough from the start.

The wall is passable without a proxy and without paid infrastructure. Whether that becomes production is
a separate decision — a second browser engine alongside crawl4ai contradicts this project's standing
"one library, exhausted" rule (`process-docs/scrape_toolbox/`).

## The product ID had moved — and that was NOT a scraper defect

The Camoufox run returned a complete, real product page — for a women's outdoor jacket, not the FritzBox
7510 that had been requested. Requested `203078159_-fritz-box-7510-avm.html`, landed on
`203078159_-woman-hybrid-jacket-fix-hood-33z6026-cmp-campagnolo.html`. Same numeric ID, different slug.

Counter-probe: requesting the same ID with a deliberately invented slug
(`203078159_-voellig-erfundener-quatsch-slug.html`) lands on the identical jacket page. idealo evaluates
only the numeric ID and rewrites the slug; the text part of the URL is decorative. Reproduced in a real
browser by the user independently.

So the ID carried the router when it was logged on 2026-08-01 and carries a jacket now. Recycled or
replaced cannot be told apart from outside.

This matters beyond idealo: an open issue records the same shape on geizhals (router URL requested,
e-guitar page delivered, `outcome=ok`) and reads it as a scraper defect deserving its own garbage
category. Hypothesis, not verified on geizhals: same ID reassignment, in which case a garbage category
would be the wrong answer to a stale URL.

Searching the current engine set for the same product returns ID `201756627`, which resolves correctly to
the FritzBox — and brave alone offers three different idealo IDs for that one device. The portals carry
the same product under multiple entries, which makes ID churn the more plausible reading.

What does stay a real gap: the scraper logs only the REQUESTED url, never the one actually reached. On a
redirect to different content that difference is the only available signal, and it is discarded.

## Reading

For a domain behind Akamai Bot Manager, no configuration value within crawl4ai closes the gap — the
research is unanimous across eight months, and the tier-2 mechanism explains why. Camoufox does close it,
measured, at the cost of a second browser engine. Under the contract this session shipped, the agent at
least SEES the Sorry page and its facts instead of a silent success, and can tell the user which URL did
not come through.
