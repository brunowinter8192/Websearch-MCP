# INFRASTRUCTURE
from abc import ABC, abstractmethod

from src.search.result import SearchResult


# Abstract base class for all search engine implementations
class BaseEngine(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, language: str = "en", max_results: int = 10) -> list[SearchResult]:
        ...
