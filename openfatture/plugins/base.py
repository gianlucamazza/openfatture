"""Base plugin interfaces and classes for OpenFatture plugin system."""

from abc import ABC, abstractmethod
from typing import Any

import typer
from pydantic import BaseModel, Field


class PluginMetadata(BaseModel):
    """Metadata for a plugin."""

    name: str = Field(..., description="Unique plugin name")
    version: str = Field(..., description="Plugin version (semantic versioning)")
    description: str = Field(..., description="Human-readable description")
    author: str = Field(..., description="Plugin author")
    requires: list[str] = Field(default_factory=list, description="Required dependencies")
    compatible_versions: str = Field(
        default=">=1.1.0", description="Compatible OpenFatture versions (PEP 440)"
    )
    homepage: str | None = Field(None, description="Plugin homepage URL")
    license: str | None = Field(None, description="Plugin license")


class BasePlugin(ABC):
    """Base class for all OpenFatture plugins.

    Plugins should inherit from this class and implement all abstract methods.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the plugin with configuration.

        Args:
            config: Plugin-specific configuration dictionary
        """
        pass

    @abstractmethod
    def get_cli_app(self) -> typer.Typer | None:
        """Return the plugin's CLI app if it provides commands.

        Returns:
            Typer app instance or None if no CLI commands
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin and cleanup resources."""
        pass

    def is_compatible(self, openfatture_version: str) -> bool:
        """Check if plugin is compatible with current OpenFatture version.

        Args:
            openfatture_version: Current OpenFatture version

        Returns:
            True if compatible, False otherwise
        """
        # Simple version check - could be enhanced with proper PEP 440 parsing
        return True  # For now, assume compatibility

    def get_dependencies(self) -> list[str]:
        """Return list of required dependencies."""
        return self.metadata.requires
