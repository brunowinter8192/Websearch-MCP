# 72 — CoinDesk CLI Concurrency Flags (--browsers / --slots)

## What we did

Added `--browsers N` and `--slots N` to the `python -m src.news` argparse entry point so
proxy_riding concurrency can be tuned per run without code edits.

**Files changed:**
- `src/news/__main__.py` — two new `parser.add_argument` entries; both threaded into the
  `run_scrape_only(...)` call as `n_browsers=args.browsers, n_slots=args.slots`
- `src/news/pipeline.py` — `import dataclasses` added to INFRASTRUCTURE; `run_scrape_only`
  gains `n_browsers: int | None = None, n_slots: int | None = None` params; override block
  inserted immediately after `riding_cfg = getattr(platform, "riding_scrape_config", None) or RidingScrapeConfig()`

## Override mechanism

```python
overrides = {k: v for k, v in (("n_browsers", n_browsers), ("n_slots", n_slots)) if v is not None}
if overrides:
    riding_cfg = dataclasses.replace(riding_cfg, **overrides)
```

`dataclasses.replace` produces a new `RidingScrapeConfig` instance with only the supplied
keys replaced; all other fields (`burn_threshold`, `page_timeout_ms`, `stall_timeout_s`) keep
their config-default values. A flag left as `None` is excluded from `overrides` → the field
is untouched. No flags → `overrides` is empty → `dataclasses.replace` never called → byte-identical
to the pre-change behavior (4 browsers × 16 slots/browser = 64 slots total).

## Backward compat

Default state: `n_browsers=None, n_slots=None` in both argparse and `run_scrape_only` signature.
Existing callers that omit the new params get the config defaults unchanged.
Other scrape paths (browser `--scrape-only`, full pipeline, discover) never receive nor inspect
the new params — no code changes in those branches.

## Tuning rationale

The riding engine's throughput scales near-linearly with slot count up to CPU saturation.
`RidingScrapeConfig` defaults (n_browsers=4, n_slots=64) are conservative; production machines
with spare CPU headroom can run 5×16=80 or 6×16=96 without code changes — just
`--browsers 5 --slots 80` or `--browsers 6 --slots 96` on the command line.
Previously this required editing `RidingScrapeConfig` defaults directly (or using the dev
prototype `run_coindesk_riding.py` which had `--browsers`/`--concurrency`). This change restores
the dev prototype capability on the production path while keeping defaults stable.

## Connection to dev prototype

`dev/coindesk/run_coindesk_riding.py` had equivalent `--browsers` / `--concurrency` flags for
exactly this sweep workflow. Production path now matches that capability; dev prototype unchanged.
