"""
Payment Tracking and Reconciliation Examples.

This script demonstrates how to use the Payment Tracking module for:
- Bank statement import (CSV/OFX/QIF)
- Automated payment matching (5 strategies)
- Manual reconciliation
- Payment reminders
- Batch operations
- Prometheus metrics

Architecture: Domain-Driven Design (DDD) + Hexagonal Architecture

Requirements:
    - OpenFatture database initialized
    - Sample bank statements (CSV format)
    - Payment data in database

Run:
    python examples/payment_examples.py
"""

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from openfatture.payment import (
    BankAccount,
    BankTransaction,
    MatchType,
    TransactionStatus,
    record_reconciliation,
    record_transaction_import,
)
from openfatture.payment.application.services.matching_service import MatchingService
from openfatture.payment.application.services.reconciliation_service import ReconciliationService
from openfatture.payment.application.services.reminder_scheduler import ReminderScheduler
from openfatture.payment.domain.enums import ImportSource, ReminderStrategy
from openfatture.payment.infrastructure.importers.csv_importer import CSVConfig, CSVImporter
from openfatture.payment.infrastructure.repository import (
    BankTransactionRepository,
    PaymentReminderRepository,
    PaymentRepository,
)
from openfatture.payment.matchers import (
    CompositeMatcher,
    ExactAmountMatcher,
    FuzzyDescriptionMatcher,
    IBANMatcher,
)
from openfatture.storage.database import SessionManager, init_db
from openfatture.storage.database.models import Pagamento

if TYPE_CHECKING:
    pass


def create_sample_csv(file_path: Path) -> None:
    """Create a sample CSV bank statement for testing.

    This simulates a typical Italian bank CSV export with:
    - Semicolon delimiter (common in Italy)
    - European date format (DD/MM/YYYY)
    - European decimal format (1.234,56)
    - Italian column headers
    """
    content = """Data;Importo;Descrizione;Riferimento;Beneficiario;IBAN
15/10/2024;1500,00;Bonifico ricevuto;INV-001;Acme Corp;IT60X0542811101000000123456
16/10/2024;2500,00;Bonifico ricevuto;Fattura 002;Tech Solutions SRL;IT28W8000000292100645211288
17/10/2024;750,50;Bonifico ricevuto;Payment Invoice 003;Cliente Beta;IT60X0542811101000000654321
18/10/2024;-50,00;Commissioni bancarie;Fee Q4;;
19/10/2024;1200,00;Bonifico ricevuto;REF-004;Gamma Industries;IT97X0326822881000052489654
20/10/2024;3000,00;Bonifico ricevuto;FAT-005;Delta Corporation;IT40S0542811101000000098765
"""
    file_path.write_text(content, encoding="utf-8")
    print(f"✅ Created sample CSV at: {file_path}")


def create_sample_payments(session: Session) -> list[Pagamento]:
    """Create sample payments for matching demonstration.

    Returns:
        List of created Pagamento entities
    """
    payments = [
        Pagamento(
            numero_fattura="INV-001",
            data_emissione=date(2024, 10, 10),
            data_scadenza=date(2024, 10, 31),
            importo_totale=Decimal("1500.00"),
            importo_da_pagare=Decimal("1500.00"),
            importo_pagato=Decimal("0.00"),
            cliente_id=1,  # Assuming client exists
        ),
        Pagamento(
            numero_fattura="002/2024",
            data_emissione=date(2024, 10, 12),
            data_scadenza=date(2024, 11, 12),
            importo_totale=Decimal("2500.00"),
            importo_da_pagare=Decimal("2500.00"),
            importo_pagato=Decimal("0.00"),
            cliente_id=2,
        ),
        Pagamento(
            numero_fattura="003",
            data_emissione=date(2024, 10, 14),
            data_scadenza=date(2024, 11, 14),
            importo_totale=Decimal("750.50"),
            importo_da_pagare=Decimal("750.50"),
            importo_pagato=Decimal("0.00"),
            cliente_id=3,
        ),
        Pagamento(
            numero_fattura="FAT-005",
            data_emissione=date(2024, 10, 15),
            data_scadenza=date(2024, 11, 30),
            importo_totale=Decimal("3000.00"),
            importo_da_pagare=Decimal("3000.00"),
            importo_pagato=Decimal("0.00"),
            cliente_id=4,
        ),
    ]

    for payment in payments:
        session.add(payment)

    session.commit()
    print(f"✅ Created {len(payments)} sample payments")
    return payments


