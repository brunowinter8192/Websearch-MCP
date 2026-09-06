#!/usr/bin/env python3
"""Boilerplate/content block classifier over EVERY paired chromium/camoufox scrape in the
production log — a faithful, mechanical implementation of Kohlschuetter/Fankhauser/Nejdl (WSDM
2010, Algorithm 2), adapted to markdown, plus the jusText-style short-heading rescue rule, plus a
block-level PROSE test on top of CONTENT: CONTENT, at or under a corpus-derived length cap, and
containing a sentence-ending mark — added because a single very long markdown line (embedded JSON/
CSS/markup) can pass the CONTENT tree with a huge word count that no real prose block has. Builds
its own pair list from the production `scrape_log.jsonl` (every URL where both lanes have a
freshest record with no `acquisition_error` and real `bytes_returned`, plus a `content_path` —
the log no longer computes an "ok" verdict itself, see src/scraper/DOCS.md's Gotchas), no external
file dependency. Reports numbers only — no verdict on which lane is "better".
"""
# INFRASTRUCTURE
import json
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPORT_DIR = SCRIPT_DIR / "md"

# The MAIN repo's canonical production log — never a worktree copy (worktrees have their own,
# separate, gitignored src/logs/ tree), same hardcoded-absolute-path convention as
# 01_backfill_pairs.py's own PROD_SCRAPE_LOG_PATH.
PROD_SCRAPE_LOG_PATH = Path(
    "/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/src/logs/scrape_log.jsonl"
)

LANES = ("chromium", "camoufox")

