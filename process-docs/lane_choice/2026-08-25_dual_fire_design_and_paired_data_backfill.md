# Dual-fire lane choice: design decisions and the paired-data backfill (2026-08-25)

New area. Driving question: when BOTH ad-hoc scrape lanes (`scrape_url_chromium`, `scrape_url_camoufox`)
fire on the same URL, how does the calling agent decide which output to read — without an LLM
classifier and without misleading single numbers? Orchestrator-side entry: the design discussion,
external grounding, and data-generation status. Implementation (a metrics summary + scorer) had not
started as of this entry. Draws on `process-docs/scrape_pipeline/` (fact-reporting contract),
`process-docs/camoufox_lane/` (second-lane design), and newly indexed external papers — a new area,
not a continuation of any one of them.

## Design decisions (user + orchestrator, chat-level)

- **Dual-fire, agent decides.** Both lanes fire on one URL; the response carries a compact per-lane
  summary first (the drilldown principle the agent already knows from search); the agent then reads
  the better output. No auto-selection — consistent with the camoufox lane's founding rule (deliberate
  second lane, no trigger logic).
- **No LLM classification.** The Anthropic-style pattern (a small model reads pages and summarizes for
  the main agent) was rejected for ad-hoc use: hallucination risk plus latency. The decision signal
  must be deterministic and computable in milliseconds.
- **Scorer emits metrics, never a verdict.** The 2026-08-05 fact-reporting contract
  (`process-docs/scrape_pipeline/`) prohibits the module deciding for the agent. Scope precision from
  the user: that doctrine's escalations governed judgments WITHIN one scraper's output (same_target,
  fit→raw); CHOOSING between two scrapers is a different case — structurally safer here because the
  drilldown design keeps both outputs retrievable, so a wrong metric misleads but destroys nothing.
  The metrics-not-verdict shape is therefore a design preference out of caution, not a doctrinal ban
  on comparison.
- **Bytes alone are insufficient, evidenced.** Clear cases resolve on bytes (live pair, terminland.de,
  same URL 14s apart, both `outcome=ok`: chromium 38 bytes post-filter vs camoufox 2048 — camoufox had
  the real page). The documented failure band is the middle: idealo's "Sorry" page at 401 bytes looked
  small-but-real; trustpilot's HTTP 403 carried 42707 bytes of real page. Scale trap: chromium bytes
  are post-PruningContentFilter, camoufox bytes unfiltered — raw-vs-raw is the comparable pair.
- **Planned signal set** (as of this entry): normalized byte pair, link density and stopword density
  (Kohlschütter/jusText shallow features), existing garbage signatures as reported observations —
  thresholds to be calibrated on real paired data, per this project's log-before-config methodology.

## External grounding indexed into websearch-reference

Four papers converted (MinerU) and indexed 2026-08-25 (180 chunks): Kohlschütter WSDM 2010 (shallow
text features — number of words + link density alone reach competitive boilerplate classification;
link density >33% → boilerplate rule; text density threshold ~10), WCXB 2026 (2,008-page multi-type
benchmark: systems converge on articles F1≥0.87, diverge 0.41-0.84 on structured types), Gupta/Webis
2022 thesis (14-extractor comparison, ensembles as SOTA baseline — validates running two engines and
choosing per page), Zhang 2022 (neural SemText, indexed for contrast). Conversion note: the Zhang PDF
triggered a MinerU VLM repetition loop (5386 hallucinated `</footer>` lines inside one code block,
97K→19.7K chars after collapsing runs >3; real text unaffected, resumes seamlessly). All four cleaned
per the websearch-pdf skill classes (backmatter stripped, tables to pipe-text, spaced math collapsed
with alphanumeric-count invariant).

## Paired-data backfill: status as of this entry

The production `scrape_log.jsonl` was heavily one-sided (109 chromium / 6 camoufox records, only 3
URLs covered by both) — no basis for calibrating a lane choice. Decision: re-fire BOTH lanes fresh
per distinct URL (historical records are config/site-drift stale; pairs must be time-close), via the
production CLI so every record is a real production record. Tooling and state live in
`dev/lane_choice/` (backfill orchestrator, dual-instrument focus-poll wrapper, resume-state JSONL).

Status at session end: 62 of 106 distinct URLs paired (124 fresh records; outcomes 61 ok / 1 empty
on chromium, 61 ok / 1 exception on camoufox — the tedi-shop.com search URL failed on both lanes,
itself a data point). The remaining 44 URLs resume with
`./venv/bin/python dev/lane_choice/02_focus_poll_smoke.py` (resume state skips completed pairs;
~20 min). The run was deliberately paused twice for the camoufox focus-steal work recorded in
`process-docs/camoufox_lane/` (two-layer fix; residual ≤1.5s flicker per camoufox launch pending
upstream daijro/camoufox#739).

## Open at entry time

- Remaining 44 URL pairs (resume command above).
- The scorer itself: signal implementation, threshold calibration on the paired corpus, summary
  format (per-lane facts; head-sample idea from the discussion not yet decided).
- Whether the pipe lane needs the same summary surface later — out of scope for the ad-hoc design.
