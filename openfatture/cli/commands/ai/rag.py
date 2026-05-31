"""RAG knowledge base commands."""

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.rag.config import get_rag_config
from openfatture.ai.rag.knowledge_indexer import KnowledgeIndexer
from openfatture.utils.async_bridge import run_async

from ._app import console, rag_app


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
            "" if source.enabled else "",
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
        f"\n[bold green]Indicizzazione completata:[/bold green] {chunks} chunk aggiornati."
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
