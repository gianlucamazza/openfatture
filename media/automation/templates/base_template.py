#!/usr/bin/env python3
"""
VHS Template Engine for OpenFatture Media Automation

This module provides a Jinja2-based template engine for generating VHS tape files
with reusable components and dynamic scenario customization.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


@dataclass
class ScenarioConfig:
    """Configuration for a VHS scenario."""

    id: str
    title: str
    duration: str
    description: str
    commands: list
    variables: dict[str, Any]


class VHSTemplateEngine:
    """
    Jinja2-based template engine for VHS tape generation.

    Features:
    - Dynamic scenario generation from templates
    - Reusable component library
    - Variable substitution and customization
    - Template validation and error handling
    """

    def __init__(self, template_dir: str = "media/automation/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Load variables first, then components
        self.variables = self._load_variables()
        self.components = self._load_components()

    def _load_components(self) -> dict[str, str]:
        """Load reusable VHS components from components directory."""
        components = {}
        components_dir = self.template_dir / "components"

        if not components_dir.exists():
            return components

        for component_file in components_dir.glob("*.tapeinc"):
            component_name = component_file.stem
            # Load component as raw text - will be processed by main template
            components[component_name] = component_file.read_text()

        return components

    def _load_variables(self) -> dict[str, Any]:
        """Load default variables from variables.yaml."""
        variables_file = self.template_dir / "variables.yaml"

        if not variables_file.exists():
            return {}

        try:
            with open(variables_file, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load variables file: {e}")
            return {}

    def get_scenario_config(self, scenario_id: str) -> ScenarioConfig | None:
        """Get configuration for a specific scenario."""
        scenario_data = self.variables.get("scenarios", {}).get(scenario_id.lower())
        if not scenario_data:
            return None

        return ScenarioConfig(
            id=scenario_id,
            title=scenario_data.get("title", f"Scenario {scenario_id}"),
            duration=scenario_data.get("duration", "Unknown"),
            description=scenario_data.get("description", ""),
            commands=scenario_data.get("commands", []),
            variables=scenario_data.get("variables", {}),
        )

    def render_scenario(
        self, scenario_id: str, custom_variables: dict[str, Any] | None = None
    ) -> str:
        """
        Render a VHS tape file for the given scenario.

        Args:
            scenario_id: Scenario identifier (A, B, C, D, E)
            custom_variables: Optional custom variables to override defaults

        Returns:
            Rendered VHS tape content as string

        Raises:
            TemplateNotFound: If scenario template doesn't exist
            Exception: For other rendering errors
        """
        # Get scenario configuration
        config = self.get_scenario_config(scenario_id.lower())
        if not config:
            raise ValueError(f"Scenario '{scenario_id}' not found in variables.yaml")

        # Prepare template variables
        template_vars = {
            "scenario": config,
            "components": self.components,
            "global_vars": self.variables.get("global", {}),
            "custom_vars": custom_variables or {},
        }

        # Merge custom variables
        if custom_variables:
            template_vars.update(custom_variables)

        try:
            # Load and render template
            template = self.env.get_template(f"scenarios/{scenario_id.lower()}.tape.j2")
            return template.render(**template_vars)
        except TemplateNotFound:
            raise TemplateNotFound(f"Template for scenario '{scenario_id}' not found")
        except Exception as e:
            raise Exception(f"Error rendering template for scenario '{scenario_id}': {e}")

    def list_scenarios(self) -> dict[str, ScenarioConfig]:
        """List all available scenarios."""
        scenarios = {}
        scenario_configs = self.variables.get("scenarios", {})

        for scenario_id, config_data in scenario_configs.items():
            scenarios[scenario_id.upper()] = ScenarioConfig(
                id=scenario_id.upper(),
                title=config_data.get("title", f"Scenario {scenario_id.upper()}"),
                duration=config_data.get("duration", "Unknown"),
                description=config_data.get("description", ""),
                commands=config_data.get("commands", []),
                variables=config_data.get("variables", {}),
            )

        return scenarios

    def validate_template(self, scenario_id: str) -> bool:
        """
        Validate that a scenario template exists and can be rendered.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to render with minimal variables
            self.render_scenario(scenario_id)
            return True
        except Exception:
            return False

    def generate_tape_file(
        self,
        scenario_id: str,
        output_path: str | None = None,
        custom_variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate and optionally save a VHS tape file.

        Args:
            scenario_id: Scenario identifier
            output_path: Optional path to save the file
            custom_variables: Optional custom variables

        Returns:
            Path to the generated file
        """
        content = self.render_scenario(scenario_id, custom_variables)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(content, encoding="utf-8")
            return str(output_file)

        # Default output path
        default_path = f"media/automation/scenario_{scenario_id.lower()}.tape"
        Path(default_path).write_text(content, encoding="utf-8")
        return default_path


def main():
    """CLI interface for the template engine."""
    import argparse

    parser = argparse.ArgumentParser(description="VHS Template Engine for OpenFatture")
    parser.add_argument(
        "action", choices=["generate", "list", "validate"], help="Action to perform"
    )
    parser.add_argument("--scenario", "-s", help="Scenario ID (A, B, C, D, E)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--variables", "-v", help="Custom variables as JSON string")

    args = parser.parse_args()

    engine = VHSTemplateEngine()

    if args.action == "list":
        scenarios = engine.list_scenarios()
        print("Available scenarios:")
        for sid, config in scenarios.items():
            print(f"  {sid}: {config.title} ({config.duration})")

    elif args.action == "validate":
        if not args.scenario:
            print("Error: --scenario required for validate action")
            return 1

        if engine.validate_template(args.scenario):
            print(f"✓ Scenario {args.scenario} template is valid")
            return 0
        else:
            print(f"✗ Scenario {args.scenario} template is invalid")
            return 1

    elif args.action == "generate":
        if not args.scenario:
            print("Error: --scenario required for generate action")
            return 1

        custom_vars = None
        if args.variables:
            import json

            custom_vars = json.loads(args.variables)

        try:
            output_path = engine.generate_tape_file(args.scenario, args.output, custom_vars)
            print(f"✓ Generated VHS tape: {output_path}")
            return 0
        except Exception as e:
            print(f"Error generating tape: {e}")
            return 1


if __name__ == "__main__":
    exit(main())
