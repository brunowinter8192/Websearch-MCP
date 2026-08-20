# INFRASTRUCTURE
import asyncio
import random
import time

# FUNCTIONS

# Return or create per-domain state entry (lastseen, lock, sem) — asyncio-safe (no await, no race)
def _ensure_domain_state(domain_states: dict, domain: str, concurrency_per_domain: int) -> dict:
    if domain not in domain_states:
        domain_states[domain] = {
            'lastseen': 0.0,
            'lock': asyncio.Lock(),
            'sem': asyncio.Semaphore(concurrency_per_domain),
        }
    return domain_states[domain]

# Scrapy gate: under domain lock, wait until delay elapsed since lastseen, then stamp lastseen=now.
async def _gate_domain(state: dict, download_delay: float) -> None:
    async with state['lock']:
        jitter = random.uniform(0.5 * download_delay, 1.5 * download_delay)
        now = time.time()
        gap = now - state['lastseen']
        if gap < jitter:
            await asyncio.sleep(jitter - gap)
        state['lastseen'] = time.time()
