# INFRASTRUCTURE
from dataclasses import dataclass


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    engine: str
    position: int
    preview: dict | None = None
