# Dataset demo OpenFatture

Questi file sono fixture di dominio per test e sperimentazioni locali. La demo
CLI ufficiale è provider-free e si esegue con `./scripts/demo.sh`.

## Contenuto
- `clients.csv` – tre clienti esempio (ACME, Studio Legale Aurora, Freelance Lab).
- `products.csv` – servizi chiave usati nelle fatture demo.
- `invoices.csv` – tre fatture 2025 in diversi stati (`bozza`, `inviata`, `consegnata`).
- `sdi-notifications/` – notifiche PEC finte per mockare il flusso SDI.

## Utilizzo

Per eseguire la demo deterministica:

```bash
./scripts/demo.sh
```

Per usare questi fixture, importa i dati dal codice o dai test di dominio. Non
sono collegati a comandi CLI rimossi.

## Nota JSON/CSV
- Encoding UTF-8 senza BOM.
- Separatore `,` (virgola), virgolette doppie solo se necessario.
- Decimali con `.` (punto).

Aggiorna questi file ogni volta che gli script o le demo vengono modificate in modo sostanziale.
