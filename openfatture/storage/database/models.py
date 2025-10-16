"""SQLAlchemy models for OpenFatture."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...utils.datetime import utc_now
from .base import Base, IntPKMixin

if TYPE_CHECKING:
    from ...payment.domain.payment_allocation import PaymentAllocation


# Enums for invoice states and types
class TipoDocumento(PyEnum):
    """Document types according to FatturaPA specifications."""

    TD01 = "TD01"  # Fattura
    TD02 = "TD02"  # Acconto/Anticipo su fattura
    TD03 = "TD03"  # Acconto/Anticipo su parcella
    TD04 = "TD04"  # Nota di credito
    TD05 = "TD05"  # Nota di debito
    TD06 = "TD06"  # Parcella
    TD16 = "TD16"  # Integrazione fattura reverse charge interno
    TD17 = "TD17"  # Integrazione/autofattura per acquisto servizi da estero
    TD18 = "TD18"  # Integrazione per acquisto di beni intracomunitari
    TD19 = "TD19"  # Integrazione/autofattura per acquisto di beni ex art.17 c.2 DPR 633/72
    TD20 = "TD20"  # Autofattura per regolarizzazione e integrazione delle fatture
    TD21 = "TD21"  # Autofattura per splafonamento
    TD22 = "TD22"  # Estrazione beni da Deposito IVA
    TD23 = "TD23"  # Estrazione beni da Deposito IVA con versamento IVA
    TD24 = "TD24"  # Fattura differita di cui art.21, comma 4, lett. a)
    TD25 = "TD25"  # Fattura differita di cui art.21, comma 4, terzo periodo lett. b)
    TD26 = "TD26"  # Cessione di beni ammortizzabili e per passaggi interni
    TD27 = "TD27"  # Fattura per autoconsumo o per cessioni gratuite senza rivalsa


class StatoFattura(PyEnum):
    """Invoice status."""

    BOZZA = "bozza"  # Draft
    DA_INVIARE = "da_inviare"  # To be sent
    INVIATA = "inviata"  # Sent to SDI
    CONSEGNATA = "consegnata"  # Delivered by SDI
    ACCETTATA = "accettata"  # Accepted by recipient
    RIFIUTATA = "rifiutata"  # Rejected by recipient
    SCARTATA = "scartata"  # Discarded by SDI (validation errors)
    ERRORE = "errore"  # Delivery error (recipient unreachable)


class RegimeFiscale(PyEnum):
    """Tax regimes according to Italian law."""

    RF01 = "RF01"  # Ordinario
    RF02 = "RF02"  # Contribuenti minimi
    RF04 = "RF04"  # Agricoltura e attività connesse e pesca
    RF05 = "RF05"  # Vendita sali e tabacchi
    RF06 = "RF06"  # Commercio fiammiferi
    RF07 = "RF07"  # Editoria
    RF08 = "RF08"  # Gestione servizi telefonia pubblica
    RF09 = "RF09"  # Rivendita documenti di trasporto pubblico e di sosta
    RF10 = "RF10"  # Intrattenimenti, giochi e altre attività
    RF11 = "RF11"  # Agenzie di viaggi e turismo
    RF12 = "RF12"  # Agriturismo
    RF13 = "RF13"  # Vendite a domicilio
    RF14 = "RF14"  # Rivendita beni usati, oggetti d'arte, d'antiquariato
    RF15 = "RF15"  # Agenzie di vendite all'asta
    RF16 = "RF16"  # IVA per cassa P.A.
    RF17 = "RF17"  # IVA per cassa
    RF18 = "RF18"  # Altro
    RF19 = "RF19"  # Regime forfettario


class StatoPagamento(PyEnum):
    """Payment status."""

    DA_PAGARE = "da_pagare"  # To be paid
    PAGATO_PARZIALE = "pagato_parziale"  # Partially paid
    PAGATO = "pagato"  # Paid
    SCADUTO = "scaduto"  # Overdue


class StatoPreventivo(PyEnum):
    """Quote/Estimate status."""

    BOZZA = "bozza"  # Draft
    INVIATO = "inviato"  # Sent to client
    ACCETTATO = "accettato"  # Accepted by client
    RIFIUTATO = "rifiutato"  # Rejected by client
    SCADUTO = "scaduto"  # Expired
    CONVERTITO = "convertito"  # Converted to invoice


class FeedbackType(PyEnum):
    """User feedback type."""

    RATING = "rating"  # Star rating (1-5)
    CORRECTION = "correction"  # User corrected AI output
    COMMENT = "comment"  # Textual comment
    THUMBS_UP = "thumbs_up"  # Quick positive feedback
    THUMBS_DOWN = "thumbs_down"  # Quick negative feedback


class PredictionType(PyEnum):
    """ML prediction type for feedback tracking."""

    INVOICE_DELAY = "invoice_delay"  # Cash flow prediction
    TAX_SUGGESTION = "tax_suggestion"  # VAT/tax recommendation
    DESCRIPTION_GENERATION = "description_generation"  # Invoice description AI
    CLIENT_RECOMMENDATION = "client_recommendation"  # Client suggestions


# Models
class Cliente(IntPKMixin, Base):
    """Client/Customer model."""

    __tablename__ = "clienti"

    # Anagrafica
    denominazione: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    nome: Mapped[str | None] = mapped_column(String(100))
    cognome: Mapped[str | None] = mapped_column(String(100))

    # Dati fiscali
    codice_fiscale: Mapped[str | None] = mapped_column(String(16), index=True)
    partita_iva: Mapped[str | None] = mapped_column(String(11), index=True)

    # Indirizzo
    indirizzo: Mapped[str | None] = mapped_column(String(200))
    numero_civico: Mapped[str | None] = mapped_column(String(10))
    cap: Mapped[str | None] = mapped_column(String(5))
    comune: Mapped[str | None] = mapped_column(String(100))
    provincia: Mapped[str | None] = mapped_column(String(2))
    nazione: Mapped[str] = mapped_column(String(2), default="IT")

    # SDI
    codice_destinatario: Mapped[str | None] = mapped_column(String(7))
    pec: Mapped[str | None] = mapped_column(String(256))

    # Contatti
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(256))

    # Note
    note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    fatture: Mapped[list[Fattura]] = relationship(back_populates="cliente")
    preventivi: Mapped[list[Preventivo]] = relationship(back_populates="cliente")

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, denominazione='{self.denominazione}')>"


class Preventivo(IntPKMixin, Base):
    """Quote/Estimate model."""

    __tablename__ = "preventivi"

    # Numero preventivo (progressivo annuale)
    numero: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    anno: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Date
    data_emissione: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    data_scadenza: Mapped[date] = mapped_column(Date, nullable=False)

    # Cliente
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clienti.id"), nullable=False)
    cliente: Mapped[Cliente] = relationship(back_populates="preventivi")

    # Importi (calcolati dalle righe)
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Stato
    stato: Mapped[StatoPreventivo] = mapped_column(
        Enum(StatoPreventivo), nullable=False, default=StatoPreventivo.BOZZA
    )

    # Note e condizioni
    note: Mapped[str | None] = mapped_column(Text)
    condizioni: Mapped[str | None] = mapped_column(Text)  # Terms and conditions

    # Validità (giorni)
    validita_giorni: Mapped[int] = mapped_column(Integer, default=30)

    # File path (PDF)
    pdf_path: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    righe: Mapped[list[RigaPreventivo]] = relationship(
        back_populates="preventivo", cascade="all, delete-orphan"
    )
    fattura: Mapped[Fattura | None] = relationship(back_populates="preventivo")

    def __repr__(self) -> str:
        return f"<Preventivo(id={self.id}, numero='{self.numero}/{self.anno}', stato='{self.stato.value}')>"


class Prodotto(IntPKMixin, Base):
    """Product/Service model."""

    __tablename__ = "prodotti"

    codice: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    descrizione: Mapped[str] = mapped_column(String(500), nullable=False)
    prezzo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aliquota_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=22.00)

    # Unità di misura
    unita_misura: Mapped[str] = mapped_column(String(10), default="ore")

    # Categoria (es. "Consulenza", "Sviluppo", "Design")
    categoria: Mapped[str | None] = mapped_column(String(100))

    # Flag per servizi vs beni
    is_servizio: Mapped[bool] = mapped_column(Boolean, default=True)

    # Note
    note: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Prodotto(id={self.id}, codice='{self.codice}', descrizione='{self.descrizione}')>"


class Fattura(IntPKMixin, Base):
    """Invoice model."""

    __tablename__ = "fatture"

    # Numero fattura (progressivo annuale)
    numero: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    anno: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Data
    data_emissione: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    # Tipo documento
    tipo_documento: Mapped[TipoDocumento] = mapped_column(
        Enum(TipoDocumento), nullable=False, default=TipoDocumento.TD01
    )

    # Cliente
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clienti.id"), nullable=False)
    cliente: Mapped[Cliente] = relationship(back_populates="fatture")

    # Preventivo (optional - if invoice was generated from a quote)
    preventivo_id: Mapped[int | None] = mapped_column(ForeignKey("preventivi.id"))

    # Importi (calcolati dalle righe)
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Ritenuta d'acconto (per professionisti)
    ritenuta_acconto: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    aliquota_ritenuta: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)

    # Bollo
    importo_bollo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Stato
    stato: Mapped[StatoFattura] = mapped_column(
        Enum(StatoFattura), nullable=False, default=StatoFattura.BOZZA
    )

    # File paths
    xml_path: Mapped[str | None] = mapped_column(String(500))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    xml_firmato_path: Mapped[str | None] = mapped_column(String(500))

    # SDI
    numero_sdi: Mapped[str | None] = mapped_column(String(50))  # Identificativo SDI
    data_invio_sdi: Mapped[datetime | None] = mapped_column()
    data_consegna_sdi: Mapped[datetime | None] = mapped_column()

    # Note
    note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    righe: Mapped[list[RigaFattura]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )
    pagamenti: Mapped[list[Pagamento]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )
    log_sdi: Mapped[list[LogSDI]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )
    preventivo: Mapped[Preventivo | None] = relationship(back_populates="fattura")

    def __repr__(self) -> str:
        return f"<Fattura(id={self.id}, numero='{self.numero}/{self.anno}', stato='{self.stato.value}')>"


class RigaFattura(IntPKMixin, Base):
    """Invoice line item."""

    __tablename__ = "righe_fattura"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="righe")

    # Riga
    numero_riga: Mapped[int] = mapped_column(Integer, nullable=False)

    # Descrizione
    descrizione: Mapped[str] = mapped_column(Text, nullable=False)

    # Quantità e prezzo
    quantita: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    prezzo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unita_misura: Mapped[str] = mapped_column(String(10), default="ore")

    # IVA
    aliquota_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=22.00)

    # Totali
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<RigaFattura(id={self.id}, fattura_id={self.fattura_id}, descrizione='{self.descrizione[:30]}...')>"


class RigaPreventivo(IntPKMixin, Base):
    """Quote/Estimate line item."""

    __tablename__ = "righe_preventivo"

    preventivo_id: Mapped[int] = mapped_column(ForeignKey("preventivi.id"), nullable=False)
    preventivo: Mapped[Preventivo] = relationship(back_populates="righe")

    # Riga
    numero_riga: Mapped[int] = mapped_column(Integer, nullable=False)

    # Descrizione
    descrizione: Mapped[str] = mapped_column(Text, nullable=False)

    # Quantità e prezzo
    quantita: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    prezzo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unita_misura: Mapped[str] = mapped_column(String(10), default="ore")

    # IVA
    aliquota_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=22.00)

    # Totali
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<RigaPreventivo(id={self.id}, preventivo_id={self.preventivo_id}, descrizione='{self.descrizione[:30]}...')>"


class Pagamento(IntPKMixin, Base):
    """Payment tracking."""

    __tablename__ = "pagamenti"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="pagamenti")

    # Importo
    importo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    importo_pagato: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )

    # Date
    data_scadenza: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date)

    # Stato
    stato: Mapped[StatoPagamento] = mapped_column(
        Enum(StatoPagamento), nullable=False, default=StatoPagamento.DA_PAGARE
    )

    # Modalità (Bonifico, Contanti, RiBa, ecc.)
    modalita: Mapped[str] = mapped_column(String(50), default="Bonifico")

    # Riferimenti bancari
    iban: Mapped[str | None] = mapped_column(String(27))
    bic_swift: Mapped[str | None] = mapped_column(String(11))

    # Note
    note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    allocations: Mapped[list[PaymentAllocation]] = relationship(
        "PaymentAllocation", back_populates="payment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Pagamento(id={self.id}, fattura_id={self.fattura_id}, importo={self.importo}, stato='{self.stato.value}')>"

    @property
    def importo_da_pagare(self) -> Decimal:
        """Total amount due for the payment (alias of importo column)."""
        return self.importo

    @importo_da_pagare.setter
    def importo_da_pagare(self, value: Decimal | float | str) -> None:
        """Allow assignments using semantic name expected by services/tests."""
        self.importo = Decimal(str(value))

    @property
    def saldo_residuo(self) -> Decimal:
        """Outstanding balance still to be paid."""
        outstanding = Decimal(self.importo_da_pagare) - Decimal(self.importo_pagato or 0)
        if outstanding < Decimal("0.00"):
            return Decimal("0.00")
        return outstanding

    def apply_payment(self, amount: Decimal, pagamento_effective_date: date | None = None) -> None:
        """Record a payment allocation against this Pagamento."""
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= Decimal("0.00"):
            raise ValueError("Payment amount must be positive")

        nuovo_pagato = Decimal(self.importo_pagato or 0) + amount_decimal
        if nuovo_pagato > Decimal(self.importo_da_pagare):
            nuovo_pagato = Decimal(self.importo_da_pagare)

        self.importo_pagato = nuovo_pagato

        if self.importo_pagato >= self.importo_da_pagare:
            self.stato = StatoPagamento.PAGATO
            if pagamento_effective_date:
                self.data_pagamento = pagamento_effective_date
        elif self.importo_pagato > Decimal("0.00"):
            self.stato = StatoPagamento.PAGATO_PARZIALE
            if pagamento_effective_date and self.data_pagamento is None:
                self.data_pagamento = pagamento_effective_date

    def revert_payment(self, amount: Decimal) -> None:
        """Roll back a previously applied payment amount."""
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= Decimal("0.00"):
            raise ValueError("Revert amount must be positive")

        current_paid = Decimal(self.importo_pagato or 0)
        if amount_decimal > current_paid:
            raise ValueError(
                f"Cannot revert {amount_decimal} because only {current_paid} has been paid"
            )

        nuovo_pagato = current_paid - amount_decimal
        self.importo_pagato = nuovo_pagato

        if nuovo_pagato <= Decimal("0.00"):
            self.stato = StatoPagamento.DA_PAGARE
            self.data_pagamento = None
        elif nuovo_pagato < Decimal(self.importo_da_pagare):
            self.stato = StatoPagamento.PAGATO_PARZIALE
        else:
            self.stato = StatoPagamento.PAGATO


class LogSDI(IntPKMixin, Base):
    """SDI notification log."""

    __tablename__ = "log_sdi"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="log_sdi")

    # Tipo notifica (RC, NS, MC, NE, DT, AT, EC)
    tipo_notifica: Mapped[str] = mapped_column(String(10), nullable=False)

    # Descrizione
    descrizione: Mapped[str] = mapped_column(Text, nullable=False)

    # File XML ricevuto
    xml_path: Mapped[str | None] = mapped_column(String(500))

    # Data ricezione
    data_ricezione: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    def __repr__(self) -> str:
        return f"<LogSDI(id={self.id}, fattura_id={self.fattura_id}, tipo='{self.tipo_notifica}')>"


class UserFeedback(IntPKMixin, Base):
    """User feedback on AI responses and chat interactions.

    Tracks user satisfaction, corrections, and comments to enable
    continuous improvement of AI models through feedback loops.
    """

    __tablename__ = "user_feedback"

    # Session reference (optional - for chat feedback)
    session_id: Mapped[str | None] = mapped_column(String(100), index=True)

    # Message reference (optional - specific message in session)
    message_id: Mapped[str | None] = mapped_column(String(100))

    # Feedback type
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType), nullable=False, index=True
    )

    # Rating (1-5 stars, only for RATING type)
    rating: Mapped[int | None] = mapped_column(Integer)

    # Original AI output (for corrections)
    original_text: Mapped[str | None] = mapped_column(Text)

    # User's corrected version (for CORRECTION type)
    corrected_text: Mapped[str | None] = mapped_column(Text)

    # User comment/explanation
    user_comment: Mapped[str | None] = mapped_column(Text)

    # Agent/feature context
    agent_type: Mapped[str | None] = mapped_column(String(100), index=True)
    feature_name: Mapped[str | None] = mapped_column(String(100))

    # Metadata (JSON-like text field for extensibility)
    metadata_json: Mapped[str | None] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, type='{self.feedback_type.value}', session='{self.session_id}')>"


class ModelPredictionFeedback(IntPKMixin, Base):
    """Feedback on ML model predictions.

    Specifically tracks feedback on ML predictions (cash flow, tax suggestions, etc.)
    to enable model retraining with human-validated corrections.
    """

    __tablename__ = "model_prediction_feedback"

    # Prediction context
    prediction_type: Mapped[PredictionType] = mapped_column(
        Enum(PredictionType), nullable=False, index=True
    )

    # Reference to entity (invoice ID, client ID, etc.)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Original prediction (JSON format)
    prediction_data: Mapped[str] = mapped_column(Text, nullable=False)

    # Model confidence score (0-1)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    # User acceptance
    user_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # User correction (JSON format if applicable)
    user_correction: Mapped[str | None] = mapped_column(Text)

    # User comment/explanation
    user_comment: Mapped[str | None] = mapped_column(Text)

    # Model version (for A/B testing and rollback)
    model_version: Mapped[str | None] = mapped_column(String(50))

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    # Processing flag (for retraining pipeline)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<ModelPredictionFeedback(id={self.id}, type='{self.prediction_type.value}', entity={self.entity_type}:{self.entity_id}, accepted={self.user_accepted})>"


class EventLog(IntPKMixin, Base):
    """Event audit log - stores all domain events for compliance and analytics.

    Captures every domain event published through the event bus for:
    - Audit trail and compliance
    - Historical analysis and reporting
    - Debugging and troubleshooting
    - Analytics and metrics
    """

    __tablename__ = "event_log"

    # Event identification
    event_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )  # UUID as string
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Event payload (JSON serialized)
    event_data: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # Entity tracking (for filtering by entity)
    entity_type: Mapped[str | None] = mapped_column(String(50), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)

    # Additional metadata
    user_id: Mapped[int | None] = mapped_column(Integer)  # For future user tracking
    metadata_json: Mapped[str | None] = mapped_column(Text)  # JSON for additional context

    def __repr__(self) -> str:
        return f"<EventLog(id={self.id}, event_type='{self.event_type}', entity={self.entity_type}:{self.entity_id}, occurred_at='{self.occurred_at}')>"


# Ensure payment allocation model is registered for relationship resolution
from ...payment.domain import payment_allocation as _payment_allocation  # noqa: F401,E402
