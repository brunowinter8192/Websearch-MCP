#!/usr/bin/env python3
"""Boilerplate/content block classifier over already-stored paired scrape outputs — a faithful,
mechanical implementation of Kohlschuetter/Fankhauser/Nejdl (WSDM 2010, Algorithm 2), adapted to
markdown, plus the jusText-style short-heading rescue rule. Reads each (chromium, camoufox) file
pair named in `/tmp/lane_pairs_20.json`, classifies every block CONTENT/BOILERPLATE, and reports
per-URL/per-lane metrics plus a cross-pair aggregate. Reports numbers only — no verdict on which
lane is "better".
"""
# INFRASTRUCTURE
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
INPUT_PATH = Path("/tmp/lane_pairs_20.json")
REPORT_DIR = SCRIPT_DIR / "md"

LANES = ("chromium", "camoufox")

# A line that is ENTIRELY an HTML comment (the sidecar header lines are exactly this shape) —
# a comment mixed into a line with other content is not this and stays a normal block.
COMMENT_LINE_RE = re.compile(r"^<!--.*-->$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")

# Algorithm 2 thresholds, verbatim from the spec
LINK_DENSITY_SPLIT = 0.333333
PREV_LINK_DENSITY_SPLIT = 0.555556
CURR_WORDS_LOW_BRANCH_SPLIT = 16
NEXT_WORDS_LOW_BRANCH_SPLIT = 15
PREV_WORDS_LOW_BRANCH_SPLIT = 4
CURR_WORDS_HIGH_BRANCH_SPLIT = 40
NEXT_WORDS_HIGH_BRANCH_SPLIT = 17

# jusText-style heading rescue: a BOILERPLATE heading becomes CONTENT if a CONTENT block starts
# within this many characters of block text
HEADING_LOOKAHEAD_CHARS = 200

ZERO_NEIGHBOR = {"num_words": 0, "link_density": 0.0}


# ORCHESTRATOR

# Load the 20 lane pairs, classify both lane files per URL, report per-URL/per-lane metrics + aggregate
def lane_metrics_workflow() -> None:
    t_start = time.perf_counter()

    pairs = load_pairs(INPUT_PATH)
    results = []
    for pair in pairs:
        lane_metrics = {}
        for lane in LANES:
            file_path = Path(pair[f"{lane}_file"])
            lane_metrics[lane] = compute_file_metrics(file_path)
        results.append({"url": pair["url"], "lanes": lane_metrics})

    aggregate = compute_aggregate(results)
    report_path = write_report(results, aggregate)

    wall_s = time.perf_counter() - t_start
    print(f"Report: {report_path}", file=sys.stderr)
    print(f"Wall time: {wall_s:.1f}s", file=sys.stderr)


# FUNCTIONS

