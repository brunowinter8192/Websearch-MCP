---
name: websearch-capture-and-index
description:
---

# Capture-and-Index — Skill

**Several domains run step by step across ALL of them, never domain by domain.**
- Discover all, take ONE Step-1 stop covering all, scrape all, clean all.

**Scrape failures are reported, never acted on mid-capture.**

## Step 1 — Discovery

```bash
cd /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch
./venv/bin/python cli.py discover_urls "<seed_url>" --url-file /tmp/<domain>_urls.txt
```

🛑 **STOP and report:**
- the absolute path of `/tmp/<domain>_urls.txt`, one URL per line, as a clickable link

**Go idle.**

## Step 2 — Scrape

**Input, named by the main agent with the go.**
- `<culled_url_file>` holds the URLs to scrape.

```bash
cd /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch
./venv/bin/python -m src.crawler.pipe_scraper \
    --url-file <culled_url_file> \
    --output-dir /tmp/<domain>/ > /tmp/<domain>_scrape.log 2>&1
```

**Go idle once that command has been run.**
- It auto-backgrounds, and `/tmp/<domain>_scrape.log` carries its summary line when it returns.

**Split the link file pipe_scraper wrote.**

```bash
comm -13 <(sort <discovery_url_file>) <(sort /tmp/<domain>_links.txt) > /tmp/<domain>_new_links.txt
comm -12 <(sort <discovery_url_file>) <(sort /tmp/<domain>_links.txt) > /tmp/<domain>_known_links.txt
```

🛑 **STOP and report:**
- scraped OK, errors, duration
- the absolute path of `/tmp/<domain>/`, as a clickable link
- the absolute path of `/tmp/<domain>_new_links.txt`, as a clickable link
- the failed URLs, one per line, written to `/tmp/<domain>_error_urls.txt`, as a clickable link

**Go idle.**
- The main agent reads the files and decides between another scrape round and Step 3.

## Step 3 — Cleanup

**Starts when the main agent says to go to Step 3, and at no other moment.**

**Leaving noise in beats cutting content out.**
- A span that is arguable stays.

**One defect class at a time, start to finish, before the next one is named.**

### Stage 1 — Sample

**Pick one `.md` from `/tmp/<domain>/` and read it end to end with the Read tool, every line.**

**Name the defect classes you see in it.**
- Each class carries the anchor that identifies it.

### Stage 2 — One script per class

**`/tmp/clean_<class>_<domain>.py`, ~20-30 LOC, `python3`.**
- Dry-run is the default, `--apply` is its own separate run.

**The script writes two things.**
- The cleaned `.md` files, in place, under `--apply` only.
- `/tmp/cut_<class>_<domain>.md`, every removed span verbatim, always, dry-run included.

**`cut_` format, one block per span, nothing around it.**

```
<filename>:<start_line>-<end_line>
<the removed text, verbatim>
```

**Run it dry first.**
- The `.md` files stay untouched until stage 3 clears the class.

### Stage 3 — Read what you cut, then apply

**Read `/tmp/cut_<class>_<domain>.md` with the Read tool, `offset` stepped across the file.**
- Step until you have seen spans from the start, the middle and the end.

**A span you cannot place as noise stays.**
- Narrow the anchor, run dry again, and read again.

**When every span reads as noise, back up and apply.**
- Copy the whole `/tmp/<domain>/` to `/tmp/<domain>_PRE_<class>_BACKUP/`, then run `--apply`.

### Stage 4 — Verify, then take the next class

**Re-scan the class over `/tmp/<domain>/` and expect zero remaining hits.**

**Read 10-15 lines from the middle of two cleaned files.**

**Confirm every file still carries its `<!-- source: URL -->` line.**

**Then go to stage 1 for the next class.**

### Report

**Per class: the anchor, files touched, spans removed, chars removed, and the `cut_` path.**

**A file that holds no content after cleaning is named, kept on disk, and left for the main agent.**
