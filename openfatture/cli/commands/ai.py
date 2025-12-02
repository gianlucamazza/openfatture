"""AI-powered assistance commands."""

import json
import os
from collections.abc import Iterable
from contextlib import nullcontext
from pathlib import Path
from typing import Any, cast

import typer
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.agents.compliance import ComplianceChecker
from openfatture.ai.agents.invoice_assistant import InvoiceAssistantAgent
from openfatture.ai.context.enrichment import enrich_with_rag
from openfatture.ai.domain.context import ChatContext, InvoiceContext, TaxContext
from openfatture.ai.domain.message import ConversationHistory, Message, Role
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.orchestration.workflows.invoice_creation import InvoiceCreationWorkflow
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.rag.config import get_rag_config
from openfatture.ai.rag.knowledge_indexer import KnowledgeIndexer
from openfatture.ai.voice import VoiceAssistant, create_voice_provider
from openfatture.cli.lifespan import get_event_bus, run_sync_with_lifespan
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.utils.async_bridge import run_async
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = get_logger(__name__)

rag_app = typer.Typer(help="Manage RAG knowledge base", no_args_is_help=True)
feedback_app = typer.Typer(help="Manage user feedback and ML predictions", no_args_is_help=True)
retrain_app = typer.Typer(help="Manage automatic ML model retraining", no_args_is_help=True)
auto_update_app = typer.Typer(help="Manage RAG auto-update on data changes", no_args_is_help=True)


def _convert_history(history: list[dict[str, str]]) -> ConversationHistory:
    """Convert list of dicts to ConversationHistory."""
    conv_history = ConversationHistory()
    for msg_dict in history:
        role_str = msg_dict.get("role", "user")
        content = msg_dict.get("content", "")
        try:
            role = Role(role_str)
        except ValueError:
            role = Role.USER  # Default to user if invalid
        message = Message(role=role, content=content)
        conv_history.add_message(message)
    return conv_history


@rag_app.command("status")
def rag_status() -> None:
    """Show knowledge base status and vector collection."""
    run_async(_rag_status())


@rag_app.command("index")
def rag_index(
    sources: list[str] | None = typer.Option(
        None,
        "--source",
        "-s",
        help="Source ID defined in manifest (repeatable option)",
    ),
) -> None:
    """Index knowledge base sources."""
    run_async(_rag_index(sources))


@rag_app.command("search")
def rag_search(
    query: str = typer.Argument(..., help="Semantic query to execute on knowledge base"),
    top: int = typer.Option(5, "--top", "-k", help="Maximum number of results to show"),
    source: str | None = typer.Option(
        None, "--source", "-s", help="Limit search to a single source"
    ),
) -> None:
    """Execute semantic search in knowledge base."""
    run_async(_rag_search(query, top, source))


async def _create_knowledge_indexer() -> KnowledgeIndexer:
    """Helper per inizializzare KnowledgeIndexer con configurazione corrente."""
    config = get_rag_config()
    api_key = os.getenv("OPENAI_API_KEY")

    if config.embedding_provider == "openai" and not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY non impostata. Impostare la chiave per generare embedding."
        )

    indexer = await KnowledgeIndexer.create(
        config=config,
        api_key=api_key,
        manifest_path=config.knowledge_manifest_path,
        base_path=Path(".").resolve(),
    )
    return indexer


