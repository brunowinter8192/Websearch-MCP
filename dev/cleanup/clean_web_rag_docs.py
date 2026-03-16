"""
Cleanup script for RAG docs collection: playwright__, crawl4ai__, trafilatura__ files.

Three domains, three site generators, one script.

PLAYWRIGHT (Docusaurus) — playwright__*.md
  - Files are mostly clean (header/footer already absent from crawl)
  - Inline noise: heading anchors `[​](URL "Direct link to X")`
  - Rare footer: `[Previous ` / `[Next ` pagination lines

CRAWL4AI (MkDocs) — crawl4ai__*.md
  - Code block button: standalone `Copy` lines after closing ``` (UI artifact)
  - Footer block: starts at `#### On this page` or `> Feedback` line
    then: TOC links, `xClose`, `Type to start searching`, `[ Ask AI ]` line

TRAFILATURA (Sphinx/ReadTheDocs) — trafilatura__*.md
  - Heading anchors: `[#](URL "Link to this heading")`
  - Footer: `[ previous X ][ next Y ]` nav line, then `On this page` TOC block,
    then `### This Page` / Show Source link

Preserves: <!-- source: URL --> comment at top of each file.
Overwrites files in-place.
"""

from pathlib import Path
import re

INPUT_DIR = Path("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/searxng")

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def extract_source_comment(lines: list[str]) -> str:
    for line in lines[:4]:
        if line.startswith("<!-- source:"):
            return line.rstrip()
    return ""


def find_content_start(lines: list[str]) -> int:
    """Index of first `# ` or `## ` heading (for files that only have h2+)."""
    for i, line in enumerate(lines):
        if line.startswith("# ") or line.startswith("## "):
            return i
    return -1


_CRAWL4AI_NAV_MARKER_RE = re.compile(r'^\[Crawl4AI Documentation')


def find_crawl4ai_content_start(lines: list[str]) -> int:
    """
    For crawl4ai files with full MkDocs nav header.

    Pattern: source comment(s), then [Crawl4AI Documentation...] nav block,
    then optional * * * hr and TOC list, then actual heading (## or #).

    Strategy:
    1. Find nav marker.
    2. Scan for first heading (# or ##) after nav marker.
    3. If no heading but nav was seen, scan forward from nav marker for first
       non-nav content line (not a list item, not empty, not a link-only line).
    """
    nav_seen = False
    nav_start_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if _CRAWL4AI_NAV_MARKER_RE.match(stripped):
            nav_seen = True
            nav_start_idx = i
        if nav_seen and (line.startswith("# ") or line.startswith("## ")):
            return i

    # Nav was seen but no heading found — find first substantive content line
    # after the nav block (nav block is all list items and link lines)
    if nav_seen and nav_start_idx >= 0:
        for i in range(nav_start_idx + 1, len(lines)):
            stripped = lines[i].strip()
            # Skip: empty, list items (start with */-), link-only lines (start with [)
            # Also skip: "* * *" horizontal rules
            if not stripped:
                continue
            if stripped.startswith("*") or stripped.startswith("-") or stripped.startswith("["):
                continue
            if stripped == "×":  # MkDocs mobile close button
                continue
            return i

    # Fall back to normal heading search
    return find_content_start(lines)


def strip_trailing_blanks(lines: list[str]) -> list[str]:
    while lines and lines[-1].strip() == "":
        lines.pop()
    return lines


def assemble(source_comment: str, content_lines: list[str]) -> str:
    parts = []
    if source_comment:
        parts.append(source_comment + "\n\n")
    parts.append("".join(content_lines))
    result = "".join(parts)
    if not result.endswith("\n"):
        result += "\n"
    return result


# ---------------------------------------------------------------------------
# PLAYWRIGHT cleaner
# ---------------------------------------------------------------------------

# Heading anchor pattern: [​](URL "Direct link to ...")
# The ​ is a zero-width-space char (U+200B) that Docusaurus inserts
_PLAYWRIGHT_ANCHOR_RE = re.compile(r'\[​\]\([^)]*"Direct link to[^"]*"\)')


def clean_playwright(lines: list[str]) -> list[str]:
    """Remove heading anchor noise and optional footer navigation."""
    cleaned = []
    for line in lines:
        # Stop at prev/next pagination (rare footer)
        if re.match(r'^\[(?:Previous|Next)\b', line):
            break
        # Remove inline heading anchor noise
        line = _PLAYWRIGHT_ANCHOR_RE.sub("", line)
        cleaned.append(line)
    return strip_trailing_blanks(cleaned)


# ---------------------------------------------------------------------------
# CRAWL4AI cleaner
# ---------------------------------------------------------------------------

