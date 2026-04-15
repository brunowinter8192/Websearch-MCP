"""Shared types for 28_stress_test.py helpers."""

# INFRASTRUCTURE
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryResult:
    query: str
    engine: str
    result_count: int
    response_time: float
    error: Optional[str]
    first_title: str