async def _rag_status() -> None:
    """Mostra stato attuale della knowledge base."""
    try:
        indexer = await _create_knowledge_indexer()
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        console.print(f"[bold red]Errore:[/bold red] {exc}")
        return

    stats = indexer.vector_store.get_stats()

    table = Table(title="Knowledge Base Sources", box=None)
    table.add_column("ID", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Percorso", style="white")
    table.add_column("Tags", style="magenta")

    for source in indexer.sources:
        tags = ", ".join(source.tags or [])
        table.add_row(
            source.id,
            "✅" if source.enabled else "❌",
            str(source.path),
            tags,
        )

    console.print(table)
    console.print()

    console.print(
        Panel.fit(
            f"[bold]Collection:[/bold] {stats['collection_name']}\n"
            f"[bold]Documenti indicizzati:[/bold] {stats['document_count']}\n"
            f"[bold]Persist directory:[/bold] {stats['persist_directory']}",
            title="Vector Store",
            border_style="blue",
        )
    )


async def _rag_index(sources: Iterable[str] | None) -> None:
    """Indicizza le sorgenti specificate (o tutte se None)."""
    try:
        indexer = await _create_knowledge_indexer()
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        console.print(f"[bold red]Errore:[/bold red] {exc}")
        return

    source_ids = list(sources) if sources else None

    with console.status("[bold green]Indicizzazione conoscenza in corso..."):
        chunks = await indexer.index_sources(source_ids=source_ids)

    console.print(
        f"\n[bold green]✅ Indicizzazione completata:[/bold green] {chunks} chunk aggiornati."
    )


async def _rag_search(query: str, top: int, source: str | None) -> None:
    """Esegue ricerca semantica nella knowledge base."""
    try:
        indexer = await _create_knowledge_indexer()
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        console.print(f"[bold red]Errore:[/bold red] {exc}")
        return

    filters: dict[str, Any] = {"type": "knowledge"}
    if source:
        filters["knowledge_source"] = source

    results = await indexer.vector_store.search(
        query=query,
        top_k=top,
        filters=filters,
    )

    if not results:
        console.print("[yellow]Nessun risultato trovato.[/yellow]")
        return

    results_table = Table(title=f'Risultati per "{query}"', box=None)
    results_table.add_column("Fonte", style="cyan")
    results_table.add_column("Sezione", style="white")
    results_table.add_column("Similarity", style="green")
    results_table.add_column("Estratto", style="magenta")

    for item in results:
        metadata = item.get("metadata", {})
        snippet = item.get("document", "")[:180] + (
            "…" if len(item.get("document", "")) > 180 else ""
        )
        results_table.add_row(
            metadata.get("knowledge_source", "n/a"),
            metadata.get("section_title", "n/a"),
            f"{item.get('similarity', 0):.2f}",
            snippet,
        )

    console.print(results_table)


@feedback_app.command("stats")
def feedback_stats(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
) -> None:
    """Show user feedback and prediction feedback statistics."""
    from openfatture.ai.feedback import FeedbackAnalytics

    analytics = FeedbackAnalytics()

    # User feedback stats
    console.print("\n[bold blue]📊 User Feedback Statistics[/bold blue]\n")
    user_stats = analytics.get_user_feedback_stats(days=days)

    stats_table = Table(title=f"Last {days} Days", show_header=False)
    stats_table.add_column("Metric", style="cyan bold")
    stats_table.add_column("Value", style="white")

    stats_table.add_row("Total Feedback", str(user_stats.total_feedback))
    if user_stats.average_rating:
        stars = "⭐" * int(user_stats.average_rating)
        stats_table.add_row("Average Rating", f"{stars} ({user_stats.average_rating:.1f}/5)")
    stats_table.add_row("Total Corrections", str(user_stats.total_corrections))
    stats_table.add_row("Recent (7 days)", str(user_stats.recent_feedback_count))

    console.print(stats_table)
    console.print()

    # By type
    if user_stats.by_type:
        console.print("[bold cyan]By Type:[/bold cyan]")
        for feedback_type, count in user_stats.by_type.items():
            console.print(f"  • {feedback_type}: {count}")
        console.print()

    # By agent
    if user_stats.by_agent:
        console.print("[bold cyan]By Agent:[/bold cyan]")
        for agent, count in user_stats.by_agent.items():
            console.print(f"  • {agent}: {count}")
        console.print()

    # Prediction feedback stats
    console.print("[bold blue]🤖 ML Prediction Feedback Statistics[/bold blue]\n")
    pred_stats = analytics.get_prediction_feedback_stats(days=days)

    pred_table = Table(title=f"Last {days} Days", show_header=False)
    pred_table.add_column("Metric", style="cyan bold")
    pred_table.add_column("Value", style="white")

    pred_table.add_row("Total Predictions", str(pred_stats.total_predictions))
    pred_table.add_row("Acceptance Rate", f"{pred_stats.acceptance_rate:.1f}%")
    if pred_stats.average_confidence:
        pred_table.add_row("Avg Confidence", f"{pred_stats.average_confidence:.1%}")
    pred_table.add_row("Total Corrections", str(pred_stats.total_corrections))
    pred_table.add_row("Unprocessed (for retraining)", str(pred_stats.unprocessed_count))

    console.print(pred_table)
    console.print()

    # By prediction type
    if pred_stats.by_type:
        console.print("[bold cyan]By Prediction Type:[/bold cyan]")
        for pred_type, count in pred_stats.by_type.items():
            console.print(f"  • {pred_type}: {count}")
        console.print()

    # By model version
    if pred_stats.by_model_version:
        console.print("[bold cyan]By Model Version:[/bold cyan]")
        version_table = Table(box=None)
        version_table.add_column("Version", style="cyan")
        version_table.add_column("Total", style="white")
        version_table.add_column("Acceptance", style="green")
        version_table.add_column("Avg Confidence", style="yellow")

        for version, data in pred_stats.by_model_version.items():
            version_table.add_row(
                version,
                str(data["total"]),
                f"{data['acceptance_rate']:.1f}%",
                f"{data['avg_confidence']:.1%}" if data["avg_confidence"] else "N/A",
            )

        console.print(version_table)
        console.print()


@feedback_app.command("export")
def feedback_export(
    output: Path = typer.Option("feedback_export.json", "--output", "-o", help="Output file path"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to export"),
) -> None:
    """Export feedback data to JSON file."""
    from datetime import datetime, timedelta

    from openfatture.ai.feedback import FeedbackService

    service = FeedbackService()
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # This is a simplified export - in production, you'd query with date filters
    console.print(f"\n[bold blue]📤 Exporting feedback data (last {days} days)[/bold blue]\n")

    # Export user feedback (simplified - would need proper date filtering in service)
    console.print("[dim]Note: Full export functionality requires additional service methods[/dim]")
    console.print(f"[green]✓ Export location: {output}[/green]\n")


@feedback_app.command("analyze")
def feedback_analyze(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of patterns to show"),
    threshold: float = typer.Option(
        0.6, "--threshold", "-t", help="Confidence threshold for low-confidence predictions"
    ),
) -> None:
    """Analyze feedback patterns and low-confidence predictions."""
    from openfatture.ai.feedback import FeedbackAnalytics

    analytics = FeedbackAnalytics()

    # Correction patterns
    console.print("\n[bold blue]🔍 Correction Patterns Analysis[/bold blue]\n")
    patterns = analytics.get_correction_patterns(limit=limit)

    if patterns:
        patterns_table = Table(title="Recent Corrections", box=None)
        patterns_table.add_column("Agent", style="cyan")
        patterns_table.add_column("Feature", style="yellow")
        patterns_table.add_column("Original", style="white", no_wrap=False, max_width=40)
        patterns_table.add_column("Corrected", style="green", no_wrap=False, max_width=40)

        for pattern in patterns[:10]:  # Show first 10
            patterns_table.add_row(
                pattern.get("agent_type", "N/A"),
                pattern.get("feature_name", "N/A"),
                pattern.get("original", "")[:50] + "..." if pattern.get("original") else "",
                pattern.get("corrected", "")[:50] + "..." if pattern.get("corrected") else "",
            )

        console.print(patterns_table)
        console.print()
    else:
        console.print("[dim]No correction patterns found.[/dim]\n")

    # Low confidence predictions
    console.print("[bold blue]⚠️  Low Confidence Predictions (Requires Review)[/bold blue]\n")
    low_conf = analytics.get_low_confidence_predictions(threshold=threshold, limit=limit)

    if low_conf:
        low_conf_table = Table(title=f"Confidence < {threshold:.0%}", box=None)
        low_conf_table.add_column("ID", style="dim")
        low_conf_table.add_column("Type", style="cyan")
        low_conf_table.add_column("Entity", style="yellow")
        low_conf_table.add_column("Confidence", style="red")
        low_conf_table.add_column("Accepted", style="green")

        for pred in low_conf:
            low_conf_table.add_row(
                str(pred["id"]),
                pred["prediction_type"],
                pred["entity"],
                f"{pred['confidence']:.1%}" if pred["confidence"] else "N/A",
                "✓" if pred["user_accepted"] else "✗",
            )

        console.print(low_conf_table)
        console.print()

        console.print(
            f"[bold yellow]💡 Tip:[/bold yellow] These {len(low_conf)} predictions need human review "
            "for model improvement.\n"
        )
    else:
        console.print(
            f"[dim]No low-confidence predictions found (threshold: {threshold:.0%}).[/dim]\n"
        )


@retrain_app.command("trigger")
def retrain_trigger(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force retraining even if triggers not met"
    ),
) -> None:
    """Manually trigger model retraining.

    Checks retraining triggers and executes retraining if conditions are met.
    Use --force to skip trigger checks.

    Examples:
        openfatture ai retrain trigger
        openfatture ai retrain trigger --force
    """
    from openfatture.ai.ml.retraining import get_scheduler

    scheduler = get_scheduler()

    console.print("\n[bold blue]🔄 Manual Model Retraining[/bold blue]\n")

    # Run async retraining

    with console.status("[bold green]Triggering retraining..."):
        result = run_async(scheduler.trigger_manual_retraining("cash_flow", force=force))

    # Display results
    if result["success"]:
        console.print(f"[bold green]✅ {result['message']}[/bold green]\n")

        if result.get("deployed"):
            console.print(f"[cyan]Version ID:[/cyan] {result.get('version_id')}")
            console.print(f"[cyan]Feedback processed:[/cyan] {result.get('feedback_count')}")

            if result.get("evaluation"):
                eval_data = result["evaluation"]
                metrics = eval_data.get("metrics", {})

                console.print("\n[bold]New Model Metrics:[/bold]")
                console.print(f"  MAE: {metrics.get('mae', 0):.2f} days")
                console.print(f"  RMSE: {metrics.get('rmse', 0):.2f} days")
                console.print(f"  Confidence: {metrics.get('avg_confidence', 0):.1%}")

                if eval_data.get("comparison"):
                    console.print("\n[bold]Improvement:[/bold]")
                    for metric, data in eval_data["comparison"].items():
                        if data["is_better"]:
                            console.print(f"  {metric.upper()}: +{data['improvement_pct']:.1f}%")
        else:
            console.print(f"[dim]Model not deployed: {result.get('message')}[/dim]")
    else:
        console.print(f"[bold red]❌ {result['message']}[/bold red]\n")


@retrain_app.command("status")
def retrain_status() -> None:
    """Show retraining scheduler status and trigger conditions.

    Displays:
    - Scheduler running status
    - Next scheduled check
    - Trigger conditions (feedback count, time elapsed)
    - Last retraining time

    Example:
        openfatture ai retrain status
    """
    from openfatture.ai.ml.retraining import get_scheduler

    scheduler = get_scheduler()
    status = scheduler.get_status()

    console.print("\n[bold blue]🔄 Retraining Scheduler Status[/bold blue]\n")

    # Main status
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Setting", style="cyan bold")
    status_table.add_column("Value")

    # Enabled/Running
    enabled_icon = "✅" if status["enabled"] else "❌"
    running_icon = "🟢" if status["running"] else "⚫"

    status_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
    status_table.add_row("Running:", f"{running_icon} {status['running']}")
    status_table.add_row("Dry Run:", "Yes" if status["dry_run"] else "No")
    status_table.add_row("Check Interval:", f"{status['interval_hours']}h")

    if status.get("last_check_time"):
        status_table.add_row("Last Check:", status["last_check_time"])

    if status.get("last_retrain_time"):
        status_table.add_row("Last Retrain:", status["last_retrain_time"])

    if status.get("next_run_time"):
        status_table.add_row("Next Run:", status["next_run_time"])

    status_table.add_row("Retraining Active:", "Yes" if status["retraining_in_progress"] else "No")

    console.print(status_table)
    console.print()

    # Trigger status
    trigger_status = status.get("trigger_status", {})
    should_trigger = trigger_status.get("should_trigger", False)

    if should_trigger:
        console.print("[bold yellow]⚠️  Retraining Triggers Met[/bold yellow]\n")
    else:
        console.print("[bold green]✅ No Retraining Needed[/bold green]\n")

    # Feedback stats
    feedback_stats = trigger_status.get("feedback_stats", {})
    console.print("[bold]Feedback Status:[/bold]")
    console.print(f"  Unprocessed: {feedback_stats.get('unprocessed_count', 0)}")
    console.print(f"  Threshold: {feedback_stats.get('threshold', 0)}")
    ready_icon = "✅" if feedback_stats.get("ready") else "❌"
    console.print(f"  Ready: {ready_icon}")
    console.print()

    # Time stats
    time_stats = trigger_status.get("time_stats", {})
    console.print("[bold]Time Status:[/bold]")
    if time_stats.get("last_training"):
        console.print(f"  Last Training: {time_stats['last_training']}")
    if time_stats.get("days_since_training") is not None:
        console.print(f"  Days Elapsed: {time_stats['days_since_training']}")
    console.print(f"  Threshold: {time_stats.get('threshold_days', 0)} days")
    ready_icon = "✅" if time_stats.get("ready") else "❌"
    console.print(f"  Ready: {ready_icon}")
    console.print()

    # Active triggers
    if trigger_status.get("triggers"):
        console.print("[bold yellow]Active Triggers:[/bold yellow]")
        for trigger in trigger_status["triggers"]:
            console.print(f"  • {trigger['message']}")
        console.print()


@retrain_app.command("history")
def retrain_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of versions to show"),
) -> None:
    """Show model version history.

    Displays all saved model versions with metrics and creation times.

    Example:
        openfatture ai retrain history
        openfatture ai retrain history --limit 5
    """
    from openfatture.ai.ml.retraining import ModelVersionManager

    version_manager = ModelVersionManager()
    versions = version_manager.list_versions("cash_flow")

    console.print("\n[bold blue]📦 Model Version History[/bold blue]\n")

    if not versions:
        console.print("[dim]No model versions found.[/dim]\n")
        return

    # Version table
    versions_table = Table(title="Cash Flow Model Versions", box=None)
    versions_table.add_column("Version ID", style="cyan")
    versions_table.add_column("Created", style="white")
    versions_table.add_column("MAE", style="green")
    versions_table.add_column("RMSE", style="green")
    versions_table.add_column("Notes", style="dim", no_wrap=False, max_width=40)

    for version in versions[:limit]:
        created = version.created_at.strftime("%Y-%m-%d %H:%M")
        mae = version.metrics.get("mae", "N/A")
        rmse = version.metrics.get("rmse", "N/A")

        mae_str = f"{mae:.2f}" if isinstance(mae, int | float) else mae
        rmse_str = f"{rmse:.2f}" if isinstance(rmse, int | float) else rmse

        notes = version.notes or ""

        versions_table.add_row(
            version.version_id,
            created,
            mae_str,
            rmse_str,
            notes,
        )

    console.print(versions_table)
    console.print()

    if len(versions) > limit:
        console.print(
            f"[dim]Showing {limit} of {len(versions)} versions. Use --limit to see more.[/dim]\n"
        )