# The 20 {url, chromium_file, camoufox_file, ...} entries
def load_pairs(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# A token contains at least one letter or digit (markdown punctuation alone is not a token)
def is_token(word: str) -> bool:
    return any(ch.isalpha() or ch.isdigit() for ch in word)


# Whitespace-split tokens of text, filtered down to actual tokens
def tokenize(text: str) -> list[str]:
    return [w for w in text.split() if is_token(w)]


# True for a line that is entirely one or more HTML comments, e.g. the sidecar header
def is_comment_line(line: str) -> bool:
    return bool(COMMENT_LINE_RE.match(line.strip()))


# True for a line starting with one or more '#' (a markdown heading)
def is_heading_line(line: str) -> bool:
    return line.lstrip().startswith("#")


# Strip images entirely, reduce links to their visible text, and count tokens that sit inside link text
def process_line(line: str) -> tuple[str, int]:
    no_images = IMAGE_RE.sub("", line)
    link_tokens = 0

    def _reduce_link(match: re.Match) -> str:
        nonlocal link_tokens
        link_text = match.group(1)
        link_tokens += len(tokenize(link_text))
        return link_text

    visible_text = LINK_RE.sub(_reduce_link, no_images)
    return visible_text, link_tokens


# One file's blocks: non-comment, non-empty lines with >=1 token, each with its own metrics
def read_blocks(path: Path) -> list[dict]:
    blocks = []
    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            if is_comment_line(line):
                continue
            visible_text, link_tokens = process_line(line)
            num_words = len(tokenize(visible_text))
            if num_words == 0:
                continue
            blocks.append({
                "num_words": num_words,
                "link_tokens": link_tokens,
                "link_density": link_tokens / num_words,
                "char_len": len(visible_text),
                "is_heading": is_heading_line(line),
            })
    return blocks


# Algorithm 2's decision tree for one block, given its previous and next neighbour
def classify_block(curr: dict, prev: dict, nxt: dict) -> str:
    if curr["link_density"] > LINK_DENSITY_SPLIT:
        return "BOILERPLATE"
    if prev["link_density"] <= PREV_LINK_DENSITY_SPLIT:
        if curr["num_words"] > CURR_WORDS_LOW_BRANCH_SPLIT:
            return "CONTENT"
        if nxt["num_words"] > NEXT_WORDS_LOW_BRANCH_SPLIT:
            return "CONTENT"
        if prev["num_words"] > PREV_WORDS_LOW_BRANCH_SPLIT:
            return "CONTENT"
        return "BOILERPLATE"
    if curr["num_words"] > CURR_WORDS_HIGH_BRANCH_SPLIT:
        return "CONTENT"
    if nxt["num_words"] > NEXT_WORDS_HIGH_BRANCH_SPLIT:
        return "CONTENT"
    return "BOILERPLATE"


# Tree classification for every block in a file; missing neighbours count as numWords=0, linkDensity=0
def classify_blocks(blocks: list[dict]) -> list[str]:
    n = len(blocks)
    classifications = []
    for i, block in enumerate(blocks):
        prev = blocks[i - 1] if i > 0 else ZERO_NEIGHBOR
        nxt = blocks[i + 1] if i < n - 1 else ZERO_NEIGHBOR
        classifications.append(classify_block(block, prev, nxt))
    return classifications


# One pass, off the tree's own classifications: a BOILERPLATE heading becomes CONTENT if a CONTENT
# block starts within HEADING_LOOKAHEAD_CHARS of block text
def apply_heading_rule(blocks: list[dict], tree_classifications: list[str]) -> list[str]:
    final = list(tree_classifications)
    for i, block in enumerate(blocks):
        if tree_classifications[i] != "BOILERPLATE" or not block["is_heading"]:
            continue
        cumulative_chars = 0
        for j in range(i + 1, len(blocks)):
            if tree_classifications[j] == "CONTENT" and cumulative_chars <= HEADING_LOOKAHEAD_CHARS:
                final[i] = "CONTENT"
                break
            cumulative_chars += blocks[j]["char_len"]
            if cumulative_chars > HEADING_LOOKAHEAD_CHARS:
                break
    return final


# blocks_total/content, words_total/content(+pct), overall link density, longest content block
def aggregate_file_metrics(blocks: list[dict], classifications: list[str]) -> dict:
    blocks_total = len(blocks)
    blocks_content = sum(1 for c in classifications if c == "CONTENT")
    words_total = sum(b["num_words"] for b in blocks)
    words_content = sum(b["num_words"] for b, c in zip(blocks, classifications) if c == "CONTENT")
    link_tokens_total = sum(b["link_tokens"] for b in blocks)
    link_density_overall = link_tokens_total / words_total if words_total else 0.0
    words_content_pct = (words_content / words_total * 100) if words_total else 0.0
    content_word_counts = [b["num_words"] for b, c in zip(blocks, classifications) if c == "CONTENT"]
    longest_content_block = max(content_word_counts, default=0)
    return {
        "blocks_total": blocks_total,
        "blocks_content": blocks_content,
        "words_total": words_total,
        "words_content": words_content,
        "words_content_pct": words_content_pct,
        "link_density_overall": link_density_overall,
        "longest_content_block": longest_content_block,
    }


# Full metric set for one file: read blocks once, classify (tree + heading rule), aggregate
def compute_file_metrics(path: Path) -> dict:
    blocks = read_blocks(path)
    tree_classifications = classify_blocks(blocks)
    final_classifications = apply_heading_rule(blocks, tree_classifications)
    return aggregate_file_metrics(blocks, final_classifications)


# 'chromium', 'camoufox', or 'tie' — whichever lane has the larger value
def winning_lane(chromium_value: float, camoufox_value: float) -> str:
    if chromium_value > camoufox_value:
        return "chromium"
    if camoufox_value > chromium_value:
        return "camoufox"
    return "tie"


# Cross-pair counts: wins on CONTENT words, wins on CONTENT percentage, and where those disagree
def compute_aggregate(results: list[dict]) -> dict:
    words_wins = {"chromium": 0, "camoufox": 0, "tie": 0}
    pct_wins = {"chromium": 0, "camoufox": 0, "tie": 0}
    disagreements = []

    for entry in results:
        chromium_m = entry["lanes"]["chromium"]
        camoufox_m = entry["lanes"]["camoufox"]

        words_winner = winning_lane(chromium_m["words_content"], camoufox_m["words_content"])
        pct_winner = winning_lane(chromium_m["words_content_pct"], camoufox_m["words_content_pct"])
        words_wins[words_winner] += 1
        pct_wins[pct_winner] += 1

        if "tie" not in (words_winner, pct_winner) and words_winner != pct_winner:
            disagreements.append(entry["url"])

    return {"words_wins": words_wins, "pct_wins": pct_wins, "disagreements": disagreements}


# Pad s to width with spaces, but never fewer than 2 (so huge numbers still get a column gap)
def pad_min2(s: str, width: int) -> str:
    return s + " " * max(2, width - len(s))


# One lane's lean summary line, e.g. "chromium  content 187/187 words (100%)  blocks 8/8  ..."
def format_lane_line(lane: str, m: dict) -> str:
    content_str = f"content {m['words_content']}/{m['words_total']} words ({m['words_content_pct']:.0f}%)"
    blocks_str = f"blocks {m['blocks_content']}/{m['blocks_total']}"
    return (
        f"{lane:<9s} {pad_min2(content_str, 32)}{pad_min2(blocks_str, 12)}"
        f"link-density {m['link_density_overall']:.2f}  longest {m['longest_content_block']}w"
    )


# Per-URL section: the URL heading plus one lean line per lane
def format_url_section(entry: dict) -> str:
    lines = [f"### {entry['url']}", ""]
    for lane in LANES:
        lines.append(format_lane_line(lane, entry["lanes"][lane]))
    return "\n".join(lines)


# One markdown table row per lane per URL, same numbers as the per-URL sections
def format_table(results: list[dict]) -> str:
    header = (
        "| URL | Lane | Content words | Content % | Blocks | Link density | Longest (w) |\n"
        "|---|---|---|---|---|---|---|"
    )
    rows = [header]
    for entry in results:
        for lane in LANES:
            m = entry["lanes"][lane]
            rows.append(
                f"| {entry['url']} | {lane} | {m['words_content']}/{m['words_total']} | "
                f"{m['words_content_pct']:.0f}% | {m['blocks_content']}/{m['blocks_total']} | "
                f"{m['link_density_overall']:.2f} | {m['longest_content_block']} |"
            )
    return "## All 20 URLs\n\n" + "\n".join(rows)


# Aggregate section: per-lane win counts on two measures, and where those two measures disagree
def format_aggregate_section(aggregate: dict) -> str:
    ww = aggregate["words_wins"]
    pw = aggregate["pct_wins"]
    lines = [
        "## Aggregate (20 pairs)",
        "",
        f"- More CONTENT words: chromium {ww['chromium']}, camoufox {ww['camoufox']}, tie {ww['tie']}",
        f"- Higher CONTENT percentage: chromium {pw['chromium']}, camoufox {pw['camoufox']}, tie {pw['tie']}",
        f"- Pairs where the two measures point at different lanes: {len(aggregate['disagreements'])}",
    ]
    if aggregate["disagreements"]:
        lines.append("")
        for url in aggregate["disagreements"]:
            lines.append(f"  - {url}")
    return "\n".join(lines)


# Assemble and write the full report to dev/lane_choice/md/
def write_report(results: list[dict], aggregate: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"04_lane_metrics_report_{ts}.md"

    sections = [
        "# Lane content/boilerplate metrics (Kohlschuetter Algorithm 2)",
        "\n\n".join(format_url_section(entry) for entry in results),
        format_table(results),
        format_aggregate_section(aggregate),
    ]
    report_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    return report_path


def main():
    lane_metrics_workflow()


if __name__ == "__main__":
    main()

