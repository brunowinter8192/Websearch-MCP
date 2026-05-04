#!/usr/bin/env python3
"""Snippet quality analysis for search_smoke_20260504_023641.md."""

# INFRASTRUCTURE
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median as stat_median

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent.parent))

REPORT_DIR = SCRIPT_DIR / "01_reports"
SMOKE_REPORT = REPORT_DIR / "search_smoke_20260504_023641.md"

ALL_ENGINES = [
    "google", "duckduckgo", "mojeek", "lobsters",
    "google scholar", "crossref", "openalex", "stack_exchange",
]

# Combined EN + DE stopwords — hardcoded, no NLTK dependency
STOPWORDS = {
    "a","about","above","after","again","all","also","although","among","an","and","any",
    "are","as","at","be","because","been","before","being","between","both","but","by",
    "can","could","did","do","does","doing","during","each","even","ever","for","from",
    "get","got","had","has","have","having","he","her","here","him","his","how","if",
    "in","into","is","it","its","itself","just","like","may","me","might","more","most",
    "much","my","nor","not","now","of","off","on","or","other","our","out","own","per",
    "s","shall","she","should","since","so","some","such","t","than","that","the","their",
    "them","then","there","these","they","this","those","through","to","too","under","up",
    "us","very","was","we","were","what","when","where","which","while","who","will",
    "with","would","you","your","re","ve","ll","d","m","no","use",
    "aber","alle","allem","allen","aller","alles","als","also","am","an","ander","andere",
    "anderen","anderer","anderes","auf","aus","bei","bin","bis","bist","da","damit","dann",
    "das","dass","dem","den","denn","der","des","dessen","die","dies","diese","diesem",
    "diesen","dieser","dieses","doch","dort","du","durch","ein","eine","einem","einen",
    "einer","eines","er","es","etwas","fur","gegen","gibt","hat","hatte","haben","hier",
    "hin","hinter","ich","im","in","ist","ja","jede","jedem","jeden","jeder","jedes",
    "jetzt","kann","kein","keine","konnte","mal","man","mehr","mein","mit","nach","nicht",
    "noch","nun","nur","ob","oder","ohne","schon","sehr","seit","sich","sie","sind","so",
    "soll","sondern","uber","um","und","uns","unter","viel","vom","von","vor","war","was",
    "weil","wenn","werden","wie","will","wir","wird","wo","wurde","zum","zur","zu",
}

# Bloat detection patterns (derived from Phase A eyeball of actual snippets)
_BLOAT = [
    ("B1_url_breadcrumb",   re.compile(r'›')),
    ("B2_read_more",        re.compile(r'\bRead more\b')),
    ("B3_web_results",      re.compile(r'^Web results')),
    ("B4_featured_snippet", re.compile(r'^Featured snippet from the web')),
    ("B5_social_proof",     re.compile(r'\d[\d,.]*[Kk+]? *(likes|comments|answers|posts) *·')),
    ("B6_scholar_ellipsis", re.compile(r'^…\s|\s…\s|…$')),
    ("B7_mojeek_nav_dump",  re.compile(r'^\.\.\. .{5,150} \.\.\.$')),
    ("B8_meta_html_entity", re.compile(r'&[a-z]+;|&#\d+;')),
    ("B9_meta_tag_noise",   re.compile(r'Tagged with [\w, ]+\.?$')),
    ("B10_jats_xml",        re.compile(r'<jats:|<ns\d+:')),
]


# ORCHESTRATOR

# Parse smoke report, compute metrics, write report
def run_analysis() -> None:
    records = parse_smoke_report(SMOKE_REPORT)
    n_s = sum(len(r["snippets"]) for r in records)
    n_og = sum(1 for r in records if r["og"])
    n_m = sum(1 for r in records if r["meta"])
    print(f"Parsed {len(records)} records  snippets:{n_s}  og:{n_og}  meta:{n_m}", file=sys.stderr)
    source_stats = compute_source_stats(records)
    overlap = compute_overlap_matrix(records)
    examples = pick_diverse_examples(records, n=5)
    path = write_report(source_stats, overlap, examples, records)
    print(f"Report: {path}", file=sys.stderr)
    for src, st in source_stats.items():
        print(
            f"  {src}: N={st['n_samples']} bloated={st['pct_bloated']:.0f}%"
            f" clean={st['mean_clean_len']:.0f} useful={st['usefulness_score']:.0f}",
            file=sys.stderr,
        )


