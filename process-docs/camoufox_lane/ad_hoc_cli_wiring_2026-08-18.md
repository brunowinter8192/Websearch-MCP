# Camoufox lane, milestone 2: ad-hoc CLI wiring (2026-08-18)

Continues the `camoufox_lane` area (milestone 1 built the calibrated core module,
`try_scrape_camoufox`, with no CLI surface). This session wired it into the ad-hoc surface as
`scrape_url_camoufox` — a deliberate SECOND acquisition lane parallel to `scrape_url`, not a
fallback, the agent picks one by which subcommand it invokes. Pipe-lane wiring remains a later
milestone.

## The engine discriminator: a first-class field, not config-shape archaeology

Both lanes share the exact same `scrape_log.jsonl` file (same `log_scrape`/`write_sidecar`
functions). The config stamp already differs completely by shape between the two engines
(chromium: `headless`/`enable_stealth`/`adapter`/`crawler_strategy`/... vs camoufox:
`headless`/`os`/`block_images`/`executable_path`/...), but requiring a reader to infer engine from
config shape is exactly the kind of low-signal archaeology this project's own logging conventions
have consistently avoided elsewhere. Added `"engine": "chromium" | "camoufox"` as its own field —
retrofitted into `scrape_url.py`'s existing `log_scrape` call too, not just the new camoufox one,
since a discriminator that only exists on one side of a two-sided distinction isn't really a
discriminator. Absent on every record written before this field existed, same convention as every
prior field addition in this project.

Every field only one engine's acquisition can produce got the same "absent, not null" treatment
already established for prior single-engine fields: `content_type`/`fallback_to_raw`/
`crawl4ai_success`/`crawl4ai_error_message`/`crawl4ai_attempts`/`crawl4ai_resolved_by`/
`crawl4ai_fallback_fetch_used`/`published_date` are absent (key never written) on
`"engine": "camoufox"` records; `markdown_conversion_error`/`content_is_raw_html` are absent on
`"engine": "chromium"` records. Verified directly against the real written JSONL records after the
CLI runs below (`'content_type' in record` → `False`, etc.), not just asserted in code comments.

`published_date` specifically: the camoufox lane never attempts htmldate extraction at all — a
permanent characteristic of the engine, not a per-call miss or an unimplemented feature. Treated
the same as the other engine-exclusive fields (absent) rather than as a special "always-null" case,
for internal consistency across the whole absent-vs-null convention rather than one-off reasoning
per field.

## config_hash: read once, not re-hashed

`try_scrape_camoufox` already computes `config_hash` internally (unlike the chromium lane, where
`scrape_url_workflow` computes it from `meta["config"]`) — a genuine, deliberate difference between
the two lanes' internal shapes, not an inconsistency to paper over. `scrape_url_camoufox_workflow`
reads `meta["config_hash"]` straight through rather than re-calling `hash_config`, which would
still produce the identical value (hashing is deterministic) but would be redundant work and would
also invite drift if the hashing algorithm's call site ever needed to change in only one place.

## The renderer: a sibling, not a shared function

`scrape_url.py`'s `_format_scrape_output` and this session's new `_format_camoufox_output` share
the same fixed-shape PHILOSOPHY (facts always, unconditionally, before a fixed `## Content`
delimiter; landed URL unconditional, same rule as the chromium lane adopted earlier this session)
but are two separate functions. The two lanes' fact vocabularies diverge too much to share one
renderer without conditional logic that would itself violate "always the same shape": the chromium
lane has `content_type`, crawl4ai's own anti-bot diagnosis, and `fallback_to_raw` (a real fit/raw
content SELECTION); the camoufox lane has none of these and instead has
`markdown_conversion_error`/`content_is_raw_html`, concepts the chromium lane has no equivalent of
at all. Reusing one function would have meant scattering `if engine == ...` branches through what
is supposed to be an unconditional-facts renderer — the wrong trade for two lanes whose real
acquisition facts are this different.

The `content_is_raw_html` line follows the SAME conditional-presence precedent already used for
`Acquisition error` (present only when there is something to say) but is worded to be unmissable
when it appears: "RAW HTML, NOT markdown" plus crawl4ai's `markdown_conversion_error` surfaced
verbatim as an OBSERVATION, not a verdict — the agent reading the block must know exactly what
format it is holding and why, not infer it from a missing byte count.

## Verification

19 tests added this session (7 new, on top of the 12 from milestone 1): the workflow logs the
engine discriminator; `config_hash` is read, not re-hashed; `mode` reflects the raw-HTML fallback;
`_format_camoufox_output`'s four shapes (normal markdown, landed-URL-absent still rendering
literally, the raw-HTML shape stating the conversion error plainly, the acquisition-failure shape).

Real CLI runs, both inspected via rendered output AND the written JSONL record directly:

- `rfc-editor.org/info/rfc2616/` (control): `engine=camoufox`, `landed_url` identical to the
  request, `http_status=200`, `mode=markdown`, 470,169 real markdown bytes, no
  `markdown_conversion_error`.
- `idealo.de` OffersOfProduct (the full showcase, same URL as milestone 1): `engine=camoufox`,
  `http_status=200` (Akamai passed again), `landed_url` still the wrong product (the jacket page),
  `mode=raw_html`, `content_is_raw_html=true`, `markdown_conversion_error` carrying crawl4ai's
  `Invalid IPv6 URL` message verbatim, 911,576 bytes of raw HTML returned as content rather than the
  page being silently lost. The rendered block surfaces engine, the wrong-product landed URL, and
  the raw-HTML observation together — a reader gets the complete picture from one block, without
  needing to separately consult the log.

Full suite: `9 failed, 167 passed`. `FAILED` list diffed against the standing baseline (7
`test_query_logger.py` + 2 `test_proxy_pool.py`) — identical, no drift.

No change to `try_scrape_camoufox`'s own acquisition behavior, `pipe_scraper.py`, or any skill file
— all explicitly out of this milestone's scope. The mandatory, deferred `open -g`/no-focus-steal
requirement recorded in milestone 1 remains open, resolution point still the pipe-wiring milestone;
nothing in this session's work touched it.
