# Stealth Layer 2: Behavioral

## Status Quo (IST)

### Baseline Mapping (2026-04-21)

Basis: `dev/search_pipeline/config.yml` + `dev/search_pipeline/01_google_smoke.py`.

**ON:**
- `block_popups: true` — blockiert Pop-up-Fenster (reduziert unerwartete Interaktionen)
- `block_notifications: true` — blockiert Notification-Permission-Dialoge

**OFF / NICHT IMPLEMENTIERT:**
- Keine Mausbewegungen zwischen Queries
- Keine Scroll-Simulation
- Kein humanisiertes Klick-Muster
- Kein Typing (keine Formularinteraktion — Navigation direkt via URL)
- `delay_between_queries: 0` — kein Delay (Timing-Signal vorhanden, siehe Layer 5)
- `consent_settle: 2.0` — einzige Wartezeit, nur bei Consent-Handling

Der Baseline-Stack navigiert ausschließlich via `tab.go_to(url)` — kein DOM-Interaktion außer beim Consent-Fallback (`btn.click()`). Es gibt keine humanisierten Behavioral-Signale.

### Detection Surface

Was Layer 2 prüft:

| Signal | Was erkannt wird | Unser Control |
|--------|-----------------|---------------|
| Request-Timing | Zu schnell, zu regelmäßig — bot-typisch | ❌ 0 Delay zwischen Queries |
| Mausbewegung | Fehlt komplett | ❌ nicht implementiert |
| Scroll-Verhalten | Fehlt | ❌ nicht implementiert |
| Klick-Muster | Zu präzise / sofort (kein Human-Jitter) | ❌ bei Consent-Button-Click |
| Tab-Aktivität | Neue Tabs öffnen/schließen ohne Idle | ⚠️ pro Query neuer Tab, sofort navigiert |

## Evidenz

Keine quantitativen Behavioral-Tests durchgeführt. Baseline-30/30 mit komplett OFF bestätigt, dass Google auf Layer 2 bei moderatem Traffic nicht aktiv blockiert.

## Recommendation (SOLL)

Pending — wird durch Stress-Test-Iterationen bestimmt. Erst wenn Stress-Break eintritt und Layer 5 (Rate-Limiting) ausgeschlossen ist, ist Behavioral der nächste Kandidat.

## Offene Fragen

- Google: Beginnt Behavioral-Detection erst bei hohem Traffic (>100 Queries pro Session) oder schon früher?
- Ist der 0-Delay-Effekt Layer 2 (Timing) oder Layer 5 (Rate-Limit) — vermutlich Layer 5 für IP-Blocking, Layer 2 für Session-Score-Erhöhung

## Quellen

- Kein spezifisches Research für Layer 2 durchgeführt
