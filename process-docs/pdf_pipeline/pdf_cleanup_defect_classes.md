# PDF Cleanup Defect Classes — MinerU mlx vlm-auto-engine (2026-06-24)

Process memory behind the `searxng-cli-pdf` skill Phase-2 cleanup classes. Batch: 13 methodology papers → `trading-reference`. Convert backend: MinerU `vlm-auto-engine` (mlx) — the only backend that carried the batch.

## What happened

Pass 1 cleaned classes A–F (the then-existing skill spec) on all 13, indexed. User inspection of Tsay2010 surfaced gross-noise classes the A–F audit + prose-window verification completely missed. Pass 2 added image/fence/separator stripping. Skill extended with classes G/H/I. All 13 indexed clean.

## Why pass-1 verification was blind to the noise

A–F audit scanned specific signatures (math/entities/tables/backmatter). Prose-window coherence check sampled only "content-looking" lines (`len>70`, `alpha-ratio>0.78`) — which by construction FILTERS OUT noise lines (a ` ``` ` or `=====` line is short, low-alpha). The verification method could not see exactly the class that dominated the worst file. Lesson: audit must include a gross-noise-line fraction, not only content-signature counts.

## Convert quality — mlx vlm-auto-engine (two-tier)

| Aspect | Quality | Recoverable? |
|---|---|---|
| Math (`$…$`/`$$…$$`) | spaced (`h _ {t}`) but structurally intact | YES — de-space (class B), alnum-count invariant holds |
| Prose (bulk) | coherent | n/a |
| Prose (space-collapse regions) | all spaces dropped, e.g. `EFFECTIVENUMBEROFOBSERVATIONS`, `5.1.Letr_tbethelogreturn…` | NO — word boundaries lost, no safe re-segmentation |
| Structural noise | fence-runs, separator lines, image tags | YES — strip (G/H) |
| Tables | MinerU `<table>` HTML | YES — pipe-text (class F) |

Math example that came out clean after de-space: `s_{T,2}\sum_{t=1}^{T}K_{h}\left(x-x_{t}\right)y_{t}`.

## Per-file defect scan (post-pass-1, the not-yet-indexed set)

| File | lines | images (G) | ref/ex/idx (H)* | bare-fence noise (J) | run-on tok (I), max chars |
|---|---|---|---|---|---|
| Tsay2010 | 27 833 | 361 | 35 (Index/#EXERCISES/#REFERENCES) | 7 092 (max run 6 880×) = 25.5% | 1 055 (1070) |
| LopezLira2023 | 2 707 | 15 | 1 (References) | 0 | 23 (1016) |
| Hamilton1994 | 37 430 | 69 | 0 (appendices=content) | 0 | 0 |
| Lahiri2003 | 9 791 | 52 | 1 (References) | 0 | 0 |
| Kou2002 | 708 | 6 | 0 (appendix) | 0 | 0 |
| PolitisRomano1994 | 543 | 10 | 0 (appendix=proofs) | 0 | 0 |
| Tetlock2007 | 453 | 2 | 0 (appendix=methodology) | 0 | 0 |
| Merton1976 | 484 | 0 | 0 | 0 | 0 |

*Scanner over-counted by including `Appendix`. Appendices are CONTENT (proofs/methodology) — must NOT be stripped. Real strip targets (References/Bibliography/Index/Exercises) were almost entirely Tsay + one each in Lahiri/LopezLira.

## Crash vector (rag-cli embedder)

Two index runs hung silently (0% CPU, lock held ~40 min). Proximate cause: `embedding-8b` server had DIED (`rag-cli server errors` → `watchdog_unlinked_dead×2`) — index waited forever on a dead server. Underlying contributor: oversized chunks from the 6 880-line fence run + run-on mega-tokens → embedder OOM/hang. Fix: restart `embedding-8b` + remove the fence/image noise (pass 2). After that all 13 indexed clean, incl. Tsay (998 chunks, was the catastrophe file). The embedding-8b instability itself is a rag-cli infra concern, not a cleanup concern.

## Decisions (crystallized into skill classes G/H/I)

| Topic | Decision | Rationale |
|---|---|---|
| Image tags `![](…)` | STRIP always (class G) | pure noise, never belongs in RAG |
| Bare fence-runs ≥2 + separator lines | STRIP (class H); keep isolated/`lang`-tagged fences | runs are noise; isolated fences wrap real code/CSV blocks (verified: R `kurtosis` output intact) |
| Run-on tokens ≤2000 chars | LEAVE (class I) | unrecoverable but indexes fine; not worth lossy section-drop |
| Run-on tokens >2000 chars | STOP → user decision (class I) | crash risk; human picks drop vs keep |
| Mid-doc / per-chapter References | do NOT strip | on mass we cannot reliably detect where content resumes after the heading; risk cutting real chapters (Tsay has 35 interspersed) |
| Final-backmatter References | STRIP (class E, unchanged) | end-of-doc, safe |
| Appendices | KEEP | content (proofs/methodology), not backmatter |

## Cleanup pass-2 result + final index

Pass 2 stripped (images / fence / separator): Tsay 361/6880/6 (27833→20440), Lahiri 52/0/0, LopezLira 15/0/0, Politis 10/0/0, Kou 6/0/0, Tetlock 2/0/0, Merton 0 (clean), Hamilton1994 untouched (per user, was 78% indexed). Final: all 13 at 100% — Hamilton1994 1772, Tsay 998, Lahiri 666, LopezLira 227, Tetlock 62, Kou 46, Politis 46, Merton 38. Whole `trading-reference` collection (52 docs) fully indexed.

## Scripts (this batch, /tmp — not pinned)

- `/tmp/analyze_trading_ref.py` — full A–J defect scanner (counts + samples per file)
- `/tmp/cleanup2_trading_ref.py` — image/fence/separator stripper (pass 2)
- backups: `/tmp/backup_<stem>.md` (pass 1), `/tmp/backup2_<stem>.md` (pass 2)
