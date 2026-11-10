"""Billing models: clients, products, invoices and their lines."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IntPKMixin

if TYPE_CHECKING:
    from .payments import CollectionEntry, CollectionStatement, Pagamento
    from .quotes import Preventivo
    from .sdi import LogSDI, SDINotificationRecord, SDISubmissionAttempt


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
    regime_fiscale: Mapped[str] = mapped_column(String(4), default="RF01", nullable=False)

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

    # Relationships
    righe: Mapped[list[RigaFattura]] = relationship("RigaFattura", back_populates="prodotto")

    def __repr__(self) -> str:
        return f"<Prodotto(id={self.id}, codice='{self.codice}', descrizione='{self.descrizione}')>"


class Fattura(IntPKMixin, Base):
    """Invoice model."""

    __tablename__ = "fatture"
    __table_args__ = (
        # Progressive numbering is unique per year (art. 21 DPR 633/72)
        Index("uq_fatture_numero_anno", "numero", "anno", unique=True),
    )

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
    # Imposta di bollo owed (always paid virtually); charging it to the
    # customer is a separate N1 line. Computed by billing.application.totals.
    importo_bollo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # STORICO / issued elsewhere flag
    # True = invoice was issued by another system/person (stored here for reference only)
    # Blocks: XML generation, SDI sending, emit flows
    issued_elsewhere: Mapped[bool] = mapped_column(Boolean, default=False)

    # Linkage for nota di credito (TD04) - DatiFattureCollegate
    # Reference to source invoice when this is a credit note
    fattura_collegata_id: Mapped[int | None] = mapped_column(ForeignKey("fatture.id"), index=True)
    fattura_collegata_numero: Mapped[str | None] = mapped_column(String(20))
    fattura_collegata_data: Mapped[date | None] = mapped_column(Date)

    # Stato
    stato: Mapped[StatoFattura] = mapped_column(
        Enum(StatoFattura), nullable=False, default=StatoFattura.BOZZA
    )

    # File paths
    xml_path: Mapped[str | None] = mapped_column(String(500))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    xml_firmato_path: Mapped[str | None] = mapped_column(String(500))

    collection_entries: Mapped[list[CollectionEntry]] = relationship()
    collection_statements: Mapped[list[CollectionStatement]] = relationship()

    sdi_receipts: Mapped[list[SDINotificationRecord]] = relationship()
    sdi_submissions: Mapped[list[SDISubmissionAttempt]] = relationship(
        foreign_keys="SDISubmissionAttempt.invoice_id"
    )

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
    cassa_previdenziale: Mapped[list[DatiCassaPrevidenziale]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Fattura(id={self.id}, numero='{self.numero}/{self.anno}', stato='{self.stato.value}')>"


class RigaFattura(IntPKMixin, Base):
    """Invoice line item."""

    __tablename__ = "righe_fattura"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="righe")

    prodotto_id: Mapped[int | None] = mapped_column(
        ForeignKey("prodotti.id", ondelete="SET NULL"), nullable=True, index=True
    )
    prodotto: Mapped[Prodotto | None] = relationship("Prodotto", back_populates="righe")

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

    # Natura IVA (for zero-rated, exempt, or out-of-scope transactions)
    # Valid values: N1, N2.1, N2.2, N3.1-N3.6, N4, N5, N6.1-N6.9, N7
    natura: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Totali
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<RigaFattura(id={self.id}, fattura_id={self.fattura_id}, descrizione='{self.descrizione[:30]}...')>"


class DatiCassaPrevidenziale(IntPKMixin, Base):
    """Social security contribution data (DatiCassaPrevidenziale).

    Used for professionals who need to apply social security contributions
    (e.g., INPS for lawyers, accountants, etc.) on their invoices.
    """

    __tablename__ = "dati_cassa_previdenziale"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="cassa_previdenziale")

    # Tipo cassa (TC01-TC22)
    # TC01 = Cassa nazionale previdenza avvocati
    # TC02 = Cassa previdenza dottori commercialisti
    # TC03 = Cassa previdenza e assistenza geometri
    # etc.
    tipo_cassa: Mapped[str] = mapped_column(String(4), nullable=False)

    # Aliquota contributo (e.g., 4.00 for 4%)
    al_cassa: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Importo contributo cassa
    importo_contributo_cassa: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Imponibile cassa (optional - base amount for contribution calculation)
    imponibile_cassa: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Aliquota IVA applicata al contributo
    aliquota_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Ritenuta (optional - SI if withholding tax applies)
    ritenuta: Mapped[str | None] = mapped_column(String(2))

    # Natura (optional - tax nature code if VAT is zero or exempt)
    natura: Mapped[str | None] = mapped_column(String(10))

    # Riferimento amministrazione (optional)
    riferimento_amministrazione: Mapped[str | None] = mapped_column(String(20))

    def __repr__(self) -> str:
        return f"<DatiCassaPrevidenziale(id={self.id}, fattura_id={self.fattura_id}, tipo_cassa='{self.tipo_cassa}')>"
