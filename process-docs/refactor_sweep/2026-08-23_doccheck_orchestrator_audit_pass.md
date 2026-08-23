# doccheck orchestrator audit pass — area verdicts, invariant fixes, first compression wave (2026-08-23)

Orchestrator half of a full `iterative-dev-doccheck` run over the project's doc surface (the worker
half — dev folder-naming restructure + the src DOCS Purpose compression — is recorded in this
area's own worker-pass entries of the same run). This entry holds the reasoning that lived only in
the orchestrator session: the per-folder area verdicts, the invariant fixes, and the first
compression wave.

## Area verdicts (all 18 process-docs folders judged)

Folded into `process-docs/scrape_pipeline/` (entries moved, folders dissolved):

- `cloudflare_render_wait` — overlap: "how long must the render wait be" is a sub-question of the
  ad-hoc lane's acquisition tuning; the strand's continuation was already tracked under
  scrape_pipeline, and its two entries came from one session.
- `time_budget` — single-settled: one entry (the config rules + promised-maximum derivation), one
  session. Folded to scrape_pipeline because the governed budgets are scrape budgets. Known cost:
  historical area references to `process-docs/time_budget/` in other write-once entries now dangle —
  accepted, entries stay untouched, RAG still finds the content.
- `scrape_toolbox` — single-settled: one entry (toolbox scoping + ad-hoc calibration), same parent.

Entry moved: the 2026-08-02 headed-vs-headless external-evidence entry left `engine_expansion` for
`browser_posture` — entry-membership: it answers the posture question, not "which engines join the
lineup." The historical justification prose in older browser_posture entries that named its old
location stays as written (write-once).

Kept VALID despite failing the single-settled test: `pdf_pipeline` and `project_rename` — both are
completed strands with NO existing parent area to fold into; a fold target that doesn't exist beats
inventing one. All remaining folders (browser_posture, scrape_pipeline, search_pipeline,
engine_expansion, news_pipeline, camoufox_lane, explore_pipeline, agentic_discovery, pooling,
pipe_scraper, pipe_scraper_hardening, refactor_sweep, logging) passed with a stateable driving
question and no misfiled entries beyond the one move above.

## Invariant fixes across process-docs

- 7 cross-entry PATH references (a specific `.md` named with its full `process-docs/<area>/...` path)
  generalized to AREA references + a dated descriptive pointer; 6 intra-area filename references
  ("this area's `<file>.md`") reworded descriptively. Ruling applied: references point at areas,
  never at single entry files — a specific entry is found via RAG/browsing.
- 2 issue mentions removed from entries (a "(a GitHub issue)" parenthetical and a "the outcome is
  two issues" clause) — docs never point back at issues.
- 3 undated entries dated from their git history: the no-backoff bound-principle record
  (2026-05-22), the pydoll non-coop teardown design (2026-05-31), the explore-pipeline design/levers
  framing doc (2026-05-29).
- Language check: every German-looking grep hit was quoted DATA (cookie-banner texts, consent
  markers) — zero violations. RAG manifest covered both layers correctly.

## dev surface (orchestrator part)

Empty `dev/akamai_probe/` deleted. `dev/cleanup/` renamed to `dev/agentic_discovery/` — its
clean_web_* scripts post-process the captured RAG collections, i.e. the capture-and-index strand.
The source-coupled renames (output folders hardcoded in scripts) went to the worker pass.

## First compression wave (orchestrator-edited DOCS)

`src/news/**` (7 DOCS.md files) and `dev/browser_posture/DOCS.md` compressed to format — Purpose to
one sentence, function-level walkthroughs and refactor-history paragraphs cut, cut content salvaged
BEFORE cutting into one dated salvage entry per area (news_pipeline, browser_posture). Behavior
constraints worth keeping were moved into Gotchas instead of cut (e.g. the regwall-guard manifest
contract, the rider.py attribute-patchability constraint, the AcquireLogger-after-start_job ordering
landmine). Also fixed: one LOC-heading mismatch, two dead references (a moved log path, a reference
into the just-folded cloudflare_render_wait folder), and the non-standard "Sub-Engines" section
(folded into the engine package's Flow).

The line-based audit script (`/tmp`, sentence/LOC/section checks) under-detected the src DOCS
mega-line Purposes — single physical lines carrying full derivation histories — which is why the
compression of `src/scraper`/`src/crawler`/`src/search`/`src/search/engines` went to the worker
pass with an explicit salvage instruction rather than being caught by the same audit.