async def example_1_basic_workflow():
    """Example 1: Complete workflow - Import → Match → Reconcile → Remind.

    This demonstrates the typical end-to-end flow:
    1. Import bank transactions from CSV
    2. Auto-match with payments using composite matcher
    3. Reconcile high-confidence matches
    4. Schedule reminders for unpaid invoices
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Complete Payment Workflow")
    print("=" * 80 + "\n")

    # Initialize database
    init_db()
    session = SessionManager.get_session()

    try:
        # Create sample data
        print("📝 Setting up sample data...")

        # Create bank account
        account = BankAccount(
            name="Intesa Sanpaolo Business",
            iban="IT60X0542811101000000123456",
            bic_swift="BPMOIT22XXX",
            bank_name="Intesa Sanpaolo",
            currency="EUR",
            opening_balance=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
        )
        session.add(account)
        session.commit()

        # Create sample payments
        payments = create_sample_payments(session)

        # Create sample CSV
        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)

        create_sample_csv(csv_path)

        # STEP 1: Import transactions from CSV
        print("\n🔄 Step 1: Importing transactions from CSV...")

        config = CSVConfig(
            delimiter=";",
            encoding="utf-8",
            field_mapping={
                "date": "Data",
                "amount": "Importo",
                "description": "Descrizione",
                "reference": "Riferimento",
                "counterparty": "Beneficiario",
                "counterparty_iban": "IBAN",
            },
            date_format="%d/%m/%Y",
            decimal_separator=",",
            thousands_separator=".",
        )

        importer = CSVImporter(csv_path, config)
        transactions = importer.parse(account)

        # Save transactions to database
        for tx in transactions:
            session.add(tx)

        session.commit()

        print(f"✅ Imported {len(transactions)} transactions")
        for tx in transactions[:3]:  # Show first 3
            print(
                f"   • {tx.date}: €{tx.amount:,.2f} - {tx.description[:40]}... "
                f"({tx.status.value})"
            )

        # Record metrics
        record_transaction_import(len(transactions), ImportSource.CSV.value)

        # STEP 2: Auto-match transactions with payments
        print("\n🔍 Step 2: Auto-matching transactions with payments...")

        # Setup repositories
        tx_repo = BankTransactionRepository(session)
        payment_repo = PaymentRepository(session)

        # Create composite matcher with all strategies
        matcher = CompositeMatcher(
            matchers=[
                ExactAmountMatcher(weight=1.0),  # Exact match gets highest priority
                IBANMatcher(weight=0.8),  # IBAN match is also strong
                FuzzyDescriptionMatcher(weight=0.6, threshold=0.7),  # Fuzzy for typos
            ]
        )

        matching_service = MatchingService(
            tx_repo=tx_repo, payment_repo=payment_repo, matchers=[matcher]
        )

        # Get unmatched transactions
        unmatched = tx_repo.get_by_status(TransactionStatus.UNMATCHED)
        print(f"   Found {len(unmatched)} unmatched transactions")

        matches_found = 0
        for tx in unmatched:
            # Skip non-business transactions (bank fees)
            if tx.amount < 0:
                continue

            # Find matching payments
            match_results = await matching_service.match_transaction(tx, confidence_threshold=0.70)

            if match_results:
                best_match = match_results[0]
                print(
                    f"   ✓ Match found: {tx.description[:30]}... → "
                    f"Invoice {best_match.payment.numero_fattura} "
                    f"(confidence: {best_match.confidence:.1%})"
                )
                matches_found += 1

        print(f"\n✅ Found {matches_found} potential matches")

        # STEP 3: Auto-reconcile high-confidence matches
        print("\n💰 Step 3: Auto-reconciling high-confidence matches...")

        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo, payment_repo=payment_repo, matching_service=matching_service
        )

        result = await reconciliation_service.reconcile_batch(
            account_id=account.id, auto_apply=True, auto_apply_threshold=0.85
        )

        print(f"✅ Auto-reconciled: {result.matched_count} transactions")
        print(f"   Review needed: {result.review_count} (confidence 60-84%)")
        print(f"   Unmatched: {result.unmatched_count}")

        # Record metrics
        record_reconciliation(result.matched_count, "auto", success=True)

        # STEP 4: Schedule reminders for unpaid invoices
        print("\n📧 Step 4: Scheduling payment reminders...")

        reminder_repo = PaymentReminderRepository(session)
        reminder_scheduler = ReminderScheduler(
            payment_repo=payment_repo, reminder_repo=reminder_repo, session=session
        )

        # Get overdue payments
        overdue = payment_repo.get_overdue_payments()
        print(f"   Found {len(overdue)} overdue payments")

        scheduled = 0
        for payment in overdue:
            if payment.importo_pagato < payment.importo_da_pagare:
                # Schedule reminder with DEFAULT strategy
                reminders = await reminder_scheduler.schedule_reminders(
                    payment=payment, strategy=ReminderStrategy.DEFAULT
                )
                scheduled += len(reminders)

        print(f"✅ Scheduled {scheduled} reminders")

        # Summary
        print("\n" + "=" * 80)
        print("📊 WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"✅ Imported:         {len(transactions)} transactions")
        print(f"✅ Matched:          {result.matched_count} auto-reconciled")
        print(f"⚠️  Review needed:   {result.review_count}")
        print(f"📧 Reminders:        {scheduled} scheduled")
        print("=" * 80)

        # Cleanup
        csv_path.unlink()

    finally:
        session.close()


async def example_2_csv_import_configurations():
    """Example 2: CSV import with different bank formats.

    Demonstrates how to configure the CSVImporter for various
    Italian bank formats (Intesa, UniCredit, BNL, etc.).
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: CSV Import - Different Bank Formats")
    print("=" * 80 + "\n")

    # Intesa Sanpaolo format (semicolon, European decimals)
    print("🏦 Format 1: Intesa Sanpaolo")
    intesa_config = CSVConfig(
        delimiter=";",
        encoding="ISO-8859-1",
        field_mapping={
            "date": "Data operazione",
            "amount": "Importo",
            "description": "Causale",
            "reference": "Riferimento",
        },
        date_format="%d/%m/%Y",
        decimal_separator=",",
        thousands_separator=".",
        skip_rows=1,  # Skip header row
    )
    print(f"   Delimiter: '{intesa_config.delimiter}'")
    print("   Decimal format: 1.234,56 (European)")
    print("   Date format: DD/MM/YYYY")

    # UniCredit format (CSV, ISO dates)
    print("\n🏦 Format 2: UniCredit")
    unicredit_config = CSVConfig(
        delimiter=",",
        encoding="UTF-8",
        field_mapping={
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
            "reference": "Reference",
            "counterparty_iban": "IBAN",
        },
        date_format="%Y-%m-%d",  # ISO format
        decimal_separator=".",
        skip_rows=0,
    )
    print("   Delimiter: ',' (CSV)")
    print("   Decimal format: 1234.56 (US)")
    print("   Date format: YYYY-MM-DD (ISO)")

    # BNL format (tab-separated)
    print("\n🏦 Format 3: BNL (Banca Nazionale del Lavoro)")
    bnl_config = CSVConfig(
        delimiter="\t",  # Tab-separated
        encoding="UTF-8",
        field_mapping={
            "date": "DATA",
            "amount": "IMPORTO",
            "description": "DESCRIZIONE",
        },
        date_format="%d-%m-%Y",
        decimal_separator=",",
        skip_footer=2,  # Skip footer summary rows
    )
    print("   Delimiter: TAB")
    print("   Skip footer: 2 rows (summary)")

    print("\n✅ Configured 3 different bank formats")
    print("   Use CSVImporter(file_path, config) to import with any format")


