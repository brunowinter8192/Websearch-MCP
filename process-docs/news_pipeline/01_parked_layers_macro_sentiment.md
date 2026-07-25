# News Pipeline — Parked Layers: Macro + Sentiment

## Scope of this note

Parking lot for layers beyond the current CoinDesk-only crypto-native scope. Not active decisions — preserved candidates from initial research so context survives iteration boundaries.

## Layer 1 — Crypto-native (active)

CoinDesk is the first site. Sitemap-based discovery confirmed working (Google News Sitemap at `/arc/outboundfeeds/news-sitemap-index`). Planned expansion: The Block, CoinTelegraph, Decrypt, CryptoSlate, Bitcoin Magazine, NewsBTC, AmbCrypto, BeInCrypto, CoinGape, Crypto Briefing, Bankless, The Defiant, U.Today, BTC-ECHO (de).

## Layer 2 — Macro/Financial (parked)

Rationale: BTC price reacts to macro signals — Fed decisions, CPI/PCE prints, ETF flow reports, dollar index (DXY), Treasury yields. Relevant sources:

**Free, no paywall:** Reuters, CNBC, MarketWatch, Yahoo Finance, Investing.com, ZeroHedge

**Paywall-limited (headlines/teasers only usable):** Bloomberg, WSJ, FT, Seeking Alpha

Note: macro sites have structurally different HTML than crypto-native sites — nav-heavy layouts, more aggressive paywalls, different JS rendering stacks. Separate filter strategy required; do not reuse CoinDesk filter directly.

## Layer 3 — Sentiment/Data (parked)

CoinCodex (fear & greed index), CoinGecko (price + market cap data), MarketBeat (analyst ratings), FXStreet (forex + crypto cross). These publish structured signals more than prose — may need a different parsing approach (structured data extraction vs markdown cleanup). Consider whether raw scrape is even the right tool here vs direct API access.

## Next expansion candidate

TBD — after CoinDesk filter design converges.
