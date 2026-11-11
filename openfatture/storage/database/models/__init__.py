"""SQLAlchemy models for OpenFatture, grouped by bounded context.

Importing this package registers every storage table on ``Base.metadata``.
"""

from .billing import (
    Cliente,
    DatiCassaPrevidenziale,
    Fattura,
    Prodotto,
    RegimeFiscale,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from .events import EventLog
from .payments import (
    CollectionEntry,
    CollectionOperation,
    CollectionReceipt,
    CollectionStatement,
    Pagamento,
    StatoPagamento,
)
from .quotes import Preventivo, RigaPreventivo, StatoPreventivo
from .sdi import LogSDI, SDIInvoiceIdentity, SDINotificationRecord, SDISubmissionAttempt

__all__ = [
    "Cliente",
    "CollectionEntry",
    "CollectionOperation",
    "CollectionReceipt",
    "CollectionStatement",
    "DatiCassaPrevidenziale",
    "EventLog",
    "Fattura",
    "LogSDI",
    "Pagamento",
    "Preventivo",
    "Prodotto",
    "RegimeFiscale",
    "RigaFattura",
    "RigaPreventivo",
    "SDIInvoiceIdentity",
    "SDINotificationRecord",
    "SDISubmissionAttempt",
    "StatoFattura",
    "StatoPagamento",
    "StatoPreventivo",
    "TipoDocumento",
]
