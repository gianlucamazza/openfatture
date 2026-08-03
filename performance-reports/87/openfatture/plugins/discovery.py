"""Plugin discovery and loading system."""

import importlib.util
import logging
from pathlib import Path

from .base import BasePlugin
from .registry import get_plugin_registry

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Handles discovery and loading of plugins."""

    def __init__(self, plugin_dirs: list[Path] | None = None):
        """Initialize plugin discovery.

        Args:
            plugin_dirs: List of directories to search for plugins.
                        Defaults to standard locations.
        """
        if plugin_dirs is None:
            plugin_dirs = self._get_default_plugin_dirs()
        self.plugin_dirs = plugin_dirs

    def _get_default_plugin_dirs(self) -> list[Path]:
        """Get default plugin directories."""
        dirs = []

        # User plugin directory
        home = Path.home()
        user_plugin_dir = home / ".openfatture" / "plugins"
        dirs.append(user_plugin_dir)

        # System plugin directory (optional)
        system_plugin_dir = Path("/usr/local/share/openfatture/plugins")
        if system_plugin_dir.exists():
            dirs.append(system_plugin_dir)

        return dirs

    def discover_plugins(self) -> list[BasePlugin]:
        """Discover and load all available plugins.

        Returns:
            List of loaded plugin instances
        """
        plugins = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.debug(f"Plugin directory does not exist: {plugin_dir}")
                continue

            logger.info(f"Searching for plugins in: {plugin_dir}")

            # Look for plugin directories (each containing __init__.py or plugin.py)
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    plugin = self._load_plugin_from_directory(item)
                    if plugin:
                        plugins.append(plugin)
                elif item.suffix == ".py" and item.name.startswith("plugin_"):
                    plugin = self._load_plugin_from_file(item)
                    if plugin:
                        plugins.append(plugin)

        return plugins

    def _load_plugin_from_directory(self, plugin_dir: Path) -> BasePlugin | None:
        """Load a plugin from a directory.

        Args:
            plugin_dir: Plugin directory path

        Returns:
            Plugin instance or None if loading failed
        """
        # Try plugin.py first, then __init__.py
        plugin_file = plugin_dir / "plugin.py"
        if not plugin_file.exists():
            plugin_file = plugin_dir / "__init__.py"

        if not plugin_file.exists():
            return None

        return self._load_plugin_from_file(plugin_file)

    def _load_plugin_from_file(self, plugin_file: Path) -> BasePlugin | None:
        """Load a plugin from a Python file.

        Args:
            plugin_file: Plugin file path

        Returns:
            Plugin instance or None if loading failed
        """
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                f"openfatture_plugin_{plugin_file.stem}", plugin_file
            )
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load plugin spec from: {plugin_file}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the plugin class (should inherit from BasePlugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr != BasePlugin:
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.warning(f"No BasePlugin subclass found in: {plugin_file}")
                return None

            # Instantiate the plugin
            plugin_instance = plugin_class()
            logger.info(f"Loaded plugin: {plugin_instance.metadata.name} from {plugin_file}")
            return plugin_instance

        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_file}: {e}")
            return None

    def auto_register_plugins(self) -> None:
        """Discover and register all available plugins."""
        registry = get_plugin_registry()
        plugins = self.discover_plugins()

        for plugin in plugins:
            registry.register_plugin(plugin)

        logger.info(f"Auto-registered {len(plugins)} plugins")
