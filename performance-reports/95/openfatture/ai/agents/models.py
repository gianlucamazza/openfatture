"""Structured output models for AI agents."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvoiceDescriptionOutput(BaseModel):
    """
    Structured output for invoice description generation.

    Used by Invoice Assistant agent to provide structured,
    professional invoice descriptions.
    """

    descrizione_completa: str = Field(
        ...,
        description="Descrizione dettagliata della prestazione professionale",
        max_length=1000,  # FatturaPA limit
    )

    deliverables: list[str] = Field(
        default_factory=list,
        description="Lista dei deliverables forniti",
    )

    competenze: list[str] = Field(
        default_factory=list,
        description="Competenze tecniche utilizzate",
    )

    durata_ore: float | None = Field(
        default=None,
        description="Durata in ore della prestazione",
    )

    note: str | None = Field(
        default=None,
        description="Note aggiuntive o contesto",
        max_length=500,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "descrizione_completa": "Consulenza professionale per sviluppo web...",
                "deliverables": ["Codice sorgente", "Documentazione tecnica"],
                "competenze": ["Python", "FastAPI", "PostgreSQL"],
                "durata_ore": 5.0,
                "note": "Progetto completato con successo",
            }
        }
    )


class TaxSuggestionOutput(BaseModel):
    """
    Structured output for tax advisor agent.

    Provides detailed VAT treatment suggestions for Italian invoices
    following FatturaPA regulations.
    """

    aliquota_iva: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Aliquota IVA suggerita (22, 10, 5, 4, 0)",
    )

    codice_natura: str | None = Field(
        None,
        description="Codice natura IVA (N1-N7) per operazioni non imponibili/esenti",
        pattern="^N[1-7](\\.\\d+)?$",
    )

    reverse_charge: bool = Field(
        False,
        description="True se applicabile reverse charge (inversione contabile)",
    )

    split_payment: bool = Field(
        False,
        description="True se applicabile split payment (PA)",
    )

    regime_speciale: str | None = Field(
        None,
        description="Eventuale regime speciale applicabile",
    )

    spiegazione: str = Field(
        ...,
        description="Spiegazione dettagliata del trattamento fiscale",
        max_length=1000,
    )

    riferimento_normativo: str = Field(
        ...,
        description="Riferimento alla normativa di legge applicabile",
        max_length=500,
    )

    note_fattura: str | None = Field(
        None,
        description="Nota da inserire in fattura (es. per reverse charge)",
        max_length=200,
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Livello di confidenza del suggerimento (0.0-1.0)",
    )

    raccomandazioni: list[str] = Field(
        default_factory=list,
        description="Raccomandazioni aggiuntive per il professionista",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "aliquota_iva": 22.0,
                "codice_natura": "N6.2",
                "reverse_charge": True,
                "split_payment": False,
                "regime_speciale": "REVERSE_CHARGE_EDILIZIA",
                "spiegazione": "Per servizi resi al settore edile si applica il reverse charge",
                "riferimento_normativo": "Art. 17, c. 6, lett. a-ter, DPR 633/72",
                "note_fattura": "Inversione contabile - art. 17 c. 6 lett. a-ter DPR 633/72",
                "confidence": 0.95,
                "raccomandazioni": [
                    "Verificare che il cliente operi nel settore edile",
                    "Non addebitare IVA in fattura",
                ],
            }
        }
    )


class PaymentInsightOutput(BaseModel):
    """
    Structured output for the payment insight agent.

    Encodes AI analysis of a bank transaction to support reconciliation.
    """

    probable_invoice_numbers: list[str] = Field(
        default_factory=list,
        description="Lista delle fatture probabilmente collegate al movimento",
    )

    is_partial_payment: bool = Field(
        default=False,
        description="True se la causale suggerisce un pagamento parziale/acconto",
    )

    suggested_allocation_amount: float | None = Field(
        default=None,
        ge=0.0,
        description="Importo suggerito da allocare alla fattura se diverso dall'intero movimento",
    )

    keywords: list[str] = Field(
        default_factory=list,
        description="Parole chiave estratte dalla causale utili alla riconciliazione",
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Livello di confidenza dell'analisi (0.0-1.0)",
    )

    summary: str | None = Field(
        default=None,
        description="Sintesi testuale dell'analisi",
        max_length=500,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "probable_invoice_numbers": ["INV-2024-001"],
                "is_partial_payment": True,
                "suggested_allocation_amount": 400.0,
                "keywords": ["acconto", "INV-2024-001"],
                "confidence": 0.82,
                "summary": "Pagamento parziale del 40% riferito alla fattura INV-2024-001",
            }
        }
    )


class InvoiceAnalysisOutput(BaseModel):
    """
    Structured output for invoice analysis agent.

    Provides insights on invoice patterns, anomalies, and pricing optimization.
    """

    total_invoices_analyzed: int = Field(
        ...,
        ge=0,
        description="Numero totale di fatture analizzate",
    )

    avg_invoice_value: float = Field(
        ...,
        ge=0.0,
        description="Valore medio delle fatture",
    )

    revenue_trends: dict[str, float] = Field(
        default_factory=dict,
        description="Trend del fatturato per periodo (es. mensile)",
    )

    top_services: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Servizi più fatturati con volumi e valori",
    )

    anomalies: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Anomalie rilevate (outliers, pattern strani)",
    )

    pricing_insights: list[str] = Field(
        default_factory=list,
        description="Suggerimenti per ottimizzazione prezzi",
    )

    client_concentration_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Rischio concentrazione (% fatturato top 3 clienti)",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Raccomandazioni strategiche basate sull'analisi",
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Livello di confidenza dell'analisi (0.0-1.0)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_invoices_analyzed": 120,
                "avg_invoice_value": 1250.50,
                "revenue_trends": {"2025-01": 15000.0, "2025-02": 18500.0},
                "top_services": [{"service": "Consulenza web", "count": 45, "revenue": 22500.0}],
                "anomalies": [
                    {
                        "type": "outlier_amount",
                        "invoice_id": 123,
                        "description": "Fattura con importo 10x superiore alla media",
                    }
                ],
                "pricing_insights": ["Considera aumentare tariffa per consulenza web (+15%)"],
                "client_concentration_risk": 0.65,
                "recommendations": [
                    "Diversificare il portafoglio clienti",
                    "Esplorare nuovi mercati",
                ],
                "confidence": 0.88,
            }
        }
    )


class ClientIntelligenceOutput(BaseModel):
    """
    Structured output for client intelligence agent.

    Provides insights on client behavior, payment patterns, and relationship health.
    """

    client_id: int = Field(
        ...,
        ge=1,
        description="ID del cliente analizzato",
    )

    client_name: str = Field(
        ...,
        description="Nome/denominazione del cliente",
    )

    relationship_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Punteggio salute relazione (0-10)",
    )

    total_revenue: float = Field(
        ...,
        ge=0.0,
        description="Fatturato totale generato dal cliente",
    )

    invoice_count: int = Field(
        ...,
        ge=0,
        description="Numero totale di fatture emesse",
    )

    avg_payment_days: float = Field(
        ...,
        description="Giorni medi di pagamento",
    )

    payment_behavior: str = Field(
        ...,
        description="Comportamento pagamento (excellent, good, average, poor, critical)",
        pattern="^(excellent|good|average|poor|critical)$",
    )

    late_payments_count: int = Field(
        default=0,
        ge=0,
        description="Numero di pagamenti in ritardo",
    )

    predicted_next_payment_days: int | None = Field(
        default=None,
        description="Previsione giorni per prossimo pagamento",
    )

    churn_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Rischio abbandono/churn (0.0-1.0)",
    )

    growth_potential: str = Field(
        default="medium",
        description="Potenziale di crescita (low, medium, high)",
        pattern="^(low|medium|high)$",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Raccomandazioni per migliorare la relazione",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Alert e warning da considerare",
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Livello di confidenza dell'analisi (0.0-1.0)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": 42,
                "client_name": "Acme Corp S.r.l.",
                "relationship_score": 7.5,
                "total_revenue": 45000.0,
                "invoice_count": 15,
                "avg_payment_days": 35.2,
                "payment_behavior": "good",
                "late_payments_count": 2,
                "predicted_next_payment_days": 30,
                "churn_risk": 0.15,
                "growth_potential": "high",
                "recommendations": [
                    "Proporre piano annuale con sconto",
                    "Organizzare meeting trimestrale",
                ],
                "warnings": ["Ritardo medio in aumento negli ultimi 3 mesi"],
                "confidence": 0.85,
            }
        }
    )


class PerformanceAnalyticsOutput(BaseModel):
    """
    Structured output for performance analytics agent.

    Provides business performance insights, forecasts, and strategic recommendations.
    """

    period: str = Field(
        ...,
        description="Periodo analizzato (es. Q1 2025, 2024, Jan-Mar 2025)",
    )

    total_revenue: float = Field(
        ...,
        ge=0.0,
        description="Fatturato totale del periodo",
    )

    revenue_growth: float = Field(
        ...,
        description="Crescita fatturato % rispetto periodo precedente",
    )

    invoices_count: int = Field(
        ...,
        ge=0,
        description="Numero fatture emesse nel periodo",
    )

    avg_invoice_value: float = Field(
        ...,
        ge=0.0,
        description="Valore medio fattura",
    )

    revenue_by_client: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Breakdown fatturato per cliente (top N)",
    )

    revenue_by_service: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Breakdown fatturato per tipologia servizio",
    )

    cash_collection_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Tasso di incasso (importo incassato / fatturato)",
    )

    avg_collection_days: float = Field(
        default=0.0,
        ge=0.0,
        description="Giorni medi di incasso",
    )

    revenue_forecast_next_period: float = Field(
        default=0.0,
        ge=0.0,
        description="Previsione fatturato periodo successivo",
    )

    forecast_confidence_interval: tuple[float, float] | None = Field(
        default=None,
        description="Intervallo di confidenza previsione (min, max)",
    )

    key_insights: list[str] = Field(
        default_factory=list,
        description="Insight chiave dalle analisi",
    )

    performance_trends: dict[str, str] = Field(
        default_factory=dict,
        description="Trend per metrica (improving, stable, declining)",
    )

    strategic_recommendations: list[str] = Field(
        default_factory=list,
        description="Raccomandazioni strategiche",
    )

    risk_factors: list[str] = Field(
        default_factory=list,
        description="Fattori di rischio identificati",
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Livello di confidenza dell'analisi (0.0-1.0)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": "Q1 2025",
                "total_revenue": 65000.0,
                "revenue_growth": 15.5,
                "invoices_count": 45,
                "avg_invoice_value": 1444.44,
                "revenue_by_client": [
                    {"client": "Acme Corp", "revenue": 15000.0, "percentage": 23.1}
                ],
                "revenue_by_service": [
                    {"service": "Consulenza", "revenue": 40000.0, "percentage": 61.5}
                ],
                "cash_collection_rate": 0.92,
                "avg_collection_days": 38.5,
                "revenue_forecast_next_period": 72000.0,
                "forecast_confidence_interval": [65000.0, 79000.0],
                "key_insights": [
                    "Crescita costante negli ultimi 3 mesi",
                    "Servizi di consulenza in forte espansione",
                ],
                "performance_trends": {
                    "revenue": "improving",
                    "collection_rate": "stable",
                },
                "strategic_recommendations": [
                    "Aumentare capacità per sostenere crescita",
                    "Esplorare servizi complementari",
                ],
                "risk_factors": ["Alta concentrazione su top 3 clienti"],
                "confidence": 0.82,
            }
        }
    )
