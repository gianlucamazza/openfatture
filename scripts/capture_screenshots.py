#!/usr/bin/env python3
"""
Automated screenshot capture with Playwright for media automation.

Usage:
    uv run python scripts/capture_screenshots.py --scenario A
    uv run python scripts/capture_screenshots.py --all
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def run_command(cmd: str, capture: bool = True, timeout: int = 30) -> dict[str, Any]:
    """Execute shell command and capture output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip() if capture else "",
            "stderr": result.stderr.strip() if capture else "",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }


def capture_cli_output(command: str, scenario: str, step: str, output_dir: Path) -> dict[str, Any]:
    """Capture CLI command output as text and metadata."""
    print(f"  → Capturing: {command}")

    result = run_command(f"uv run {command}")

    # Save metadata
    metadata = {
        "scenario": scenario,
        "step": step,
        "command": command,
        "timestamp": datetime.now().isoformat(),
        "success": result["success"],
        "output_length": len(result["stdout"]),
    }

    # Generate filename
    safe_step = step.lower().replace(" ", "_").replace("/", "-")
    filename_base = f"{scenario.lower()}_{safe_step}"

    # Save output text
    text_file = output_dir / f"{filename_base}.txt"
    text_file.write_text(result["stdout"] + "\n")

    # Save metadata JSON
    meta_file = output_dir / f"{filename_base}.json"
    meta_file.write_text(json.dumps(metadata, indent=2))

    print(f"    ✓ Saved: {text_file.name}")
    return metadata


def capture_scenario_a(output_dir: Path) -> list[dict[str, Any]]:
    """Capture screenshots for Scenario A - Onboarding & Setup."""
    print("\n📸 Scenario A: Onboarding & Setup")

    captures = []

    # Step 1: Config show
    captures.append(
        capture_cli_output(
            "openfatture config show",
            "A",
            "01_config_show",
            output_dir,
        )
    )

    # Step 2: Version
    captures.append(
        capture_cli_output(
            "openfatture --version",
            "A",
            "02_version",
            output_dir,
        )
    )

    # Step 3: Help
    captures.append(
        capture_cli_output(
            "openfatture --help",
            "A",
            "03_help",
            output_dir,
        )
    )

    return captures


def capture_scenario_b(output_dir: Path) -> list[dict[str, Any]]:
    """Capture screenshots for Scenario B - Invoice Creation."""
    print("\n📸 Scenario B: Invoice Creation")

    captures = []

    # Step 1: List clients
    captures.append(
        capture_cli_output(
            "openfatture cliente list",
            "B",
            "01_cliente_list",
            output_dir,
        )
    )

    # Step 2: List invoices
    captures.append(
        capture_cli_output(
            "openfatture fattura list",
            "B",
            "02_fattura_list",
            output_dir,
        )
    )

    # Step 3: Show invoice details
    captures.append(
        capture_cli_output(
            "openfatture fattura show 1",
            "B",
            "03_fattura_show",
            output_dir,
        )
    )

    return captures


def capture_scenario_c(output_dir: Path) -> list[dict[str, Any]]:
    """Capture screenshots for Scenario C - AI Assistant."""
    print("\n📸 Scenario C: AI Assistant (Ollama)")

    captures = []

    # Step 1: AI help
    captures.append(
        capture_cli_output(
            "openfatture ai --help",
            "C",
            "01_ai_help",
            output_dir,
        )
    )

    # Note: AI chat commands may take longer and depend on Ollama
    print("    ⚠️  Skipping AI inference commands (require Ollama and can be slow)")

    return captures


def capture_scenario_d(output_dir: Path) -> list[dict[str, Any]]:
    """Capture screenshots for Scenario D - Batch Operations."""
    print("\n📸 Scenario D: Batch Operations")

    captures = []

    # Step 1: Batch help
    captures.append(
        capture_cli_output(
            "openfatture batch --help",
            "D",
            "01_batch_help",
            output_dir,
        )
    )

    return captures


def capture_scenario_e(output_dir: Path) -> list[dict[str, Any]]:
    """Capture screenshots for Scenario E - PEC & SDI."""
    print("\n📸 Scenario E: PEC & SDI Notifications")

    captures = []

    # Step 1: PEC help
    captures.append(
        capture_cli_output(
            "openfatture pec --help",
            "E",
            "01_pec_help",
            output_dir,
        )
    )

    # Step 2: Notifications help
    captures.append(
        capture_cli_output(
            "openfatture notifiche --help",
            "E",
            "02_notifiche_help",
            output_dir,
        )
    )

    return captures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated screenshot capture for OpenFatture media automation."
    )
    parser.add_argument(
        "--scenario",
        choices=["A", "B", "C", "D", "E"],
        help="Scenario storyboard identifier (A-E).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Capture all scenarios.",
    )
    parser.add_argument(
        "--output-dir",
        default="media/screenshots/v2025",
        help="Destination directory for screenshots.",
    )
    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.scenario:
        parser.error("Either --scenario or --all must be specified")

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🎬 OpenFatture Screenshot Automation")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print()

    # Determine scenarios to capture
    scenarios = ["A", "B", "C", "D", "E"] if args.all else [args.scenario]

    # Capture each scenario
    all_captures: list[dict[str, Any]] = []

    for scenario in scenarios:
        if scenario == "A":
            all_captures.extend(capture_scenario_a(output_dir))
        elif scenario == "B":
            all_captures.extend(capture_scenario_b(output_dir))
        elif scenario == "C":
            all_captures.extend(capture_scenario_c(output_dir))
        elif scenario == "D":
            all_captures.extend(capture_scenario_d(output_dir))
        elif scenario == "E":
            all_captures.extend(capture_scenario_e(output_dir))

    # Summary
    print()
    print(f"✅ Captured {len(all_captures)} screenshots")
    print(f"📊 Success rate: {sum(1 for c in all_captures if c['success'])}/{len(all_captures)}")
    print()
    print("💡 Next steps:")
    print("  - Review text outputs in media/screenshots/v2025/")
    print("  - For rendered screenshots, use Playwright in browser mode (future enhancement)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
