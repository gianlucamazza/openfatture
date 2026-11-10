"""Invoice and quote totals with FatturaPA rounding.

Amounts are rounded half-up to the cent. VAT is computed per rate and
natura on the summed taxable amount, exactly like the ``DatiRiepilogo``
section of the XML, so stored totals, PDF and XML always agree and
``totale == imponibile + iva``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

CENT = Decimal("0.01")


def cents(value: Decimal) -> Decimal:
    """Round half-up to two decimals."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


class Line(Protocol):
    quantita: Decimal
    prezzo_unitario: Decimal
    aliquota_iva: Decimal
    imponibile: Decimal
    iva: Decimal
    totale: Decimal


class Document(Protocol):
    imponibile: Decimal
    iva: Decimal
    totale: Decimal


def price_line(line: Line) -> None:
    """Set a line's taxable amount, VAT and total from quantity, price and rate."""
    line.imponibile = cents(line.quantita * line.prezzo_unitario)
    line.iva = cents(line.imponibile * line.aliquota_iva / Decimal("100"))
    line.totale = line.imponibile + line.iva


def vat_summary(lines: Iterable[Line]) -> dict[tuple[Decimal, str | None], tuple[Decimal, Decimal]]:
    """``(aliquota, natura) -> (imponibile, imposta)`` as in ``DatiRiepilogo``."""
    taxable: dict[tuple[Decimal, str | None], Decimal] = defaultdict(lambda: Decimal("0"))
    for line in lines:
        taxable[(Decimal(line.aliquota_iva), getattr(line, "natura", None))] += line.imponibile
    return {
        key: (cents(amount), cents(amount * key[0] / Decimal("100")))
        for key, amount in taxable.items()
    }


def recompute_totals(document: Document, lines: Iterable[Line]) -> None:
    """Reprice every line and set the document totals from the VAT summary."""
    priced = list(lines)
    for line in priced:
        price_line(line)
    summary = vat_summary(priced)
    document.imponibile = sum((imponibile for imponibile, _ in summary.values()), Decimal("0.00"))
    document.iva = sum((imposta for _, imposta in summary.values()), Decimal("0.00"))
    document.totale = document.imponibile + document.iva
