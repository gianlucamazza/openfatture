# Operazioni Batch (CSV)

Guida per importare, esportare e validare grandi volumi di fatture con la CLI `openfatture batch`.

---

## Quando usare il batch

- Migrazione da altri gestionali (esporta CSV e importalo in OpenFatture).
- Caricamento periodico di fatture generate da sistemi esterni.
- Analisi di alto livello (esporta CSV per BI/Excel).

---

## Prerequisiti

1. **Clienti già presenti** nel database. Gli ID cliente vengono usati nel CSV. Recuperali con:
   ```bash
   uv run openfatture cliente list
   ```
2. **Ambiente configurato** (`openfatture init`) e `.env` con PEC/notifiche se vuoi i riepiloghi via email.
3. File CSV in UTF-8 con intestazione corrispondente al formato descritto qui sotto.

---

## Formato CSV di import

Colonne obbligatorie:

| Campo | Descrizione | Esempio |
|-------|-------------|---------|
| `numero` | Numero fattura (stringa). | `001` |
| `anno` | Anno contabile. | `2025` |
| `data_emissione` | Data ISO (`YYYY-MM-DD`). | `2025-01-15` |
| `cliente_id` | ID cliente già presente nel DB. | `3` |
| `imponibile` | Imponibile complessivo (decimali). | `500.00` |
| `iva` | IVA totale. | `110.00` |
| `totale` | Totale lordo. | `610.00` |
| `note` | Facoltativo – note visibili in fattura. | `Consulenza gennaio` |

> **Suggerimento**: se hai righe di dettaglio, importale dopo con script dedicati oppure aggiungile manualmente dal comando `openfatture fattura show` → `fattura righe add` (feature pianificata). Il batch import attuale crea fatture con totali già calcolati.

### Esempio CSV

```csv
numero,anno,data_emissione,cliente_id,imponibile,iva,totale,note
001,2025,2025-01-15,3,500.00,110.00,610.00,"Consulenza gestionale"
002,2025,2025-01-18,5,1200.00,264.00,1464.00,"Sviluppo backend API"
```

---

## Importare fatture

1. **Dry-run (consigliato):**
   ```bash
   uv run openfatture batch import fatture.csv --dry-run
   ```
   - Valida struttura e clienti senza salvare nulla.
   - Mostra errori dettagliati (fino a 10 righe, poi un riepilogo).

2. **Import reale:**
   ```bash
   uv run openfatture batch import fatture.csv
   ```
   - Al termine indica numero totale, successi/fallimenti e durata.
   - Se `NOTIFICATION_EMAIL` è configurata, invia un riepilogo con template professionale (disattiva con `--no-summary`).

3. **Verifica:**
   ```bash
   uv run openfatture fattura list --anno 2025
   ```

### Errori comuni

- `Client X not found`: crea prima il cliente o correggi l’ID nel CSV.
- `Row N: ... invalid literal`: numero con virgola → usa il punto come separatore decimale.
- `Import failed: ...`: file non leggibile o encoding errato → salva in UTF-8 senza BOM.

---

## Esportare fatture

```bash
uv run openfatture batch export export_2025.csv --anno 2025 --stato inviata
```

- Salva un riepilogo per fattura (numero, data, cliente, imponibile, IVA, totale, note).
- I file vengono creati nel percorso indicato; la cartella viene generata automaticamente se non esiste.
- Apri in Excel/Numbers/LibreOffice e imposta separatore `,` (virgola).

> L’esportazione con righe dettaglio (`include_lines`) è disponibile a livello di API (`openfatture.core.batch.operations`) e verrà esposta nella CLI nelle prossime versioni.

---

## Manutenzione e storicizzazione

- I batch import appartengono allo stato **bozza**. Completa eventuali righe mancanti prima di inviare a SDI.
- Mantieni una copia del CSV importato insieme ai log (`~/.openfatture/data/logs`).
- `openfatture batch history` mostra oggi un placeholder: il tracciamento storico verrà collegato a una tabella dedicata (`batch_operation`) in roadmap.

---

## Checklist post-import

1. `openfatture fattura list --stato bozza` per verificare le nuove fatture.
2. `openfatture fattura show ID` per controllare dati e totali.
3. Genera XML/PDF e invia a SDI con i comandi `fattura xml` / `fattura invia`.
4. Processa eventuali notifiche PEC con `openfatture notifiche process`.

---

Hai dubbi o trovi casi limite? Apri una issue su GitHub oppure consulta il canale batch nel README. Buon lavoro! 📦
