"""Single database seam for invoice tools.

All invoice tool submodules call ``_db.get_session()`` so that tests can
patch the database session at a single point:
``openfatture.ai.tools.invoice_tools._db.get_session``.
"""

from openfatture.storage.database.base import get_session

__all__ = ["get_session"]
