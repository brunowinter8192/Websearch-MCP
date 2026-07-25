# INFRASTRUCTURE
from pathlib import Path

from src.news.platform import ScrapeConfig

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # websearch/

# Precise regwall signals — do NOT use loose markers (subscribe/register fire on article footers)
REGWALL_SIGNALS: list[str] = [
    "from_regwall",
    "Create a FREE account to continue reading",
    "You've reached your monthly limit",
]

SCRAPE_CONFIG = ScrapeConfig()

# Timeline API
TIMELINE_BASE = "https://www.coindesk.com/api/v1/articles/timeline"
COINDESK_BASE = "https://www.coindesk.com"
TARGET_URL    = "https://www.coindesk.com/latest-crypto-news"

# Discovery loop
CALL_DELAY           = 0.3     # seconds between cursor calls
REWARM_EVERY         = 240.0   # proactive re-warm interval (seconds)
CLICKS_WARMUP        = 8       # clicks for initial browser warmup (SSR buffer clears at ~click 6)
CLICKS_REWARM        = 7       # clicks for browser re-warm
MAX_CURSOR_FALLBACKS = 3       # cursor anchor fallback attempts before declaring rewarm needed
CHECKPOINT_EVERY     = 50      # log progress every N successful cursor calls
DEFAULT_DELTA_DAYS   = 30      # days back when timeframe is "delta" or unparseable int
FULL_MODE_FLOOR      = "2018-01-01"   # full-mode stop date; Binance candles start 2017-08

# Master URL discover shards: data/news/coindesk/discover/coindesk_{year}.txt
DISCOVER_DIR = PROJECT_ROOT / "data" / "news" / "coindesk" / "discover"

SKIP_HEADERS = frozenset({
    ":authority", ":method", ":path", ":scheme",
    "host", "content-length", "content-encoding", "transfer-encoding",
})
