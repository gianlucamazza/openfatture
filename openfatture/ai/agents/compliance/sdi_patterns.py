"""SDI rejection patterns database.

This module contains a comprehensive database of known SDI (Sistema di Interscambio)
rejection patterns, error codes, and common validation failures based on:
- Official SDI documentation
- Historical rejection data
- Common merchant/professional mistakes

Each pattern includes:
- Error code from SDI
- Pattern description
- Detection logic
- Fix suggestions
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from re import Pattern

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class SDIErrorCode(Enum):
    """SDI rejection error codes.

    Based on official SDI technical specifications.
    """

    # File format errors (00xxx)
    E00001 = "00001"  # File non conforme allo schema XSD
    E00002 = "00002"  # File non conforme al formato
    E00003 = "00003"  # File vuoto

    # Signature errors (00xxx)
    E00101 = "00101"  # Firma non valida
    E00102 = "00102"  # Certificato scaduto
    E00103 = "00103"  # Firma assente quando richiesta

    # Transmission data errors (00xxx)
    E00200 = "00200"  # IdTrasmittente non valido
    E00201 = "00201"  # ProgressivoInvio duplicato
    E00202 = "00202"  # FormatoTrasmissione non valido

    # Invoice header errors (00xxx)
    E00300 = "00300"  # TipoDocumento non valido
    E00301 = "00301"  # Divisa non valida
    E00302 = "00302"  # Data fattura futura
    E00303 = "00303"  # Numero fattura duplicato

    # Supplier errors (00xxx)
    E00400 = "00400"  # P.IVA cedente/prestatore non valida
    E00401 = "00401"  # Indirizzo cedente non valido
    E00402 = "00402"  # RegimeFiscale non valido

    # Customer errors (00xxx)
    E00500 = "00500"  # P.IVA/CF cessionario non valido
    E00501 = "00501"  # Indirizzo cessionario non valido
    E00502 = "00502"  # CodiceDestinatario non valido
    E00503 = "00503"  # Nessun canale di ricezione specificato

    # Invoice lines errors (00xxx)
    E00600 = "00600"  # Descrizione riga mancante
    E00601 = "00601"  # Quantità non valida
    E00602 = "00602"  # Prezzo unitario non valido
    E00603 = "00603"  # Aliquota IVA non valida

    # Totals errors (00xxx)
    E00700 = "00700"  # Totale documento non corretto
    E00701 = "00701"  # Imponibile non corretto
    E00702 = "00702"  # IVA non corretta
    E00703 = "00703"  # Arrotondamento non valido


@dataclass
class SDIRejectionPattern:
    """Pattern for detecting potential SDI rejection.

    Attributes:
        error_code: SDI error code
        pattern_name: Human-readable pattern name
        description: Detailed description of the issue
        regex_patterns: List of regex patterns to match
        field_checks: List of field names to validate
        severity: Issue severity (error/warning)
        fix_suggestion: How to fix the issue
        reference: Link or reference to documentation
    """

    error_code: str
    pattern_name: str
    description: str
    regex_patterns: list[str] = field(default_factory=list)
    field_checks: list[str] = field(default_factory=list)
    severity: str = "error"
    fix_suggestion: str = ""
    reference: str = ""
    compiled_patterns: list[Pattern] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Compile regex patterns."""
        self.compiled_patterns: list[Pattern] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.regex_patterns
        ]


