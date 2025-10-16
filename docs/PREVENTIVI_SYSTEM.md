# Sistema Pro-forma/Preventivi - Documentazione Completa

## Panoramica

Il sistema preventivi (pro-forma/quotes/estimates) è ora completamente integrato in OpenFatture, permettendo di creare, gestire e convertire preventivi in fatture.

## Architettura

### Modelli Database

**Nuovi Modelli:**

```python
# StatoPreventivo (Enum)
BOZZA = "bozza"              # Draft
INVIATO = "inviato"          # Sent to client
ACCETTATO = "accettato"      # Accepted by client
RIFIUTATO = "rifiutato"      # Rejected by client
SCADUTO = "scaduto"          # Expired
CONVERTITO = "convertito"    # Converted to invoice

# Preventivo (Model)
- numero: str                 # Sequential number (per year)
- anno: int                   # Year
- data_emissione: date        # Issue date
- data_scadenza: date         # Expiration date
- cliente_id: int             # Foreign key to Cliente
- imponibile: Decimal         # Taxable amount
- iva: Decimal                # VAT amount
- totale: Decimal             # Total amount
- stato: StatoPreventivo      # Status
- note: str (optional)        # Notes
- condizioni: str (optional)  # Terms and conditions
- validita_giorni: int        # Validity period (default: 30 days)
- pdf_path: str (optional)    # PDF file path

# RigaPreventivo (Model)
- preventivo_id: int          # Foreign key to Preventivo
- numero_riga: int            # Line number
- descrizione: str            # Description
- quantita: Decimal           # Quantity
- prezzo_unitario: Decimal    # Unit price
- unita_misura: str           # Unit of measure
- aliquota_iva: Decimal       # VAT rate
- imponibile: Decimal         # Taxable amount
- iva: Decimal                # VAT amount
- totale: Decimal             # Total amount
```

**Relazioni:**
- `Cliente` → `Preventivo` (one-to-many): `cliente.preventivi`
- `Preventivo` → `RigaPreventivo` (one-to-many): `preventivo.righe`
- `Preventivo` ↔ `Fattura` (one-to-one): `preventivo.fattura` / `fattura.preventivo`

### Business Logic Layer

**PreventivoService** (`openfatture/core/preventivi/service.py`)

Servizio principale con le seguenti operazioni:

1. **create_preventivo()**: Crea nuovo preventivo
   - Genera numero sequenziale (per anno)
   - Calcola totali da righe
   - Imposta data scadenza automatica
   - Gestisce note e condizioni

2. **get_preventivo()**: Recupera preventivo per ID

3. **list_preventivi()**: Lista preventivi con filtri
   - Filtro per stato
   - Filtro per cliente
   - Filtro per anno
   - Limit risultati

4. **update_stato()**: Aggiorna stato preventivo
   - Validazione: non può cambiare se CONVERTITO

5. **delete_preventivo()**: Elimina preventivo
   - Validazione: non può eliminare se CONVERTITO

6. **check_scadenza()**: Verifica e aggiorna scadenza
   - Aggiorna automaticamente stato a SCADUTO se necessario

7. **converti_a_fattura()**: Converte preventivo in fattura
   - Genera nuovo numero fattura (sequenziale)
   - Copia tutti i dati (righe, importi, note)
   - Aggiorna preventivo a CONVERTITO
   - Crea relazione bidirezionale

### CLI Commands

**Comandi disponibili:**

```bash
# Creare preventivo (wizard interattivo)
openfatture preventivo crea [--cliente ID] [--validita GIORNI]

# Listare preventivi
openfatture preventivo lista [--stato STATO] [--anno ANNO] [--cliente ID] [--limit N]

# Mostrare dettaglio preventivo
openfatture preventivo show <id>

# Eliminare preventivo
openfatture preventivo delete <id> [--force]

# Convertire preventivo in fattura
openfatture preventivo converti <id> [--tipo TD01]

# Aggiornare stato
openfatture preventivo aggiorna-stato <id> <stato>
```

**Stati validi:** bozza, inviato, accettato, rifiutato, scaduto

### Generazione PDF

**PreventivoPDFGenerator** (`openfatture/services/pdf/preventivo_generator.py`)

Generatore PDF specializzato per preventivi:

