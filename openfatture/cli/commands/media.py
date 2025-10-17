#!/usr/bin/env python3
"""
Media automation commands for OpenFatture.

Provides commands for generating VHS tape files from templates,
validating templates, and managing media automation.
"""

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="media",
    help="Media automation commands for VHS tape generation and management",
    no_args_is_help=True,
)

console = Console()

# Template engine will be called as subprocess for now
# TODO: Refactor to proper import once module structure is finalized


@app.command()
def template(
    action: str = typer.Argument(..., help="Action to perform: generate, list, validate"),
    scenario: str | None = typer.Option(
        None, "--scenario", "-s", help="Scenario ID (A, B, C, D, E)"
    ),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    variables: str | None = typer.Option(
        None, "--variables", "-v", help="Custom variables as JSON string"
    ),
):
    """
    Manage VHS tape templates.

    Actions:
    - generate: Generate VHS tape from template
    - list: List available scenarios
    - validate: Validate template syntax
    """
    try:
        template_script = (
            Path(__file__).parent.parent.parent.parent
            / "media"
            / "automation"
            / "templates"
            / "base_template.py"
        )

        if not template_script.exists():
            console.print("[red]Error: Template engine not found[/red]")
            console.print(f"[dim]Expected at: {template_script}[/dim]")
            raise typer.Exit(1)

        if action == "list":
            # For list, we need to implement it here since the script doesn't have this functionality
            console.print("[yellow]List functionality not yet implemented in CLI[/yellow]")
            console.print("[dim]Use: python media/automation/templates/base_template.py list[/dim]")

        elif action == "validate":
            if not scenario:
                console.print("[red]Error: --scenario required for validate action[/red]")
                raise typer.Exit(1)

            result = subprocess.run(
                [sys.executable, str(template_script), "validate", "--scenario", scenario],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
            )

            if result.returncode == 0:
                console.print(f"[green]✓ Scenario {scenario} template is valid[/green]")
            else:
                console.print(f"[red]✗ Scenario {scenario} template is invalid[/red]")
                if result.stderr:
                    console.print(f"[dim]{result.stderr.strip()}[/dim]")
                raise typer.Exit(1)

        elif action == "generate":
            if not scenario:
                console.print("[red]Error: --scenario required for generate action[/red]")
                raise typer.Exit(1)

            cmd = [sys.executable, str(template_script), "generate", "--scenario", scenario]

            if output:
                cmd.extend(["--output", output])
            if variables:
                cmd.extend(["--variables", variables])

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

            if result.returncode == 0:
                # Extract output path from stdout
                for line in result.stdout.split("\n"):
                    if "Generated VHS tape:" in line:
                        output_path = line.split(": ")[1].strip()
                        console.print(f"[green]✓ Generated VHS tape: {output_path}[/green]")

                        # Show file size
                        if Path(output_path).exists():
                            file_size = Path(output_path).stat().st_size
                            console.print(f"[dim]File size: {file_size:,} bytes[/dim]")
                        break
                else:
                    console.print("[green]✓ VHS tape generated successfully[/green]")
            else:
                console.print("[red]Error generating VHS tape[/red]")
                if result.stderr:
                    console.print(f"[dim]{result.stderr.strip()}[/dim]")
                raise typer.Exit(1)

        else:
            console.print(f"[red]Error: Unknown action '{action}'[/red]")
            console.print("[dim]Available actions: generate, list, validate[/dim]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def check():
    """
    Check media automation prerequisites and status.
    """
    console.print("[bold]Media Automation Check[/bold]")
    console.print()

    # Check VHS
    vhs_available = False
    try:
        import subprocess

        result = subprocess.run(["vhs", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            vhs_available = True
            console.print(f"[green]✓ VHS:[/green] {result.stdout.strip()}")
        else:
            console.print("[red]✗ VHS: Not available[/red]")
    except FileNotFoundError:
        console.print("[red]✗ VHS: Not installed[/red]")

    # Check ffmpeg
    ffmpeg_available = False
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            ffmpeg_available = True
            version_line = result.stdout.split("\n")[0]
            console.print(f"[green]✓ ffmpeg:[/green] {version_line}")
        else:
            console.print("[red]✗ ffmpeg: Not available[/red]")
    except FileNotFoundError:
        console.print("[red]✗ ffmpeg: Not installed[/red]")

    # Check template engine
    template_dir = Path("media/automation/templates")
    if template_dir.exists():
        console.print(f"[green]✓ Template directory:[/green] {template_dir}")

        # Count templates
        scenario_templates = list(template_dir.glob("scenarios/*.tape.j2"))
        console.print(f"[green]✓ Scenario templates:[/green] {len(scenario_templates)} found")

        # Count components
        components = list(template_dir.glob("components/*.tapeinc"))
        console.print(f"[green]✓ Components:[/green] {len(components)} found")

        # Check variables file
        variables_file = template_dir / "variables.yaml"
        if variables_file.exists():
            console.print("[green]✓ Variables file:[/green] Found")
        else:
            console.print("[red]✗ Variables file: Missing[/red]")
    else:
        console.print("[red]✗ Template directory: Not found[/red]")

    # Overall status
    console.print()
    if vhs_available and ffmpeg_available and template_dir.exists():
        console.print("[green]🎬 Media automation is ready![/green]")
    else:
        console.print("[yellow]⚠️  Some prerequisites are missing[/yellow]")
        console.print("[dim]Run 'uv run openfatture media setup' to install missing tools[/dim]")


@app.command()
def setup():
    """
    Setup media automation tools and directories.
    """
    console.print("[bold]Setting up Media Automation[/bold]")
    console.print()

    # Create directories
    dirs_to_create = [
        "media/automation/templates/components",
        "media/automation/templates/scenarios",
        "media/output",
        "media/screenshots/v2025",
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓ Created directory:[/green] {dir_path}")

    # Check for required files
    required_files = [
        "media/automation/templates/base_template.py",
        "media/automation/templates/variables.yaml",
    ]

    for file_path in required_files:
        if Path(file_path).exists():
            console.print(f"[green]✓ Found:[/green] {file_path}")
        else:
            console.print(f"[red]✗ Missing:[/red] {file_path}")

    console.print()
    console.print("[green]✓ Media automation setup complete![/green]")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print("  1. Install VHS: brew install vhs")
    console.print("  2. Install ffmpeg: brew install ffmpeg")
    console.print("  3. Generate tapes: openfatture media template generate --scenario A")


@app.command()
def info():
    """
    Show media automation information and statistics.
    """
    console.print("[bold]Media Automation Info[/bold]")
    console.print()

    # Template statistics
    template_dir = Path("media/automation/templates")
    if template_dir.exists():
        scenarios = len(list(template_dir.glob("scenarios/*.tape.j2")))
        components = len(list(template_dir.glob("components/*.tapeinc")))

        console.print(f"[cyan]Templates:[/cyan] {scenarios} scenarios, {components} components")

    # Output statistics
    output_dir = Path("media/output")
    if output_dir.exists():
        videos = len(list(output_dir.glob("*.mp4")))
        gifs = len(list(output_dir.glob("*.gif")))
        total_size = sum(f.stat().st_size for f in output_dir.glob("*") if f.is_file())

        console.print(f"[cyan]Generated files:[/cyan] {videos} videos, {gifs} GIFs")
        console.print(f"[cyan]Total size:[/cyan] {total_size / (1024 * 1024):.1f} MB")

    # Recent activity
    console.print()
    console.print("[bold]Recent Activity[/bold]")

    # Check for recent tape files
    tape_files = list(Path("media/automation").glob("scenario_*.tape"))
    if tape_files:
        # Sort by modification time
        tape_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        recent = tape_files[:3]

        for tape_file in recent:
            mtime = tape_file.stat().st_mtime
            from datetime import datetime

            dt = datetime.fromtimestamp(mtime)
            console.print(f"[dim]{dt.strftime('%Y-%m-%d %H:%M')}: Generated {tape_file.name}[/dim]")
    else:
        console.print("[dim]No recent tape generations[/dim]")


if __name__ == "__main__":
    app()
