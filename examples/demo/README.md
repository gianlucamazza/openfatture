# Dataset demo OpenFatture (2025)

Questo pacchetto fornisce dati coerenti con gli scenari video/documentazione.

## Contenuto
- `clients.csv` – tre clienti esempio (ACME, Studio Legale Aurora, Freelance Lab).
- `products.csv` – servizi chiave usati nelle fatture demo.
- `invoices.csv` – tre fatture 2025 in diversi stati (`bozza`, `inviata`, `consegnata`).
- `sdi-notifications/` – notifiche PEC finte per mockare il flusso SDI.

## Utilizzo Rapido
```bash
uv run openfatture cliente list
uv run openfatture batch import examples/demo/invoices.csv --dry-run
uv run openfatture batch import examples/demo/invoices.csv
uv run openfatture fattura list --anno 2025
```

Per ripristinare l'intero ambiente:
```bash
./scripts/reset_demo.sh
```

## Nota JSON/CSV
- Encoding UTF-8 senza BOM.
- Separatore `,` (virgola), virgolette doppie solo se necessario.
- Decimali con `.` (punto).

Aggiorna questi file ogni volta che gli script o le demo vengono modificate in modo sostanziale.
