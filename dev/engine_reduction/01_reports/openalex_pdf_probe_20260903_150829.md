# OpenAlex PDF-URL Availability Probe (Milestone 1) — 20260903_150829

Measurement only — no src/ touched, no wiring. Direct httpx against `https://api.openalex.org/works?search=<q>&per_page=100`, no `mailto`, no API key.

## Per-Query Counts

| # | Query | Total | pdf_url | landing-only | no OA | Top-10 total | Top-10 pdf_url | Top-10 landing-only | Top-10 no OA |
|---|-------|------:|--------:|--------------:|------:|--------------:|----------------:|----------------------:|--------------:|
| 1 | WHO environmental noise guidelines European Region 2018 | 100 | 86 | 13 | 1 | 10 | 5 | 4 | 1 |
| 2 | WHO Night Noise Guidelines for Europe 2009 pdf | 100 | 87 | 12 | 1 | 10 | 8 | 2 | 0 |
| 3 | Basner McGuire systematic review environmental noise effects | 100 | 92 | 7 | 1 | 10 | 9 | 1 | 0 |
| 4 | iris.who.int environmental noise guidelines European region  | 56 | 48 | 8 | 0 | 10 | 8 | 2 | 0 |
| 5 | Basner McGuire 2018 IJERPH 15 519 sleep pdf full text | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 |
| 6 | web content extraction quality evaluation benchmark | 100 | 95 | 5 | 0 | 10 | 10 | 0 | 0 |
| 7 | clothing lifespan wears per garment replacement rate study | 100 | 92 | 7 | 1 | 10 | 9 | 1 | 0 |
| **All** | | **557** | **501** | **52** | **4** | **61** | **50** | **10** | **1** |

## Type Breakdown of pdf_url-Present Works (full result set)

**Q1** `WHO environmental noise guidelines European Region 2018`: article=71, review=12, book=2, report=1
**Q2** `WHO Night Noise Guidelines for Europe 2009 pdf`: article=77, review=5, editorial=1, book=1, report=1, dissertation=1, preprint=1
**Q3** `Basner McGuire systematic review environmental noise effects`: article=78, review=11, book-chapter=2, preprint=1
**Q4** `iris.who.int environmental noise guidelines European region `: article=26, dissertation=9, book=4, paratext=3, review=2, report=2, data-paper=1, conference-paper=1
**Q5** `Basner McGuire 2018 IJERPH 15 519 sleep pdf full text`: review=1
**Q6** `web content extraction quality evaluation benchmark`: article=68, conference-paper=15, preprint=9, review=2, book=1
**Q7** `clothing lifespan wears per garment replacement rate study`: article=71, report=4, dissertation=4, other=4, book=4, conference-paper=2, preprint=2, book-chapter=1

## Eyeball: First 10 Results — Chosen URL vs best_oa_location.pdf_url

### Q3: `Basner McGuire systematic review environmental noise effects on sleep 2018`

