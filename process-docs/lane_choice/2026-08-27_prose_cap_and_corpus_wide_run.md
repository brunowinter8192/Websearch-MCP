# A block-level PROSE test on top of CONTENT, and the metric run moved to the full 111-pair corpus (2026-08-27)

Continues the `lane_choice` area. The classifier from the earlier session (`04_lane_metrics.py`)
counted a single very long markdown line — embedded JSON, CSS, or markup arriving as one "block" —
as CONTENT with no upper bound on its word count. `zweidigital.de/team/`, a 404 page, scored 91%
CONTENT with a 5,521-word longest CONTENT block; `ikea.com`'s product page scored 98% with a
5,118-word longest block. No prose paragraph has that shape. This entry adds a PROSE test to
separate "classified CONTENT" from "looks like actual readable text", and moves the script's input
from the fixed 20-URL `/tmp/lane_pairs_20.json` file to the full corpus, built at runtime from the
production log.

## The PROSE test

A block counts as PROSE when it is CONTENT (the existing Algorithm 2 + heading-rule result), its
word count is at or under a length cap, and it contains at least one sentence-ending mark (`.`,
`!`, or `?`) anywhere in its visible text. The sentence-ending check alone already rejects most
markup/data blobs (a JSON array or a CSS ruleset frequently contains none of the three), and the
cap catches the cases that do contain one incidentally.

## Deriving the cap from the corpus, not inventing it

The cap needed a source that is itself already mostly prose, to avoid circularity (using
CONTENT-classified blocks from either lane to derive a CONTENT-quality threshold). Chromium's
stored output is post-`PruningContentFilter` (`mode=filtered` — see `2026-08-27_paired_corpus_completed.md`
for the mode distinction), i.e. already close to clean text before this script ever sees it, which
makes its raw block-word-count distribution the least circular proxy available in this project for
"what does a prose block's word count look like".

Measured over all 15,030 blocks (not just CONTENT-classified ones) across the 111 both-ok pairs'
chromium files:

| stat | value |
|---|---|
| median | 4 |
| p75 | 8 |
| p90 | 20 |
| p95 | 35 |
| p99 | 72 |
| p99.9 | 151 |
| max | 332 |

The shape is a single smooth, heavily right-skewed decay with no bimodal gap or knee: 65% of all
chromium blocks are 1-5 words (headers, nav items, list entries), and the share roughly halves
every doubling of length band up to the ~150-200 word range before tailing off completely at 332.
Nothing in that shape argues for a different mechanism (e.g. a natural cutoff at a visible gap) —
it is the ordinary long tail of line-based markdown blocks, so a percentile cutoff is the right
tool, as the task anticipated as the default case.

Cap chosen: **72 words, the 99th percentile** (`statistics.quantiles(..., n=100,
method="inclusive")[98]`, computed fresh on every run, never hardcoded — a future corpus growth or
composition shift changes the cap automatically). p99 was picked over p95 (35, too tight — genuine
multi-sentence paragraphs in the 40-70 word range are common and would be misclassified as
non-prose for pure length) and over p99.9/max (151/332, too loose relative to how conservative "a
high percentile" should read) as the balance point: it excludes exactly the top 1% tail while
keeping every realistic single-paragraph block. Either way, 72 sits roughly two orders of magnitude
below the pathological 5,000+-word blocks that motivated this work, so the exact percentile choice
inside the 95-99.9 band was never going to change which blocks the cap actually excludes.

## What the cap excludes, aggregated over both lanes

Chromium: 149 blocks, 15,628 words excluded — consistent with "roughly the top 1% of ~15,030
blocks" as a sanity check on the derivation itself. Camoufox: 4,111 blocks, 2,083,481 words
excluded — the same top-1%-of-chromium cap applied to camoufox's unfiltered output removes vastly
more, which is exactly the asymmetry this whole test exists to surface, not an artifact of the cap
being lane-specific (it is derived from chromium alone and applied identically to both).

## Moving off the fixed 20-URL file to the full production corpus

`load_pairs(/tmp/lane_pairs_20.json)` was replaced with `collect_pairs_from_scrape_log()`, which
reads the production `scrape_log.jsonl` directly (hardcoded absolute path into the MAIN repo, the
same convention `01_backfill_pairs.py` already uses and for the same reason — worktrees have their
own separate, gitignored `src/logs/`), takes the freshest `outcome: ok` + `content_path` record per
`(url, engine)`, and pairs every URL present on both lanes. This produced 111 pairs (unchanged from
the count established in `2026-08-27_paired_corpus_completed.md`) with no re-scraping — every file
already existed on disk. Full run: 3.4-3.5s wall, reading ~197 MB of camoufox content plus ~1.3 MB
of chromium content once each.

## The chromium-zero-CONTENT / camoufox-PROSE-rescue counts

8 pairs have zero chromium CONTENT blocks. Of those, camoufox has at least one PROSE block in 7:
`qis.server.uni-frankfurt.de`, both `praxis-am-marbachweg.de` URL variants plus its
`/aktuelles/neue-patienten.html` page, `zweidigital.de/team/`, and both `terminland.de` URLs. The
one exception — camoufox has zero PROSE blocks too — is `galeria.de`'s search-result page, meaning
neither lane produced anything answering the PROSE test there. Full numbers, per-URL lines, and the
complete table live in the generated report (`dev/lane_choice/md/`, latest timestamp), not
duplicated here in full — the report is the artifact this entry is about, not a replacement for it.
