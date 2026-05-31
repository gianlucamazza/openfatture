# Payment Tracking & Bank Reconciliation Module

**Enterprise-grade payment tracking and bank reconciliation system for OpenFatture**

Version: 1.0.0 | Python 3.12+ | License: GPL-3.0

---

## Overview

The Payment Tracking Module provides comprehensive bank reconciliation and payment monitoring capabilities for Italian freelancers and small businesses. It automatically matches bank transactions with invoice payments using intelligent matching algorithms, sends automated payment reminders, and provides a rich CLI interface for manual reconciliation.

### Key Features

- **Multi-Bank Support** - Import statements from CSV, OFX, QIF formats
- **Intelligent Matching** - 5 matching algorithms with confidence scoring
- **Bank Presets** - Pre-configured for Intesa Sanpaolo, UniCredit, Revolut
- **Smart Workflow** - Auto-apply high-confidence, review medium-confidence matches
- **Payment Reminders** - Automated escalation strategies (DEFAULT, PROGRESSIVE, AGGRESSIVE)
- **Multi-Channel Notifications** - Email, SMS, webhook with Jinja2 templates
- **Rich CLI** - Interactive reconciliation with progress tracking
- **Clean Architecture** - Hexagonal, DDD, SOLID principles

---

## Architecture

### Design Patterns

- **Hexagonal Architecture** (Ports & Adapters) - Clear separation of domain, application, and infrastructure
- **Domain-Driven Design** - Rich domain models with behavior, aggregates, value objects
- **Strategy Pattern** - Pluggable matching algorithms and notification channels
- **Saga Pattern** - Multi-step reconciliation workflow with rollback capabilities
- **Facade Pattern** - Simplified MatchingService API for complex matching operations
- **Composite Pattern** - Multi-channel notification system
- **Factory Pattern** - Bank statement importer detection and creation

### Layer Structure

```
payment/
├── domain/                    # Domain Layer (pure business logic)
│   ├── models.py             # Entities: BankAccount, BankTransaction, PaymentReminder
│   ├── value_objects.py      # Value Objects: MatchResult, ReconciliationResult
│   ├── enums.py              # Enums: TransactionStatus, MatchType, ReminderStatus
│   └── payment_allocation.py # Allocation tracking for reversals
│
├── application/               # Application Layer (use cases)
│   ├── services/
│   │   ├── matching_service.py        # Facade for matching operations
│   │   ├── reconciliation_service.py  # Saga-based reconciliation workflow
│   │   └── reminder_scheduler.py      # Automated reminder system
│   └── notifications/
│       └── notifier.py       # Strategy-based notification system
│
├── infrastructure/            # Infrastructure Layer (technical concerns)
│   ├── repository.py         # Data access layer (SQLAlchemy)
│   └── importers/
│       ├── base.py           # Abstract importer interface
│       ├── csv_importer.py   # CSV format with bank presets
│       ├── ofx_importer.py   # OFX/QFX format
│       ├── qif_importer.py   # Quicken QIF format
│       ├── factory.py        # Auto-detection factory
│       └── presets.py        # Bank-specific field mappings
│
├── matchers/                  # Matching Strategies
│   ├── base.py               # IMatchingStrategy interface
│   ├── exact.py              # ExactAmountMatcher (amount + date)
│   ├── fuzzy.py              # FuzzyDescriptionMatcher (NLP)
│   ├── iban.py               # IBANMatcher (direct validation)
│   ├── date_window.py        # DateWindowMatcher (flexible dates)
│   └── composite.py          # CompositeMatcher (weighted combination)
│
├── cli/                       # CLI Interface
│   └── payment_cli.py        # Typer commands (import, reconcile, etc.)
│
└── templates/                 # Email Templates
    ├── reminder_email.html   # HTML template
    └── reminder_email.txt    # Text fallback
```

---

## Domain Models

### BankAccount

Represents a business bank account with IBAN validation.

