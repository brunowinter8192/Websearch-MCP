# INFRASTRUCTURE
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DATE_RE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")


# FUNCTIONS

# Compute URL hash matching the filename convention
def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:12]


# Extract YYYY-MM-DD from publication_date field or URL path
def pub_date_str(entry: dict) -> str:
    pub = entry.get("publication_date", "")
    if pub and len(pub) >= 10:
        return pub[:10]
    m = DATE_RE.search(entry.get("url", ""))
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "unknown"


# Copy cleaned MDs to collection_dir as f"{source}__{pubdate}__{hash}.md"; return count copied.
def copy_articles(
    manifest: list[dict],
    clean_dir: Path,
    collection_dir: Path,
    source: str,
) -> int:
    n_copied = 0
    for entry in manifest:
        h = entry.get("hash") or url_hash(entry.get("url", ""))
        pubdate = pub_date_str(entry)
        src = clean_dir / f"{h}.md"
        dest = collection_dir / f"{source}__{pubdate}__{h}.md"
        if not src.exists():
            print(f"  WARN: source not found: {src}", file=sys.stderr)
            continue
        shutil.copy2(src, dest)
        n_copied += 1
    return n_copied


# Run rag-cli index on collection; return (files_indexed, chunks_indexed)
def run_rag_index(collection: str) -> tuple[int, int]:
    result = subprocess.run(
        ["rag-cli", "index", "--collection", collection],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"rag-cli index failed (exit {result.returncode}):\n{result.stderr}"
        )
    return parse_index_result(result.stdout + result.stderr)


# Parse "Done: N files indexed (M chunks)" from rag-cli output
def parse_index_result(output: str) -> tuple[int, int]:
    m = re.search(r"Done:\s*(\d+)\s*files?\s*indexed\s*\((\d+)\s*chunks?\)", output)
    if m:
        return int(m.group(1)), int(m.group(2))
    files_m = re.search(r"(\d+)\s*files?\s*indexed", output)
    chunks_m = re.search(r"\((\d+)\s*chunks?\)", output)
    files = int(files_m.group(1)) if files_m else 0
    chunks = int(chunks_m.group(1)) if chunks_m else 0
    return files, chunks


# Write/merge {collection_name}__index.jsonl in collection_dir; one line per article; dedup by hash.
def _write_index(
    manifest: list[dict],
    collection_dir: "Path",
    collection_name: str,
    source: str,
) -> None:
    index_path = collection_dir / f"{collection_name}__index.jsonl"
    existing: dict[str, dict] = {}
    if index_path.exists():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rec = json.loads(line)
                existing[rec["hash"]] = rec
    for entry in manifest:
        h = entry.get("hash") or url_hash(entry.get("url", ""))
        pubdate = pub_date_str(entry)
        existing[h] = {
            "hash": h,
            "url": entry.get("url", ""),
            "publication_date": pubdate,
            "filename": f"{source}__{pubdate}__{h}.md",
        }
    index_path.write_text(
        "\n".join(json.dumps(rec, ensure_ascii=False) for rec in existing.values()) + "\n",
        encoding="utf-8",
    )


# Copy articles to collection_dir then optionally run rag-cli index; return (n_copied, n_chunks).
def publish_articles(
    manifest: list[dict],
    clean_dir: Path,
    collection_dir: Path,
    source: str,
    collection_name: str,
    skip_index: bool = False,
) -> tuple[int, int]:
    if not manifest:
        print("Manifest empty — nothing to publish.", file=sys.stderr)
        return 0, 0

    collection_dir.mkdir(parents=True, exist_ok=True)
    n_copied = copy_articles(manifest, clean_dir, collection_dir, source)
    _write_index(manifest, collection_dir, collection_name, source)
    print(f"Copied: {n_copied} article(s) → {collection_dir}", file=sys.stderr)

    if skip_index:
        print("--skip-index set; skipping rag-cli index.", file=sys.stderr)
        return n_copied, 0

    indexed_files, indexed_chunks = run_rag_index(collection_name)
    print(f"Indexed: {indexed_files} file(s), {indexed_chunks} chunk(s).", file=sys.stderr)
    return n_copied, indexed_chunks
