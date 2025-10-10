"""Main compliance checker orchestrator.

This module provides the unified ComplianceChecker class that orchestrates:
- Deterministic rules validation
- SDI rejection pattern matching
- AI-powered heuristic analysis

It provides a single, comprehensive compliance check for invoices before
submission to SDI.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from openfatture.ai.agents.compliance.heuristics import (
    AIHeuristicAnalyzer,
)
from openfatture.ai.agents.compliance.rules import (
    ComplianceRulesEngine,
    ValidationIssue,
    ValidationSeverity,
)
from openfatture.ai.agents.compliance.sdi_patterns import (
    SDIPatternDatabase,
    SDIRejectionPattern,
)
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ComplianceLevel(Enum):
    """Compliance check levels."""

    BASIC = "basic"  # Only rules engine
    STANDARD = "standard"  # Rules + SDI patterns
    ADVANCED = "advanced"  # Rules + SDI patterns + AI heuristics


@dataclass
class ComplianceReport:
    """Comprehensive compliance check report.

    Attributes:
        invoice_id: Invoice ID
        invoice_number: Invoice number for reference
        timestamp: When the check was performed
        is_compliant: True if invoice passes all ERROR-level checks
        compliance_score: Overall score (0-100)
        risk_score: Risk assessment score (0-100)
        validation_issues: List of all validation issues
        sdi_pattern_matches: Matched SDI rejection patterns
        heuristic_anomalies: AI-detected anomalies
        recommendations: List of recommendations
        level: Compliance check level used
    """

    invoice_id: int
    invoice_number: str
    timestamp: datetime
    is_compliant: bool
    compliance_score: float
    risk_score: float = 0.0
    validation_issues: list[ValidationIssue] = field(default_factory=list)
    sdi_pattern_matches: list[SDIRejectionPattern] = field(default_factory=list)
    heuristic_anomalies: list[ValidationIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    level: ComplianceLevel = ComplianceLevel.STANDARD

    def get_errors(self) -> list[ValidationIssue]:
        """Get all ERROR-level issues."""
        return [
            issue
            for issue in self.validation_issues + self.heuristic_anomalies
            if issue.severity == ValidationSeverity.ERROR
        ]

    def get_warnings(self) -> list[ValidationIssue]:
        """Get all WARNING-level issues."""
        return [
            issue
            for issue in self.validation_issues + self.heuristic_anomalies
            if issue.severity == ValidationSeverity.WARNING
        ]

    def get_info(self) -> list[ValidationIssue]:
        """Get all INFO-level issues."""
        return [
            issue
            for issue in self.validation_issues + self.heuristic_anomalies
            if issue.severity == ValidationSeverity.INFO
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "timestamp": self.timestamp.isoformat(),
            "is_compliant": self.is_compliant,
            "compliance_score": self.compliance_score,
            "risk_score": self.risk_score,
            "level": self.level.value,
            "summary": {
                "total_issues": len(self.validation_issues) + len(self.heuristic_anomalies),
                "errors": len(self.get_errors()),
                "warnings": len(self.get_warnings()),
                "info": len(self.get_info()),
                "sdi_patterns_matched": len(self.sdi_pattern_matches),
            },
            "errors": [
                {
                    "code": issue.code,
                    "field": issue.field,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                }
                for issue in self.get_errors()
            ],
            "warnings": [
                {
                    "code": issue.code,
                    "field": issue.field,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                }
                for issue in self.get_warnings()
            ],
            "recommendations": self.recommendations,
        }


class ComplianceChecker:
    """Comprehensive compliance checker for FatturaPA invoices.

    Orchestrates multiple validation layers:
    1. Deterministic rules (ComplianceRulesEngine)
    2. SDI rejection patterns (SDIPatternDatabase)
    3. AI-powered heuristics (AIHeuristicAnalyzer)

    Features:
    - Multi-level compliance checking
    - Comprehensive reporting
    - Batch processing support
    - Historical pattern analysis
    - SDI rejection prediction

    Example:
        >>> checker = ComplianceChecker(level=ComplianceLevel.ADVANCED)
        >>> report = await checker.check_invoice(invoice_id=123)
        >>> if not report.is_compliant:
        ...     print(f"Found {len(report.get_errors())} errors")
        ...     for error in report.get_errors():
        ...         print(f"  - {error.message}")
    """

    def __init__(
        self,
        level: ComplianceLevel = ComplianceLevel.STANDARD,
        ai_provider: str = "anthropic",
        ai_model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
    ) -> None:
        """Initialize compliance checker.

        Args:
            level: Compliance check level
            ai_provider: AI provider for heuristics (used if level=ADVANCED)
            ai_model: AI model for heuristics
            api_key: API key for AI provider
        """
        self.level = level

        # Initialize rules engine (always used)
        self.rules_engine = ComplianceRulesEngine()

        # Initialize SDI patterns (used for STANDARD and ADVANCED)
        if self.level in [ComplianceLevel.STANDARD, ComplianceLevel.ADVANCED]:
            self.sdi_patterns = SDIPatternDatabase()
        else:
            self.sdi_patterns = None

        # Initialize AI heuristics (used only for ADVANCED)
        if self.level == ComplianceLevel.ADVANCED:
            self.ai_analyzer = AIHeuristicAnalyzer(
                provider_name=ai_provider,
                model=ai_model,
                api_key=api_key,
            )
        else:
            self.ai_analyzer = None

        logger.info(
            "compliance_checker_initialized",
            level=level.value,
            has_sdi_patterns=self.sdi_patterns is not None,
            has_ai_analyzer=self.ai_analyzer is not None,
        )

    async def check_invoice(
        self,
        invoice_id: int,
        include_history: bool = True,
    ) -> ComplianceReport:
        """Perform comprehensive compliance check on invoice.

        Args:
            invoice_id: Invoice ID to check
            include_history: Include client history in analysis

        Returns:
            ComplianceReport with all findings
        """
        db = SessionLocal()

        try:
            # Load invoice
            fattura = db.query(Fattura).filter(Fattura.id == invoice_id).first()

            if not fattura:
                raise ValueError(f"Invoice {invoice_id} not found")

            logger.info(
                "compliance_check_started",
                invoice_id=invoice_id,
                numero=fattura.numero,
                level=self.level.value,
            )

            # Create report
            report = ComplianceReport(
                invoice_id=invoice_id,
                invoice_number=f"{fattura.numero}/{fattura.anno}",
                timestamp=datetime.now(),
                is_compliant=True,
                compliance_score=100.0,
                level=self.level,
            )

            # 1. Run rules engine validation
            validation_result = self.rules_engine.validate_invoice(fattura)
            report.validation_issues = validation_result.issues
            report.is_compliant = validation_result.is_valid
            report.compliance_score = validation_result.score

            # 2. Match SDI patterns (if enabled)
            if self.sdi_patterns:
                self._match_sdi_patterns(fattura, report)

            # 3. Run AI heuristic analysis (if enabled)
            if self.ai_analyzer and include_history:
                client_history = self._get_client_history(db, fattura)
                heuristic_analysis = await self.ai_analyzer.analyze_invoice(fattura, client_history)

                report.heuristic_anomalies = heuristic_analysis.anomalies_found
                report.risk_score = heuristic_analysis.risk_score
                report.recommendations.extend(heuristic_analysis.suggestions)

            # 4. Generate recommendations
            self._generate_recommendations(report)

            # 5. Calculate final scores
            self._calculate_final_scores(report)

            logger.info(
                "compliance_check_completed",
                invoice_id=invoice_id,
                is_compliant=report.is_compliant,
                compliance_score=report.compliance_score,
                risk_score=report.risk_score,
                errors_count=len(report.get_errors()),
                warnings_count=len(report.get_warnings()),
            )

            return report

        finally:
            db.close()

    def _match_sdi_patterns(self, fattura: Fattura, report: ComplianceReport) -> None:
        """Match invoice against known SDI rejection patterns."""

        # Get all patterns
        all_patterns = self.sdi_patterns.get_all_patterns()

        matched_patterns = []

        for pattern in all_patterns:
            # Check field-based patterns
            if pattern.field_checks:
                if self._pattern_matches_fields(fattura, pattern):
                    matched_patterns.append(pattern)

        report.sdi_pattern_matches = matched_patterns

        # Add matched patterns as validation issues
        for pattern in matched_patterns:
            # Only add if not already flagged by rules engine
            existing_codes = {issue.code for issue in report.validation_issues}

            if pattern.error_code not in existing_codes:
                severity = (
                    ValidationSeverity.ERROR
                    if pattern.severity == "error"
                    else ValidationSeverity.WARNING
                )

                report.validation_issues.append(
                    ValidationIssue(
                        code=pattern.error_code,
                        severity=severity,
                        field=pattern.field_checks[0] if pattern.field_checks else "unknown",
                        message=f"SDI Pattern: {pattern.pattern_name}",
                        suggestion=pattern.fix_suggestion,
                        reference=pattern.reference,
                    )
                )

    def _pattern_matches_fields(self, fattura: Fattura, pattern: SDIRejectionPattern) -> bool:
        """Check if pattern matches invoice fields."""

        # Simplified pattern matching (in production, use more sophisticated logic)
        for field_check in pattern.field_checks:
            if "cliente." in field_check:
                field_name = field_check.replace("cliente.", "")
                value = getattr(fattura.cliente, field_name, None)

                # Check regex patterns
                if value and pattern.compiled_patterns:
                    for regex in pattern.compiled_patterns:
                        if regex.match(str(value)):
                            return True

            elif "righe" in field_check:
                # Check invoice lines
                for riga in fattura.righe:
                    if pattern.compiled_patterns:
                        for regex in pattern.compiled_patterns:
                            if regex.search(str(riga.descrizione)):
                                return True

        return False

    def _get_client_history(self, db, fattura: Fattura, limit: int = 10) -> list[Fattura]:
        """Get client invoice history."""

        return (
            db.query(Fattura)
            .filter(
                Fattura.cliente_id == fattura.cliente_id,
                Fattura.id != fattura.id,
                Fattura.data_emissione < fattura.data_emissione,
            )
            .order_by(Fattura.data_emissione.desc())
            .limit(limit)
            .all()
        )

    def _generate_recommendations(self, report: ComplianceReport) -> None:
        """Generate actionable recommendations based on findings."""

        errors = report.get_errors()
        warnings = report.get_warnings()

        if len(errors) > 0:
            report.recommendations.append(
                f"⚠️  Correggere {len(errors)} errori critici prima dell'invio a SDI"
            )

        if len(warnings) > 5:
            report.recommendations.append(
                f"⚡ Risolvere {len(warnings)} avvisi per ridurre il rischio di scarto"
            )

        if report.risk_score > 50:
            report.recommendations.append(
                "🔍 Fattura ad alto rischio - revisione accurata consigliata"
            )

        # Specific recommendations based on issue types
        issue_codes = {issue.code for issue in report.validation_issues}

        if "FPA012" in issue_codes or "FPA013" in issue_codes:
            report.recommendations.append("📋 Verificare i dati fiscali del cliente (P.IVA/CF)")

        if "FPA018" in issue_codes:
            report.recommendations.append("📬 Richiedere Codice Destinatario o PEC al cliente")

        if any("FPA03" in code for code in issue_codes):
            report.recommendations.append("📅 Controllare le date (emissione, scadenza)")

        if any("FPA04" in code or "FPA07" in code for code in issue_codes):
            report.recommendations.append("💰 Ricalcolare gli importi e verificare i totali")

    def _calculate_final_scores(self, report: ComplianceReport) -> None:
        """Calculate final compliance and risk scores."""

        # Compliance score already calculated by rules engine
        # Adjust based on SDI patterns and heuristics

        if report.sdi_pattern_matches:
            # Each SDI pattern match reduces compliance score
            report.compliance_score -= len(report.sdi_pattern_matches) * 5

        # Ensure scores are in valid range
        report.compliance_score = max(0.0, min(100.0, report.compliance_score))
        report.risk_score = max(0.0, min(100.0, report.risk_score))

    async def check_batch(
        self,
        invoice_ids: list[int],
    ) -> dict[int, ComplianceReport]:
        """Check multiple invoices.

        Args:
            invoice_ids: List of invoice IDs

        Returns:
            Dictionary mapping invoice IDs to reports
        """
        logger.info("batch_compliance_check_started", count=len(invoice_ids))

        results = {}

        for invoice_id in invoice_ids:
            try:
                report = await self.check_invoice(invoice_id)
                results[invoice_id] = report

            except Exception as e:
                logger.error(
                    "invoice_check_failed",
                    invoice_id=invoice_id,
                    error=str(e),
                )

        logger.info("batch_compliance_check_completed", count=len(results))

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get compliance checker statistics.

        Returns:
            Dictionary with stats
        """
        stats = {
            "level": self.level.value,
            "components": {
                "rules_engine": True,
                "sdi_patterns": self.sdi_patterns is not None,
                "ai_heuristics": self.ai_analyzer is not None,
            },
        }

        if self.sdi_patterns:
            stats["sdi_patterns_count"] = len(self.sdi_patterns.get_all_patterns())

        return stats