async def example_3_matching_strategies():
    """Example 3: Demonstration of all 5 matching strategies.

    Shows how each matcher works and when to use it:
    - ExactAmountMatcher: Exact invoice number match
    - FuzzyDescriptionMatcher: Handles typos and variations
    - IBANMatcher: Matches by client IBAN
    - DateWindowMatcher: Matches by date proximity
    - CompositeMatcher: Combines multiple strategies
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Matching Strategies Comparison")
    print("=" * 80 + "\n")

    init_db()
    session = SessionManager.get_session()

    try:
        # Create test data
        account = BankAccount(name="Test Account", iban="IT123")
        session.add(account)

        payment = Pagamento(
            numero_fattura="INV-2024-042",
            data_emissione=date(2024, 10, 1),
            data_scadenza=date(2024, 10, 31),
            importo_totale=Decimal("1500.00"),
            importo_da_pagare=Decimal("1500.00"),
            importo_pagato=Decimal("0.00"),
            cliente_id=1,
        )
        session.add(payment)
        session.commit()

        # Create transactions with different matching scenarios
        scenarios = [
            {
                "description": "Payment for INV-2024-042",  # Exact match
                "reference": "INV-2024-042",
                "amount": Decimal("1500.00"),
                "scenario": "Exact Match",
            },
            {
                "description": "Payment Invoice 2024/042",  # Fuzzy match (typo)
                "reference": "INV-2024-042-PAID",
                "amount": Decimal("1500.00"),
                "scenario": "Fuzzy Match (variation)",
            },
            {
                "description": "Bonifico ricevuto",  # IBAN match only
                "reference": None,
                "amount": Decimal("1500.00"),
                "scenario": "IBAN Match",
            },
            {
                "description": "Generic payment",  # Date + Amount match
                "reference": None,
                "amount": Decimal("1500.00"),
                "scenario": "Date Window Match",
            },
        ]

        # Initialize matchers
        exact_matcher = ExactAmountMatcher(weight=1.0)
        fuzzy_matcher = FuzzyDescriptionMatcher(weight=0.8, threshold=0.65)
        iban_matcher = IBANMatcher(weight=0.7)

        print("🔍 Testing matching strategies:\n")

        for i, scenario_data in enumerate(scenarios, 1):
            tx = BankTransaction(
                account=account,
                date=date(2024, 10, 15),
                amount=scenario_data["amount"],
                description=scenario_data["description"],
                reference=scenario_data["reference"],
                import_source=ImportSource.MANUAL,
            )
            session.add(tx)
            session.commit()

            print(f"Scenario {i}: {scenario_data['scenario']}")
            print(f"   Transaction: {tx.description}")
            print(f"   Reference: {tx.reference or 'None'}")

            # Test each matcher
            exact_match = exact_matcher.match(tx, payment)
            fuzzy_match = fuzzy_matcher.match(tx, payment)
            iban_match = iban_matcher.match(tx, payment)

            print("   Results:")
            print(f"      ExactAmountMatcher:  {exact_match.confidence:.1%}")
            print(f"      FuzzyDescriptionMatcher:  {fuzzy_match.confidence:.1%}")
            print(f"      IBANMatcher:   {iban_match.confidence:.1%}")

            # Show best match
            best = max([exact_match, fuzzy_match, iban_match], key=lambda m: m.confidence)
            if best.confidence > 0.5:
                print(
                    f"   ✅ Best: {best.match_type.value} " f"(confidence: {best.confidence:.1%})"
                )
            print()

    finally:
        session.close()


async def example_4_manual_reconciliation():
    """Example 4: Manual reconciliation with review queue.

    Demonstrates:
    - Getting transactions that need manual review
    - Manual reconciliation workflow
    - Unmatching and re-matching
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Manual Reconciliation Workflow")
    print("=" * 80 + "\n")

    init_db()
    session = SessionManager.get_session()

    try:
        # Setup
        account = BankAccount(name="Business Account", iban="IT456")
        session.add(account)
        session.commit()

        tx_repo = BankTransactionRepository(session)
        payment_repo = PaymentRepository(session)

        # Create sample transaction
        tx = BankTransaction(
            account=account,
            date=date(2024, 10, 20),
            amount=Decimal("850.00"),
            description="Generic payment received",
            import_source=ImportSource.CSV,
        )
        session.add(tx)

        payment = Pagamento(
            numero_fattura="MAN-001",
            data_emissione=date(2024, 10, 10),
            data_scadenza=date(2024, 11, 10),
            importo_totale=Decimal("850.00"),
            importo_da_pagare=Decimal("850.00"),
            importo_pagato=Decimal("0.00"),
            cliente_id=1,
        )
        session.add(payment)
        session.commit()

        print(f"📝 Transaction: €{tx.amount} - {tx.description}")
        print(f"📄 Payment: Invoice {payment.numero_fattura} - €{payment.importo_totale}")

        # Manual reconciliation
        print("\n🔍 Step 1: Manual reconciliation...")

        matching_service = MatchingService(tx_repo=tx_repo, payment_repo=payment_repo, matchers=[])

        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo, payment_repo=payment_repo, matching_service=matching_service
        )

        reconciled = await reconciliation_service.reconcile(
            transaction_id=tx.id,
            payment_id=payment.id,
            match_type=MatchType.MANUAL,
            confidence=1.0,
        )

        session.refresh(payment)

        print("✅ Transaction matched!")
        print(f"   Status: {reconciled.status.value}")
        print(f"   Match type: {reconciled.match_type.value}")
        print(f"   Payment total paid: €{payment.importo_pagato}")

        # Unmatch (rollback)
        print("\n↩️  Step 2: Unmatching transaction...")

        reset_tx = await reconciliation_service.reset_transaction(tx.id)
        session.refresh(payment)

        print("✅ Transaction unmatched!")
        print(f"   Status: {reset_tx.status.value}")
        print(f"   Payment total paid: €{payment.importo_pagato}")

        # Re-match
        print("\n🔄 Step 3: Re-matching with updated confidence...")

        rematched = await reconciliation_service.reconcile(
            transaction_id=tx.id,
            payment_id=payment.id,
            match_type=MatchType.EXACT,
            confidence=0.95,
        )

        print("✅ Transaction re-matched!")
        print(f"   Match type: {rematched.match_type.value}")
        print(f"   Confidence: {rematched.match_confidence:.1%}")

    finally:
        session.close()


