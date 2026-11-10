"""Social security contribution (``DatiCassaPrevidenziale``) of an invoice.

One contribution per invoice: the rate applies to the lines not excluded under
art. 15, and the amount is recomputed with the invoice totals.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from openfatture.billing.application.totals import recompute_invoice, resolve_vat
from openfatture.platform.config import get_settings
from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import DatiCassaPrevidenziale, Fattura, StatoFattura
from openfatture.storage.session import db_session

logger = get_logger(__name__)

_TIPO_CASSA = re.compile(r"TC(0[1-9]|1[0-9]|2[0-2])")


def set_cassa_previdenziale(
    fattura_id: int,
    tipo_cassa: str | None,
    al_cassa: float = 0,
    aliquota_iva: float | None = None,
    natura: str | None = None,
) -> dict[str, Any]:
    """Set or remove the invoice's social security contribution.

    Args:
        fattura_id: Invoice ID (BOZZA or DA_INVIARE)
        tipo_cassa: TC01..TC22 (TC22 = INPS gestione separata); ``None`` removes it
        al_cassa: Contribution rate in percent (e.g. 4)
        aliquota_iva: VAT rate on the contribution; cedente default when omitted
        natura: VAT natura of the contribution when the rate is 0%
    """
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    if tipo_cassa is not None and not _TIPO_CASSA.fullmatch(tipo_cassa):
        return {"error": f"Unknown tipo_cassa {tipo_cassa!r}; expected TC01..TC22"}
    rate = Decimal(str(al_cassa))
    if tipo_cassa is not None and not Decimal("0") < rate <= Decimal("100"):
        return {"error": "al_cassa must be a percentage greater than 0"}
    try:
        vat_rate, vat_natura = resolve_vat(
            aliquota_iva, natura, get_settings().cedente_regime_fiscale
        )
    except ValueError as e:
        return {"error": str(e)}

    with db_session() as db:
        try:
            fattura = db.get(Fattura, fattura_id)
            if fattura is None:
                return {"error": f"Invoice {fattura_id} not found"}
            if fattura.stato not in (StatoFattura.BOZZA, StatoFattura.DA_INVIARE):
                return {
                    "error": f"Cannot modify invoice in status '{fattura.stato.value}'. "
                    "Only BOZZA or DA_INVIARE can be edited."
                }
            fattura.cassa_previdenziale.clear()
            if tipo_cassa is not None:
                fattura.cassa_previdenziale.append(
                    DatiCassaPrevidenziale(
                        tipo_cassa=tipo_cassa,
                        al_cassa=rate,
                        importo_contributo_cassa=Decimal("0"),
                        aliquota_iva=vat_rate,
                        natura=vat_natura,
                    )
                )
            recompute_invoice(fattura)
            db.commit()
            contribution = fattura.cassa_previdenziale[0] if fattura.cassa_previdenziale else None
            logger.info("cassa_previdenziale_set", fattura_id=fattura_id, tipo_cassa=tipo_cassa)
            return {
                "success": True,
                "fattura_id": fattura_id,
                "tipo_cassa": tipo_cassa,
                "importo_contributo_cassa": float(contribution.importo_contributo_cassa)
                if contribution
                else 0.0,
                "invoice_totale": float(fattura.totale),
                "importo_bollo": float(fattura.importo_bollo),
            }
        except Exception as e:
            db.rollback()
            logger.error("set_cassa_previdenziale_failed", error=str(e))
            return {"error": describe_error(e)}
