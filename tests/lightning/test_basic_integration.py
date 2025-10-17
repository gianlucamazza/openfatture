"""Basic integration tests for Lightning Network functionality."""

from decimal import Decimal

import pytest

from openfatture.lightning.application.services.invoice_service import LightningInvoiceService
from openfatture.lightning.application.services.payment_service import LightningPaymentService
from openfatture.lightning.infrastructure.repository import LightningInvoiceRepository


class TestLightningBasicIntegration:
    """Test basic Lightning integration functionality."""

    @pytest.fixture
    def invoice_service(self, mock_lnd_client, mock_btc_converter):
        """Lightning invoice service for testing."""
        return LightningInvoiceService(mock_lnd_client, mock_btc_converter)

    @pytest.fixture
    def payment_service(self, mock_lnd_client):
        """Lightning payment service for testing."""
        repo = LightningInvoiceRepository()
        return LightningPaymentService(mock_lnd_client, repo)

    @pytest.mark.asyncio
    async def test_create_invoice_from_fattura(self, invoice_service):
        """Test creating Lightning invoice from fattura data."""
        fattura_id = 123
        totale_eur = Decimal("100.00")
        descrizione = "Consulenza IT"
        cliente_nome = "Mario Rossi SRL"

        invoice = await invoice_service.create_invoice_from_fattura(
            fattura_id=fattura_id,
            totale_eur=totale_eur,
            descrizione=descrizione,
            cliente_nome=cliente_nome,
        )

        assert invoice.payment_hash
        assert invoice.payment_request.startswith("lnbc")
        assert invoice.amount_msat > 0
        assert str(fattura_id) in invoice.description
        assert cliente_nome in invoice.description

    @pytest.mark.asyncio
    async def test_create_zero_amount_invoice(self, invoice_service):
        """Test creating zero-amount Lightning invoice."""
        descrizione = "Donazione libera"
        expiry_hours = 48

        invoice = await invoice_service.create_zero_amount_invoice(
            descrizione=descrizione, expiry_hours=expiry_hours
        )

        assert invoice.payment_hash
        assert invoice.payment_request.startswith("lnbc")
        assert invoice.amount_msat is None  # Zero-amount
        assert invoice.description == descrizione

    @pytest.mark.asyncio
    async def test_simulate_payment_settlement(self, invoice_service, payment_service):
        """Test simulating payment settlement."""
        # Create an invoice
        invoice = await invoice_service.create_zero_amount_invoice("Test payment")

        # Simulate payment
        success = await payment_service.simulate_payment(invoice.payment_hash)

        assert success

        # Check that invoice status was updated
        status = await payment_service.lnd_client.lookup_invoice(invoice.payment_hash)
        assert status["settled"] is True

    @pytest.mark.asyncio
    async def test_calculate_fees_estimate(self, invoice_service):
        """Test fee estimation for Lightning payments."""
        amount_msat = 100_000_000  # 100k msat = 1000 sat
        description = "Test payment"

        fees = await invoice_service.calculate_fees_estimate(amount_msat, description)

        assert "estimated_min_fee_sat" in fees
        assert "estimated_max_fee_sat" in fees
        assert "estimated_min_fee_eur" in fees
        assert "estimated_max_fee_eur" in fees
        assert fees["estimated_min_fee_sat"] > 0
        assert fees["estimated_max_fee_sat"] > fees["estimated_min_fee_sat"]

    @pytest.mark.asyncio
    async def test_bolt11_validation(self, invoice_service):
        """Test BOLT-11 invoice validation."""
        # Valid invoice (mock format)
        valid_invoice = "lnbc100n1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqhp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqsfpp3qjmp7lwpagxun9pygexvgpjdc4jdj85fr9yq20q82gphp2nflc7jtzrcazrra7wwgzxqc8u7754cdlpfrmccae92qgzqvzq2ps8pqqqqqqpqqqqq9qqqvpeuqafqxu92d8lr6fvg0r5gv0heeeqgcrqlnm6jhphu9y00rrhy4grqszsvpcgpy9qqqqqqgqqqqq7qqzqj9n4evl6mr5aj9f58zp6fyjzup6ywn3x6sk8akg5v4tgn2q8g4fhx05wf6juaxu9760yp46454gpg5mtzgerlzezqcqvjnhjh8z3g2qqdhhwkj"

        assert invoice_service.validate_bolt11_invoice(valid_invoice)

        # Invalid invoice
        invalid_invoice = "not_a_lightning_invoice"
        assert not invoice_service.validate_bolt11_invoice(invalid_invoice)

    @pytest.mark.asyncio
    async def test_payment_stats(self, payment_service):
        """Test payment statistics calculation."""
        stats = await payment_service.get_payment_stats()

        # Should have basic structure even with no payments
        assert "total_payments_30d" in stats
        assert "total_amount_msat_30d" in stats
        assert "success_rate" in stats
        assert isinstance(stats["success_rate"], float)
        assert 0.0 <= stats["success_rate"] <= 1.0

    @pytest.mark.asyncio
    async def test_lnd_client_operations(self, mock_lnd_client):
        """Test basic LND client operations."""
        # Get node info
        node_info = await mock_lnd_client.get_node_info()
        assert node_info.pubkey
        assert node_info.alias
        assert isinstance(node_info.num_peers, int)

        # List channels
        channels = await mock_lnd_client.list_channels()
        assert isinstance(channels, list)

        # Create invoice
        invoice = await mock_lnd_client.create_invoice(
            amount_msat=100000, description="Test invoice"
        )
        assert invoice.payment_hash
        assert invoice.payment_request

        # Lookup invoice
        status = await mock_lnd_client.lookup_invoice(invoice.payment_hash)
        assert "payment_hash" in status
        assert status["payment_hash"] == invoice.payment_hash
