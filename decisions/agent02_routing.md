# Agent Step 2: Plugin Routing

## Status Quo

**Code:** `agents/web-research.md` (Step 2: Filter Results), `skills/agent-web-research/SKILL.md` (Plugin Routing section)

**Routing table** (applied to all search results before scraping):

| Domain | Action | Plugin |
|--------|--------|--------|
| arxiv.org | Report: "USE RAG PLUGIN" | `mcp__rag__search_hybrid` or `/rag:pdf-convert` |
| github.com | Report: "USE GITHUB PLUGIN" | `github__get_file_content` |
| reddit.com | Report: "USE REDDIT PLUGIN" | `reddit__search_posts` |
| youtube.com | SKIP entirely | — (video content not scrapable) |

**Routing logic:** URL-domain matching only. No content-based routing. No subdomain handling documented.

**Agent output:** Plugin-routed URLs reported in a separate section ("Plugin-Routed URLs") with plugin action tagged. Not scraped.

## Evidenz

Plugin routing compliance across 3 eval agents:

| Agent | Plugin-routed URLs |
|-------|-------------------|
| Agent 4 (test) | 22 |
| Agent 5 (chunking) | 28 |
| Agent 6 (embedding) | 40+ |

No misrouted URLs observed (no arxiv/github/reddit URLs in scraped content). Routing appears reliable.

High plugin-routed counts (40+) suggest the routing table is working — arxiv and github appear frequently in research-topic searches, and agents correctly separate them instead of attempting to scrape.

## Entscheidung

Plugin routing is the best-functioning part of the agent pipeline. No change needed.

The routing table is correct: arxiv/github/reddit all have dedicated plugins that provide better access than scraping (structured metadata, full content, no auth issues). youtube skip is correct (no scraping value).

One gap: no routing for `huggingface.co` (model cards, papers with code — frequently appears in ML research). Currently scraped like any other domain; scraper may hit rate limits or return incomplete model card content.

## Offene Fragen

- Should `huggingface.co` be added to the routing table? HF has no dedicated plugin currently, so it would need to either: (a) be scraped as normal, (b) be skipped, or (c) be noted for future plugin development.
- What about `paperswithcode.com`? Frequently surfaces in ML benchmarks. No dedicated plugin, but content is structured and scrapable.
- Subdomain handling: does `gist.github.com` match the `github.com` routing rule? If not, gists get scraped instead of plugin-routed.
- Should the routing table be in `SKILL.md` only (tool reference) or duplicated in `agents/web-research.md` (agent instructions)? Currently duplicated — risk of divergence.

## Quellen

- `agents/web-research.md` — Step 2 routing instructions
- `skills/agent-web-research/SKILL.md` — Plugin Routing table (canonical reference)
- Eval session findings (2026-03-15): 22/28/40+ plugin-routed URLs, no misrouting observed
