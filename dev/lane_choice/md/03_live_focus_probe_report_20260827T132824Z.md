## Live focus-steal probe (20260827T132824Z)
- Lane: camoufox
- URLs (5): https://www.mainova.de/de/wissenswertes/ratgeber/wasserqualitaet-und-wasserhaerte-mainova-trinkwasser, https://www.verbraucherzentrale.de/wissen/gesundheit-pflege/aerztinnen-und-kliniken/termin-beim-facharzt-nach-4-wochen-so-vermittelt-sie-die-nummer-116-117-12494, https://www.tk.de/techniker/krankheit-und-behandlungen/praxisbesuch-und-klinikaufenthalt/arzt-und-therapeuten-finden/arzttermin-2011842, https://www.personalausweisportal.de/SharedDocs/faqs/Webs/PA/DE/Haeufige-Fragen/3_pin_brief/C3_3_PIN-Brief_verloren.html, https://www.moin.ai/chatbot-lexikon/chatbots-datenschutz-dsgvo
- Worktree root: /Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/watchdog-removal
- Countdown given before the first launch (one countdown for the whole sequence): 10s
- Baseline (expected) frontmost app: `ghostty`
- Instrument 2 target app (AXMain/key-window): `Camoufox`
- Nominal poll interval (sleep() argument, NOT the real cadence — see resolution below): 0.25s

## Per-URL launch spans (elapsed seconds since the countdown ended — instruments polled continuously across all of them, one fresh browser per URL)
- [1] `https://www.mainova.de/de/wissenswertes/ratgeber/wasserqualitaet-und-wasserhaerte-mainova-trinkwasser`: t=0.0s-10.61s (wall 10.61s), exit code 0
- [2] `https://www.verbraucherzentrale.de/wissen/gesundheit-pflege/aerztinnen-und-kliniken/termin-beim-facharzt-nach-4-wochen-so-vermittelt-sie-die-nummer-116-117-12494`: t=10.61s-20.78s (wall 10.17s), exit code 0
- [3] `https://www.tk.de/techniker/krankheit-und-behandlungen/praxisbesuch-und-klinikaufenthalt/arzt-und-therapeuten-finden/arzttermin-2011842`: t=20.78s-29.09s (wall 8.31s), exit code 0
- [4] `https://www.personalausweisportal.de/SharedDocs/faqs/Webs/PA/DE/Haeufige-Fragen/3_pin_brief/C3_3_PIN-Brief_verloren.html`: t=29.09s-37.21s (wall 8.12s), exit code 0
- [5] `https://www.moin.ai/chatbot-lexikon/chatbots-datenschutz-dsgvo`: t=37.21s-50.09s (wall 12.88s), exit code 0

## Overall verdict (whole sequence, all URLs pooled)
- Instrument 1 (frontmost app): 81 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2 (AXMain key-window): 81 samples, 72 deviations, longest continuous deviation 12.37s

## Observed sampling resolution (real, not nominal — see sample_gaps/instrument_resolution_stats)
- Instrument 1: mean interval 0.579s, max gap 3.59s, effective rate ~1.73 samples/s
- Instrument 2: mean interval 0.579s, max gap 3.59s, effective rate ~1.73 samples/s
- A 0-deviation line above only covers the span actually sampled at this cadence — a run shorter than the max gap between two samples is not guaranteed to be caught by either instrument.

## Instrument 1 — deviation offsets (0 of 81)
NONE

## Instrument 2 — deviation offsets (72 of 81)
t=6.69s, t=7.06s, t=7.44s, t=7.81s, t=8.19s, t=8.56s, t=8.95s, t=9.33s, t=13.55s, t=13.92s, t=14.3s, t=14.69s, t=15.07s, t=15.44s, t=15.82s, t=16.2s, t=16.57s, t=16.94s, t=17.31s, t=17.69s, t=18.07s, t=18.46s, t=18.85s, t=23.16s, t=23.54s, t=23.92s, t=24.3s, t=24.67s, t=25.06s, t=25.44s, t=25.82s, t=26.21s, t=26.59s, t=26.97s, t=27.34s, t=27.73s, t=28.11s, t=32.37s, t=32.76s, t=33.15s, t=33.53s, t=33.91s, t=34.3s, t=34.68s, t=35.06s, t=35.44s, t=35.83s, t=36.22s, t=40.22s, t=40.6s, t=40.99s, t=41.37s, t=41.75s, t=42.14s, t=42.52s, t=42.91s, t=43.3s, t=43.67s, t=44.06s, t=44.45s, t=44.84s, t=45.24s, t=45.62s, t=46.0s, t=46.38s, t=46.75s, t=47.11s, t=47.48s, t=47.85s, t=48.27s, t=48.69s, t=49.09s

## Per-URL verdict (instrument samples sliced to each URL's own launch span above)
### `https://www.mainova.de/de/wissenswertes/ratgeber/wasserqualitaet-und-wasserhaerte-mainova-trinkwasser` — t=0.0s-10.61s, exit code 0
- Instrument 1: 10 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2: 10 samples, 8 deviations, longest continuous deviation 3.04s

### `https://www.verbraucherzentrale.de/wissen/gesundheit-pflege/aerztinnen-und-kliniken/termin-beim-facharzt-nach-4-wochen-so-vermittelt-sie-die-nummer-116-117-12494` — t=10.61s-20.78s, exit code 0
- Instrument 1: 17 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2: 17 samples, 15 deviations, longest continuous deviation 5.77s

