"""Performance Analytics Agent - Business performance analysis and forecasting."""

import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy import extract

from openfatture.ai.agents.models import PerformanceAnalyticsOutput
from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import PerformanceAnalyticsContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers import BaseLLMProvider
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, Pagamento, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class PerformanceAnalyticsAgent(BaseAgent[PerformanceAnalyticsContext]):
    """
    AI agent for business performance analysis and forecasting.

    Features:
    - Revenue and growth analysis
    - Client and service breakdown
    - Cash collection analysis
    - Revenue forecasting
    - Strategic recommendations
    - Risk identification

    Uses structured output with Pydantic validation.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        use_structured_output: bool = True,
    ) -> None:
        """
        Initialize Performance Analytics agent.

        Args:
            provider: LLM provider instance
            use_structured_output: Use Pydantic structured outputs
        """
        config = AgentConfig(
            name="performance_analytics",
            description="Business performance analysis and forecasting",
            version="1.0.0",
            temperature=0.3,  # Lower temperature for analytical accuracy
            max_tokens=1800,
            tools_enabled=False,
            memory_enabled=False,
            rag_enabled=False,
        )

        super().__init__(config=config, provider=provider)
        self.use_structured_output = use_structured_output

        logger.info(
            "performance_analytics_agent_initialized",
            provider=provider.provider_name,
            model=provider.model,
        )

    async def validate_input(self, context: PerformanceAnalyticsContext) -> tuple[bool, str | None]:
        """
        Validate performance analytics context.

        Args:
            context: Performance analytics context

        Returns:
            Tuple of (is_valid, error_message)
        """
        if context.anno is not None:
            if context.anno < 2000 or context.anno > 2100:
                return False, "Anno deve essere tra 2000 e 2100"

        if context.mese is not None:
            if context.mese < 1 or context.mese > 12:
                return False, "Mese deve essere tra 1 e 12"

        if context.trimestre is not None:
            valid_quarters = ["Q1", "Q2", "Q3", "Q4"]
            if context.trimestre not in valid_quarters:
                return False, f"Trimestre deve essere uno di: {', '.join(valid_quarters)}"

        if context.forecast_periods < 0 or context.forecast_periods > 12:
            return False, "forecast_periods deve essere tra 0 e 12"

        return True, None

    async def _build_prompt(self, context: PerformanceAnalyticsContext) -> list[Message]:
        """
        Build prompt for performance analytics.

        Args:
            context: Performance analytics context

        Returns:
            List of messages for LLM
        """
        # Collect performance data from database
        performance_data = self._collect_performance_data(context)

        # Build system prompt
        system_prompt = """Sei un analista di business esperto specializzato in performance analysis e forecasting.
Il tuo compito è analizzare i dati di performance del business e fornire insight strategici
per migliorare i risultati e guidare la crescita.

Analizza:
- Trend di fatturato e crescita
- Breakdown per cliente e servizio
- Efficienza di incasso (collection rate, DSO)
- Previsioni di fatturato
- Key performance indicators
- Raccomandazioni strategiche
- Fattori di rischio

