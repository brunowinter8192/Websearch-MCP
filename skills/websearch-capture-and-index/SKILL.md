---
name: websearch-capture-and-index
description:
---

# Capture-and-Index — Skill

**Several domains run one by one.**
- Take one domain through Step 1 to Step 4, then start over at Step 1 with the next.

**Scrape failures are reported, never acted on mid-capture.**

## Step 1 — Discovery

**Input, named by the main agent with the go.**
- `<seed_url>` holds one seed URL per domain.

1. Run discovery against the seed URL.

   ```bash
   cd /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch
   ./venv/bin/python cli.py discover_urls "<seed_url>" --url-file /tmp/<domain>_urls.txt
   ```

2. 🛑 STOP and report:
   - the absolute path of `/tmp/<domain>_urls.txt`, one URL per line, as a clickable link

3. Go idle.

## Step 2 — Scrape

**Input, named by the main agent with the go.**
- `<culled_url_file>` holds the URLs to scrape.

1. Scrape the culled list.

   ```bash
   cd /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch
   ./venv/bin/python -m src.crawler.pipe_scraper \
       --url-file <culled_url_file> \
       --output-dir /tmp/<domain>/ > /tmp/<domain>_scrape.log 2>&1
   ```

2. Go idle once that command has been run.
   - It auto-backgrounds, and `/tmp/<domain>_scrape.log` carries its summary line when it returns.

3. Split the link file pipe_scraper wrote.

   ```bash
   comm -13 <(sort <discovery_url_file>) <(sort /tmp/<domain>_links.txt) > /tmp/<domain>_new_links.txt
   comm -12 <(sort <discovery_url_file>) <(sort /tmp/<domain>_links.txt) > /tmp/<domain>_known_links.txt
   ```

4. 🛑 STOP and report:
   - scraped OK, errors, duration
   - the absolute path of `/tmp/<domain>/`, as a clickable link
   - the absolute path of `/tmp/<domain>_new_links.txt`, as a clickable link
   - the failed URLs, one per line, written to `/tmp/<domain>_error_urls.txt`, as a clickable link

5. Go idle.
   - The main agent reads the files and decides between another scrape round and Step 3.

## Step 3 — Cleanup

**Starts when the main agent says to go to Step 3, and at no other moment.**

**Leaving noise in beats cutting content out.**
- A span that is arguable stays.

**One defect class at a time, start to finish, before the next one is named.**

### Stage 1 — Sample

1. Pick one `.md` from `/tmp/<domain>/` and read it end to end with the Read tool, every line.

2. Name the defect classes you see in it.
   - Each class carries the anchor that identifies it.

### Stage 2 — One script per class

1. Write `/tmp/clean_<class>_<domain>.py`, `python3`.
   - Dry-run is the default, `--apply` is its own separate run.

2. Have the script write two things.
   - the cleaned `.md` files, in place, under `--apply` only
   - `/tmp/cut_<class>_<domain>.md`, every removed span verbatim, always, dry-run included

3. Give `cut_` one block per span, nothing around it.

   ```
   <filename>:<start_line>-<end_line>
   <the removed text, verbatim>
   ```

4. Run it dry first.
   - The `.md` files stay untouched until stage 3 clears the class.

### Stage 3 — Read what you cut, then apply

1. Read `/tmp/cut_<class>_<domain>.md` with the Read tool, `offset` stepped across the file.
   - Step until you have seen spans from the start, the middle and the end.

2. Keep every span you cannot place as noise.
   - Narrow the anchor, run dry again, and read again.

3. Back up and apply once every span reads as noise.
   - Copy the whole `/tmp/<domain>/` to `/tmp/<domain>_PRE_<class>_BACKUP/`, then run `--apply`.

### Stage 4 — Verify, then take the next class

1. Re-scan the class over `/tmp/<domain>/` and expect zero remaining hits.

2. Read 10-15 lines from the middle of two cleaned files.

3. Confirm every file still carries its `<!-- source: URL -->` line.

4. Go to stage 1 for the next class.

## Step 4 — Report

**Report that the cleanup is done, and go idle.**
- the absolute path of `/tmp/<domain>/`, holding the cleaned `.md` files, as a clickable link