```python
from openfatture.payment.domain.models import BankAccount

account = BankAccount(
    name="Conto Corrente Intesa",
    iban="IT60X0542811101000000123456",
    bic_swift="BCITITMM",
    bank_name="Intesa Sanpaolo"
)
```

**Fields:**
- `id`: Auto-generated primary key
- `name`: Account display name
- `iban`: IBAN code (validated)
- `bic_swift`: BIC/SWIFT code
- `bank_name`: Bank institution name

### BankTransaction

Bank statement transaction with lifecycle management.

```python
from openfatture.payment.domain.models import BankTransaction
from openfatture.payment.domain.enums import TransactionStatus

transaction = BankTransaction(
    account_id=account.id,
    date=date(2025, 10, 15),
    amount=Decimal("1220.00"),
    description="Pagamento fattura 2025/001",
    status=TransactionStatus.UNMATCHED
)
```

**Lifecycle:** UNMATCHED MATCHED IGNORED

**Fields:**
- `id`: UUID identifier
- `account_id`: Foreign key to BankAccount
- `date`: Transaction date
- `amount`: Transaction amount (positive for income)
- `description`: Transaction description
- `status`: Current status (enum)
- `matched_payment_id`: Linked payment ID (when matched)
- `match_type`: Type of match (MANUAL, EXACT, FUZZY, etc.)
- `match_confidence`: Confidence score (0.0-1.0)
- `matched_at`: Timestamp of matching

### PaymentReminder

Automated payment reminder with escalation strategies.

```python
from openfatture.payment.domain.models import PaymentReminder
from openfatture.payment.domain.enums import ReminderStrategy, ReminderStatus

reminder = PaymentReminder(
    payment_id=payment.id,
    reminder_date=date(2025, 10, 24),
    strategy=ReminderStrategy.PROGRESSIVE,
    status=ReminderStatus.PENDING
)
```

**Strategies:**
- `DEFAULT`: Single reminder at due date
- `PROGRESSIVE`: -7, -3, 0, +3, +7 days
- `AGGRESSIVE`: -14, -7, -3, 0, +1, +3, +5, +7, +10, +14 days
- `CUSTOM`: User-defined schedule

---

## Application Services

### MatchingService

Facade for payment matching operations using multiple strategies.

```python
from openfatture.payment.application.services import MatchingService
from openfatture.payment.matchers import ExactAmountMatcher, FuzzyDescriptionMatcher

matching_service = MatchingService(
    tx_repo=tx_repo,
    payment_repo=payment_repo,
    strategies=[
        ExactAmountMatcher(date_tolerance_days=30),
        FuzzyDescriptionMatcher(threshold=0.7)
    ]
)

# Match single transaction
matches = await matching_service.match_transaction(
    transaction,
    confidence_threshold=0.60
)

# Batch matching
result = await matching_service.match_batch(
    account_id=1,
    auto_apply_threshold=0.85
)
```

### ReconciliationService

Saga-based reconciliation workflow with state transitions and rollback.

```python
from openfatture.payment.application.services import ReconciliationService
from openfatture.payment.domain.enums import MatchType

reconciliation_service = ReconciliationService(
    tx_repo=tx_repo,
    payment_repo=payment_repo,
    matching_service=matching_service
)

# Reconcile transaction to payment
transaction = await reconciliation_service.reconcile(
    transaction_id=tx_id,
    payment_id=payment_id,
    match_type=MatchType.MANUAL,
    confidence=0.95
)

# Reset transaction (undo reconciliation)
transaction = await reconciliation_service.reset_transaction(tx_id)

# Ignore non-business transaction
transaction = await reconciliation_service.ignore_transaction(
    tx_id,
    reason="Personal expense"
)

# Get review queue
queue = await reconciliation_service.get_review_queue(
    account_id=1,
    confidence_range=(0.60, 0.84)
)
```

### ReminderScheduler

Automated payment reminder system with strategy-based scheduling.

