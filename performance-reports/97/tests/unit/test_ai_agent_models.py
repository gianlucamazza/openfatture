"""Tests for AI agent output models."""

import pytest
from pydantic import ValidationError

from openfatture.ai.agents.models import (
    ClientIntelligenceOutput,
    InvoiceAnalysisOutput,
    PaymentInsightOutput,
    PerformanceAnalyticsOutput,
)


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
        # Invalid confidence
        with pytest.raises(ValidationError):
            PaymentInsightOutput(confidence=1.5)

        # Invalid suggested amount
        with pytest.raises(ValidationError):
            PaymentInsightOutput(suggested_allocation_amount=-100.0)


class TestInvoiceAnalysisOutput:
    """Test InvoiceAnalysisOutput model."""

    def test_valid_invoice_analysis_output(self):
        """Test creating a valid InvoiceAnalysisOutput."""
        output = InvoiceAnalysisOutput(
            total_invoices_analyzed=150,
            avg_invoice_value=1250.50,
            revenue_trends={"2025-01": 15000.0, "2025-02": 18500.0},
            top_services=[{"service": "Consulenza web", "count": 45, "revenue": 22500.0}],
            anomalies=[
                {
                    "type": "outlier_amount",
                    "invoice_id": 123,
                    "description": "Importo 10x superiore alla media",
                }
            ],
            pricing_insights=["Aumentare tariffa del 15%"],
            client_concentration_risk=0.65,
            recommendations=["Diversificare clienti", "Esplorare nuovi mercati"],
            confidence=0.88,
        )

        assert output.total_invoices_analyzed == 150
        assert output.avg_invoice_value == 1250.50
        assert output.revenue_trends["2025-01"] == 15000.0
        assert len(output.top_services) == 1
        assert len(output.anomalies) == 1
        assert output.client_concentration_risk == 0.65
        assert len(output.recommendations) == 2
        assert output.confidence == 0.88

    def test_invoice_analysis_output_validation(self):
        """Test InvoiceAnalysisOutput validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            InvoiceAnalysisOutput()

        # Invalid total_invoices_analyzed
        with pytest.raises(ValidationError):
            InvoiceAnalysisOutput(
                total_invoices_analyzed=-1,
                avg_invoice_value=1000.0,
            )

        # Invalid avg_invoice_value
        with pytest.raises(ValidationError):
            InvoiceAnalysisOutput(
                total_invoices_analyzed=100,
                avg_invoice_value=-500.0,
            )

        # Invalid client_concentration_risk
        with pytest.raises(ValidationError):
            InvoiceAnalysisOutput(
                total_invoices_analyzed=100,
                avg_invoice_value=1000.0,
                client_concentration_risk=1.5,
            )


class TestClientIntelligenceOutput:
    """Test ClientIntelligenceOutput model."""

    def test_valid_client_intelligence_output(self):
        """Test creating a valid ClientIntelligenceOutput."""
        output = ClientIntelligenceOutput(
            client_id=42,
            client_name="Acme Corp S.r.l.",
            relationship_score=7.5,
            total_revenue=45000.0,
            invoice_count=15,
            avg_payment_days=35.2,
            payment_behavior="good",
            late_payments_count=2,
            predicted_next_payment_days=30,
            churn_risk=0.15,
            growth_potential="high",
            recommendations=["Proporre piano annuale", "Organizzare meeting trimestrale"],
            warnings=["Ritardo medio in aumento"],
            confidence=0.85,
        )

        assert output.client_id == 42
        assert output.client_name == "Acme Corp S.r.l."
        assert output.relationship_score == 7.5
        assert output.total_revenue == 45000.0
        assert output.invoice_count == 15
        assert output.avg_payment_days == 35.2
        assert output.payment_behavior == "good"
        assert output.late_payments_count == 2
        assert output.predicted_next_payment_days == 30
        assert output.churn_risk == 0.15
        assert output.growth_potential == "high"
        assert len(output.recommendations) == 2
        assert len(output.warnings) == 1
        assert output.confidence == 0.85

    def test_client_intelligence_output_validation(self):
        """Test ClientIntelligenceOutput validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            ClientIntelligenceOutput()

        # Invalid client_id
        with pytest.raises(ValidationError):
            ClientIntelligenceOutput(
                client_id=0,
                client_name="Test",
                relationship_score=5.0,
                total_revenue=1000.0,
                invoice_count=1,
                avg_payment_days=30.0,
                payment_behavior="good",
            )

        # Invalid relationship_score
        with pytest.raises(ValidationError):
            ClientIntelligenceOutput(
                client_id=1,
                client_name="Test",
                relationship_score=15.0,  # > 10.0
                total_revenue=1000.0,
                invoice_count=1,
                avg_payment_days=30.0,
                payment_behavior="good",
            )

        # Invalid payment_behavior
        with pytest.raises(ValidationError):
            ClientIntelligenceOutput(
                client_id=1,
                client_name="Test",
                relationship_score=5.0,
                total_revenue=1000.0,
                invoice_count=1,
                avg_payment_days=30.0,
                payment_behavior="invalid",  # not in allowed values
            )

        # Invalid growth_potential
        with pytest.raises(ValidationError):
            ClientIntelligenceOutput(
                client_id=1,
                client_name="Test",
                relationship_score=5.0,
                total_revenue=1000.0,
                invoice_count=1,
                avg_payment_days=30.0,
                payment_behavior="good",
                growth_potential="invalid",  # not in allowed values
            )


