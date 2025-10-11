# Guida ai Comandi CLI

Panoramica completa dei comandi `openfatture` e delle attività quotidiane che puoi svolgere dalla riga di comando.

> **🎥 Demo Videos:** Watch these scenario videos to see commands in action:
> - [Setup & Configuration](../media/output/scenario_a_onboarding.mp4) (2:30)
> - [Invoice Creation](../media/output/scenario_b_invoice.mp4) (3:30)
> - [AI Assistant](../media/output/scenario_c_ai.mp4) (2:45)
> - [Batch Operations](../media/output/scenario_d_batch.mp4) (2:15)
> - [PEC & SDI](../media/output/scenario_e_pec.mp4) (3:00)

---

## Struttura Generale

- Visualizza l'help globale: `openfatture --help`
- Autocomplete (consigliato): `openfatture --install-completion zsh` / `bash`
- Modalità interattiva (menu): `openfatture --interactive` oppure `openfatture interactive`

Ogni gruppo di comandi dispone del proprio `--help`, ad esempio `openfatture fattura --help`.

---

## 1. Setup Iniziale

| Comando | Descrizione | Opzioni utili |
|---------|-------------|---------------|
| `openfatture init` | Crea cartelle dati, inizializza il database e (in modalità interattiva) genera `.env`. | `--no-interactive` per saltare il wizard e usare solo i valori già presenti in `.env`. |
| `openfatture config show` | Mostra configurazione corrente (valori derivati da `.env`). | `--json` per output strutturato. |
| `openfatture config edit` | Apre l'editor per modificare `.env` (rispetta `$EDITOR`) e ricarica le impostazioni. |  |
| `openfatture config set KEY VALUE` | Aggiorna uno o più valori della configurazione e ricarica `.env`. | Supporta formati `KEY VALUE` e `KEY=VALUE`. |
| `openfatture config reload` | Forza il ricaricamento delle impostazioni da `.env`. |  |

---

## 2. Gestione Clienti

| Comando | Scopo | Esempio |
|---------|-------|---------|
| `openfatture cliente add` | Aggiunge un cliente (`--interactive` avvia il wizard guidato). | `openfatture cliente add "ACME SRL" --piva 12345678901 --sdi ABC1234 --pec acme@pec.it` |
| `openfatture cliente list` | Elenca i clienti con limite configurabile (default 50). | `openfatture cliente list --limit 20` |
| `openfatture cliente show ID` | Mostra i dettagli completi (anagrafiche, indirizzi). | `openfatture cliente show 3` |
| `openfatture cliente delete ID` | Rimuove il cliente (blocca se esistono fatture collegate). | `openfatture cliente delete 7 --force` |

Suggerimento: usa `cliente list` per recuperare gli ID prima di fatturare o importare CSV batch.

---

## 3. Gestione Fatture

### Creazione e aggiornamento
- `openfatture fattura crea [--cliente ID] [--pdf]`: wizard per creare fatture, aggiungere righe, calcolare IVA, ritenuta, bollo. Con `--pdf` genera subito il PDF.
- `openfatture fattura delete ID [--force]`: elimina bozze/non inviate.

### Consultazione
- `openfatture fattura list [--stato inviata] [--anno 2025]`: elenco con filtri.
- `openfatture fattura show ID`: riepilogo completo con righe e totali.

### Esportazione
- `openfatture fattura pdf ID [--template professional] [--output path.pdf]`: genera PDF (template `minimalist`, `professional`, `branded`).
- `openfatture fattura xml ID [--output path.xml] [--no-validate]`: produce XML FatturaPA (validazione XSD attiva di default).

### Invio
- `openfatture fattura invia ID [--pec/--no-pec]`: genera XML e invia via PEC con template HTML professionale. Ricorda di configurare PEC e NOTIFICATION_EMAIL in `.env`.

---

## 4. PEC & Email

| Comando | Utilità |
|---------|---------|
| `openfatture pec test` | Verifica credenziali PEC, server SMTP e invia un messaggio di prova. |
| `openfatture email test` | Invia la mail di test con template professionale alle notifiche interne. |
| `openfatture email preview --template sdi/invio_fattura` | Genera l’HTML in `/tmp/email_preview.html` con dati demo. |
| `openfatture email info` | Mostra branding, colori, template disponibili. |

Se il test fallisce, controlla le variabili `PEC_ADDRESS`, `PEC_PASSWORD`, `PEC_SMTP_*` nel file `.env`.

---

## 5. Notifiche SDI