```python
from openfatture.payment.application.services import ReminderScheduler
from openfatture.payment.application.notifications import EmailNotifier, SMTPConfig

# Setup notifier
smtp_config = SMTPConfig(
    host="smtp.gmail.com",
    port=587,
    username="your@email.com",
    password="your_password",
    from_email="noreply@yourcompany.com"
)
email_notifier = EmailNotifier(smtp_config)

scheduler = ReminderScheduler(
    payment_repo=payment_repo,
    notifier=email_notifier
)

# Schedule reminders
count = await scheduler.schedule_reminders(
    payment_ids=[1, 2, 3],
    strategy=ReminderStrategy.PROGRESSIVE
)

# Process due reminders
processed = await scheduler.process_due_reminders()
```

---

## Matching Strategies

### ExactAmountMatcher

Matches by exact amount within a date tolerance window.

```python
from openfatture.payment.matchers import ExactAmountMatcher

matcher = ExactAmountMatcher(date_tolerance_days=30)
matches = await matcher.match(transaction, candidate_payments)
```

**Algorithm:**
1. Filter payments with exact amount match
2. Check if transaction date is within ±`date_tolerance_days` of payment due date
3. Return confidence: 1.0 (perfect match)

### FuzzyDescriptionMatcher

NLP-based description matching using Levenshtein distance.

```python
from openfatture.payment.matchers import FuzzyDescriptionMatcher

matcher = FuzzyDescriptionMatcher(threshold=0.7, date_tolerance_days=90)
matches = await matcher.match(transaction, candidate_payments)
```

**Algorithm:**
1. Extract invoice number from transaction description (regex: `\d{3,}`)
2. Compare with payment invoice numbers using Levenshtein ratio
3. Return confidence: ratio score (0.0-1.0)

### IBANMatcher

Direct IBAN/BIC validation for wire transfers.

```python
from openfatture.payment.matchers import IBANMatcher

matcher = IBANMatcher()
matches = await matcher.match(transaction, candidate_payments)
```

**Algorithm:**
1. Extract IBAN from transaction metadata
2. Match against client IBAN in payment invoice
3. Return confidence: 1.0 (exact match) or 0.0

### CompositeMatcher

Weighted combination of multiple strategies.

```python
from openfatture.payment.matchers import CompositeMatcher

matcher = CompositeMatcher(
    strategies=[
        (ExactAmountMatcher(date_tolerance_days=30), 0.5),
        (FuzzyDescriptionMatcher(threshold=0.7), 0.3),
        (IBANMatcher(), 0.2)
    ]
)
matches = await matcher.match(transaction, candidate_payments)
```

**Algorithm:**
1. Run all sub-strategies in parallel
2. Aggregate results with weighted average: `confidence = Σ(strategy_conf × weight)`
3. Deduplicate and sort by confidence

---

## Bank Statement Import

### Supported Formats

| Format | Extension | Use Case | Banks |
|--------|-----------|----------|-------|
| CSV | `.csv` | Most Italian banks | Intesa Sanpaolo, UniCredit, Revolut |
| OFX | `.ofx`, `.qfx` | Quicken, QuickBooks | Most US/EU banks |
| QIF | `.qif` | Legacy Quicken | Older systems |

### CSV Import with Bank Presets

```python
from openfatture.payment.infrastructure.importers import CSVImporter
from openfatture.payment.infrastructure.importers.presets import BankPreset

# Auto-detect bank
importer = CSVImporter.from_file(
    file_path=Path("statement.csv"),
    account=account
)

# Or specify preset
importer = CSVImporter(
    file_path=Path("statement.csv"),
    account=account,
    preset=BankPreset.INTESA_SANPAOLO
)

transactions = importer.import_transactions()
```

### Bank Presets

**Intesa Sanpaolo:**
- Date format: `DD/MM/YYYY`
- Amount columns: `Entrate` (credit), `Uscite` (debit)
- Delimiter: `;`
- Encoding: `latin-1`

**UniCredit:**
- Date format: `DD-MM-YYYY`
- Amount column: `Importo` (signed)
- Delimiter: `;`
- Encoding: `latin-1`

