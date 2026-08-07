"""Tests for Lightning tax compliance value objects.

Tests cover:
- Unit tests for TaxableAmount, CapitalGain, QuadroRWData
- Validation constraints
- Property-based tests (Hypothesis)
- Edge cases and boundary conditions
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from openfatture.lightning.domain.value_objects import (
    CapitalGain,
    QuadroRWData,
    TaxableAmount,
)

# ============================================================================
# TAXABLE AMOUNT TESTS
# ============================================================================


class TestTaxableAmount:
    """Test suite for TaxableAmount value object."""

    def test_create_valid_taxable_amount(self) -> None:
        """Test creating a valid taxable amount."""
        amount = TaxableAmount(
            amount_eur=Decimal("1000.00"),
            btc_eur_rate=Decimal("45000.00"),
            timestamp=datetime.now(UTC),
        )

        assert amount.amount_eur == Decimal("1000.00")
        assert amount.btc_eur_rate == Decimal("45000.00")
        assert amount.timestamp is not None

    def test_amount_btc_calculation(self) -> None:
        """Test BTC amount calculation from EUR and rate."""
        amount = TaxableAmount(
            amount_eur=Decimal("45000.00"),
            btc_eur_rate=Decimal("45000.00"),
            timestamp=datetime.now(UTC),
        )

        assert amount.amount_btc == Decimal("1.0")

    def test_amount_sat_calculation(self) -> None:
        """Test satoshi amount calculation."""
        amount = TaxableAmount(
            amount_eur=Decimal("4500.00"),  # 0.1 BTC at 45k EUR/BTC
            btc_eur_rate=Decimal("45000.00"),
            timestamp=datetime.now(UTC),
        )

        assert amount.amount_sat == 10_000_000  # 0.1 BTC = 10M sats

    def test_negative_amount_rejected(self) -> None:
        """Test that negative amounts are rejected."""
        with pytest.raises(ValueError, match="Amount must be non-negative"):
            TaxableAmount(
                amount_eur=Decimal("-100.00"),
                btc_eur_rate=Decimal("45000.00"),
                timestamp=datetime.now(UTC),
            )

    def test_zero_or_negative_rate_rejected(self) -> None:
        """Test that zero or negative rates are rejected."""
        with pytest.raises(ValueError, match="BTC/EUR rate must be positive"):
            TaxableAmount(
                amount_eur=Decimal("1000.00"),
                btc_eur_rate=Decimal("0"),
                timestamp=datetime.now(UTC),
            )

        with pytest.raises(ValueError, match="BTC/EUR rate must be positive"):
            TaxableAmount(
                amount_eur=Decimal("1000.00"),
                btc_eur_rate=Decimal("-1000.00"),
                timestamp=datetime.now(UTC),
            )

    def test_future_timestamp_rejected(self) -> None:
        """Test that future timestamps are rejected."""
        future = datetime.now(UTC) + timedelta(days=1)

        with pytest.raises(ValueError, match="Timestamp cannot be in future"):
            TaxableAmount(
                amount_eur=Decimal("1000.00"), btc_eur_rate=Decimal("45000.00"), timestamp=future
            )

    def test_to_dict_serialization(self) -> None:
        """Test dictionary serialization."""
        timestamp = datetime.now(UTC)
        amount = TaxableAmount(
            amount_eur=Decimal("1000.00"), btc_eur_rate=Decimal("45000.00"), timestamp=timestamp
        )

        data = amount.to_dict()

        assert data["amount_eur"] == "1000.00"
        assert data["btc_eur_rate"] == "45000.00"
        assert data["timestamp"] == timestamp.isoformat()
        assert "amount_btc" in data
        assert "amount_sat" in data


# ============================================================================
# CAPITAL GAIN TESTS
# ============================================================================


class TestCapitalGain:
    """Test suite for CapitalGain value object."""

    def test_create_capital_gain_with_profit(self) -> None:
        """Test creating a capital gain with profit."""
        gain = CapitalGain(
            payment_hash="a" * 64,  # Valid 64-char hex
            acquisition_cost_eur=Decimal("40000.00"),
            sale_price_eur=Decimal("45000.00"),
            gain_loss_eur=Decimal("5000.00"),
            tax_year=2025,
        )

        assert gain.gain_loss_eur == Decimal("5000.00")
        assert gain.is_taxable is True

    def test_create_capital_gain_with_loss(self) -> None:
        """Test creating a capital gain with loss (minusvalenza)."""
        gain = CapitalGain(
            payment_hash="b" * 64,
            acquisition_cost_eur=Decimal("45000.00"),
            sale_price_eur=Decimal("40000.00"),
            gain_loss_eur=Decimal("-5000.00"),
            tax_year=2025,
        )

        assert gain.gain_loss_eur == Decimal("-5000.00")
        assert gain.is_taxable is False  # Losses are not taxable

    def test_capital_gain_without_acquisition_cost(self) -> None:
        """Test capital gain when acquisition cost is unknown."""
        gain = CapitalGain(
            payment_hash="c" * 64,
            acquisition_cost_eur=None,  # Unknown cost
            sale_price_eur=Decimal("45000.00"),
            gain_loss_eur=Decimal("0"),  # Conservative estimate
            tax_year=2025,
        )

        assert gain.acquisition_cost_eur is None
        assert gain.is_taxable is False

    def test_tax_rates_2025_vs_2026(self) -> None:
        """Test different tax rates for 2025 (26%) and 2026+ (33%)."""
        gain_2025 = CapitalGain(
            payment_hash="d" * 64,
            acquisition_cost_eur=Decimal("40000.00"),
            sale_price_eur=Decimal("50000.00"),
            gain_loss_eur=Decimal("10000.00"),
            tax_year=2025,
        )

        gain_2026 = CapitalGain(
            payment_hash="e" * 64,
            acquisition_cost_eur=Decimal("40000.00"),
            sale_price_eur=Decimal("50000.00"),
            gain_loss_eur=Decimal("10000.00"),
            tax_year=2026,
        )

        # 2025: 10,000 * 0.26 = 2,600
        assert gain_2025.tax_owed_eur == Decimal("2600.00")

        # 2026: 10,000 * 0.33 = 3,300
        assert gain_2026.tax_owed_eur == Decimal("3300.00")

    def test_invalid_payment_hash_rejected(self) -> None:
        """Test that invalid payment hashes are rejected."""
        with pytest.raises(ValueError, match="Invalid payment_hash format"):
            CapitalGain(
                payment_hash="invalid",
                acquisition_cost_eur=Decimal("40000.00"),
                sale_price_eur=Decimal("45000.00"),
                gain_loss_eur=Decimal("5000.00"),
                tax_year=2025,
            )

    def test_negative_acquisition_cost_rejected(self) -> None:
        """Test that negative acquisition costs are rejected."""
        with pytest.raises(ValueError, match="Acquisition cost cannot be negative"):
            CapitalGain(
                payment_hash="f" * 64,
                acquisition_cost_eur=Decimal("-1000.00"),
                sale_price_eur=Decimal("45000.00"),
                gain_loss_eur=Decimal("46000.00"),
                tax_year=2025,
            )

    def test_gain_loss_calculation_validated(self) -> None:
        """Test that gain/loss calculation is validated."""
        # Correct calculation should work
        CapitalGain(
            payment_hash="1" * 64,  # Valid hex
            acquisition_cost_eur=Decimal("40000.00"),
            sale_price_eur=Decimal("45000.00"),
            gain_loss_eur=Decimal("5000.00"),  # Correct: 45k - 40k
            tax_year=2025,
        )

        # Incorrect calculation should fail
        with pytest.raises(ValueError, match="Gain/loss mismatch"):
            CapitalGain(
                payment_hash="2" * 64,  # Valid hex
                acquisition_cost_eur=Decimal("40000.00"),
                sale_price_eur=Decimal("45000.00"),
                gain_loss_eur=Decimal("1000.00"),  # Wrong: should be 5k
                tax_year=2025,
            )

    def test_invalid_tax_year_rejected(self) -> None:
        """Test that invalid tax years are rejected."""
        with pytest.raises(ValueError, match="Invalid tax year"):
            CapitalGain(
                payment_hash="3" * 64,  # Valid hex
                acquisition_cost_eur=Decimal("40000.00"),
                sale_price_eur=Decimal("45000.00"),
                gain_loss_eur=Decimal("5000.00"),
                tax_year=1999,  # Too old
            )

    def test_to_dict_serialization(self) -> None:
        """Test dictionary serialization."""
        gain = CapitalGain(
            payment_hash="4" * 64,  # Valid hex
            acquisition_cost_eur=Decimal("40000.00"),
            sale_price_eur=Decimal("45000.00"),
            gain_loss_eur=Decimal("5000.00"),
            tax_year=2025,
        )

        data = gain.to_dict()

        assert data["payment_hash"] == "4" * 64  # Match the hash used above
        assert data["acquisition_cost_eur"] == "40000.00"
        assert data["sale_price_eur"] == "45000.00"
        assert data["gain_loss_eur"] == "5000.00"
        assert data["tax_year"] == 2025
        assert data["is_taxable"] is True
        assert data["tax_owed_eur"] == "1300.00"  # 5000 * 0.26 = 1300


# ============================================================================
# QUADRO RW DATA TESTS
# ============================================================================


class TestQuadroRWData:
    """Test suite for QuadroRWData value object."""

    def test_create_valid_quadro_rw_data(self) -> None:
        """Test creating valid Quadro RW data."""
        data = QuadroRWData(
            tax_year=2025,
            total_holdings_eur=Decimal("10000.00"),
            average_holdings_eur=Decimal("8000.00"),
            num_transactions=15,
            total_inflows_eur=Decimal("5000.00"),
            total_outflows_eur=Decimal("3000.00"),
        )

        assert data.tax_year == 2025
        assert data.total_holdings_eur == Decimal("10000.00")
        assert data.num_transactions == 15

    def test_declaration_always_required_from_2025(self) -> None:
        """Test that Quadro RW declaration is always required from 2025."""
        data = QuadroRWData(
            tax_year=2025,
            total_holdings_eur=Decimal("1.00"),  # Even small amounts
            average_holdings_eur=Decimal("0.50"),
            num_transactions=1,
        )

        assert data.requires_declaration is True

    def test_ivafe_tax_currently_zero(self) -> None:
        """Test that IVAFE tax is currently 0 (pending advisor confirmation)."""
        data = QuadroRWData(
            tax_year=2025,
            total_holdings_eur=Decimal("100000.00"),
            average_holdings_eur=Decimal("80000.00"),
            num_transactions=50,
        )

        # IVAFE not applied pending tax advisor confirmation
        assert data.ivafe_tax_owed_eur == Decimal("0")

    def test_negative_holdings_rejected(self) -> None:
        """Test that negative holdings are rejected."""
        with pytest.raises(ValueError, match="Total holdings cannot be negative"):
            QuadroRWData(
                tax_year=2025,
                total_holdings_eur=Decimal("-1000.00"),
                average_holdings_eur=Decimal("500.00"),
                num_transactions=5,
            )

    def test_negative_transactions_rejected(self) -> None:
        """Test that negative transaction counts are rejected."""
        with pytest.raises(ValueError, match="Number of transactions cannot be negative"):
            QuadroRWData(
                tax_year=2025,
                total_holdings_eur=Decimal("1000.00"),
                average_holdings_eur=Decimal("500.00"),
                num_transactions=-5,
            )

    def test_invalid_tax_year_rejected(self) -> None:
        """Test that invalid tax years are rejected."""
        current_year = datetime.now(UTC).year

        with pytest.raises(ValueError, match="Invalid tax year"):
            QuadroRWData(
                tax_year=current_year + 2,  # Future year
                total_holdings_eur=Decimal("1000.00"),
                average_holdings_eur=Decimal("500.00"),
                num_transactions=5,
            )

    def test_to_dict_serialization(self) -> None:
        """Test dictionary serialization."""
        data = QuadroRWData(
            tax_year=2025,
            total_holdings_eur=Decimal("10000.00"),
            average_holdings_eur=Decimal("8000.00"),
            num_transactions=15,
            total_inflows_eur=Decimal("5000.00"),
            total_outflows_eur=Decimal("3000.00"),
        )

        dict_data = data.to_dict()

        assert dict_data["tax_year"] == 2025
        assert dict_data["total_holdings_eur"] == "10000.00"
        assert dict_data["num_transactions"] == 15
        assert dict_data["requires_declaration"] is True


# ============================================================================
# PROPERTY-BASED TESTS (Hypothesis)
# ============================================================================


class TestTaxValueObjectsProperties:
    """Property-based tests for tax value objects using Hypothesis."""

    @given(
        amount_eur=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1000000"), places=2),
        btc_eur_rate=st.decimals(min_value=Decimal("1000"), max_value=Decimal("100000"), places=2),
    )
    def test_taxable_amount_btc_eur_conversion_invertible(
        self, amount_eur: Decimal, btc_eur_rate: Decimal
    ) -> None:
        """Test that EUR -> BTC -> EUR conversion is approximately invertible."""
        amount = TaxableAmount(
            amount_eur=amount_eur, btc_eur_rate=btc_eur_rate, timestamp=datetime.now(UTC)
        )

        # Convert EUR -> BTC -> EUR
        recovered_eur = amount.amount_btc * btc_eur_rate

        # Should be approximately equal (within 0.01 EUR due to rounding)
        assert abs(recovered_eur - amount_eur) < Decimal("0.01")

    @given(
        acquisition_cost=st.decimals(
            min_value=Decimal("1000"), max_value=Decimal("100000"), places=2
        ),
        sale_price=st.decimals(min_value=Decimal("1000"), max_value=Decimal("100000"), places=2),
    )
    def test_capital_gain_calculation_consistent(
        self, acquisition_cost: Decimal, sale_price: Decimal
    ) -> None:
        """Test that capital gain calculation is mathematically consistent."""
        gain_loss = sale_price - acquisition_cost

        gain = CapitalGain(
            payment_hash="a" * 64,
            acquisition_cost_eur=acquisition_cost,
            sale_price_eur=sale_price,
            gain_loss_eur=gain_loss,
            tax_year=2025,
        )

        # Tax owed should always be non-negative
        assert gain.tax_owed_eur >= 0

        # Tax owed should be zero for losses
        if gain_loss <= 0:
            assert gain.tax_owed_eur == 0

        # Tax owed should be <= gain for profits
        if gain_loss > 0:
            assert gain.tax_owed_eur <= gain_loss
            # Tax rate should be reasonable (0-50%)
            tax_rate = gain.tax_owed_eur / gain_loss
            assert Decimal("0") <= tax_rate <= Decimal("0.5")

    @given(
        total_holdings=st.decimals(min_value=Decimal("0"), max_value=Decimal("1000000"), places=2),
        num_transactions=st.integers(min_value=0, max_value=10000),
    )
    def test_quadro_rw_data_bounds(self, total_holdings: Decimal, num_transactions: int) -> None:
        """Test that Quadro RW data respects mathematical bounds."""
        # Average holdings should be <= total holdings
        average_holdings = total_holdings * Decimal("0.5")  # Conservative estimate

        data = QuadroRWData(
            tax_year=2025,
            total_holdings_eur=total_holdings,
            average_holdings_eur=average_holdings,
            num_transactions=num_transactions,
        )

        # Average should be <= total
        assert data.average_holdings_eur <= data.total_holdings_eur

        # Tax rates should be reasonable
        assert data.ivafe_tax_rate == Decimal("0.002")  # 0.2%
