"""Plugin system for OpenFatture.

This module provides a modular architecture for extending OpenFatture
with optional features and third-party integrations.
"""

from .base import BasePlugin, PluginMetadata
from .discovery import PluginDiscovery
from .registry import PluginRegistry, get_plugin_registry

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginRegistry",
    "PluginDiscovery",
    "get_plugin_registry",
]
