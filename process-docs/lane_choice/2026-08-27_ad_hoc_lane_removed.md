# The Camoufox lane was removed from the ad-hoc path, and the dual-lane question closed with it (2026-08-27)

Continues the `lane_choice` area. This entry records the decision that ended the line of work the
area was opened for: on the ad-hoc single-URL path there is no longer a lane to choose, because
Camoufox was taken out of it. The decision was the user's, taken in chat after the measurement
entries in this area came back without an edge. It was implemented on 2026-08-27 but never written
down at the time — the reasoning survived only as a Gotcha bullet in `src/scraper/DOCS.md`, which
is the wrong home for a measurement series. The corpus numbers below were re-counted from the
production log on 2026-08-28 and are stated with that date, not with the decision's.

## What changed, and what deliberately did not

Two commits, both small on purpose:

- `cli.py` lost the `scrape_url_camoufox` subparser, its dispatch branch, and the
  `scrape_url_camoufox_workflow` import. The dispatcher went from 4 subcommands to 3.
- `skills/websearch-web-research/SKILL.md` lost the second row of its command table and the
  paragraph that framed the two lanes as a free per-call choice. The retry-the-other-lane
  instruction was replaced with reporting the failure plainly.

Untouched by design: `src/scraper/camoufox_scrape.py` itself, its calibrated launch config, and
`dev/tests/test_camoufox_scrape.py`, which still drives `scrape_url_camoufox_workflow` directly.
Also untouched is the batch capture pipeline's own Camoufox engine
(`src/crawler/pipe_scraper_acquisition.py`'s `_scrape_one_camoufox`), a separate consumer of
`try_scrape_camoufox` that this decision never covered. Reactivating the ad-hoc lane therefore
means re-adding an import and a subparser branch to `cli.py`, and nothing else.

## The evidence: the lane never once did the job it was added for

The Camoufox lane exists to get through anti-bot protection that Chromium cannot pass. The
production `scrape_log.jsonl` is the only place that claim can be checked, because both lanes write
into it with an `engine` discriminator.

Counted on 2026-08-28 over 319 records (204 chromium, 115 camoufox), covering 112 URLs that both
lanes have visited at least once:

- URLs where every chromium attempt failed and some camoufox attempt succeeded: **zero**.
- HTTP 403 on camoufox: 5 URLs (`frankfurt.de` twice, `anwalt.de`, `guenstiger.de`, `olymp.com`).
  On all five, chromium returned HTTP 200 on the same target.
- HTTP 403 on chromium: 2 URLs that camoufox also visited. On one (`idealo.de`) camoufox got a 200;
  the other (`sciencedirect.com`) camoufox never tried.

So the ledger reads five URLs where the stealth lane was blocked and the ordinary lane was not,
against one in the other direction. The founding justification has no supporting instance in this
corpus, and the measured direction is the reverse of it. The counts at decision time were 198
chromium records and 2 chromium 403s; the six chromium records and one 403 added since did not move
the finding.

The `idealo.de` case is worth naming, because it is the single instance in favour of the lane and it
is weaker than it looks: chromium's stored output there is 38 words of an HTTP 403 error page that
the content classifier scores at 100% CONTENT. The lane difference is real, the rescue is one page.

## Why the dual-fire redesign died with it

The plan this area was pursuing was to fire both lanes on every ad-hoc URL, return a per-lane
summary, and let the agent read the better one, with a deterministic shallow-feature scorer
supplying the signal. That plan needs two lanes on the ad-hoc path.

It had also already failed its own test. Held against 14 decisive read judgments, the CONTENT
percentage agreed 11 times, and a constant predictor that always answers "chromium" agreed 11 times
as well — zero edge, recorded in this area's metric-versus-judgment entry. Removing the lane and
keeping the scorer would have meant paying for a second browser launch per URL to reproduce an
answer that costs nothing to guess.

## What was lost, and what it would cost to get back

The paired corpus (111 both-lanes-ok pairs), the block classifier in `dev/lane_choice/`, and the 20
read judgments all remain on disk and stay valid as evidence. What no longer accumulates is fresh
paired data, because the ad-hoc path now only ever writes chromium records; camoufox records stopped
at 115. A future hold-out test of the "read chromium unless chromium is thin" rule therefore has to
draw from the frozen 111 pairs, or re-enable the lane first.

## Open at entry time

- The capture-and-index pipeline still offers `--engine camoufox`, unreviewed against this finding.
  Whether the same ledger holds at batch volume is a separate question, answerable from
  `pipe_scrape_log.jsonl`, which this entry did not touch.
- The hold-out test of the asymmetric rule stays unrun, and is now bounded by the frozen corpus.
- `dev/lane_choice/` keeps a hardcoded absolute path into the main repo's `src/logs/`, which is a
  worktree workaround rather than a decision, noted here so it is not mistaken for one.
