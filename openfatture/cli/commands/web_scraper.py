"""CLI commands for regulatory web scraping."""

import json

import typer
from rich.console import Console
from rich.table import Table

from ...web_scraper.config import get_web_scraper_config
from ...web_scraper.service import RegulatoryUpdateService

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def status():
    """Show web scraper status and cache information."""
    try:
        config = get_web_scraper_config()
        service = RegulatoryUpdateService(config)

        # For sync CLI, we'll show basic config info
        status_info = {
            "is_running": False,
            "last_check_time": None,
            "check_interval_hours": config.check_interval_hours,
            "should_check": True,
            "config": {
                "enabled": config.enabled,
                "require_human_review": config.require_human_review,
                "auto_update_threshold": config.auto_update_threshold,
            },
        }

        console.print("\n[bold blue]Regulatory Web Scraper Status[/bold blue]")
        console.print(f"Enabled: {'✅' if config.enabled else '❌'}")
        console.print(f"Running: {'✅' if status_info['is_running'] else '❌'}")
        console.print(f"Check Interval: {config.check_interval_hours} hours")
        console.print(f"Require Human Review: {'✅' if config.require_human_review else '❌'}")
        console.print(f"Auto Update Threshold: {config.auto_update_threshold}")
        console.print(f"Should Check Now: {'✅' if status_info['should_check'] else '❌'}")

        if status_info["last_check_time"]:
            console.print(f"Last Check: {status_info['last_check_time']}")
        else:
            console.print("Last Check: Never")

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
async def check_updates(
    force: bool = typer.Option(False, "--force", "-f", help="Force check even if not due"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Check for regulatory updates from configured sources."""
    try:
        config = get_web_scraper_config()

        if not config.enabled:
            console.print("[yellow]Web scraper is disabled in configuration[/yellow]")
            raise typer.Exit(1)

        # Initialize service (would need LLM provider in real implementation)
        service = RegulatoryUpdateService(config)

        # For demo purposes, we'll skip LLM initialization
        # In real implementation: service.set_llm_provider(llm_provider)

        if not force and not service.should_check_for_updates():
            console.print("[yellow]Not yet time for update check[/yellow]")
            console.print("Use --force to check anyway")
            raise typer.Exit(0)

        console.print("[bold blue]Checking for regulatory updates...[/bold blue]")

        with console.status("[bold green]Scanning sources...[/bold green]"):
            results = await service.check_for_updates()

        # Display results
        console.print("\n[bold green]Update Check Completed[/bold green]")
        console.print(f"Status: {results['status']}")
        console.print(f"Sources Checked: {results['sources_checked']}")
        console.print(f"Documents Processed: {results['documents_processed']}")
        console.print(f"Changes Detected: {results['changes_detected']}")
        console.print(f"Errors: {results['errors']}")

        if verbose and results.get("source_results"):
            console.print("\n[bold]Source Results:[/bold]")
            table = Table()
            table.add_column("Source ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Documents", style="yellow")
            table.add_column("Changes", style="red")

            for source_result in results["source_results"]:
                if isinstance(source_result, dict):
                    table.add_row(
                        source_result.get("source_id", "N/A"),
                        source_result.get("status", "unknown"),
                        str(source_result.get("documents_processed", 0)),
                        str(source_result.get("changes_detected", 0)),
                    )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error checking updates: {e}[/red]")
        raise typer.Exit(1)


@app.command()
async def list_sources():
    """List configured regulatory sources."""
    try:
        config = get_web_scraper_config()
        sources_config_path = config.sources_config_path

        if not sources_config_path.exists():
            console.print(f"[red]Sources config not found: {sources_config_path}[/red]")
            raise typer.Exit(1)

        with open(sources_config_path, encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])

        if not sources:
            console.print("[yellow]No sources configured[/yellow]")
            return

        console.print(f"\n[bold blue]Configured Regulatory Sources ({len(sources)})[/bold blue]")

        table = Table()
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Category", style="green")
        table.add_column("Priority", style="yellow", justify="right")
        table.add_column("Enabled", style="magenta")
        table.add_column("Official", style="blue")

        for source in sources:
            table.add_row(
                source["id"],
                source["name"][:50] + "..." if len(source["name"]) > 50 else source["name"],
                source.get("category", "N/A"),
                str(source.get("priority", 1)),
                "✅" if source.get("enabled", True) else "❌",
                "✅" if source.get("official_source", False) else "❌",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing sources: {e}[/red]")
        raise typer.Exit(1)


@app.command()
async def show_source(source_id: str):
    """Show detailed information about a regulatory source."""
    try:
        config = get_web_scraper_config()
        sources_config_path = config.sources_config_path

        if not sources_config_path.exists():
            console.print(f"[red]Sources config not found: {sources_config_path}[/red]")
            raise typer.Exit(1)

        with open(sources_config_path, encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        source = next((s for s in sources if s["id"] == source_id), None)

        if not source:
            console.print(f"[red]Source not found: {source_id}[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold blue]Regulatory Source: {source['id']}[/bold blue]")
        console.print(f"Name: {source['name']}")
        console.print(f"URL: {source['url']}")
        console.print(f"Category: {source.get('category', 'N/A')}")
        console.print(f"Jurisdiction: {source.get('jurisdiction', 'N/A')}")
        console.print(f"Priority: {source.get('priority', 1)}")
        console.print(f"Enabled: {'✅' if source.get('enabled', True) else '❌'}")
        console.print(f"Official Source: {'✅' if source.get('official_source', False) else '❌'}")
        console.print(f"Content Type: {source.get('content_type', 'html')}")
        console.print(f"Follow Links: {'✅' if source.get('follow_links', False) else '❌'}")

        if source.get("description"):
            console.print(f"Description: {source['description']}")

        if source.get("tags"):
            console.print(f"Tags: {', '.join(source['tags'])}")

        if source.get("selectors"):
            console.print("Selectors:")
            for key, selector in source["selectors"].items():
                console.print(f"  {key}: {selector}")

    except Exception as e:
        console.print(f"[red]Error showing source: {e}[/red]")
        raise typer.Exit(1)


@app.command()
async def test_scraper(
    url: str | None = typer.Option(None, "--url", help="Test URL to scrape"),
    source_id: str | None = typer.Option(None, "--source", help="Test specific source"),
):
    """Test web scraper functionality."""
    try:
        config = get_web_scraper_config()

        if not config.enabled:
            console.print("[yellow]Web scraper is disabled in configuration[/yellow]")
            raise typer.Exit(1)

        # Initialize scraper
        from ...web_scraper.scraper import RegulatoryWebScraper

        scraper = RegulatoryWebScraper(config)

        if url:
            # Test direct URL
            console.print(f"[bold blue]Testing scraper with URL: {url}[/bold blue]")

            async with scraper:
                # This would require a RegulatorySource object
                console.print("[yellow]Direct URL testing not yet implemented[/yellow]")
                console.print("Use --source to test a configured source")

        elif source_id:
            # Test configured source
            console.print(f"[bold blue]Testing scraper with source: {source_id}[/bold blue]")

            # Load source config
            sources_config_path = config.sources_config_path
            if not sources_config_path.exists():
                console.print(f"[red]Sources config not found: {sources_config_path}[/red]")
                raise typer.Exit(1)

            with open(sources_config_path, encoding="utf-8") as f:
                data = json.load(f)

            sources = data.get("sources", [])
            source_data = next((s for s in sources if s["id"] == source_id), None)

            if not source_data:
                console.print(f"[red]Source not found: {source_id}[/red]")
                raise typer.Exit(1)

            from ...web_scraper.models import RegulatorySource

            source = RegulatorySource(**source_data)

            async with scraper:
                with console.status("[bold green]Scraping test page...[/bold green]"):
                    documents = await scraper.scrape_source(source)

                console.print("[green]Test completed successfully![/green]")
                console.print(f"Documents scraped: {len(documents)}")

                if documents:
                    console.print("\n[bold]Sample Document:[/bold]")
                    doc = documents[0]
                    console.print(f"Title: {doc.title}")
                    console.print(f"Content Length: {len(doc.content)} characters")
                    console.print(f"Status: {doc.status}")
        else:
            console.print("[red]Must specify either --url or --source[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error testing scraper: {e}[/red]")
        raise typer.Exit(1)


@app.command()
async def clean_cache():
    """Clean web scraper cache and temporary files."""
    try:
        config = get_web_scraper_config()

        cache_dir = config.cache_dir
        temp_dir = config.temp_dir

        cleaned_files = 0
        cleaned_size = 0

        # Clean cache directory
        if cache_dir.exists():
            for file_path in cache_dir.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_files += 1
                    cleaned_size += size

        # Clean temp directory
        if temp_dir.exists():
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_files += 1
                    cleaned_size += size

        console.print("[green]Cache cleaned successfully![/green]")
        console.print(f"Files removed: {cleaned_files}")
        console.print(f"Space freed: {cleaned_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        console.print(f"[red]Error cleaning cache: {e}[/red]")
        raise typer.Exit(1)
