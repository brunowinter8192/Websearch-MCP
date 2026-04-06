# INFRASTRUCTURE
import asyncio
import logging
import random
import time

logger = logging.getLogger(__name__)

MAX_REQUESTS = 10
WINDOW_SECONDS = 60.0
JITTER_MIN = 1.0
JITTER_MAX = 3.0
BACKOFF_BASE = 30.0

_limiters: dict[str, "RateLimiter"] = {}


class RateLimiter:
    """Token bucket rate limiter with jitter and exponential backoff."""

    def __init__(self, max_requests: int = MAX_REQUESTS, window_seconds: float = WINDOW_SECONDS):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._tokens: list[float] = []
        self._lock = asyncio.Lock()
        self._backoff_until: float = 0.0
        self._backoff_attempt: int = 0

    async def acquire(self) -> None:
        """Wait until a request can be made, respecting rate limits."""
        logger.debug("Rate limit: acquiring token")
        async with self._lock:
            now = time.monotonic()

            # Respect backoff from 429/403 responses
            if now < self._backoff_until:
                wait = self._backoff_until - now
                await asyncio.sleep(wait)
                now = time.monotonic()

            # Remove tokens older than the window
            self._tokens = [t for t in self._tokens if now - t < self._window_seconds]

            # If at capacity, wait until the oldest token expires
            if len(self._tokens) >= self._max_requests:
                oldest = self._tokens[0]
                wait = self._window_seconds - (now - oldest)
                if wait > 0:
                    await asyncio.sleep(wait)
                    now = time.monotonic()
                    self._tokens = [t for t in self._tokens if now - t < self._window_seconds]

            # Add random jitter between requests
            jitter = random.uniform(JITTER_MIN, JITTER_MAX)
            await asyncio.sleep(jitter)

            self._tokens.append(time.monotonic())

    def backoff(self) -> None:
        """Set exponential backoff after a 429/403 response."""
        delay = BACKOFF_BASE * (2 ** self._backoff_attempt) + random.uniform(1.0, 10.0)
        logger.warning("Rate limited, backing off %ds", delay)
        self._backoff_until = time.monotonic() + delay
        self._backoff_attempt += 1

    def reset_backoff(self) -> None:
        """Reset backoff counter after a successful request."""
        self._backoff_attempt = 0


# Return per-engine singleton rate limiter with optional custom config
def get_limiter(engine_name: str, max_requests: int = MAX_REQUESTS, window_seconds: float = WINDOW_SECONDS) -> RateLimiter:
    if engine_name not in _limiters:
        _limiters[engine_name] = RateLimiter(max_requests, window_seconds)
    return _limiters[engine_name]
