"""Progressive per-year document numbering for invoices and quotes."""

from sqlalchemy.orm import Session

from openfatture.storage.database.models import Fattura, Preventivo


def next_numero(db: Session, model: type[Fattura] | type[Preventivo], anno: int) -> str:
    """Return the next progressive number for ``anno``.

    ``numero`` is stored as text, so ordering in SQL is lexicographic ("9" > "10").
    The maximum is computed numerically over purely numeric values; custom
    non-numeric numbers do not take part in the sequence.
    """
    numeri = db.query(model.numero).filter(model.anno == anno).all()
    massimo = max((int(n) for (n,) in numeri if n and n.isdigit()), default=0)
    return str(massimo + 1)
