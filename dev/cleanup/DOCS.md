# Cleanup Scripts

One-shot scripts for removing UI chrome, navigation, and formatting artifacts from website-crawled markdown files before RAG indexing. Each script targets a specific domain or collection. Files are overwritten in-place; `<!-- source: URL -->` headers are preserved.

Run from project root with:
```bash
./venv/bin/python dev/cleanup/<script>.py
```

## clean_web_searxng.py

**Purpose:** Remove navigation chrome and formatting artifacts from the `searxng` RAG collection (2076 files across 12 domain prefixes: searxng, crawl4ai, playwright, tor, anthropic, trafilatura, onetrust, cookieyes, web, paper, sitemaps, cookiebot).
**Input:** `*.md` files in `RAG/data/documents/searxng/` — all domain prefixes handled in one pass with per-domain header/footer strategies.
**Output:** Files overwritten in-place with headers, footers, and inline artifacts removed.

## clean_web_anthropic.py

**Purpose:** Fix formatting artifacts in Anthropic (platform.claude.com/docs) crawled pages.
**Input:** `anthropic__*.md` files in `RAG/data/documents/searxng/`.
**Output:** Files overwritten in-place. Fixes: excessive blank lines after source comment → 1 blank; broken headings (`## \n<text>` → `## <text>`); concatenated card navigation links at end of file removed.

## clean_web_cookieyes.py

**Purpose:** Remove UI chrome from cookieyes.com/documentation pages.
**Input:** `cookieyes__*.md` files in `RAG/data/documents/searxng/`.
**Output:** Files overwritten in-place. Removes: blank lines before first heading; "Search for:Search Button" line; breadcrumb navigation; "Was this article helpful?" block; G2 Rating Badges; newsletter subscribe block; "Related articles" link list.

## clean_web_onetrust.py

**Purpose:** Remove UI chrome from developer.onetrust.com pages.
**Input:** `onetrust__*.md` files in `RAG/data/documents/searxng/`.
**Output:** Files overwritten in-place. Removes: leading blank lines before first heading; split heading artifacts (`# ` alone on a line); empty anchor links; footer navigation (Prev/Next links after `* * *` separator); trailing `* * *` separators; pagination markers (`N of M[](URL)` lines).

## clean_web_Playwright.py

**Purpose:** Remove Docusaurus chrome from Playwright docs pages (playwright.dev).
**Input:** `*.md` files in `RAG/data/documents/Playwright/`.
**Output:** Files overwritten in-place. Content sandwiched between first `# ` heading and first `[Previous ` / `[Next ` pagination link. Removes full sidebar nav, breadcrumb, "On this page" label, and footer sections (Learn/Community/More + copyright).

## clean_web_rag_docs.py

**Purpose:** Remove site-generator chrome from Playwright, Crawl4AI, and Trafilatura docs in the RAG collection (`playwright__*`, `crawl4ai__*`, `trafilatura__*` files).
**Input:** Files matching the three prefixes in `RAG/data/documents/searxng/`.
**Output:** Files overwritten in-place. Per-domain fixes: Playwright — heading anchors; Crawl4AI — standalone `Copy` UI lines after code blocks, `#### On this page` / `> Feedback` footer blocks; Trafilatura — heading anchors, `[ previous X ][ next Y ]` nav lines, `On this page` TOC blocks.

## clean_web_tor.py

**Purpose:** Remove navigation chrome and UI artifacts from support.torproject.org pages.
**Input:** `tor__*.md` files in `RAG/data/documents/searxng/`.
**Output:** Files overwritten in-place. Removes: footer block starting at Jobs link (social media links, Copyleft notice, trademark, onion image); "View for:" UI widget; "Expand all Collapse all" widget; leading blank lines before first heading (reduced to max 1).
