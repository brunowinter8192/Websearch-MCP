# The shallow-feature metric has no edge over "always chromium" — measured against 20 read judgments (2026-08-27)

Continues the `lane_choice` area. Two independent passes were run over the SAME 20 paired
chromium/camoufox scrapes: one read both outputs per URL and recorded which it would rather have
received, the other implemented Kohlschütter WSDM 2010 Algorithm 2 on markdown and computed
per-lane metrics. Neither pass saw the other's output, and the reading pass was given no metric,
no thresholds and no paper. This entry records what happened when the two were held against each
other, and it is orchestrator-side: the comparison arithmetic below was done outside both passes.

## The sample

20 of the 111 both-lanes-ok pairs. Six were deliberately included because earlier entries in this
area name them as the documented failure band or as size outliers (terminland, idealo, olymp,
zweidigital, ikea, bahn); the other fourteen were drawn at random with a fixed seed. The set
therefore over-represents hard cases on purpose and is not a random sample of the corpus.

## What the reading pass decided, and on what grounds

Tally over the 20: chromium 11, camoufox 3, equivalent 4, neither-usable 2.

The grounds matter more than the tally. In all 11 chromium verdicts the stated reason is the same:
both lanes carry the same substance, and camoufox carries much more non-substance alongside it —
mega-menus, cookie-consent declarations, inlined scripts, font-face blocks, lazy-load image grids.
Not one chromium verdict was given because chromium had MORE content. In 2 of the 3 camoufox
verdicts chromium had returned essentially nothing (terminland 229 bytes of a TLS boilerplate line;
praxis-am-marbachweg 290 bytes, the title only). The remaining camoufox verdict (olat) is the ONLY
case in the 20 where both lanes carried real substance and camoufox carried more of it — a guest-
access link that chromium's filter had dropped. The 2 neither-usable cases are both anti-bot
challenge pages (Akamai, Cloudflare) where the lane choice changed nothing.

camoufox did carry extra material in 13 of the 20 pairs, often by orders of magnitude. The reading
pass named that extra explicitly eight times: subcategory tiles, navigation trees, footer links,
enumerated review lists. Substantive for the page's own question exactly once.

## The metric numbers, and the result that matters

Per lane per file the classifier produced: blocks total and CONTENT, words total and in CONTENT
blocks, the CONTENT percentage, overall link density, and the longest CONTENT block. Full report:
`dev/lane_choice/md/04_lane_metrics_report_20260827T171744Z.md`.

Held against the 14 decisive judgments:

- CONTENT percentage agrees with the reading pass 11 of 14 (79%).
- Absolute CONTENT words agrees 5 of 14 (36%).
- A constant predictor that always says "chromium" agrees 11 of 14 (79%).

The percentage metric therefore delivers ZERO edge over the trivial constant, and the absolute word
count is 43 points WORSE than it. That is the central result of this entry.

Absolute words fails for a structural reason: in six pairs the camoufox/chromium content-word ratio
runs between 20 and 614 (hemden.de: 529,098 vs 862 words, on a 404 fallback page both lanes render
identically). Every one of those six was judged chromium.

## Why the percentage cannot be trusted either, despite matching the constant

The two percentages are not measurements of the same thing. Chromium's stored output is already
post-`PruningContentFilter`, so boilerplate was removed before the classifier ever saw it; camoufox's
is unfiltered. Chromium wins the percentage in 16 of 20 pairs largely by construction, not by
quality. Where the metric and the reading pass diverge, the divergence is instructive:

- zweidigital (chromium 0%, camoufox 91%) and ikea (chromium 63%, camoufox 98%): the classifier
  counts embedded JSON/CSS/markup as words. The longest CONTENT block is 5,521 and 5,118 words
  respectively — no prose block has that shape. Both were judged chromium.
- olat (chromium 99%, camoufox 78%): camoufox was judged better on the strength of ONE extra link.
  No density measure can price a single link.

Two further cases show why knock-out signatures are not optional: idealo's chromium output scores
100% CONTENT on 38 words that are an HTTP 403 error message, and olymp's scores 98% on a Cloudflare
block page. The project already owns a 7-category garbage classifier (`src/scraper/`), unused by
this comparison.

Blind spots of the implementation as built: a line consisting only of a markdown image yields zero
tokens and never becomes a block at all, so image farms are invisible to both the numerator and the
denominator; and a single line of embedded JSON counts its tokens as content words in full.

## The rule the judgments actually imply

The reading pass's own reasons collapse into one asymmetric rule: read chromium, unless chromium's
output is insufficient. On these 20 that rule matches 13 of 14 decisive judgments (93%), the single
miss being olat. It needs no comparison between lanes for its trigger — "is chromium thin" is
answerable on chromium alone — but it does need the dual-fire summary to resolve the trigger,
because thin chromium is an alarm rather than an answer: zweidigital's chromium output was 9 words
and still the better read, since the page itself was a genuine 404 and camoufox answered it with
3.3 MB of noise.

This rule was derived from the same 20 pairs it is scored on. It is a hypothesis, not a result. The
honest test is a fresh batch drawn from the 91 pairs neither pass has seen, judged blind before the
rule is applied.

## A confound found along the way

Spot-checking three of the twenty judgments against the raw files (zweidigital and olat verified as
described; the reading pass's verdicts held) surfaced something the reading pass had described
imprecisely: on olat the two lanes did not return the same page in two languages, they returned
different language versions of it — chromium German, camoufox English. That turned out to be a real
configuration defect in the camoufox lane, recorded and fixed separately under
`process-docs/camoufox_lane/`. Until that fix, any content-overlap comparison between the two lanes
was measuring language difference as content loss on multilingual sites.

## On training a classifier of our own

Considered and deferred. Kohlschütter's tree is a pruned C4.8 trained on 72,662 hand-labelled
blocks; this project holds 222 files with hundreds of thousands of blocks and zero block-level
labels. Distilling labels from a model is a legitimate route to a deterministic runtime classifier,
but the target variable here is the lane choice, and of that there is exactly one label per URL —
111 in total, enough to validate a one-threshold rule and nowhere near enough to train a tree. The
corpus is also not a random sample of the web but of one user's own research, heavily weighted
toward German shops. Training is therefore only worth revisiting if the simple rule fails its
hold-out test.

## Open at entry time

- The hold-out batch: 20 fresh pairs, blind reading judgments, then the rule scored against them.
- Threshold policy: what "insufficient chromium output" means numerically, and whether anything
  beyond the garbage-signature knock-outs needs a threshold at all.
- The summary format for the dual-fire response, and its wiring into the ad-hoc path.
- The labelling inconsistency to resolve before any scoring target is fixed: the reading pass used
  "equivalent" both for pages where both lanes fully answer and for pages where both fail
  identically, while reserving "neither-usable" for anti-bot blocks.