class SDIPatternDatabase:
    """Database of SDI rejection patterns.

    Contains known patterns from:
    - Official SDI error codes documentation
    - Historical rejection analysis
    - Common merchant mistakes
    """

    def __init__(self):
        """Initialize pattern database."""
        self.patterns = self._load_patterns()
        logger.info("sdi_pattern_database_initialized", patterns_count=len(self.patterns))

    def _load_patterns(self) -> list[SDIRejectionPattern]:
        """Load all SDI rejection patterns."""

        return [
            # === Partita IVA / Codice Fiscale Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00500.value,
                pattern_name="P.IVA Cliente Non Valida",
                description="Partita IVA del cliente non conforme al formato italiano",
                regex_patterns=[
                    r"^[0-9]{10}$",  # Too short (10 digits)
                    r"^[0-9]{12,}$",  # Too long (>11 digits)
                    r"^[0-9A-Z]{11}$",  # Contains letters
                ],
                field_checks=["cliente.partita_iva"],
                severity="error",
                fix_suggestion="La P.IVA italiana deve essere composta da esattamente 11 cifre numeriche",
                reference="Art. 35 DPR 633/72",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00500.value,
                pattern_name="CF Cliente Non Valido",
                description="Codice Fiscale del cliente non conforme",
                regex_patterns=[
                    r"^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{2}[A-Z]$",  # Wrong format
                ],
                field_checks=["cliente.codice_fiscale"],
                severity="error",
                fix_suggestion="Il CF deve essere nel formato standard a 16 caratteri",
                reference="DPR 605/73",
            ),
            # === CodiceDestinatario / PEC Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00502.value,
                pattern_name="Codice Destinatario Mancante",
                description="Né Codice Destinatario né PEC specificati",
                field_checks=["cliente.codice_destinatario", "cliente.pec"],
                severity="error",
                fix_suggestion="Specificare almeno uno tra Codice Destinatario (7 caratteri) o PEC",
                reference="Specifiche SDI v1.6.2",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00502.value,
                pattern_name="Codice Destinatario Errato",
                description="Codice Destinatario non valido (deve essere 7 caratteri)",
                regex_patterns=[
                    r"^[A-Z0-9]{6}$",  # Too short
                    r"^[A-Z0-9]{8,}$",  # Too long
                    r"^[a-z0-9]{7}$",  # Lowercase (not allowed)
                ],
                field_checks=["cliente.codice_destinatario"],
                severity="error",
                fix_suggestion="Il Codice Destinatario deve essere esattamente 7 caratteri alfanumerici maiuscoli",
                reference="Specifiche SDI v1.6.2 - Campo 1.1.6",
            ),
            # === Address Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00501.value,
                pattern_name="Indirizzo Incompleto",
                description="Indirizzo del cliente incompleto (manca via, cap, comune o provincia)",
                field_checks=[
                    "cliente.indirizzo",
                    "cliente.cap",
                    "cliente.comune",
                    "cliente.provincia",
                ],
                severity="error",
                fix_suggestion="Per clienti italiani sono obbligatori: Indirizzo, CAP, Comune, Provincia",
                reference="FatturaPA v1.2.2 - Campo 1.4.2",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00501.value,
                pattern_name="CAP Non Valido",
                description="CAP non conforme (deve essere 5 cifre)",
                regex_patterns=[
                    r"^[0-9]{4}$",  # Too short
                    r"^[0-9]{6,}$",  # Too long
                    r"^[0-9]{2}-[0-9]{3}$",  # Wrong format (with dash)
                ],
                field_checks=["cliente.cap"],
                severity="error",
                fix_suggestion="Il CAP italiano deve essere 5 cifre (es. 00100, 20121)",
                reference="Codifiche CAP Poste Italiane",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00501.value,
                pattern_name="Provincia Non Valida",
                description="Sigla provincia non valida",
                regex_patterns=[
                    r"^[A-Z]{1}$",  # Too short (1 letter)
                    r"^[A-Z]{3,}$",  # Too long (>2 letters)
                    r"^[a-z]{2}$",  # Lowercase
                ],
                field_checks=["cliente.provincia"],
                severity="error",
                fix_suggestion="La sigla provincia deve essere 2 lettere maiuscole (es. RM, MI, NA)",
                reference="ISO 3166-2:IT",
            ),
            # === Invoice Number / Date Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00302.value,
                pattern_name="Data Fattura Futura",
                description="Data di emissione della fattura è nel futuro",
                field_checks=["data_emissione"],
                severity="error",
                fix_suggestion="La data di emissione non può essere successiva alla data odierna",
                reference="Validazione logica SDI",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00303.value,
                pattern_name="Numero Fattura Duplicato",
                description="Numero fattura già utilizzato per lo stesso anno",
                field_checks=["numero", "anno"],
                severity="error",
                fix_suggestion="Utilizzare un numero progressivo univoco per l'anno",
                reference="Art. 21 DPR 633/72",
            ),
            # === Invoice Lines Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00600.value,
                pattern_name="Descrizione Riga Mancante",
                description="Descrizione obbligatoria per ogni riga fattura",
                field_checks=["righe.descrizione"],
                severity="error",
                fix_suggestion="Inserire una descrizione dettagliata per ogni riga",
                reference="FatturaPA v1.2.2 - Campo 2.2.1.4",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00601.value,
                pattern_name="Quantità Zero o Negativa",
                description="Quantità deve essere maggiore di zero",
                field_checks=["righe.quantita"],
                severity="error",
                fix_suggestion="Inserire quantità > 0 (per note di credito usare TipoDocumento TD04)",
                reference="FatturaPA v1.2.2 - Campo 2.2.1.5",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00603.value,
                pattern_name="Aliquota IVA Non Valida",
                description="Aliquota IVA non presente nell'elenco ufficiale",
                field_checks=["righe.aliquota_iva"],
                severity="error",
                fix_suggestion="Aliquote valide: 0%, 4%, 5%, 10%, 22% (o Esente/Fuori Campo con Natura)",
                reference="DPR 633/72 - Tabella aliquote IVA",
            ),
            # === Totals Calculation Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00700.value,
                pattern_name="Totale Documento Errato",
                description="Totale fattura non corrisponde alla somma delle righe",
                field_checks=["totale", "imponibile", "iva"],
                severity="error",
                fix_suggestion="Ricalcolare: Totale = Somma Imponibili + Somma IVA - Ritenuta + Bollo",
                reference="FatturaPA v1.2.2 - Campo 2.4.2.6",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00701.value,
                pattern_name="Imponibile Non Corretto",
                description="Imponibile non corrisponde alla somma degli imponibili delle righe",
                field_checks=["imponibile"],
                severity="error",
                fix_suggestion="Verificare che Imponibile = Somma(Quantità × Prezzo Unitario) di tutte le righe",
                reference="FatturaPA v1.2.2 - Campo 2.2.2.5",
            ),
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00702.value,
                pattern_name="IVA Non Corretta",
                description="IVA calcolata erroneamente",
                field_checks=["iva"],
                severity="error",
                fix_suggestion="Verificare che IVA = Somma(Imponibile × Aliquota%) di tutte le righe",
                reference="FatturaPA v1.2.2 - Campo 2.2.2.6",
            ),
            # === Document Type Errors ===
            SDIRejectionPattern(
                error_code=SDIErrorCode.E00300.value,
                pattern_name="Tipo Documento Non Valido",
                description="TipoDocumento non conforme alle specifiche",
                field_checks=["tipo_documento"],
                severity="error",
                fix_suggestion="Usare codici validi: TD01-TD27 (es. TD01=Fattura, TD04=Nota Credito)",
                reference="FatturaPA v1.2.2 - Campo 1.1.1 (TipoDocumento)",
            ),
            # === Common Formatting Errors ===
            SDIRejectionPattern(
                error_code="COMMON_001",
                pattern_name="Caratteri Speciali in Descrizione",
                description="Caratteri non permessi in campi testuali XML",
                regex_patterns=[
                    r"[<>&]",  # XML special chars not escaped
                ],
                field_checks=["righe.descrizione", "note"],
                severity="error",
                fix_suggestion="Evitare caratteri < > & o usare escape XML (&lt; &gt; &amp;)",
                reference="Specifiche XML 1.0",
            ),
            SDIRejectionPattern(
                error_code="COMMON_002",
                pattern_name="Campi Troppo Lunghi",
                description="Lunghezza campo supera il massimo consentito",
                field_checks=["righe.descrizione"],  # Max 1000 chars
                severity="error",
                fix_suggestion="Descrizione riga: max 1000 caratteri",
                reference="FatturaPA v1.2.2 - Limiti campi",
            ),
            # === Missing Required Fields ===
            SDIRejectionPattern(
                error_code="REQUIRED_001",
                pattern_name="Modalità Pagamento Assente",
                description="Modalità di pagamento obbligatoria",
                field_checks=["pagamenti.modalita"],
                severity="warning",
                fix_suggestion="Specificare modalità di pagamento (es. MP05=Bonifico, MP01=Contanti)",
                reference="FatturaPA v1.2.2 - Campo 2.4.2.2",
            ),
            SDIRejectionPattern(
                error_code="REQUIRED_002",
                pattern_name="Nessuna Riga Fattura",
                description="Fattura senza righe di dettaglio",
                field_checks=["righe"],
                severity="error",
                fix_suggestion="Aggiungere almeno una riga di dettaglio",
                reference="FatturaPA v1.2.2 - Campo 2.2.1 (obbligatorio)",
            ),
            # === Business Logic Errors ===
            SDIRejectionPattern(
                error_code="LOGIC_001",
                pattern_name="Ritenuta Superiore all'Imponibile",
                description="Importo ritenuta d'acconto superiore all'imponibile",
                field_checks=["ritenuta_acconto", "imponibile"],
                severity="error",
                fix_suggestion="La ritenuta non può essere > imponibile (tipicamente 20% dell'imponibile)",
                reference="Normativa ritenuta d'acconto",
            ),
            SDIRejectionPattern(
                error_code="LOGIC_002",
                pattern_name="Bollo su Fattura con IVA",
                description="Imposta di bollo applicata a fattura con IVA",
                field_checks=["importo_bollo", "iva"],
                severity="warning",
                fix_suggestion="Il bollo (€2) si applica solo a fatture senza IVA con importo > €77,47",
                reference="DPR 642/72 - Imposta di bollo",
            ),
            SDIRejectionPattern(
                error_code="LOGIC_003",
                pattern_name="Data Scadenza Precedente a Emissione",
                description="Data scadenza pagamento precedente alla data di emissione",
                field_checks=["pagamenti.data_scadenza", "data_emissione"],
                severity="error",
                fix_suggestion="La data di scadenza deve essere >= data di emissione",
                reference="Validazione logica",
            ),
        ]

    def get_pattern_by_code(self, error_code: str) -> SDIRejectionPattern | None:
        """Get pattern by error code.

        Args:
            error_code: SDI error code

        Returns:
            Pattern if found, None otherwise
        """
        for pattern in self.patterns:
            if pattern.error_code == error_code:
                return pattern
        return None

    def get_patterns_by_field(self, field_name: str) -> list[SDIRejectionPattern]:
        """Get all patterns related to a specific field.

        Args:
            field_name: Field name to search

        Returns:
            List of matching patterns
        """
        matching_patterns = []

        for pattern in self.patterns:
            if pattern.field_checks and field_name in pattern.field_checks:
                matching_patterns.append(pattern)

        return matching_patterns

    def search_patterns(self, text: str) -> list[SDIRejectionPattern]:
        """Search patterns by text matching.

        Args:
            text: Text to search in pattern descriptions

        Returns:
            List of matching patterns
        """
        text_lower = text.lower()
        matching_patterns = []

        for pattern in self.patterns:
            if (
                text_lower in pattern.pattern_name.lower()
                or text_lower in pattern.description.lower()
            ):
                matching_patterns.append(pattern)

        return matching_patterns

    def get_all_patterns(self) -> list[SDIRejectionPattern]:
        """Get all patterns.

        Returns:
            List of all patterns
        """
        return self.patterns
