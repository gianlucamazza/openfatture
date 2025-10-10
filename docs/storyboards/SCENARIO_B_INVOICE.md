# Scenario B · Creazione Fattura CLI (Storyboard)

**Versione:** v2025.02.03
**Owner:** Backend Guild (lead: Davide Ricci)
**Durata target:** 3'30" ± 10s

## Sequenza Shot
| # | Durata | Video | Audio/VO | Overlay/Note |
|---|--------|-------|----------|--------------|
| 1 | 0:04 | Logo animato + titolo "Fatturazione Elettronica" | SFX intro breve | Paletta brand |
| 2 | 0:15 | Speaker on cam | "Creiamo una fattura elettronica completa da CLI" | CTA "Step 1/5" |
| 3 | 0:20 | Terminale: `openfatture cliente list` | "Verifichiamo i clienti disponibili" | Highlight righe clienti |
| 4 | 0:25 | Terminale: `openfatture fattura crea --interactive` | "Wizard guidato per compilazione campi" | Zoom su validazioni |
| 5 | 0:30 | Compilazione dati fattura (cliente, data, note) | "Selezioniamo cliente e impostiamo parametri" | Callout field obbligatori |
| 6 | 0:35 | Aggiunta righe fattura (prodotti, quantità, IVA) | "Aggiungiamo servizi/prodotti con calcolo automatico" | Lower-third calcolo IVA |
| 7 | 0:20 | Riepilogo e conferma | "Riepilogo totali: imponibile, IVA, totale" | Badge validazione OK |
| 8 | 0:25 | Esportazione XML: `openfatture fattura xml 1` | "Generazione XML FatturaPA conforme SDI" | Preview XML structure |
| 9 | 0:25 | Generazione PDF: `openfatture fattura pdf 1 --template professional` | "PDF per invio cliente" | Zoom su PDF renderizzato |
| 10 | 0:11 | Outro + CTA | "Prossimo: AI Assistant per automazioni" | Link scenario C |

## Note Produzione
- **Dataset**: usare demo con cliente "ACME Innovazione S.r.l." già esistente
- **Prodotti**: "Consulenza GDPR" + "Sviluppo backend API"
- **Output**: fattura 2025-004 (per evitare conflitto con demo seed)
- **Screen capture**: OBS preset standard, terminale fullscreen
- **Callout**: evidenziare validazione campi (P.IVA, Codice destinatario)

## Asset Necessari
- Database demo popolato (`./scripts/reset_demo.sh`)
- Template PDF "professional" verificato
- Sample XML output da mostrare in editor (VS Code con syntax highlight)
- Lower-third callout Figma "Calcolo IVA 22%"

## Checklist Pre-shoot
- [ ] Eseguire `./scripts/reset_demo.sh` e verificare 3 clienti presenti
- [ ] Testare wizard `openfatture fattura crea --interactive` manualmente
- [ ] Verificare output XML valido con validator FatturaPA
- [ ] Testare generazione PDF con template "professional"
- [ ] Preparare marker Resolve: Intro, List, Create, XML, PDF, Outro

## Post-produzione
- Marker timeline: Intro (0:00), Clienti (0:20), Wizard (0:55), Righe (1:30), XML (2:30), PDF (2:55), Outro (3:20)
- Inserire sottotitoli IT (auto + revisione manuale)
- Export: Master ProRes + H.264 1080p + vertical 60s highlight Step 4-7
