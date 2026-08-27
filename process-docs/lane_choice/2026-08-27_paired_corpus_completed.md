# Paired lane corpus completed, plus the external grounding for the coming scorer (2026-08-27)

Continues the `lane_choice` area. The paired-data backfill started 2026-08-25 was finished in one
uninterrupted run; this entry records the completed corpus, what its byte distribution shows, one
previously undocumented camoufox output class the corpus surfaced, and the implementation-level
grounding read for the scorer that has still not been built. Orchestrator-side entry — the backfill
is pure execution of an existing dev script, no code changed this session.

## The run

`./venv/bin/python dev/lane_choice/01_backfill_pairs.py`, invoked directly rather than through the
`02_focus_poll_smoke.py` wrapper: that wrapper exists only for the focus-steal instrumentation, and
the question it served was closed 2026-08-27 with the watchdog removal (`process-docs/camoufox_lane/`).
For pure data generation the direct call is the shorter path.

Result: 1198.9s wall (~20 min), resume state 124 → 224 entries, i.e. 112 distinct non-PDF URLs × 2
lanes. 111 URLs have `outcome=ok` on BOTH lanes. Every record's content sidecar is present on disk
(210+ files, zero missing), so the whole corpus is available for offline scoring without re-scraping.

The target set is NOT fixed: the script enumerates distinct URLs from the live production
`scrape_log.jsonl`, which grew from 106 to 112 URLs between 2026-08-25 and 2026-08-27 through
ordinary production use. A backfill "remainder" count is therefore only valid for the moment it was
computed.

The one URL failing on both lanes is unchanged from the 2026-08-25 run: `tedi-shop.com`'s search URL
(`/de-de/search/?q=duschtuch`), chromium `empty`, camoufox `exception` — reproduced, and itself a
data point about a page shape neither lane handles.

## What the byte distribution shows

Across the 111 both-ok pairs, the camoufox/chromium `bytes_returned` ratio has a median of 3.36.
That factor is structural, not quality: chromium's stored output is post-`PruningContentFilter`
(`mode=filtered`), camoufox's is unfiltered markdown (`mode=markdown`). An absolute byte comparison
across lanes is therefore meaningless without normalising against this baseline — the corpus now
quantifies what the 2026-08-25 entry argued qualitatively.

Three previously documented failure-band cases reproduced in fresh records:

- `terminland.de/hiv-sti-beratung-ffm/` — chromium 38 bytes, camoufox 2048, both HTTP 200.
- `idealo.de`'s `ProductCategory` page — chromium 367 bytes at HTTP 403, camoufox 138 bytes at
  HTTP 200. Both lanes thin, neither useful; the status codes contradict each other.
- `olymp.com/de/de/hemden` — the reverse direction: chromium 788 bytes at HTTP 200, camoufox 48
  bytes at HTTP 403. Only one pair in the corpus has chromium more than 3× camoufox.

## New: multi-megabyte camoufox outputs that the raw-HTML flag does not catch

Six camoufox outputs exceed 3 MB, topping out at 52,457,029 chars for a single
`josephjoseph.com` blog post (chromium returned 16,996 bytes for the same URL). Composition, read
directly from the sidecars:

- `ikea.com` (14.5 MB): markdown image links, the same product images repeated dozens of times.
- `josephjoseph.com` (52 MB): 553,334 lines but only 5,493 distinct non-empty ones — `</div>` alone
  appears 23,436 times, `}` 21,042 times, `</svg>` 10,332 times, i.e. inline script/style/svg residue.

Measured across the corpus: 16 of 111 camoufox outputs carry >2% closing-HTML-tag characters (worst
5.2%, `guenstiger.de`), while chromium's median for the same measure is 0.0000.

The camoufox record's own guard fields do not flag any of this: all 115 camoufox records have
`content_is_raw_html: false` and `markdown_conversion_error: null`. crawl4ai's markdown generator
reported success and passed HTML through as legal inline markdown. Any lane-choice signal must
therefore derive this from the CONTENT, not from the existing flags.

## Comparison basis: product vs product, settled

The scorer compares what each lane actually delivers — chromium's filtered markdown against
camoufox's raw markdown — not a reconstructed raw-vs-raw pair. Reasoning: the agent chooses between
exactly these two delivered outputs, so a higher link share in the camoufox output is a true property
of that output, not an artefact to correct for. Raw-vs-raw is also not available without a code
change: chromium's raw markdown is never persisted, only its size (`bytes_raw_markdown`).

The residual risk of a single density number is that it conflates two questions — did the lane
acquire the real page, and how clean is the lane's own post-processing. The idealo/terminland band is
exactly where those two come apart. Kohlschütter-style per-block classification addresses this
without touching the data basis: nav chrome, image-link farms and script residue fall out as
boilerplate in either lane's output, and what remains comparable is the surviving content volume per
lane. Unverified as of this entry — it is the hypothesis the next milestone tests on this corpus.

## External grounding, read at implementation level

The 2026-08-25 entry recorded the papers (Kohlschütter WSDM 2010 et al., indexed into
`websearch-reference`). This session read how two production extractors actually implement those
features:

- **jusText** (`justext/paragraph.py`, `justext/core.py`): link density = characters inside links /
  characters in the paragraph; stopword density = stopword count / word count. Both per paragraph,
  never per document. Defaults: `MAX_LINK_DENSITY=0.2` (a paragraph above it is classified `bad`
  before any other test), `STOPWORDS_LOW=0.30`, `STOPWORDS_HIGH=0.32`, `LENGTH_LOW=70`,
  `LENGTH_HIGH=200` characters.
- **trafilatura** (`trafilatura/htmlprocessing.py`): also character-ratio based, but thresholds are
  size-dependent — small elements fall at 0.8 link-char ratio, large "link farms" at
  `LINK_FARM_RATIO=0.9`, tables at 0.8 below 1000 chars and 0.5 above, with element-length gates of
  30/60/100/300 chars deciding which test applies at all.

The three sources give three different numbers for nominally the same feature — 0.33 (Kohlschütter),
0.2 (jusText), 0.8-0.9 (trafilatura) — because the unit and the denominator differ in each. No
threshold can be copied into this project; a block definition on markdown has to be fixed first and
the numbers derived on this corpus, consistent with the log-before-config methodology this project
applies elsewhere (`process-docs/scrape_pipeline/`).

Markdown makes the link measure cheaper than HTML rather than harder: link text is directly countable
from the `[text](url)` syntax, and a blank-line-separated block replaces the DOM node as the unit.
jusText's German (692 words) and English (503 words) stoplists were retrieved for the mixed-language
corpus.

Field practice, as a weak corroborating signal only (one low-engagement 2026-07 r/WebScrapingInsider
thread, partly vendor self-promotion): practitioners describe a content quality gate of text-density
ratio, minimum meaningful length, and a "did we get the article body or just nav+footer" structural
check, plus mapping known challenge-page signatures against response content rather than trusting
HTTP 200. The latter matches this project's existing 7-category garbage classifier.

## Open at entry time

- Threshold policy undecided: whether hard thresholds exist at all beyond the garbage-signature
  knock-outs, or whether every other signal is reported as a bare per-lane number.
- The scorer itself: block definition on markdown, signal implementation, calibration on this corpus.
- Summary format for the dual-fire response, and the dual-fire wiring in the ad-hoc path.
