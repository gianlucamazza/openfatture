# Scenario E · Invio PEC & Gestione Notifiche SDI (Storyboard)

**Versione:** v2025.02.03
**Owner:** Compliance & PEC (lead: Chiara Lombardi)
**Durata target:** 3'00" ± 10s

## Sequenza Shot
| # | Durata | Video | Audio/VO | Overlay/Note |
|---|--------|-------|----------|--------------|
| 1 | 0:04 | Logo animato + titolo "Invio SDI" | SFX intro breve | Badge "Compliance" |
| 2 | 0:12 | Speaker on cam | "Invio fatture elettroniche al Sistema di Interscambio" | CTA "Step 1/6" |
| 3 | 0:18 | Terminale: `openfatture pec test` | "Verifica configurazione PEC prima dell'invio" | Callout SMTP config |
| 4 | 0:20 | Output test PEC: connessione OK | "Test invio a casella PEC di prova" | Badge "Connection OK" |
| 5 | 0:22 | Terminale: `openfatture fattura show 1` | "Verifica fattura pronta per l'invio (stato: bozza)" | Highlight status field |
| 6 | 0:25 | Terminale: `openfatture fattura invia 1 --pec` | "Invio al SDI via PEC certificata" | Lower-third "sdi01@pec.fatturapa.it" |
| 7 | 0:18 | Output invio: ID trasmissione, timestamp | "Conferma invio con identificativo univoco" | Badge "Sent to SDI" |
| 8 | 0:20 | Simulazione: notifica RC (ricevuta consegna) | "Elaborazione notifiche da SDI" | Callout "RC = Delivered" |
| 9 | 0:25 | Terminale: `openfatture notifiche process examples/sdi/RC_*.xml` | "Import notifiche ricevute da SDI" | XML snippet overlay |
| 10 | 0:18 | Terminale: `openfatture fattura show 1` | "Stato fattura aggiornato: CONSEGNATA" | Highlight status change |
| 11 | 0:16 | Dashboard email template personalizzato | "Notifiche automatiche via email" | Preview email template |
| 12 | 0:12 | Outro + note compliance | "Archivio digitale conservato per 10 anni" | CTA docs compliance |

## Note Produzione
- **PEC**: usare credenziali demo (non reali), simulare invio
- **SDI Notifiche**: usare XML di esempio in `examples/sdi/` (RC, NS, MC)
- **Privacy**: oscurare indirizzi PEC reali se presenti
- **Screen capture**: OBS standard, terminale + preview email (opzionale)
- **Timing**: simulare attesa SDI (in realtà istantanea in demo)

## Asset Necessari
- File XML notifiche SDI esempio (`examples/sdi/RC_IT12345678901_00001.xml`)
- Template email notifica configurato
- Database demo con fattura in stato "inviata"
- Callout Figma "Sistema di Interscambio (SDI)" explanation
- Badge stati fattura: BOZZA → INVIATA → CONSEGNATA

## Checklist Pre-shoot
- [ ] Verificare file XML notifiche in `examples/sdi/`
- [ ] Testare comando `openfatture pec test` con config demo
- [ ] Preparare fattura demo in stato "bozza" (ID 1)
- [ ] Verificare template email funzionante
- [ ] Confermare variabili PEC_* in `.env.demo` non esposte
- [ ] Marker Resolve: Intro, PEC Test, Show, Invio, Notifica, Update, Email, Outro

## Post-produzione
- Marker timeline: Intro (0:00), PEC Test (0:16), Show (0:54), Invio (1:16), Notifiche (2:01), Email (2:37), Outro (2:48)
- Sottotitoli IT (con glossario SDI, PEC, RC, NS, MC)
- Export: Master ProRes + H.264 1080p + infographic PDF "Flusso SDI"
- Nota: aggiungere disclaimer "Demo con credenziali fittizie - non usare in produzione"
- Includere link a docs AgID e FatturaPA nel video description
