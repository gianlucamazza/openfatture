"""Invoice Creation Workflow using LangGraph.

Multi-agent workflow for creating invoices with AI assistance and human oversight.

Workflow Steps:
1. User provides brief description
2. Description Agent expands to professional description
3. [Optional] Human approves description
4. Tax Advisor suggests VAT rate and treatment
5. [Optional] Human approves tax treatment
6. Compliance Checker validates invoice data
7. [Conditional] Human approves if warnings/errors
8. Create invoice in database
9. Generate FatturaPA XML

Conditional Routing:
- Skip human checkpoints if confidence > threshold
- Require approval on low confidence or errors
- Fall back to manual mode on critical failures

Example:
    >>> workflow = InvoiceCreationWorkflow()
    >>> result = await workflow.execute(
    ...     user_input="consulenza DevOps 3 giorni cliente Acme",
    ...     client_id=123,
    ...     require_approvals=True
    ... )
    >>> print(f"Created invoice #{result.invoice_id}")
"""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from importlib import import_module
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from openfatture.ai.agents.compliance import ComplianceChecker, ComplianceLevel
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
from openfatture.ai.domain.context import InvoiceContext, TaxContext
from openfatture.ai.orchestration.states import (
    AgentResult,
    AgentType,
    ApprovalDecision,
    InvoiceCreationState,
)
from openfatture.ai.providers import BaseLLMProvider, create_provider
from openfatture.core.fatture.service import InvoiceService
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    Pagamento,
    RigaFattura,
    StatoFattura,
    StatoPagamento,
    TipoDocumento,
)
from openfatture.utils.config import Settings, get_settings
from openfatture.utils.datetime import utc_now
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def _get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() before running workflows.")
    return SessionLocal()


if TYPE_CHECKING:
    from langgraph.graph import END as _END
    from langgraph.graph import StateGraph as _StateGraph
else:
    _graph_module = import_module("langgraph.graph")
    _StateGraph = _graph_module.StateGraph
    _END = _graph_module.END

StateGraph = _StateGraph
END = _END


