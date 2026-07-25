# Cross-Site Signal Aggregation Design

## Scope of this note

Forward-looking design decisions for the news_pipeline architecture as we expand beyond CoinDesk to multiple news sources. Not yet implemented — captures the design intent before we commit to it in code.

## Decision: No cross-site URL-dedup

A single piece of news appearing on multiple independent sources is a **stronger signal**, not a duplicate to suppress. Two CoinDesk + The Block + CoinTelegraph reports on the same Fed-decision-impact carry more weight than one isolated report. The trading-bot LLM-layer should SEE the multi-source coverage as positive signal-amplification, not have it deduplicated away.

## Decision: Per-site URL-dedup only

Each news source maintains its own URL-seen state. The dedup logic operates per-site: a URL scraped by a previous run of THAT site's pipeline is skipped. Cross-site, no comparison happens — same story-URL from CoinDesk and The Block are stored as two distinct indexed documents.

## Decision: Channel independence as selection criterion

Adding a new news source requires the source to be GENUINELY INDEPENDENT from already-included sources — no echo chambers. Avoid:

- Sources that primarily aggregate / re-post other crypto sites
- Sources owned by the same parent company (e.g., avoid two outlets from the same media group)
- Sources that consistently cite each other as primary source (one is the original reporter, others are secondary)

Prefer:

- Original reporters with own newsrooms
- Sources with different geographical / cultural reporting perspective (e.g. US vs European vs Asian crypto-news)
- Sources with different editorial focus (news vs analysis vs deep-research)

## Implication: Same story = N indexed documents

When the same event (e.g., a SEC ruling) is reported by 5 independent sources, we end up with 5 separate indexed documents. The LLM-layer can interpret this as confirmation-via-multiple-sources. RAG queries will return all 5 as separate chunks, and the LLM synthesizes the cross-source picture.

## Open: When N reports of same story is noise vs signal

If 10+ independent sources report the same story, is that signal or noise? Probably signal initially (high-impact event), then noise as sources echo. Mitigation may need to come from RAG-search-time filtering rather than indexing-time deduplication. Deferred — revisit after multi-site indexing produces enough data to evaluate empirically.

## Trigger for next session

This note was written at end-of-session as the CoinDesk single-site dev pipeline reached milestone-complete state. Next session work guided by this design:

1. Promote CoinDesk dev/news_pipeline to prod (decide MD storage location, build RAG vector collection, build per-site URL-dedup module, full indexed run)
2. Discover and add the next Layer-1 site applying the channel-independence criterion above
3. Cron orchestrator deferred to a following session
