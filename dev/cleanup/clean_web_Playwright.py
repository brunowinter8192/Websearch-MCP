"""
Cleanup script for Playwright docs crawled markdown files.

Removes Docusaurus website chrome:
- Header: "Skip to main content" through full sidebar nav + breadcrumb + "On this page" label
- Footer: [Previous/Next] nav + in-page TOC + Learn/Community/More sections + copyright

Content is sandwiched between:
  START: first `# ` heading (after "On this page" block)
  END:   "[Previous " or "[Next " pagination link (whichever comes first after content starts)
         OR "Learn\n" section header if no prev/next link

Preserves: <!-- source: URL --> comment at top of file.
"""

from pathlib import Path
import re

INPUT_DIR = Path("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/MCP/RAG/data/documents/Playwright")


def find_content_start(lines: list[str]) -> int:
    """Return index of first `# ` heading line (the real page title)."""
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return i
    return -1


def find_content_end(lines: list[str], start: int) -> int:
    """
    Return index of first footer line after content start.

    Footer begins at whichever comes first:
      - A line matching `[Previous ` or `[Next ` (Docusaurus prev/next nav)
      - A bare `Learn` line followed by a list item (site footer section header)
    """
    for i in range(start, len(lines)):
        line = lines[i]

        # Prev/Next navigation link (marks end of content, start of footer)
        if re.match(r'^\[(?:Previous|Next)\b', line):
            return i

        # Site footer section headers (Learn / Community / More)
        if line.strip() in ("Learn", "Community", "More"):
            # Confirm next non-empty line is a list item
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].strip():
                    if lines[j].strip().startswith("* ["):
                        return i
                    break

    return len(lines)


def extract_source_comment(lines: list[str]) -> str:
    """Return the <!-- source: ... --> comment if it's on line 0 or 1."""
    for line in lines[:3]:
        if line.startswith("<!-- source:"):
            return line.rstrip()
    return ""


def clean_file(path: Path) -> tuple[int, int]:
    """Clean one file in-place. Returns (chars_before, chars_after)."""
    text = path.read_text(encoding="utf-8")
    chars_before = len(text)

    lines = text.splitlines(keepends=True)

    source_comment = extract_source_comment(lines)

    content_start = find_content_start(lines)
    if content_start == -1:
        # No heading found — keep file as-is
        return chars_before, chars_before

    content_end = find_content_end(lines, content_start)

    content_lines = lines[content_start:content_end]

    # Strip trailing blank lines from content
    while content_lines and content_lines[-1].strip() == "":
        content_lines.pop()

    # Assemble cleaned file
    parts = []
    if source_comment:
        parts.append(source_comment + "\n\n")
    parts.append("".join(content_lines))
    if not parts[-1].endswith("\n"):
        parts.append("\n")

    cleaned = "".join(parts)
    path.write_text(cleaned, encoding="utf-8")

    return chars_before, len(cleaned)


def main():
    md_files = sorted(INPUT_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {INPUT_DIR}")
        return

    total_before = 0
    total_after = 0
    processed = 0
    skipped = 0

    for path in md_files:
        before, after = clean_file(path)
        total_before += before
        total_after += after
        if before == after:
            skipped += 1
        else:
            processed += 1

    reduction = (1 - total_after / total_before) * 100 if total_before else 0
    print(f"FILES PROCESSED: {processed} cleaned, {skipped} unchanged")
    print(f"Total chars before: {total_before:,}")
    print(f"Total chars after:  {total_after:,}")
    print(f"Reduction: {reduction:.1f}%")


if __name__ == "__main__":
    main()