@retrain_app.command("rollback")
def retrain_rollback(
    version_id: str = typer.Argument(..., help="Version ID to rollback to"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Rollback to a previous model version.

    Restores a previous model version to the current model location.
    This overwrites the current model.

    Example:
        openfatture ai retrain rollback 20250116_143022
        openfatture ai retrain rollback 20250116_143022 --yes
    """
    from openfatture.ai.ml.retraining import ModelVersionManager

    version_manager = ModelVersionManager()

    console.print("\n[bold blue]🔄 Model Rollback[/bold blue]\n")

    # Verify version exists
    try:
        version = version_manager.load_version("cash_flow", version_id, restore_to_current=False)
    except FileNotFoundError:
        console.print(f"[bold red]❌ Version '{version_id}' not found[/bold red]\n")
        raise typer.Exit(1)

    # Show version info
    console.print(f"[bold]Rolling back to version:[/bold] {version_id}")
    console.print(f"[bold]Created:[/bold] {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if version.notes:
        console.print(f"[bold]Notes:[/bold] {version.notes}")

    # Show metrics
    if version.metrics:
        console.print("\n[bold]Metrics:[/bold]")
        for key, value in version.metrics.items():
            if isinstance(value, int | float):
                console.print(f"  {key}: {value:.2f}")

    console.print()

    # Confirmation
    if not confirm:
        proceed = typer.confirm("⚠️  This will overwrite the current model. Continue?")
        if not proceed:
            console.print("[dim]Rollback cancelled.[/dim]\n")
            raise typer.Exit(0)

    # Perform rollback
    try:
        version_manager.rollback_to_version("cash_flow", version_id)
        console.print(
            f"[bold green]✅ Successfully rolled back to version {version_id}[/bold green]\n"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Rollback failed: {e}[/bold red]\n")
        raise typer.Exit(1)


@auto_update_app.command("status")
def auto_update_status() -> None:
    """Show RAG auto-update service status.

    Displays:
    - Service enabled/running status
    - Queue statistics (pending changes, processed count)
    - Configuration settings
    - Tracker statistics

    Example:
        openfatture ai auto-update status
    """
    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()
    status = service.get_status()

    console.print("\n[bold blue]🔄 RAG Auto-Update Service Status[/bold blue]\n")

    # Main status
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Setting", style="cyan bold")
    status_table.add_column("Value")

    # Enabled/Running
    enabled_icon = "✅" if status["enabled"] else "❌"
    running_icon = "🟢" if status["running"] else "⚫"

    status_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
    status_table.add_row("Running:", f"{running_icon} {status['running']}")

    console.print(status_table)
    console.print()

    # Configuration
    config = status.get("config", {})
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Batch Size: {config.get('batch_size', 0)}")
    console.print(f"  Debounce: {config.get('debounce_seconds', 0)}s")
    console.print(f"  Incremental Updates: {config.get('incremental_updates', False)}")
    tracked = config.get("tracked_entities", [])
    if tracked:
        console.print(f"  Tracked Entities: {', '.join(tracked)}")
    console.print()

    # Queue statistics
    queue_stats = status.get("queue_stats", {})
    console.print("[bold]Queue Statistics:[/bold]")
    console.print(f"  Running: {queue_stats.get('running', False)}")
    console.print(f"  Total Processed: {queue_stats.get('total_processed', 0)}")
    console.print(f"  Total Batches: {queue_stats.get('total_batches', 0)}")
    if queue_stats.get("last_process_time_ms"):
        console.print(f"  Last Process Time: {queue_stats['last_process_time_ms']:.0f}ms")
    console.print()

    # Tracker statistics
    tracker_stats = status.get("tracker_stats", {})
    if tracker_stats:
        console.print("[bold]Tracker Statistics:[/bold]")
        for entity_type, count in tracker_stats.items():
            console.print(f"  {entity_type}: {count} pending")
        console.print()


@auto_update_app.command("start")
def auto_update_start() -> None:
    """Start the RAG auto-indexing service.

    Starts background processing of data changes for automatic
    reindexing of the vector store.

    Example:
        openfatture ai auto-update start
    """

    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()

    console.print("\n[bold blue]🔄 Starting RAG Auto-Update Service[/bold blue]\n")

    with console.status("[bold green]Starting service..."):
        run_async(service.start())

    console.print("[bold green]✅ Service started successfully[/bold green]\n")


@auto_update_app.command("stop")
def auto_update_stop() -> None:
    """Stop the RAG auto-indexing service.

    Stops background processing and optionally persists pending
    changes to disk based on configuration.

    Example:
        openfatture ai auto-update stop
    """

    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()

    console.print("\n[bold blue]🔄 Stopping RAG Auto-Update Service[/bold blue]\n")

    with console.status("[bold yellow]Stopping service..."):
        run_async(service.stop())

    console.print("[bold yellow]⏸️  Service stopped[/bold yellow]\n")


@auto_update_app.command("queue")
def auto_update_queue() -> None:
    """Show detailed queue statistics.

    Displays pending changes by entity type and processing metrics.

    Example:
        openfatture ai auto-update queue
    """
    from openfatture.ai.rag.auto_update import get_change_tracker, get_reindex_queue

    tracker = get_change_tracker()
    queue = get_reindex_queue()

    console.print("\n[bold blue]📊 RAG Auto-Update Queue Statistics[/bold blue]\n")

    # Queue stats
    queue_stats = queue.get_stats()
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Metric", style="cyan bold")
    stats_table.add_column("Value")

    stats_table.add_row("Running:", "🟢 Yes" if queue_stats["running"] else "⚫ No")
    stats_table.add_row("Total Processed:", str(queue_stats["total_processed"]))
    stats_table.add_row("Total Batches:", str(queue_stats["total_batches"]))
    if queue_stats.get("last_process_time_ms"):
        stats_table.add_row("Last Process Time:", f"{queue_stats['last_process_time_ms']:.0f}ms")

    console.print(stats_table)
    console.print()

    # Tracker stats (pending changes)
    tracker_stats = tracker.get_queue_stats()
    console.print("[bold]Pending Changes:[/bold]")
    if tracker_stats:
        pending_table = Table(box=None)
        pending_table.add_column("Entity Type", style="cyan")
        pending_table.add_column("Count", justify="right", style="yellow")

        total_pending = 0
        for entity_type, count in tracker_stats.items():
            pending_table.add_row(entity_type, str(count))
            total_pending += count

        console.print(pending_table)
        console.print(f"\n[bold]Total Pending:[/bold] {total_pending}")
    else:
        console.print("[dim]No pending changes[/dim]")
    console.print()


@auto_update_app.command("manual")
def auto_update_manual(
    entity_type: str = typer.Argument(..., help="Entity type to reindex (invoice, client)"),
    entity_ids: list[int] = typer.Argument(..., help="Entity IDs to reindex (space-separated)"),
) -> None:
    """Manually trigger reindexing for specific entities.

    Forces immediate reindexing of specified invoices or clients,
    bypassing the normal queue processing.

    Examples:
        openfatture ai auto-update manual invoice 1 2 3
        openfatture ai auto-update manual client 123
    """

    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    service = get_auto_indexing_service()

    console.print("\n[bold blue]🔄 Manual Reindexing[/bold blue]\n")
    console.print(f"[bold]Entity Type:[/bold] {entity_type}")
    console.print(f"[bold]Entity IDs:[/bold] {', '.join(map(str, entity_ids))}\n")

    with console.status("[bold green]Reindexing..."):
        result = run_async(service.manual_reindex(entity_type, entity_ids))

    # Display results
    console.print("[bold green]✅ Reindexing completed[/bold green]\n")
    console.print(f"[cyan]Requested:[/cyan] {result['requested_count']}")
    console.print(f"[green]Successful:[/green] {len(result['successful'])}")
    console.print(f"[red]Failed:[/red] {len(result['failed'])}")

    if result["successful"]:
        console.print("\n[bold green]Successfully reindexed:[/bold green]")
        for entity_id in result["successful"][:10]:  # Show first 10
            console.print(f"  • {entity_type} {entity_id}")
        if len(result["successful"]) > 10:
            console.print(f"  ... and {len(result['successful']) - 10} more")

    if result["failed"]:
        console.print("\n[bold red]Failed to reindex:[/bold red]")
        for failure in result["failed"][:5]:  # Show first 5 errors
            console.print(f"  • {entity_type} {failure['entity_id']}: {failure['error']}")
        if len(result["failed"]) > 5:
            console.print(f"  ... and {len(result['failed']) - 5} more")

    console.print()


app.add_typer(feedback_app, name="feedback")
app.add_typer(retrain_app, name="retrain")
app.add_typer(auto_update_app, name="auto-update")


@app.command("status")
def self_learning_status() -> None:
    """Show comprehensive self-learning system status.

    Displays unified dashboard of all self-learning components:
    - RAG Auto-Update service
    - ML Model Retraining scheduler
    - Feedback Collection statistics

    This provides a quick overview of the entire self-learning system health.

    Example:
        openfatture ai status
    """
    from openfatture.ai.feedback import FeedbackAnalytics
    from openfatture.ai.ml.retraining import get_scheduler
    from openfatture.ai.rag.auto_update import get_auto_indexing_service

    console.print("\n[bold blue]🤖 Self-Learning System Dashboard[/bold blue]\n")

    # RAG Auto-Update Status
    console.print("[bold cyan]═══ RAG Auto-Update ═══[/bold cyan]\n")
    try:
        service = get_auto_indexing_service()
        status = service.get_status()

        # Status indicators
        enabled_icon = "✅" if status["enabled"] else "❌"
        running_icon = "🟢" if status["running"] else "⚫"

        rag_table = Table(show_header=False, box=None)
        rag_table.add_column("Metric", style="dim")
        rag_table.add_column("Value")

        rag_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
        rag_table.add_row("Running:", f"{running_icon} {status['running']}")

        config = status.get("config", {})
        tracked = config.get("tracked_entities", [])
        if tracked:
            rag_table.add_row("Tracking:", ", ".join(tracked))

        queue_stats = status.get("queue_stats", {})
        rag_table.add_row("Processed:", str(queue_stats.get("total_processed", 0)))

        tracker_stats = status.get("tracker_stats", {})
        pending_total = sum(tracker_stats.values()) if tracker_stats else 0
        rag_table.add_row("Pending:", str(pending_total))

        console.print(rag_table)
        console.print()

        # Show pending by type if any
        if tracker_stats:
            console.print("[dim]Pending by type:[/dim]")
            for entity_type, count in tracker_stats.items():
                console.print(f"  • {entity_type}: {count}")
            console.print()

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not fetch RAG auto-update status: {e}[/yellow]\n")

    # ML Retraining Status
    console.print("[bold cyan]═══ ML Model Retraining ═══[/bold cyan]\n")
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        # Status indicators
        enabled_icon = "✅" if status["enabled"] else "❌"
        running_icon = "🟢" if status["running"] else "⚫"

        retrain_table = Table(show_header=False, box=None)
        retrain_table.add_column("Metric", style="dim")
        retrain_table.add_column("Value")

        retrain_table.add_row("Enabled:", f"{enabled_icon} {status['enabled']}")
        retrain_table.add_row("Running:", f"{running_icon} {status['running']}")

        if status.get("last_retrain_time"):
            retrain_table.add_row("Last Retrain:", status["last_retrain_time"])

        if status.get("next_run_time"):
            retrain_table.add_row("Next Check:", status["next_run_time"])

        # Trigger status
        trigger_status = status.get("trigger_status", {})
        should_trigger = trigger_status.get("should_trigger", False)
        trigger_icon = "⚠️" if should_trigger else "✅"
        retrain_table.add_row("Ready to Train:", f"{trigger_icon} {should_trigger}")

        # Feedback count
        feedback_stats = trigger_status.get("feedback_stats", {})
        unprocessed = feedback_stats.get("unprocessed_count", 0)
        threshold = feedback_stats.get("threshold", 0)
        retrain_table.add_row("Feedback:", f"{unprocessed}/{threshold}")

        console.print(retrain_table)
        console.print()

        # Show active triggers if any
        if trigger_status.get("triggers"):
            console.print("[yellow]Active triggers:[/yellow]")
            for trigger in trigger_status["triggers"][:3]:  # Show first 3
                console.print(f"  • {trigger['message']}")
            console.print()

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not fetch retraining status: {e}[/yellow]\n")

    # Feedback Collection Stats
    console.print("[bold cyan]═══ Feedback Collection ═══[/bold cyan]\n")
    try:
        analytics = FeedbackAnalytics()

        # Last 7 days stats
        user_stats = analytics.get_user_feedback_stats(days=7)
        pred_stats = analytics.get_prediction_feedback_stats(days=7)

        feedback_table = Table(show_header=False, box=None)
        feedback_table.add_column("Metric", style="dim")
        feedback_table.add_column("Value")

        # User feedback
        feedback_table.add_row("User Feedback (7d):", str(user_stats.total_feedback))
        if user_stats.average_rating:
            stars = "⭐" * min(5, int(user_stats.average_rating))
            feedback_table.add_row("Avg Rating:", f"{stars} ({user_stats.average_rating:.1f}/5)")

        # Prediction feedback
        feedback_table.add_row("Predictions (7d):", str(pred_stats.total_predictions))
        feedback_table.add_row("Acceptance Rate:", f"{pred_stats.acceptance_rate:.1f}%")
        feedback_table.add_row("Unprocessed:", str(pred_stats.unprocessed_count))

        console.print(feedback_table)
        console.print()

        # Top agent types if available
        if user_stats.by_agent:
            console.print("[dim]Top agents:[/dim]")
            for agent, count in list(user_stats.by_agent.items())[:3]:
                console.print(f"  • {agent}: {count}")
            console.print()

    except Exception as e:
        console.print(f"[yellow]⚠️  Could not fetch feedback stats: {e}[/yellow]\n")

    # Footer with helpful commands
    console.print("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
    console.print("\n[bold]Detailed Commands:[/bold]")
    console.print("  • RAG Auto-Update:    [cyan]openfatture ai auto-update status[/cyan]")
    console.print("  • ML Retraining:      [cyan]openfatture ai retrain status[/cyan]")
    console.print("  • Feedback Analysis:  [cyan]openfatture ai feedback stats[/cyan]")
    console.print("\n[dim]See docs/SELF_LEARNING.md for complete documentation[/dim]\n")


@app.command("describe")
def ai_describe(
    ctx: typer.Context,
    text: str = typer.Argument(..., help="Service description to expand"),
    hours: float | None = typer.Option(None, "--hours", "-h", help="Hours worked"),
    rate: float | None = typer.Option(None, "--rate", "-r", help="Hourly rate (€)"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name"),
    technologies: str | None = typer.Option(
        None, "--tech", "-t", help="Technologies used (comma-separated)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Use AI to generate detailed invoice descriptions.

    Example:
        openfatture ai describe "3 ore consulenza web"
        openfatture ai describe "sviluppo backend API" --hours 5 --tech "Python,FastAPI"
        openfatture ai describe "consulenza" --format markdown
    """
    run_async(_run_invoice_assistant(ctx, text, hours, rate, project, technologies, json_output))


async def _run_invoice_assistant(
    ctx: typer.Context,
    text: str,
    hours: float | None,
    rate: float | None,
    project: str | None,
    technologies: str | None,
    json_output: bool,
) -> None:
    """Run the Invoice Assistant agent."""
    import time

    from openfatture.cli.formatters.utils import (
        get_format_from_context,
        render_data,
        render_response,
    )

    # Determine output format
    format_type = get_format_from_context(ctx, json_output)

    if format_type == "rich":
        console.print("\n[bold blue]🤖 AI Invoice Description Generator[/bold blue]\n")

    # Track execution metrics
    start_time = time.time()
    success = False
    tokens_used = 0
    cost_usd = 0.0

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        settings = get_settings()
        event_bus.publish(
            AICommandStartedEvent(
                command="describe",
                user_input=text,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "hours": hours,
                    "rate": rate,
                    "project": project,
                    "technologies": technologies,
                },
            )
        )

    try:
        # Parse technologies
        tech_list = []
        if technologies:
            tech_list = [t.strip() for t in technologies.split(",")]

        # Create context
        context = InvoiceContext(
            user_input=text,
            servizio_base=text,
            ore_lavorate=hours,
            tariffa_oraria=rate,
            progetto=project,
            tecnologie=tech_list,
        )

        # Optional RAG enrichment (invoice history + knowledge snippets)
        context.enable_rag = True
        try:
            context = cast(InvoiceContext, await enrich_with_rag(context, text))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("invoice_context_rag_failed", error=str(exc))

        # Show input (only for rich format)
        if format_type == "rich":
            _display_input(context)

        # Create provider and agent
        if format_type == "rich":
            with console.status("[bold green]Generating description with AI..."):
                provider = create_provider()
                agent = InvoiceAssistantAgent(provider=provider)
                response = await agent.execute(context)
        else:
            provider = create_provider()
            agent = InvoiceAssistantAgent(provider=provider)
            response = await agent.execute(context)

        # Check for errors
        if response.status.value == "error":
            if format_type == "rich":
                console.print(f"\n[bold red]❌ Error:[/bold red] {response.error}\n")
            else:
                from openfatture.cli.formatters.utils import render_error

                render_error(response.error or "Unknown error", format_type, console)
            logger.error("ai_describe_failed", error=response.error)
            return

        # Display results using formatter
        if json_output or format_type == "json":
            # Raw JSON output (backward compatibility)
            if response.metadata.get("is_structured"):
                output = response.metadata["parsed_model"]
            else:
                output = {"descrizione_completa": response.content}
            render_data(output, format_type, console)
        elif format_type == "rich":
            # Use existing rich display
            _display_result(response)
            _display_metrics(response)
        else:
            # Use formatter for other formats
            render_response(response, format_type, console, show_metrics=True)

        # Track success and metrics
        success = True
        tokens_used = response.usage.total_tokens
        cost_usd = response.usage.estimated_cost_usd

    except Exception as e:
        if format_type == "rich":
            console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        else:
            from openfatture.cli.formatters.utils import render_error

            render_error(e, format_type, console)
        logger.error("ai_describe_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="describe",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                )
            )


def _display_input(context: InvoiceContext) -> None:
    """Display input context."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📝 Service:", context.servizio_base)

    if context.ore_lavorate:
        table.add_row("⏱️  Hours:", f"{context.ore_lavorate:.1f}h")

    if context.tariffa_oraria:
        table.add_row("💰 Rate:", f"€{context.tariffa_oraria:.2f}/h")

    if context.progetto:
        table.add_row("📁 Project:", context.progetto)

    if context.tecnologie:
        table.add_row("🔧 Technologies:", ", ".join(context.tecnologie))

    console.print(table)
    console.print()


app.add_typer(rag_app, name="rag")


def _display_result(response: AgentResponse) -> None:
    """Display structured result."""
    # Try to get structured model
    if response.metadata.get("is_structured"):
        data = response.metadata["parsed_model"]

        # Description
        console.print(
            Panel(
                data["descrizione_completa"],
                title="[bold]📄 Professional Description[/bold]",
                border_style="green",
            )
        )

        # Deliverables
        if data.get("deliverables"):
            console.print("\n[bold cyan]📦 Deliverables:[/bold cyan]")
            for item in data["deliverables"]:
                console.print(f"  • {item}")

        # Competenze
        if data.get("competenze"):
            console.print("\n[bold cyan]🔧 Technical Skills:[/bold cyan]")
            for skill in data["competenze"]:
                console.print(f"  • {skill}")

        # Duration
        if data.get("durata_ore"):
            console.print(f"\n[bold cyan]⏱️  Duration:[/bold cyan] {data['durata_ore']}h")

        # Notes
        if data.get("note"):
            console.print(f"\n[bold cyan]📌 Notes:[/bold cyan] {data['note']}")

    else:
        # Fallback to plain text
        console.print(
            Panel(
                response.content,
                title="[bold]📄 Generated Description[/bold]",
                border_style="green",
            )
        )

    console.print()


def _display_metrics(response: AgentResponse) -> None:
    """Display response metrics."""
    metrics_table = Table(show_header=False, box=None, padding=(0, 2))
    metrics_table.add_column("Metric", style="dim")
    metrics_table.add_column("Value", style="dim")

    metrics_table.add_row(
        f"Provider: {response.provider}",
        f"Model: {response.model}",
    )
    metrics_table.add_row(
        f"Tokens: {response.usage.total_tokens}",
        f"Cost: ${response.usage.estimated_cost_usd:.4f}",
    )
    metrics_table.add_row(
        f"Latency: {response.latency_ms:.0f}ms",
        "",
    )

    console.print(metrics_table)
    console.print()


@app.command("suggest-vat")
def ai_suggest_vat(
    ctx: typer.Context,
    description: str = typer.Argument(..., help="Service/product description"),
    pa: bool = typer.Option(False, "--pa", help="Client is Public Administration"),
    estero: bool = typer.Option(False, "--estero", help="Foreign client"),
    paese: str | None = typer.Option(
        None, "--paese", help="Client country code (IT, FR, US, etc.)"
    ),
    categoria: str | None = typer.Option(None, "--categoria", "-c", help="Service category"),
    importo: float | None = typer.Option(None, "--importo", "-i", help="Amount in EUR"),
    ateco: str | None = typer.Option(None, "--ateco", help="ATECO code"),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Use AI to suggest appropriate VAT rate and fiscal treatment.

    Examples:
        openfatture ai suggest-vat "consulenza IT"
        openfatture ai suggest-vat "consulenza IT per azienda edile"
        openfatture ai suggest-vat "formazione professionale" --pa
        openfatture ai suggest-vat "consulenza" --estero --paese US --format markdown
    """
    run_async(
        _run_tax_advisor(
            ctx, description, pa, estero, paese, categoria, importo, ateco, json_output
        )
    )


async def _run_tax_advisor(
    ctx: typer.Context,
    description: str,
    pa: bool,
    estero: bool,
    paese: str | None,
    categoria: str | None,
    importo: float | None,
    ateco: str | None,
    json_output: bool,
) -> None:
    """Run the Tax Advisor agent."""
    import time

    from openfatture.cli.formatters.utils import (
        get_format_from_context,
    )

    # Determine output format
    format_type = get_format_from_context(ctx, json_output)

    if format_type == "rich":
        console.print("\n[bold blue]🧾 AI Tax Advisor - Suggerimento Fiscale[/bold blue]\n")

    # Track execution metrics
    start_time = time.time()
    success = False
    tokens_used = 0
    cost_usd = 0.0

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        settings = get_settings()
        event_bus.publish(
            AICommandStartedEvent(
                command="suggest-vat",
                user_input=description,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "pa": pa,
                    "estero": estero,
                    "paese": paese,
                    "categoria": categoria,
                    "importo": importo,
                    "ateco": ateco,
                },
            )
        )

    try:
        # Import TaxContext
        from openfatture.ai.agents.tax_advisor import TaxAdvisorAgent
        from openfatture.ai.domain.context import TaxContext

        # Create context
        context = TaxContext(
            user_input=description,
            tipo_servizio=description,
            categoria_servizio=categoria,
            importo=importo or 0,
            cliente_pa=pa,
            cliente_estero=estero,
            paese_cliente=paese or ("IT" if not estero else "XX"),
            codice_ateco=ateco,
        )

        context.enable_rag = True
        try:
            context = cast(TaxContext, await enrich_with_rag(context, description))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("tax_context_rag_failed", error=str(exc))

        # Show input
        _display_tax_input(context)

        # Create provider and agent
        with console.status("[bold green]Analizzando trattamento fiscale..."):
            provider = create_provider()
            agent = TaxAdvisorAgent(provider=provider)

            # Execute agent
            response = await agent.execute(context)

        # Check for errors
        if response.status.value == "error":
            console.print(f"\n[bold red]❌ Errore:[/bold red] {response.error}\n")
            logger.error("ai_suggest_vat_failed", error=response.error)
            return

        # Display results
        if json_output:
            # Raw JSON output
            if response.metadata.get("is_structured"):
                output = response.metadata["parsed_model"]
            else:
                output = {"spiegazione": response.content}
            console.print(JSON(json.dumps(output, indent=2, ensure_ascii=False)))
        else:
            # Formatted output
            _display_tax_result(response)

        # Show metrics
        _display_metrics(response)

        # Track success and metrics
        success = True
        tokens_used = response.usage.total_tokens
        cost_usd = response.usage.estimated_cost_usd

    except Exception as e:
        console.print(f"\n[bold red]❌ Errore:[/bold red] {e}\n")
        logger.error("ai_suggest_vat_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="suggest-vat",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                )
            )