### `https://www.tk.de/techniker/krankheit-und-behandlungen/praxisbesuch-und-klinikaufenthalt/arzt-und-therapeuten-finden/arzttermin-2011842` — t=20.78s-29.09s, exit code 0
- Instrument 1: 16 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2: 16 samples, 14 deviations, longest continuous deviation 5.36s

### `https://www.personalausweisportal.de/SharedDocs/faqs/Webs/PA/DE/Haeufige-Fragen/3_pin_brief/C3_3_PIN-Brief_verloren.html` — t=29.09s-37.21s, exit code 0
- Instrument 1: 12 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2: 12 samples, 11 deviations, longest continuous deviation 4.24s

### `https://www.moin.ai/chatbot-lexikon/chatbots-datenschutz-dsgvo` — t=37.21s-50.09s, exit code 0
- Instrument 1: 25 samples, 0 deviations, longest continuous deviation 0.0s
- Instrument 2: 25 samples, 24 deviations, longest continuous deviation 9.26s

## Instrument 1 — full sample series
- t=6.35s: ghostty
- t=6.73s: ghostty
- t=7.11s: ghostty
- t=7.48s: ghostty
- t=7.85s: ghostty
- t=8.23s: ghostty
- t=8.6s: ghostty
- t=8.98s: ghostty
- t=9.36s: ghostty
- t=9.78s: ghostty
- t=13.19s: ghostty
- t=13.59s: ghostty
- t=13.96s: ghostty
- t=14.35s: ghostty
- t=14.73s: ghostty
- t=15.11s: ghostty
- t=15.49s: ghostty
- t=15.87s: ghostty
- t=16.27s: ghostty
- t=16.65s: ghostty
- t=17.05s: ghostty
- t=17.44s: ghostty
- t=17.84s: ghostty
- t=18.23s: ghostty
- t=18.64s: ghostty
- t=19.04s: ghostty
- t=19.44s: ghostty
- t=22.79s: ghostty
- t=23.19s: ghostty
- t=23.58s: ghostty
- t=23.95s: ghostty
- t=24.34s: ghostty
- t=24.72s: ghostty
- t=25.1s: ghostty
- t=25.47s: ghostty
- t=25.87s: ghostty
- t=26.25s: ghostty
- t=26.63s: ghostty
- t=27.0s: ghostty
- t=27.39s: ghostty
- t=27.78s: ghostty
- t=28.16s: ghostty
- t=28.56s: ghostty
- t=32.01s: ghostty
- t=32.42s: ghostty
- t=32.8s: ghostty
- t=33.2s: ghostty
- t=33.58s: ghostty
- t=33.95s: ghostty
- t=34.33s: ghostty
- t=34.72s: ghostty
- t=35.11s: ghostty
- t=35.49s: ghostty
- t=35.89s: ghostty
- t=36.28s: ghostty
- t=39.87s: ghostty
- t=40.26s: ghostty
- t=40.65s: ghostty
- t=41.03s: ghostty
- t=41.43s: ghostty
- t=41.82s: ghostty
- t=42.24s: ghostty
- t=42.63s: ghostty
- t=43.03s: ghostty
- t=43.43s: ghostty
- t=43.83s: ghostty
- t=44.22s: ghostty
- t=44.63s: ghostty
- t=45.04s: ghostty
- t=45.44s: ghostty
- t=45.84s: ghostty
- t=46.24s: ghostty
- t=46.64s: ghostty
- t=47.03s: ghostty
- t=47.43s: ghostty
- t=47.83s: ghostty
- t=48.26s: ghostty
- t=48.68s: ghostty
- t=49.07s: ghostty
- t=49.55s: ghostty
- t=52.64s: ghostty

## Instrument 2 — full sample series
- t=6.3s: False
- t=6.69s: True
- t=7.06s: True
- t=7.44s: True
- t=7.81s: True
- t=8.19s: True
- t=8.56s: True
- t=8.95s: True
- t=9.33s: True
- t=9.73s: False
- t=13.14s: False
- t=13.55s: True
- t=13.92s: True
- t=14.3s: True
- t=14.69s: True
- t=15.07s: True
- t=15.44s: True
- t=15.82s: True
- t=16.2s: True
- t=16.57s: True
- t=16.94s: True
- t=17.31s: True
- t=17.69s: True
- t=18.07s: True
- t=18.46s: True
- t=18.85s: True
- t=19.32s: False
- t=22.74s: False
- t=23.16s: True
- t=23.54s: True
- t=23.92s: True
- t=24.3s: True
- t=24.67s: True
- t=25.06s: True
- t=25.44s: True
- t=25.82s: True
- t=26.21s: True
- t=26.59s: True
- t=26.97s: True
- t=27.34s: True
- t=27.73s: True
- t=28.11s: True
- t=28.52s: False
- t=31.96s: False
- t=32.37s: True
- t=32.76s: True
- t=33.15s: True
- t=33.53s: True
- t=33.91s: True
- t=34.3s: True
- t=34.68s: True
- t=35.06s: True
- t=35.44s: True
- t=35.83s: True
- t=36.22s: True
- t=39.81s: False
- t=40.22s: True
- t=40.6s: True
- t=40.99s: True
- t=41.37s: True
- t=41.75s: True
- t=42.14s: True
- t=42.52s: True
- t=42.91s: True
- t=43.3s: True
- t=43.67s: True
- t=44.06s: True
- t=44.45s: True
- t=44.84s: True
- t=45.24s: True
- t=45.62s: True
- t=46.0s: True
- t=46.38s: True
- t=46.75s: True
- t=47.11s: True
- t=47.48s: True
- t=47.85s: True
- t=48.27s: True
- t=48.69s: True
- t=49.09s: True
- t=52.59s: False
