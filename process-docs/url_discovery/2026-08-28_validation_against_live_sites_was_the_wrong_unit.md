# Validating against live sites was the wrong unit, and it cost more than the implementation (2026-08-28)

Continues the `url_discovery` area. Four milestones of the discovery rebuild were built and merged
in one session (frontier pre-seeding probe, robots/sitemap feeders, navigation-tree feeder,
frontier wiring). Every one of them was verified by running against a live third-party website.
By the fourth, the verification was costing more than the implementation and had become the
thing blocking progress. This entry records what that cost concretely, what the missing
distinction was, and what replaces it.

The finding is about method, not about any of the four milestones' code. All four passed their
own checks and are merged.

## What it cost, in the session's own numbers

- The `docs.github.com/de/rest` benchmark run takes ~176s. A single instrumented reproduction of
  it took over 4½ minutes.
- That benchmark's final run reported 101 successful fetches against 682 failures out of 783
  attempts. The failures were GitHub's own rate limiting plus crawl4ai classifying the resulting
  168-byte HTTP 200 bodies as anti-bot blocks.
- By the end of the session the same IP was in a sustained rate-limit penalty, confirmed by
  isolated single-page checks still returning 429 long after the offending burst. The "after"
  measurement for the pacing fix could therefore not be taken at all, and that milestone's
  verification is recorded as partial for that reason alone.
- `coindesk.com`, named in a milestone brief as the App Router reference case, turned out to be
  behind a Vercel challenge returning 429. Two substitute hosts had to be found mid-milestone.
- Two `theblock.co` runs minutes apart returned 44,547 and 44,548 raw `<loc>` URLs. The site
  publishes continuously, so no two runs agree.
- The navigation-tree count on `docs.github.com` moved from a recorded 256 to a measured 254, and
  the version union from 305 to 304, because a documentation version was retired upstream between
  the two measurements.

Each of those individually looked like a local nuisance with a local fix. The pattern only became
visible once they were counted together.

## The distinction that was missing

Exploring and verifying were done with the same instrument.

Exploring means finding out what the world actually looks like, and there live sites are the only
possible source. This session's genuinely new knowledge all came from that: that the Next.js App
Router ships its payload as an RSC stream under `self.__next_f` rather than the older embedded
JSON blob; that the RSC stream is itself not uniform, carrying a structured page tree on one site
and only rendered DOM elements on another; that `coindesk.com` is challenge-gated. None of that
could have been learned from a fixture.

Verifying means checking that the code does what was claimed, and that requires ground truth. A
live site never supplies it. The `docs.github.com` benchmark compared every run against a figure
someone measured on 2026-05-31 — so when a run produced 304 instead of 305, nobody could say
whether the code was right and the site had changed, or the site was stable and the code was
wrong. Every such gap was closed by writing a paragraph explaining the drift. That is not
verification.

## What replaces it

A fixture site: a local HTTP server serving a documentation site this project wrote itself, whose
page count is a fact rather than a hope. To exercise what the four milestones actually do, it
needs a nested `<sitemapindex>` resolving to sub-sitemaps, a `robots.txt` carrying `Allow`,
`Disallow` and `Sitemap` directives, an embedded navigation payload with several versions where
some pages exist only in the oldest, orphan pages reachable by link alone, and switchable failure
modes — 429 after a set number of requests, and thin-body HTTP 200 responses.

The last of those is the point. The milestone that stalled, stalled on rate limiting and on
crawl4ai's anti-bot classification of thin responses. Against a fixture that serves both on
demand, the pacing fix would have had a before-and-after measurement in seconds instead of an
untakeable one.

Live sites then keep exactly one role: a single acceptance run at the end, to check that the
fixture's assumptions match the real web. Not a per-milestone cost.

## The brief's own share of it

The milestone briefs written for this work all said verification must be "measured output from
real runs, not a code review". The intent was that reading the diff does not count as checking
the code, and that part holds. But "real runs" was read — correctly — as runs against real
websites, when what was actually wanted was deterministic runs against known ground truth. The
wording chose the instrument when it should have named the property.

## Open at entry time

- The fixture site does not exist yet. Until it does, every remaining milestone in this area
  inherits the same problem.
- The pacing values now in `src/crawler/discovery.py` (`mean_delay=1.0`, `max_range=0.5`,
  `semaphore_count=8`) are this project's own measured chromium values carried over from
  `pipe_scraper`. Whether they are sufficient for an anti-bot-protected host is unverified — that
  is the measurement the rate-limit penalty prevented.
- One further gap was found and deliberately not fixed: traversal-discovered URLs carrying an
  explicit version segment are never run through the navigation-tree feeder's own version
  canonicalization, so they count as new when they are duplicates of a canonical seed.