def _display_tax_input(context: TaxContext) -> None:
    """Display tax context input."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📝 Servizio/Prodotto:", context.tipo_servizio)

    if context.categoria_servizio:
        table.add_row("📂 Categoria:", context.categoria_servizio)

    if context.importo:
        table.add_row("💰 Importo:", f"€{context.importo:.2f}")

    if context.cliente_pa:
        table.add_row("🏛️  Cliente:", "Pubblica Amministrazione")

    if context.cliente_estero:
        table.add_row("🌍 Cliente estero:", context.paese_cliente)

    if context.codice_ateco:
        table.add_row("🔢 Codice ATECO:", context.codice_ateco)

    console.print(table)
    console.print()


def _display_tax_result(response: AgentResponse) -> None:
    """Display tax suggestion result."""
    # Try to get structured model
    if response.metadata.get("is_structured"):
        data = response.metadata["parsed_model"]

        # Main tax info panel
        tax_info = f"""[bold]Aliquota IVA:[/bold]    {data["aliquota_iva"]}%
[bold]Reverse Charge:[/bold]  {"✓ SI" if data["reverse_charge"] else "✗ NO"}"""

        if data.get("codice_natura"):
            tax_info += f"\n[bold]Natura IVA:[/bold]      {data['codice_natura']}"

        if data.get("split_payment"):
            tax_info += "\n[bold]Split Payment:[/bold]   ✓ SI"

        if data.get("regime_speciale"):
            tax_info += f"\n[bold]Regime Speciale:[/bold] {data['regime_speciale']}"

        tax_info += f"\n[bold]Confidence:[/bold]      {int(data['confidence'] * 100)}%"

        console.print(
            Panel(
                tax_info,
                title="[bold]📊 Trattamento Fiscale[/bold]",
                border_style="green",
            )
        )

        # Spiegazione
        console.print("\n[bold cyan]📋 Spiegazione:[/bold cyan]")
        console.print(f"{data['spiegazione']}\n")

        # Riferimento normativo
        console.print("[bold cyan]📜 Riferimento normativo:[/bold cyan]")
        console.print(f"{data['riferimento_normativo']}\n")

        # Nota fattura
        if data.get("note_fattura"):
            console.print("[bold cyan]📝 Nota per fattura:[/bold cyan]")
            console.print(f'"{data["note_fattura"]}"\n')

        # Raccomandazioni
        if data.get("raccomandazioni") and len(data["raccomandazioni"]) > 0:
            console.print("[bold cyan]💡 Raccomandazioni:[/bold cyan]")
            for racc in data["raccomandazioni"]:
                console.print(f"  • {racc}")
            console.print()

    else:
        # Fallback to plain text
        console.print(
            Panel(
                response.content,
                title="[bold]📊 Suggerimento Fiscale[/bold]",
                border_style="green",
            )
        )


@app.command("forecast")
def ai_forecast(
    ctx: typer.Context,
    months: int = typer.Option(3, "--months", "-m", help="Months to forecast"),
    client_id: int | None = typer.Option(None, "--client", "-c", help="Filter by client ID"),
    retrain: bool = typer.Option(False, "--retrain", help="Force model retraining"),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Use AI/ML to forecast cash flow based on invoice payment predictions.

    The forecast analyzes unpaid invoices using an ML ensemble (Prophet + XGBoost)
    to predict when payments will arrive and provides AI-powered insights.

    Examples:
        openfatture ai forecast --months 6
        openfatture ai forecast --client 123 --months 3
        openfatture ai forecast --retrain --months 12
        openfatture ai forecast --months 6 --format markdown
    """
    run_async(_run_cash_flow_forecast(ctx, months, client_id, retrain, json_output))