| Comando | Descrizione | Note |
|---------|-------------|------|
| `openfatture notifiche process FILE.xml` | Analizza la notifica SDI (AT/RC/NS/MC/NE), aggiorna la fattura e invia email. | Usa `--no-email` per saltare l’avviso automatico. |
| `openfatture notifiche list [--tipo RC]` | Elenca le notifiche salvate in archivio. | I dati provengono dalla tabella `log_sdi`. |
| `openfatture notifiche show ID` | Mostra i dettagli di una singola notifica. | Utile per capire perché una fattura è stata scartata. |

Quando scarichi manualmente le notifiche PEC, processale con `notifiche process` per mantenere il database allineato.

---

## 6. Operazioni Batch

- `openfatture batch import file.csv [--dry-run] [--no-summary]`: importa fatture in massa. Con `--dry-run` valida senza salvare. Al termine può inviare un riepilogo email.
- `openfatture batch export output.csv [--anno 2025] [--stato inviata]`: esporta fatture per report o migrazione.
- `openfatture batch history`: segnaposto (mostra solo un esempio). Il tracciamento storico sarà completato nelle prossime versioni.

Consulta [docs/BATCH_OPERATIONS.md](BATCH_OPERATIONS.md) per il formato CSV e le best practice.

---

## 7. Reportistica

| Comando | Output |
|---------|--------|
| `openfatture report iva [--anno 2025] [--trimestre Q1]` | Riepilogo IVA, imponibile e totali per aliquota. |
| `openfatture report clienti [--anno 2025]` | Classifica clienti per fatturato. |
| `openfatture report scadenze` | Elenca pagamenti scaduti, in scadenza e futuri con residui e stato dal ledger pagamenti. |

---

## 8. AI & Automazione

Prima di usare i comandi AI configura le variabili `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY` (oppure Ollama). Verifica con `openfatture config show`.

| Comando | Cosa fa | Esempio |
|---------|---------|---------|
| `openfatture ai describe "testo"` | Genera descrizioni professionali per le linee fattura, riutilizzando esempi rilevanti e citando note operative. | `openfatture ai describe "Consulenza backend" --hours 8 --rate 75 --tech "Python,FastAPI"` |
| `openfatture ai suggest-vat "servizio"` | Suggerisce aliquota IVA, natura e note fiscali con riferimenti DPR 633/72 dalla knowledge base. | `openfatture ai suggest-vat "Formazione online" --pa` |
| `openfatture ai forecast [--months 6]` | Previsione incassi con ensemble Prophet + XGBoost; salva modelli/metriche in `.models/` e supporta `--retrain`. | `openfatture ai forecast --client 12 --retrain` |
| `openfatture ai check ID [--level advanced]` | Analizza la fattura con regole + AI per individuare errori prima dell’invio. | `openfatture ai check 45 --level standard --verbose` |
| `openfatture ai rag status` | Mostra sorgenti della knowledge base, conteggio documenti e directory ChromaDB. |  |
| `openfatture ai rag index [--source id]` | Indicizza (o reindicizza) le sorgenti definite nel manifest RAG. | `openfatture ai rag index --source tax_guides`
| `openfatture ai rag search "query"` | Ricerca semantica nella knowledge base (utile per debug o audit interno). | `openfatture ai rag search "reverse charge edilizia" --source tax_guides` |

Il comando `ai forecast` usa i modelli presenti in `MLConfig.model_path` (predefinito `.models/`); se non trovati viene eseguito il training iniziale e vengono generati i file `cash_flow_*`. Usa `--retrain` per rigenerare i modelli dopo aggiornamenti dati. Le analisi AI di compliance (`ai check`) restano in beta: in caso di errori utilizza l’opzione `--json` per diagnosticare più facilmente.

> ℹ️ **Suggerimento:** dopo aver configurato `OPENAI_API_KEY` (o un provider embedding locale) esegui `openfatture ai rag index` per popolare la knowledge base. Gli agenti citeranno automaticamente le fonti normative con il formato `[numero]`.

---

## 9. Modalità Interattiva

`openfatture interactive` (o `openfatture --interactive`) avvia l’interfaccia testuale con menu Rich/Questionary:

- Navigazione rapida tra clienti, fatture, report
- Chat AI con cronologia persistente (`~/.openfatture/ai/sessions`)
- Suggerimenti fiscali IVA guidati dall'AI direttamente dal menu
- Accesso diretto alle azioni più comuni senza ricordare sintassi CLI

---

## Suggerimenti Finali

- Esegui `uv run openfatture ...` se usi `uv` (consigliato). Con ambienti virtuali classici basta attivarli e usare `openfatture`.
- Per debugging aggiungi `--verbose` ai comandi che lo supportano o controlla i log in `~/.openfatture/data`.
- Aggiorna spesso `.env` e mantieni un backup del database (`openfatture.db` o l’istanza PostgreSQL).

Buon lavoro con OpenFatture! 🧾
