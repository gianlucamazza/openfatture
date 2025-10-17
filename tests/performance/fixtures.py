"""Dataset generators for performance testing.

Provides realistic test data for benchmarking:
- Invoice (Fattura) generation
- Client (Cliente) generation
- Payment (Pagamento) generation
- Bulk data generation with relationships
"""

from datetime import date, timedelta
from decimal import Decimal
from random import Random
from typing import Any

from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    Pagamento,
    RigaFattura,
    StatoFattura,
    StatoPagamento,
    TipoDocumento,
)


class DataGenerator:
    """Generate realistic test data for performance testing.

    Uses seeded random generator for reproducible datasets.

    Example:
        >>> gen = DataGenerator(seed=42)
        >>> clienti = gen.generate_clients(count=100)
        >>> fatture = gen.generate_invoices(clienti, count=1000)
    """

    def __init__(self, seed: int = 42):
        """Initialize generator with seed.

        Args:
            seed: Random seed for reproducibility
        """
        self.rng = Random(seed)
        self._company_names = [
            "Tech Solutions",
            "Digital Agency",
            "Marketing Pro",
            "Software House",
            "Consulting Group",
            "IT Services",
            "Web Studio",
            "Creative Lab",
            "Business Partners",
            "Innovation Hub",
        ]
        self._services = [
            "Consulenza informatica",
            "Sviluppo software personalizzato",
            "Progettazione siti web",
            "Manutenzione sistemi IT",
            "Assistenza tecnica",
            "Analisi dati",
            "Marketing digitale",
            "Gestione social media",
            "Formazione aziendale",
            "Ottimizzazione processi",
        ]

    def generate_clients(self, count: int = 100) -> list[Cliente]:
        """Generate realistic client data.

        Args:
            count: Number of clients to generate

        Returns:
            List of Cliente objects
        """
        clienti = []

        for i in range(count):
            # Generate P.IVA (11 digits)
            partita_iva = f"{self.rng.randint(10000000000, 99999999999)}"

            # Generate codice fiscale (16 chars)
            codice_fiscale = f"{''.join(self.rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))}{self.rng.randint(10, 99)}A{self.rng.randint(10, 99)}A{''.join(self.rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))}"

            cliente = Cliente(
                denominazione=f"{self.rng.choice(self._company_names)} {i+1}",
                partita_iva=partita_iva,
                codice_fiscale=codice_fiscale if self.rng.random() > 0.3 else None,
                indirizzo=f"Via {self.rng.choice(['Roma', 'Milano', 'Napoli', 'Torino'])} {self.rng.randint(1, 200)}",
                cap=f"{self.rng.randint(10000, 99999)}",
                comune=self.rng.choice(["Milano", "Roma", "Torino", "Bologna", "Firenze"]),
                provincia=self.rng.choice(["MI", "RM", "TO", "BO", "FI"]),
                nazione="IT",
                codice_destinatario=f"{''.join(self.rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=7))}",
                email=f"cliente{i+1}@example.com",
                telefono=f"+39 {self.rng.randint(300, 399)} {self.rng.randint(1000000, 9999999)}",
            )
            clienti.append(cliente)

        return clienti

    def generate_invoices(
        self,
        clienti: list[Cliente],
        count: int = 1000,
        year: int = 2025,
        with_lines: bool = True,
    ) -> list[Fattura]:
        """Generate realistic invoice data.

        Args:
            clienti: List of clients to associate invoices with
            count: Number of invoices to generate
            year: Invoice year
            with_lines: Whether to generate invoice lines

        Returns:
            List of Fattura objects
        """
        fatture = []
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        date_range = (end_date - start_date).days

        for i in range(count):
            # Random date in year
            invoice_date = start_date + timedelta(days=self.rng.randint(0, date_range))

            # Random client
            cliente = self.rng.choice(clienti)

            # Random stato (weighted towards INVIATA/CONSEGNATA for realism)
            stato = self.rng.choices(
                [
                    StatoFattura.BOZZA,
                    StatoFattura.DA_INVIARE,
                    StatoFattura.INVIATA,
                    StatoFattura.CONSEGNATA,
                ],
                weights=[0.1, 0.1, 0.3, 0.5],
            )[0]

            fattura = Fattura(
                numero=f"{i+1:04d}",
                anno=year,
                data_emissione=invoice_date,
                tipo_documento=TipoDocumento.TD01,
                cliente=cliente,
                stato=stato,
                imponibile=Decimal("0.00"),
                iva=Decimal("0.00"),
                totale=Decimal("0.00"),
            )

            if with_lines:
                num_lines = self.rng.randint(1, 5)
                fattura.righe = self._generate_invoice_lines(fattura, num_lines)

                # Calculate totals
                fattura.imponibile = sum(riga.imponibile for riga in fattura.righe)
                fattura.iva = sum(riga.iva for riga in fattura.righe)
                fattura.totale = fattura.imponibile + fattura.iva

            fatture.append(fattura)

        return fatture

    def _generate_invoice_lines(self, fattura: Fattura, count: int) -> list[RigaFattura]:
        """Generate invoice line items.

        Args:
            fattura: Parent invoice
            count: Number of lines to generate

        Returns:
            List of RigaFattura objects
        """
        righe = []

        for i in range(count):
            quantita = Decimal(str(self.rng.uniform(1.0, 100.0))).quantize(Decimal("0.01"))
            prezzo_unitario = Decimal(str(self.rng.uniform(10.0, 500.0))).quantize(Decimal("0.01"))
            aliquota_iva = Decimal("22.00")  # Most common IVA rate in Italy

            imponibile = quantita * prezzo_unitario
            iva = (imponibile * aliquota_iva / Decimal("100")).quantize(Decimal("0.01"))
            totale = imponibile + iva

            riga = RigaFattura(
                fattura=fattura,
                numero_riga=i + 1,
                descrizione=self.rng.choice(self._services),
                quantita=quantita,
                prezzo_unitario=prezzo_unitario,
                unita_misura=self.rng.choice(["ore", "giorni", "cad", "mese"]),
                aliquota_iva=aliquota_iva,
                imponibile=imponibile,
                iva=iva,
                totale=totale,
            )
            righe.append(riga)

        return righe

    def generate_payments(
        self, fatture: list[Fattura], payment_rate: float = 0.7
    ) -> list[Pagamento]:
        """Generate payment records for invoices.

        Args:
            fatture: List of invoices to generate payments for
            payment_rate: Probability that an invoice has a payment (0.0-1.0)

        Returns:
            List of Pagamento objects
        """
        pagamenti = []

        for fattura in fatture:
            if self.rng.random() < payment_rate:
                # Payment due date (30-60 days after invoice)
                data_scadenza = fattura.data_emissione + timedelta(days=self.rng.randint(30, 60))

                # Random payment status
                stato = self.rng.choices(
                    [
                        StatoPagamento.DA_PAGARE,
                        StatoPagamento.PAGATO_PARZIALE,
                        StatoPagamento.PAGATO,
                    ],
                    weights=[0.2, 0.1, 0.7],
                )[0]

                importo = fattura.totale
                importo_pagato = Decimal("0.00")

                if stato == StatoPagamento.PAGATO:
                    importo_pagato = importo
                    data_pagamento = data_scadenza - timedelta(
                        days=self.rng.randint(0, 10)
                    )  # Paid a bit early/on time
                elif stato == StatoPagamento.PAGATO_PARZIALE:
                    importo_pagato = importo * Decimal(str(self.rng.uniform(0.3, 0.9))).quantize(
                        Decimal("0.01")
                    )
                    data_pagamento = data_scadenza
                else:
                    data_pagamento = None

                pagamento = Pagamento(
                    fattura=fattura,
                    importo=importo,
                    importo_pagato=importo_pagato,
                    data_scadenza=data_scadenza,
                    data_pagamento=data_pagamento,
                    stato=stato,
                    modalita="Bonifico",
                    iban=f"IT{self.rng.randint(10, 99)}{self.rng.randint(10, 99)}{self.rng.randint(10000000000000000000, 99999999999999999999)}",
                )
                pagamenti.append(pagamento)

        return pagamenti

    def generate_documents_for_rag(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate text documents for RAG vector store testing.

        Args:
            count: Number of documents to generate

        Returns:
            List of document dicts with text and metadata
        """
        documents = []

        for i in range(count):
            # Generate realistic invoice-like text
            company = self.rng.choice(self._company_names)
            service = self.rng.choice(self._services)
            amount = self.rng.uniform(100, 5000)
            invoice_num = f"{i+1:04d}"
            year = 2025

            text = f"Fattura {invoice_num}/{year} - Cliente: {company} SRL\n"
            text += f"Servizio: {service}\n"
            text += f"Importo: €{amount:.2f}\n"
            text += f"P.IVA: {self.rng.randint(10000000000, 99999999999)}"

            metadata = {
                "type": "invoice",
                "invoice_id": i + 1,
                "invoice_number": invoice_num,
                "invoice_year": year,
                "client_name": f"{company} SRL",
                "amount": float(amount),
                "date": str(date(year, self.rng.randint(1, 12), self.rng.randint(1, 28))),
            }

            documents.append({"text": text, "metadata": metadata})

        return documents


# Global generator instance with fixed seed for reproducibility
_default_generator = DataGenerator(seed=42)


# Convenience functions
def generate_clients(count: int = 100, seed: int = 42) -> list[Cliente]:
    """Generate test clients.

    Args:
        count: Number of clients
        seed: Random seed

    Returns:
        List of Cliente objects
    """
    gen = DataGenerator(seed=seed)
    return gen.generate_clients(count)


def generate_invoices(
    clienti: list[Cliente], count: int = 1000, year: int = 2025, seed: int = 42
) -> list[Fattura]:
    """Generate test invoices.

    Args:
        clienti: List of clients
        count: Number of invoices
        year: Invoice year
        seed: Random seed

    Returns:
        List of Fattura objects
    """
    gen = DataGenerator(seed=seed)
    return gen.generate_invoices(clienti, count, year)


def generate_payments(
    fatture: list[Fattura], payment_rate: float = 0.7, seed: int = 42
) -> list[Pagamento]:
    """Generate test payments.

    Args:
        fatture: List of invoices
        payment_rate: Payment probability
        seed: Random seed

    Returns:
        List of Pagamento objects
    """
    gen = DataGenerator(seed=seed)
    return gen.generate_payments(fatture, payment_rate)


def generate_rag_documents(count: int = 100, seed: int = 42) -> list[dict[str, Any]]:
    """Generate test documents for RAG.

    Args:
        count: Number of documents
        seed: Random seed

    Returns:
        List of document dicts
    """
    gen = DataGenerator(seed=seed)
    return gen.generate_documents_for_rag(count)