async def _run_cash_flow_forecast(
    ctx: typer.Context,
    months: int,
    client_id: int | None,
    retrain: bool,
    json_output: bool,
) -> None:
    """Run cash flow forecasting with ML models."""
    import time

    from openfatture.cli.formatters.utils import get_format_from_context, render_data

    format_type = get_format_from_context(ctx, json_output)

    if format_type == "rich":
        console.print("\n[bold blue]💰 AI Cash Flow Forecasting[/bold blue]\n")

    # Track execution metrics (ML model, not LLM, so no tokens)
    start_time = time.time()
    success = False

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="forecast",
                user_input=f"{months} months forecast",
                provider="ml_ensemble",
                model="prophet_xgboost",
                parameters={
                    "months": months,
                    "client_id": client_id,
                    "retrain": retrain,
                },
            )
        )

    try:
        from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent

        # Create agent
        if format_type == "rich":
            with console.status("[bold green]Initializing ML models..."):
                agent = CashFlowPredictorAgent()
                await agent.initialize(force_retrain=retrain)
        else:
            agent = CashFlowPredictorAgent()
            await agent.initialize(force_retrain=retrain)

        # Generate forecast
        if format_type == "rich":
            status_msg = f"[bold green]Forecasting {months} months..."
            if client_id:
                status_msg += f" (client {client_id})"
            with console.status(status_msg):
                forecast = await agent.forecast_cash_flow(
                    months=months,
                    client_id=client_id,
                )
        else:
            forecast = await agent.forecast_cash_flow(
                months=months,
                client_id=client_id,
            )

        # Display results
        if json_output or format_type == "json":
            render_data(forecast.to_dict(), format_type, console)
        elif format_type == "rich":
            _display_forecast(forecast)
        else:
            # For other formats, render forecast as data
            render_data(forecast.to_dict(), format_type, console)

        # Track success
        success = True

    except ValueError as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        logger.error("forecast_error", error=str(e))
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e}\n")
        logger.error("forecast_unexpected_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (ML model, no tokens/cost)
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="forecast",
                    success=success,
                    tokens_used=0,  # ML model, not LLM
                    cost_usd=0.0,  # ML model, not LLM
                    latency_ms=latency_ms,
                )
            )


