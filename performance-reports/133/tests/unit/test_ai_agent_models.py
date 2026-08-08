"""Tests for AI agent output models."""

import pytest
from pydantic import ValidationError

from openfatture.ai.agents.models import PaymentInsightOutput


class TestPaymentInsightOutput:
    """Test PaymentInsightOutput model."""

    def test_valid_payment_insight_output(self):
        """Test creating a valid PaymentInsightOutput."""
        output = PaymentInsightOutput(
            probable_invoice_numbers=["INV-2024-001", "INV-2024-002"],
            is_partial_payment=True,
            suggested_allocation_amount=500.0,
            keywords=["acconto", "parziale"],
            confidence=0.85,
            summary="Pagamento parziale per progetto web",
        )

        assert output.probable_invoice_numbers == ["INV-2024-001", "INV-2024-002"]
        assert output.is_partial_payment is True
        assert output.suggested_allocation_amount == 500.0
        assert output.keywords == ["acconto", "parziale"]
        assert output.confidence == 0.85
        assert output.summary == "Pagamento parziale per progetto web"

    def test_payment_insight_output_defaults(self):
        """Test PaymentInsightOutput with default values."""
        output = PaymentInsightOutput()

        assert output.probable_invoice_numbers == []
        assert output.is_partial_payment is False
        assert output.suggested_allocation_amount is None
        assert output.keywords == []
        assert output.confidence == 1.0
        assert output.summary is None

    def test_payment_insight_output_validation(self):
        """Test PaymentInsightOutput validation."""
        with pytest.raises(ValidationError):
            PaymentInsightOutput(confidence=1.5)

        with pytest.raises(ValidationError):
            PaymentInsightOutput(suggested_allocation_amount=-100.0)