**Revolut:**
- Date format: `YYYY-MM-DD`
- Amount column: `Amount` (signed)
- Delimiter: `,`
- Encoding: `utf-8`

### Custom CSV Mapping

```python
from openfatture.payment.infrastructure.importers import CSVImporter, FieldMapping

mapping = FieldMapping(
    date="Data operazione",
    amount="Importo",
    description="Causale",
    date_format="%d/%m/%Y",
    amount_credit="Entrate",
    amount_debit="Uscite"
)

importer = CSVImporter(
    file_path=Path("custom_bank.csv"),
    account=account,
    field_mapping=mapping,
    delimiter=";",
    encoding="latin-1"
)
```

---

## CLI Usage

### Import Transactions

```bash
# Import with auto-detection
openfatture payment import transactions.csv --account-id 1

# Specify format
openfatture payment import statement.ofx --account-id 1 --format ofx

# Specify bank preset
openfatture payment import intesa.csv --account-id 1 --preset intesa_sanpaolo
```

### List Transactions

```bash
# List all transactions
openfatture payment list-transactions

# Filter by status
openfatture payment list-transactions --status UNMATCHED

# Filter by account
openfatture payment list-transactions --account-id 1

# Pagination
openfatture payment list-transactions --limit 50 --offset 100
```

### Reconcile Transactions

```bash
# Interactive reconciliation (shows matches with confidence)
openfatture payment reconcile <transaction-id>

# Manual reconciliation
openfatture payment reconcile <transaction-id> --payment-id 123

# Review queue (medium-confidence matches)
openfatture payment review --account-id 1

# Batch auto-reconcile (high-confidence only)
openfatture payment batch-reconcile --account-id 1 --threshold 0.85
```

### Transaction Management

```bash
# Ignore transaction (mark as non-business)
openfatture payment ignore <transaction-id> --reason "Personal expense"

# Reset transaction (undo reconciliation)
openfatture payment reset <transaction-id>
```

### Payment Reminders

```bash
# Schedule reminders for payment
openfatture payment reminders schedule --payment-id 123 --strategy PROGRESSIVE

# Process due reminders
openfatture payment reminders process

# List pending reminders
openfatture payment reminders list --status PENDING
```

---

## Testing

The module includes comprehensive test coverage:

- **Unit Tests**: 62 tests covering all components
- **Integration Tests**: 12 end-to-end workflow tests
- **Test Coverage**: 82-96% on critical services
- **Property-Based Testing**: Hypothesis for edge cases

### Running Tests

```bash
# All payment tests
pytest tests/payment/

# Specific test file
pytest tests/payment/application/services/test_reconciliation_service.py -v

# With coverage
pytest tests/payment/ --cov=openfatture.payment --cov-report=html

# Integration tests only
pytest tests/payment/test_integration_workflow.py -v
```

### CI/CD

GitHub Actions workflow at `.github/workflows/payment-tests.yml`:
- Multi-OS: Ubuntu, macOS, Windows
- Multi-Python: 3.12, 3.13
- Coverage enforcement: 85% minimum
- PostgreSQL integration tests

---

## Configuration

### Database Models

The module adds these tables to the OpenFatture database:

- `bank_accounts`: Bank account information
- `bank_transactions`: Imported transactions with matching state
- `payment_reminders`: Scheduled reminders
- `payment_allocations`: Allocation tracking for reversals

### SMTP Configuration

For email notifications, configure in `.env`:

```env
# SMTP Server
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_FROM_NAME=Your Company

# Email templates directory (optional)
PAYMENT_TEMPLATE_DIR=openfatture/payment/templates
```

---

## Examples

See `examples/payment_examples.py` for complete usage examples:

```python
# Run all examples
uv run python examples/payment_examples.py

# Or import specific functions
from examples.payment_examples import (
    example_import_csv,
    example_matching,
    example_reconciliation,
    example_reminders
)
```

---

## API Reference

### Repositories

