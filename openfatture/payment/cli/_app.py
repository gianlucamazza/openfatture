"""Shared Typer app, console, logger, and helpers for payment CLI commands."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager

import typer
from rich.console import Console
from sqlalchemy.orm import Session

from ...storage.database import get_db
from ...utils.async_bridge import run_async
from ...utils.logging import get_logger
from ..application.services import (
    MatchingService,
    TransactionInsightService,
)
from ..infrastructure.repository import (
    BankTransactionRepository,
    PaymentRepository,
)
from ..matchers import CompositeMatcher, ExactAmountMatcher, IMatcherStrategy

app = typer.Typer(name="payment", help="💰 Payment tracking & reconciliation", no_args_is_help=True)
console = Console()
logger = get_logger(__name__)

_INSIGHT_SERVICE: TransactionInsightService | None = None
_INSIGHT_INITIALIZED = False


def _run(coro):
    """Execute coroutine synchronously using a fresh event loop."""
    return run_async(coro)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Provide a managed SQLAlchemy session using the shared generator helper."""
    db_generator = get_db()
    session = next(db_generator)
    try:
        yield session
    finally:
        try:
            db_generator.close()
        except RuntimeError:
            # If the generator is already closed (e.g., during test mocks), ignore.
            pass


def _get_transaction_insight_service() -> TransactionInsightService | None:
    """Lazily initialize AI insight service (optional)."""
    global _INSIGHT_SERVICE, _INSIGHT_INITIALIZED

    if _INSIGHT_INITIALIZED:
        return _INSIGHT_SERVICE

    _INSIGHT_INITIALIZED = True

    # Imported lazily: the payment CLI must not drag in the whole AI/providers
    # stack (and its heavy transitive ML deps) just to run non-AI commands.
    from ...ai.agents.payment_insight_agent import PaymentInsightAgent
    from ...ai.providers.base import ProviderError
    from ...ai.providers.factory import create_provider

    try:
        provider = create_provider()
        agent = PaymentInsightAgent(provider=provider)
        _INSIGHT_SERVICE = TransactionInsightService(agent=agent)
        logger.info(
            "payment_cli_ai_insight_enabled",
            provider=provider.provider_name,
            model=provider.model,
        )
        console.print(
            "[dim green]🤖 AI payment insight abilitato per analizzare causali e pagamenti parziali[/]"
        )
    except ProviderError as exc:
        logger.info(
            "payment_cli_ai_insight_disabled",
            reason=str(exc),
            provider=exc.provider,
        )
        console.print(
            "[dim yellow]⚠️  AI insight non disponibile (configura le credenziali OPENFATTURE_AI_* per abilitarlo)[/]"
        )
        _INSIGHT_SERVICE = None
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "payment_cli_ai_insight_error",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        console.print(f"[dim yellow]⚠️  Impossibile inizializzare l'AI insight: {exc}[/]")
        _INSIGHT_SERVICE = None

    return _INSIGHT_SERVICE


def _build_matching_service(
    session: Session,
    *,
    strategies: Sequence[IMatcherStrategy] | None = None,
) -> MatchingService:
    """Factory to create MatchingService with optional AI insight."""
    strategy_list: list[IMatcherStrategy] = (
        list(strategies) if strategies is not None else [ExactAmountMatcher(), CompositeMatcher()]
    )
    tx_repo = BankTransactionRepository(session)
    payment_repo = PaymentRepository(session)
    insight_service = _get_transaction_insight_service()

    return MatchingService(
        tx_repo=tx_repo,
        payment_repo=payment_repo,
        strategies=strategy_list,
        insight_service=insight_service,
    )
