"""Progressive per-year invoice numbering."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from openfatture.billing.application.invoice_commands import create_invoice
from openfatture.billing.application.numbering import next_numero
from openfatture.storage.database.models import Fattura, Preventivo


def _fattura(cliente_id: int, numero: str, anno: int = 2026) -> Fattura:
    return Fattura(
        numero=numero,
        anno=anno,
        data_emissione=date(anno, 1, 1),
        cliente_id=cliente_id,
        imponibile=Decimal("0"),
        iva=Decimal("0"),
        totale=Decimal("0"),
    )


def test_next_numero_is_numeric_not_lexicographic(db_session, sample_cliente):
    db_session.add_all(_fattura(sample_cliente.id, str(n)) for n in range(1, 11))
    db_session.commit()

    assert next_numero(db_session, Fattura, 2026) == "11"


def test_next_numero_ignores_custom_numbers_and_other_years(db_session, sample_cliente):
    db_session.add_all(
        [
            _fattura(sample_cliente.id, "DR0910"),
            _fattura(sample_cliente.id, "7"),
            _fattura(sample_cliente.id, "99", anno=2025),
        ]
    )
    db_session.commit()

    assert next_numero(db_session, Fattura, 2026) == "8"
    assert next_numero(db_session, Fattura, 2027) == "1"
    assert next_numero(db_session, Preventivo, 2026) == "1"


def test_numero_is_unique_per_year(db_session, sample_cliente):
    db_session.add_all([_fattura(sample_cliente.id, "1"), _fattura(sample_cliente.id, "1", 2025)])
    db_session.commit()

    db_session.add(_fattura(sample_cliente.id, "1"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_invoice_continues_after_ten(runtime_session, seed_cliente):
    runtime_session.add_all(_fattura(seed_cliente.id, str(n)) for n in range(1, 11))
    runtime_session.commit()

    result = create_invoice(cliente_id=seed_cliente.id, anno=2026)

    assert result.get("numero") == "11", result
