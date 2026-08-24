# pytest docs captured into websearch-reference (2026-08-24)

Permanent capture of `docs.pytest.org/en/stable/` into the `websearch-reference` RAG collection,
procured to ground the suite-relocation wiring decisions (same-day work in this area): rootdir
determination, the `pythonpath` ini option (rootdir does NOT touch `sys.path`), and
`norecursedirs` semantics (fnmatch on directory BASENAMES; setting it REPLACES the defaults).

## Funnel

- 256 docnames discovered via Sphinx `searchindex.js` (site has no sitemap, no `__NEXT_DATA__`).
- 187 auto-culled pre-scrape: `announce/release-*` per-version archive back to 2010 + license.
- 18 Opus-culled: marketing/meta/history/legacy pages (adopt, sponsor, talks, tidelift, contact,
  contributing, development_guide, changelog full-history page, funcarg_compare, yieldfixture,
  historical-notes, backwards-compatibility, proposals, recwarn) plus `reference/plugin_list`
  (a huge low-value plugin roster).
- 51 scraped, 0 errors, 51s; indexed as 934 chunks. Kept: full reference (customize, reference,
  fixtures, exit-codes), explanation (goodpractices, pythonpath), all how-tos, examples,
  getting-started, deprecations.

## Cleanup note

Furo-Sphinx theme was not one of the capture skill's documented shapes — a custom throwaway
cleaner stripped the header to the first `# ` heading and the footer from `Copyright ©`/nav
markers (repeated on-page TOC, EthicalAds block removed). Content windows spot-checked on 5+
files, coherent prose, zero cookie/paywall signatures.