class InvoiceCreationWorkflow:
    """LangGraph-based invoice creation workflow.

    This workflow orchestrates multiple AI agents with optional human oversight
    to create validated, compliant invoices.

    Features:
    - Multi-agent collaboration (Description, Tax, Compliance)
    - Conditional routing based on confidence scores
    - Human approval checkpoints (configurable)
    - Error handling and recovery
    - State persistence for resume capability
    - Comprehensive logging and tracking

    Example:
        >>> workflow = InvoiceCreationWorkflow()
        >>> result = await workflow.execute(
        ...     user_input="sviluppo API REST 40 ore",
        ...     client_id=456,
        ...     imponibile=3200,
        ...     hours=40,
        ...     hourly_rate=80,
        ... )
    """

    def __init__(
        self,
        confidence_threshold: float = 0.85,
        enable_checkpointing: bool = True,
        settings: Settings | None = None,
        provider: BaseLLMProvider | None = None,
        validate_xml: bool = True,
    ):
        """Initialize workflow.

        Args:
            confidence_threshold: Minimum confidence to skip human approval
            enable_checkpointing: Enable state persistence for resume
        """
        self.confidence_threshold = confidence_threshold
        self.enable_checkpointing = enable_checkpointing
        self.settings = settings or get_settings()
        self.validate_xml = validate_xml

        # AI provider (shared across agents)
        self.ai_provider = provider or create_provider()

        # Agents
        self.description_agent = InvoiceAssistantAgent(provider=self.ai_provider)
        self.tax_agent = TaxAdvisorAgent(provider=self.ai_provider)
        self.compliance_checker = ComplianceChecker(level=ComplianceLevel.STANDARD)
        self.invoice_service = InvoiceService(self.settings)

        # Build graph
        self.graph: Any = self._build_graph()

        logger.info(
            "invoice_creation_workflow_initialized",
            confidence_threshold=confidence_threshold,
            validate_xml=validate_xml,
            provider=self.ai_provider.provider_name,
        )

    def _build_graph(self) -> Any:
        """Build LangGraph state machine.

        Graph structure:
        START → description_agent → [approval_check] → tax_agent → [approval_check]
              → compliance_check → [approval_check] → create_invoice → END

        Conditional edges:
        - Skip approval if confidence > threshold
        - Require approval on errors/warnings
        - Abort on critical failures
        """
        # Create graph
        workflow = StateGraph(InvoiceCreationState)

        # Add nodes
        workflow.add_node("enrich_context", self._enrich_context_node)
        workflow.add_node("description_agent", self._description_agent_node)
        workflow.add_node("description_approval", self._description_approval_node)
        workflow.add_node("tax_agent", self._tax_agent_node)
        workflow.add_node("tax_approval", self._tax_approval_node)
        workflow.add_node("compliance_check", self._compliance_check_node)
        workflow.add_node("compliance_approval", self._compliance_approval_node)
        workflow.add_node("create_invoice", self._create_invoice_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Entry point
        workflow.set_entry_point("enrich_context")

        # Sequential edges
        workflow.add_edge("enrich_context", "description_agent")

        # Conditional edge: description approval
        workflow.add_conditional_edges(
            "description_agent",
            self._should_approve_description,
            {
                "approve": "description_approval",
                "skip": "tax_agent",
                "error": "handle_error",
            },
        )

        workflow.add_edge("description_approval", "tax_agent")

        # Conditional edge: tax approval
        workflow.add_conditional_edges(
            "tax_agent",
            self._should_approve_tax,
            {
                "approve": "tax_approval",
                "skip": "compliance_check",
                "error": "handle_error",
            },
        )

        workflow.add_edge("tax_approval", "compliance_check")

        # Conditional edge: compliance approval
        workflow.add_conditional_edges(
            "compliance_check",
            self._should_approve_compliance,
            {
                "approve": "compliance_approval",
                "skip": "create_invoice",
                "error": "handle_error",
            },
        )

        workflow.add_edge("compliance_approval", "create_invoice")

        # End
        workflow.add_edge("create_invoice", END)
        workflow.add_edge("handle_error", END)

        # Compile with checkpointing
        if self.enable_checkpointing:
            from importlib import import_module

            checkpoint_module = import_module("langgraph.checkpoint")
            memory_saver_cls = getattr(checkpoint_module, "MemorySaver", None)
            if memory_saver_cls is None:
                raise RuntimeError("LangGraph MemorySaver unavailable")
            checkpointer = memory_saver_cls()
            return workflow.compile(checkpointer=checkpointer)
        return workflow.compile()

    # ========================================================================
    # Node Implementations
    # ========================================================================

    async def _enrich_context_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Enrich state with business context."""
        logger.info("enriching_context", workflow_id=state.workflow_id)

        db = _get_session()
        try:
            # Load year-to-date statistics
            from sqlalchemy import extract, func

            current_year = utc_now().year

            cliente = db.query(Cliente).filter(Cliente.id == state.client_id).first()
            if not cliente:
                raise ValueError(f"Cliente {state.client_id} non trovato")

            state.context["total_invoices_ytd"] = (
                db.query(func.count(Fattura.id))
                .filter(extract("year", Fattura.data_emissione) == current_year)
                .scalar()
                or 0
            )

            state.context["total_revenue_ytd"] = (
                db.query(func.sum(Fattura.totale))
                .filter(extract("year", Fattura.data_emissione) == current_year)
                .scalar()
                or 0.0
            )

            # Basic client snapshot for downstream agents
            state.metadata["cliente_denominazione"] = cliente.denominazione
            state.metadata["cliente_paese"] = cliente.nazione
            state.metadata["cliente"] = {
                "id": cliente.id,
                "denominazione": cliente.denominazione,
                "paese": cliente.nazione,
                "codice_destinatario": cliente.codice_destinatario,
                "pec": cliente.pec,
                "partita_iva": cliente.partita_iva,
            }

            # Set invoice and payment dates
            issue_date = state.invoice_date or date.today()
            state.invoice_date = issue_date
            state.payment_due_date = state.payment_due_date or (
                issue_date + timedelta(days=state.payment_terms_days)
            )
            state.context["default_payment_terms"] = state.payment_terms_days

            state.status = "in_progress"
            state.updated_at = utc_now()

            logger.info(
                "context_enriched",
                workflow_id=state.workflow_id,
                invoices_ytd=state.context["total_invoices_ytd"],
                cliente_id=cliente.id,
            )

            return state

        except Exception as e:
            logger.error(
                "context_enrichment_failed",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Failed to enrich context: {e}")
            return state

        finally:
            db.close()

    async def _description_agent_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Execute Description Agent."""
        logger.info("executing_description_agent", workflow_id=state.workflow_id)

        try:
            db = _get_session()
            try:
                cliente = db.query(Cliente).filter(Cliente.id == state.client_id).first()
            finally:
                db.close()

            if not cliente:
                raise ValueError(f"Cliente {state.client_id} non trovato")

            # Create context
            context = InvoiceContext(
                user_input=state.user_input,
                servizio_base=state.user_input,
                ore_lavorate=state.hours,
                tariffa_oraria=float(state.hourly_rate) if state.hourly_rate is not None else None,
                cliente=cliente,
            )

            # Execute agent
            response = await self.description_agent.execute(context)

            # Extract result
            if response.status.value == "success":
                content = response.content
                confidence = response.metadata.get("confidence", 0.8)
                structured = response.metadata.get("parsed_model")

                state.metadata["description_structured"] = structured or {}

                state.description_result = AgentResult(
                    agent_type=AgentType.DESCRIPTION,
                    success=True,
                    content=content,
                    confidence=confidence,
                    metadata=response.metadata,
                )

                # Capture duration from structured model if not provided
                if structured and not state.hours:
                    duration = structured.get("durata_ore")
                    if duration:
                        state.hours = float(duration)

                logger.info(
                    "description_agent_completed",
                    workflow_id=state.workflow_id,
                    confidence=confidence,
                )
            else:
                state.add_error(f"Description agent failed: {response.error}")

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error(
                "description_agent_error",
                workflow_id=state.workflow_id,
                error=str(e),
            )
            state.add_error(f"Description agent error: {e}")
            return state

    async def _description_approval_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Human approval checkpoint for description."""
        logger.info("awaiting_description_approval", workflow_id=state.workflow_id)

        state.status = "awaiting_approval"

        # In real implementation, this would trigger UI or CLI prompt
        # For now, we simulate approval based on confidence
        if (
            state.description_result
            and state.description_result.confidence > self.confidence_threshold
        ):
            from openfatture.ai.orchestration.states import HumanReview

            state.description_review = HumanReview(
                decision=ApprovalDecision.APPROVE,
                feedback="Auto-approved (high confidence)",
                reviewer="system",
            )
            state.status = "approved"
        else:
            # Would pause here for human input
            state.status = "awaiting_approval"

        state.updated_at = utc_now()
        return state

    async def _tax_agent_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Execute Tax Advisor Agent."""
        logger.info("executing_tax_agent", workflow_id=state.workflow_id)

        try:
            # Get description from previous step
            description = (
                state.description_result.content if state.description_result else state.user_input
            )

            cliente_data = state.metadata.get("cliente", {})
            cliente_paese = cliente_data.get("paese", "IT") or "IT"
            codice_dest = (cliente_data.get("codice_destinatario") or "").upper()

            cliente_pa = codice_dest == "0000000"
            cliente_estero = cliente_paese != "IT"

            # Create tax context
            tax_context = TaxContext(
                user_input=description,
                tipo_servizio=description,
                importo=float(state.imponibile_target),
                cliente_pa=cliente_pa,
                cliente_estero=cliente_estero,
                paese_cliente=cliente_paese,
            )

            # Execute agent
            response = await self.tax_agent.execute(tax_context)

            if response.status.value == "success":
                state.tax_result = AgentResult(
                    agent_type=AgentType.TAX_ADVISOR,
                    success=True,
                    content=response.content,
                    confidence=response.metadata.get("confidence", 0.8),
                    metadata=response.metadata,
                )

                structured = response.metadata.get("parsed_model")
                if structured:
                    state.tax_details = structured
                    aliquota = structured.get("aliquota_iva")
                    if aliquota is not None:
                        state.vat_rate = Decimal(str(aliquota))
                    if structured.get("note_fattura"):
                        state.metadata["nota_fattura"] = structured["note_fattura"]

                logger.info(
                    "tax_agent_completed",
                    workflow_id=state.workflow_id,
                    confidence=state.tax_result.confidence,
                )
            else:
                state.add_error(f"Tax agent failed: {response.error}")

            state.updated_at = utc_now()
            return state

        except Exception as e:
            logger.error("tax_agent_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Tax agent error: {e}")
            return state

    async def _tax_approval_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Human approval checkpoint for tax suggestion."""
        logger.info("awaiting_tax_approval", workflow_id=state.workflow_id)

        # Simulate approval logic
        if state.tax_result and state.tax_result.confidence > self.confidence_threshold:
            from openfatture.ai.orchestration.states import HumanReview

            state.tax_review = HumanReview(
                decision=ApprovalDecision.APPROVE,
                feedback="Auto-approved (high confidence)",
                reviewer="system",
            )
            state.status = "approved"
        else:
            state.status = "awaiting_approval"

        state.updated_at = utc_now()
        return state

    async def _compliance_check_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Execute Compliance Checker."""
        logger.info("executing_compliance_check", workflow_id=state.workflow_id)

        try:
            if state.imponibile_target <= Decimal("0.00"):
                raise ValueError("Imponibile deve essere maggiore di zero per generare la fattura")

            issue_date = state.invoice_date or date.today()
            state.invoice_date = issue_date
            state.payment_due_date = state.payment_due_date or (
                issue_date + timedelta(days=state.payment_terms_days)
            )

            db = _get_session()
            try:
                fattura = None
                if state.invoice_id:
                    fattura = db.query(Fattura).filter(Fattura.id == state.invoice_id).first()
                    if not fattura:
                        raise ValueError(f"Fattura {state.invoice_id} non trovata")

                if not fattura:
                    numero = self._generate_invoice_number(db, issue_date.year)
                    fattura = Fattura(
                        numero=numero,
                        anno=issue_date.year,
                        data_emissione=issue_date,
                        cliente_id=state.client_id,
                        tipo_documento=TipoDocumento.TD01,
                        stato=StatoFattura.BOZZA,
                    )
                    db.add(fattura)
                    db.flush()
                    state.invoice_id = fattura.id
                    state.invoice_number = fattura.numero

                # Update invoice metadata
                fattura.data_emissione = issue_date
                fattura.anno = issue_date.year
                fattura.stato = StatoFattura.BOZZA

                # Financial calculations
                imponibile = state.imponibile_target.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                vat_rate = state.vat_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                vat_amount = (imponibile * vat_rate / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                totale = imponibile + vat_amount

                quantity = Decimal(str(state.hours)) if state.hours else Decimal("1.00")
                if quantity <= Decimal("0.00"):
                    quantity = Decimal("1.00")

                if state.hourly_rate is not None:
                    unit_price = state.hourly_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    unit_price = (imponibile / quantity).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

                description_model = state.metadata.get("description_structured") or {}
                description_text = description_model.get("descrizione_completa") or (
                    state.description_result.content
                    if state.description_result
                    else state.user_input
                )

                # Clear existing line items
                for existing_line in list(fattura.righe):
                    db.delete(existing_line)

                riga = RigaFattura(
                    fattura_id=fattura.id,
                    numero_riga=1,
                    descrizione=description_text,
                    quantita=quantity,
                    prezzo_unitario=unit_price,
                    unita_misura="ore" if state.hours else "servizio",
                    aliquota_iva=vat_rate,
                    imponibile=imponibile,
                    iva=vat_amount,
                    totale=totale,
                )
                db.add(riga)

                fattura.imponibile = imponibile
                fattura.iva = vat_amount
                fattura.totale = totale

                # Update or create payment schedule
                due_date = state.payment_due_date
                if fattura.pagamenti:
                    pagamento = fattura.pagamenti[0]
                    pagamento.importo = totale
                    pagamento.data_scadenza = due_date
                    pagamento.stato = StatoPagamento.DA_PAGARE
                else:
                    pagamento = Pagamento(
                        fattura_id=fattura.id,
                        importo=totale,
                        data_scadenza=due_date,
                        stato=StatoPagamento.DA_PAGARE,
                    )
                    db.add(pagamento)

                db.commit()

                state.line_items = [
                    {
                        "descrizione": description_text,
                        "quantita": float(quantity),
                        "prezzo_unitario": float(unit_price),
                        "aliquota_iva": float(vat_rate),
                        "imponibile": float(imponibile),
                        "iva": float(vat_amount),
                        "totale": float(totale),
                    }
                ]

            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

            # Run compliance checker on persisted invoice
            report = await self.compliance_checker.check_invoice(state.invoice_id)  # type: ignore[arg-type]

            confidence = max(0.0, min(1.0, report.compliance_score / 100))
            summary = (
                "La fattura risulta conforme ai controlli principali."
                if report.is_compliant
                else f"Rilevate {len(report.get_errors())} non conformità da risolvere."
            )

            state.compliance_result = AgentResult(
                agent_type=AgentType.COMPLIANCE,
                success=report.is_compliant,
                content=summary,
                confidence=confidence,
                metadata={
                    "report": report.to_dict(),
                    "errors": [issue.code for issue in report.get_errors()],
                    "warnings": [issue.code for issue in report.get_warnings()],
                },
            )

            state.metadata["compliance_report"] = report.to_dict()
            state.metadata["compliance_recommendations"] = report.recommendations
            state.updated_at = utc_now()

            logger.info(
                "compliance_check_completed",
                workflow_id=state.workflow_id,
                compliant=report.is_compliant,
                compliance_score=report.compliance_score,
                errors=len(report.get_errors()),
                warnings=len(report.get_warnings()),
            )

            return state

        except Exception as e:
            logger.error("compliance_check_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Compliance check error: {e}")
            return state

    async def _compliance_approval_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Human approval checkpoint for compliance issues."""
        logger.info("awaiting_compliance_approval", workflow_id=state.workflow_id)

        # Always require approval if compliance failed
        if not state.is_compliant:
            state.status = "awaiting_approval"
        else:
            from openfatture.ai.orchestration.states import HumanReview

            state.compliance_review = HumanReview(
                decision=ApprovalDecision.APPROVE,
                feedback="Compliance check passed",
                reviewer="system",
            )
            state.status = "approved"

        state.updated_at = utc_now()
        return state

    async def _create_invoice_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Create invoice in database."""
        logger.info("creating_invoice", workflow_id=state.workflow_id)

        try:
            if not state.invoice_id:
                raise ValueError("Nessuna fattura generata durante i passaggi precedenti")

            db = _get_session()
            try:
                fattura = db.query(Fattura).filter(Fattura.id == state.invoice_id).first()
                if not fattura:
                    raise ValueError(
                        f"Fattura {state.invoice_id} non trovata per la finalizzazione"
                    )

                state.invoice_number = fattura.numero

                if state.is_compliant:
                    fattura.stato = StatoFattura.DA_INVIARE
                else:
                    fattura.stato = StatoFattura.BOZZA

                xml_content, error = self.invoice_service.generate_xml(
                    fattura, validate=self.validate_xml
                )

                if error:
                    state.add_warning(error)
                    logger.warning(
                        "invoice_xml_validation_warning",
                        workflow_id=state.workflow_id,
                        invoice_id=fattura.id,
                        error=error,
                    )
                else:
                    state.metadata["xml_preview"] = xml_content[:500]

                db.commit()

                state.invoice_xml_path = fattura.xml_path

            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

            state.mark_completed()

            logger.info(
                "invoice_created",
                workflow_id=state.workflow_id,
                invoice_id=state.invoice_id,
            )

            return state

        except Exception as e:
            logger.error("invoice_creation_error", workflow_id=state.workflow_id, error=str(e))
            state.add_error(f"Failed to create invoice: {e}")
            return state

    async def _handle_error_node(self, state: InvoiceCreationState) -> InvoiceCreationState:
        """Handle workflow errors."""
        logger.error(
            "workflow_failed",
            workflow_id=state.workflow_id,
            errors=state.errors,
        )

        state.status = "failed"
        state.updated_at = utc_now()

        return state

    # ========================================================================
    # Conditional Routing
    # ========================================================================

    def _should_approve_description(self, state: InvoiceCreationState) -> str:
        """Determine if description approval is needed."""
        if state.errors:
            return "error"

        if not state.require_description_approval:
            return "skip"

        if (
            state.description_result
            and state.description_result.confidence > self.confidence_threshold
        ):
            return "skip"  # Auto-approve high confidence

        return "approve"

    def _should_approve_tax(self, state: InvoiceCreationState) -> str:
        """Determine if tax approval is needed."""
        if state.errors:
            return "error"

        if not state.require_tax_approval:
            return "skip"

        if state.tax_result and state.tax_result.confidence > self.confidence_threshold:
            return "skip"

        return "approve"

    def _should_approve_compliance(self, state: InvoiceCreationState) -> str:
        """Determine if compliance approval is needed."""
        if state.errors:
            return "error"

        if (
            state.is_compliant
            and state.compliance_result is not None
            and state.compliance_result.confidence > 0.8
        ):
            return "skip"

        return "approve"

    # ========================================================================
    # Public API
    # ========================================================================

    def _generate_invoice_number(self, db: Session, year: int) -> str:
        """Generate progressive invoice number for the given year."""
        last_invoice = (
            db.query(Fattura).filter(Fattura.anno == year).order_by(Fattura.numero.desc()).first()
        )

        if last_invoice is None:
            return "1"

        try:
            next_number = int(last_invoice.numero) + 1
            return str(next_number)
        except (TypeError, ValueError):
            # Fallback if previous number not numeric
            logger.warning(
                "invoice_number_non_numeric",
                numero=last_invoice.numero,
                anno=year,
            )
            return f"{last_invoice.numero}-1"

    async def execute(
        self,
        user_input: str,
        client_id: int,
        imponibile: float | Decimal,
        *,
        vat_rate: float | Decimal = 22.0,
        hours: float | None = None,
        hourly_rate: float | Decimal | None = None,
        payment_terms_days: int = 30,
        issue_date: date | None = None,
        payment_due_date: date | None = None,
        require_approvals: bool = False,
    ) -> InvoiceCreationState:
        """Execute invoice creation workflow.

        Args:
            user_input: User's brief invoice description
            client_id: Client ID for the invoice
            imponibile: Imponibile amount (before VAT)
            vat_rate: VAT percentage to apply
            hours: Optional number of hours worked
            hourly_rate: Optional hourly rate (€)
            payment_terms_days: Payment due terms in days
            issue_date: Invoice issue date (defaults to today)
            payment_due_date: Optional explicit payment due date
            require_approvals: Enable human approval checkpoints

        Returns:
            Final workflow state with invoice_id if successful

        Example:
            >>> result = await workflow.execute(
            ...     user_input="consulenza cloud 2 giorni",
            ...     client_id=123,
            ...     imponibile=1200.0,
            ...     hours=16,
            ...     hourly_rate=75,
            ... )
            >>> if result.status == "completed":
            ...     print(f"Invoice created: {result.invoice_id}")
        """
        from openfatture.ai.orchestration.states import create_invoice_workflow

        imponibile_decimal: Decimal | None
        if imponibile is None:
            imponibile_decimal = None
        elif isinstance(imponibile, Decimal):
            imponibile_decimal = imponibile
        else:
            imponibile_decimal = Decimal(str(imponibile))

        # Create initial state
        initial_state = create_invoice_workflow(
            user_input=user_input,
            client_id=client_id,
            imponibile=imponibile_decimal,
            vat_rate=vat_rate,
            hours=hours,
            hourly_rate=hourly_rate,
            payment_terms_days=payment_terms_days,
            invoice_date=issue_date,
            payment_due_date=payment_due_date,
            require_approvals=require_approvals,
        )

        logger.info(
            "starting_invoice_workflow",
            workflow_id=initial_state.workflow_id,
            client_id=client_id,
            imponibile=float(initial_state.imponibile_target),
            vat_rate=float(initial_state.vat_rate),
        )

        # Execute graph
        final_state = await self.graph.ainvoke(initial_state)

        if isinstance(final_state, dict):
            final_state = InvoiceCreationState.model_validate(final_state)

        logger.info(
            "invoice_workflow_completed",
            workflow_id=final_state.workflow_id,
            status=final_state.status,
            invoice_id=final_state.invoice_id,
        )

        return final_state


def create_invoice_workflow(
    confidence_threshold: float = 0.85,
) -> InvoiceCreationWorkflow:
    """Create invoice creation workflow instance.

    Args:
        confidence_threshold: Minimum confidence for auto-approval

    Returns:
        InvoiceCreationWorkflow ready to execute
    """
    return InvoiceCreationWorkflow(confidence_threshold=confidence_threshold)