| # | Title | Type | Chosen URL (_pick_url) | best_oa_location.pdf_url |
|---|-------|------|-------------------------|---------------------------|
| 1 | Environmental noise in hospitals: a systematic review | review | https://doi.org/10.1007/s11356-021-13211-2 | https://link.springer.com/content/pdf/10.1007/s11356-021-13211-2.pdf |
| 2 | Noise pollution and human cognition: An updated systematic review and meta-analysis of recent eviden | review | https://doi.org/10.1016/j.envint.2021.106905 | https://www.sciencedirect.com/science/article/pii/S0160412021005304/pdf |
| 3 | Traffic Noise and Mental Health: A Systematic Review and Meta-Analysis | review | https://doi.org/10.3390/ijerph17176175 | https://www.mdpi.com/1660-4601/17/17/6175/pdf |
| 4 | Sleep deprivation, vigilant attention, and brain function: a review | article | https://doi.org/10.1038/s41386-019-0432-6 | https://www.nature.com/articles/s41386-019-0432-6.pdf |
| 5 | Evidence for Environmental Noise Effects on Health for the United Kingdom Policy Context: A Systemat | review | https://doi.org/10.3390/ijerph17020393 | https://www.mdpi.com/1660-4601/17/2/393/pdf?version=1579179719 |
| 6 | Sleep deficiency and chronic pain: potential underlying mechanisms and clinical implications | article | https://doi.org/10.1038/s41386-019-0439-z | https://www.nature.com/articles/s41386-019-0439-z.pdf |
| 7 | Adverse Cardiovascular Effects of Traffic Noise with a Focus on Nighttime Noise and the New WHO Nois | article | https://doi.org/10.1146/annurev-publhealth-081519-062400 |  |
| 8 | Road Traffic Noise Exposure and Depression/Anxiety: An Updated Systematic Review and Meta-Analysis | review | https://doi.org/10.3390/ijerph16214134 | https://www.mdpi.com/1660-4601/16/21/4134/pdf?version=1572148611 |
| 9 | Cerebral consequences of environmental noise exposure | article | https://doi.org/10.1016/j.envint.2022.107306 | https://www.sciencedirect.com/science/article/pii/S0160412022002331/pdf |
| 10 | Evidence Relating to Environmental Noise Exposure and Annoyance, Sleep Disturbance, Cardio-Vascular  | article | https://doi.org/10.3390/ijerph17093016 | https://www.mdpi.com/1660-4601/17/9/3016/pdf?version=1587914235 |

### Q6: `web content extraction quality evaluation benchmark`

| # | Title | Type | Chosen URL (_pick_url) | best_oa_location.pdf_url |
|---|-------|------|-------------------------|---------------------------|
| 1 | The Pascal Visual Object Classes (VOC) Challenge | article | https://doi.org/10.1007/s11263-009-0275-4 | https://www.research.ed.ac.uk/files/7879113/ijcv_voc09.pdf |
| 2 | Microplastics in seafood: Benchmark protocol for their extraction and characterization | article | https://doi.org/10.1016/j.envpol.2016.05.018 | https://ars.els-cdn.com/content/image/1-s2.0-S0269749116303979-fx1_lrg.jpg |
| 3 | Soil quality – A critical review | article | https://doi.org/10.1016/j.soilbio.2018.01.030 | https://www.sciencedirect.com/science/article/pii/S0038071718300294/pdf |
| 4 | Metrics for evaluating 3D medical image segmentation: analysis, selection, and tool | article | https://doi.org/10.1186/s12880-015-0068-x | https://bmcmedimaging.biomedcentral.com/counter/pdf/10.1186/s12880-015-0068-x |
| 5 | Evaluation campaigns and TRECVid | conference-paper | https://doi.org/10.1145/1178677.1178722 | https://publications.tno.nl/publication/104201/sbHlB5/kraaij-2006-evaluation.pdf |
| 6 | BioCreative V CDR task corpus: a resource for chemical disease relation extraction | article | https://doi.org/10.1093/database/baw068 | https://academic.oup.com/database/article-pdf/doi/10.1093/database/baw068/8224483/baw068.pdf |
| 7 | A benchmark for comparison of cell tracking algorithms | article | https://doi.org/10.1093/bioinformatics/btu080 | https://academic.oup.com/bioinformatics/article-pdf/30/11/1609/48928140/bioinformatics_30_11_1609.pdf |
| 8 | CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environment | article | https://doi.org/10.3390/s23135941 | https://www.mdpi.com/1424-8220/23/13/5941/pdf?version=1687924880 |
| 9 | Knowledge graph refinement: A survey of approaches and evaluation methods | article | https://doi.org/10.3233/sw-160218 | https://content.iospress.com:443/download/semantic-web/sw218?id=semantic-web%2Fsw218 |
| 10 | Reliable B Cell Epitope Predictions: Impacts of Method Development and Improved Benchmarking | article | https://doi.org/10.1371/journal.pcbi.1002829 | https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1002829&type=printable |
