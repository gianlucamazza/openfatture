# OpenFatture Media Capture Plan 2025

## 1. Obiettivi
- Documentare i flussi chiave (setup, fatturazione, AI, batch, PEC) con video dimostrativi e screenshot aggiornati al 2025.
- Garantire output conformi a brand, accessibilità e best practice di produzione multimediale.
- Rendere ripetibile la produzione (script, preset, checklist) per futuri aggiornamenti.

## 2. Scenari Video Prioritari
### Scenario A · Onboarding & Setup
- **Durata target**: 2:30
- **Obiettivo**: mostrare installazione, configurazione `.env`, bootstrap DB.
- **Prerequisiti**: repo pulita `main`, ambiente demo con credenziali fittizie (`/scripts/reset_demo.sh`).
- **Script**:
  1. Intro (Speaker in video o voice-over, logo animato 3s).
  2. Clonazione repo, `uv sync`, `uv run openfatture init --no-interactive`.
  3. Copia `.env.example`, modifica variabili core con editor testuale (sottolineare campo obbligatorio).
  4. Esecuzione `openfatture config show`.
  5. Call to action: “Pronti per creare la prima fattura”.
- **Screenshot**: editor `.env`, output `openfatture config show`.

### Scenario B · Creazione Fattura da CLI
- **Durata target**: 3:30
- **Obiettivo**: generare fattura completa e salvarla in XML.
- **Prerequisiti**: Database con cliente demo `ACME Srl`, prodotto `Servizio Dev`.
- **Script**:
  1. Richiamo comando `openfatture fattura crea --pdf`.
  2. Evidenziare validazione campi e suggerimenti.
  3. Salvataggio e preview XML (mostrare estratto in VS Code).
  4. Uso `openfatture fattura pdf 1 --template professional`.
  5. Reminder su versionamento dei documenti.
- **Screenshot**: wizard CLI, preview XML, PDF generato.

### Scenario C · AI Assistant & Automazioni
- **Durata target**: 2:45
- **Obiettivo**: dimostrare `openfatture -i` modalità interattiva + comandi AI (`ai describe`, `ai suggest-vat`).
- **Prerequisiti**: Provider AI configurato con chiave dummy, dataset fatture 2024/2025.
- **Script**:
  1. Avvio UI interattiva, selezione “AI Assistant”.
  2. Prompt esempio: “Crea descrizione per consulenza GDPR”.
  3. Uso `openfatture ai suggest-vat "Consulenza GDPR" --importo 1500 --categoria consulenza`.
  4. Chiusura con riepilogo benefici e nota privacy/dataset.
- **Screenshot**: chat assistant con risposta, output CLI AI.

### Scenario D · Operazioni Batch & Import/Export
- **Durata target**: 2:15
- **Obiettivo**: importare clienti/prodotti via CSV e generare fatture multiple.
- **Prerequisiti**: file demo `examples/batch/clients.csv`, `products.csv`, `invoices.csv`.
- **Script**:
  1. Presentazione CSV (zoom su colonne principali).
  2. Comando `openfatture batch import examples/batch/invoices.csv --dry-run`.
  3. Import definitivo senza `--dry-run` e riepilogo degli errori.
  4. Visualizzazione dashboard CLI (`openfatture interactive start` → “Report & Statistiche”).
- **Screenshot**: CSV in spreadsheet, output batch dry-run vs apply.

### Scenario E · Invio PEC & Gestione Notifiche SDI
- **Durata target**: 3:00
- **Obiettivo**: mostrare firma opzionale, invio PEC e tracking notifiche.
- **Prerequisiti**: certificato demo `.p12`, casella PEC test, notifiche simulate in `/examples/sdi`.
- **Script**:
  1. Invio `openfatture fattura invia 1 --pec` (illustra il passo di firma digitale previsto).
  2. Verifica configurazione PEC con `openfatture pec test`.
  3. Apertura `docs/EMAIL_TEMPLATES.md` per mostrare personalizzazione.
  4. Elaborazione notifiche `openfatture notifiche process examples/sdi/RC_IT12345678901_00001.xml`.
  5. Visualizzazione stato fattura con `openfatture fattura show 1`.
- **Screenshot**: log PEC, email template, dashboard stato fattura.

## 3. Deliverable Screenshot Standalone
- Formato PNG 2×, 2560 px lato lungo, profilo colore sRGB.
- Layout CLI: font 18 pt, tema “Solarized Dark” o “One Dark” con sfondo pulito.
- Annotazioni leggere (rettangoli semitrasparenti) esportate anche senza overlay per versioni raw.
- Nomina: `media/screenshots/v2025/<scenario>_<step>.png`.

## 4. Ambiente & Toolchain
- **Mac Studio / Linux workstation** con monitor 27" 1440p.
- **OBS Studio 30+** preset `media/presets/OBS_OF-1440p60.json` (NVENC/Apple VT H.264, bitrate 18 Mbps, lossless master ProRes).
- **Audio**: microfono XLR + interfaccia, filtro passa-alto 80 Hz, compressione ratio 2:1.
- **Software**: iTerm2 (CLI), VS Code, Figma (annotazioni), DaVinci Resolve/FCPX (editing, preset `media/presets/resolve_of_timeline.yaml`), ffmpeg (export batch), WhisperX (sottotitoli).
- **Asset Brand**: logo SVG `docs/assets/logo.svg`, palette `#001f3f`, `#2ECC71`, `#FF851B`.

