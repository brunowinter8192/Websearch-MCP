---
name: websearch-pdf
description:
---

# PDF → MD → Index — Skill

Interactive. The USER runs the convert command; Claude does ONLY: naming, cleanup, index.
ONE command converts ALL PDFs in the batch sequentially, each as a whole document,
MinerU `vlm-auto-engine` (mlx).

## Paths
- MINERU = `~/Documents/ai/Mineru/venv/bin/python ~/Documents/ai/Mineru/workflow.py`
- COLLECTION = `trading-reference` (default; confirm only if user names another)
- OUTPUT_DIR = `~/Documents/ai/Meta/ClaudeCode/cli/rag-cli/data/documents/<COLLECTION>/`
- COMMAND FILE = `~/Downloads/<batch>_pdf_commands.md`

## Rule
The CONVERT command → USER runs it. Claude runs: naming, cleanup scripts, `rag-cli index`.

## Phase 0 — Naming + skip-check (CLAUDE)
1. Per PDF: assign a PascalCase STEM, alphanumeric + underscore ONLY — no brackets, parentheses,
   dots, commas, spaces. Rename the source PDF in place → `<STEM>.pdf`.
2. Skip-check: drop any PDF that already has `<OUTPUT_DIR>/<STEM>.md` — only un-converted PDFs go
   into the command.
3. Backend is always `vlm-auto-engine` (mlx).

## Phase 1 — MinerU convert (USER runs, ONE command for the whole batch)
Write the COMMAND FILE: ONE block listing ALL non-skipped PDFs (whole document):
```
mkdir -p <OUTPUT_DIR>
PYTHONUNBUFFERED=1 ~/Documents/ai/Mineru/venv/bin/python ~/Documents/ai/Mineru/workflow.py convert \
  --pdf "<PDF1>" "<PDF2>" "<PDF3>" ... \
  --out-dir <OUTPUT_DIR> 2>&1 | tee /tmp/<batch>_mineru.log
```
- Output: flat `<OUTPUT_DIR>/<STEM>.md` per PDF.
- USER runs the block, reports done.

## Phase 2 — Clean (CLAUDE)
Run on each `<OUTPUT_DIR>/<STEM>.md`. Audit FIRST — sample the hits, then strip.

Per-class detection + action:
- **A — lost formula (UNRECOVERABLE → do NOT clean):** `??`, `` (U+FFFD), empty/`?`-containing
  `<sub>`/`<sup>` (`<su[bp]>[[:space:]]*</su[bp]>|<su[bp]>[^<]*\?[^<]*</su[bp]>`), whitespace-only
  `$$…$$` blocks (split on `$$`, test odd segments). Any A hit → do NOT clean.
  **Report the symbol/page to the user.**
- **B — spaced math (RECOVERABLE → de-space):** `_ {`, `^ {`, `\ [a-z]( [a-z])+`, spaced single-char
  runs `([A-Za-z] ){3,}[A-Za-z]`. Collapse runs to real tokens (`\mathrm { a r g m i n }` →
  `\mathrm{argmin}`). Invariant: alphanumeric-char count EXACTLY stable; word count drops.
- **C — encoding (RECOVERABLE → unescape):** HTML entities
  `&(amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+);`, mojibake `Ã.`/`â€`. Entity count → 0.
- **D — prose char-typos:** ignore. Pervasive prose garble → treat as A, report.
- **E — backmatter (MANDATORY STRIP):** from the first
  References/Bibliography/Index/Symbols/Abbreviations/Nomenclature heading in the last ~40% (or
  headingless reference run: most non-blank lines match `\(\d{4}[a-z]?\)`/`^Surname, Init.`; index run:
  `,\s*\d+([–-]\d+)?`) through EOF. Confirm 3 lines above the cut are real content. Do NOT cut numbered
  content subsections (heading text starts with a digit) or per-chapter "Bibliographic Notes".
- **F — table markup (RECOVERABLE → pipe-text):** MinerU `<table>` HTML, markup ratio > 50%. Strip
  tags, one row per `</tr>`, cells `|`-separated, content unchanged, no truncation. Validate cell-text
  token set unchanged.
- **G — image tags (MANDATORY STRIP):** `!\[[^\]]*\]\([^)]*\)` → remove every match. Drop lines
  emptied by the removal; collapse 3+ consecutive blank lines → 1. Re-scan: count → 0.
- **H — block noise (MANDATORY STRIP):** consecutive runs ≥ 2 of bare fence lines (line = optional
  whitespace + 3+ backticks + optional whitespace, nothing else) → remove the whole run. KEEP isolated
  fences and language-tagged openers (```` ```txt ````, ```` ```csv ````).
  Separator lines: on the space-stripped line, if the most-common char ∈ `=#-~*_.+` is > 70% of chars
  AND length ≥ 20 → remove the line. Re-scan: max consecutive bare-fence run = 1.
- **I — run-on tokens (CONDITIONAL → user decision):** whitespace-split; flag tokens ≥ 46 chars with
  alpha-ratio > 0.7, excluding tokens containing `\` / `http` / `/`. Any flagged token > 2000 chars →
  STOP, list doc + token to the user, wait for decision. All flagged ≤ 2000 chars → leave in place, do
  NOT strip.
- **J — oversized spans (MANDATORY):** scan BOTH granularities, report every hit with line number +
  first 200 chars:
  ```bash
  awk '{ if (length($0) > 1000) print NR, length($0) }' "$MD"                       # long lines
  awk 'BEGIN{RS="\n\n"} { gsub(/\n/," "); if (length($0) > 1000) print NR, length($0) }' "$MD"  # long blocks
  ```
  Per hit, classify and act:
  - **repeated-char run** (`(.)\1{39,}`) → collapse to 3 chars:
    `re.sub(r"(.)\1{39,}", lambda m: m.group(1)*3, text)`.
  - **real prose/table/formula** → leave in place.
  Re-scan: report max line length + max block length; name every remaining > 1000 span as real content.

Prose window (every md): pull 1–2 body lines (len > 70, starts alpha, > 10 spaces, alpha-ratio > 0.78)
from the middle third and READ. Coherent → pass; garbled → A → report (unrecoverable).

Per-issue scripts: one `/tmp/fix_<issue>_<STEM>.py` each, test on the file, re-scan that class to 0,
spot-check 10–15 middle lines. Preserve source content; overwrite in place; back up to
`/tmp/backup_<STEM>.md` first.

## Phase 3 — Index (CLAUDE)
```
rag-cli index --collection <COLLECTION>
```
Incremental (hash-skip). Must be the ONLY command in its Bash call — assignments, a `cd` and a
redirect may accompany it, nothing else, no command substitution.

When it returns: READ THE OUTPUT IN FULL before reporting or diagnosing.
The error sits in the FIRST line. A stalled chunk counter = run ENDED, never "slow".

`HTTP 400 … exceeds the available context size` → re-run class J's scan on the named document, fix,
re-index.

Report files indexed + chunks. Confirm docs in the collection.