async def example_5_batch_operations():
    """Example 5: Batch operations for high-volume processing.

    Demonstrates:
    - Batch import from multiple files
    - Batch matching and reconciliation
    - Performance metrics
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Batch Operations")
    print("=" * 80 + "\n")

    init_db()
    session = SessionManager.get_session()

    try:
        # Create 2 accounts (simulating multi-account setup)
        accounts = [
            BankAccount(name="Business Account 1", iban="IT111", current_balance=Decimal("5000")),
            BankAccount(name="Business Account 2", iban="IT222", current_balance=Decimal("8000")),
        ]

        for acc in accounts:
            session.add(acc)

        session.commit()

        print(f"🏦 Created {len(accounts)} bank accounts")

        # Simulate batch import (normally from multiple CSV files)
        print("\n📥 Batch importing transactions...")

        total_imported = 0
        start_time = datetime.now()

        for account in accounts:
            # Simulate importing 10 transactions per account
            for i in range(10):
                tx = BankTransaction(
                    account=account,
                    date=date(2024, 10, 1) + timedelta(days=i),
                    amount=Decimal("100.00") * (i + 1),
                    description=f"Transaction {i + 1} for account {account.name}",
                    import_source=ImportSource.CSV,
                )
                session.add(tx)
                total_imported += 1

        session.commit()

        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"✅ Imported {total_imported} transactions")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Throughput: {total_imported / elapsed:.1f} tx/sec")

        # Batch reconciliation
        print("\n🔄 Batch reconciliation...")

        tx_repo = BankTransactionRepository(session)
        payment_repo = PaymentRepository(session)
        matching_service = MatchingService(tx_repo=tx_repo, payment_repo=payment_repo, matchers=[])
        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo, payment_repo=payment_repo, matching_service=matching_service
        )

        for account in accounts:
            result = await reconciliation_service.reconcile_batch(
                account_id=account.id, auto_apply=False  # Just analyze, don't auto-apply
            )

            print(f"\n   Account: {account.name}")
            print(f"      Unmatched: {result.unmatched_count}")
            print(f"      Potential matches: {result.matched_count + result.review_count}")

    finally:
        session.close()


async def example_6_prometheus_metrics():
    """Example 6: Prometheus metrics integration.

    Demonstrates:
    - Starting metrics server
    - Recording custom metrics
    - Monitoring reconciliation performance
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Prometheus Metrics")
    print("=" * 80 + "\n")

    # Start metrics server (disabled by default)
    # Uncomment to enable in production:
    # start_metrics_server(port=8000)

    print("📊 Recording metrics...")

    # Record transaction imports
    record_transaction_import(count=50, source="csv")
    record_transaction_import(count=30, source="ofx")
    print("   ✅ Recorded 50 CSV + 30 OFX imports")

    # Record reconciliation
    record_reconciliation(count=45, match_type="exact", success=True)
    record_reconciliation(count=15, match_type="fuzzy", success=True)
    record_reconciliation(count=5, match_type="manual", success=False)
    print("   ✅ Recorded 60 successful + 5 failed reconciliations")

    # In production, metrics are available at http://localhost:8000/metrics
    print("\n📈 Metrics available at: http://localhost:8000/metrics")
    print("   (Enable with start_metrics_server() in production)")

    # Example metrics output:
    print("\n   Sample metrics:")
    print('   payment_transactions_imported_total{source="csv"} 50')
    print('   payment_transactions_imported_total{source="ofx"} 30')
    print('   payment_reconciliations_total{match_type="exact",status="success"} 45')
    print('   payment_reconciliations_total{match_type="fuzzy",status="success"} 15')


