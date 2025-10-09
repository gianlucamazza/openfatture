"""SQLAlchemy models for OpenFatture."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


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


# Models
class Cliente(Base):
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
    fatture: Mapped[list["Fattura"]] = relationship(back_populates="cliente")

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, denominazione='{self.denominazione}')>"


class Prodotto(Base):
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


class Fattura(Base):
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
    cliente: Mapped["Cliente"] = relationship(back_populates="fatture")

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
    righe: Mapped[list["RigaFattura"]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )
    pagamenti: Mapped[list["Pagamento"]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )
    log_sdi: Mapped[list["LogSDI"]] = relationship(
        back_populates="fattura", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Fattura(id={self.id}, numero='{self.numero}/{self.anno}', stato='{self.stato.value}')>"


class RigaFattura(Base):
    """Invoice line item."""

    __tablename__ = "righe_fattura"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped["Fattura"] = relationship(back_populates="righe")

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


class Pagamento(Base):
    """Payment tracking."""

    __tablename__ = "pagamenti"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped["Fattura"] = relationship(back_populates="pagamenti")

    # Importo
    importo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

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

    def __repr__(self) -> str:
        return f"<Pagamento(id={self.id}, fattura_id={self.fattura_id}, importo={self.importo}, stato='{self.stato.value}')>"


class LogSDI(Base):
    """SDI notification log."""

    __tablename__ = "log_sdi"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped["Fattura"] = relationship(back_populates="log_sdi")

    # Tipo notifica (RC, NS, MC, NE, DT, AT, EC)
    tipo_notifica: Mapped[str] = mapped_column(String(10), nullable=False)

    # Descrizione
    descrizione: Mapped[str] = mapped_column(Text, nullable=False)

    # File XML ricevuto
    xml_path: Mapped[str | None] = mapped_column(String(500))

    # Data ricezione
    data_ricezione: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LogSDI(id={self.id}, fattura_id={self.fattura_id}, tipo='{self.tipo_notifica}')>"
