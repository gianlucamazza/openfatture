"""Prompt template management."""

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, ConfigDict, Field

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class PromptTemplate(BaseModel):
    """
    Structured prompt template.

    Loaded from YAML files and rendered with Jinja2.
    """

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template purpose")
    version: str = Field(default="1.0.0", description="Template version")

    # Prompts
    system_prompt: str = Field(..., description="System prompt template")
    user_template: str = Field(..., description="User message template")

    # Examples for few-shot learning
    few_shot_examples: list[dict[str, str]] = Field(
        default_factory=list,
        description="Few-shot examples (input/output pairs)",
    )

    # Required variables
    required_variables: list[str] = Field(
        default_factory=list,
        description="Required template variables",
    )

    # Optional settings
    temperature: float | None = Field(default=None, description="Recommended temperature")
    max_tokens: int | None = Field(default=None, description="Recommended max tokens")

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Template tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PromptManager:
    """
    Manages prompt templates with Jinja2 rendering.

    Loads prompts from YAML files and renders them with
    context variables. Supports caching and validation.

    Example YAML format:
    ```yaml
    name: invoice_assistant
    description: Generate invoice descriptions
    version: 1.0.0

    system_prompt: |
      You are an expert invoice assistant for Italian freelancers.
      Your job is to expand brief service descriptions into detailed,
      professional invoice descriptions.

    user_template: |
      Service: {{ servizio_base }}
      Hours: {{ ore_lavorate }}
      {% if tecnologie %}
      Technologies: {{ tecnologie|join(', ') }}
      {% endif %}

      Generate a detailed invoice description.

    few_shot_examples:
      - input: "3 ore consulenza web"
        output: "Consulenza professionale..."

    required_variables:
      - servizio_base
      - ore_lavorate

    temperature: 0.7
    max_tokens: 500
    tags:
      - invoice
      - description
    ```
    """

    def __init__(self, templates_dir: Path) -> None:
        """
        Initialize prompt manager.

        Args:
            templates_dir: Directory containing YAML template files
        """
        self.templates_dir = templates_dir

        # Create directory if it doesn't exist
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            logger.info("created_prompts_directory", path=str(self.templates_dir))

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Cache for loaded templates
        self._cache: dict[str, PromptTemplate] = {}

        logger.info("prompt_manager_initialized", templates_dir=str(templates_dir))

    def load_template(self, name: str) -> PromptTemplate:
        """
        Load prompt template from YAML file.

        Args:
            name: Template name (without .yaml extension)

        Returns:
            PromptTemplate instance

        Raises:
            FileNotFoundError: If template file not found
            ValueError: If template format is invalid
        """
        # Check cache first
        if name in self._cache:
            logger.debug("prompt_template_cache_hit", name=name)
            return self._cache[name]

        # Load from file
        yaml_path = self.templates_dir / f"{name}.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(
                f"Prompt template '{name}' not found at {yaml_path}. "
                f"Available templates: {self.list_templates()}"
            )

        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)

            # Validate required fields
            if "system_prompt" not in data:
                raise ValueError(f"Template '{name}' missing required field: system_prompt")

            if "user_template" not in data:
                raise ValueError(f"Template '{name}' missing required field: user_template")

            # Create template
            template = PromptTemplate(
                name=data.get("name", name),
                description=data.get("description", ""),
                version=data.get("version", "1.0.0"),
                system_prompt=data["system_prompt"],
                user_template=data["user_template"],
                few_shot_examples=data.get("few_shot_examples", []),
                required_variables=data.get("required_variables", []),
                temperature=data.get("temperature"),
                max_tokens=data.get("max_tokens"),
                tags=data.get("tags", []),
                metadata=data.get("metadata", {}),
            )

            # Cache it
            self._cache[name] = template

            logger.info("prompt_template_loaded", name=name, version=template.version)

            return template

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in template '{name}': {e}")

        except Exception as e:
            raise ValueError(f"Error loading template '{name}': {e}")

    def render(
        self,
        template_name: str,
        variables: dict[str, Any],
        validate: bool = True,
    ) -> tuple[str, str]:
        """
        Render prompt template with variables.

        Args:
            template_name: Name of template to render
            variables: Variables to render with
            validate: Whether to validate required variables

        Returns:
            Tuple of (system_prompt, user_prompt)

        Raises:
            FileNotFoundError: If template not found
            ValueError: If required variables missing
        """
        # Load template
        template = self.load_template(template_name)

        # Validate required variables
        if validate and template.required_variables:
            missing = set(template.required_variables) - set(variables.keys())
            if missing:
                raise ValueError(
                    f"Template '{template_name}' requires variables: {missing}. "
                    f"Provided: {list(variables.keys())}"
                )

        # Render system prompt
        system_tmpl = Template(template.system_prompt)
        system_prompt = system_tmpl.render(**variables)

        # Render user prompt
        user_tmpl = Template(template.user_template)
        user_prompt = user_tmpl.render(**variables)

        logger.debug(
            "prompt_rendered",
            template=template_name,
            system_length=len(system_prompt),
            user_length=len(user_prompt),
        )

        return system_prompt, user_prompt

    def render_with_examples(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Render template including few-shot examples.

        Args:
            template_name: Template name
            variables: Template variables

        Returns:
            Tuple of (system_prompt, user_prompt_with_examples)
        """
        template = self.load_template(template_name)

        # Render base prompts
        system_prompt, user_prompt = self.render(template_name, variables)

        # Add examples if available
        if template.few_shot_examples:
            examples_text = "\n\nExamples:\n\n"

            for i, example in enumerate(template.few_shot_examples, 1):
                examples_text += f"Example {i}:\n"
                examples_text += f"Input: {example.get('input', '')}\n"
                examples_text += f"Output: {example.get('output', '')}\n\n"

            # Prepend examples to user prompt
            user_prompt = examples_text + user_prompt

        return system_prompt, user_prompt

    def list_templates(self) -> list[str]:
        """
        List available template names.

        Returns:
            List of template names (without .yaml extension)
        """
        templates = []

        for yaml_file in self.templates_dir.glob("*.yaml"):
            templates.append(yaml_file.stem)

        return sorted(templates)

    def get_template_info(self, name: str) -> dict[str, Any]:
        """
        Get template metadata without loading full template.

        Args:
            name: Template name

        Returns:
            Dictionary with template info
        """
        template = self.load_template(name)

        return {
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "required_variables": template.required_variables,
            "temperature": template.temperature,
            "max_tokens": template.max_tokens,
            "tags": template.tags,
            "has_examples": len(template.few_shot_examples) > 0,
        }

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()
        logger.info("prompt_template_cache_cleared")

    def reload_template(self, name: str) -> PromptTemplate:
        """
        Reload a template from disk, bypassing cache.

        Args:
            name: Template name

        Returns:
            Reloaded PromptTemplate
        """
        # Remove from cache if present
        if name in self._cache:
            del self._cache[name]

        # Load fresh
        return self.load_template(name)


def create_prompt_manager(templates_dir: Path | None = None) -> PromptManager:
    """
    Create a prompt manager instance.

    Args:
        templates_dir: Templates directory (uses default if None)

    Returns:
        PromptManager instance
    """
    if templates_dir is None:
        # Use default from project
        templates_dir = Path("openfatture/ai/prompts")

    return PromptManager(templates_dir=templates_dir)
