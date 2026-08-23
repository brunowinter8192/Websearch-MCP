#!/usr/bin/env python3
"""
clean.py — URL-spanning cleanup of raw scraped markdown for RAG indexing.

Reads raw .md files from a 02_raw_data/<ts>/ directory, applies cleanup patterns,
writes cleaned versions to dev/scrape_pipeline/03_cleanup/cleaned_data/<ts>/.

Patterns are URL-spanning heuristics — NOT site-specific. Each pattern is documented
inline with the URL where it was first discovered. New patterns are added as we
encounter new chrome variants while iterating through the raw output set.

Usage:
    ./venv/bin/python dev/scrape_pipeline/03_cleanup/clean.py
    ./venv/bin/python dev/scrape_pipeline/03_cleanup/clean.py --input dev/scrape_pipeline/02_raw_data/<ts>/
"""
# INFRASTRUCTURE
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DIR_DEFAULT = PROJECT_ROOT / "dev" / "scrape_pipeline" / "02_raw_data"
CLEANED_DIR_BASE = PROJECT_ROOT / "dev" / "scrape_pipeline" / "03_cleanup" / "cleaned_data"

MIN_CONTENT_BYTES = 500  # skip near-empty raw files (PDFs etc.)


# ===================== ORCHESTRATOR =====================

def cleanup_workflow(input_dir: Path, output_dir: Path) -> None:
    raw_files = sorted(p for p in input_dir.glob("*.md") if p.name != "02_raw_report.md")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"clean.py — input: {input_dir}", file=sys.stderr)
    print(f"           output: {output_dir}", file=sys.stderr)
    print(f"Files: {len(raw_files)}\n", file=sys.stderr)

    rows = []
    for f in raw_files:
        raw = f.read_text(encoding="utf-8")
        raw_size = len(raw)

        if raw_size < MIN_CONTENT_BYTES:
            rows.append((f.name, raw_size, 0, "skipped: near-empty"))
            print(f"  SKIP  {f.name:80s}  raw={raw_size}B (near-empty)", file=sys.stderr)
            continue

        cleaned = clean_markdown(raw)
        out_path = output_dir / f.name
        out_path.write_text(cleaned, encoding="utf-8")

        delta = raw_size - len(cleaned)
        pct = 100 * delta / raw_size
        rows.append((f.name, raw_size, len(cleaned), f"{delta:,}B ({pct:.1f}%) stripped"))
        print(f"  OK    {f.name:80s}  raw={raw_size:>7,}  out={len(cleaned):>7,}  -{pct:5.1f}%", file=sys.stderr)

    write_summary(output_dir, rows)


# ===================== CLEANUP PIPELINE =====================

def clean_markdown(text: str) -> str:
    """Apply all cleanup patterns in order. Site-specific strips run before
    generic ones so they can establish the right content anchor."""
    text = strip_hn_top_nav(text)          # site-specific: HN tables
    text = strip_github_chrome(text)        # site-specific: github heavy nav
    text = strip_pre_h1_chrome(text)        # generic: chrome before title h1
    text = strip_pre_content_chrome(text)   # fallback: when no h1 exists
    text = strip_skip_links(text)
    text = strip_sphinx_anchors(text)
    text = strip_tail_chrome(text)
    text = collapse_blank_lines(text)
    return text


# ----- Pattern: GitHub chrome strip (site-specific) -----
# Discovered on: github.com/adbar/trafilatura/issues/25
# GitHub issue/PR pages prefix the actual content with ~150 lines of nav, search,
# sponsor, repo navigation, branch/file browsers. The issue/PR TITLE appears as
# `# <text> #<N>` where N is the issue/PR number visible in the source URL.
# Strategy: detect github URL, extract issue/PR number from URL path,
# find matching `^# .+ #<N>` line, strip everything before it.
GITHUB_SOURCE_RE = re.compile(
    r"^<!-- source: https?://github\.com/[^/]+/[^/]+/(?:issues|pull)/(\d+)",
    re.MULTILINE,
)

def strip_github_chrome(text: str) -> str:
    src = SOURCE_RE.search(text)
    gh = GITHUB_SOURCE_RE.search(text)
    if not (src and gh):
        return text
    issue_n = gh.group(1)
    # Match issue/PR title line: `# <text> #<N>` (allow extra whitespace after #)
    title_re = re.compile(rf"^# +.+ #{issue_n}\s*$", re.MULTILINE)
    m = title_re.search(text)
    if not m or m.start() <= src.end():
        return text
    return text[:src.end()] + "\n\n" + text[m.start():]


