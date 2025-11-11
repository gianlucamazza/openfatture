"""Performance benchmarks for FuzzyDescriptionMatcher.

This module tests the performance of the fuzzy matcher with realistic workloads.
The implementation uses rapidfuzz (C-optimized) for fast Levenshtein distance calculations.

Performance Targets (realistic for CI runners):
- Latency with 10 payments: <20ms average
- Latency with 100 payments: <200ms P95
- Throughput: >10 transactions/second with 50 payments

Run with:
    pytest tests/payment/matchers/test_fuzzy_matcher_performance.py -v
"""

import time
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from openfatture.payment.matchers.fuzzy import FuzzyDescriptionMatcher

pytestmark = pytest.mark.unit


class TestFuzzyMatcherPerformance:
    """Performance benchmarks for FuzzyDescriptionMatcher."""

    @pytest.fixture
    def create_sample_transactions(self):
        """Factory to create sample transactions for benchmarking."""

        def _create(count: int) -> list[Mock]:
            transactions = []
            base_date = date(2025, 10, 15)

            descriptions = [
                "BONIFICO SEPA DA MARIO ROSSI SRL",
                "PAYMENT FROM ACME CORPORATION",
                "Transfer from Client ABC",
                "Wire transfer MARIO ROSSI",
                "SEPA BONIFICO ACME",
                "Invoice payment ABC Company",
                "Payment received MARIO ROSSI",
                "Bank transfer from ACME",
                "BONIFICO SEPA ABC",
                "Transfer MARIO ROSSI SRL",
            ]

            for i in range(count):
                transaction = Mock()
                transaction.id = f"tx-perf-{i:04d}"
                transaction.amount = Decimal("1000.00") + Decimal(i % 100)
                transaction.description = descriptions[i % len(descriptions)]
                transaction.reference = f"REF-{i:04d}"
                transaction.counterparty = f"Client {i % 5}"
                transaction.date = base_date + timedelta(days=i % 30)
                transaction.memo = None
                transaction.note = None
                transaction.counterparty_iban = None
                transactions.append(transaction)

            return transactions

        return _create

    @pytest.fixture
    def create_sample_payments(self):
        """Factory to create sample payments for benchmarking."""

        def _create(count: int) -> list[Mock]:
            payments = []
            base_date = date(2025, 10, 15)

            # Create mock cliente
            cliente = Mock()
            cliente.id = 1
            cliente.denominazione = "MARIO ROSSI SRL"
            cliente.ragione_sociale = "Mario Rossi Srl"
            cliente.email = "mario.rossi@example.com"
            cliente.pec = None

            for i in range(count):
                payment = Mock()
                payment.id = i + 1
                payment.descrizione = f"Consulting services {i}"
                payment.data_scadenza = base_date + timedelta(days=i % 30)
                payment.importo = Decimal("1000.00") + Decimal(i % 100)
                payment.importo_pagato = Decimal("0.00")
                payment.saldo_residuo = None
                payment.reference = f"INV-{i:04d}"

                # Mock fattura relationship
                fattura = Mock()
                fattura.id = i + 1
                fattura.numero = f"INV-2025-{i:04d}"
                fattura.descrizione = "Professional consulting services"
                fattura.cliente = cliente
                payment.fattura = fattura

                payments.append(payment)

            return payments

        return _create

    def test_latency_10_payments(self, create_sample_transactions, create_sample_payments):
        """Test latency with 10 payments (small workload)."""
        matcher = FuzzyDescriptionMatcher(min_similarity=80.0)

        transactions = create_sample_transactions(10)
        payments = create_sample_payments(10)

        # Benchmark run
        latencies = []
        for trans in transactions:
            start_time = time.perf_counter()
            results = matcher.match(trans, payments)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            latencies.append(elapsed_ms)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print("\n🔹 Latency (10 payments):")
        print(f"   Average: {avg_latency:.2f}ms")
        print(f"   P95: {p95_latency:.2f}ms")
        print(f"   Min: {min(latencies):.2f}ms, Max: {max(latencies):.2f}ms")

        # Target: <20ms average latency (realistic for CI)
        assert avg_latency < 20.0, f"Average latency too high: {avg_latency:.2f}ms (target: <20ms)"

    def test_latency_100_payments(self, create_sample_transactions, create_sample_payments):
        """Test latency with 100 payments (realistic workload)."""
        matcher = FuzzyDescriptionMatcher(min_similarity=80.0)

        transactions = create_sample_transactions(20)
        payments = create_sample_payments(100)

        # Benchmark
        latencies = []
        for trans in transactions:
            start_time = time.perf_counter()
            results = matcher.match(trans, payments)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            latencies.append(elapsed_ms)

        avg_latency = sum(latencies) / len(latencies)
        p50_latency = sorted(latencies)[int(len(latencies) * 0.50)]
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print("\n🔹 Latency (100 payments):")
        print(f"   P50: {p50_latency:.2f}ms")
        print(f"   Average: {avg_latency:.2f}ms")
        print(f"   P95: {p95_latency:.2f}ms")

        # Target: <200ms p95 latency with 100 payments (realistic for CI)
        assert p95_latency < 200.0, f"P95 latency too high: {p95_latency:.2f}ms (target: <200ms)"

    def test_throughput_benchmark(self, create_sample_transactions, create_sample_payments):
        """Test throughput (transactions per second)."""
        matcher = FuzzyDescriptionMatcher(min_similarity=80.0)

        transactions = create_sample_transactions(50)
        payments = create_sample_payments(50)

        # Benchmark throughput
        start_time = time.perf_counter()
        for trans in transactions:
            matcher.match(trans, payments)
        elapsed = time.perf_counter() - start_time

        throughput = len(transactions) / elapsed
        print("\n🔹 Throughput (50 payments):")
        print(f"   {throughput:.0f} transactions/second")
        print(f"   Total time: {elapsed:.2f}s for {len(transactions)} transactions")
        print(f"   Avg latency per match: {(elapsed / len(transactions)) * 1000:.2f}ms")

        # Target: >10 tx/s (realistic for CI runners)
        assert throughput > 10, f"Throughput too low: {throughput:.0f} tx/s (target: >10 tx/s)"


class TestFuzzyMatcherBackwardCompatibility:
    """Ensure matcher API remains stable."""

    def test_results_identical_between_runs(self):
        """Test that matcher produces consistent results."""
        # Create sample data
        transaction = Mock()
        transaction.id = "tx-001"
        transaction.amount = Decimal("1500.00")
        transaction.description = "BONIFICO SEPA DA MARIO ROSSI"
        transaction.reference = "INV-123"
        transaction.counterparty = "MARIO ROSSI"
        transaction.date = date(2025, 10, 15)
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = None

        payment = Mock()
        payment.id = 1
        payment.descrizione = "Consulting services"
        payment.data_scadenza = date(2025, 10, 15)
        payment.importo = Decimal("1500.00")
        payment.importo_pagato = Decimal("0.00")
        payment.reference = "INV-123"

        fattura = Mock()
        fattura.numero = "INV-123"
        fattura.descrizione = "Professional services"
        fattura.cliente = Mock()
        fattura.cliente.denominazione = "MARIO ROSSI"
        payment.fattura = fattura

        # Match twice
        matcher = FuzzyDescriptionMatcher()
        results1 = matcher.match(transaction, [payment])
        results2 = matcher.match(transaction, [payment])

        # Results should be identical
        assert len(results1) == len(results2)

        if results1:
            assert results1[0].confidence == results2[0].confidence
            assert results1[0].match_type == results2[0].match_type
            assert results1[0].match_reason == results2[0].match_reason
