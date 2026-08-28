# resume_state probe (20260828T151632Z)

Target: books.toscrape.com (static, stable). crawl4ai 0.9.2.

## Experiment 1 — existence + start_url fate

- start_url: `https://books.toscrape.com/index.html`
- resume_state pending (3): https://books.toscrape.com/catalogue/category/books/travel_2/index.html, https://books.toscrape.com/catalogue/category/books/mystery_3/index.html, https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html
- max_depth=0 (isolates: exactly 3 requests if start_url ignored)
- total results returned: 3
- all 3 pending URLs crawled: True
- start_url crawled too: False

  - `https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html` success=True status=200 depth=0
  - `https://books.toscrape.com/catalogue/category/books/mystery_3/index.html` success=True status=200 depth=0
  - `https://books.toscrape.com/catalogue/category/books/travel_2/index.html` success=True status=200 depth=0

## Experiment 2 — resume_state dict shape

### 2a. minimal correct: {"pending": [{url, parent_url}]}, no other keys
- resume_state: `{'pending': [{'url': 'https://books.toscrape.com/catalogue/category/books/travel_2/index.html', 'parent_url': None}]}`
- results returned: 1
  - `https://books.toscrape.com/catalogue/category/books/travel_2/index.html` success=True status=200 depth=0

### 2b. wrong key: {"seed_urls": [...]} (dict truthy, "pending" missing)
- resume_state: `{'seed_urls': ['https://books.toscrape.com/catalogue/category/books/travel_2/index.html']}`
- results returned: 0

### 2c. empty dict: {} (falsy -> falls back to plain start_url crawl)
- resume_state: `{}`
- results returned: 1
  - `https://books.toscrape.com/index.html` success=True status=200 depth=0

## Experiment 3 — depth bookkeeping vs max_depth

### Variant A — depths={https://books.toscrape.com/catalogue/category/books/mystery_3/index.html: 2}, max_depth=2
- seed fetched: [{'url': 'https://books.toscrape.com/catalogue/category/books/mystery_3/index.html', 'success': True, 'status_code': 200, 'depth': 2}]
- children discovered (next BFS level size): 0
- expectation: next_depth=3 > max_depth=2 -> 0 children

### Variant B — depths omitted (defaults to 0), max_depth=2
- seed fetched: [{'url': 'https://books.toscrape.com/catalogue/category/books/mystery_3/index.html', 'success': True, 'status_code': 200, 'depth': 0}]
- children discovered (next BFS level size): 73
- sample assigned child depth: 1
- expectation: next_depth=1 <= max_depth=2 -> children discovered, each stamped depth=1

## Experiment 4 — FilterChain bypass for the injected seed

- seed: `https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html`
- filter: *philosophy_7* (reverse=True, so any URL containing philosophy_7 is rejected)
- seed fetch result: [{'url': 'https://books.toscrape.com/catalogue/category/books/philosophy_7/index.html', 'success': True, 'status_code': 200, 'depth': 0}]
- children discovered: 62
- philosophy_7 self-link present among children: False
- filter_chain.stats: total=63 passed=62 rejected=1
- expectation: seed fetched despite matching the blocking pattern (seeds bypass can_process_url entirely); the SAME URL, rediscovered as a child via the sidebar's self-link, gets rejected by the filter chain (rejected count >= 1).

