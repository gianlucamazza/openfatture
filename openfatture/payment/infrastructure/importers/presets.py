"""Pre-configured bank import presets for Italian banks.

Provides ready-to-use CSVConfig configurations for major Italian banks.
"""

from .csv_importer import CSVConfig

# ============================================================================
# ITALIAN BANK PRESETS
# ============================================================================

INTESA_SANPAOLO = CSVConfig(
    delimiter=";",
    encoding="ISO-8859-1",  # Windows Latin-1
    skip_rows=0,  # DictReader handles header automatically
    field_mapping={
        "date": "Data operazione",
        "amount": "Importo",
        "description": "Descrizione",
        "reference": "Causale",
        "counterparty": "Ordinante/Beneficiario",
    },
    date_format="%d/%m/%Y",  # Italian format: 31/12/2024
    decimal_separator=",",  # European: 1.234,56
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Intesa Sanpaolo CSV export format.

Typical column structure:
- Data operazione: Transaction date (DD/MM/YYYY)
- Data valuta: Value date
- Importo: Amount (1.234,56)
- Descrizione: Description
- Causale: Reference/Reason
- Ordinante/Beneficiario: Counterparty name

Example CSV header:
    Data operazione;Data valuta;Importo;Descrizione;Causale;Ordinante/Beneficiario
"""

UNICREDIT = CSVConfig(
    delimiter=";",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Data",
        "amount": "Importo",
        "description": "Causale",
        "reference": "Riferimento",
        "counterparty": "Beneficiario",
    },
    date_format="%Y-%m-%d",  # ISO format: 2025-01-15
    decimal_separator=",",
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""UniCredit CSV export format.

Typical column structure:
- Data: Transaction date
- Importo: Amount
- Causale: Description/Reason
- Riferimento: Reference
- Beneficiario: Beneficiary

Example CSV header:
    Data;Importo;Causale;Riferimento;Beneficiario
"""

BANCO_BPM = CSVConfig(
    delimiter=";",
    encoding="ISO-8859-1",
    skip_rows=0,
    field_mapping={
        "date": "Data",
        "amount": "Importo",
        "description": "Descrizione",
        "reference": "Causale",
        "counterparty": "Controparte",
    },
    date_format="%d/%m/%Y",
    decimal_separator=",",
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Banco BPM (ex-Banco Popolare) CSV export format.

Typical column structure:
- Data: Transaction date
- Importo: Amount
- Descrizione: Description
- Causale: Reference/Reason
- Controparte: Counterparty

Example CSV header:
    Data;Importo;Descrizione;Causale;Controparte
"""

FINECO = CSVConfig(
    delimiter=";",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Data operazione",
        "amount": "Importo",
        "description": "Descrizione completa",
        "reference": "Causale",
        "counterparty": "Beneficiario",
    },
    date_format="%d/%m/%Y",
    decimal_separator=",",
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""FinecoBank CSV export format.

Typical column structure:
- Data operazione: Transaction date
- Importo: Amount
- Descrizione completa: Full description
- Causale: Reason
- Beneficiario: Beneficiary

Example CSV header:
    Data operazione;Importo;Descrizione completa;Causale;Beneficiario
"""

BANCA_SELLA = CSVConfig(
    delimiter=";",
    encoding="ISO-8859-1",
    skip_rows=0,
    field_mapping={
        "date": "Data",
        "amount": "Importo",
        "description": "Descrizione",
        "reference": "Causale",
    },
    date_format="%d/%m/%Y",
    decimal_separator=",",
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Banca Sella CSV export format.

Typical column structure:
- Data: Transaction date
- Importo: Amount
- Descrizione: Description
- Causale: Reference

Example CSV header:
    Data;Importo;Descrizione;Causale
"""

POSTE_ITALIANE = CSVConfig(
    delimiter=";",
    encoding="ISO-8859-1",
    skip_rows=0,
    field_mapping={
        "date": "Data",
        "amount": "Importo",
        "description": "Descrizione",
        "reference": "Causale",
        "counterparty": "Ordinante/Beneficiario",
    },
    date_format="%d/%m/%Y",
    decimal_separator=",",
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Poste Italiane (BancoPosta) CSV export format.

Typical column structure:
- Data: Transaction date
- Importo: Amount
- Descrizione: Description
- Causale: Reference
- Ordinante/Beneficiario: Payer/Payee

Example CSV header:
    Data;Importo;Descrizione;Causale;Ordinante/Beneficiario
"""

# ============================================================================
# INTERNATIONAL BANK PRESETS
# ============================================================================

REVOLUT = CSVConfig(
    delimiter=",",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Completed Date",
        "amount": "Amount",
        "description": "Description",
        "reference": "Reference",
        "counterparty": "Counterparty",
    },
    date_format="%Y-%m-%d",  # ISO format: 2024-12-31
    decimal_separator=".",  # US/UK format
    thousands_separator=",",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Revolut CSV export format.

Typical column structure:
- Completed Date: Transaction date (ISO format)
- Amount: Amount (US format: 1,234.56)
- Description: Description
- Reference: Reference
- Counterparty: Counterparty name

Example CSV header:
    Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
"""

N26 = CSVConfig(
    delimiter=",",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Date",
        "amount": "Amount (EUR)",
        "description": "Payment reference",
        "reference": "Transaction ID",
        "counterparty": "Payee",
    },
    date_format="%Y-%m-%d",
    decimal_separator=".",
    thousands_separator=",",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""N26 Bank CSV export format.

Typical column structure:
- Date: Transaction date (ISO format)
- Amount (EUR): Amount
- Payment reference: Description
- Transaction ID: Unique reference
- Payee: Counterparty name

Example CSV header:
    Date,Payee,Account number,Transaction type,Payment reference,Amount (EUR),Amount (Foreign Currency),Type Foreign Currency,Exchange Rate
"""

WISE = CSVConfig(
    delimiter=",",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Date",
        "amount": "Amount",
        "description": "Description",
        "reference": "TransferWise ID",
        "counterparty": "Merchant",
    },
    date_format="%d-%m-%Y",  # EU format with dashes
    decimal_separator=".",
    thousands_separator=",",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Wise (TransferWise) CSV export format.

Typical column structure:
- Date: Transaction date
- Amount: Amount in account currency
- Description: Transaction description
- TransferWise ID: Unique reference
- Merchant: Counterparty

Example CSV header:
    TransferWise ID,Date,Amount,Currency,Description,Payment Reference,Running Balance,Exchange From,Exchange To,Exchange Rate,Payer Name,Payee Name,Payee Account Number,Merchant
"""

# ============================================================================
# GENERIC PRESETS
# ============================================================================

GENERIC_EU = CSVConfig(
    delimiter=";",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Date",
        "amount": "Amount",
        "description": "Description",
        "reference": "Reference",
    },
    date_format="%d/%m/%Y",
    decimal_separator=",",
    thousands_separator=".",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Generic European bank CSV format.

Standard European format with:
- Semicolon delimiter
- DD/MM/YYYY dates
- Comma decimal separator (1.234,56)
"""

GENERIC_US = CSVConfig(
    delimiter=",",
    encoding="UTF-8",
    skip_rows=0,
    field_mapping={
        "date": "Date",
        "amount": "Amount",
        "description": "Description",
        "reference": "Reference",
    },
    date_format="%m/%d/%Y",  # US format: 12/31/2024
    decimal_separator=".",
    thousands_separator=",",
    optional_fields=["reference", "counterparty", "counterparty_iban"],
)
"""Generic US bank CSV format.

Standard US format with:
- Comma delimiter
- MM/DD/YYYY dates
- Period decimal separator (1,234.56)
"""

# ============================================================================
# PRESET REGISTRY
# ============================================================================

BANK_PRESETS = {
    # Italian banks
    "intesa": INTESA_SANPAOLO,
    "intesa_sanpaolo": INTESA_SANPAOLO,
    "unicredit": UNICREDIT,
    "banco_bpm": BANCO_BPM,
    "bpm": BANCO_BPM,
    "fineco": FINECO,
    "finecobank": FINECO,
    "sella": BANCA_SELLA,
    "banca_sella": BANCA_SELLA,
    "poste": POSTE_ITALIANE,
    "poste_italiane": POSTE_ITALIANE,
    "bancoposta": POSTE_ITALIANE,
    # International banks
    "revolut": REVOLUT,
    "n26": N26,
    "wise": WISE,
    "transferwise": WISE,
    # Generic
    "generic_eu": GENERIC_EU,
    "generic_us": GENERIC_US,
}
"""Registry of all available bank presets.

Usage:
    >>> from openfatture.payment.infrastructure.importers.presets import BANK_PRESETS
    >>> config = BANK_PRESETS["intesa"]
    >>> importer = CSVImporter(file_path, config)

Available presets:
    Italian banks:
    - intesa, intesa_sanpaolo: Intesa Sanpaolo
    - unicredit: UniCredit
    - banco_bpm, bpm: Banco BPM
    - fineco, finecobank: FinecoBank
    - sella, banca_sella: Banca Sella
    - poste, poste_italiane, bancoposta: Poste Italiane

    International:
    - revolut: Revolut
    - n26: N26 Bank
    - wise, transferwise: Wise (TransferWise)

    Generic:
    - generic_eu: Generic European format
    - generic_us: Generic US format
"""


def get_preset(name: str) -> CSVConfig:
    """Get bank preset configuration by name.

    Args:
        name: Preset name (case-insensitive)

    Returns:
        CSVConfig for the specified bank

    Raises:
        KeyError: If preset name not found

    Example:
        >>> config = get_preset("intesa")
        >>> config = get_preset("REVOLUT")
    """
    name_lower = name.lower()
    if name_lower not in BANK_PRESETS:
        available = ", ".join(sorted(set(BANK_PRESETS.keys())))
        raise KeyError(
            f"Unknown bank preset: '{name}'. Available presets: {available}"
        )
    return BANK_PRESETS[name_lower]


def list_presets() -> list[str]:
    """Get list of all available preset names.

    Returns:
        Sorted list of preset names

    Example:
        >>> presets = list_presets()
        >>> print(f"Available banks: {', '.join(presets)}")
    """
    # Return unique preset names (some banks have aliases)
    unique_names = set(BANK_PRESETS.keys())
    return sorted(unique_names)