class TestPerformanceAnalyticsOutput:
    """Test PerformanceAnalyticsOutput model."""

    def test_valid_performance_analytics_output(self):
        """Test creating a valid PerformanceAnalyticsOutput."""
        output = PerformanceAnalyticsOutput(
            period="Q1 2025",
            total_revenue=65000.0,
            revenue_growth=15.5,
            invoices_count=45,
            avg_invoice_value=1444.44,
            revenue_by_client=[{"client": "Acme Corp", "revenue": 15000.0, "percentage": 23.1}],
            revenue_by_service=[{"service": "Consulenza", "revenue": 40000.0, "percentage": 61.5}],
            cash_collection_rate=0.92,
            avg_collection_days=38.5,
            revenue_forecast_next_period=72000.0,
            forecast_confidence_interval=(65000.0, 79000.0),
            key_insights=["Crescita costante", "Servizi in espansione"],
            performance_trends={"revenue": "improving", "collection_rate": "stable"},
            strategic_recommendations=["Aumentare capacità", "Esplorare nuovi servizi"],
            risk_factors=["Alta concentrazione clienti"],
            confidence=0.82,
        )

        assert output.period == "Q1 2025"
        assert output.total_revenue == 65000.0
        assert output.revenue_growth == 15.5
        assert output.invoices_count == 45
        assert output.avg_invoice_value == 1444.44
        assert len(output.revenue_by_client) == 1
        assert len(output.revenue_by_service) == 1
        assert output.cash_collection_rate == 0.92
        assert output.avg_collection_days == 38.5
        assert output.revenue_forecast_next_period == 72000.0
        assert output.forecast_confidence_interval == (65000.0, 79000.0)
        assert len(output.key_insights) == 2
        assert output.performance_trends["revenue"] == "improving"
        assert len(output.strategic_recommendations) == 2
        assert len(output.risk_factors) == 1
        assert output.confidence == 0.82

    def test_performance_analytics_output_validation(self):
        """Test PerformanceAnalyticsOutput validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            PerformanceAnalyticsOutput()

        # Invalid total_revenue
        with pytest.raises(ValidationError):
            PerformanceAnalyticsOutput(
                period="Q1 2025",
                total_revenue=-1000.0,
                revenue_growth=10.0,
                invoices_count=10,
                avg_invoice_value=100.0,
            )

        # Invalid invoices_count
        with pytest.raises(ValidationError):
            PerformanceAnalyticsOutput(
                period="Q1 2025",
                total_revenue=10000.0,
                revenue_growth=10.0,
                invoices_count=-5,
                avg_invoice_value=100.0,
            )

        # Invalid cash_collection_rate
        with pytest.raises(ValidationError):
            PerformanceAnalyticsOutput(
                period="Q1 2025",
                total_revenue=10000.0,
                revenue_growth=10.0,
                invoices_count=10,
                avg_invoice_value=100.0,
                cash_collection_rate=1.5,  # > 1.0
            )

        # Invalid confidence
        with pytest.raises(ValidationError):
            PerformanceAnalyticsOutput(
                period="Q1 2025",
                total_revenue=10000.0,
                revenue_growth=10.0,
                invoices_count=10,
                avg_invoice_value=100.0,
                confidence=-0.5,  # < 0.0
            )
