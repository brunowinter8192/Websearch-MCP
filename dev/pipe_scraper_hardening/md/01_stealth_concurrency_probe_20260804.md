# Stealth-at-concurrency-8 probe — 20260804

Dataset: `dev/explore_pipeline/06_discovered_urls.txt` (316 URLs). Config held constant across both runs: `DOWNLOAD_DELAY=1.0`, `CONCURRENCY_PER_DOMAIN=8`, `page_timeout=15000`, `delay_before_return_html=0.5`. Order: baseline run first, then stealth, gap = 300s between runs.

## Outcome breakdown

| variant | ok | waf_429 | http_error | empty | error | wall_s |
|---|---|---|---|---|---|---|
| baseline | 316 | 0 | 0 | 0 | 0 | 317 |
| stealth | 316 | 0 | 0 | 0 | 0 | 317 |

## Crash / exception signatures

Baseline:
```
(none)
```

Stealth:
```
(none)
```

## Byte-count comparison (stealth vs baseline, per URL)

- URLs compared: 316
- Identical byte count: 280
- Changed byte count: 36
- Mean delta (stealth - baseline): 72.0 bytes
- Max |delta|: 2987 bytes at `https://docs.github.com/de/rest/using-the-rest-api/issue-event-types`

Root cause of the largest delta (line-diffed baseline vs stealth `.md` for that URL): 134 internal anchor
links in the stealth run carry a `?apiVersion=2026-03-10` query-string suffix that baseline's identical
links lack (`grep -c apiVersion=2026-03-10`: stealth=134, baseline=0). This is docs.github.com's own
client-side API-version-selector JS stamping outgoing links — a content difference, not a fetch failure.
33/36 changed URLs grew, 3 shrank (`models/catalog`, `models/embeddings`, `models/inference`, all -120 bytes).

## Verdict

**Measured — holds:** `enable_stealth=True` survives `CONCURRENCY_PER_DOMAIN=8` on this 316-URL set.
316/316 ok in both runs, 0 crashes, 0 exceptions of any kind in either variant's crash log. No
"Target page/context/browser has been closed" or comparable browser-level failure surfaced. Wall clock
identical (317s both runs).

**What was actually measured, not isolated:** crawl4ai wires `enable_stealth` to two things at once —
the `playwright_stealth` JS injection (`StealthAdapter`, per-page `add_init_script`) AND, via
`browser_manager.py`'s `if not config.enable_stealth: flags += [--disable-gpu, ...]`, WebGL availability
(disabled in baseline, left on in stealth). This probe measured that combined package surviving
concurrency 8 — it does NOT isolate whether the JS injection alone is concurrency-safe independent of the
WebGL/GPU-flag difference riding along with it. A pass here is a pass for the package crawl4ai ships,
not evidence about the JS mechanism in isolation.

**Byte-count finding — inferred, not causally proven:** 36/316 URLs (11%) differ in byte count between
runs, traced to session-dependent link query-string stamping by docs.github.com's own client JS, not to
scrape failures or missing content. Cannot attribute this specifically to stealth's fingerprint (vs WebGL
availability vs ordinary session-state variance between two independently-launched browser instances) —
flagging as inference. This is the kind of effect a source-level read of crawl4ai would never surface:
stealth mode measurably changes captured CONTENT on ~11% of pages here, not just fetch success/failure.

**Not measured:** whether this result holds on non-github domains/WAFs, over longer sustained runs, or
under interleaved/repeated ordering; whether the byte-count effect is driven by WebGL alone vs JS
injection alone (would need a third variant with the two decoupled).

**Run-order confound:** baseline ran first, stealth second, 300s gap between them (raised from an initial
60s plan specifically because this project's own WAF characterization — process-docs/pipe_scraper/ —
recorded budget recovery on the order of minutes, and an 8s gap alone had produced a ban; 300s was chosen
to make baseline-afterglow an implausible explanation for any stealth-run degradation). Both runs still
returned 316/316 ok, so no degradation to explain — but only one ordering was tested, so a
directional-bias effect (site got more used to this traffic pattern, cache warmed, etc.) cannot be
ruled out from this data alone.