# FUNCTIONS

# Parse markdown smoke report into URL records with snippets and previews
def parse_smoke_report(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    records = []
    current_query = None
    current_record = None
    i = 0

    while i < len(lines):
        line = lines[i]

        m = re.match(r'^## Query \d+: (.+)$', line)
        if m:
            current_query = m.group(1).strip()
            i += 1
            continue

        m = re.match(r'^### \[\d+\] (https?://\S+)', line)
        if m:
            if current_record is not None:
                records.append(current_record)
            current_record = {
                "url": m.group(1),
                "query": current_query,
                "engine_sources": [],
                "snippets": {},
                "og": None,
                "meta": None,
            }
            i += 1
            continue

        if current_record is None:
            i += 1
            continue

        m = re.match(r'^\*\*Engines:\*\* (.+)$', line)
        if m:
            current_record["engine_sources"] = re.findall(r'`([^`]+)`', m.group(1))
            i += 1
            continue

        m = re.match(r'^\*\*Snippet \[([^\]]+)\]:\*\*(.*)', line)
        if m:
            engine = m.group(1)
            inline = m.group(2).strip()
            if "*(empty)*" in inline:
                current_record["snippets"][engine] = ""
                i += 1
            else:
                i += 1
                if i < len(lines):
                    nxt = lines[i].strip()
                    ok = nxt and "*(empty)*" not in nxt and not nxt.startswith("**") \
                        and not nxt.startswith("---") and not nxt.startswith("#")
                    current_record["snippets"][engine] = nxt if ok else ""
                else:
                    current_record["snippets"][engine] = ""
                i += 1
            continue

        m = re.match(r'^\*\*Preview \(og\):\*\* (.+)$', line)
        if m:
            current_record["og"] = m.group(1).strip()
            i += 1
            continue

        m = re.match(r'^\*\*Preview \(meta\):\*\* (.+)$', line)
        if m:
            current_record["meta"] = m.group(1).strip()
            i += 1
            continue

        i += 1

    if current_record is not None:
        records.append(current_record)
    return records


# Return set of bloat indicator IDs that fire on text
def detect_bloat(text: str) -> set[str]:
    return {name for name, pat in _BLOAT if pat.search(text)}


# Strip bloat patterns from text and return cleaned string
def strip_bloat(text: str) -> str:
    text = re.sub(r'^Web results', '', text)
    text = re.sub(r'^Featured snippet from the web', '', text)
    text = re.sub(r'\bRead more\b.*', '', text)
    text = re.sub(r'\d[\d,.]*[Kk+]? *(likes|comments|answers|posts) *·[^\n]*', '', text)
    text = re.sub(r'\S*›\S*', '', text)        # URL breadcrumb tokens
    text = re.sub(r'\d{1,2} \w{3,9} \d{4} — ', '', text)  # date prefix
    text = re.sub(r'&[a-z]+;|&#\d+;', '', text)
    text = re.sub(r'Tagged with [\w, ]+\.?$', '', text)
    text = re.sub(r'<[^>]+>', ' ', text)   # strip XML/HTML tags (e.g. <jats:p>)
    return ' '.join(text.split())


# Ratio of unique non-stopword content words (≥3 chars) to all word tokens
def lexical_density(text: str) -> float:
    words = re.findall(r'\b[a-zA-ZäöüÄÖÜßé]{3,}\b', text.lower())
    if not words:
        return 0.0
    unique_content = {w for w in words if w not in STOPWORDS}
    return len(unique_content) / len(words)


# Compute aggregate stats per snippet source across all records
def compute_source_stats(records: list[dict]) -> dict:
    texts_by: dict[str, list[str]] = {s: [] for s in ALL_ENGINES + ["preview_og", "preview_meta"]}
    total_by: dict[str, int] = defaultdict(int)
    empty_by: dict[str, int] = defaultdict(int)

    for rec in records:
        for eng, text in rec["snippets"].items():
            k = eng.lower()
            if k not in texts_by: continue
            total_by[k] += 1
            if text: texts_by[k].append(text)
            else: empty_by[k] += 1
        for k, v in (("preview_og", rec["og"]), ("preview_meta", rec["meta"])):
            if v is None: continue
            total_by[k] += 1
            if v: texts_by[k].append(v)
            else: empty_by[k] += 1

    stats = {}
    for src in ALL_ENGINES + ["preview_og", "preview_meta"]:
        txts = texts_by[src]
        n_samples = len(txts)
        if not txts:
            stats[src] = dict(n_total=total_by[src], n_empty=empty_by[src], n_samples=0,
                              mean_len=0.0, median_len=0.0, pct_bloated=0.0,
                              mean_clean_len=0.0, lexical_density=0.0, usefulness_score=0.0)
            continue
        lengths = [len(t) for t in txts]
        bloated = [bool(detect_bloat(t)) for t in txts]
        clean_lens = [len(strip_bloat(t)) for t in txts]
        lex = [lexical_density(t) for t in txts]
        m_clean = mean(clean_lens)
        m_lex = mean(lex)
        stats[src] = dict(
            n_total=total_by[src], n_empty=empty_by[src], n_samples=n_samples,
            mean_len=mean(lengths), median_len=stat_median(lengths),
            pct_bloated=100.0 * sum(bloated) / n_samples,
            mean_clean_len=m_clean,
            lexical_density=m_lex,
            usefulness_score=m_clean * m_lex,
        )
    return stats


# 8×8 co-occurrence: count (URL, query) pairs found by both engines
def compute_overlap_matrix(records: list[dict]) -> dict:
    url_engines: dict[tuple, set] = defaultdict(set)
    for rec in records:
        key = (rec["url"], rec["query"])
        for eng in rec["engine_sources"]:
            if eng.lower() in set(ALL_ENGINES):
                url_engines[key].add(eng.lower())

    matrix: dict[tuple, int] = defaultdict(int)
    for engines in url_engines.values():
        eng_list = sorted(engines)
        for a in range(len(eng_list)):
            for b in range(a + 1, len(eng_list)):
                matrix[(eng_list[a], eng_list[b])] += 1
                matrix[(eng_list[b], eng_list[a])] += 1
    return matrix


# Pick n URL records with diverse source families (≥3 distinct source types)
def pick_diverse_examples(records: list[dict], n: int = 5) -> list[dict]:
    WEB = {"google", "duckduckgo", "mojeek"}
    ACAD = {"google scholar", "crossref", "openalex"}

    scored = []
    for rec in records:
        snips = {e: t for e, t in rec["snippets"].items() if t}
        has_og, has_meta = bool(rec["og"]), bool(rec["meta"])
        n_web = sum(1 for e in snips if e in WEB)
        n_acad = sum(1 for e in snips if e in ACAD)
        has_se = bool(snips.get("stack_exchange"))
        n_prev = int(has_og) + int(has_meta)
        total_kinds = len(snips) + n_prev
        if total_kinds < 3:
            continue
        score = (
            total_kinds
            + int(n_web > 0 and n_acad > 0) * 4
            + int(has_se and n_web > 0) * 3
            + n_prev * 2
            + int(n_web > 1)
        )
        scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)

    selected: list[dict] = []
    seen_queries: set = set()
    for _, rec in scored:
        if len(selected) >= n:
            break
        if rec["query"] not in seen_queries:
            selected.append(rec)
            seen_queries.add(rec["query"])
    for _, rec in scored:  # fill remaining from any query
        if len(selected) >= n:
            break
        if rec not in selected:
            selected.append(rec)
    return selected[:n]


