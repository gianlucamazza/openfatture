# Scenario D · Operazioni Batch & Import/Export (Storyboard)

**Versione:** v2025.02.03
**Owner:** Operations Team (lead: Marco Greco)
**Durata target:** 2'15" ± 10s

## Sequenza Shot
| # | Durata | Video | Audio/VO | Overlay/Note |
|---|--------|-------|----------|--------------|
| 1 | 0:04 | Logo animato + titolo "Batch Operations" | SFX intro breve | Badge "Scalabilità" |
| 2 | 0:10 | Speaker on cam | "Importazione massiva clienti e fatture da CSV" | CTA "Automazione" |
| 3 | 0:15 | Esplora file CSV in editor (VS Code) | "Formato CSV semplice con colonne standard" | Zoom su header CSV |
| 4 | 0:20 | Terminale: `openfatture batch import examples/batch/clients.csv --dry-run` | "Modalità dry-run: validazione senza modifiche" | Callout "Safe Mode" |
| 5 | 0:18 | Output dry-run con validazione | "Rilevamento errori: P.IVA duplicata, CAP mancante" | Highlight errori in rosso |
| 6 | 0:12 | Correzione CSV (edit rapido) | "Fix degli errori identificati" | Fast-forward effect |
| 7 | 0:20 | Terminale: `openfatture batch import examples/batch/clients.csv` | "Import effettivo dopo validazione" | Progress bar animation |
| 8 | 0:15 | Riepilogo import: 5 clienti aggiunti | "Conferma operazioni completate" | Badge "5 clients imported" |
| 9 | 0:18 | Terminale: `openfatture batch import examples/batch/invoices.csv --dry-run` | "Batch import fatture con dry-run" | Lower-third "Best Practice" |
| 10 | 0:13 | Outro + CTA report | "Dashboard statistiche accessibile da CLI" | Link scenario E |

## Note Produzione
- **File CSV**: preparare in `examples/batch/` con casi realistici:
  - `clients.csv`: 5 clienti (1 con errore P.IVA duplicata)
  - `invoices.csv`: 10 fatture Q1 2025
- **Validazione**: mostrare sia successi che errori per realismo
- **Screen capture**: split-screen opzionale (CSV editor + terminale)
- **Timing**: dry-run è veloce, import reale richiede 2-3s per animazione

## Asset Necessari
- File CSV esempio in `examples/batch/` (creare se mancanti)
- Database demo reset per evitare conflitti ID
- Lower-third "Dry-run: Safe validation" callout
- Badge "X records imported" dinamico

## Checklist Pre-shoot
- [ ] Creare/verificare CSV in `examples/batch/` con dati realistici
- [ ] Testare comando batch con `--dry-run` e senza
- [ ] Verificare output errori leggibile e formattato
- [ ] Preparare CSV con errore intenzionale per demo validazione
- [ ] Marker Resolve: Intro, CSV, Dry-run, Fix, Import, Fatture, Outro

## Post-produzione
- Marker timeline: Intro (0:00), Explore CSV (0:14), Dry-run (0:29), Fix (0:47), Import (0:59), Invoices (1:34), Outro (2:02)
- Sottotitoli IT
- Export: Master ProRes + H.264 1080p + tutorial clip per docs
- Nota: includere link a template CSV scaricabili nel video description