# A line that is ENTIRELY an HTML comment (the sidecar header lines are exactly this shape) —
# a comment mixed into a line with other content is not this and stays a normal block.
COMMENT_LINE_RE = re.compile(r"^<!--.*-->$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
SENTENCE_END_CHARS = (".", "!", "?")

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

# The PROSE length cap is this percentile of the corpus's own chromium block-word-count
# distribution (see process-docs/lane_choice/ for the measured distribution and the reasoning for
# picking a percentile at all) — chromium output is post-PruningContentFilter, the best available
# proxy in this project for what a real prose block looks like.
PROSE_PERCENTILE = 99

ZERO_NEIGHBOR = {"num_words": 0, "link_density": 0.0}


# ORCHESTRATOR

# Build the pair list from the production log, derive the PROSE cap, classify both lanes per URL, report
def lane_metrics_workflow() -> None:
    t_start = time.perf_counter()

    pairs = collect_pairs_from_scrape_log()
    chromium_blocks_by_url = {pair["url"]: read_blocks(pair["chromium_path"]) for pair in pairs}
    cap, distribution = compute_prose_cap(list(chromium_blocks_by_url.values()))

    results = []
    for pair in pairs:
        url = pair["url"]
        lane_metrics = {
            "chromium": compute_metrics_from_blocks(chromium_blocks_by_url[url], cap),
            "camoufox": compute_file_metrics(pair["camoufox_path"], cap),
        }
        results.append({"url": url, "lanes": lane_metrics})

    aggregate = compute_aggregate(results)
    report_path = write_report(results, aggregate, cap, distribution)

    wall_s = time.perf_counter() - t_start
    print(f"Pairs: {len(pairs)}", file=sys.stderr)
    print(f"PROSE cap: {cap} words (p{PROSE_PERCENTILE} of {distribution['n']} chromium blocks)", file=sys.stderr)
    print(f"Report: {report_path}", file=sys.stderr)
    print(f"Wall time: {wall_s:.1f}s", file=sys.stderr)


# FUNCTIONS

# The freshest ok+content_path record per (url, engine) in the production log — the log
# accumulates across sessions, so a later scrape supersedes an earlier one of the same pair.
# "ok" is no longer a field the log computes (see src/scraper/DOCS.md's Gotchas): a record newer
# than that removal has no "outcome" key at all, so the old `!= "ok"` check would silently exclude
# every one of them. Reconstructed here off the two facts that replaced it — no acquisition_error,
# and real bytes actually came back — a historical pre-removal record with a genuine
# `"outcome": "ok"` also has `acquisition_error` absent (falsy via .get) and a real byte count, so
# this reads identically on old and new records alike.
def _latest_ok_records_by_url_engine(log_path: Path) -> dict[tuple[str, str], dict]:
    latest: dict[tuple[str, str], dict] = {}
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("acquisition_error") or not record.get("bytes_returned"):
                continue
            if not record.get("content_path"):
                continue
            key = (record["url"], record.get("engine"))
            if key not in latest or record["ts"] > latest[key]["ts"]:
                latest[key] = record
    return latest


# A record's sidecar content file, relative to the log file's own directory (scrape_logger.py's convention)
def _resolve_content_path(log_path: Path, record: dict) -> Path:
    return log_path.parent / record["content_path"]


# Every URL with a freshest-ok record on BOTH lanes, first-seen order in the log
def collect_pairs_from_scrape_log() -> list[dict]:
    latest = _latest_ok_records_by_url_engine(PROD_SCRAPE_LOG_PATH)

    seen_urls: list[str] = []
    seen_set: set[str] = set()
    for url, _engine in latest:
        if url not in seen_set:
            seen_set.add(url)
            seen_urls.append(url)

    pairs = []
    for url in seen_urls:
        chromium_record = latest.get((url, "chromium"))
        camoufox_record = latest.get((url, "camoufox"))
        if chromium_record is None or camoufox_record is None:
            continue
        pairs.append({
            "url": url,
            "chromium_path": _resolve_content_path(PROD_SCRAPE_LOG_PATH, chromium_record),
            "camoufox_path": _resolve_content_path(PROD_SCRAPE_LOG_PATH, camoufox_record),
        })
    return pairs


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


# True if the visible text contains at least one sentence-ending mark
def contains_sentence_end(text: str) -> bool:
    return any(ch in text for ch in SENTENCE_END_CHARS)


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
                "has_sentence_end": contains_sentence_end(visible_text),
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


# Derive the PROSE cap (PROSE_PERCENTILE of the pooled chromium block-word-count distribution)
# plus the distribution itself, for the report
def compute_prose_cap(chromium_block_lists: list[list[dict]]) -> tuple[int, dict]:
    word_counts = sorted(b["num_words"] for blocks in chromium_block_lists for b in blocks)
    quantiles = statistics.quantiles(word_counts, n=100, method="inclusive")
    cap = round(quantiles[PROSE_PERCENTILE - 1])
    distribution = {
        "n": len(word_counts),
        "median": statistics.median(word_counts),
        "p50": quantiles[49],
        "p75": quantiles[74],
        "p90": quantiles[89],
        "p95": quantiles[94],
        "p99": quantiles[98],
        "max": word_counts[-1],
    }
    return cap, distribution


# CONTENT, at or under the corpus-derived length cap, and containing a sentence-ending mark
def is_prose_block(classification: str, block: dict, cap: int) -> bool:
    return classification == "CONTENT" and block["num_words"] <= cap and block["has_sentence_end"]


# blocks_total/content, words_total/content(+pct), overall link density, longest content block,
# PROSE blocks/words, and blocks/words the cap excludes (CONTENT + sentence-ending, over cap)
def aggregate_file_metrics(blocks: list[dict], classifications: list[str], cap: int) -> dict:
    blocks_total = len(blocks)
    blocks_content = sum(1 for c in classifications if c == "CONTENT")
    words_total = sum(b["num_words"] for b in blocks)
    words_content = sum(b["num_words"] for b, c in zip(blocks, classifications) if c == "CONTENT")
    link_tokens_total = sum(b["link_tokens"] for b in blocks)
    link_density_overall = link_tokens_total / words_total if words_total else 0.0
    words_content_pct = (words_content / words_total * 100) if words_total else 0.0
    content_word_counts = [b["num_words"] for b, c in zip(blocks, classifications) if c == "CONTENT"]
    longest_content_block = max(content_word_counts, default=0)

    prose_flags = [is_prose_block(c, b, cap) for b, c in zip(blocks, classifications)]
    prose_blocks = sum(prose_flags)
    prose_words = sum(b["num_words"] for b, flag in zip(blocks, prose_flags) if flag)

    cap_excluded_flags = [
        c == "CONTENT" and b["has_sentence_end"] and b["num_words"] > cap
        for b, c in zip(blocks, classifications)
    ]
    cap_excluded_blocks = sum(cap_excluded_flags)
    cap_excluded_words = sum(b["num_words"] for b, flag in zip(blocks, cap_excluded_flags) if flag)

    return {
        "blocks_total": blocks_total,
        "blocks_content": blocks_content,
        "words_total": words_total,
        "words_content": words_content,
        "words_content_pct": words_content_pct,
        "link_density_overall": link_density_overall,
        "longest_content_block": longest_content_block,
        "prose_blocks": prose_blocks,
        "prose_words": prose_words,
        "cap_excluded_blocks": cap_excluded_blocks,
        "cap_excluded_words": cap_excluded_words,
    }


# Classify (tree + heading rule) + aggregate an already-read block list
def compute_metrics_from_blocks(blocks: list[dict], cap: int) -> dict:
    tree_classifications = classify_blocks(blocks)
    final_classifications = apply_heading_rule(blocks, tree_classifications)
    return aggregate_file_metrics(blocks, final_classifications, cap)


# Full metric set for one file: read blocks once, classify, aggregate
def compute_file_metrics(path: Path, cap: int) -> dict:
    blocks = read_blocks(path)
    return compute_metrics_from_blocks(blocks, cap)


# 'chromium', 'camoufox', or 'tie' — whichever lane has the larger value
def winning_lane(chromium_value: float, camoufox_value: float) -> str:
    if chromium_value > camoufox_value:
        return "chromium"
    if camoufox_value > chromium_value:
        return "camoufox"
    return "tie"


# Cross-pair counts: wins on CONTENT words/percentage, cap-exclusion totals per lane, and the
# chromium-zero-CONTENT / camoufox-PROSE-rescue counts
def compute_aggregate(results: list[dict]) -> dict:
    words_wins = {"chromium": 0, "camoufox": 0, "tie": 0}
    pct_wins = {"chromium": 0, "camoufox": 0, "tie": 0}
    disagreements = []
    cap_excluded = {lane: {"blocks": 0, "words": 0} for lane in LANES}

    for entry in results:
        chromium_m = entry["lanes"]["chromium"]
        camoufox_m = entry["lanes"]["camoufox"]

        words_winner = winning_lane(chromium_m["words_content"], camoufox_m["words_content"])
        pct_winner = winning_lane(chromium_m["words_content_pct"], camoufox_m["words_content_pct"])
        words_wins[words_winner] += 1
        pct_wins[pct_winner] += 1
        if "tie" not in (words_winner, pct_winner) and words_winner != pct_winner:
            disagreements.append(entry["url"])

        for lane in LANES:
            cap_excluded[lane]["blocks"] += entry["lanes"][lane]["cap_excluded_blocks"]
            cap_excluded[lane]["words"] += entry["lanes"][lane]["cap_excluded_words"]

    zero_content_chromium = [e for e in results if e["lanes"]["chromium"]["blocks_content"] == 0]
    rescued_by_camoufox_prose = [
        e["url"] for e in zero_content_chromium if e["lanes"]["camoufox"]["prose_blocks"] >= 1
    ]
    not_rescued = [
        e["url"] for e in zero_content_chromium if e["lanes"]["camoufox"]["prose_blocks"] == 0
    ]

    return {
        "words_wins": words_wins,
        "pct_wins": pct_wins,
        "disagreements": disagreements,
        "cap_excluded": cap_excluded,
        "zero_content_chromium_count": len(zero_content_chromium),
        "rescued_by_camoufox_prose": rescued_by_camoufox_prose,
        "not_rescued": not_rescued,
    }


# Pad s to width with spaces, but never fewer than 2 (so huge numbers still get a column gap)
def pad_min2(s: str, width: int) -> str:
    return s + " " * max(2, width - len(s))


# One lane's lean summary line, e.g. "chromium  content 187/187 words (100%)  blocks 8/8  ..."
def format_lane_line(lane: str, m: dict) -> str:
    content_str = f"content {m['words_content']}/{m['words_total']} words ({m['words_content_pct']:.0f}%)"
    blocks_str = f"blocks {m['blocks_content']}/{m['blocks_total']}"
    link_str = f"link-density {m['link_density_overall']:.2f}"
    longest_str = f"longest {m['longest_content_block']}w"
    prose_str = f"prose {m['prose_blocks']}/{m['blocks_content']}blk {m['prose_words']}w"
    return (
        f"{lane:<9s} {pad_min2(content_str, 32)}{pad_min2(blocks_str, 12)}"
        f"{pad_min2(link_str, 18)}{pad_min2(longest_str, 14)}{prose_str}"
    )


# Per-URL section: the URL heading plus one lean line per lane
def format_url_section(entry: dict) -> str:
    lines = [f"### {entry['url']}", ""]
    for lane in LANES:
        lines.append(format_lane_line(lane, entry["lanes"][lane]))
    return "\n".join(lines)


# One markdown table row per lane per URL, same numbers as the per-URL sections, plus PROSE columns
def format_table(results: list[dict]) -> str:
    header = (
        "| URL | Lane | Content words | Content % | Blocks | Link density | Longest (w) | "
        "Prose blocks | Prose words |\n"
        "|---|---|---|---|---|---|---|---|---|"
    )
    rows = [header]
    for entry in results:
        for lane in LANES:
            m = entry["lanes"][lane]
            rows.append(
                f"| {entry['url']} | {lane} | {m['words_content']}/{m['words_total']} | "
                f"{m['words_content_pct']:.0f}% | {m['blocks_content']}/{m['blocks_total']} | "
                f"{m['link_density_overall']:.2f} | {m['longest_content_block']} | "
                f"{m['prose_blocks']}/{m['blocks_content']} | {m['prose_words']} |"
            )
    return f"## All {len(results)} URLs\n\n" + "\n".join(rows)


# The corpus-derived PROSE cap: the chromium block-word-count distribution and the value chosen
def format_cap_section(cap: int, distribution: dict) -> str:
    lines = [
        "## PROSE length cap (derived from the chromium block-word-count distribution)",
        "",
        f"- Chromium blocks measured: {distribution['n']}",
        f"- median: {distribution['median']:.0f}  p50: {distribution['p50']:.0f}  "
        f"p75: {distribution['p75']:.0f}  p90: {distribution['p90']:.0f}  "
        f"p95: {distribution['p95']:.0f}  p99: {distribution['p99']:.0f}  max: {distribution['max']}",
        f"- Cap chosen: {cap} words — the {PROSE_PERCENTILE}th percentile of the distribution above.",
    ]
    return "\n".join(lines)


# Aggregate section: per-lane win counts, cap-exclusion totals, and where the two win-measures disagree
def format_aggregate_section(aggregate: dict, pair_count: int) -> str:
    ww = aggregate["words_wins"]
    pw = aggregate["pct_wins"]
    ce = aggregate["cap_excluded"]
    lines = [
        f"## Aggregate ({pair_count} pairs)",
        "",
        f"- More CONTENT words: chromium {ww['chromium']}, camoufox {ww['camoufox']}, tie {ww['tie']}",
        f"- Higher CONTENT percentage: chromium {pw['chromium']}, camoufox {pw['camoufox']}, tie {pw['tie']}",
        f"- Pairs where the two measures point at different lanes: {len(aggregate['disagreements'])}",
    ]
    if aggregate["disagreements"]:
        lines.append("")
        for url in aggregate["disagreements"]:
            lines.append(f"  - {url}")
    lines += [
        "",
        "- PROSE-cap exclusions (CONTENT blocks with a sentence-ending mark, over the cap), per lane:",
        f"  - chromium: {ce['chromium']['blocks']} blocks, {ce['chromium']['words']} words",
        f"  - camoufox: {ce['camoufox']['blocks']} blocks, {ce['camoufox']['words']} words",
    ]
    return "\n".join(lines)


# Where chromium has zero CONTENT blocks, split by whether camoufox has a PROSE block or not
def format_rescue_section(aggregate: dict) -> str:
    rescued = aggregate["rescued_by_camoufox_prose"]
    not_rescued = aggregate["not_rescued"]
    lines = [
        "## Pairs where chromium has zero CONTENT blocks",
        "",
        f"- Total: {aggregate['zero_content_chromium_count']}",
        f"- Of those, camoufox has at least one PROSE block: {len(rescued)}",
        f"- Of those, camoufox has zero PROSE blocks: {len(not_rescued)}",
    ]
    if rescued:
        lines += ["", "### camoufox has >=1 PROSE block"]
        for url in rescued:
            lines.append(f"- {url}")
    if not_rescued:
        lines += ["", "### camoufox has zero PROSE blocks"]
        for url in not_rescued:
            lines.append(f"- {url}")
    return "\n".join(lines)


# Assemble and write the full report to dev/lane_choice/md/
def write_report(results: list[dict], aggregate: dict, cap: int, distribution: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"04_lane_metrics_report_{ts}.md"

    sections = [
        "# Lane content/boilerplate metrics (Kohlschuetter Algorithm 2 + PROSE cap)",
        format_cap_section(cap, distribution),
        "\n\n".join(format_url_section(entry) for entry in results),
        format_table(results),
        format_aggregate_section(aggregate, len(results)),
        format_rescue_section(aggregate),
    ]
    report_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    return report_path


def main():
    lane_metrics_workflow()


if __name__ == "__main__":
    main()
