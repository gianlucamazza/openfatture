"""Structured output models for AI agents."""

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
