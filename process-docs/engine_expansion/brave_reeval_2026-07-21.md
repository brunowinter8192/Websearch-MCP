# Brave Search Re-Evaluation — Dev Probe (2026-07-21)

**Probe:** `dev/search_pipeline/26_brave_probe.py` (self-contained, no `src/` import)
**Report:** `dev/search_pipeline/md/brave_probe_20260721_215133.md`
**Gate tested:** real result rows from Brave's own index, WITHOUT triggering Brave's Proof-of-Work (PoW) CAPTCHA, at a per-query wall latency consistently ≤5s, run one query at a time the way the production `asyncio.gather` pool runs each engine — no architectural special-casing (no own-timeout/fallback scheme; that design was explicitly rejected going into this probe).

## Verdict: DROP

Condition failed: **PoW/CAPTCHA**, not latency. 10 queries run back-to-back: queries 1-4 returned 10 real results each with no CAPTCHA; queries 5-10 all hit a PoW block. Latency itself was fine throughout (10/10 ≤5s, min 1763ms / median 1840ms / max 3947ms) — moot given the PoW failure and its persistence (below).

## Two new findings from this re-eval

### 1. Patchright + real Chrome, headless — the previously-untested angle — closes without a candidate

The stealth-inventory resume note flagged "Patchright with real Chrome binary (`channel=\"chrome\"`), never correctly tested" as the fresh angle. Tested here: instant slider CAPTCHA (title `Captcha - Brave Search`, `Schieberegler ziehen`, link to `/help/pow-captcha`) on the very first query, headless. The same real-Chrome binary, same query, **headed** (`headless=False`) returned a clean results page, no CAPTCHA.

This is a **single-trial controlled observation** (one headless run vs. one headed run, same query, same binary) — plausible as "headless-ness is the dominant signal for this stack against Brave," but not repeated across multiple queries/sessions, so it should be read as a strong lead, not a confirmed mechanism. What does NOT depend on that mechanism being exactly right: headed is not viable in this codebase's production context (server pipeline, no display) regardless of why headless fails — so the decision to close this angle without a candidate holds either way.

### 2. Post-block state does not clear within 30s — but the underlying mechanism is not established

The committed probe (pydoll stealth stack) ran 10 queries with no inter-query delay and got 4 clean results before PoW triggered at query 5, staying blocked through query 10. A follow-up one-shot check (not committed — `/tmp`, per dev/ convention for a no-regression-value verification) waited 30s on the same already-blocked persistent browser profile (`~/.searxng-mcp/browser-session` — the same profile shared by every production engine via `new_tab()`) and issued one more query: still blocked (a "checking that you're not a bot" interstitial, not a clean results page).

**This is framed as one hypothesis, not a proven mechanism.** Two explanations are consistent with the same observation and were not distinguished here (out of scope — no PoW/rate-limit reverse-engineering was attempted, per task scope):
- a session/profile-scoped trust flag that persists once tripped, independent of elapsed time, or
- an IP-rate-based block with a cooldown window longer than the 30s tested.

**The DROP verdict and its practical risk do not depend on which explanation is correct.** Under either mechanism, a burst of Brave queries against the shared persistent profile risks poisoning that profile/IP reputation for a period extending beyond the burst itself — a materially worse failure mode than a clean per-query CAPTCHA-and-move-on, since the shared profile is used by every other production engine (`google`, `duckduckgo`, `mojeek`, `startpage`, etc.). This shared-profile/shared-IP poisoning risk is real under either the session-scoped or the IP-rate-based reading, which is why it is called out here rather than deferred pending root-cause.

## The drop is anti-bot-driven, not quality-driven

Before the PoW block, Brave surfaced genuine own-index results distinct from Google/Startpage/Mojeek — e.g. `testsieger.de`, `mediamarkt.de`, `imtest.de`, `faz.net` for `beste kaffeemaschine test` (a different top set than the equivalent Startpage/Google runs), plus the expected `realpython.com`/`docs.python.org` set for `python asyncio tutorial` and real Frankfurt local-business listings (`wmz-horn.de`, `kleinanzeigen.de`, `quoka.de`) for the local-biz queries. The coverage value that motivated re-testing Brave is real and on record — the DROP is entirely the PoW/anti-bot gate, not a data-quality finding. Should Brave's PoW posture change (e.g. via the official Search API becoming viable, or a stealth technique not covered here), the index-quality case for revisiting it still stands.
