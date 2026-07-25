# 38 — Session retrospective: orchestration/design errors (2026-06-15)

Honest record of Opus-side errors this session, on the user's explicit request — so they are seen and
do not recur. Not catastrophic (nothing was deleted, everything is recoverable), but they cost a day's
apparent progress and reintroduced problems that did not exist before.

## The throughline

Two recurring failure modes, both mine:
1. **Dropping load-bearing behavior when "simplifying" / rewriting.** Reframing a small change as a
   clean-slate rebuild, and silently discarding parts of the working design that were carrying weight.
2. **Validating against my own framing instead of the baseline / the goal.** Reviewing a rewrite for
   internal consistency with the spec I wrote, not for "does it do at least what it replaced?"

## Error 1 — over-scoped the tail-race into a full loop rewrite (the big one)

The agreed change was surgical: *fire 128 always, race the tail* — a delta to `run_loop`, keeping
buffer / working-set / 2-strikes / proxy-reuse / cooldown. Instead I scoped a full rewrite
(`run_loop` → `run_race`, `p4_race.py`), dropping proxy-reuse. Reuse was load-bearing: a good proxy
fetched many sub-sitemaps. Result: 64er regressed **64/64 → 2/64**.
- **Cause:** the diff-size did not match the concept-size. I wrote a worker prompt that said "replace
  run_loop with a new continuous-dispatch model" for something we both called a small change.
- **Prevention:** a "small change" must be a surgical delta that NAMES what stays unchanged (which
  should be most of the code). A prompt that says "replace / rewrite / new design" for an agreed-small
  change is the red flag — stop and reframe as "modify X so that …". Before dispatching a "small"
  change, state to the user in one line what stays and what changes, so an over-scope can be vetoed in
  five seconds.

## Error 2 — reviewed a rewrite against my own spec, not the baseline

The probe's `_fetch_parallel` was specified by me as "fire 128, first success" — a single 128-sample,
no pool walk. The worker built exactly that. In Phase-4 review I validated it as "correct" against my
spec — but it tried only 128 of ~18k proxies, doing LESS than the version it replaced (which walked
the whole pool). It then failed on the large `post_26`.
- **Prevention:** the first review question for any rewrite is "does this do at least what it replaced
  / what the goal needs?" Old `_fetch_parallel`-predecessor tried thousands; mine tried 128. One
  comparison catches it. (This same miss recurred at scale in Error 1.)

## Error 3 — wasted time re-proving the already-known

The first probe full-scanned all 27 `post_type_post` sub-sitemaps to "confirm" ascending pagination —
which a raw sitemap had already shown (post_0 = 2018). And I advised letting the slow run finish.
- **Prevention:** when existing evidence already answers a question, do not build a run to re-prove it.

## Error 4 — coupled a must-confirm action to a killable timer

`worker-cli send` was chained with a backgrounded `sleep` timer; a SIGTERM on the sleep (exit 143)
killed the send before it delivered — silent message loss.
- **Fixed structurally:** `monitor-cc/src/hooks/block_worker_send_background.py` blocks
  `worker-cli send` with `run_in_background=true`. Send must be its own foreground call; timer separate.

## What survived (not in the trash)

- Probe findings: The Block is server-rendered, JSON-LD `articleBody` + `datePublished`, no
  browser needed — real, reusable progress.
- The whole sustained design: intact on disk; `acquire_pipe` reverted to `run_loop`.
- The tail-race idea: `p4_race.py` kept as the reference for the surgical port.

## Next session (clean start from the above)

1. Port the tail-race into `run_loop` as a surgical delta (the "correct next step" from the tail-race regression).
2. Re-run the 64er; verify 64/64 + no straggler tail; inspect results.
3. Port the 48h-delta path into `src/news/` as a new platform.
4. Set up the one-time 27k backfill in `dev/`.