# ----- Pattern 1: Pre-H1 chrome (smart title h1 detection) -----
# Discovered on: seirdy.one (simple), github.com (cluster of chrome h1s)
# Generic: between <!-- source --> and the title-h1 sits navigation chrome.
# Heuristic: the TITLE h1 is the first h1 followed by >= MIN_TITLE_GAP lines of
# substantive content (NOT just another chrome-h1 within a few lines).
# Falls back to first h1 if clustering doesn't reveal a clear title.
SOURCE_RE = re.compile(r"^<!-- source: .* -->\s*$", re.MULTILINE)
# H1: single hash + 1+ spaces + non-space char. Allows `# Title` and `#  Title`
# variants (some pages render with double-space).
H1_RE = re.compile(r"^# +\S", re.MULTILINE)
MIN_TITLE_PROSE_CHARS = 200

def gap_substantive_chars(gap: str) -> int:
    """Count chars of substantive prose in `gap` text — excluding link-only lines,
    table rows, headings, and short labels. Markdown link-text counts as prose."""
    total = 0
    for line in gap.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|"):
            continue
        # Pure-link line (e.g. "* [Foo](bar)") = chrome, skip
        if re.match(r"^\s*[\*\-]?\s*\[[^\]]*\]\([^)]*\)\s*$", s):
            continue
        # Strip markdown link wrappers — keep link text as prose
        prose = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        prose = re.sub(r"[\*\_\`\!]", "", prose)
        if len(prose.strip()) > 60:
            total += len(prose.strip())
    return total

def find_title_h1(text: str) -> int:
    """Return position of the title h1 (or -1 if none).
    Heuristic: first h1 with >= MIN_TITLE_PROSE_CHARS of substantive prose in
    the gap to the next h1 (or end of document). Falls back to first h1."""
    h1_positions = [m.start() for m in H1_RE.finditer(text)]
    if not h1_positions:
        return -1
    for i, pos in enumerate(h1_positions):
        next_pos = h1_positions[i + 1] if i + 1 < len(h1_positions) else len(text)
        if gap_substantive_chars(text[pos:next_pos]) >= MIN_TITLE_PROSE_CHARS:
            return pos
    return h1_positions[0]  # fallback: first h1

def strip_pre_h1_chrome(text: str) -> str:
    src = SOURCE_RE.search(text)
    title_pos = find_title_h1(text)
    if not src or title_pos == -1 or title_pos <= src.end():
        return text
    return text[:src.end()] + "\n\n" + text[title_pos:]


# ----- Pattern 1b: No-H1 fallback — strip top-nav until first prose -----
# Discovered on: adrien.barbaresi.eu, ACL Anthology (doi.org/v1/...)
# When the doc has no `# ` h1 at all, we can't anchor on it. Fallback:
# strip leading lines that look like pure-link nav until we hit a substantive
# prose line (>60 chars, not link-only) or a heading.
NAV_LINE_RE = re.compile(r"^\s*[\*\-]?\s*\[[^\]]*\]\([^)]*\)\s*$")
GENERIC_NAV_PHRASES = re.compile(r"^\s*(Toggle navigation|Menu|Search this site)\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6} +\S")  # h1-h6 with 1+ spaces after hashes

def visible_text_len(s: str) -> int:
    """Length of visible prose text after stripping markdown link/image wrappers
    and bare URLs. Robust against nested image-in-link markdown like
    `[![ACL Logo](url)ACL Anthology](url2)`."""
    # Strip image-in-link composite wrappers (image inside a link)
    s = re.sub(r"\[!\[[^\]]*\]\([^)]*\)([^\]]*)\]\([^)]*\)", r"\1", s)
    # Strip standalone images
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    # Strip link wrappers, keep just text content
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    # Strip bare URLs
    s = re.sub(r"https?://\S+", "", s)
    # Strip markdown emphasis / code chars
    s = re.sub(r"[\*\_\`]", "", s)
    return len(s.strip())

