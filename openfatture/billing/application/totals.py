"""Invoice and quote amounts with FatturaPA rounding.

This module is the single source of every amount that appears on a document:
stored totals, the XML (``DatiRiepilogo``, ``ImportoTotaleDocumento``,
``ImportoPagamento``, ``DatiBollo``) and the PDF use the same functions, so
they always agree.

- Amounts are rounded half-up to the cent.
- VAT is computed per rate and natura on the summed taxable amount, exactly
  like ``DatiRiepilogo``; social security contributions (``DatiCassaPrevidenziale``)
  are part of that summary at their own rate and natura.
- ``totale == imponibile + iva``.
- The stamp duty is due when the amounts outside VAT exceed EUR 77.47.
  Charging it to the customer is a separate ``N1`` line; it is never added
  to the total implicitly.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
BOLLO_AMOUNT = Decimal("2.00")
BOLLO_THRESHOLD = Decimal("77.47")

# Natura codes of amounts outside VAT that make the stamp duty due:
# excluded (N1), not subject (N2.x) and exempt (N4) operations.
_BOLLO_NATURE_PREFIXES = ("N1", "N2", "N4")
# Amounts excluded under art. 15 (e.g. expense refunds, the stamp duty itself)
# are not subject to social security contributions.
_EXCLUDED_FROM_CASSA = "N1"

NATURE = (
    "N1",
    "N2.1",
    "N2.2",
    "N3.1",
    "N3.2",
    "N3.3",
    "N3.4",
    "N3.5",
    "N3.6",
    "N4",
    "N5",
    "N6.1",
    "N6.2",
    "N6.3",
    "N6.4",
    "N6.5",
    "N6.6",
    "N6.7",
    "N6.8",
    "N6.9",
    "N7",
)

# Default for a zero-rate line of a cedente in the forfettario regime.
FORFETTARIO_NATURA = "N2.2"

VatKey = tuple[Decimal, str | None]


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


class Contribution(Protocol):
    al_cassa: Decimal
    importo_contributo_cassa: Decimal
    imponibile_cassa: Decimal | None
    aliquota_iva: Decimal
    natura: str | None


class Document(Protocol):
    imponibile: Decimal
    iva: Decimal
    totale: Decimal


def check_vat(aliquota_iva: Decimal, natura: str | None) -> str | None:
    """Return an error when rate and natura are inconsistent, else ``None``.

    FatturaPA requires a natura for a zero rate and forbids it otherwise.
    """
    if natura is not None and natura not in NATURE:
        return f"Unknown natura {natura!r}; expected one of {', '.join(NATURE)}"
    if aliquota_iva == 0 and natura is None:
        return "A 0% VAT rate requires a natura (e.g. N2.2 for the forfettario regime)"
    if aliquota_iva != 0 and natura is not None:
        return f"Natura {natura} is only allowed with a 0% VAT rate"
    return None


def default_vat(regime_fiscale: str | None) -> tuple[Decimal, str | None]:
    """Default rate and natura for a new line of the configured cedente."""
    if regime_fiscale == "RF19":
        return Decimal("0"), FORFETTARIO_NATURA
    return Decimal("22"), None


def resolve_vat(
    aliquota_iva: Decimal | float | str | None,
    natura: str | None,
    regime_fiscale: str | None,
) -> tuple[Decimal, str | None]:
    """Rate and natura of a new or edited line, with the cedente's defaults.

    A missing rate takes the regime default; a zero rate without natura takes
    ``N2.2`` in the forfettario regime. Raises ``ValueError`` when the result
    is not a valid FatturaPA combination.
    """
    default_rate, default_natura = default_vat(regime_fiscale)
    rate = default_rate if aliquota_iva is None else Decimal(str(aliquota_iva))
    natura = natura or None
    if natura is None and rate == 0 and regime_fiscale == "RF19":
        natura = default_natura
    error = check_vat(rate, natura)
    if error:
        raise ValueError(error)
    return rate, natura


def _natura(item: object) -> str | None:
    value = getattr(item, "natura", None)
    return value if isinstance(value, str) and value else None


def price_line(line: Line) -> None:
    """Set a line's taxable amount, VAT and total from quantity, price and rate."""
    line.imponibile = cents(line.quantita * line.prezzo_unitario)
    line.iva = cents(line.imponibile * line.aliquota_iva / Decimal("100"))
    line.totale = line.imponibile + line.iva


def price_contribution(contribution: Contribution, lines: Iterable[Line]) -> None:
    """Set the contribution base (lines not excluded under art. 15) and amount."""
    base = sum(
        (line.imponibile for line in lines if _natura(line) != _EXCLUDED_FROM_CASSA),
        ZERO,
    )
    contribution.imponibile_cassa = cents(base)
    contribution.importo_contributo_cassa = cents(base * contribution.al_cassa / Decimal("100"))


def vat_summary(
    lines: Iterable[Line], contributions: Iterable[Contribution] = ()
) -> dict[VatKey, tuple[Decimal, Decimal]]:
    """``(aliquota, natura) -> (imponibile, imposta)`` as in ``DatiRiepilogo``.

    Ordered by rate, then natura.
    """
    taxable: dict[VatKey, Decimal] = defaultdict(lambda: ZERO)
    for line in lines:
        taxable[(Decimal(line.aliquota_iva), _natura(line))] += line.imponibile
    for contribution in contributions:
        key = (Decimal(contribution.aliquota_iva), _natura(contribution))
        taxable[key] += contribution.importo_contributo_cassa
    ordered = sorted(taxable.items(), key=lambda item: (item[0][0], item[0][1] or ""))
    return {
        key: (cents(amount), cents(amount * key[0] / Decimal("100"))) for key, amount in ordered
    }


def bollo_due(lines: Iterable[Line], contributions: Iterable[Contribution] = ()) -> Decimal:
    """Stamp duty owed on the document: EUR 2.00 above EUR 77.47 outside VAT."""
    outside_vat = sum(
        (
            imponibile
            for (_, natura), (imponibile, _) in vat_summary(lines, contributions).items()
            if natura is not None and natura.startswith(_BOLLO_NATURE_PREFIXES)
        ),
        ZERO,
    )
    return BOLLO_AMOUNT if outside_vat > BOLLO_THRESHOLD else ZERO


def recompute_totals(
    document: Document,
    lines: Iterable[Line],
    contributions: Sequence[Contribution] = (),
) -> None:
    """Reprice lines and contributions and set the document totals.

    Documents with an ``importo_bollo`` attribute (invoices) also get the
    stamp duty owed.
    """
    priced = list(lines)
    for line in priced:
        price_line(line)
    for contribution in contributions:
        price_contribution(contribution, priced)
    summary = vat_summary(priced, contributions)
    document.imponibile = sum((imponibile for imponibile, _ in summary.values()), ZERO)
    document.iva = sum((imposta for _, imposta in summary.values()), ZERO)
    document.totale = document.imponibile + document.iva
    if hasattr(document, "importo_bollo"):
        document.importo_bollo = bollo_due(priced, contributions)


def amount_due(totale: Decimal, ritenuta_acconto: Decimal | None) -> Decimal:
    """What the customer pays: the document total less the withholding tax."""
    return cents(totale - (ritenuta_acconto or ZERO))


class Invoice(Document, Protocol):
    importo_bollo: Decimal

    @property
    def righe(self) -> Sequence[Line]: ...

    @property
    def cassa_previdenziale(self) -> Sequence[Contribution]: ...


def recompute_invoice(invoice: Invoice) -> None:
    """Recompute an invoice from its lines and social security contributions."""
    recompute_totals(invoice, invoice.righe, invoice.cassa_previdenziale)
