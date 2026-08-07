"""Deterministic rule engine for FatturaPA compliance validation.

This module implements strict validation rules based on FatturaPA technical
specifications and SDI requirements. All rules are deterministic and based on
official documentation.

References:
- FatturaPA v1.2.2 Technical Specifications
- Agenzia delle Entrate SDI Documentation
- DM 17/06/2014 and subsequent updates
"""

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import cast

from openfatture.storage.database.models import Cliente, Fattura, RigaFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Will cause SDI rejection
    WARNING = "warning"  # May cause issues
    INFO = "info"  # Best practice recommendation


@dataclass
class ValidationIssue:
    """Represents a validation issue found during compliance check.

    Attributes:
        code: Unique code identifying the rule (e.g., "FPA001")
        severity: Issue severity level
        field: Field name where issue was found
        message: Human-readable error message
        suggestion: Optional fix suggestion
        reference: Reference to FatturaPA spec or law
    """

    code: str
    severity: ValidationSeverity
    field: str
    message: str
    suggestion: str | None = None
    reference: str | None = None


@dataclass
class ValidationResult:
    """Result of compliance validation.

    Attributes:
        is_valid: True if invoice passes all ERROR-level checks
        issues: List of validation issues found
        score: Compliance score (0-100)
    """

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    score: float = 100.0

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add validation issue and update score."""
        self.issues.append(issue)

        if issue.severity == ValidationSeverity.ERROR:
            self.is_valid = False
            self.score -= 20
        elif issue.severity == ValidationSeverity.WARNING:
            self.score -= 5
        else:  # INFO
            self.score -= 1

        self.score = max(0.0, self.score)


class ComplianceRulesEngine:
    """Deterministic rule engine for FatturaPA validation.

    Implements validation rules from:
    - FatturaPA Technical Specifications v1.2.2
    - SDI validation requirements
    - Italian tax regulations (DM 17/06/2014)

    Example:
        >>> engine = ComplianceRulesEngine()
        >>> result = engine.validate_invoice(fattura)
        >>> if not result.is_valid:
        ...     for issue in result.issues:
        ...         print(f"{issue.code}: {issue.message}")
    """

    # Regex patterns for validation
    PARTITA_IVA_PATTERN = re.compile(r"^[0-9]{11}$")
    CODICE_FISCALE_PATTERN = re.compile(r"^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$")
    CODICE_DESTINATARIO_PATTERN = re.compile(r"^[A-Z0-9]{7}$")
    CAP_PATTERN = re.compile(r"^[0-9]{5}$")
    PROVINCIA_PATTERN = re.compile(r"^[A-Z]{2}$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # SDI defaults
    CODICE_DESTINATARIO_DEFAULT = "0000000"  # Used when PEC is provided

    def __init__(self) -> None:
        """Initialize rules engine."""
        logger.info("compliance_rules_engine_initialized")

    def validate_invoice(self, fattura: Fattura) -> ValidationResult:
        """Validate complete invoice for FatturaPA compliance.

        Args:
            fattura: Invoice to validate

        Returns:
            ValidationResult with all issues found
        """
        logger.debug("validating_invoice", invoice_id=fattura.id, numero=fattura.numero)

        result = ValidationResult(is_valid=True)

        # 1. Invoice metadata validation
        self._validate_invoice_metadata(fattura, result)

        # 2. Client data validation
        self._validate_client_data(fattura.cliente, result)

        # 3. Invoice lines validation
        self._validate_invoice_lines(fattura, result)

        # 4. Totals and calculations
        self._validate_totals(fattura, result)

        # 5. Payment terms validation
        self._validate_payment_terms(fattura, result)

        # 6. SDI-specific requirements
        self._validate_sdi_requirements(fattura, result)

        logger.info(
            "invoice_validation_completed",
            invoice_id=fattura.id,
            is_valid=result.is_valid,
            issues_count=len(result.issues),
            score=result.score,
        )

        return result

    def _validate_invoice_metadata(self, fattura: Fattura, result: ValidationResult) -> None:
        """Validate invoice metadata (numero, data, tipo documento)."""

        # FPA001: Invoice number required
        if not fattura.numero or not fattura.numero.strip():
            result.add_issue(
                ValidationIssue(
                    code="FPA001",
                    severity=ValidationSeverity.ERROR,
                    field="numero",
                    message="Numero fattura obbligatorio",
                    suggestion="Inserire un numero progressivo univoco per l'anno",
                    reference="FatturaPA v1.2.2 - Campo 1.1.2 (Numero)",
                )
            )

        # FPA002: Year required
        if not fattura.anno or fattura.anno < 2000 or fattura.anno > 2100:
            result.add_issue(
                ValidationIssue(
                    code="FPA002",
                    severity=ValidationSeverity.ERROR,
                    field="anno",
                    message="Anno fattura non valido",
                    suggestion=f"Inserire un anno valido (es. {date.today().year})",
                    reference="Dato richiesto per identificazione univoca",
                )
            )

        # FPA003: Emission date required
        if not fattura.data_emissione:
            result.add_issue(
                ValidationIssue(
                    code="FPA003",
                    severity=ValidationSeverity.ERROR,
                    field="data_emissione",
                    message="Data di emissione obbligatoria",
                    suggestion="Inserire la data di emissione della fattura",
                    reference="FatturaPA v1.2.2 - Campo 1.1.3 (Data)",
                )
            )
        else:
            # FPA004: Emission date cannot be in the future
            if fattura.data_emissione > date.today():
                result.add_issue(
                    ValidationIssue(
                        code="FPA004",
                        severity=ValidationSeverity.ERROR,
                        field="data_emissione",
                        message="La data di emissione non può essere futura",
                        suggestion="Verificare la data inserita",
                        reference="Validazione logica SDI",
                    )
                )

            # FPA005: Emission date should match year
            if fattura.data_emissione.year != fattura.anno:
                result.add_issue(
                    ValidationIssue(
                        code="FPA005",
                        severity=ValidationSeverity.WARNING,
                        field="data_emissione",
                        message=f"La data di emissione ({fattura.data_emissione.year}) "
                        f"non corrisponde all'anno della fattura ({fattura.anno})",
                        suggestion="Verificare se l'anno è corretto (es. fattura differita)",
                        reference="Best practice - verificare coerenza temporale",
                    )
                )

        # FPA006: Document type required
        if not fattura.tipo_documento:
            result.add_issue(
                ValidationIssue(
                    code="FPA006",
                    severity=ValidationSeverity.ERROR,
                    field="tipo_documento",
                    message="Tipo documento obbligatorio",
                    suggestion="Selezionare un tipo documento valido (es. TD01)",
                    reference="FatturaPA v1.2.2 - Campo 1.1.1 (TipoDocumento)",
                )
            )

    def _validate_client_data(self, cliente: Cliente, result: ValidationResult) -> None:
        """Validate client/customer data."""

        # FPA010: Client denomination required
        if not cliente.denominazione or not cliente.denominazione.strip():
            result.add_issue(
                ValidationIssue(
                    code="FPA010",
                    severity=ValidationSeverity.ERROR,
                    field="cliente.denominazione",
                    message="Denominazione cliente obbligatoria",
                    suggestion="Inserire ragione sociale o nome e cognome",
                    reference="FatturaPA v1.2.2 - Campo 1.4.2 (Anagrafica)",
                )
            )

        # FPA011: P.IVA or CF required
        has_piva = bool(cliente.partita_iva and cliente.partita_iva.strip())
        has_cf = bool(cliente.codice_fiscale and cliente.codice_fiscale.strip())

        if not has_piva and not has_cf:
            result.add_issue(
                ValidationIssue(
                    code="FPA011",
                    severity=ValidationSeverity.ERROR,
                    field="cliente.partita_iva",
                    message="Partita IVA o Codice Fiscale obbligatori",
                    suggestion="Inserire almeno uno tra P.IVA o CF del cliente",
                    reference="FatturaPA v1.2.2 - Campo 1.4.1.1 (IdPaese/IdCodice)",
                )
            )

        # FPA012: P.IVA format validation (Italian)
        if has_piva and cliente.nazione == "IT":
            partita_iva = cast(str, cliente.partita_iva)
            if not self.PARTITA_IVA_PATTERN.match(partita_iva):
                result.add_issue(
                    ValidationIssue(
                        code="FPA012",
                        severity=ValidationSeverity.ERROR,
                        field="cliente.partita_iva",
                        message=f"Partita IVA non valida: {cliente.partita_iva}",
                        suggestion="La P.IVA italiana deve essere di 11 cifre numeriche",
                        reference="FatturaPA v1.2.2 - Campo 1.4.1.1.2 (IdCodice)",
                    )
                )

        # FPA013: CF format validation (Italian)
        if has_cf and cliente.nazione == "IT":
            codice_fiscale = cast(str, cliente.codice_fiscale)
            if not self.CODICE_FISCALE_PATTERN.match(codice_fiscale.upper()):
                result.add_issue(
                    ValidationIssue(
                        code="FPA013",
                        severity=ValidationSeverity.WARNING,
                        field="cliente.codice_fiscale",
                        message=f"Codice Fiscale formato non standard: {cliente.codice_fiscale}",
                        suggestion="Il CF italiano standard è di 16 caratteri alfanumerici",
                        reference="FatturaPA v1.2.2 - Campo 1.4.1.2 (CodiceFiscale)",
                    )
                )

        # FPA014: Address validation (Italian customers)
        if cliente.nazione == "IT":
            if not cliente.indirizzo or not cliente.indirizzo.strip():
                result.add_issue(
                    ValidationIssue(
                        code="FPA014",
                        severity=ValidationSeverity.ERROR,
                        field="cliente.indirizzo",
                        message="Indirizzo obbligatorio per clienti italiani",
                        suggestion="Inserire via/piazza",
                        reference="FatturaPA v1.2.2 - Campo 1.4.2 (Sede)",
                    )
                )

            if not cliente.cap or not self.CAP_PATTERN.match(cliente.cap):
                result.add_issue(
                    ValidationIssue(
                        code="FPA015",
                        severity=ValidationSeverity.ERROR,
                        field="cliente.cap",
                        message="CAP obbligatorio e deve essere di 5 cifre",
                        suggestion="Inserire CAP valido (es. 00100)",
                        reference="FatturaPA v1.2.2 - Campo 1.4.2.4 (CAP)",
                    )
                )

            if not cliente.comune or not cliente.comune.strip():
                result.add_issue(
                    ValidationIssue(
                        code="FPA016",
                        severity=ValidationSeverity.ERROR,
                        field="cliente.comune",
                        message="Comune obbligatorio per clienti italiani",
                        suggestion="Inserire il comune di residenza/sede",
                        reference="FatturaPA v1.2.2 - Campo 1.4.2.5 (Comune)",
                    )
                )

            if not cliente.provincia or not self.PROVINCIA_PATTERN.match(cliente.provincia):
                result.add_issue(
                    ValidationIssue(
                        code="FPA017",
                        severity=ValidationSeverity.ERROR,
                        field="cliente.provincia",
                        message="Provincia obbligatoria (sigla 2 caratteri)",
                        suggestion="Inserire sigla provincia (es. RM, MI)",
                        reference="FatturaPA v1.2.2 - Campo 1.4.2.6 (Provincia)",
                    )
                )

        # FPA018: Codice Destinatario or PEC required
        has_codice_dest = bool(
            cliente.codice_destinatario
            and cliente.codice_destinatario != self.CODICE_DESTINATARIO_DEFAULT
        )
        has_pec = bool(cliente.pec and cliente.pec.strip())

        if not has_codice_dest and not has_pec:
            result.add_issue(
                ValidationIssue(
                    code="FPA018",
                    severity=ValidationSeverity.ERROR,
                    field="cliente.codice_destinatario",
                    message="Codice Destinatario o PEC obbligatori per invio SDI",
                    suggestion="Richiedere al cliente Codice Destinatario SDI o indirizzo PEC",
                    reference="Specifiche SDI - Recapito fattura elettronica",
                )
            )

        # FPA019: Codice Destinatario format
        if has_codice_dest:
            codice_destinatario = cast(str, cliente.codice_destinatario)
            if not self.CODICE_DESTINATARIO_PATTERN.match(codice_destinatario):
                result.add_issue(
                    ValidationIssue(
                        code="FPA019",
                        severity=ValidationSeverity.ERROR,
                        field="cliente.codice_destinatario",
                        message=f"Codice Destinatario non valido: {cliente.codice_destinatario}",
                        suggestion="Il Codice Destinatario deve essere di 7 caratteri alfanumerici",
                        reference="FatturaPA v1.2.2 - Campo 1.1.6 (CodiceDestinatario)",
                    )
                )

        # FPA020: PEC format
        if has_pec:
            pec = cast(str, cliente.pec)
            if not self.EMAIL_PATTERN.match(pec):
                result.add_issue(
                    ValidationIssue(
                        code="FPA020",
                        severity=ValidationSeverity.WARNING,
                        field="cliente.pec",
                        message=f"Formato PEC non valido: {pec}",
                        suggestion="Verificare l'indirizzo PEC",
                        reference="FatturaPA v1.2.2 - Campo 1.1.5 (PECDestinatario)",
                    )
                )

    def _validate_invoice_lines(self, fattura: Fattura, result: ValidationResult) -> None:
        """Validate invoice lines."""

        # FPA030: At least one line required
        if not fattura.righe or len(fattura.righe) == 0:
            result.add_issue(
                ValidationIssue(
                    code="FPA030",
                    severity=ValidationSeverity.ERROR,
                    field="righe",
                    message="La fattura deve contenere almeno una riga",
                    suggestion="Aggiungere servizi/prodotti alla fattura",
                    reference="FatturaPA v1.2.2 - Campo 2.2.1 (DettaglioLinee)",
                )
            )
            return

        # Validate each line
        for i, riga in enumerate(fattura.righe, 1):
            self._validate_invoice_line(riga, i, result)

    def _validate_invoice_line(
        self, riga: RigaFattura, line_number: int, result: ValidationResult
    ) -> None:
        """Validate single invoice line."""

        field_prefix = f"righe[{line_number}]"

        # FPA031: Description required
        if not riga.descrizione or not riga.descrizione.strip():
            result.add_issue(
                ValidationIssue(
                    code="FPA031",
                    severity=ValidationSeverity.ERROR,
                    field=f"{field_prefix}.descrizione",
                    message=f"Riga {line_number}: Descrizione obbligatoria",
                    suggestion="Inserire una descrizione del servizio/prodotto",
                    reference="FatturaPA v1.2.2 - Campo 2.2.1.4 (Descrizione)",
                )
            )

        # FPA032: Quantity must be positive
        if riga.quantita <= 0:
            result.add_issue(
                ValidationIssue(
                    code="FPA032",
                    severity=ValidationSeverity.ERROR,
                    field=f"{field_prefix}.quantita",
                    message=f"Riga {line_number}: Quantità deve essere positiva",
                    suggestion="Inserire quantità > 0",
                    reference="FatturaPA v1.2.2 - Campo 2.2.1.5 (Quantita)",
                )
            )

        # FPA033: Unit price required
        if riga.prezzo_unitario is None:
            result.add_issue(
                ValidationIssue(
                    code="FPA033",
                    severity=ValidationSeverity.ERROR,
                    field=f"{field_prefix}.prezzo_unitario",
                    message=f"Riga {line_number}: Prezzo unitario obbligatorio",
                    suggestion="Inserire il prezzo unitario",
                    reference="FatturaPA v1.2.2 - Campo 2.2.1.6 (PrezzoUnitario)",
                )
            )

        # FPA034: VAT rate validation
        valid_vat_rates = [0, 4, 5, 10, 22]  # Standard Italian VAT rates
        if riga.aliquota_iva not in valid_vat_rates:
            result.add_issue(
                ValidationIssue(
                    code="FPA034",
                    severity=ValidationSeverity.WARNING,
                    field=f"{field_prefix}.aliquota_iva",
                    message=f"Riga {line_number}: Aliquota IVA {riga.aliquota_iva}% non standard",
                    suggestion=f"Aliquote standard: {', '.join(map(str, valid_vat_rates))}%",
                    reference="DPR 633/1972 - Aliquote IVA ordinarie",
                )
            )

        # FPA035: Line calculations
        expected_imponibile = riga.quantita * riga.prezzo_unitario
        expected_iva = expected_imponibile * riga.aliquota_iva / 100
        expected_totale = expected_imponibile + expected_iva

        if abs(riga.imponibile - expected_imponibile) > Decimal("0.01"):
            result.add_issue(
                ValidationIssue(
                    code="FPA035",
                    severity=ValidationSeverity.ERROR,
                    field=f"{field_prefix}.imponibile",
                    message=f"Riga {line_number}: Imponibile errato (atteso: €{expected_imponibile:.2f})",
                    suggestion=f"Ricalcolare: {riga.quantita} × €{riga.prezzo_unitario:.2f}",
                    reference="Calcolo matematico imponibile",
                )
            )

        if abs(riga.iva - expected_iva) > Decimal("0.01"):
            result.add_issue(
                ValidationIssue(
                    code="FPA036",
                    severity=ValidationSeverity.ERROR,
                    field=f"{field_prefix}.iva",
                    message=f"Riga {line_number}: IVA errata (atteso: €{expected_iva:.2f})",
                    suggestion=f"Ricalcolare: €{expected_imponibile:.2f} × {riga.aliquota_iva}%",
                    reference="Calcolo matematico IVA",
                )
            )

    def _validate_totals(self, fattura: Fattura, result: ValidationResult) -> None:
        """Validate invoice totals and calculations."""

        if not fattura.righe:
            return  # Already flagged in _validate_invoice_lines

        # Calculate expected totals
        expected_imponibile = sum(riga.imponibile for riga in fattura.righe)
        expected_iva = sum(riga.iva for riga in fattura.righe)
        expected_totale = expected_imponibile + expected_iva

        # FPA040: Imponibile validation
        if abs(fattura.imponibile - expected_imponibile) > Decimal("0.01"):
            result.add_issue(
                ValidationIssue(
                    code="FPA040",
                    severity=ValidationSeverity.ERROR,
                    field="imponibile",
                    message=f"Imponibile totale errato (atteso: €{expected_imponibile:.2f}, "
                    f"trovato: €{fattura.imponibile:.2f})",
                    suggestion="Ricalcolare la somma degli imponibili delle righe",
                    reference="FatturaPA v1.2.2 - Campo 2.2.2 (DatiRiepilogo)",
                )
            )

        # FPA041: IVA validation
        if abs(fattura.iva - expected_iva) > Decimal("0.01"):
            result.add_issue(
                ValidationIssue(
                    code="FPA041",
                    severity=ValidationSeverity.ERROR,
                    field="iva",
                    message=f"IVA totale errata (atteso: €{expected_iva:.2f}, "
                    f"trovato: €{fattura.iva:.2f})",
                    suggestion="Ricalcolare la somma dell'IVA delle righe",
                    reference="FatturaPA v1.2.2 - Campo 2.2.2 (DatiRiepilogo)",
                )
            )

        # FPA042: Total validation
        # Account for ritenuta and bollo
        expected_total_final = (
            expected_totale - (fattura.ritenuta_acconto or Decimal("0")) + fattura.importo_bollo
        )

        if abs(fattura.totale - expected_total_final) > Decimal("0.01"):
            result.add_issue(
                ValidationIssue(
                    code="FPA042",
                    severity=ValidationSeverity.ERROR,
                    field="totale",
                    message=f"Totale fattura errato (atteso: €{expected_total_final:.2f}, "
                    f"trovato: €{fattura.totale:.2f})",
                    suggestion="Ricalcolare: Imponibile + IVA - Ritenuta + Bollo",
                    reference="FatturaPA v1.2.2 - Campo 2.4.2 (ImportoPagamento)",
                )
            )

        # FPA043: Positive totals
        if fattura.imponibile < 0:
            result.add_issue(
                ValidationIssue(
                    code="FPA043",
                    severity=ValidationSeverity.WARNING,
                    field="imponibile",
                    message="Imponibile negativo (verificare se nota di credito)",
                    suggestion="Per importi negativi usare Tipo Documento TD04 (Nota di credito)",
                    reference="FatturaPA v1.2.2 - TipoDocumento TD04",
                )
            )

    def _validate_payment_terms(self, fattura: Fattura, result: ValidationResult) -> None:
        """Validate payment terms and data."""

        if not fattura.pagamenti or len(fattura.pagamenti) == 0:
            result.add_issue(
                ValidationIssue(
                    code="FPA050",
                    severity=ValidationSeverity.WARNING,
                    field="pagamenti",
                    message="Nessuna condizione di pagamento specificata",
                    suggestion="Aggiungere scadenza e modalità di pagamento",
                    reference="FatturaPA v1.2.2 - Campo 2.4 (DatiPagamento)",
                )
            )
            return

        # Validate payment due date
        for i, pagamento in enumerate(fattura.pagamenti, 1):
            if pagamento.data_scadenza < fattura.data_emissione:
                result.add_issue(
                    ValidationIssue(
                        code="FPA051",
                        severity=ValidationSeverity.ERROR,
                        field=f"pagamenti[{i}].data_scadenza",
                        message=f"Pagamento {i}: Scadenza precedente alla data di emissione",
                        suggestion="La scadenza deve essere >= data emissione",
                        reference="Validazione logica",
                    )
                )

    def _validate_sdi_requirements(self, fattura: Fattura, result: ValidationResult) -> None:
        """Validate SDI-specific requirements."""

        # FPA060: XML not already generated for draft
        if fattura.stato.value == "bozza" and fattura.xml_path:
            result.add_issue(
                ValidationIssue(
                    code="FPA060",
                    severity=ValidationSeverity.INFO,
                    field="stato",
                    message="XML già generato per fattura in bozza",
                    suggestion="Rigenerare XML se sono state fatte modifiche",
                    reference="Best practice",
                )
            )

        # FPA061: Invoices ready to send should be complete
        if fattura.stato.value == "da_inviare":
            if not fattura.xml_path:
                result.add_issue(
                    ValidationIssue(
                        code="FPA061",
                        severity=ValidationSeverity.ERROR,
                        field="xml_path",
                        message="XML non generato per fattura da inviare",
                        suggestion="Generare il file XML prima dell'invio",
                        reference="Requisito SDI",
                    )
                )
