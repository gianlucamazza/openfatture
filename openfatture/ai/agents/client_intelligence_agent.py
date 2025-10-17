"""Client Intelligence Agent - Analyzes client behavior and relationship health."""

import json
from datetime import datetime, timedelta

from openfatture.ai.agents.models import ClientIntelligenceOutput
from openfatture.ai.domain import AgentConfig, BaseAgent, Message, Role
from openfatture.ai.domain.context import ClientIntelligenceContext
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers import BaseLLMProvider
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente, Fattura, Pagamento, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ClientIntelligenceAgent(BaseAgent[ClientIntelligenceContext]):
    """
    AI agent for analyzing client behavior and relationship health.

    Features:
    - Payment behavior analysis
    - Relationship health scoring
    - Churn risk prediction
    - Growth potential assessment
    - Personalized recommendations

    Uses structured output with Pydantic validation.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        use_structured_output: bool = True,
    ) -> None:
        """
        Initialize Client Intelligence agent.

        Args:
            provider: LLM provider instance
            use_structured_output: Use Pydantic structured outputs
        """
        config = AgentConfig(
            name="client_intelligence",
            description="Analyzes client behavior and relationship health",
            version="1.0.0",
            temperature=0.4,  # Balanced for analytical and creative insights
            max_tokens=1200,
            tools_enabled=False,
            memory_enabled=False,
            rag_enabled=False,
        )

        super().__init__(config=config, provider=provider)
        self.use_structured_output = use_structured_output

        logger.info(
            "client_intelligence_agent_initialized",
            provider=provider.provider_name,
            model=provider.model,
        )

    async def validate_input(self, context: ClientIntelligenceContext) -> tuple[bool, str | None]:
        """
        Validate client intelligence context.

        Args:
            context: Client intelligence context

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Require cliente_id
        if not context.cliente_id or context.cliente_id < 1:
            return False, "cliente_id è richiesto e deve essere positivo"

        if context.mesi_analisi < 1 or context.mesi_analisi > 60:
            return False, "mesi_analisi deve essere tra 1 e 60"

        return True, None

    async def _build_prompt(self, context: ClientIntelligenceContext) -> list[Message]:
        """
        Build prompt for client intelligence analysis.

        Args:
            context: Client intelligence context

        Returns:
            List of messages for LLM
        """
        # Collect client data from database
        client_data = self._collect_client_data(context)

        # Build system prompt
        system_prompt = """Sei un analista di business esperto specializzato in gestione clienti e CRM.
Il tuo compito è analizzare il comportamento del cliente e fornire insight actionable per
migliorare la relazione commerciale e prevenire l'abbandono (churn).

Analizza:
- Comportamento pagamenti (puntualità, ritardi, pattern)
- Salute della relazione (frequenza ordini, valore, engagement)
- Rischio di churn (segnali di disimpegno)
- Potenziale di crescita (upsell, cross-sell opportunities)
- Raccomandazioni personalizzate per il cliente

Rispondi SOLO con JSON valido nel formato ClientIntelligenceOutput specificato."""

        # Build user prompt with data
        user_prompt = self._format_client_data_for_prompt(client_data, context)

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_prompt),
        ]

        return messages

    def _collect_client_data(self, context: ClientIntelligenceContext) -> dict:
        """
        Collect client data from database for analysis.

        Args:
            context: Client intelligence context

        Returns:
            Dictionary with client analysis data
        """
        db = get_session()
        try:
            # Get client
            cliente = db.query(Cliente).filter(Cliente.id == context.cliente_id).first()
            if not cliente:
                return {"error": f"Cliente {context.cliente_id} non trovato"}

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=context.mesi_analisi * 30)

            # Get invoices
            fatture = (
                db.query(Fattura)
                .filter(
                    Fattura.cliente_id == context.cliente_id,
                    Fattura.stato != StatoFattura.BOZZA,
                    Fattura.data_emissione >= start_date.date(),
                )
                .order_by(Fattura.data_emissione.desc())
                .all()
            )

            # Get payments
            fattura_ids = [f.id for f in fatture]
            pagamenti = []
            if fattura_ids:
                pagamenti = db.query(Pagamento).filter(Pagamento.fattura_id.in_(fattura_ids)).all()

            # Calculate metrics
            total_revenue = sum(float(f.totale) for f in fatture)
            avg_invoice_value = total_revenue / len(fatture) if fatture else 0

            # Payment analysis
            payment_delays = []
            for p in pagamenti:
                if p.data_pagamento and p.data_scadenza:
                    delay = (p.data_pagamento - p.data_scadenza).days
                    payment_delays.append(delay)

            avg_payment_days = sum(payment_delays) / len(payment_delays) if payment_delays else 0
            late_payments = sum(1 for d in payment_delays if d > 0)

            # Revenue trends (last 6 months)
            monthly_revenue = {}
            for f in fatture:
                if f.data_emissione:
                    month_key = f.data_emissione.strftime("%Y-%m")
                    if month_key not in monthly_revenue:
                        monthly_revenue[month_key] = 0.0
                    monthly_revenue[month_key] += float(f.totale)

            # Recent activity
            last_invoice_date = fatture[0].data_emissione if fatture else None
            days_since_last_invoice = (
                (datetime.now().date() - last_invoice_date).days if last_invoice_date else None
            )

            data = {
                "client": {
                    "id": cliente.id,
                    "nome": cliente.denominazione,
                    "email": cliente.email or "N/A",
                    "pec": cliente.pec or "N/A",
                    "partita_iva": cliente.partita_iva or "N/A",
                },
                "summary": {
                    "total_revenue": total_revenue,
                    "invoice_count": len(fatture),
                    "avg_invoice_value": avg_invoice_value,
                    "period_months": context.mesi_analisi,
                },
                "payment_behavior": {
                    "avg_payment_days": avg_payment_days,
                    "late_payments_count": late_payments,
                    "total_payments": len(payment_delays),
                    "late_payment_rate": (
                        late_payments / len(payment_delays) if payment_delays else 0
                    ),
                },
                "activity": {
                    "last_invoice_date": (
                        last_invoice_date.isoformat() if last_invoice_date else None
                    ),
                    "days_since_last_invoice": days_since_last_invoice,
                    "monthly_revenue": monthly_revenue,
                },
                "comparative": {
                    "avg_payment_days_all": context.avg_payment_days_all_clients or 30.0,
                    "avg_revenue_per_client": context.avg_revenue_per_client or 10000.0,
                },
            }

            return data

        finally:
            db.close()

    def _format_client_data_for_prompt(self, data: dict, context: ClientIntelligenceContext) -> str:
        """
        Format client data for LLM prompt.

        Args:
            data: Aggregated client data
            context: Analysis context

        Returns:
            Formatted prompt string
        """
        if "error" in data:
            return f"Errore: {data['error']}"

        lines = ["Analizza il seguente cliente:\n"]

        # Client info
        client = data["client"]
        lines.append(f"Cliente: {client['nome']} (ID: {client['id']})")
        lines.append(f"P.IVA: {client['partita_iva']}")
        lines.append(f"Email: {client['email']}\n")

        # Summary
        summary = data["summary"]
        lines.append("Riepilogo attività:")
        lines.append(f"  Periodo analisi: {summary['period_months']} mesi")
        lines.append(f"  Fatturato totale: €{summary['total_revenue']:,.2f}")
        lines.append(f"  Numero fatture: {summary['invoice_count']}")
        lines.append(f"  Valore medio fattura: €{summary['avg_invoice_value']:,.2f}\n")

        # Payment behavior
        payment = data["payment_behavior"]
        lines.append("Comportamento pagamenti:")
        lines.append(f"  Giorni medi pagamento: {payment['avg_payment_days']:.1f}")
        lines.append(
            f"  Pagamenti in ritardo: {payment['late_payments_count']}/{payment['total_payments']}"
        )
        lines.append(f"  Tasso ritardi: {payment['late_payment_rate']:.1%}\n")

        # Activity
        activity = data["activity"]
        if activity["last_invoice_date"]:
            lines.append("Attività recente:")
            lines.append(f"  Ultima fattura: {activity['last_invoice_date']}")
            lines.append(f"  Giorni dall'ultima fattura: {activity['days_since_last_invoice']}")
        lines.append("")

        # Monthly trends
        if activity["monthly_revenue"]:
            lines.append("Fatturato mensile (ultimi 6 mesi):")
            for month, revenue in sorted(activity["monthly_revenue"].items())[-6:]:
                lines.append(f"  {month}: €{revenue:,.2f}")
            lines.append("")

        # Comparative
        comp = data["comparative"]
        lines.append("Dati comparativi (vs media tutti i clienti):")
        lines.append(f"  Giorni pagamento medi (tutti): {comp['avg_payment_days_all']:.1f}")
        lines.append(f"  Fatturato medio cliente (tutti): €{comp['avg_revenue_per_client']:,.2f}\n")

        lines.append(
            "\nFornisci analisi dettagliata con scoring, rischio churn, potenziale, raccomandazioni."
        )

        return "\n".join(lines)

    async def _parse_response(
        self,
        response: AgentResponse,
        context: ClientIntelligenceContext,
    ) -> AgentResponse:
        """
        Parse and validate LLM response.

        Args:
            response: Raw LLM response
            context: Client intelligence context

        Returns:
            Processed AgentResponse with metadata
        """
        if self.use_structured_output:
            try:
                data = json.loads(response.content)
                model = ClientIntelligenceOutput(**data)

                response.metadata["parsed_model"] = model.model_dump()
                response.metadata["is_structured"] = True

                logger.info(
                    "structured_output_parsed",
                    agent=self.config.name,
                    client_id=model.client_id,
                    relationship_score=model.relationship_score,
                    churn_risk=model.churn_risk,
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
