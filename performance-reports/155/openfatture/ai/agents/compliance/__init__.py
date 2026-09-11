"""OpenFatture Compliance Checker Agent.

This module provides comprehensive FatturaPA compliance checking using:
- Deterministic rules validation
- SDI rejection pattern matching
- AI-powered heuristic analysis

Example Usage:
    >>> from openfatture.ai.agents.compliance import ComplianceChecker, ComplianceLevel
    >>>
    >>> # Initialize checker
    >>> checker = ComplianceChecker(level=ComplianceLevel.ADVANCED)
    >>>
    >>> # Check single invoice
    >>> report = await checker.check_invoice(invoice_id=123)
    >>>
    >>> # Print results
    >>> if not report.is_compliant:
    ...     print(f"Found {len(report.get_errors())} errors")
    ...     for error in report.get_errors():
    ...         print(f"  - {error.code}: {error.message}")
    >>>
    >>> # Check batch
    >>> reports = await checker.check_batch([123, 124, 125])
"""

from openfatture.ai.agents.compliance.checker import (
    ComplianceChecker,
    ComplianceLevel,
    ComplianceReport,
)
from openfatture.ai.agents.compliance.heuristics import (
    AIHeuristicAnalyzer,
    HeuristicAnalysis,
)
from openfatture.ai.agents.compliance.rules import (
    ComplianceRulesEngine,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from openfatture.ai.agents.compliance.sdi_patterns import (
    SDIErrorCode,
    SDIPatternDatabase,
    SDIRejectionPattern,
)

__all__ = [
    # Main API
    "ComplianceChecker",
    "ComplianceReport",
    "ComplianceLevel",
    # Rules Engine
    "ComplianceRulesEngine",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    # SDI Patterns
    "SDIPatternDatabase",
    "SDIRejectionPattern",
    "SDIErrorCode",
    # AI Heuristics
    "AIHeuristicAnalyzer",
    "HeuristicAnalysis",
]
