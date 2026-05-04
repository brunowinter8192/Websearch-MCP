# INFRASTRUCTURE
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    engine: str
    position: int
    preview: dict | None = None
    engines: list[str] = field(default_factory=list)   # all engines that returned this URL (set by merge step)
    snippets: dict[str, str] = field(default_factory=dict)  # snippet per engine, key = engine name (set by merge step)
