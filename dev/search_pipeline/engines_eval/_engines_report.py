"""Report building and saving for 01_engines.py search quality suite."""

# INFRASTRUCTURE
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

REPORTS_DIR = Path(__file__).parent / "01_reports"


# Extract domain from URL
def extract_domain(url: str) -> str:
    return urlparse(url).netloc


# Build full markdown report from all query results
def build_report(all_results: dict, compare: bool) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    all_items = [item for results in all_results.values() for item in results]
    total_queries = len(set(q for q, _ in all_results.keys()))
    total_results = sum(len(r) for r in all_results.values())
    avg_results = total_results / len(all_results) if all_results else 0
    multi_engine = sum(1 for item in all_items if len(item.get("engines", [])) > 1)
    multi_engine_pct = (multi_engine / len(all_items) * 100) if all_items else 0
    avg_score = sum(item.get("score", 0) for item in all_items) / len(all_items) if all_items else 0

    domain_counts = Counter(extract_domain(item.get("url", "")) for item in all_items)
    top_domains = domain_counts.most_common(10)

    lines = []
    lines.append("# Search Quality Report")
    lines.append(f"Date: {timestamp}")
    lines.append(f"Compare mode: {'yes' if compare else 'no'}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Unique queries: {total_queries}")
    lines.append(f"- Total runs: {len(all_results)} (queries x profiles)")
    lines.append(f"- Total results: {total_results}")
    lines.append(f"- Avg results per run: {avg_results:.1f}")
    lines.append(f"- Multi-engine results: {multi_engine_pct:.0f}% ({multi_engine}/{len(all_items)})")
    lines.append(f"- Avg score: {avg_score:.1f}")
    lines.append("")
    lines.append("### Top Domains")
    lines.append("")
    lines.append("| Domain | Count |")
    lines.append("|--------|-------|")
    for domain, count in top_domains:
        lines.append(f"| {domain} | {count} |")
    lines.append("")

    queries_seen = {}
    for (query, profile), results in all_results.items():
        if query not in queries_seen:
            queries_seen[query] = []
        queries_seen[query].append((profile, results))

    for query, profile_results in queries_seen.items():
        for profile_name, results in profile_results:
            lines.append(f'## Query: "{query}"')
            lines.append(f"Profile: {profile_name} | Results: {len(results)}")
            lines.append("")

            if not results:
                lines.append("*No results*")
                lines.append("")
                continue

            lines.append("| # | Score | Engines | Domain | Title | URL | Snippet |")
            lines.append("|---|-------|---------|--------|-------|-----|---------|")

            for idx, item in enumerate(results, 1):
                score = item.get("score", 0)
                engines = ", ".join(item.get("engines", []))
                domain = extract_domain(item.get("url", ""))
                title = item.get("title", "")[:80]
                url = item.get("url", "")
                snippet = item.get("content", "").replace("\n", " ").replace("|", "/")
                lines.append(f"| {idx} | {score:.1f} | {engines} | {domain} | {title} | {url} | {snippet} |")

            lines.append("")

        if compare and len(profile_results) > 1:
            lines.append(f'### Comparison: "{query}"')
            lines.append("")
            lines.append("| Metric | " + " | ".join(p for p, _ in profile_results) + " |")
            lines.append("|--------|" + "|".join("-----" for _ in profile_results) + "|")

            counts = [str(len(r)) for _, r in profile_results]
            lines.append("| Results | " + " | ".join(counts) + " |")

            avgs = [f"{sum(i.get('score', 0) for i in r) / len(r):.1f}" if r else "0" for _, r in profile_results]
            lines.append("| Avg Score | " + " | ".join(avgs) + " |")

            url_sets = [set(extract_domain(i.get("url", "")) for i in r) for _, r in profile_results]
            if len(url_sets) == 2:
                overlap = len(url_sets[0] & url_sets[1])
                total = len(url_sets[0] | url_sets[1])
                lines.append(f"| Domain Overlap | {overlap}/{total} domains shared | |")

            lines.append("")

    return "\n".join(lines)


# Save report to 01_reports directory
def save_report(report: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"search_report_{timestamp}.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved: {report_path}")
