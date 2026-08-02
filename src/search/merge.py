# INFRASTRUCTURE
import random
from collections import defaultdict

from src.search.result import SearchResult


# FUNCTIONS

# Group raw engine results into per-engine owned pools with cross-engine URL dedup.
# Owner = engine with lowest position for a URL; random choice on ties.
# Each pool sorted by owner engine's native position (ascending).
def build_engine_pools(results: list[SearchResult]) -> dict[str, list[SearchResult]]:
    # Step 1: group by URL — one bucket per URL, one entry per engine
    url_buckets: dict[str, list[SearchResult]] = defaultdict(list)
    for r in results:
        url_buckets[r.url].append(r)

    # Step 2: assign owner; build pool entries with engine_positions populated
    pools: dict[str, list[SearchResult]] = defaultdict(list)
    for url, bucket in url_buckets.items():
        min_pos = min(r.position for r in bucket)
        tied = [r for r in bucket if r.position == min_pos]
        winner = random.choice(tied)
        engine_positions = {r.engine: r.position for r in bucket}
        pools[winner.engine].append(SearchResult(
            url=winner.url,
            title=winner.title,
            snippet=winner.snippet,
            engine=winner.engine,
            position=winner.position,
            engine_positions=engine_positions,
            date=winner.date,
        ))

    # Step 3: sort each pool by owner engine's native position (ascending)
    return {eng: sorted(pool, key=lambda r: r.position) for eng, pool in pools.items()}