Rispondi SOLO con JSON valido nel formato PerformanceAnalyticsOutput specificato."""

        # Build user prompt with data
        user_prompt = self._format_performance_data_for_prompt(performance_data, context)

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_prompt),
        ]

        return messages

    def _collect_performance_data(self, context: PerformanceAnalyticsContext) -> dict:
        """
        Collect performance data from database for analysis.

        Args:
            context: Performance analytics context

        Returns:
            Dictionary with performance metrics
        """
        db = get_session()
        try:
            # Determine current period
            if context.anno:
                current_year = context.anno
            else:
                current_year = datetime.now().year

            # Base query
            query_current = db.query(Fattura).filter(
                Fattura.stato != StatoFattura.BOZZA, Fattura.anno == current_year
            )

            # Apply period filters
            if context.trimestre:
                quarter_months = {
                    "Q1": (1, 3),
                    "Q2": (4, 6),
                    "Q3": (7, 9),
                    "Q4": (10, 12),
                }
                start_month, end_month = quarter_months[context.trimestre]
                query_current = query_current.filter(
                    extract("month", Fattura.data_emissione) >= start_month,
                    extract("month", Fattura.data_emissione) <= end_month,
                )
                period_name = f"{context.trimestre} {current_year}"
            elif context.mese:
                query_current = query_current.filter(
                    extract("month", Fattura.data_emissione) == context.mese
                )
                period_name = f"{datetime(2000, context.mese, 1).strftime('%B')} {current_year}"
            else:
                period_name = str(current_year)

            fatture_current = query_current.all()

            # Previous period for comparison
            fatture_previous = []
            if context.compare_to_previous_period:
                if context.trimestre:
                    # Previous quarter
                    prev_quarter_num = int(context.trimestre[1]) - 1
                    if prev_quarter_num == 0:
                        prev_quarter_num = 4
                        prev_year = current_year - 1
                    else:
                        prev_year = current_year
                    prev_quarter = f"Q{prev_quarter_num}"
                    start_month, end_month = quarter_months[prev_quarter]

                    query_prev = db.query(Fattura).filter(
                        Fattura.stato != StatoFattura.BOZZA,
                        Fattura.anno == prev_year,
                        extract("month", Fattura.data_emissione) >= start_month,
                        extract("month", Fattura.data_emissione) <= end_month,
                    )
                elif context.mese:
                    # Previous month
                    prev_month = context.mese - 1 if context.mese > 1 else 12
                    prev_year = current_year if context.mese > 1 else current_year - 1

                    query_prev = db.query(Fattura).filter(
                        Fattura.stato != StatoFattura.BOZZA,
                        Fattura.anno == prev_year,
                        extract("month", Fattura.data_emissione) == prev_month,
                    )
                else:
                    # Previous year
                    query_prev = db.query(Fattura).filter(
                        Fattura.stato != StatoFattura.BOZZA, Fattura.anno == current_year - 1
                    )

                fatture_previous = query_prev.all()

            # Calculate metrics
            total_revenue = sum(float(f.totale) for f in fatture_current)
            total_revenue_prev = sum(float(f.totale) for f in fatture_previous)

            # Growth calculation
            if total_revenue_prev > 0:
                revenue_growth = ((total_revenue - total_revenue_prev) / total_revenue_prev) * 100
            else:
                revenue_growth = 0.0

            # Client breakdown
            revenue_by_client: defaultdict[str, float] = defaultdict(float)
            for f in fatture_current:
                if f.cliente:
                    revenue_by_client[f.cliente.denominazione] += float(f.totale)

            # Service breakdown (from invoice lines)
            revenue_by_service: defaultdict[str, float] = defaultdict(float)
            for f in fatture_current:
                for riga in f.righe:
                    service_name = riga.descrizione[:50] if riga.descrizione else "Unknown"
                    revenue_by_service[service_name] += float(riga.totale)

            # Cash collection analysis
            fattura_ids = [f.id for f in fatture_current]
            pagamenti = []
            if fattura_ids:
                pagamenti = db.query(Pagamento).filter(Pagamento.fattura_id.in_(fattura_ids)).all()

            total_due = sum(float(p.importo) for p in pagamenti)
            total_paid = sum(float(p.importo_pagato) for p in pagamenti)
            cash_collection_rate = total_paid / total_due if total_due > 0 else 0.0

            # Average collection days
            collection_days = []
            for p in pagamenti:
                if p.data_pagamento and p.data_scadenza:
                    days = (p.data_pagamento - p.data_scadenza).days
                    collection_days.append(days)
            avg_collection_days = (
                sum(collection_days) / len(collection_days) if collection_days else 0
            )

            data = {
                "period": period_name,
                "current": {
                    "revenue": total_revenue,
                    "invoices_count": len(fatture_current),
                    "avg_invoice_value": (
                        total_revenue / len(fatture_current) if fatture_current else 0
                    ),
                },
                "previous": {
                    "revenue": total_revenue_prev,
                    "invoices_count": len(fatture_previous),
                },
                "growth": {
                    "revenue_growth_pct": revenue_growth,
                },
                "breakdown": {
                    "by_client": dict(
                        sorted(revenue_by_client.items(), key=lambda x: x[1], reverse=True)[:10]
                    ),
                    "by_service": dict(
                        sorted(revenue_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
                    ),
                },
                "cash": {
                    "collection_rate": cash_collection_rate,
                    "avg_collection_days": avg_collection_days,
                    "total_due": total_due,
                    "total_paid": total_paid,
                },
            }

            return data

        finally:
            db.close()

    def _format_performance_data_for_prompt(
        self, data: dict, context: PerformanceAnalyticsContext
    ) -> str:
        """
        Format performance data for LLM prompt.

        Args:
            data: Aggregated performance data
            context: Analysis context

        Returns:
            Formatted prompt string
        """
        lines = ["Analizza le seguenti performance di business:\n"]

        # Period
        lines.append(f"Periodo: {data['period']}\n")

        # Current period metrics
        current = data["current"]
        lines.append("Performance periodo corrente:")
        lines.append(f"  Fatturato: €{current['revenue']:,.2f}")
        lines.append(f"  Numero fatture: {current['invoices_count']}")
        lines.append(f"  Valore medio fattura: €{current['avg_invoice_value']:,.2f}\n")

        # Growth
        if context.compare_to_previous_period:
            previous = data["previous"]
            growth = data["growth"]
            lines.append("Confronto periodo precedente:")
            lines.append(f"  Fatturato precedente: €{previous['revenue']:,.2f}")
            lines.append(f"  Crescita: {growth['revenue_growth_pct']:+.1f}%\n")

        # Client breakdown
        if context.include_client_breakdown:
            breakdown = data["breakdown"]
            lines.append("Top 10 clienti per fatturato:")
            for client, revenue in list(breakdown["by_client"].items())[:10]:
                pct = (revenue / current["revenue"]) * 100 if current["revenue"] > 0 else 0
                lines.append(f"  {client}: €{revenue:,.2f} ({pct:.1f}%)")
            lines.append("")

        # Service breakdown
        if context.include_service_breakdown:
            lines.append("Top 10 servizi per fatturato:")
            for service, revenue in list(breakdown["by_service"].items())[:10]:
                pct = (revenue / current["revenue"]) * 100 if current["revenue"] > 0 else 0
                lines.append(f"  {service[:40]}: €{revenue:,.2f} ({pct:.1f}%)")
            lines.append("")

        # Cash metrics
        if context.include_cash_analysis:
            cash = data["cash"]
            lines.append("Analisi cash collection:")
            lines.append(f"  Tasso di incasso: {cash['collection_rate']:.1%}")
            lines.append(f"  Giorni medi incasso: {cash['avg_collection_days']:.1f}")
            lines.append(f"  Totale da incassare: €{cash['total_due']:,.2f}")
            lines.append(f"  Totale incassato: €{cash['total_paid']:,.2f}\n")

        # Forecast request
        if context.include_forecast:
            lines.append(
                f"\nFornisci previsione fatturato per i prossimi {context.forecast_periods} periodi."
            )

        lines.append(
            "\nFornisci analisi completa con insights, trend, raccomandazioni e fattori di rischio."
        )

        return "\n".join(lines)

    async def _parse_response(
        self,
        response: AgentResponse,
        context: PerformanceAnalyticsContext,
    ) -> AgentResponse:
        """
        Parse and validate LLM response.

        Args:
            response: Raw LLM response
            context: Performance analytics context

        Returns:
            Processed AgentResponse with metadata
        """
        if self.use_structured_output:
            try:
                data = json.loads(response.content)
                model = PerformanceAnalyticsOutput(**data)

                response.metadata["parsed_model"] = model.model_dump()
                response.metadata["is_structured"] = True

                logger.info(
                    "structured_output_parsed",
                    agent=self.config.name,
                    period=model.period,
                    revenue=model.total_revenue,
                    growth=model.revenue_growth,
                )

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(
                    "structured_output_parse_failed",
                    agent=self.config.name,
                    error=str(e),
                )
                response.metadata["is_structured"] = False
        else:
            response.metadata["is_structured"] = False

        return response
