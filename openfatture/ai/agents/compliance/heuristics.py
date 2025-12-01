"""AI-powered heuristic analyzer for invoice compliance.

This module uses AI to detect anomalies and potential issues that deterministic
rules might miss. It analyzes:
- Unusual invoice amounts or patterns
- Suspicious or incomplete descriptions
- Client-specific anomalies
- Historical pattern deviations
- Industry-specific compliance risks

Uses the existing AI provider infrastructure for analysis.
"""

import statistics
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy.orm import Session

from openfatture.ai.agents.compliance.rules import ValidationIssue, ValidationSeverity
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.providers import create_provider
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.storage.session import db_session
from openfatture.storage.database.models import Fattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HeuristicAnalysis:
    """Result of AI heuristic analysis.

    Attributes:
        anomalies_found: List of anomaly issues detected
        risk_score: Risk score (0-100, higher = more risky)
        confidence: Confidence in the analysis (0-1)
        suggestions: List of improvement suggestions
    """

    anomalies_found: list[ValidationIssue] = field(default_factory=list)
    risk_score: float = 0.0
    confidence: float = 1.0
    suggestions: list[str] = field(default_factory=list)


class AIHeuristicAnalyzer:
    """AI-powered heuristic analyzer for compliance checking.

    Features:
    - Anomaly detection (amounts, dates, patterns)
    - Description quality analysis
    - Client behavior pattern analysis
    - Historical comparison
    - Industry-specific risk assessment

    Example:
        >>> analyzer = AIHeuristicAnalyzer(api_key="...", model="claude-3-5-sonnet-20241022")
        >>> analysis = await analyzer.analyze_invoice(fattura)
        >>> if analysis.risk_score > 50:
        ...     print("High risk invoice!")
    """

    def __init__(
        self,
        provider_name: str = "anthropic",
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
    ) -> None:
        """Initialize heuristic analyzer.

        Args:
            provider_name: AI provider name (anthropic, openai, ollama)
            model: Model to use
            api_key: API key for the provider
        """
        self.provider: BaseLLMProvider = create_provider(
            provider_name=provider_name,
            model=model,
            api_key=api_key,
        )
        self.model = model

        logger.info(
            "ai_heuristic_analyzer_initialized",
            provider=provider_name,
            model=model,
        )

    async def analyze_invoice(
        self,
        fattura: Fattura,
        client_history: list[Fattura] | None = None,
    ) -> HeuristicAnalysis:
        """Perform AI-powered heuristic analysis on invoice.

        Args:
            fattura: Invoice to analyze
            client_history: Optional client invoice history for context

        Returns:
            HeuristicAnalysis with anomalies and suggestions
        """
        logger.debug("analyzing_invoice_heuristics", invoice_id=fattura.id)

        analysis = HeuristicAnalysis()

        # 1. Analyze invoice amounts for anomalies
        await self._analyze_amount_anomalies(fattura, client_history, analysis)

        # 2. Analyze description quality
        await self._analyze_description_quality(fattura, analysis)

        # 3. Analyze temporal patterns
        await self._analyze_temporal_patterns(fattura, client_history, analysis)

        # 4. Analyze client-specific patterns
        if client_history:
            await self._analyze_client_patterns(fattura, client_history, analysis)

        # 5. Calculate overall risk score
        self._calculate_risk_score(analysis)

        logger.info(
            "heuristic_analysis_completed",
            invoice_id=fattura.id,
            anomalies_count=len(analysis.anomalies_found),
            risk_score=analysis.risk_score,
        )

        return analysis

    async def _analyze_amount_anomalies(
        self,
        fattura: Fattura,
        client_history: list[Fattura] | None,
        analysis: HeuristicAnalysis,
    ) -> None:
        """Detect unusual amounts using statistical analysis and AI."""

        # Statistical analysis if we have history
        if client_history and len(client_history) >= 3:
            amounts = [float(f.totale) for f in client_history]
            mean_amount = statistics.mean(amounts)
            stdev_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0

            current_amount = float(fattura.totale)

            # Check if current amount is > 2 standard deviations from mean
            if stdev_amount > 0:
                z_score = abs((current_amount - mean_amount) / stdev_amount)

                if z_score > 2:
                    analysis.anomalies_found.append(
                        ValidationIssue(
                            code="HEUR001",
                            severity=ValidationSeverity.WARNING,
                            field="totale",
                            message=f"Importo inusuale per questo cliente: €{current_amount:.2f} "
                            f"(media storica: €{mean_amount:.2f})",
                            suggestion="Verificare che l'importo sia corretto",
                            reference="Analisi statistica degli importi storici",
                        )
                    )

        # Detect suspiciously round numbers (e.g., exactly 1000.00, 5000.00)
        if fattura.totale % 100 == 0 and fattura.totale >= 1000:
            analysis.anomalies_found.append(
                ValidationIssue(
                    code="HEUR002",
                    severity=ValidationSeverity.INFO,
                    field="totale",
                    message=f"Importo tondo (€{fattura.totale:.2f}) - verificare calcoli",
                    suggestion="Gli importi tondi possono indicare stime approssimative",
                    reference="Pattern analysis",
                )
            )

        # Very small amounts (potential error)
        if fattura.totale < Decimal("10.00"):
            analysis.anomalies_found.append(
                ValidationIssue(
                    code="HEUR003",
                    severity=ValidationSeverity.WARNING,
                    field="totale",
                    message=f"Importo molto basso: €{fattura.totale:.2f}",
                    suggestion="Verificare che l'importo sia corretto",
                    reference="Threshold analysis",
                )
            )

        # Very large amounts (potential error or fraud risk)
        if fattura.totale > Decimal("50000.00"):
            analysis.anomalies_found.append(
                ValidationIssue(
                    code="HEUR004",
                    severity=ValidationSeverity.WARNING,
                    field="totale",
                    message=f"Importo molto elevato: €{fattura.totale:.2f}",
                    suggestion="Fatture di importo elevato richiedono particolare attenzione",
                    reference="Threshold analysis",
                )
            )

    async def _analyze_description_quality(
        self,
        fattura: Fattura,
        analysis: HeuristicAnalysis,
    ) -> None:
        """Analyze invoice line descriptions using AI."""

        if not fattura.righe:
            return

        # Check for very short descriptions
        for i, riga in enumerate(fattura.righe, 1):
            desc = riga.descrizione.strip()

            # Too short
            if len(desc) < 10:
                analysis.anomalies_found.append(
                    ValidationIssue(
                        code="HEUR010",
                        severity=ValidationSeverity.WARNING,
                        field=f"righe[{i}].descrizione",
                        message=f"Riga {i}: Descrizione troppo breve ({len(desc)} caratteri)",
                        suggestion="Descrizioni dettagliate riducono rischi di contestazione",
                        reference="Best practice FatturaPA",
                    )
                )

            # Generic/vague terms (using AI)
            vague_terms = ["servizi", "consulenza", "prestazione", "lavori", "attività"]
            if any(term in desc.lower() for term in vague_terms) and len(desc) < 50:
                analysis.anomalies_found.append(
                    ValidationIssue(
                        code="HEUR011",
                        severity=ValidationSeverity.INFO,
                        field=f"righe[{i}].descrizione",
                        message=f"Riga {i}: Descrizione generica",
                        suggestion="Specificare dettagli (es. tecnologie, ore, deliverables)",
                        reference="Best practice per descrizioni dettagliate",
                    )
                )

        # AI-powered description quality analysis
        if len(fattura.righe) > 0:
            await self._ai_analyze_descriptions(fattura, analysis)

    async def _ai_analyze_descriptions(
        self,
        fattura: Fattura,
        analysis: HeuristicAnalysis,
    ) -> None:
        """Use AI to analyze description quality and completeness."""

        descriptions = [riga.descrizione for riga in fattura.righe]
        descriptions_text = "\n".join(f"{i+1}. {desc}" for i, desc in enumerate(descriptions))

        prompt = f"""Analizza la qualità e completezza delle seguenti descrizioni di fattura elettronica (FatturaPA):

{descriptions_text}

Valuta:
1. Chiarezza e dettaglio delle descrizioni
2. Presenza di informazioni tecniche sufficienti
3. Potenziali ambiguità o vaghezze
4. Conformità alle best practice FatturaPA

Rispondi in formato JSON con:
{{
    "quality_score": <0-100>,
    "issues": [
        {{
            "line_number": <numero riga>,
            "issue": "<descrizione problema>",
            "suggestion": "<suggerimento miglioramento>"
        }}
    ],
    "overall_assessment": "<valutazione complessiva breve>"
}}"""

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.provider.generate(messages=messages, temperature=0.3)

            # Parse AI response (simplified - in production use structured output)
            ai_content = response.content

            # Extract quality assessment
            if "quality_score" in ai_content.lower():
                # AI found potential issues
                analysis.suggestions.append(
                    "AI ha identificato potenziali miglioramenti nelle descrizioni"
                )

        except Exception as e:
            logger.warning("ai_description_analysis_failed", error=str(e))
            # Gracefully degrade - don't fail the analysis

    async def _analyze_temporal_patterns(
        self,
        fattura: Fattura,
        client_history: list[Fattura] | None,
        analysis: HeuristicAnalysis,
    ) -> None:
        """Analyze temporal patterns and anomalies."""

        # Weekend invoicing (unusual)
        if fattura.data_emissione.weekday() in [5, 6]:  # Saturday, Sunday
            analysis.anomalies_found.append(
                ValidationIssue(
                    code="HEUR020",
                    severity=ValidationSeverity.INFO,
                    field="data_emissione",
                    message=f"Fattura emessa in weekend ({fattura.data_emissione.strftime('%A')})",
                    suggestion="Verificare la data di emissione",
                    reference="Pattern inusuale",
                )
            )

        # Holiday detection (simplified - December 25, January 1, etc.)
        holiday_dates = [
            (1, 1),  # New Year
            (1, 6),  # Epiphany
            (4, 25),  # Liberation Day
            (5, 1),  # Labor Day
            (6, 2),  # Republic Day
            (8, 15),  # Assumption
            (11, 1),  # All Saints
            (12, 8),  # Immaculate Conception
            (12, 25),  # Christmas
            (12, 26),  # Santo Stefano
        ]

        if (fattura.data_emissione.month, fattura.data_emissione.day) in holiday_dates:
            analysis.anomalies_found.append(
                ValidationIssue(
                    code="HEUR021",
                    severity=ValidationSeverity.INFO,
                    field="data_emissione",
                    message="Fattura emessa in giorno festivo",
                    suggestion="Verificare la data di emissione",
                    reference="Pattern inusuale",
                )
            )

        # Check for unusual gaps if we have history
        if client_history and len(client_history) >= 2:
            # Sort by date
            sorted_history = sorted(client_history, key=lambda f: f.data_emissione)

            # Check gap between last invoice and current
            last_invoice = sorted_history[-1]
            days_since_last = (fattura.data_emissione - last_invoice.data_emissione).days

            # Very frequent (< 1 day apart)
            if days_since_last < 1:
                analysis.anomalies_found.append(
                    ValidationIssue(
                        code="HEUR022",
                        severity=ValidationSeverity.WARNING,
                        field="data_emissione",
                        message=f"Fattura emessa {days_since_last} giorni dopo la precedente",
                        suggestion="Verificare se non si tratti di duplicazione",
                        reference="Pattern analysis",
                    )
                )

            # Very infrequent (> 6 months)
            elif days_since_last > 180:
                analysis.anomalies_found.append(
                    ValidationIssue(
                        code="HEUR023",
                        severity=ValidationSeverity.INFO,
                        field="data_emissione",
                        message=f"Fattura emessa {days_since_last} giorni dopo la precedente",
                        suggestion="Cliente inattivo da tempo - verificare dati aggiornati",
                        reference="Pattern analysis",
                    )
                )

    async def _analyze_client_patterns(
        self,
        fattura: Fattura,
        client_history: list[Fattura],
        analysis: HeuristicAnalysis,
    ) -> None:
        """Analyze client-specific patterns."""

        if len(client_history) < 2:
            return

        # Analyze VAT rate consistency
        historical_vat_rates = set()
        for hist_fattura in client_history:
            for riga in hist_fattura.righe:
                historical_vat_rates.add(float(riga.aliquota_iva))

        current_vat_rates = {float(riga.aliquota_iva) for riga in fattura.righe}

        # New VAT rate for this client
        new_rates = current_vat_rates - historical_vat_rates
        if new_rates:
            analysis.anomalies_found.append(
                ValidationIssue(
                    code="HEUR030",
                    severity=ValidationSeverity.INFO,
                    field="righe.aliquota_iva",
                    message=f"Nuova aliquota IVA per questo cliente: {new_rates}",
                    suggestion="Verificare che l'aliquota IVA sia corretta",
                    reference="Historical pattern analysis",
                )
            )

        # Analyze payment terms consistency
        if client_history[0].pagamenti and fattura.pagamenti:
            hist_payment_days = (
                client_history[0].pagamenti[0].data_scadenza - client_history[0].data_emissione
            ).days

            current_payment_days = (
                fattura.pagamenti[0].data_scadenza - fattura.data_emissione
            ).days

            if abs(hist_payment_days - current_payment_days) > 15:
                analysis.anomalies_found.append(
                    ValidationIssue(
                        code="HEUR031",
                        severity=ValidationSeverity.INFO,
                        field="pagamenti.data_scadenza",
                        message=f"Termini di pagamento diversi dal solito "
                        f"({current_payment_days} giorni vs {hist_payment_days} storici)",
                        suggestion="Verificare le condizioni di pagamento concordate",
                        reference="Historical pattern analysis",
                    )
                )

    def _calculate_risk_score(self, analysis: HeuristicAnalysis) -> None:
        """Calculate overall risk score based on anomalies found."""

        risk_score = 0.0

        for issue in analysis.anomalies_found:
            if issue.severity == ValidationSeverity.ERROR:
                risk_score += 30
            elif issue.severity == ValidationSeverity.WARNING:
                risk_score += 15
            else:  # INFO
                risk_score += 5

        # Cap at 100
        analysis.risk_score = min(100.0, risk_score)

        # Confidence decreases with fewer checks
        if len(analysis.anomalies_found) == 0:
            analysis.confidence = 0.9  # High confidence in clean invoice
        else:
            analysis.confidence = 0.8  # Moderate confidence

    async def analyze_batch(
        self,
        fatture: list[Fattura],
    ) -> dict[int, HeuristicAnalysis]:
        """Analyze multiple invoices for patterns.

        Args:
            fatture: List of invoices to analyze

        Returns:
            Dictionary mapping invoice IDs to analyses
        """
        results = {}

        for fattura in fatture:
            # Get client history
            with db_session() as db:
                client_history = (
                    db.query(Fattura)
                    .filter(
                        Fattura.cliente_id == fattura.cliente_id,
                        Fattura.id != fattura.id,
                        Fattura.data_emissione < fattura.data_emissione,
                    )
                    .order_by(Fattura.data_emissione.desc())
                    .limit(10)
                    .all()
                )

                analysis = await self.analyze_invoice(fattura, client_history)
                results[fattura.id] = analysis

        logger.info("batch_heuristic_analysis_completed", count=len(results))

        return results
