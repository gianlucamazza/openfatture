# Notifiche SDI Demo

File placeholder per simulare il flusso `openfatture sdi process`.

## Contenuto
- `RC_2025-002.xml` – Ricevuta di consegna per la fattura 2025-002.
- `NS_2025-003.xml` – Notifica di scarto per fattura 2025-003 (dati fittizi).

Copiali in una directory temporanea e lancia:
```bash
uv run openfatture sdi process --input examples/demo/sdi-notifications
```

> I contenuti XML sono ridotti al minimo e non validi per produzione; servono solo per demo/screenshot.