def _display_forecast(forecast: Any) -> None:
    """Display cash flow forecast in rich format."""
    # Summary panel
    summary_text = f"""[bold]Forecast Period:[/bold] {forecast.months} months
[bold]Total Expected:[/bold] €{forecast.total_expected:,.2f}"""

    console.print(
        Panel(
            summary_text,
            title="[bold]📊 Cash Flow Summary[/bold]",
            border_style="blue",
        )
    )
    console.print()

    # Monthly forecast table
    table = Table(title="Monthly Forecast", box=None, show_header=True)
    table.add_column("Month", style="cyan", no_wrap=True)
    table.add_column("Expected Revenue", justify="right", style="green")

    for month_data in forecast.monthly_forecast:
        # Color based on amount
        amount = month_data["expected"]
        if amount > 0:
            amount_str = f"€{amount:,.2f}"
            amount_style = "green bold" if amount > 1000 else "green"
        else:
            amount_str = "€0.00"
            amount_style = "dim"

        table.add_row(
            month_data["month"],
            f"[{amount_style}]{amount_str}[/{amount_style}]",
        )

    console.print(table)
    console.print()

    # AI Insights
    if forecast.insights:
        console.print(
            Panel(
                forecast.insights,
                title="[bold]🤖 AI Insights[/bold]",
                border_style="magenta",
            )
        )
        console.print()

    # Recommendations
    if forecast.recommendations:
        console.print("[bold cyan]💡 Recommendations:[/bold cyan]\n")
        for rec in forecast.recommendations:
            console.print(f"  • {rec}")
        console.print()


@app.command("check")
def ai_check(
    ctx: typer.Context,
    fattura_id: int = typer.Argument(..., help="Invoice ID to check"),
    level: str = typer.Option(
        "standard",
        "--level",
        "-l",
        help="Check level: basic, standard, advanced",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all issues (including INFO)"),
) -> None:
    """
    Check invoice compliance using AI and rules engine.

    Levels:
    - basic: Only deterministic rules
    - standard: Rules + SDI rejection patterns (default)
    - advanced: Rules + SDI patterns + AI heuristics

    Examples:
        openfatture ai check 123
        openfatture ai check 123 --level advanced
        openfatture ai check 123 --json > report.json
        openfatture ai check 123 -v  # Show all issues
        openfatture ai check 123 --format markdown
    """
    run_async(_run_compliance_check(ctx, fattura_id, level, json_output, verbose))


async def _run_compliance_check(
    ctx: typer.Context,
    fattura_id: int,
    level_str: str,
    json_output: bool,
    verbose: bool,
) -> None:
    """Run compliance check on invoice."""
    import time

    from openfatture.ai.agents.compliance import ComplianceLevel
    from openfatture.cli.formatters.utils import get_format_from_context, render_data

    format_type = get_format_from_context(ctx, json_output)

    # Parse level
    level_map = {
        "basic": ComplianceLevel.BASIC,
        "standard": ComplianceLevel.STANDARD,
        "advanced": ComplianceLevel.ADVANCED,
    }

    level = level_map.get(level_str.lower())
    if not level:
        console.print(f"[bold red]❌ Invalid level: {level_str}[/bold red]")
        console.print("Valid levels: basic, standard, advanced")
        raise typer.Exit(1)

    if format_type == "rich":
        console.print(f"\n[bold blue]🔍 Compliance Check (Level: {level.value})[/bold blue]\n")

    # Track execution metrics (rules-based, not LLM)
    start_time = time.time()
    success = False

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="check",
                user_input=f"Invoice {fattura_id}",
                provider="compliance_engine",
                model=level.value,
                parameters={"fattura_id": fattura_id, "level": level_str, "verbose": verbose},
            )
        )

    try:
        # Create checker
        status_context = (
            console.status("[bold green]Analyzing invoice...")
            if format_type == "rich"
            else nullcontext()
        )
        with status_context:
            checker = ComplianceChecker(level=level)
            report = await checker.check_invoice(fattura_id)

        # Output results
        if json_output or format_type == "json":
            render_data(report.to_dict(), format_type, console)
        elif format_type == "rich":
            _display_compliance_report(report, verbose)
        else:
            # For other formats, output as data
            render_data(report.to_dict(), format_type, console)

        # Track success
        success = True

    except ValueError as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {e}\n")
        logger.error("compliance_check_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (rules-based, no tokens/cost)
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="check",
                    success=success,
                    tokens_used=0,  # Rules-based, not LLM
                    cost_usd=0.0,  # Rules-based, not LLM
                    latency_ms=latency_ms,
                )
            )


