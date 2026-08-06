# Camoufox lane: block_images default unified to False (2026-08-21)

Continues the `camoufox_lane` area. Resolves the open calibration question recorded in
`pipe_switch_and_no_focus_steal_2026-08-20.md`: the pipe engine (`src/crawler/pipe_scraper.py`)
defaulted `block_images=True`, split from the ad-hoc lane's (`scrape_url_camoufox_workflow`)
`block_images=False`.

## Decision

Settled by the user this session, by design decision rather than measurement: `block_images`
defaults `False` on BOTH Camoufox call sites — `scrape_urls_workflow`/`_scrape_all`
(`src/crawler/pipe_scraper.py`) and `scrape_url_camoufox_workflow`/`try_scrape_camoufox`
(`src/scraper/camoufox_scrape.py`, already `False`, unchanged). Stealth wins over the bandwidth
saving: Camoufox's own `LeakWarning` ("Blocking image requests has been reported to cause
detection issues on major WAFs...") is a documented anti-bot-signal risk, and this lane exists
specifically for hard anti-bot targets — a bandwidth saving that risks a documented detection
signal was judged not worth it. Images never reach the pipeline's output either way (markdown
text), so nothing about content changes with either setting. An explicit `block_images=True`
still overrides the default for a caller who deliberately wants it.

No new measurement was taken (the tension recorded 2026-08-20 — no pass-rate data on either side —
still holds as of this entry); the decision closes the question by design priority rather than by
resolving that data gap.

## Implementation

- `scrape_urls_workflow`/`_scrape_all` default changed `True` -> `False`.
- CLI `--block-images`/`--no-block-images` share `dest='block_images'`: argparse resolves a shared
  dest's default from the FIRST action added that lacks a namespace value yet (confirmed via
  `argparse.ArgumentParser.parse_known_args`'s `hasattr(namespace, action.dest)` gate) — so
  `--block-images`'s own `default=` is what governs omission, not `--no-block-images`'s. Changed
  that default `True` -> `False` accordingly; `--no-block-images`'s default is inert but left in
  place for symmetry.
- `src/scraper/camoufox_scrape.py` needed no code change — verified both defaulting sites already
  held `False`.
- `tests/test_pipe_scraper.py`: added `test_scrape_all_camoufox_default_block_images_is_false`
  (asserts `_scrape_all(engine="camoufox")`, `block_images` omitted, calls
  `try_scrape_camoufox(..., block_images=False)`); left the existing explicit-`True` dispatch test
  unchanged (already proves an explicit value overrides the default).

## Verification

`tests/test_pipe_scraper.py`: 34/34 passing (unit/integration level — real `_scrape_all` call
graph, `try_scrape_camoufox` faked at the I/O boundary). Full suite: 181 passed, 9 failed
(standing baseline: 7 `test_query_logger` + 2 `test_proxy_pool`, unrelated to this change, no
drift). No live CLI subprocess test was run against `--block-images`/`--no-block-images` — the
argparse default-resolution reasoning was verified by reading argparse's own source
(`get_original`/dest-resolution logic), not by a subprocess-level test (none existed for this
module's CLI block prior to this change).
