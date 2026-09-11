"""Bank statement importers with Factory pattern.

Supports multiple formats:
- CSV: Configurable field mapping with bank presets
- OFX: Open Financial Exchange (via ofxparse)
- QIF: Quicken Interchange Format (legacy)

Usage:
    >>> from openfatture.payment.infrastructure.importers import ImporterFactory
    >>> factory = ImporterFactory()
    >>>
    >>> # Auto-detect format
    >>> importer = factory.create_from_file("statement.csv")
    >>> result = importer.import_transactions(account)
    >>> print(f"Imported {result.success_count} transactions")
    >>>
    >>> # Use bank preset
    >>> importer = factory.create_from_file("statement.csv", bank_preset="intesa")
    >>> result = importer.import_transactions(account)
    >>>
    >>> # Custom CSV configuration
    >>> from openfatture.payment.infrastructure.importers import CSVConfig
    >>> config = CSVConfig(delimiter=";", date_format="%d/%m/%Y")
    >>> importer = factory.create_from_file("statement.csv", config=config)
"""

__all__ = [
    # Base classes
    "BaseImporter",
    "ImportResult",
    "FileFormat",
    # Factory
    "ImporterFactory",
    # Importers
    "CSVImporter",
    "CSVConfig",
    "OFXImporter",
    "QIFImporter",
    # Presets
    "BANK_PRESETS",
    "get_preset",
    "list_presets",
]

from .base import BaseImporter, FileFormat, ImportResult
from .csv_importer import CSVConfig, CSVImporter
from .factory import ImporterFactory
from .ofx_importer import OFXImporter
from .presets import BANK_PRESETS, get_preset, list_presets
from .qif_importer import QIFImporter
