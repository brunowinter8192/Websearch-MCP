# Startpage Re-Evaluation — Dev Probe (2026-07-21)

**Probe:** `dev/search_pipeline/25_startpage_probe.py` (self-contained, no `src/` import)
**Report:** `dev/search_pipeline/md/startpage_probe_20260721_200301.md`
**Motivation:** Startpage is a Google-index frontend (fetches Google results server-side and re-serves them) — a candidate path to the Google index when direct-Google is CAPTCHA-blocked for the current IP. It was tried previously and dropped at "0/30 results, root cause unclear."

## Historical 0/30 — hypothesis, not a re-verified fact

The engine code from that earlier attempt no longer exists in the tree, so its exact request shape (direct GET vs. form-driven, headers, session handling) cannot be inspected or re-run. Two candidate explanations for the historical 0/30 were on the table going in:

1. **Hot-IP / anti-bot block at the time** (the standing explanation carried into this task).
2. **Naive direct-GET hitting a token-gated degraded shell** (the mechanism this probe empirically found — see below).

This probe **confirms mechanism (2) exists today** — a direct GET is silently empty regardless of IP reputation — but it does **not** confirm that (2), rather than (1), was the actual cause back then. Both method (browser flow) and IP/time have changed since the original attempt, so the hot-IP explanation can neither be confirmed nor ruled out retroactively. Treat "historical 0/30 = naive direct-GET" as a plausible hypothesis suggested by today's data, not a proven root cause.

## What IS proven: scrapeability as of 2026-07-21

Live run, 10 queries (mainstream DE/EN, local-business DE — the motivating use case, docs-style EN/DE), single browser session, current IP: **10/10 OK, 0 blocked, 0 captcha markers, 0 errors.** Avg latency 3111ms (first half) vs. 3300ms (second half) — no degradation trend within the run. Sample titles/URLs for local-business queries (`gebrauchte waschmaschine frankfurt`, `hausgeräte händler frankfurt`, `gebrauchtwagen ankauf frankfurt`) resolved to real local listings (`kleinanzeigen.de`, `wmz-horn.de`, `hgs-horn.de`, `auto-ankauf-frankfurt.de`) — Google-index quality, not degraded/generic content.

## Measurement limits — explicitly out of scope for this probe

- **10 queries over ~35s** — no burst/high-volume test, no sustained-duration test. Whether Startpage rate-limits or blocks under higher query volume or over hours/days is unmeasured.
- **Single browser session, single IP, single point in time.** No repeat runs across different times of day or after a cooldown.
- **No adversarial CAPTCHA trigger attempted** — per task scope, the probe observed natural behavior only; it did not try to force a block via burst/rate abuse to see what Startpage's actual block page looks like.
- Conclusion is bounded to: "scrapeable today, at this volume, from this IP" — not "safe at production volume" or "immune to blocking."

## Mechanism findings (empirical, current DOM as of 2026-07-21)

- Direct GET `https://www.startpage.com/sp/search?query=<q>` (no prior homepage visit): redirects internally to `/do/search?...&sc=<token>`, returns a degraded shell (header/nav + privacy-guarantee dropdown only) — zero `div.result` nodes, zero external links, no captcha/block text anywhere. The `sc` token in that redirect does not correspond to a valid session — the request is missing the token minted on the homepage's search form.
- Working path: load `https://www.startpage.com/` → set `#q` via the native `HTMLInputElement.value` setter + `input` event (React controlled input — plain `.value =` assignment does not update React's internal state) → real `.click()` on `button.search-btn`. `form.submit()` was tried first and does NOT work — it bypasses the React submit handler entirely and just reloads the homepage with a fresh `sc` param, no search executed.
- Result DOM (current build): `div.result` container (10/page), title `a.result-title h2.wgl-title` (href lives on `a.result-title`), snippet `p.description`. Emotion-generated hash classes (`css-XXXXX`) coexist with these semantic classes and were treated as unstable/ignored for selector purposes.
- A nonsense/gibberish query still returned 10 `div.result` entries (Google's own broad-match fallback behavior) rather than a clean "0 results" — a literal zero-result page was not observed in this probe; distinguishing genuine-zero from block-shell relies on the block-marker/URL-path heuristic implemented in `_diagnose_empty`, not on having seen a real zero-result case.