async def example_7_error_handling():
    """Example 7: Error handling and validation.

    Demonstrates:
    - Import validation errors
    - Reconciliation errors (already matched, amount mismatch)
    - Transaction state validation
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Error Handling")
    print("=" * 80 + "\n")

    init_db()
    session = SessionManager.get_session()

    try:
        account = BankAccount(name="Test Account", iban="IT999")
        session.add(account)

        tx = BankTransaction(
            account=account,
            date=date(2024, 10, 25),
            amount=Decimal("500.00"),
            description="Test transaction",
            status=TransactionStatus.MATCHED,  # Already matched
            import_source=ImportSource.MANUAL,
        )
        session.add(tx)

        payment = Pagamento(
            numero_fattura="ERR-001",
            data_emissione=date(2024, 10, 1),
            data_scadenza=date(2024, 10, 31),
            importo_totale=Decimal("100.00"),  # Different amount
            importo_da_pagare=Decimal("100.00"),
            importo_pagato=Decimal("0.00"),
            cliente_id=1,
        )
        session.add(payment)
        session.commit()

        tx_repo = BankTransactionRepository(session)
        payment_repo = PaymentRepository(session)
        matching_service = MatchingService(tx_repo=tx_repo, payment_repo=payment_repo, matchers=[])
        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo, payment_repo=payment_repo, matching_service=matching_service
        )

        # Test 1: Try to reconcile already-matched transaction
        print("Test 1: Reconcile already-matched transaction")
        try:
            await reconciliation_service.reconcile(
                transaction_id=tx.id, payment_id=payment.id, match_type=MatchType.MANUAL
            )
            print("   ❌ Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ Caught expected error: {e}")

        # Test 2: Amount mismatch warning
        print("\nTest 2: Amount mismatch (logs warning)")

        tx2 = BankTransaction(
            account=account,
            date=date(2024, 10, 26),
            amount=Decimal("500.00"),
            description="Large payment",
            status=TransactionStatus.UNMATCHED,
            import_source=ImportSource.MANUAL,
        )
        session.add(tx2)
        session.commit()

        try:
            # This should log a warning but still succeed
            await reconciliation_service.reconcile(
                transaction_id=tx2.id,
                payment_id=payment.id,  # €100 payment vs €500 transaction
                match_type=MatchType.MANUAL,
            )
            print("   ⚠️  Warning logged: Transaction (€500) exceeds payment (€100)")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 3: Transaction not found
        print("\nTest 3: Transaction not found")
        try:
            from uuid import uuid4

            await reconciliation_service.reconcile(
                transaction_id=uuid4(),  # Random UUID
                payment_id=payment.id,
                match_type=MatchType.MANUAL,
            )
            print("   ❌ Should have raised ValueError")
        except ValueError as e:
            print("   ✅ Caught expected error: Transaction ... not found")

        print("\n✅ All error handling tests completed")

    finally:
        session.close()


async def main():
    """Run all examples."""
    print("\n💰 OpenFatture - Payment Tracking Examples")
    print("=" * 80)
    print()
    print("This demo showcases the complete Payment Tracking module:")
    print("  • Bank statement import (CSV/OFX/QIF)")
    print("  • 5 matching strategies (Exact, Fuzzy, IBAN, DateWindow, Composite)")
    print("  • Auto-reconciliation engine")
    print("  • Manual review workflow")
    print("  • Batch operations")
    print("  • Prometheus metrics")
    print("  • Error handling")
    print()
    print("Note: These examples use in-memory test data.")
    print("      For production use, connect to your actual database.")
    print("=" * 80)

    # Run examples
    await example_1_basic_workflow()
    await example_2_csv_import_configurations()
    await example_3_matching_strategies()
    await example_4_manual_reconciliation()
    await example_5_batch_operations()
    await example_6_prometheus_metrics()
    await example_7_error_handling()

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
    print()
    print("📚 Next steps:")
    print("  • Read full documentation: docs/PAYMENT_TRACKING.md")
    print("  • Explore matchers: openfatture/payment/matchers/")
    print("  • Check CLI commands: openfatture payment --help")
    print("  • View metrics: http://localhost:8000/metrics (if enabled)")
    print()


if __name__ == "__main__":
    """
    Run examples with proper error handling.

    Requirements:
        1. Database initialized (openfatture db init)
        2. At least one client in database
        3. Python 3.12+

    Environment variables (optional):
        PROMETHEUS_ENABLED=true  # Enable metrics server
        PROMETHEUS_PORT=8000     # Metrics server port
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        print("\n💡 Troubleshooting:")
        print("  1. Make sure database is initialized: openfatture db init")
        print("  2. Check that at least one client exists in database")
        print("  3. Ensure all dependencies are installed: uv sync --all-extras")