- Riutilizza componenti PDF esistenti (header, footer, table)
- Layout dedicato con enfasi su:
  - **"PREVENTIVO"** come titolo prominente
  - Data scadenza in rosso (evidenziata)
  - Watermark "BOZZA" per preventivi in bozza
- Sezioni:
  - Intestazione azienda
  - Info preventivo (numero, date, validità)
  - Dati cliente
  - Tabella righe
  - Totali (box evidenziato)
  - Note
  - Termini e condizioni
- Footer: "Questo preventivo non costituisce fattura"

**Utilizzo:**

```python
from openfatture.services.pdf.preventivo_generator import create_preventivo_pdf_generator

generator = create_preventivo_pdf_generator(
    company_name="ACME S.r.l.",
    company_vat="12345678901",
    logo_path="./logo.png",
    watermark_text="BOZZA"
)

pdf_path = generator.generate(preventivo, "preventivo_001.pdf")
```

## Workflow Tipico

### 1. Creazione Preventivo

```bash
$ openfatture preventivo crea

📋 Create New Preventivo (Quote)

Available clients:
  1. Cliente Test SRL (12345678901)
  2. ACME Corp (98765432100)

Select client ID [1]: 1
✓ Client: Cliente Test SRL

Validity: 30 days (expires: 2025-11-15)

Add line items
Enter empty description to finish

Item 1 description: Consulenza IT
Quantity [1.0]: 10
Unit price (€) [100.0]: 150
VAT rate (%) [22.0]: 22
Unit of measure [ore]: ore
  ✓ Added: Consulenza IT - €1830.00

Item 2 description:

Add notes? [y/n]: n
Add terms and conditions? [y/n]: n

✓ Preventivo created successfully!

┌─────────────────────────────────────┐
│ Preventivo 1/2025                   │
├────────────────┬────────────────────┤
│ Client         │    Cliente Test    │
│ Issue date     │      2025-10-16    │
│ Expiration date│      2025-11-15    │
│ Line items     │                  1 │
│ Imponibile     │          €1500.00  │
│ IVA            │           €330.00  │
│ TOTALE         │          €1830.00  │
└────────────────┴────────────────────┘

Next: openfatture preventivo converti 1 (to create invoice)
```

### 2. Lista Preventivi

```bash
$ openfatture preventivo lista --stato bozza

┌────────────────────────────────────────────────────────────┐
│ Preventivi (3)                                             │
├────┬──────────┬────────────┬────────────┬───────┬─────────┤
│ ID │ Number   │ Date       │ Expiration │ Total │ Status  │
├────┼──────────┼────────────┼────────────┼───────┼─────────┤
│  1 │ 1/2025   │ 2025-10-16 │ 2025-11-15 │€1830  │ bozza   │
│  2 │ 2/2025   │ 2025-10-16 │ 2025-11-15 │€2500  │ bozza   │
│  3 │ 3/2025   │ 2025-10-14 │ 2025-10-20 │€1000  │ scaduto │
└────┴──────────┴────────────┴────────────┴───────┴─────────┘
```

### 3. Conversione in Fattura

```bash
$ openfatture preventivo converti 1

🔄 Converting Preventivo to Fattura

Preventivo: 1/2025
Client: Cliente Test SRL
Total: €1830.00

Convert to invoice? [Y/n]: y

✓ Preventivo converted successfully!

┌─────────────────────────────────────┐
│ Invoice 1/2025                      │
├────────────────┬────────────────────┤
│ Client         │    Cliente Test    │
│ Date           │      2025-10-16    │
│ Document type  │             TD01   │
│ Line items     │                  1 │
│ Imponibile     │          €1500.00  │
│ IVA            │           €330.00  │
│ TOTALE         │          €1830.00  │
└────────────────┴────────────────────┘

Invoice ID: 1
Original preventivo: 1/2025 (ID: 1)

Next: openfatture fattura invia 1 --pec
```

## Testing

### Test Coverage

**Unit Tests** (`tests/core/test_preventivo_service.py`):
- ✅ 10 test cases
- ✅ 63% coverage del service
- Tests:
  - Creazione preventivo con successo
  - Validazione cliente invalido
  - Numerazione sequenziale
  - CRUD operations (get, list, update, delete)
  - Gestione scadenza
  - Protezione preventivi convertiti

