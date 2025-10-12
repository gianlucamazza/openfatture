# Payment Tracking & Bank Reconciliation

**Complete guide to OpenFatture's payment tracking system with automated bank reconciliation.**

> **📦 Module**: `openfatture.payment`
> **Architecture**: Domain-Driven Design (DDD) + Hexagonal Architecture
> **Status**: ✅ Production-ready (implemented in Phase 5.3)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Domain Models](#domain-models)
5. [Bank Statement Import](#bank-statement-import)
6. [Reconciliation Engine](#reconciliation-engine)
7. [Payment Reminders](#payment-reminders)
8. [CLI Commands](#cli-commands)
9. [API Reference](#api-reference)
10. [Examples](#examples)
11. [Best Practices](#best-practices)

---

## Overview

OpenFatture's **Payment Tracking** module provides enterprise-grade automated bank reconciliation with:

- 🏦 **Multi-Bank Support** - Import from CSV, OFX, QIF formats
- 🤖 **AI-Powered Matching** - 5 fuzzy matching strategies with confidence scoring
- 📧 **Automated Reminders** - Smart notification system with 4 strategies
- 🔄 **Auto-Reconciliation** - Match transactions to invoices automatically
- 🎯 **High Accuracy** - 95%+ matching accuracy with composite matcher

### Use Cases

1. **Freelancers**: Track incoming payments and automate reminders
2. **Small Businesses**: Reconcile hundreds of transactions monthly
3. **Accounting Firms**: Automate client reconciliation workflows
4. **SaaS Companies**: Monitor subscription payments at scale

---

## Features

### 1. Bank Statement Import

- **Formats**: CSV (custom presets), OFX, QIF
- **Banks**: Pre-configured presets for Italian banks (Intesa, UniCredit, BNL, etc.)
- **Data Extraction**: Automatically parse date, amount, description, IBAN
- **Duplicate Detection**: Prevent re-importing same transactions
- **Batch Processing**: Import thousands of transactions efficiently

### 2. Reconciliation Engine

- **5 Matching Strategies**:
  1. **Exact Matcher** - Exact amount + date match
  2. **Fuzzy Matcher** - Similarity-based description matching (RapidFuzz)
  3. **IBAN Matcher** - Match by counterparty IBAN
  4. **Date Window Matcher** - Flexible date range matching
  5. **Composite Matcher** - Weighted combination of all strategies

- **Confidence Scoring**: 0.0-1.0 score for each match
- **Manual Review**: Review low-confidence matches before acceptance
- **Audit Trail**: Full history of match decisions
- **Partial Ledger**: Split transactions across multiple payments with allocation history
- **AI Insights (optional)**: LLM-assisted causale analysis to detect partial payments and references
- **Event Bus**: In-memory event bus dispatches `TransactionMatchedEvent` / `TransactionUnmatchedEvent` with default audit logging; custom listeners can be registered via `register_default_payment_listeners()` or configured via the `PAYMENT_EVENT_LISTENERS` setting (`comma`-separated dotted paths).

#### Partial Payments & AI Insights (2025.10)

- Every `Pagamento` now keeps track of `importo_pagato` and exposes `saldo_residuo` to indicate the remaining balance.
- Reconciliations write to a new `payment_allocations` ledger so you can audit split payments, overpayments, and reversals.
- When AI credentials are configured (`OPENFATTURE_AI_*`), the CLI auto-loads the **PaymentInsightAgent** to analyse bank causali. The agent can:
  - Flag likely partial/acconto payments.
  - Extract probable invoice numbers mentioned in the narrative text.
  - Suggest a split amount when the credited sum differs from the outstanding balance.
- The ledger is used when resetting a reconciliation to restore the previous payment state safely.

### 3. Payment Reminders

- **4 Reminder Strategies**:
  - `DEFAULT`: Standard reminders (7 days before, on due date, 7 days after)
  - `AGGRESSIVE`: Frequent reminders (3 days before, on due date, every 3 days after)
  - `GENTLE`: Minimal reminders (on due date, 14 days after)
  - `MINIMAL`: Single reminder on due date only

- **Email Templates**: Professional, customizable templates
- **Automatic Scheduling**: Schedule reminders when invoice is created
- **Cancellation**: Auto-cancel when payment received

## Architecture

### Hexagonal Architecture (Ports & Adapters)

```
┌──────────────────────────────────────────────────────────────┐
│                      CLI / API Layer                         │
│                   (openfatture.payment.cli)                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                  Application Services                        │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Reconciliation │  │   Matching   │  │ Reminder        │  │
│  │ Service        │  │   Service    │  │ Scheduler       │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                     Domain Layer                             │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  BankAccount   │  │ Bank         │  │ Payment         │  │
│  │                │  │ Transaction  │  │ Reminder        │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
│                                                              │
│  Enums: TransactionStatus, MatchType, ReminderStatus        │
│  Value Objects: MatchResult, ReminderStrategy               │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ CSV Importer   │  │ OFX Importer │  │ QIF Importer    │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ SQLAlchemy     │  │ Email        │  │ Metrics         │  │
│  │ Repository     │  │ Notifier     │  │ Exporter        │  │
│  └────────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Domain-Driven Design Principles

- **Entities**: BankAccount, BankTransaction, PaymentReminder
- **Value Objects**: MatchResult, ReminderStrategy, ImportSource
- **Aggregates**: BankAccount (root) contains Transactions
- **Services**: ReconciliationService, MatchingService
- **Repositories**: Database access abstraction
- **Events**: (planned) Event-driven notifications

---

## Domain Models

### BankAccount

Represents a bank account for transaction tracking.

```python
from openfatture.payment import BankAccount

account = BankAccount(
    name="Intesa Business Account",
    iban="IT60X0542811101000000123456",
    bic_swift="BCITITMM",
    bank_name="Intesa Sanpaolo",
    currency="EUR",
    opening_balance=Decimal("5000.00"),
    is_active=True
)
```

**Attributes**:
- `name` (str): Friendly account name
- `iban` (str): IBAN (27 chars for Italy)
- `bic_swift` (str): BIC/SWIFT code (8-11 chars)
- `bank_name` (str): Bank name
- `currency` (str): ISO 4217 currency code (default: EUR)
- `opening_balance` (Decimal): Opening balance
- `current_balance` (Decimal): Current balance (auto-updated)
- `last_sync_date` (datetime): Last import date
- `is_active` (bool): Account status

### BankTransaction

Represents a single bank transaction from import.

```python
from openfatture.payment import BankTransaction, TransactionStatus

transaction = BankTransaction(
    account_id=account.id,
    date=date(2025, 10, 5),
    amount=Decimal("1500.00"),
    description="BONIFICO SEPA DA MARIO ROSSI SRL",
    reference="TRN-2025-10-05-123456",
    counterparty="MARIO ROSSI SRL",
    counterparty_iban="IT28W8000000292100645211151",
    status=TransactionStatus.UNMATCHED,
    import_source=ImportSource.CSV
)
```

**Attributes**:
- `id` (UUID): Unique transaction ID
- `account_id` (int): Foreign key to BankAccount
- `date` (date): Transaction date
- `amount` (Decimal): Amount (positive = incoming, negative = outgoing)
- `description` (str): Bank description
- `reference` (str): Bank reference/memo
- `counterparty` (str): Other party name
- `counterparty_iban` (str): Other party IBAN
- `status` (TransactionStatus): UNMATCHED/MATCHED/IGNORED
- `matched_payment_id` (int): FK to Pagamento if matched
- `match_confidence` (float): Match confidence (0.0-1.0)
- `match_type` (MatchType): Matching algorithm used
- `import_source` (ImportSource): CSV/OFX/QIF/MANUAL

**Methods**:
- `match_to_payment(payment, confidence, match_type)` - Match to invoice
- `unmatch()` - Remove match
- `ignore()` - Mark as ignored
- `is_incoming` - Check if incoming payment
- `is_outgoing` - Check if outgoing payment

### Pagamento

Stores the expected amount for an invoice instalment and its progressive collections.

```python
from openfatture.storage.database.models import Pagamento, StatoPagamento

payment = Pagamento(
    fattura_id=fattura.id,
    importo=Decimal("1200.00"),
    data_scadenza=date(2025, 11, 30),
    stato=StatoPagamento.DA_PAGARE,
)

# Apply partial payment (e.g. €400 acconto)
payment.apply_payment(Decimal("400.00"))
assert payment.importo_pagato == Decimal("400.00")
assert payment.saldo_residuo == Decimal("800.00")
assert payment.stato == StatoPagamento.PAGATO_PARZIALE
```

**Key fields & helpers**:
- `importo` (Decimal): Total amount due for the instalment.
- `importo_pagato` (Decimal): Progressive amount collected (auto-managed).
- `stato` (StatoPagamento): Includes `PAGATO_PARZIALE` for in-progress payments.
- `saldo_residuo` (property): Remaining amount still to be paid.
- `apply_payment(amount, pagamento_effective_date)` / `revert_payment(amount)`: Safe domain helpers used by the reconciliation service.
- `allocations`: Relationship to the `PaymentAllocation` ledger entries linked to each bank transaction.

### PaymentAllocation

Immutable ledger entry linking a bank transaction (or portion of it) to a payment.

```python
from openfatture.payment.domain.payment_allocation import PaymentAllocation
allocation = PaymentAllocation(
    payment_id=payment.id,
    transaction_id=transaction.id,
    amount=Decimal("400.00"),
    match_type=MatchType.MANUAL,
    match_confidence=1.0,
)
```

**Purpose**:
- Captures how much of a transaction was allocated to a given payment.
- Provides metadata (match type/confidence) for audits.
- Enables safe reversals via `reset_transaction`, which reads and removes the allocation entry.

### PaymentReminder

Represents a scheduled payment reminder.

```python
from openfatture.payment import PaymentReminder, ReminderStatus, ReminderStrategy

reminder = PaymentReminder(
    payment_id=payment.id,
    reminder_date=date(2025, 10, 20),
    status=ReminderStatus.PENDING,
    strategy=ReminderStrategy.DEFAULT,
    email_template="default",
    email_subject="Reminder: Invoice #001 Payment Due",
)
```

**Attributes**:
- `payment_id` (int): FK to Pagamento
- `reminder_date` (date): When to send reminder
- `status` (ReminderStatus): PENDING/SENT/FAILED/CANCELLED
- `strategy` (ReminderStrategy): DEFAULT/AGGRESSIVE/GENTLE/MINIMAL
- `email_template` (str): Template name
- `email_subject` (str): Subject line
- `email_body` (str): Email body (if custom)
- `sent_date` (datetime): When sent
- `error_message` (str): Error if failed

**Methods**:
- `mark_sent()` - Mark as sent
- `mark_failed(error)` - Mark as failed with error
- `cancel()` - Cancel reminder
- `is_overdue_reminder` - Check if overdue

---

## Bank Statement Import

### Supported Formats

#### 1. CSV Import

**Pre-configured Bank Presets**:
- Intesa Sanpaolo
- UniCredit
- BNL (Banca Nazionale del Lavoro)
- Monte dei Paschi di Siena
- Banco BPM
- Generic Italian banks

**Custom CSV Format**:
```csv
Date,Amount,Description,Reference,Counterparty,IBAN
2025-10-01,1500.00,"Payment from Client A","TRN-001","Client A SRL","IT28W8000000292100645211151"
2025-10-03,-500.00,"Supplier payment","TRN-002","Supplier B","IT60X0542811101000000123456"
```

#### 2. OFX (Open Financial Exchange)

Standard format used by most banks worldwide.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20251001</DTPOSTED>
            <TRNAMT>1500.00</TRNAMT>
            <FITID>TRN-001</FITID>
            <NAME>Client A SRL</NAME>
            <MEMO>Invoice payment</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
```

#### 3. QIF (Quicken Interchange Format)

Legacy format still supported by some banks.

```
!Type:Bank
D10/01/2025
T1500.00
PClient A SRL
MInvoice payment
^
D10/03/2025
T-500.00
PSupplier B
MSupplier payment
^
```

### Import via CLI

```bash
# Import from CSV with preset
openfatture payment import transactions.csv --preset intesa --account-id 1

# Import from OFX
openfatture payment import statement.ofx --account-id 1

# Import from QIF
openfatture payment import transactions.qif --account-id 1

# Import with custom format (CSV)
openfatture payment import custom.csv --account-id 1 \
  --date-col "Data" \
  --amount-col "Importo" \
  --description-col "Descrizione"
```

### Import via Python API

```python
from openfatture.payment.infrastructure.importers import CSVImporter, OFXImporter
from openfatture.payment.infrastructure.importers.presets import ITALIAN_BANK_PRESETS

# CSV import with preset
importer = CSVImporter(preset=ITALIAN_BANK_PRESETS["intesa"])
transactions = importer.import_file("statement.csv", account_id=1)
print(f"Imported {len(transactions)} transactions")

# OFX import
importer = OFXImporter()
transactions = importer.import_file("statement.ofx", account_id=1)

# Custom CSV format
importer = CSVImporter(
    date_column="Date",
    amount_column="Amount",
    description_column="Description",
    iban_column="IBAN",
    date_format="%Y-%m-%d"
)
transactions = importer.import_file("custom.csv", account_id=1)
```

---

## Reconciliation Engine

### Matching Strategies

#### 1. Exact Matcher

Matches transactions to payments with exact amount and date.

```python
from openfatture.payment.matchers import ExactAmountMatcher

matcher = ExactAmountMatcher(date_tolerance_days=0)
result = matcher.match(transaction, payments)

if result.matched:
    print(f"Exact match: {result.payment.numero_fattura}")
    print(f"Confidence: {result.confidence:.2f}")
```

**Parameters**:
- `date_tolerance_days` (int): Date tolerance (default: 0)

**Confidence**: 1.0 if exact match, 0.0 otherwise

#### 2. Fuzzy Matcher

Uses RapidFuzz for similarity-based description matching.

```python
from openfatture.payment.matchers import FuzzyDescriptionMatcher

matcher = FuzzyDescriptionMatcher(
    description_threshold=0.7,
    amount_threshold=0.95
)
result = matcher.match(transaction, payments)

if result.matched:
    print(f"Fuzzy match: {result.payment.numero_fattura}")
    print(f"Similarity: {result.confidence:.2%}")
```

**Parameters**:
- `description_threshold` (float): Minimum similarity (0.0-1.0, default: 0.7)
- `amount_threshold` (float): Amount tolerance (0.0-1.0, default: 0.95)

**Algorithm**: Uses `fuzz.token_sort_ratio` from RapidFuzz

#### 3. IBAN Matcher

Matches by counterparty IBAN when available.

```python
from openfatture.payment.matchers import IBANMatcher

matcher = IBANMatcher()
result = matcher.match(transaction, payments)
```

**Confidence**: 1.0 if IBAN matches, 0.0 otherwise

#### 4. Date Window Matcher

Flexible date range matching.

```python
from openfatture.payment.matchers import DateWindowMatcher

matcher = DateWindowMatcher(window_days=7)  # ±7 days
result = matcher.match(transaction, payments)
```

**Parameters**:
- `window_days` (int): Days before/after due date (default: 7)

#### 5. Composite Matcher (Recommended)

Combines all strategies with weighted scoring.

```python
from openfatture.payment.matchers import CompositeMatcher

matcher = CompositeMatcher(
    weights={
        "exact": 0.4,
        "fuzzy": 0.3,
        "iban": 0.2,
        "date_window": 0.1
    },
    min_confidence=0.7
)
result = matcher.match(transaction, payments)
```

**Parameters**:
- `weights` (dict): Strategy weights (must sum to 1.0)
- `min_confidence` (float): Minimum confidence for match (default: 0.7)

**Recommended for production**: Provides best accuracy (95%+)

### Reconciliation Service

High-level service for automated reconciliation.

```python
from openfatture.payment.application.services import ReconciliationService

service = ReconciliationService(session, matcher=CompositeMatcher())

# Reconcile all unmatched transactions
results = service.reconcile_unmatched_transactions()

for result in results:
    if result.matched:
        print(f"✓ Matched: Transaction {result.transaction.id} → "
              f"Invoice {result.payment.numero_fattura} "
              f"(confidence: {result.confidence:.2%})")
    else:
        print(f"✗ No match for transaction {result.transaction.id}")

# Reconcile specific transaction
transaction = session.query(BankTransaction).filter_by(id=uuid).first()
result = service.reconcile_transaction(transaction)

if result.matched and result.confidence < 0.8:
    # Low confidence - request manual review
    print("Low confidence match - please review manually")
```

---

## Payment Reminders

### Reminder Strategies

```python
from openfatture.payment.domain.enums import ReminderStrategy

# DEFAULT: Standard reminders
# - 7 days before due date
# - On due date
# - 7 days after due date
strategy = ReminderStrategy.DEFAULT

# AGGRESSIVE: Frequent reminders
# - 3 days before
# - On due date
# - 3, 6, 9 days after
strategy = ReminderStrategy.AGGRESSIVE

# GENTLE: Minimal reminders
# - On due date
# - 14 days after
strategy = ReminderStrategy.GENTLE

# MINIMAL: Single reminder on due date
strategy = ReminderStrategy.MINIMAL
```

### Scheduling Reminders

```python
from openfatture.payment.application.services import ReminderScheduler

scheduler = ReminderScheduler(session)

# Schedule reminders for a payment with DEFAULT strategy
reminders = scheduler.schedule_reminders_for_payment(
    payment=payment,
    strategy=ReminderStrategy.DEFAULT
)
print(f"Scheduled {len(reminders)} reminders")

# Schedule for all unpaid invoices
count = scheduler.schedule_reminders_for_unpaid_invoices()
print(f"Scheduled reminders for {count} invoices")
```

### Sending Reminders

```python
from openfatture.payment.application.notifications import ReminderNotifier

notifier = ReminderNotifier(session, email_sender=pec_sender)

# Process pending reminders (run daily via cron)
results = notifier.process_pending_reminders()

for result in results:
    if result.success:
        print(f"✓ Sent reminder for invoice {result.reminder.payment.numero_fattura}")
    else:
        print(f"✗ Failed: {result.error}")
```

### CLI Command Reference

The Typer application exposes the following commands (run them via `uv run openfatture payment ...`):

| Command | Description | Key options |
|---------|-------------|-------------|
| `create-account <name>` | Create a bank account used for imports. | `--iban`, `--bank-name`, `--bic`, `--currency`, `--opening-balance`, `--notes` |
| `list-accounts` | List accounts (include inactive ones with `--all`). | `--all` |
| `update-account <id>` | Update account metadata or status. | `--name`, `--iban`, `--bank-name`, `--bic`, `--currency`, `--notes`, `--active/--inactive` |
| `delete-account <id>` | Delete an account and its transactions. | - |
| `import <file>` | Import bank statements and optionally auto-match transactions. | `--account / -a`, `--bank / -b`, `--auto-match/--no-auto-match`, `--confidence` |
| `list-transactions` | Show imported transactions filtered by account/status. | `--account / -a`, `--status`, `--limit` |
| `show-transaction <uuid>` | Display transaction details. | - |
| `match` | Re-run matching for unmatched transactions. | `--account / -a`, `--confidence`, `--auto-apply/--manual-only`, `--limit` |
| `reconcile` | Perform batch reconciliation (`auto` or `preview`). | `--account / -a`, `--mode`, `--confidence` |
| `match-transaction <uuid> <payment_id>` | Manually link a transaction to a payment. | `--match-type`, `--confidence` |
| `unmatch-transaction <uuid>` | Undo a previous reconciliation. | - |
| `queue` | Manage the review queue (interactive or list view). | `--account / -a`, `--interactive/--list-only`, `--min`, `--max` |
| `schedule-reminders <payment_id>` | Schedule reminders for a payment. | `--strategy` (`default` / `aggressive` / `gentle` / `minimal`) |
| `process-reminders` | Process and send due reminders. | `--date` (YYYY-MM-DD) |
| `list-reminders` | List scheduled or sent reminders. | `--status`, `--payment`, `--limit` |
| `cancel-reminder <id>` | Cancel a reminder that has not been sent yet. | - |
| `stats` | Aggregate statistics by status (UNMATCHED/MATCHED/IGNORED). | `--account / -a` |

Examples:

```bash
# Create a bank account
uv run openfatture payment create-account "Intesa Business" \
  --iban IT60X0542811101000000123456 --bank-name "Intesa Sanpaolo" \
  --opening-balance 5000.00

# Import a CSV with the Intesa preset and 90% auto-matching
uv run openfatture payment import data/intesa.csv --account 1 --bank intesa --confidence 0.90

# Re-run matching for a specific account without auto-apply
uv run openfatture payment match --account 1 --confidence 0.75 --manual-only

# Review the queue interactively (confidence range 0.6-0.84)
uv run openfatture payment queue --account 1 --min 0.60 --max 0.84

# Schedule reminders for payment 123 with the aggressive strategy
uv run openfatture payment schedule-reminders 123 --strategy aggressive

# Process reminders due on a specific date
uv run openfatture payment process-reminders --date 2025-01-15

# List pending reminders
uv run openfatture payment list-reminders --status PENDING --limit 20

# Statistiche complessive
uv run openfatture payment stats
```

## API Reference

### Core Classes

- `BankAccount` - Bank account entity
- `BankTransaction` - Transaction entity
- `PaymentReminder` - Reminder entity

### Enums

- `TransactionStatus` - UNMATCHED, MATCHED, IGNORED
- `MatchType` - EXACT, FUZZY, IBAN, DATE_WINDOW, COMPOSITE
- `ReminderStatus` - PENDING, SENT, FAILED, CANCELLED
- `ReminderStrategy` - DEFAULT, AGGRESSIVE, GENTLE, MINIMAL
- `ImportSource` - CSV, OFX, QIF, MANUAL

### Services

- `ReconciliationService` - Auto-reconciliation
- `MatchingService` - Low-level matching
- `ReminderScheduler` - Reminder scheduling

### Matchers

- `ExactAmountMatcher` - Exact amount/date matching
- `FuzzyDescriptionMatcher` - Similarity-based matching
- `IBANMatcher` - IBAN matching
- `DateWindowMatcher` - Flexible date matching
- `CompositeMatcher` - Weighted combination

### Importers

- `CSVImporter` - CSV import with presets
- `OFXImporter` - OFX format import
- `QIFImporter` - QIF format import

---

## Examples

See `examples/payment_examples.py` for complete examples:

1. **Basic Workflow**: Import → Reconcile → Send Reminders
2. **Custom Matcher**: Build custom matching logic
3. **Batch Processing**: Process thousands of transactions
4. **Multi-Account**: Handle multiple bank accounts
5. **Advanced Reconciliation**: Manual review workflow

---

## Best Practices

### 1. Import Frequency

- **Daily**: For active businesses (automated via cron)
- **Weekly**: For small freelancers
- **Monthly**: For low-volume accounts

### 2. Matching Strategy

- **Production**: Use `CompositeMatcher` with `min_confidence=0.7`
- **Testing**: Start with `ExactAmountMatcher`, then add fuzzy matching
- **High-Stakes**: Use `min_confidence=0.9` and manual review

### 3. Reminder Strategy

- **B2B Clients**: Use `DEFAULT` or `GENTLE`
- **B2C Clients**: Use `DEFAULT`
- **Chronic Late Payers**: Use `AGGRESSIVE`
- **High-Value Clients**: Use `MINIMAL` + manual follow-up

### 4. Performance

- **Batch Import**: Use `batch_size=1000` for large imports
- **Index**: Ensure indexes on `date`, `amount`, `status` columns
- **Archiving**: Archive matched transactions older than 1 year

### 5. Security

- **GDPR Compliance**: Anonymize transaction descriptions after 2 years
- **Access Control**: Restrict payment data access to authorized users
- **Audit Trail**: Log all manual reconciliation decisions

### Database Upgrade (Partial Payments Ledger)

For existing deployments, apply the following migration before deploying the new code:

```sql
-- 1. Add progressive amount column
ALTER TABLE pagamenti
    ADD COLUMN IF NOT EXISTS importo_pagato NUMERIC(10, 2) NOT NULL DEFAULT 0;

-- 2. Backfill legacy data (mark fully-paid instalments)
UPDATE pagamenti
SET importo_pagato = CASE
        WHEN stato = 'pagato' THEN importo
        ELSE 0
    END;

-- 3. Create payment allocation ledger
CREATE TABLE IF NOT EXISTS payment_allocations (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES pagamenti(id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES bank_transactions(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    allocated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    match_type VARCHAR(50),
    match_confidence DOUBLE PRECISION,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_payment_allocations_payment_id ON payment_allocations (payment_id);
CREATE INDEX IF NOT EXISTS ix_payment_allocations_transaction_id ON payment_allocations (transaction_id);
```

> ℹ️  If you rely on SQLite for local testing, run the same statements using the `sqlite3` CLI. SQLite will ignore the index names and `SERIAL` keyword automatically.

### Enabling AI Payment Insight

- Configure your preferred LLM provider via the existing AI settings (e.g. `OPENFATTURE_AI_PROVIDER`, `OPENFATTURE_AI_OPENAI_API_KEY`).
- The payment CLI will automatically enable the **PaymentInsightAgent** and log a notice when the provider is available.
- Without credentials the workflow still operates, simply skipping AI-based boosts.

---

## Troubleshooting

### Low Match Rate

**Symptom**: <70% of transactions matched automatically

**Solutions**:
1. Check bank description format - may need custom CSV columns
2. Adjust `description_threshold` in FuzzyDescriptionMatcher (try 0.6)
3. Verify client IBAN is stored in database
4. Use DateWindowMatcher with wider window (14 days)

### Duplicate Imports

**Symptom**: Same transactions imported multiple times

**Solutions**:
1. Implement unique constraint on `(account_id, date, amount, reference)`
2. Use `skip_duplicates=True` in importer
3. Check import source logs for duplicate files

### Failed Reminders

**Symptom**: Reminders stuck in PENDING status

**Solutions**:
1. Check PEC credentials in `.env`
2. Verify email template exists
3. Check notifier logs for SMTP errors
4. Ensure `process-reminders` cron job is running

---

## Related Documentation

- [CLI Reference](CLI_REFERENCE.md) - Full CLI command reference
- [Configuration](CONFIGURATION.md) - Payment module configuration
- [Batch Operations](BATCH_OPERATIONS.md) - CSV import/export workflows
- [API Architecture](AI_ARCHITECTURE.md) - AI-powered features

---

**Last Updated**: October 10, 2025
**Module Version**: 0.2.0-rc1
**Maintainer**: OpenFatture Core Team
