"""Invoice Analysis Agent - Analyzes invoice patterns, anomalies, and pricing."""

import json
from collections import defaultdict
from decimal import Decimal
from typing import Any

from openfatture.ai.agents.models import InvoiceAnalysisOutput
from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import InvoiceAnalysisContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers import BaseLLMProvider
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class InvoiceAnalysisAgent(BaseAgent[InvoiceAnalysisContext]):
    """
    AI agent for analyzing invoice patterns and providing business insights.

    Features:
    - Pattern analysis across time periods
    - Anomaly detection (outliers, unusual patterns)
    - Pricing optimization suggestions
    - Client concentration risk analysis
    - Revenue trend identification

    Uses structured output with Pydantic validation.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        use_structured_output: bool = True,
    ) -> None:
        """
        Initialize Invoice Analysis agent.

        Args:
            provider: LLM provider instance
            use_structured_output: Use Pydantic structured outputs
        """
        config = AgentConfig(
            name="invoice_analysis",
            description="Analyzes invoice patterns and provides business insights",
            version="1.0.0",
            temperature=0.3,  # Lower temperature for analytical tasks
            max_tokens=1500,
            tools_enabled=False,
            memory_enabled=False,
            rag_enabled=False,
        )

        super().__init__(config=config, provider=provider)
        self.use_structured_output = use_structured_output

        logger.info(
            "invoice_analysis_agent_initialized",
            provider=provider.provider_name,
            model=provider.model,
        )

    async def validate_input(self, context: InvoiceAnalysisContext) -> tuple[bool, str | None]:
        """
        Validate invoice analysis context.

        Args:
            context: Invoice analysis context

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation - context must have some analysis parameters
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

        return True, None

    async def _build_prompt(self, context: InvoiceAnalysisContext) -> list[Message]:
        """
        Build prompt for invoice analysis.

        Args:
            context: Invoice analysis context

        Returns:
            List of messages for LLM
        """
        # Collect invoice data from database
        invoice_data = self._collect_invoice_data(context)

        # Build system prompt
        system_prompt = """Sei un analista di business esperto specializzato in analisi di fatturazione.
Il tuo compito è analizzare i dati delle fatture e fornire insight actionable per ottimizzare
il business del professionista.

Fornisci analisi su:
- Pattern e trend del fatturato
- Servizi più redditizi
- Anomalie e outlier
- Suggerimenti per ottimizzazione prezzi
- Rischi di concentrazione clienti
- Raccomandazioni strategiche

Rispondi SOLO con JSON valido nel formato InvoiceAnalysisOutput specificato."""

        # Build user prompt with data
        user_prompt = self._format_invoice_data_for_prompt(invoice_data, context)

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_prompt),
        ]

        return messages

    def _collect_invoice_data(self, context: InvoiceAnalysisContext) -> dict:
        """
        Collect invoice data from database for analysis.

        Args:
            context: Invoice analysis context

        Returns:
            Dictionary with aggregated invoice data
        """
        db = get_session()
        try:
            # Base query - exclude drafts
            query = db.query(Fattura).filter(Fattura.stato != StatoFattura.BOZZA)

            # Apply filters
            if context.anno:
                query = query.filter(Fattura.anno == context.anno)
            if context.mese:
                from sqlalchemy import extract

                query = query.filter(extract("month", Fattura.data_emissione) == context.mese)
            if context.cliente_id:
                query = query.filter(Fattura.cliente_id == context.cliente_id)
            if context.min_importo:
                query = query.filter(Fattura.totale >= Decimal(str(context.min_importo)))
            if context.max_importo:
                query = query.filter(Fattura.totale <= Decimal(str(context.max_importo)))

            fatture = query.all()

            # Aggregate data - explicitly typed defaultdicts for mypy
            monthly_revenue: defaultdict[str, float] = defaultdict(float)
            service_types: defaultdict[str, dict[str, float]] = defaultdict(
                lambda: {"count": 0, "revenue": 0.0}
            )

            data: dict[str, Any] = {
                "total_invoices": len(fatture),
                "invoices": [],
                "clients": {},
                "monthly_revenue": monthly_revenue,
                "service_types": service_types,
            }

            for f in fatture:
                # Invoice details
                invoice_info = {
                    "id": f.id,
                    "numero": f"{f.numero}/{f.anno}",
                    "data": f.data_emissione.isoformat() if f.data_emissione else None,
                    "cliente_id": f.cliente_id,
                    "cliente_nome": f.cliente.denominazione if f.cliente else "Unknown",
                    "totale": float(f.totale),
                    "imponibile": float(f.imponibile),
                    "iva": float(f.iva),
                }
                data["invoices"].append(invoice_info)

                # Client aggregation
                if f.cliente_id:
                    if f.cliente_id not in data["clients"]:
                        data["clients"][f.cliente_id] = {
                            "nome": f.cliente.denominazione if f.cliente else "Unknown",
                            "count": 0,
                            "revenue": 0.0,
                        }
                    data["clients"][f.cliente_id]["count"] += 1
                    data["clients"][f.cliente_id]["revenue"] += float(f.totale)

                # Monthly revenue
                if f.data_emissione:
                    month_key = f.data_emissione.strftime("%Y-%m")
                    data["monthly_revenue"][month_key] += float(f.totale)

                # Service analysis from invoice lines
                for riga in f.righe:
                    desc_short = riga.descrizione[:50] if riga.descrizione else "Unknown"
                    data["service_types"][desc_short]["count"] += 1
                    data["service_types"][desc_short]["revenue"] += float(riga.totale)

            return data

        finally:
            db.close()

    def _format_invoice_data_for_prompt(self, data: dict, context: InvoiceAnalysisContext) -> str:
        """
        Format invoice data for LLM prompt.

        Args:
            data: Aggregated invoice data
            context: Analysis context

        Returns:
            Formatted prompt string
        """
        lines = ["Analizza i seguenti dati di fatturazione:\n"]

        # Summary
        total_revenue = sum(inv["totale"] for inv in data["invoices"])
        avg_invoice = total_revenue / len(data["invoices"]) if data["invoices"] else 0

        lines.append(f"Periodo: {context.anno or 'Tutti gli anni'}")
        lines.append(f"Totale fatture: {data['total_invoices']}")
        lines.append(f"Fatturato totale: €{total_revenue:,.2f}")
        lines.append(f"Valore medio fattura: €{avg_invoice:,.2f}\n")

        # Monthly breakdown
        if data["monthly_revenue"]:
            lines.append("Fatturato mensile:")
            for month, revenue in sorted(data["monthly_revenue"].items()):
                lines.append(f"  {month}: €{revenue:,.2f}")
            lines.append("")

        # Top clients
        if data["clients"]:
            top_clients = sorted(
                data["clients"].items(), key=lambda x: x[1]["revenue"], reverse=True
            )[:5]
            lines.append("Top 5 clienti per fatturato:")
            for client_id, info in top_clients:
                lines.append(f"  {info['nome']}: €{info['revenue']:,.2f} ({info['count']} fatture)")
            lines.append("")

        # Top services
        if data["service_types"]:
            top_services = sorted(
                data["service_types"].items(), key=lambda x: x[1]["revenue"], reverse=True
            )[:5]
            lines.append("Top 5 servizi per fatturato:")
            for service, info in top_services:
                lines.append(f"  {service}: €{info['revenue']:,.2f} ({info['count']}x)")
            lines.append("")

        lines.append("\nFornisci analisi dettagliata con insights, anomalie e raccomandazioni.")

        return "\n".join(lines)

    async def _parse_response(
        self,
        response: AgentResponse,
        context: InvoiceAnalysisContext,
    ) -> AgentResponse:
        """
        Parse and validate LLM response.

        Args:
            response: Raw LLM response
            context: Invoice analysis context

        Returns:
            Processed AgentResponse with metadata
        """
        if self.use_structured_output:
            try:
                data = json.loads(response.content)
                model = InvoiceAnalysisOutput(**data)

                response.metadata["parsed_model"] = model.model_dump()
                response.metadata["is_structured"] = True

                logger.info(
                    "structured_output_parsed",
                    agent=self.config.name,
                    invoices_analyzed=model.total_invoices_analyzed,
                    anomalies_count=len(model.anomalies),
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