## 5. Workflow di Produzione
1. **Pre-produzione**: approvazione script/storyboard, setup ambiente demo tramite `scripts/reset_demo.sh`.
2. **Cattura**: registrazione tracce separate (video, mic, system audio, curosre highlight).
3. **Editing**:
   - Import in NLE, sincronizzare tracce, inserire capitoli (marker ogni scenario/step).
  - Inserire lower-third per comandi chiave (`openfatture fattura crea`, ecc.).
   - Color grading leggero, noise reduction audio, compressione finale -1 LUFS short-term.
4. **Accessibilità**: generare trascrizione con WhisperX, revisione manuale, esport SRT/WEBVTT.
5. **QA**: checklist (sezione 7), revisione tecnica (dev lead) + revisione brand (design).
6. **Distribuzione**: export master ProRes + deliverable H.264 1080p, verticale 1080×1920. Upload su CDN/YouTube (unlisted) → embed in docs.
7. **Versioning**: tag cartella `media/v2025.1`, aggiornare `docs/QUICKSTART.md` e README con nuovi link/screenshot.

## 6. Ruoli e Responsabilità
- **Producer**: pianificazione, coordinamento risorse.
- **Technical Host**: esecuzione comandi, garantire coerenza dati demo.
- **Narrator**: voice-over in IT/EN, segue script approvato.
- **Editor**: montaggio, color correction, export multiformato.
- **Accessibility Reviewer**: verifica sottotitoli, contrasto, ritmo parlato.
- **QA Lead**: firma la checklist finale prima della pubblicazione.

## 7. Checklist Qualità
- Contenuti: comandi corretti, output coerente, versioni CLI/UI aggiornate (verificare `openfatture --version` in video).
- Visual: testo leggibile, nessun flicker, zoom/overlay non invasivi.
- Audio: volume -16 LUFS integrato, dinamica controllata, niente rumori di fondo.
- Accessibilità: sottotitoli sincronizzati, trascrizione pubblicata, callout descrittivi per elementi UI.
- Brand: intro/outro ≤4 s, logo e palette ufficiali, titoli scenario coerenti.
- Deliverable: master lossless + compressi, screenshot 2×, metadata (titolo, descrizione, capitoli, tag).
- Distribuzione: link aggiornati in `README.md` e `docs`, file caricati su storage condiviso con naming corretto.

## 8. Sequenza Temporale (stima)
- **Settimana 1**: finalizzazione script, preset OBS, setup ambiente.
- **Settimana 2**: registrazioni primarie, capture screenshot.
- **Settimana 3**: editing, sottotitoli, QA iterazioni.
- **Settimana 4**: pubblicazione, aggiornamento documentazione, retrospettiva.

## 9. Manutenzione Continuativa
- Audit trimestrale per verificare che CLI/UI non abbiano modifiche sostanziali.
- Aggiornamento asset a ogni release minor (`v0.x.y`): revisionare scenario impattato, rigenerare video/screenshot coinvolti.
- Conservare materiali sorgenti (progetti NLE, preset OBS, dataset demo) nel repository `media/` protetto con versione semantica.

## 10. Validazione Script & Assegnazione Ruoli (Feb 2025)
- **Revisioni script**: confermati in riunione del 3 febbraio 2025 con Product, Backend e Content; eventuali micro-aggiornamenti vanno registrati in `docs/storyboards/`.
- **Owner scenario**:
  - Scenario A → Product Team (lead: Gianluca Mazza) ✅
  - Scenario B → Backend Guild (lead: Davide Ricci) ✅
  - Scenario C → AI/ML Guild (lead: Elisa Moretti) ✅
  - Scenario D → Operations Team (lead: Marco Greco) ✅
  - Scenario E → Compliance & PEC (lead: Chiara Lombardi) ✅
- **Ruoli produzione assegnati**
  - Producer: Gianluca Mazza (`@gianluca`) – backup: Laura Conti (`@laura.conti`)
  - Technical Host: Davide Ricci (`@davide.ricci`) – backup: Marco Greco (`@marco.greco`)
  - Narrator: Elisa Moretti (`@elisa.moretti`) – backup: Federica Bianchi (`@federica.b`)
  - Editor: Martina Rinaldi (`@martina.video`) – backup: Paolo Serra (`@paolo.serra`)
  - Accessibility Reviewer: Chiara Lombardi (`@chiara.access`) – backup: Sara Vitale (`@sara.vitale`)
  - QA Lead: Luca De Santis (`@luca.qa`) – backup: Anna Parisi (`@anna.parisi`)
- **Controllo qualità storyboard**: ogni aggiornamento (>3 modifiche) richiede approvazione incrociata di Producer + QA Lead prima della cattura.
- **Canali operativi**: #openfatture-media (Slack) per comunicazioni giornaliere; board dedicato in Linear `MED-2025`.
- **Pianificazione**: calendario dettagliato in `docs/MEDIA_PRODUCTION_SCHEDULE.md` (aggiornamento quotidiano a cura del Producer).