**Integration Tests** (`tests/integration/test_preventivo_conversion.py`):
- ✅ 8 test cases
- ✅ 59% coverage della conversione
- Tests:
  - Conversione preventivo→fattura completa
  - Validazioni (già convertito, scaduto)
  - Preservazione dati (note, righe)
  - Tipi documento diversi (TD01, TD06)
  - Numerazione sequenziale fatture
  - Relazioni bidirezionali

**Esecuzione:**

```bash
# Unit tests
uv run python -m pytest tests/core/test_preventivo_service.py -v

# Integration tests
uv run python -m pytest tests/integration/test_preventivo_conversion.py -v

# Tutti i test preventivi
uv run python -m pytest -k preventivo -v
```

## Validazioni e Business Rules

### Validazioni Create

1. **Creazione:**
   - Cliente deve esistere
   - Almeno una riga richiesta
   - Calcolo automatico totali

2. **Conversione a fattura:**
   - Preventivo non deve essere già convertito
   - Preventivo non deve essere scaduto
   - Data scadenza deve essere futura
   - Genera nuovo numero fattura sequenziale

3. **Eliminazione:**
   - Non può eliminare preventivi convertiti
   - Cancellazione cascade delle righe

4. **Cambio stato:**
   - Non può cambiare stato di preventivi convertiti

### Stati e Transizioni

```
BOZZA ──────────┐
    │           │
    ↓           ↓
INVIATO ──→ ACCETTATO ──→ CONVERTITO (finale)
    │           │
    ↓           ↓
RIFIUTATO   SCADUTO
```

**Stati finali:** CONVERTITO (non modificabile)
**Controllo automatico:** SCADUTO (aggiornato da `check_scadenza()`)

## Differenze Preventivo vs Fattura

| Feature                | Preventivo              | Fattura                    |
|------------------------|-------------------------|----------------------------|
| Scopo                  | Offerta/Stima           | Documento fiscale          |
| XML FatturaPA          | ❌ No                   | ✅ Sì                      |
| Invio SDI              | ❌ No                   | ✅ Sì                      |
| Scadenza               | ✅ Sì (validità)        | ❌ No                      |
| Stati                  | 6 stati                 | 7 stati (diversi)          |
| Numerazione            | Separata (1/2025, ...)  | Separata (1/2025, ...)     |
| Conversione            | → Fattura               | ← Preventivo (opzionale)   |
| PDF                    | Template specifico      | Template fattura           |
| Footer PDF             | "Non costituisce fattura" | "Documento fiscale"      |
| Pagamenti              | ❌ No tracking          | ✅ Sistema completo        |
| SDI Notifications      | ❌ No                   | ✅ RC/NS/MC/DT             |

## Esempi di Utilizzo Avanzato

### Esempio 1: Preventivo con Condizioni Personalizzate

```python
from openfatture.core.preventivi.service import PreventivoService
from openfatture.utils.config import get_settings

settings = get_settings()
service = PreventivoService(settings)

righe = [
    {
        "descrizione": "Sviluppo applicazione web",
        "quantita": 40,
        "prezzo_unitario": 80.00,
        "aliquota_iva": 22.00,
        "unita_misura": "ore"
    },
    {
        "descrizione": "Setup server e deployment",
        "quantita": 8,
        "prezzo_unitario": 100.00,
        "aliquota_iva": 22.00,
        "unita_misura": "ore"
    }
]

condizioni = """
1. Preventivo valido 30 giorni
2. Pagamento 50% anticipo, 50% a consegna
3. Consegna prevista in 60 giorni lavorativi
4. Include 3 revisioni
5. Hosting non incluso
"""

preventivo, error = service.create_preventivo(
    db=session,
    cliente_id=1,
    righe=righe,
    validita_giorni=30,
    note="Progetto CRM custom",
    condizioni=condizioni
)
```

### Esempio 2: Workflow Automatizzato

