# Orchestrator verdicts for the full-src refactor run (2026-08-20)

Companion to this area's per-milestone worker entries: the scan results and classification
decisions taken at orchestration level, which no single milestone entry carries. The run covered
all of `src/` (iterative-dev refactor skill: Placement → Cohesion/Splits → Control-Flow →
Standards Conformance → Doc-Drift).

## Policy chain that triggered the run

Session start was a grounding review of both ad-hoc scrape lanes' configs. The user ruled that
derivation/provenance comments have no place at code values at all; the worker code-standards
(three comment types only) already encoded that, and the refactor skill was amended the same
session with an explicit comment-triage rule (uncovered substance → dated process-docs entry;
value-guards → DOCS.md Gotchas; covered → delete). Later the same session, the doccheck skill
gained the mirror rule for DOCS.md format cuts, simplified on user direction to a blanket
salvage: everything cut is written to one dated `<date>_docs_format_salvage.md` per affected
area, no coverage check — RAG makes it findable. Both amendments live in the iterative-dev repo.

## Step 1 — Placement: clean

`src/log_janitor.py` is the only top-level module; imported by three subpackages
(scraper/crawler/search) — justified at root, no move.

## Step 2 — classification calls beyond the worker entries

- Constant-cluster scan flagged `src/search/status.py` (EMPTY_*/TIMEOUT_*/ERROR_*) and
  `src/search/engines/google.py` (SOCS_*/_JS_*). Both classified as prefix-heuristic false
  positives: status.py is one hierarchical status vocabulary (parents + subs deliberately in one
  module); google.py's groups are three fields of ONE cookie plus the engine's own DOM scripts,
  all consumed in-file. No splits.
- For `src/scraper/scrape_url.py` (465 LOC) and `camoufox_scrape.py` (532 LOC) the >400 overage
  was comment-driven, not concern-mass. Decision: mandatory comment triage FIRST, then measure;
  split only if still >400. Post-triage 299/227 — no split. Deviation from a strict
  raw-LOC-first reading of the skill, taken deliberately: tearing ~230 code lines into modules
  to satisfy a threshold inflated by comments is the wrong cut, and the triage was mandatory
  anyway.

## Step 3 — Control-Flow: zero fixes, all findings classified

- Tripwires (kept): both scrape lanes' fail-soft `acquisition_error` returns, the search-engine
  status taxonomy surfaced via `search_with_reason`/`_engine_with_timing`, cache-miss `None`,
  `log_janitor`'s logged prune degradation.
- Deliberate alternative acquisition, NOT correctness fallbacks (kept): pipe_scraper's curl_cffi
  paths a/b and the fit→raw content selection. Which route ran is recorded first-class in the
  logs (`pipe_fallback_used`, `crawl4ai_resolved_by`, `fallback_to_raw`) and the output honestly
  labeled — the One-Way-Redesign doctrine targets internal double derivations that can diverge,
  not externally-blocked acquisition with an alternative transport. User informed, no veto.
- Legacy surface (kept): the 16 engines' exception-swallowing `search()` wrappers serve 23
  `dev/search_pipeline` scripts only; the production path does not swallow.

## Baseline note

The run started against a documented 9-failed baseline that was really 10 (one
`test_query_logger` test postdated the last baseline record). At session end the baseline was
repaired to 192 passed / 0 failed (see this area's dead-code-and-baseline entry for the five
root causes); future sessions measure against green.

## Run shape

Two workers (crawler/search area, news area), strictly sequential milestones, each with plan
gate (skipped once, deliberately, for a comments-only sweep), full-diff review, recap, merge.
One worker session-limit hit and one mid-response API drop occurred; both recovered without
loss (uncommitted worktree state survived, resume prompts continued the milestone).
