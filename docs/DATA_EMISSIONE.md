# Data Emissione (Invoice Date) Management

## Overview

The `data_emissione` field represents the official invoice issue date and is **independent** of when you create the draft.

This allows flexible workflows:
- Create draft today, date it for next week
- Create draft today, backdate it to last week
- Prepare multiple invoices with different dates

## Key Points

✅ **data_emissione is editable** (while invoice is BOZZA)  
✅ **PDF/XML use data_emissione** (not draft creation time)  
✅ **Payment terms reference data_emissione** (e.g., immediate payment = data emissione)  
❌ **Cannot modify after sending** (INVIATA status locks it)

---

## Usage

### 1. Set date when creating invoice

```python
from openfatture.billing.application.invoice_commands import create_invoice

# Create invoice dated for future
result = create_invoice(
    cliente_id=1,
    anno=2026,
    numero="10",
    data_emissione="2026-09-14",  # Invoice date (not today)
    note="Consulting - September 2026",
)
```

### 2. Update date after creation (BOZZA only)

```python
from openfatture.billing.application.invoice_commands import update_invoice

# Change emission date
result = update_invoice(
    fattura_id=123,
    data_emissione="2026-09-14",  # New invoice date
)
```

### 3. Default behavior

If you don't specify `data_emissione`, it defaults to **today**:

```python
# This invoice will be dated today
result = create_invoice(cliente_id=1, anno=2026)
# → data_emissione = date.today()
```

---

## Common Workflows

### Scenario 1: Prepare invoice for future billing

You're planning ahead and want to prepare next month's invoice today:

```python
# Today: 2026-09-10
# Invoice date: 2026-10-01

create_invoice(
    cliente_id=5,
    anno=2026,
    data_emissione="2026-10-01",  # Next month
    note="October billing cycle",
)
```

### Scenario 2: Backdate invoice for completed work

You completed work last week but are issuing the invoice today:

```python
# Today: 2026-09-17
# Service completed: 2026-09-10

create_invoice(
    cliente_id=8,
    anno=2026,
    data_emissione="2026-09-10",  # Service completion date
    note="Consulting services - completed 10.09.2026",
)
```

### Scenario 3: Fix incorrect date

You created a draft with the wrong date:

```python
# Oops, created with today's date by mistake
# Let's fix it while it's still BOZZA

update_invoice(
    fattura_id=42,
    data_emissione="2026-09-14",  # Correct date
)
```

---

## CLI Examples

### Create with specific date

```bash
# Via assistant
openfatture assistant "Create invoice for Acme Corp, dated 2026-09-14"

# The assistant will use:
create_invoice(
    cliente_id=<acme_id>,
    data_emissione="2026-09-14"
)
```

### Update existing draft date

```bash
openfatture assistant "Change invoice 42 date to 2026-09-20"

# The assistant will use:
update_invoice(
    fattura_id=42,
    data_emissione="2026-09-20"
)
```

---

## Technical Details

### Model Definition

```python
class Fattura(Base):
    data_emissione: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
```

- **Type**: `date` (not datetime - no time component)
- **Nullable**: No (must have a date)
- **Default**: Today (if not specified)

### XML Generation

FatturaPA XML uses `data_emissione` directly:

```xml
<DatiGeneraliDocumento>
  <Data>2026-09-14</Data>  <!-- From fattura.data_emissione -->
</DatiGeneraliDocumento>
```

### PDF Generation

PDF invoice header displays `data_emissione`:

```
Fattura N. 10/2026
Data: 14/09/2026  ← From fattura.data_emissione
```

### Payment Terms

Immediate payment (`giorni_scadenza=0`) references `data_emissione`:

```
Rif. termini pagamento: 14.09.2026
```

---

## Validation Rules

### ✅ Allowed

- Any past date
- Today
- Any future date
- Updating while BOZZA
- Different dates for different invoices

### ❌ Not Allowed

- Updating after invoice is sent (INVIATA status)
- Invalid date formats (use YYYY-MM-DD)
- Null/empty dates

---

## Migration Notes

**No migration needed** - this functionality already exists in openfatture.

The model, application commands, and XML/PDF generators all respect the `data_emissione` field as the authoritative invoice date, independent of when the draft was created.

---

## Related

- [Payment Terms](./PAYMENT_TERMS.md) - Payment terms reference data_emissione
- [Invoice Workflow](./INVOICE_WORKFLOW.md) - Status transitions and editing rules
- [CLI Reference](./CLI_REFERENCE.md) - Command-line invoice management