```python
from datetime import date

# 1. Crea preventivo
preventivo, _ = service.create_preventivo(db, cliente_id=1, righe=righe)

# 2. Invia a cliente (aggiorna stato)
service.update_stato(db, preventivo.id, StatoPreventivo.INVIATO)

# 3. Cliente accetta
service.update_stato(db, preventivo.id, StatoPreventivo.ACCETTATO)

# 4. Converti in fattura
fattura, _ = service.converti_a_fattura(db, preventivo.id)

# 5. Genera PDF fattura
from openfatture.services.pdf import create_pdf_generator
generator = create_pdf_generator(template="professional")
pdf_path = generator.generate(fattura)

# 6. Invia fattura a SDI
from openfatture.core.fatture.service import InvoiceService
invoice_service = InvoiceService(settings)
xml_content, _ = invoice_service.generate_xml(fattura)
```

### Esempio 3: Report Preventivi per Cliente

```python
# Lista tutti i preventivi di un cliente
preventivi = service.list_preventivi(db, cliente_id=1)

# Calcola statistiche
from collections import Counter

stati = Counter(p.stato for p in preventivi)
totale_valore = sum(p.totale for p in preventivi)
tasso_conversione = (
    stati[StatoPreventivo.CONVERTITO] / len(preventivi) * 100
    if preventivi else 0
)

print(f"Preventivi totali: {len(preventivi)}")
print(f"Valore totale: €{totale_valore:.2f}")
print(f"Tasso conversione: {tasso_conversione:.1f}%")
print(f"Per stato: {dict(stati)}")
```

## Migrazione Database

Per aggiungere il sistema preventivi a un database esistente:

```python
from openfatture.storage.database.session import init_db
from openfatture.utils.config import get_settings

settings = get_settings()
init_db(str(settings.database_url))

# Le tabelle verranno create automaticamente:
# - preventivi
# - righe_preventivo
# - Aggiunto campo preventivo_id a fatture (nullable)
```

## Prossimi Sviluppi Possibili

1. **Email automatiche:**
   - Invio preventivo via email a cliente
   - Notifiche scadenza
   - Reminder follow-up

2. **Dashboard analytics:**
   - Tassi di conversione
   - Valore medio preventivi
   - Tempo medio accettazione

3. **Versioning preventivi:**
   - Revisioni multiple dello stesso preventivo
   - Storico modifiche

4. **Template preventivi:**
   - Preventivi predefiniti per servizi ricorrenti
   - Quick create da template

5. **Firma digitale preventivi:**
   - Firma elettronica cliente
   - Tracciamento accettazione

6. **Integrazione AI:**
   - Generazione automatica descrizioni
   - Suggerimenti prezzi basati su storico
   - Stima probabilità accettazione

## Supporto e Troubleshooting

### Problema: "Cannot convert expired preventivo"

**Causa:** Il preventivo è scaduto (data_scadenza < oggi)

**Soluzione:**
```bash
# Estendi la validità prima di convertire
openfatture preventivo aggiorna-stato <id> bozza
# Poi modifica manualmente data_scadenza nel database
# Oppure crea nuovo preventivo
```

### Problema: "Cannot delete converted preventivo"

**Causa:** Il preventivo è stato già convertito in fattura

**Soluzione:** I preventivi convertiti non possono essere eliminati per mantenere l'integrità dei dati. Se necessario, elimina prima la fattura collegata.

### Problema: Numero preventivo duplicato

**Causa:** Raro, possibile con concorrenza

**Soluzione:** Il sistema genera numeri sequenziali automaticamente. Se si verifica, ricreare il preventivo.

## Riferimenti

- **Modelli:** `openfatture/storage/database/models.py`
- **Service:** `openfatture/core/preventivi/service.py`
- **CLI:** `openfatture/cli/commands/preventivo.py`
- **PDF:** `openfatture/services/pdf/preventivo_generator.py`
- **Tests:** `tests/core/test_preventivo_service.py`, `tests/integration/test_preventivo_conversion.py`

## Changelog

**v1.1.0 (2025-10-16)** - Sistema Preventivi
- ✅ Modelli database (Preventivo, RigaPreventivo, StatoPreventivo)
- ✅ PreventivoService completo (CRUD + conversione)
- ✅ CLI commands (6 comandi)
- ✅ PDF generator dedicato
- ✅ 18 test cases (10 unit + 8 integration)
- ✅ Relazione bidirezionale Preventivo ↔ Fattura
- ✅ Gestione automatica scadenze
- ✅ Validazioni business logic completa

---

**Sistema preventivi implementato e testato con successo! 🎉**