**BankTransactionRepository:**
- `get_by_id(transaction_id: UUID) -> BankTransaction | None`
- `get_by_account(account_id: int) -> list[BankTransaction]`
- `get_by_status(status: TransactionStatus, account_id: int | None = None) -> list[BankTransaction]`
- `add(transaction: BankTransaction) -> BankTransaction`
- `update(transaction: BankTransaction) -> BankTransaction`
- `delete(transaction_id: UUID) -> None`

**PaymentRepository:**
- `get_by_id(payment_id: int) -> Pagamento | None`
- `get_unpaid(cliente_id: int | None = None) -> list[Pagamento]`
- `add_allocation(allocation: PaymentAllocation) -> PaymentAllocation`
- `get_allocation(payment_id: int, transaction_id: UUID) -> PaymentAllocation | None`
- `delete_allocation(allocation: PaymentAllocation) -> None`

### Value Objects

**MatchResult:**
- `payment`: Matched payment entity
- `confidence`: Confidence score (0.0-1.0)
- `match_type`: Type of match (enum)
- `reason`: Explanation of match

**ReconciliationResult:**
- `total_transactions`: Total transactions processed
- `matched_count`: Number of matches found
- `auto_reconciled_count`: High-confidence auto-applied
- `review_needed_count`: Medium-confidence requiring review
- `matches`: List of (transaction, [MatchResult])

---

## Performance

### Benchmarks

Tested on MacBook Pro M1 (2020):

| Operation | Dataset | Time | Throughput |
|-----------|---------|------|------------|
| CSV Import | 1,000 transactions | 0.8s | 1,250 tx/s |
| Batch Matching | 500 tx × 100 payments | 12s | 42 tx/s |
| Exact Matcher | 1,000 comparisons | 0.05s | 20,000/s |
| Fuzzy Matcher | 1,000 comparisons | 2.5s | 400/s |
| Composite Matcher | 1,000 comparisons | 3.0s | 333/s |

### Optimization Tips

1. **Use ExactAmountMatcher first** - It's 50x faster than fuzzy matching
2. **Limit candidate payments** - Filter by date range and amount before matching
3. **Batch operations** - Use `match_batch()` for better concurrency
4. **Composite weights** - Give higher weight to fast matchers (Exact, IBAN)
5. **Date tolerance** - Reduce tolerance days for faster filtering

---

## Troubleshooting

### Common Issues

**Issue: CSV import fails with encoding error**
```
Solution: Specify encoding explicitly:
importer = CSVImporter(file_path=path, encoding="latin-1")
```

**Issue: No matches found for obvious matches**
```
Solution: Increase date_tolerance_days or lower confidence_threshold:
matcher = ExactAmountMatcher(date_tolerance_days=60)
matches = await matching_service.match_transaction(tx, confidence_threshold=0.50)
```

**Issue: Payment reminders not sending**
```
Solution: Check SMTP configuration and test with ConsoleNotifier first:
from openfatture.payment.application.notifications import ConsoleNotifier
scheduler = ReminderScheduler(payment_repo=repo, notifier=ConsoleNotifier())
```

**Issue: Duplicate transaction imports**
```
Solution: Module includes automatic deduplication. Check transaction IDs in logs.
```

---

## Contributing

The payment module follows strict coding standards:

- **Type Safety**: Full mypy compliance with no `Any` types
- **Testing**: 85%+ coverage required
- **Documentation**: Docstrings for all public APIs
- **Design Patterns**: Follow existing architectural patterns
- **SOLID Principles**: Single Responsibility, Open/Closed, etc.

### Adding a New Matcher

1. Implement `IMatchingStrategy` interface in `payment/matchers/`
2. Add docstrings with algorithm explanation
3. Write unit tests with edge cases
4. Update `CompositeMatcher` documentation
5. Add example to `examples/payment_examples.py`

---

## License

GPL-3.0-or-later - See LICENSE file

---

## Support

- **Documentation**: This README + inline docstrings
- **Examples**: `examples/payment_examples.py`
- **Tests**: `tests/payment/` for usage patterns
- **Issues**: [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)

---

**Built with following Clean Architecture, DDD, and SOLID principles**