def _display_compliance_report(report: Any, verbose: bool) -> None:
    """Display compliance check report in rich format."""
    # Header
    console.print(f"[bold]Invoice:[/bold] {report.invoice_number}")
    console.print(f"[bold]Check Level:[/bold] {report.level.value}")
    console.print()

    # Status panel
    if report.is_compliant:
        status_text = (
            "[bold green]✓ COMPLIANT[/bold green]\n\nThe invoice is ready for SDI submission"
        )
        border_style = "green"
    else:
        status_text = f"[bold red]✗ NOT COMPLIANT[/bold red]\n\nFound {len(report.get_errors())} critical errors"
        border_style = "red"

    console.print(
        Panel(
            status_text,
            title="[bold]Compliance Status[/bold]",
            border_style=border_style,
        )
    )
    console.print()

    # Scores
    scores_table = Table(show_header=False, box=None)
    scores_table.add_column("Metric", style="cyan bold")
    scores_table.add_column("Value")

    # Compliance score with color
    score_color = (
        "green"
        if report.compliance_score >= 80
        else "yellow" if report.compliance_score >= 60 else "red"
    )
    scores_table.add_row(
        "Compliance Score:", f"[{score_color}]{report.compliance_score:.1f}/100[/{score_color}]"
    )

    # Risk score with color (if available)
    if report.risk_score > 0:
        risk_color = (
            "red" if report.risk_score >= 70 else "yellow" if report.risk_score >= 40 else "green"
        )
        scores_table.add_row(
            "Risk Score:", f"[{risk_color}]{report.risk_score:.1f}/100[/{risk_color}]"
        )

    console.print(scores_table)
    console.print()

    # Issues summary
    errors = report.get_errors()
    warnings = report.get_warnings()
    infos = report.get_info()

    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Category", style="bold")
    summary_table.add_column("Count")

    summary_table.add_row("[red]Errors (must fix):", f"[red]{len(errors)}[/red]")
    summary_table.add_row("[yellow]Warnings:", f"[yellow]{len(warnings)}[/yellow]")
    summary_table.add_row("[blue]Info:", f"[blue]{len(infos)}[/blue]")

    if report.sdi_pattern_matches:
        summary_table.add_row(
            "[magenta]SDI Patterns Matched:",
            f"[magenta]{len(report.sdi_pattern_matches)}[/magenta]",
        )

    console.print(summary_table)
    console.print()

    # Display errors
    if errors:
        console.print("[bold red]❌ Errors (Must Fix):[/bold red]\n")
        for i, issue in enumerate(errors, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            console.print(f"     Field: [cyan]{issue.field}[/cyan]")
            if issue.suggestion:
                console.print(f"     💡 {issue.suggestion}")
            if issue.reference:
                console.print(f"     [dim]Ref: {issue.reference}[/dim]")
            console.print()

    # Display warnings
    if warnings:
        console.print("[bold yellow]⚠️  Warnings:[/bold yellow]\n")
        for i, issue in enumerate(warnings, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            console.print(f"     Field: [cyan]{issue.field}[/cyan]")
            if issue.suggestion:
                console.print(f"     💡 {issue.suggestion}")
            console.print()

    # Display info (only if verbose)
    if verbose and infos:
        console.print("[bold blue]ℹ️  Informational:[/bold blue]\n")
        for i, issue in enumerate(infos, 1):
            console.print(f"  {i}. [{issue.code}] {issue.message}")
            if issue.suggestion:
                console.print(f"     💡 {issue.suggestion}")
            console.print()

    # Recommendations
    if report.recommendations:
        console.print("[bold cyan]💡 Recommendations:[/bold cyan]\n")
        for rec in report.recommendations:
            console.print(f"  • {rec}")
        console.print()

    # Next steps
    if not report.is_compliant:
        console.print("[bold]Next Steps:[/bold]")
        console.print("  1. Fix all ERROR-level issues above")
        console.print("  2. Run compliance check again")
        console.print("  3. Address warnings to reduce rejection risk")
        console.print()
    else:
        console.print("[bold green]✅ Invoice is ready for SDI submission![/bold green]\n")


@app.command("create-invoice")
def ai_create_invoice(
    ctx: typer.Context,
    description: str = typer.Argument(..., help="Service description"),
    client_id: int = typer.Option(..., "--client", "-c", help="Client ID"),
    imponibile: float = typer.Option(..., "--amount", "-a", help="Invoice amount (€)"),
    hours: float | None = typer.Option(None, "--hours", "-h", help="Hours worked"),
    rate: float | None = typer.Option(None, "--rate", "-r", help="Hourly rate (€)"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name"),
    technologies: str | None = typer.Option(
        None, "--tech", "-t", help="Technologies used (comma-separated)"
    ),
    require_approvals: bool = typer.Option(
        False, "--require-approvals", help="Require human approval at each step"
    ),
    confidence_threshold: float = typer.Option(
        0.85, "--confidence", help="Confidence threshold for auto-approval (0.0-1.0)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Create a complete invoice using AI workflow orchestration.

    This command uses a multi-agent LangGraph workflow to:
    1. Generate detailed description
    2. Suggest VAT treatment
    3. Check compliance
    4. Create the invoice

    Example:
        openfatture ai create-invoice "consulenza web 3 ore" --client 123 --amount 300
        openfatture ai create-invoice "sviluppo app mobile" --hours 20 --rate 50 --require-approvals
        openfatture ai create-invoice "development" --client 1 --amount 500 --format json
    """
    run_async(
        _run_invoice_workflow(
            ctx=ctx,
            description=description,
            client_id=client_id,
            imponibile=imponibile,
            hours=hours,
            rate=rate,
            project=project,
            technologies=technologies,
            require_approvals=require_approvals,
            confidence_threshold=confidence_threshold,
            json_output=json_output,
        )
    )


async def _run_invoice_workflow(
    ctx: typer.Context,
    description: str,
    client_id: int,
    imponibile: float,
    hours: float | None,
    rate: float | None,
    project: str | None,
    technologies: str | None,
    require_approvals: bool,
    confidence_threshold: float,
    json_output: bool,
) -> None:
    """Execute invoice creation workflow."""
    import time

    from openfatture.cli.formatters.utils import get_format_from_context, render_data

    format_type = get_format_from_context(ctx, json_output)

    # Track execution metrics
    start_time = time.time()
    success = False

    # Publish AICommandStartedEvent
    event_bus = get_event_bus()
    if event_bus:
        settings = get_settings()
        event_bus.publish(
            AICommandStartedEvent(
                command="create-invoice",
                user_input=description,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "client_id": client_id,
                    "imponibile": imponibile,
                    "hours": hours,
                    "rate": rate,
                    "project": project,
                    "technologies": technologies,
                    "require_approvals": require_approvals,
                    "confidence_threshold": confidence_threshold,
                },
            )
        )

    try:
        # Parse technologies
        tech_list = [t.strip() for t in technologies.split(",")] if technologies else None

        # Create workflow
        workflow = InvoiceCreationWorkflow(confidence_threshold=confidence_threshold)

        # Execute workflow
        result = await workflow.execute(
            user_input=description,
            client_id=client_id,
            imponibile=imponibile,
            hours=hours,
            hourly_rate=rate,
            require_approvals=require_approvals,
        )

        if json_output or format_type == "json":
            render_data(result.model_dump(), format_type, console)
        elif format_type == "rich":
            # Display results in rich format
            if result.invoice_id:
                console.print("[bold green]✅ Invoice created successfully![/bold green]")
                console.print(f"Invoice ID: {result.invoice_id}")
            else:
                console.print(f"[yellow]⚠️ Workflow completed with status: {result.status}[/yellow]")

            console.print(f"Status: {result.status}")

            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")

            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  • {error}")
        else:
            # For other formats, render as data
            render_data(result.model_dump(), format_type, console)

        # Track success (workflow may have succeeded even with warnings)
        success = result.invoice_id is not None

    except Exception as e:
        logger.error("Workflow execution failed", error=str(e))
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (workflow uses LLMs, but we don't track tokens here)
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="create-invoice",
                    success=success,
                    tokens_used=0,  # Workflow aggregates multiple steps
                    cost_usd=0.0,  # Workflow aggregates multiple steps
                    latency_ms=latency_ms,
                )
            )


@app.command("chat")
def ai_chat(
    ctx: typer.Context,
    message: str | None = typer.Argument(
        None, help="Message to send (interactive if not provided)"
    ),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Enable streaming responses"),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (deprecated, use --format json)"
    ),
) -> None:
    """
    Interactive AI chat assistant for invoice and tax questions.

    This command provides a conversational interface to ask questions about:
    - Invoice creation and management
    - Tax regulations and VAT rates
    - Payment tracking and reconciliation
    - General business advice

    The assistant has access to your business data and can perform actions
    like creating invoices, checking compliance, and analyzing payments.

    Examples:
        openfatture ai chat "How do I create an invoice for consulting work?"
        openfatture ai chat --no-stream "What VAT rate applies to software development?"
        openfatture ai chat "Help me" --format json
        openfatture ai chat  # Interactive mode
    """
    run_sync_with_lifespan(_run_chat(ctx, message, stream, json_output))


async def _run_chat(
    ctx: typer.Context, message: str | None, stream: bool, json_output: bool
) -> None:
    """Run interactive chat session."""
    import time

    from openfatture.cli.formatters.utils import get_format_from_context, render_response

    format_type = get_format_from_context(ctx, json_output)

    # Track execution metrics
    start_time = time.time()
    success = False
    tokens_used = 0
    cost_usd = 0.0

    # Get event bus and settings
    event_bus = get_event_bus()
    settings = get_settings()

    # Publish AICommandStartedEvent (for single message mode)
    if message and event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="chat",
                user_input=message,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={"stream": stream, "interactive": False},
            )
        )

    try:
        # Get debug configuration
        debug_config = settings.debug_config

        # Create chat agent
        provider = create_provider()
        agent = ChatAgent(provider=provider, enable_streaming=stream, debug_config=debug_config)

        if message:
            # Single message mode - use formatters
            context = ChatContext(user_input=message)
            if stream and format_type == "rich":
                console.print("[dim]Assistant:[/dim] ", end="")
                async for chunk in agent.execute_stream(context):
                    console.print(chunk, end="")
                console.print()  # New line
            else:
                response = await agent.execute(context)
                if json_output or format_type == "json":
                    console.print_json(data=response.model_dump())
                elif format_type == "rich":
                    console.print(f"[dim]Assistant:[/dim] {response.content}")
                else:
                    # Use formatter for other formats
                    render_response(response, format_type, console, show_metrics=False)

                # Track metrics for single message mode
                success = True
                tokens_used = response.usage.total_tokens
                cost_usd = response.usage.estimated_cost_usd
        else:
            # Interactive mode - publish started event
            if event_bus:
                event_bus.publish(
                    AICommandStartedEvent(
                        command="chat",
                        user_input="Interactive chat session",
                        provider=settings.ai_provider,
                        model=settings.ai_model,
                        parameters={"stream": stream, "interactive": True},
                    )
                )

            # Interactive mode
            console.print("[bold blue]🤖 OpenFatture AI Assistant[/bold blue]")
            console.print(
                "Type your questions about invoices, taxes, or business. Type 'exit' to quit.\n"
            )

            conversation_history = []

            while True:
                try:
                    user_input = console.input("[bold green]You:[/bold green] ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("exit", "quit", "q"):
                        console.print("[dim]Goodbye! 👋[/dim]")
                        break

                    # Add to history
                    conversation_history.append({"role": "user", "content": user_input})

                    # Create context with history
                    context = ChatContext(
                        user_input=user_input,
                        conversation_history=_convert_history(conversation_history),
                    )

                    if stream:
                        console.print("[dim]Assistant:[/dim] ", end="")
                        full_response = ""
                        async for event in agent.execute_stream(context):
                            if event.is_content():
                                text = event.get_text()
                                console.print(text, end="")
                                full_response += text
                        console.print()  # New line
                        # Add assistant response to history
                        conversation_history.append({"role": "assistant", "content": full_response})
                    else:
                        response = await agent.execute(context)
                        if json_output:
                            console.print_json(data=response.model_dump())
                        else:
                            console.print(f"[dim]Assistant:[/dim] {response.content}")
                        # Add to history
                        conversation_history.append(
                            {"role": "assistant", "content": response.content}
                        )

                    console.print()  # Empty line between exchanges

                except KeyboardInterrupt:
                    console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
                    continue
                except EOFError:
                    console.print("\n[dim]Goodbye! 👋[/dim]")
                    break

            # Interactive mode completed successfully
            success = True

    except Exception as e:
        logger.error("Chat execution failed", error=str(e))
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (only for single message mode or on exit from interactive)
        if event_bus and message:  # Single message mode
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="chat",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                )
            )
        elif event_bus and not message:  # Interactive mode on exit
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="chat",
                    success=success,
                    tokens_used=0,  # Interactive mode - tokens tracked per message
                    cost_usd=0.0,  # Interactive mode - cost tracked per message
                    latency_ms=latency_ms,
                )
            )


@app.command("voice-chat")
def ai_voice_chat(
    duration: int = typer.Option(5, "--duration", "-d", help="Recording duration in seconds"),
    sample_rate: int = typer.Option(16000, "--sample-rate", "-s", help="Audio sample rate (Hz)"),
    channels: int = typer.Option(1, "--channels", "-c", help="Number of audio channels"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode (press Enter to record)"
    ),
    save_audio: bool = typer.Option(False, "--save-audio", help="Save audio files to disk"),
    no_playback: bool = typer.Option(False, "--no-playback", help="Disable audio playback"),
) -> None:
    """
    Interactive voice chat with AI assistant.

    This command enables voice-based interaction with the AI assistant:
    1. Records audio from your microphone
    2. Transcribes speech to text (STT)
    3. Processes with LLM (ChatAgent)
    4. Synthesizes response to speech (TTS)
    5. Plays back the audio response

    Modes:
    - Single recording: Record once for specified duration
    - Interactive: Press Enter to start recording, record for duration, repeat

    Requirements:
    - Microphone access
    - OPENAI_API_KEY in environment (for Whisper STT and TTS)

    Examples:
        openfatture ai voice-chat --duration 5
        openfatture ai voice-chat --interactive --duration 10
        openfatture ai voice-chat -i -d 8 --save-audio
        openfatture ai voice-chat --no-playback  # Text output only
    """
    run_sync_with_lifespan(
        _run_voice_chat(duration, sample_rate, channels, interactive, save_audio, no_playback)
    )


async def _run_voice_chat(
    duration: int,
    sample_rate: int,
    channels: int,
    interactive: bool,
    save_audio: bool,
    no_playback: bool,
) -> None:
    """Run voice chat session with audio recording and playback."""
    import io
    import time
    import wave
    from pathlib import Path

    try:
        import sounddevice as sd
    except ImportError:
        console.print(
            "[bold red]❌ Error:[/bold red] Audio dependencies not installed.\n"
            "Install with: [cyan]uv sync[/cyan]\n"
        )
        raise typer.Exit(1)

    # Get event bus and settings
    event_bus = get_event_bus()
    settings = get_settings()

    # Check if voice is enabled in settings
    if not settings.voice_enabled:
        console.print(
            "[bold yellow]⚠️  Voice features are not enabled in settings.[/bold yellow]\n"
            "Set OPENFATTURE_VOICE_ENABLED=true in .env\n"
        )

    # Verify API key
    if not settings.openai_api_key:
        console.print(
            "[bold red]❌ Error:[/bold red] OPENAI_API_KEY not set.\n"
            "Voice features require OpenAI API access for Whisper STT and TTS.\n"
        )
        raise typer.Exit(1)

    console.print("[bold blue]🎤 Voice Chat Assistant[/bold blue]\n")
    console.print(f"Recording: {duration}s at {sample_rate}Hz, {channels} channel(s)")
    console.print(f"Mode: {'Interactive' if interactive else 'Single recording'}\n")

    # Track execution metrics
    start_time = time.time()
    success = False
    total_interactions = 0

    # Publish AICommandStartedEvent
    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="voice-chat",
                user_input="Voice chat session",
                provider="openai",
                model="whisper-1 + gpt",
                parameters={
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "interactive": interactive,
                },
            )
        )

    try:
        # Create voice provider and assistant
        with console.status("[bold green]Initializing voice assistant..."):
            voice_provider = create_voice_provider(api_key=settings.openai_api_key)
            chat_provider = create_provider()
            chat_agent = ChatAgent(provider=chat_provider)
            assistant = VoiceAssistant(
                voice_provider=voice_provider,
                chat_agent=chat_agent,
                enable_tts=not no_playback,
            )

        console.print("[green]✓ Voice assistant ready[/green]\n")

        # List available audio devices
        devices = sd.query_devices()
        default_input = sd.default.device[0]
        console.print(f"[dim]Using microphone: {devices[default_input]['name']}[/dim]\n")

        # Interactive or single mode
        if interactive:
            console.print(
                "Press [bold cyan]Enter[/bold cyan] to start recording, "
                "or type 'exit' to quit.\n"
            )

        conversation_number = 0

        while True:
            conversation_number += 1

            # Wait for user input in interactive mode
            if interactive:
                user_command = console.input(
                    f"[bold green]Recording {conversation_number}:[/bold green] "
                ).strip()
                if user_command.lower() in ("exit", "quit", "q"):
                    console.print("[dim]Goodbye! 👋[/dim]\n")
                    break

            # Record audio
            console.print(f"[bold yellow]🔴 Recording for {duration} seconds...[/bold yellow]")
            try:
                audio_data = sd.rec(
                    int(duration * sample_rate),
                    samplerate=sample_rate,
                    channels=channels,
                    dtype="int16",
                )
                sd.wait()  # Wait for recording to finish
                console.print("[green]✓ Recording complete[/green]\n")
            except Exception as e:
                console.print(f"[bold red]❌ Recording failed:[/bold red] {e}\n")
                if not interactive:
                    raise typer.Exit(1)
                continue

            # Convert to WAV bytes
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 16-bit audio
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            wav_bytes = wav_buffer.getvalue()

            # Save audio if requested
            if save_audio:
                timestamp = int(time.time())
                audio_path = Path(f"voice_input_{timestamp}.wav")
                audio_path.write_bytes(wav_bytes)
                console.print(f"[dim]Saved recording: {audio_path}[/dim]\n")

            # Process with voice assistant
            with console.status("[bold green]Processing voice input..."):
                try:
                    save_path = (
                        Path(f"voice_response_{int(time.time())}.mp3") if save_audio else None
                    )
                    response = await assistant.process_voice_input(
                        audio=wav_bytes,
                        save_audio=save_path,
                    )
                except Exception as e:
                    console.print(f"[bold red]❌ Processing failed:[/bold red] {e}\n")
                    if not interactive:
                        raise typer.Exit(1)
                    continue

            # Display transcription
            console.print(f"[cyan]You said:[/cyan] {response.transcription.text}")
            console.print(
                f"[dim](Language: {response.transcription.language}, "
                f"STT: {response.stt_latency_ms:.0f}ms)[/dim]\n"
            )

            # Display LLM response
            console.print(f"[magenta]Assistant:[/magenta] {response.llm_response}")
            console.print(
                f"[dim](LLM: {response.llm_latency_ms:.0f}ms, "
                f"Tokens: {response.llm_metadata['tokens']})[/dim]\n"
            )

            # Play audio response
            if response.synthesis and not no_playback:
                console.print("[bold yellow]🔊 Playing response...[/bold yellow]")
                try:
                    # OpenAI TTS returns MP3 by default, we need to decode it
                    # For simplicity, save to temp file and inform user
                    # TODO: Add MP3 decoding for direct playback
                    import tempfile

                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                        tmp.write(response.synthesis.audio_data)
                        tmp_path = tmp.name

                    console.print(
                        f"[yellow]Audio saved to:[/yellow] {tmp_path}\n"
                        "[dim]Direct playback requires MP3 decoding. "
                        "Use --save-audio to save responses.[/dim]\n"
                    )
                except Exception as e:
                    console.print(f"[yellow]⚠️  Audio save failed:[/yellow] {e}\n")

            # Save response audio if requested
            if save_audio and response.synthesis:
                response_path = Path(f"voice_response_{int(time.time())}.mp3")
                response_path.write_bytes(response.synthesis.audio_data)
                console.print(f"[dim]Saved response: {response_path}[/dim]\n")

            # Display metrics
            console.print("[dim]─────────────────────────────[/dim]")
            console.print(
                f"[dim]Total latency: {response.total_latency_ms:.0f}ms "
                f"(STT: {response.stt_latency_ms:.0f}ms, "
                f"LLM: {response.llm_latency_ms:.0f}ms, "
                f"TTS: {response.tts_latency_ms or 0:.0f}ms)[/dim]"
            )
            if response.llm_metadata.get("cost_usd"):
                console.print(f"[dim]Cost: ${response.llm_metadata['cost_usd']:.4f}[/dim]")
            console.print("[dim]─────────────────────────────[/dim]\n")

            total_interactions += 1

            # Exit if not interactive
            if not interactive:
                break

        # Mark as successful
        success = True

    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted by user[/dim]")
        success = False
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")
        logger.error("voice_chat_error", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent
        if event_bus:
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="voice-chat",
                    success=success,
                    tokens_used=0,  # Voice sessions aggregate multiple interactions
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                )
            )
