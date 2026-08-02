# Client-side API reference pages scrape to `Loading...` placeholders

**Date:** 2026-08-02
**Topic:** A page class where every escalation phase "succeeds" but returns no body — nav chrome plus repeated `Loading...` placeholders. Observed on 13 pages of one domain; the cleaner rejects them on `no h1`, so the failure surfaces late.

## Sources

- `src/scraper/scrape_url.py` — phase escalation (fastpath → browser_1a networkidle → browser_1b domcontentloaded → browser_2_stealth)
- Capture run 2026-08-02 against `platform.claude.com/docs/en`, target collection `monitor-cc-reference`
- Artefact on disk: `~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/monitor-cc-reference/platform_claude_com_docs_en_api_messages_create.md`

## Observation

Scraping `https://platform.claude.com/docs/en/api/messages/create` reports success — no error, no timeout, non-trivial byte count. The resulting markdown is 205 lines and contains the cookie banner, the full nav sidebar, the search box, and **51 occurrences of the literal string `Loading`**. The h1, the parameter tables and the request/response examples never appear. Two consecutive attempts produced the same result.

The same signature appeared on 12 further pages of the same domain, all under `api/messages/*` and `api/models/*`:

```
api/messages, api/messages/count_tokens, api/messages/create,
api/messages/batches (+ cancel, create, delete, list, results, retrieve),
api/models, api/models/list, api/models/retrieve
```

Neighbouring sections of the same domain scraped cleanly in the same run — `build-with-claude/*`, `agents-and-tools/tool-use/*`, `managed-agents/*`, `about-claude/*` all produced full bodies. The failure is scoped to one page *template*, not to the domain and not to a rate limit.

## Mechanism (hypothesis, not proven)

The API reference template renders its body client-side after the shell has painted. `domcontentloaded` fires and `networkidle` is plausibly reached, since the placeholder state is quiet — so no phase escalates, and the phase that "wins" is one that returns the pre-hydration DOM. The `Loading` strings are the placeholder cells of the parameter tables, captured verbatim.

Not verified: which phase actually served the result on these pages, and whether a longer wait alone is sufficient. The scrape log per page would settle both and was not inspected during the capture session.

## Why it is worse than a hard failure

An HTTP error stops the pipeline and is visible immediately. This returns HTTP 200 with plausible-looking markdown, so:

- the scrape funnel counts it as `ok` (run reported `49/49 ok, 0 errors`)
- the file lands on disk and overwrites whatever was there before
- the failure only surfaces one stage later, in the cleaner, as `no h1` — a rejection reason that reads like a formatting problem, not like an empty page

In the 2026-08-02 run the cleaner's `no h1` rejection was the *only* signal that 13 pages had no content.

## Candidate mitigations

Ordered by how much per-domain tuning they invite:

1. **Wait-for-selector.** Wait for a content-bearing element (e.g. an `h1` inside the main region) before returning. Directly targets the actual condition — "body has hydrated" — instead of approximating it by time or network quiet.
2. **Longer `delay_before_return_html` on a retry phase.** Cheap to add, but a fixed delay is a guess; too short still fails, too long taxes every page in the class.
3. **Post-scrape content assertion.** Treat "no h1" or "N× `Loading` and nothing else" as a scrape failure rather than a cleaner rejection, so the pipeline escalates instead of shipping an empty page. This does not fix the capture, but it moves the detection to where an escalation is still possible.

(1) and (3) compose: assert on the result, escalate to a selector wait when the assertion trips. Note the hamster-wheel risk already recorded for phase escalation — per-domain selector lists do not generalise; the assertion in (3) is the part that stays domain-agnostic.

## Collateral state left behind (2026-08-02)

The 13 raw files remain on disk in `monitor-cc-reference` while their previously indexed chunks — from an earlier crawl, with real content — remain in the index and are still functional. Deliberately not resolved in that session: a full reindex of the collection would pull the raw placeholder content in and silently replace working chunks.
