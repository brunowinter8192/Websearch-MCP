# Brave Headed-Background Lane Probe (2026-07-21)

**Probe:** `dev/search_pipeline/27_brave_headed_lane_probe.py` (self-contained, no `src/` import)
**Report:** `dev/search_pipeline/md/brave_headed_lane_probe_20260721_223755.md`
**Gate tested:** real result rows, no PoW/CAPTCHA, per-query latency ≤5s, AND a usable run of 3-4+ consecutive clean queries (relaxed bar — need not be block-free forever), run one query at a time.

## Verdict: DROP — solid

2/10 queries clean (10 real results each, no CAPTCHA), then a persistent PoW block from query 3 through query 10. Longest consecutive clean run = 2, below the relaxed 3-4 bar. Latency was never the issue — 10/10 queries ≤5s (min 1742ms / median 1753ms / max 3420ms). This DROP is not in question: headed-background Chrome does not clear Brave's PoW gate reliably enough to serve as a working lane, on this IP, today.

## What is NOT established: why headed did worse than headless — confounded by same-day repeated probing

The prior milestone's headless pydoll-stealth run (`26_brave_probe.py`, same day) got 4/10 clean before blocking; this headed-background run got only 2/10. Read at face value this looks like "headed is worse than headless against Brave" — but that comparison is **confounded**: by the time this headed run executed, Brave had already been probed against this same IP **three times today** (the headless pydoll-stealth run, the Patchright-headless single-query check, the Patchright-headed single-query check from the prior milestone, plus this run's own earlier single manual headed test during development). An IP-level reputation/rate signal accumulating across all of today's probing is at least as plausible an explanation for "2 clean instead of 4" as any headed-vs-headless mechanism.

**State this as: the DATA (2 clean, then persistent block) is valid and reported as measured. The WHY (headed detection vs. accumulated same-IP reputation vs. request velocity) is open and was not distinguished — no repeat run on a fresh IP/day was performed (out of scope; avoiding a PoW reverse-engineering rabbit hole per task limits).** Do not read this probe as evidence that "headed is worse than headless for Brave" — it is equally consistent with "this IP was already worn down from three prior probes today."

## What IS proven and kept on record: the headed-background launch mechanism itself works

Independent of the Brave-specific verdict, this probe validates a reusable technique for any future hard-engine candidate whose block is genuinely headless-fingerprint-based (rather than IP/velocity-based, as Brave's may be):

- `pydoll.browser.managers.BrowserProcessManager` accepts a `process_creator` callback (`command -> subprocess.Popen`). `Chrome(options)` does not expose this in its constructor — `browser._browser_process_manager` must be swapped to a custom-`process_creator` instance AFTER construction, BEFORE `await browser.start()`.
- The custom creator discards the resolved `binary_location` (element 0 of the command list) and launches via macOS `open -g -n -a "Google Chrome" --args --remote-debugging-port=<port> --user-data-dir=<isolated dir> ...` — `-g` prevents focus-stealing (background), `-n` forces a new instance. A single hand-test before the full run confirmed this reaches Brave with a clean (non-CAPTCHA) title on the very first request.
- Teardown is a real CDP `Browser.close` via `browser.stop()` (confirmed working — it's a genuine command against the real Chrome instance) plus an unconditional `pkill -f user-data-dir=<isolated dir>` safety net, since `open -g` returns immediately and pydoll's own process-reaping logic never held a handle to actual Chrome. Verified clean after both the hand-test and the full 10-query run: `ps aux | grep <isolated profile>` returned zero processes both times — no orphaned Chrome left behind.

This is a proven, working technique with no current customer (Brave's DROP is not a mechanism failure) — not a dead end. It stays available for a future candidate engine where headless is confirmed to be the actual, isolated trigger (not entangled with same-day IP wear, as here).