def is_substantive_line(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("<!--"):
        return False
    if HEADING_RE.match(s):
        return True
    if NAV_LINE_RE.match(s):
        return False
    if GENERIC_NAV_PHRASES.match(s):
        return False
    return visible_text_len(s) > 60

def strip_pre_content_chrome(text: str) -> str:
    if H1_RE.search(text):
        return text  # already handled by Pattern 1
    src = SOURCE_RE.search(text)
    if not src:
        return text
    after = text[src.end():]
    lines = after.split("\n")
    skip_count = 0
    for i, line in enumerate(lines):
        if is_substantive_line(line):
            skip_count = i
            break
    else:
        return text  # no substantive line found, leave alone
    return text[:src.end()] + "\n\n" + "\n".join(lines[skip_count:])


# ----- Pattern 2: Skip-to-content links anywhere -----
# Discovered on: seirdy.one (Skip to content)
SKIP_LINK_RE = re.compile(
    r"^\s*\[\s*Skip to [^\]]+\]\([^)]+\)\s*$",
    re.MULTILINE | re.IGNORECASE,
)

def strip_skip_links(text: str) -> str:
    return SKIP_LINK_RE.sub("", text)


# ----- Pattern 3: Sphinx/Furo permalink-anchors next to headings -----
# Discovered on: trafilatura.readthedocs.io
# Pattern: `[#](url "Link to this heading")` and `[¶](url "Permalink to ...")`
# These are anchor links Sphinx adds next to each heading — pure DOM noise.
SPHINX_ANCHOR_RE = re.compile(
    r'\[(#|¶|\xb6)\]\([^)]+\s+"(?:Link to this heading|Permalink[^"]*)"\)',
)

def strip_sphinx_anchors(text: str) -> str:
    return SPHINX_ANCHOR_RE.sub("", text)


# ----- Pattern 4: Tail chrome -----
# Discovered on: seirdy.one (Continue reading), expanded for Webmention/Comments
# Generic: standardized post-content sections that delimit footer chrome.
TAIL_MARKERS = [
    re.compile(r"^## Continue reading\s*$", re.MULTILINE),
    re.compile(r"^## Related posts?\s*$", re.MULTILINE),
    re.compile(r"^## Related articles?\s*$", re.MULTILINE),
    re.compile(r"^## Comments\s*$", re.MULTILINE),
    re.compile(r"^## Webmentions?\s*$", re.MULTILINE),
    re.compile(r"^## Replies\s*$", re.MULTILINE),
    re.compile(r"^You are here:\s*$", re.MULTILINE),
    re.compile(r"^\s*Copyright\s+\d{4}", re.MULTILINE),
]

def strip_tail_chrome(text: str) -> str:
    earliest = len(text)
    for pat in TAIL_MARKERS:
        m = pat.search(text)
        if m and m.start() < earliest:
            earliest = m.start()
    return text[:earliest].rstrip() + "\n"


# ----- Pattern 5: HN top nav strip -----
# Discovered on: news.ycombinator.com
# HN renders entire page as nested markdown tables. The first table-row block
# is the global nav (Hacker News logo + new/past/comments/ask/show/jobs/submit/login).
# Story content begins at the row containing the story title link.
# Strategy: detect news.ycombinator.com source URL, find first line containing
# the HN nav signature, then find the story-title-row (heuristic: row with a
# link AND points label + comments link) and strip everything before it.
HN_SOURCE_RE = re.compile(r"^<!-- source: https?://news\.ycombinator\.com/", re.MULTILINE)
HN_NAV_SIG = re.compile(r"\[Hacker News\]\(https://news\.ycombinator\.com/news\)")
# vote?id= link is universal — present on both story rows and comment-permalink rows
HN_STORY_ROW = re.compile(r"\(https://news\.ycombinator\.com/vote\?id=\d+", re.MULTILINE)

def strip_hn_top_nav(text: str) -> str:
    if not HN_SOURCE_RE.search(text):
        return text
    src = SOURCE_RE.search(text)
    nav_match = HN_NAV_SIG.search(text)
    story_match = HN_STORY_ROW.search(text)
    if not (src and nav_match and story_match):
        return text
    # Find start of the line containing the story-row marker
    line_start = text.rfind("\n", 0, story_match.start()) + 1
    return text[:src.end()] + "\n\n" + text[line_start:]


# ----- Pattern 6: Collapse excessive blank lines -----
BLANK_LINES_RE = re.compile(r"\n{4,}")

def collapse_blank_lines(text: str) -> str:
    return BLANK_LINES_RE.sub("\n\n\n", text)


# ===================== REPORT =====================

def write_summary(output_dir: Path, rows: list) -> None:
    lines = [
        "# Cleanup Run Summary",
        "",
        f"**Output:** `{output_dir}`",
        f"**Files:** {len(rows)}",
        "",
        "| File | Raw bytes | Cleaned bytes | Delta |",
        "|------|-----------|---------------|-------|",
    ]
    for name, raw, cleaned, note in rows:
        short = name[:60] + ("…" if len(name) > 60 else "")
        lines.append(f"| {short} | {raw:,} | {cleaned:,} | {note} |")

    (output_dir / "_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ===================== CLI =====================

def find_latest_raw_dir() -> Path:
    candidates = sorted(p for p in RAW_DIR_DEFAULT.iterdir() if p.is_dir())
    if not candidates:
        raise SystemExit(f"No subdirs in {RAW_DIR_DEFAULT}")
    return candidates[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to raw outputs dir (default: latest in 02_raw_data/)")
    parser.add_argument("--output", help="Output dir (default: 03_cleanup/cleaned_data/<ts>/)")
    args = parser.parse_args()

    input_dir = Path(args.input) if args.input else find_latest_raw_dir()
    if args.output:
        output_dir = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = CLEANED_DIR_BASE / ts

    cleanup_workflow(input_dir, output_dir)


if __name__ == "__main__":
    main()
