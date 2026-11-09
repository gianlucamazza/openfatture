"""Historical documents must not be presented as unissued drafts."""

from openfatture.billing.application.invoice_queries import get_invoice_stats
from openfatture.storage.database.models import Fattura


def test_historical_stats_separate_technical_status(runtime_db, seed_fattura):
    with runtime_db() as session:
        invoice = session.get(Fattura, seed_fattura.id)
        invoice.issued_elsewhere = True
        session.commit()
        result = get_invoice_stats(seed_fattura.anno, session=session)
    assert result["per_stato"]["bozza"] == 1
    assert result["per_documento"]["bozza"] == 0
    assert result["per_documento"]["storica"] == 1
    assert result["fatture_storiche"] == 1
    assert result["per_stato_incasso"] == {"no_payment_record": 1}
    assert result["residuo_totale"] == float(seed_fattura.totale)
    assert "non è verificato" in result["avvertenza_stato"]