# Render and write the markdown report
def write_report(stats: dict, overlap: dict, examples: list[dict], records: list[dict]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"snippet_quality_{ts}.md"
    L: list[str] = []

    L += [
        f"# Snippet Quality Analysis — {ts}",
        "",
        f"Source: `{SMOKE_REPORT.name}`  ",
        f"URL records parsed: {len(records)}",
        "",
        "## 1. Per-Source Aggregated Stats",
        "",
        "Bloat indicators (any one fires → bloated): "
        "B1 URL breadcrumb (›) · B2 Read-more · B3 Web-results prefix · "
        "B4 Featured-snippet prefix · B5 Social-proof (N likes/comments ·) · "
        "B6 Scholar ellipsis (…) · B7 Mojeek nav-dump (…text…) · "
        "B8 HTML entities · B9 Tag noise (Tagged with …) · B10 JATS/NS XML tags (<jats:p> etc.).  ",
        "Usefulness = mean_clean_len × lexical_density.  ",
        "Lexical density = unique non-stopword words (≥3 chars) / all words (EN+DE combined stoplist).",
        "",
        "| Source | N total | N empty | N samples | Mean len | Median len | % bloated | Mean clean len | Lex density | Usefulness |",
        "|--------|---------|---------|-----------|----------|------------|-----------|----------------|-------------|------------|",
    ]
    for src in ALL_ENGINES + ["preview_og", "preview_meta"]:
        st = stats[src]
        L.append(
            f"| {src} | {st['n_total']} | {st['n_empty']} | {st['n_samples']}"
            f" | {st['mean_len']:.0f} | {st['median_len']:.0f}"
            f" | {st['pct_bloated']:.0f}% | {st['mean_clean_len']:.0f}"
            f" | {st['lexical_density']:.2f} | {st['usefulness_score']:.0f} |"
        )

    L += [
        "",
        "> **CrossRef — critical finding:** 49/300 entries have non-empty snippet text, but it is "
        "raw JATS XML (`<jats:p>…</jats:p>`, `<ns4:p>…</ns4:p>`) — unstripped. The other 251 are "
        "empty. **Consequence for SearchResult format:** CrossRef snippets need XML stripping when "
        "present, and metadata-field synthesis (title + journal + year) when absent. Neither is "
        "currently done — both cases return broken or empty snippet text to the model.",
        "",
        "## 2. Engine Overlap Matrix",
        "",
        "Cell (i, j) = count of (URL, query) pairs where both engines returned the URL.  ",
        "Same URL across different queries is counted separately.",
        "",
    ]
    short = {
        "google": "google", "duckduckgo": "ddg", "mojeek": "mojeek",
        "lobsters": "lobsters", "google scholar": "scholar", "crossref": "crossref",
        "openalex": "openalex", "stack_exchange": "stack_ex",
    }
    L.append("| — | " + " | ".join(short[e] for e in ALL_ENGINES) + " |")
    L.append("|---|" + "---|" * len(ALL_ENGINES))
    for e1 in ALL_ENGINES:
        row = [short[e1]] + [
            "—" if e1 == e2 else str(overlap.get((e1, e2), 0))
            for e2 in ALL_ENGINES
        ]
        L.append("| " + " | ".join(row) + " |")

    L += [
        "",
        "## 3. Side-by-Side Examples (≥3 distinct source kinds)",
        "",
        "Each example: one URL, all its non-empty snippet sources shown in full. "
        "Enables visual comparison of how different source families represent the same page.",
        "",
    ]
    for idx, rec in enumerate(examples, 1):
        snips = {e: t for e, t in rec["snippets"].items() if t}
        all_src = list(snips.keys()) + (["og"] if rec["og"] else []) + (["meta"] if rec["meta"] else [])
        L += [
            f"### Example {idx} — {len(snips)} engine snippet(s) + "
            f"{'og' if rec['og'] else ''}{'+ meta' if rec['meta'] else ''}",
            "",
            f"**URL:** {rec['url']}  ",
            f"**Query:** `{rec['query']}`  ",
            f"**Engine-sources line:** {', '.join(rec['engine_sources'])}  ",
            f"**Source kinds present:** {', '.join(all_src)}",
            "",
            "| Source | Full text |",
            "|--------|-----------|",
        ]
        for eng, text in snips.items():
            L.append(f"| snippet [{eng}] | {text.replace('|', chr(92) + '|')} |")
        if rec["og"]:
            L.append(f"| preview (og) | {rec['og'].replace('|', chr(92) + '|')} |")
        if rec["meta"]:
            L.append(f"| preview (meta) | {rec['meta'].replace('|', chr(92) + '|')} |")
        L.append("")

    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    run_analysis()