# `Copy` appears alone on a line after a closing ``` (MkDocs UI button artifact)
_COPY_LINE_RE = re.compile(r'^Copy\s*$')


def _is_crawl4ai_footer_start(line: str) -> bool:
    stripped = line.strip()
    # "#### On this page" TOC block
    if stripped.startswith("#### On this page"):
        return True
    # Feedback blockquote line
    if stripped.startswith("> Feedback"):
        return True
    # xClose / search UI
    if stripped in ("xClose", "Type to start searching"):
        return True
    # Ask AI link
    if stripped.startswith("[ Ask AI ]"):
        return True
    return False


def clean_crawl4ai(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        if _is_crawl4ai_footer_start(line):
            break
        # Drop standalone Copy lines (code block button artifact)
        if _COPY_LINE_RE.match(line):
            continue
        cleaned.append(line)
    return strip_trailing_blanks(cleaned)


# ---------------------------------------------------------------------------
# TRAFILATURA cleaner
# ---------------------------------------------------------------------------

# Heading anchor: [#](URL "Link to this heading")
_TRAFILATURA_ANCHOR_RE = re.compile(r'\[#\]\([^)]*"Link to this heading"\)')


def _is_trafilatura_footer_start(line: str) -> bool:
    stripped = line.strip()
    # [ previous X ][ next Y ] navigation bar
    if re.match(r'^\[ previous ', stripped) or re.match(r'^\[previous ', stripped):
        return True
    # "On this page" section (no heading prefix, just the label)
    if stripped == "On this page":
        return True
    # Sphinx "This Page" section
    if stripped == "### This Page":
        return True
    return False


def clean_trafilatura(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        if _is_trafilatura_footer_start(line):
            break
        # Remove heading anchor noise
        line = _TRAFILATURA_ANCHOR_RE.sub("", line)
        cleaned.append(line)
    return strip_trailing_blanks(cleaned)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def clean_file(path: Path) -> tuple[int, int]:
    """Clean one file in-place. Returns (chars_before, chars_after)."""
    text = path.read_text(encoding="utf-8")
    chars_before = len(text)

    lines = text.splitlines(keepends=True)
    source_comment = extract_source_comment(lines)

    name = path.name
    if name.startswith("playwright__"):
        domain_cleaner = clean_playwright
        content_start = find_content_start(lines)
    elif name.startswith("crawl4ai__"):
        domain_cleaner = clean_crawl4ai
        content_start = find_crawl4ai_content_start(lines)
    elif name.startswith("trafilatura__"):
        domain_cleaner = clean_trafilatura
        content_start = find_content_start(lines)
    else:
        # Unknown domain — leave untouched
        return chars_before, chars_before

    if content_start == -1:
        # No heading — apply domain cleaner to full content but keep source comment
        content_lines = lines
    else:
        content_lines = lines[content_start:]

    content_lines = domain_cleaner(content_lines)

    cleaned = assemble(source_comment, content_lines)
    path.write_text(cleaned, encoding="utf-8")

    return chars_before, len(cleaned)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    patterns = ["playwright__*.md", "crawl4ai__*.md", "trafilatura__*.md"]
    all_files = []
    for pattern in patterns:
        all_files.extend(sorted(INPUT_DIR.glob(pattern)))

    if not all_files:
        print(f"No matching files found in {INPUT_DIR}")
        return

    domain_stats: dict[str, list] = {
        "playwright": [0, 0, 0, 0],   # [files, before, after, changed]
        "crawl4ai":   [0, 0, 0, 0],
        "trafilatura":[0, 0, 0, 0],
    }

    for path in all_files:
        name = path.name
        if name.startswith("playwright__"):
            key = "playwright"
        elif name.startswith("crawl4ai__"):
            key = "crawl4ai"
        else:
            key = "trafilatura"

        before, after = clean_file(path)
        s = domain_stats[key]
        s[0] += 1
        s[1] += before
        s[2] += after
        if before != after:
            s[3] += 1

    total_before = sum(s[1] for s in domain_stats.values())
    total_after = sum(s[2] for s in domain_stats.values())
    reduction = (1 - total_after / total_before) * 100 if total_before else 0

    print("=" * 60)
    print(f"FILES PROCESSED: {len(all_files)} total")
    print()
    for domain, (n, before, after, changed) in domain_stats.items():
        dom_reduction = (1 - after / before) * 100 if before else 0
        print(f"  {domain}: {n} files, {changed} modified, "
              f"{before:,} → {after:,} chars ({dom_reduction:.1f}% reduction)")
    print()
    print(f"TOTAL chars before: {total_before:,}")
    print(f"TOTAL chars after:  {total_after:,}")
    print(f"TOTAL reduction:    {reduction:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
