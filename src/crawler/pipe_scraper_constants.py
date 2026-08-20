# INFRASTRUCTURE
# Pacing, timeout, and threshold constants shared across pipe_scraper.py's sibling modules
# (pipe_scraper_config.py, pipe_scraper_acquisition.py, pipe_scraper.py itself). Full sourced
# rationale for each value lives in src/crawler/DOCS.md (Purpose/Gotchas), not here.

DOWNLOAD_DELAY = 1.0
CONCURRENCY_PER_DOMAIN = 8
CAMOUFOX_CONCURRENCY_PER_DOMAIN = 1
PAGE_TIMEOUT_MS = 15000
DELAY_BEFORE_RETURN_HTML = 0.5
EMPTY_THRESHOLD_BYTES = 100
FALLBACK_FETCH_TIMEOUT_S = 15.0
