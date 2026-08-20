# INFRASTRUCTURE
from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable


# FUNCTIONS

@dataclass
class ProxyScrapeConfig:
    pool_provider: Callable[[], tuple[list[tuple[str, str]], list[dict]]]
    content_type: str = "html"
    concurrency: int = 128
    buffer_size: int = 1280


@dataclass
class ScrapeConfig:
    download_delay: float = 1.0
    concurrency_per_domain: int = 8
    page_timeout_ms: int = 15000
    delay_before_return_html: float = 0.5


@runtime_checkable
class Platform(Protocol):
    name: str
    collection: str
    precondition_url: str
    regwall_signals: list[str]
    scrape_engine: str
    scrape_config: ScrapeConfig
    proxy_scrape_config: "ProxyScrapeConfig | None"

    async def discover(self) -> list[dict]: ...
    def cleanup(self, raw_markdown: str, entry: dict) -> str: ...
