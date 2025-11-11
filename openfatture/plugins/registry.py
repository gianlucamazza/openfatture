"""Plugin registry for managing OpenFatture plugins."""

import logging

from .base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for managing OpenFatture plugins."""

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._enabled_plugins: set[str] = set()
        self._initialized_plugins: set[str] = set()

    def register_plugin(self, plugin: BasePlugin) -> None:
        """Register a plugin in the registry.

        Args:
            plugin: Plugin instance to register
        """
        name = plugin.metadata.name
        if name in self._plugins:
            logger.warning(f"Plugin '{name}' already registered, overwriting")
        self._plugins[name] = plugin
        logger.info(f"Registered plugin: {name} v{plugin.metadata.version}")

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin from the registry.

        Args:
            name: Plugin name to unregister

        Returns:
            True if plugin was unregistered, False if not found
        """
        if name in self._plugins:
            del self._plugins[name]
            self._enabled_plugins.discard(name)
            self._initialized_plugins.discard(name)
            logger.info(f"Unregistered plugin: {name}")
            return True
        return False

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin.

        Args:
            name: Plugin name to enable

        Returns:
            True if plugin was enabled, False if not found
        """
        if name in self._plugins:
            self._enabled_plugins.add(name)
            logger.info(f"Enabled plugin: {name}")
            return True
        logger.warning(f"Cannot enable plugin '{name}': not registered")
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin.

        Args:
            name: Plugin name to disable

        Returns:
            True if plugin was disabled, False if not found
        """
        if name in self._enabled_plugins:
            self._enabled_plugins.discard(name)
            # Shutdown if initialized
            if name in self._initialized_plugins:
                try:
                    self._plugins[name].shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down plugin '{name}': {e}")
                self._initialized_plugins.discard(name)
            logger.info(f"Disabled plugin: {name}")
            return True
        return False

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a registered plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[BasePlugin]:
        """List all registered plugins.

        Returns:
            List of all registered plugin instances
        """
        return list(self._plugins.values())

    def list_enabled_plugins(self) -> list[BasePlugin]:
        """List all enabled plugins.

        Returns:
            List of enabled plugin instances
        """
        return [self._plugins[name] for name in self._enabled_plugins if name in self._plugins]

    def is_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled.

        Args:
            name: Plugin name

        Returns:
            True if plugin is enabled, False otherwise
        """
        return name in self._enabled_plugins

    def initialize_enabled_plugins(self, config: dict[str, dict]) -> None:
        """Initialize all enabled plugins with their configuration.

        Args:
            config: Dictionary mapping plugin names to their config
        """
        for name in self._enabled_plugins:
            if name in self._plugins:
                plugin = self._plugins[name]
                plugin_config = config.get(name, {})
                try:
                    plugin.initialize(plugin_config)
                    self._initialized_plugins.add(name)
                    logger.info(f"Initialized plugin: {name}")
                except Exception as e:
                    logger.error(f"Failed to initialize plugin '{name}': {e}")
                    # Disable plugin on initialization failure
                    self._enabled_plugins.discard(name)

    def shutdown_all_plugins(self) -> None:
        """Shutdown all initialized plugins."""
        for name in list(self._initialized_plugins):
            if name in self._plugins:
                try:
                    self._plugins[name].shutdown()
                    logger.info(f"Shutdown plugin: {name}")
                except Exception as e:
                    logger.error(f"Error shutting down plugin '{name}': {e}")
        self._initialized_plugins.clear()

    def get_enabled_plugin_names(self) -> list[str]:
        """Get list of enabled plugin names.

        Returns:
            List of enabled plugin names
        """
        return list(self._enabled_plugins)

    def get_registered_plugin_names(self) -> list[str]:
        """Get list of registered plugin names.

        Returns:
            List of registered plugin names
        """
        return list(self._plugins.keys())


# Global registry instance
_global_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry
