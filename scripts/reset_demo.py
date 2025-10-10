#!/usr/bin/env python3
"""
Reset and seed a demo dataset for documentation/media capture.

Usage:
    uv run python scripts/reset_demo.py

This script expects environment variables (or `.env`) to define at least:
    - DATABASE_URL (defaults to sqlite:///./openfatture_demo.db if not set)
    - CEDENTE_* metadata for contextual screenshots (optional)

It will wipe the existing SQLite file (if applicable), recreate the schema,
and populate sample clients, products, invoices, and line items tailored for
the 2025 media scenarios.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from openfatture.storage.database import base as db_base
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    Prodotto,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.utils.config import reload_settings


def _path_from_sqlite_url(database_url: str) -> Path | None:
    """Extract the filesystem path from a sqlite URL."""
    if not database_url.startswith("sqlite:///"):
        return None
    path_str = database_url.removeprefix("sqlite:///")
    return Path(path_str).expanduser()


def reset_database(database_url: str) -> None:
    """Drop the existing SQLite DB file (if present) and recreate schema."""
    db_path = _path_from_sqlite_url(database_url)
    if db_path:
        if db_path.exists():
            db_path.unlink()
        db_path.parent.mkdir(parents=True, exist_ok=True)

    db_base.init_db(database_url)

    # Ensure clean state for non-sqlite URLs (drop all tables if engine is active)
    if db_base.engine is not None:
        with db_base.engine.connect() as connection:
            dialect = connection.dialect.name
            if dialect != "sqlite":
                if dialect == "postgresql":
                    connection.execute(text("SET session_replication_role = 'replica'"))  # type: ignore[arg-type]
                db_base.Base.metadata.drop_all(bind=db_base.engine)
                db_base.Base.metadata.create_all(bind=db_base.engine)
                if dialect == "postgresql":
                    connection.execute(text("SET session_replication_role = 'origin'"))  # type: ignore[arg-type]


def seed_demo_data() -> None:
    """Populate the database with deterministic demo data."""
    settings = reload_settings()
    reset_database(settings.database_url)

    session = db_base.SessionLocal()
    try:
        clients = [
            Cliente(
                denominazione="ACME Innovazione S.r.l.",
                partita_iva="10293847561",
                codice_fiscale="ACMINN85L01H501Z",
                codice_destinatario="ABC1234",
                pec="acme.innovazione@pec.demo.it",
                indirizzo="Via Industria 10",
                cap="20121",
                comune="Milano",
                provincia="MI",
                nazione="IT",
                email="amministrazione@acme-demo.it",
            ),
            Cliente(
                denominazione="Studio Legale Aurora",
                partita_iva="01928374650",
                codice_fiscale="STLAUR80A41F205S",
                codice_destinatario="0000000",
                pec="studio.aurora@pec.demo.it",
                indirizzo="Corso Italia 45",
                cap="40121",
                comune="Bologna",
                provincia="BO",
                nazione="IT",
                email="contabilita@studioaurora.demo",
            ),
            Cliente(
                denominazione="Freelance Lab di Marta Neri",
                partita_iva="01234567890",
                codice_fiscale="NERMRT90B41H501U",
                codice_destinatario="KRRH6B9",
                pec="marta.neri@pec.demo.it",
                indirizzo="Via Garibaldi 12",
                cap="10121",
                comune="Torino",
                provincia="TO",
                nazione="IT",
                email="hello@freelancelab.demo",
            ),
        ]
        session.add_all(clients)
        session.flush()

        products = [
            Prodotto(
                codice="CONS_GDPR",
                descrizione="Consulenza GDPR avanzata",
                prezzo_unitario=Decimal("120.00"),
                aliquota_iva=Decimal("22.00"),
                unita_misura="ore",
                categoria="Consulenza",
                note="Include valutazione DPIA e piano remediation.",
            ),
            Prodotto(
                codice="DEV_BACKEND",
                descrizione="Sviluppo backend API FastAPI",
                prezzo_unitario=Decimal("95.00"),
                aliquota_iva=Decimal("22.00"),
                unita_misura="ore",
                categoria="Sviluppo",
                note="Sprint di sviluppo backend con test automatici.",
            ),
            Prodotto(
                codice="FORMAZIONE_AI",
                descrizione="Workshop AI Assistants per team finance",
                prezzo_unitario=Decimal("1500.00"),
                aliquota_iva=Decimal("22.00"),
                unita_misura="sessione",
                categoria="Formazione",
                note="Sessione di 4h + materiali personalizzati.",
            ),
        ]
        session.add_all(products)
        session.flush()

        def create_invoice(
            *,
            cliente: Cliente,
            numero: str,
            giorno_offset: int,
            righe: list[dict[str, Decimal | Prodotto | str | float]],
            stato: StatoFattura,
        ) -> Fattura:
            emission_date = date.today().replace(day=1) - timedelta(days=giorno_offset)
            fattura = Fattura(
                numero=numero,
                anno=emission_date.year,
                data_emissione=emission_date,
                cliente_id=cliente.id,
                tipo_documento=TipoDocumento.TD01,
                stato=stato,
                note=f"Scenario demo {numero}",
            )
            session.add(fattura)
            session.flush()

            totale_imponibile = Decimal("0")
            totale_iva = Decimal("0")

            for idx, riga in enumerate(righe, start=1):
                prodotto = riga["prodotto"]
                quantita = Decimal(str(riga.get("quantita", Decimal("1"))))
                prezzo = Decimal(str(riga.get("prezzo", prodotto.prezzo_unitario)))
                aliquota = Decimal(str(riga.get("aliquota", prodotto.aliquota_iva)))

                imponibile = quantita * prezzo
                iva = (imponibile * aliquota) / Decimal("100")
                totale = imponibile + iva

                session.add(
                    RigaFattura(
                        fattura_id=fattura.id,
                        numero_riga=idx,
                        descrizione=f"{prodotto.descrizione} ({riga.get('descrizione_extra', 'Servizio')})",
                        quantita=quantita,
                        prezzo_unitario=prezzo,
                        aliquota_iva=aliquota,
                        imponibile=imponibile,
                        iva=iva,
                        totale=totale,
                    )
                )

                totale_imponibile += imponibile
                totale_iva += iva

            fattura.imponibile = totale_imponibile
            fattura.iva = totale_iva
            fattura.totale = totale_imponibile + totale_iva

            if stato in {StatoFattura.INVIATA, StatoFattura.CONSEGNATA}:
                fattura.data_invio = emission_date + timedelta(days=1)

            return fattura

        invoices = [
            create_invoice(
                cliente=clients[0],
                numero="2025-001",
                giorno_offset=12,
                righe=[
                    {
                        "prodotto": products[0],
                        "quantita": Decimal("6"),
                        "descrizione_extra": "Analisi e workshop",
                    },
                    {
                        "prodotto": products[1],
                        "quantita": Decimal("8"),
                        "prezzo": Decimal("100.00"),
                    },
                ],
                stato=StatoFattura.BOZZA,
            ),
            create_invoice(
                cliente=clients[1],
                numero="2025-002",
                giorno_offset=25,
                righe=[
                    {
                        "prodotto": products[2],
                        "quantita": Decimal("1"),
                        "descrizione_extra": "Sessione onsite",
                    },
                    {
                        "prodotto": products[0],
                        "quantita": Decimal("2"),
                        "prezzo": Decimal("130.00"),
                    },
                ],
                stato=StatoFattura.INVIATA,
            ),
            create_invoice(
                cliente=clients[2],
                numero="2025-003",
                giorno_offset=35,
                righe=[
                    {
                        "prodotto": products[1],
                        "quantita": Decimal("12"),
                        "prezzo": Decimal("90.00"),
                    },
                ],
                stato=StatoFattura.CONSEGNATA,
            ),
        ]

        session.add_all(invoices)
        session.commit()

        print("✅ Demo dataset generated successfully:")
        print(f"  • Clients: {len(clients)}")
        print(f"  • Products: {len(products)}")
        print(f"  • Invoices: {len(invoices)} (statuses: bozza/inviata/consegnata)")
        print(f"  • Database URL: {settings.database_url}\n")

    finally:
        session.close()


if __name__ == "__main__":
    seed_demo_data()
