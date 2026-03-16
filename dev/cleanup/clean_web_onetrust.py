#!/usr/bin/env python3
"""
Cleanup script for developer.onetrust.com crawled markdown files.
Removes UI chrome while preserving content and <!-- source: URL --> comments.

Patterns removed:
1. Leading blank lines between <!-- source: --> and first heading
2. Split heading artifacts: "# " or "## " on its own line (heading text split across lines)
3. Empty anchor links: standalone [](https://developer.onetrust.com/...#anchor) lines
4. Footer navigation links: last * * * separator + [Prev](URL)[Next](URL) nav at end of file
5. Trailing double * * * separators (e.g. at end of changelog)
6. Pagination markers: "N of M[](URL)" lines
"""

import re
import sys
from pathlib import Path

INPUT_DIR = Path(__file__).parent.parent.parent.parent / "RAG" / "data" / "documents" / "searxng"
FILE_PATTERN = "onetrust__*.md"

# Regex for empty anchor links (standalone lines with only an anchor link)
RE_EMPTY_ANCHOR = re.compile(r'^\[\]\(https://[^\)]+\)\s*$')

# Regex for split heading lines: one or more # followed by nothing (or just spaces)
RE_SPLIT_HEADING = re.compile(r'^(#{1,6})\s*$')

# Regex for pagination marker: "N of M[](URL)" at start of line
RE_PAGINATION = re.compile(r'^\d+ of \d+\[\]\([^\)]*\)\s*$')

# Regex for footer nav links: lines that are ONLY [text](url) pairs (no other content)
# These appear after * * * at the end of documents
RE_NAV_LINK_LINE = re.compile(r'^(\[([^\]]+)\]\([^\)]+\))+\s*$')


def is_footer_nav_line(line: str) -> bool:
    """Check if line is a footer navigation link (prev/next page links)."""
    stripped = line.strip()
    if not stripped:
        return False
    return bool(RE_NAV_LINK_LINE.match(stripped))


def clean_content(text: str) -> str:
    lines = text.split('\n')
    result = []

    # --- Step 1: Preserve source comment, strip leading blanks before first heading ---
    source_line = None
    content_start = 0

    if lines and lines[0].startswith('<!-- source:'):
        source_line = lines[0]
        # Skip blank lines until first heading
        i = 1
        while i < len(lines) and not lines[i].startswith('#'):
            i += 1
        content_start = i
    else:
        content_start = 0

    if source_line is not None:
        result.append(source_line)
        result.append('')

    # --- Step 2: Process content lines ---
    content_lines = lines[content_start:]

    # --- Step 3: Strip footer nav links from end ---
    # Find the last content line, removing trailing * * * + nav link block
    end = len(content_lines)
    while end > 0 and content_lines[end - 1].strip() == '':
        end -= 1

    # Remove trailing nav line pattern: "* * *\n[nav](url)[nav](url)"
    if end >= 2 and is_footer_nav_line(content_lines[end - 1]):
        # Remove the nav line
        end -= 1
        # Remove trailing * * * separator(s) before it
        while end > 0 and content_lines[end - 1].strip() in ('* * *', '---', '***'):
            end -= 1
        # Remove any blank lines before the separator
        while end > 0 and content_lines[end - 1].strip() == '':
            end -= 1

    # Also strip trailing * * * separators that appear at the very end with no content after
    # (e.g. changelog ends with * * *\n* * * which is pure footer noise)
    # Only strip if there's no meaningful content after the separators
    saved_end = end
    temp_end = end
    while temp_end > 0 and content_lines[temp_end - 1].strip() in ('* * *', '---', '***'):
        temp_end -= 1
    while temp_end > 0 and content_lines[temp_end - 1].strip() == '':
        temp_end -= 1
    # Accept: removed at least one separator and didn't remove content
    if temp_end < saved_end and temp_end > 0:
        end = temp_end

    content_lines = content_lines[:end]

    # --- Step 4: Process remaining lines ---
    # Track whether previous non-empty line was a split heading prefix
    prev_was_split_heading = False
    split_heading_prefix = ''

    i = 0
    while i < len(content_lines):
        line = content_lines[i]

        # Skip empty anchor links
        if RE_EMPTY_ANCHOR.match(line):
            i += 1
            continue

        # Skip pagination markers
        if RE_PAGINATION.match(line):
            i += 1
            continue

        # Handle split headings: "# " alone on a line, followed by heading text on next line
        split_match = RE_SPLIT_HEADING.match(line)
        if split_match:
            hashes = split_match.group(1)
            # Check if next non-empty line is heading text (not another heading or anchor)
            next_i = i + 1
            while next_i < len(content_lines) and content_lines[next_i].strip() == '':
                next_i += 1
            if next_i < len(content_lines):
                next_line = content_lines[next_i].strip()
                # Next line is heading text if it doesn't start with # and isn't an anchor
                if next_line and not next_line.startswith('#') and not RE_EMPTY_ANCHOR.match(next_line):
                    # Merge: emit combined heading, skip the split prefix
                    result.append(f"{hashes} {next_line}")
                    i = next_i + 1
                    continue
            # If no valid next line, just skip the bare heading prefix
            i += 1
            continue

        result.append(line)
        i += 1

    # --- Step 5: Collapse multiple consecutive blank lines into one ---
    final = []
    prev_blank = False
    for line in result:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        final.append(line)
        prev_blank = is_blank

    # Remove trailing blank lines
    while final and final[-1].strip() == '':
        final.pop()

    return '\n'.join(final) + '\n'


def process_file(path: Path) -> tuple[int, int]:
    """Returns (chars_before, chars_after)."""
    original = path.read_text(encoding='utf-8')
    cleaned = clean_content(original)
    path.write_text(cleaned, encoding='utf-8')
    return len(original), len(cleaned)


def main(test_file: str = None):
    if test_file:
        # Test mode: process single file and print result
        p = Path(test_file)
        before, after = process_file(p)
        print(f"TEST: {p.name}")
        print(f"  Before: {before} chars")
        print(f"  After:  {after} chars")
        print(f"  Reduction: {(before - after) / before * 100:.1f}%")
        return

    files = sorted(INPUT_DIR.glob(FILE_PATTERN))
    if not files:
        print(f"No files found matching {INPUT_DIR}/{FILE_PATTERN}")
        sys.exit(1)

    total_before = 0
    total_after = 0
    processed = 0

    for path in files:
        before, after = process_file(path)
        total_before += before
        total_after += after
        processed += 1
        if processed % 100 == 0:
            print(f"  Processed {processed}/{len(files)} files...")

    reduction = (total_before - total_after) / total_before * 100 if total_before > 0 else 0
    print(f"\nFILES PROCESSED: {processed}")
    print(f"Total chars before: {total_before:,}")
    print(f"Total chars after:  {total_after:,}")
    print(f"Reduction: {reduction:.1f}%")


if __name__ == '__main__':
    test_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(test_arg)
