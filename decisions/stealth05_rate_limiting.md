# Stealth Layer 5: Rate-Limiting

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**`delay_between_queries: 0`** — kein Delay zwischen Queries.

Rationale: 2026-04-07 Baseline lief mit 0 Delay und lieferte 30/30. Ein 10s Delay wurde 2026-04-16 als defensiver Wert eingebaut — ohne Evidenz, dass er nötig war. Im neuen Smoke-Stack wurde auf 0 zurückgesetzt.

**`page_load_timeout: 20`** — maximale Wartezeit pro Navigation.

**`consent_settle: 2.0`** — 2s Settle nur bei Consent-Handling (nicht zwischen normalen Queries).

**`wait_for_results.max_cycles: 15`, `interval_seconds: 1.0`** — bis zu 15 Sekunden Warten auf DOM-Ergebnisse pro Query.

Effektives Timing pro Query: Navigation (~1–2s) + DOM-Wait (0–15s, typisch 1–2s) + Tab-Open/Close (~0.1s). Kein expliziter Delay dazwischen.

Gesamte 30-Query-Run: ~2.5 Minuten (aus Baseline-Report `smoke_20260421_022343.md`).

### Detection Surface

Was Layer 5 prüft:

| Signal | Was erkannt wird | Unser Control |
|--------|-----------------|---------------|
| X Requests/Zeitfenster (IP) | Rate > Threshold → 429 / Redirect zu /sorry/ | ❌ kein Delay — Rate ist hoch |
| Request-Pattern | Zu regelmäßig (kein Jitter) | ❌ natürliches Jitter durch DOM-Wait variiert |
| Burst-Detection | Viele Requests in kurzer Zeit | ❌ 30 Queries in ~2.5min = ~12 Req/min |

## Evidenz

### Mojeek Rate-Limit (2026-04-09)

- Exakt 15 Requests pro ~60s Sliding Window
- Ab Request 16: HTTP 403 "automated queries"
- IP-basiert — `use_context` (Browser-Rotation) hilft nicht
- Unabhängig von Sprache der Query

### Google Rate-Tolerance (2026-04-07 + 2026-04-21)

- 30/30 mit 0 Delay in ~2.5min — kein Rate-Limit
- Google scheint bei 12 Req/min (mit realem DOM-Wait-Jitter) kein Blocking zu aktivieren
- Stress-Test über mehrere Back-to-Back Runs noch nicht durchgeführt

## Recommendation (SOLL)

Pending — 0 Delay ist die korrekte Baseline. Delay nur einführen wenn Stress-Tests einen konkreten Rate-Limit-Break zeigen.

**Stress-Test-Protokoll:** Mehrere Runs back-to-back ohne Cooldown — erst wenn Google anfängt zu blocken, ist Rate-Limiting die Hypothese.

## Offene Fragen

- Google: Wo ist die tatsächliche Rate-Limit-Schwelle? (noch nicht stress-getestet über mehrere Runs)
- Jitter durch DOM-Wait: Reicht die natürliche Varianz (1–15s pro Query) um Regularity-Detection zu umgehen?
