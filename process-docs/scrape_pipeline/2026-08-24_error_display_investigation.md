# Why scrapes surfaced as Bash [ERROR] despite returned content (2026-08-24)

Investigation of a recurring monitor-pane observation: `websearch scrape_url` calls displayed as
`Bash [ERROR] Exit code 1` while their output body visibly began with the normal
`# Content from: <url>` header. Question: acquisition failures, or an exit-code artifact?

## Quantification: the operational logs are green

Outcome distribution over the full 14-day retention window, as of 2026-08-24:

| Log | ok | empty | exception |
|---|---|---|---|
| `scrape_log.jsonl` (107 records) | 104 | 2 | 1 |
| `pipe_scrape_log.jsonl` (64 records) | 62 | 2 | 0 |

All non-ok records carried `http_status: null` (no acquisition result at all). No error cluster —
the pipeline itself was healthy; the [ERROR] impression could not come from acquisition.

## Mechanism: a monitor-cc hook rewrite orphaned dependent segments

Proven from monitor-cc's dual_log (full request payloads) + `hook_firing.jsonl`:

1. The model issued
   `websearch scrape_url <url> > /tmp/dpd_eckenheim.md 2>&1; wc -l /tmp/dpd_eckenheim.md; head -120 /tmp/dpd_eckenheim.md`.
2. monitor-cc's `rewrite_websearch_scrape_noise` hook stripped the redirect from the scrape
   segment (its purpose: full page must land in context, not a file) but left the later segments
   untouched.
3. `/tmp/dpd_eckenheim.md` was never created; the recorded tool_result ends with
   `wc: /tmp/dpd_eckenheim.md: open: No such file or directory` and the same from `head`.
4. Claude Code labels the whole Bash call with the LAST segment's exit code — `head` exited 1, so
   the call rendered [ERROR] with the fully successful scrape content on top.

The firing log recorded the rewrites verbatim (55 firings; e.g. original
`... 2>&1 | head -60` → rewritten without the pipe), confirming the hook, not the scraper.

Cross-check of shell semantics in the CC Bash runtime: `pipefail` is off, so a single-pipe
`scrape | head` yields exit 0 — only multi-segment chains with a failing LAST segment can produce
the observed exit 1, which matched the incident command exactly.

## Consequence

Nothing to fix in this project. The fix landed the same day in monitor-cc
(`process-docs/tool_use_safety/`, CLI-noise rewrite family converted to isolation block hooks):
noisy/chained scrape calls are now blocked with an instructive message instead of silently
rewritten, so a dependent segment can no longer desync from an edited command.
