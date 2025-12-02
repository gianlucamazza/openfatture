"""Fluent translation loader and bundle manager.

This module handles loading Fluent Translation List (.ftl) files and manages
the FluentBundle instances for each supported locale with intelligent caching.
"""

import os
import threading
from pathlib import Path
from typing import Any

import structlog
from fluent.runtime import FluentBundle, FluentLocalization, FluentResource, FluentResourceLoader

from openfatture.utils.config import get_settings

logger = structlog.get_logger(__name__)

# Supported locales
SUPPORTED_LOCALES = ["it", "en", "es", "fr", "de"]
DEFAULT_LOCALE = "it"
FALLBACK_LOCALE = "it"

# Thread-local storage for per-request/session locale
_thread_local = threading.local()

# Global bundle cache {locale: FluentBundle}
_bundle_cache: dict[str, FluentBundle] = {}
_localization_cache: dict[str, FluentLocalization] = {}


def get_locales_dir() -> Path:
    """Get the locales directory path."""
    return Path(__file__).parent / "locales"


def _load_bundle(locale: str) -> FluentBundle:
    """Load Fluent bundle for a specific locale.

    Args:
        locale: Language code (it, en, es, fr, de)

    Returns:
        FluentBundle instance with all .ftl files loaded

    Raises:
        FileNotFoundError: If locale directory doesn't exist
    """
    if locale not in SUPPORTED_LOCALES:
        logger.warning(f"Unsupported locale {locale}, falling back to {FALLBACK_LOCALE}")
        locale = FALLBACK_LOCALE

    locale_dir = get_locales_dir() / locale
    if not locale_dir.exists():
        raise FileNotFoundError(f"Locale directory not found: {locale_dir}")

    # Create FluentBundle
    bundle = FluentBundle([locale])

    # Load all .ftl files in the locale directory
    ftl_files = sorted(locale_dir.glob("*.ftl"))
    if not ftl_files:
        logger.warning(f"No .ftl files found in {locale_dir}")
        return bundle

    for ftl_file in ftl_files:
        try:
            with open(ftl_file, encoding="utf-8") as f:
                content = f.read()
                # FluentResource() parses the content automatically
                resource = FluentResource(content)
                bundle.add_resource(resource)
            logger.debug(f"Loaded {ftl_file.name} for locale {locale}")
        except Exception as e:
            logger.error(f"Failed to load {ftl_file}: {e}")

    logger.info(f"Loaded Fluent bundle for locale: {locale} ({len(ftl_files)} files)")
    return bundle


def _load_localization(locales: list[str]) -> FluentLocalization:
    """Load FluentLocalization with fallback chain.

    Args:
        locales: List of locale codes in priority order (first = preferred)

    Returns:
        FluentLocalization instance with resource loader
    """
    locales_dir = get_locales_dir()

    # Create resource loader with correct path template
    # FluentResourceLoader expects: /path/to/locales/{locale}/{resource_id}.ftl
    loader = FluentResourceLoader(str(locales_dir / "{locale}"))

    # Get all .ftl file names from the first locale
    first_locale_dir = locales_dir / locales[0]
    if not first_locale_dir.exists():
        logger.warning(f"Locale directory not found: {first_locale_dir}, using fallback")
        first_locale_dir = locales_dir / FALLBACK_LOCALE

    # resource_ids should be the file names without .ftl extension
    resource_ids = [f.stem for f in sorted(first_locale_dir.glob("*.ftl"))]

    # Create FluentLocalization with fallback chain
    l10n = FluentLocalization(locales, resource_ids, loader)

    logger.info(f"Loaded FluentLocalization for locales: {locales} ({len(resource_ids)} resources)")
    return l10n


def get_bundle(locale: str) -> FluentBundle:
    """Get cached Fluent bundle for a locale.

    Args:
        locale: Language code

    Returns:
        Cached FluentBundle instance
    """
    if locale not in _bundle_cache:
        _bundle_cache[locale] = _load_bundle(locale)
    return _bundle_cache[locale]


def get_localization(locale: str) -> FluentLocalization:
    """Get cached FluentLocalization with fallback chain.

    Args:
        locale: Preferred language code

    Returns:
        FluentLocalization with locale → en → it fallback
    """
    cache_key = locale

    if cache_key not in _localization_cache:
        # Build fallback chain: requested → en (if not requested) → it
        locales = [locale]
        if locale != "en" and locale != FALLBACK_LOCALE:
            locales.append("en")
        if locale != FALLBACK_LOCALE:
            locales.append(FALLBACK_LOCALE)

        _localization_cache[cache_key] = _load_localization(locales)

    return _localization_cache[cache_key]


def get_locale() -> str:
    """Get current locale from thread-local storage or config.

    Priority:
    1. Thread-local storage (for per-session/request locale)
    2. OPENFATTURE_LOCALE environment variable
    3. Settings.locale
    4. Default locale (it)

    Returns:
        Current locale code
    """
    # Check thread-local storage first
    if hasattr(_thread_local, "locale") and _thread_local.locale:
        return _thread_local.locale

    # Check environment variable
    env_locale = os.getenv("OPENFATTURE_LOCALE")
    if env_locale and env_locale in SUPPORTED_LOCALES:
        return env_locale

    # Check settings
    try:
        settings = get_settings()
        if settings.locale in SUPPORTED_LOCALES:
            return settings.locale
    except Exception:
        pass

    return DEFAULT_LOCALE


def set_locale(locale: str) -> None:
    """Set locale for current thread/session.

    Args:
        locale: Language code (it, en, es, fr, de)

    Raises:
        ValueError: If locale is not supported
    """
    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale: {locale}. Supported: {', '.join(SUPPORTED_LOCALES)}")

    _thread_local.locale = locale
    logger.debug(f"Locale set to: {locale}")


def reload_translations() -> None:
    """Reload all translation bundles from disk.

    Useful for development or when .ftl files are updated without restarting the app.
    """
    global _bundle_cache, _localization_cache

    _bundle_cache.clear()
    _localization_cache.clear()

    logger.info("Translation bundles reloaded")


def format_value(
    locale: str, message_id: str, variables: dict[str, Any] | None = None
) -> str | None:
    """Format a message using FluentBundle.

    Args:
        locale: Language code
        message_id: Fluent message ID
        variables: Optional variables for interpolation

    Returns:
        Formatted message or None if not found
    """
    bundle = get_bundle(locale)
    variables = variables or {}

    try:
        # Get message from bundle
        message = bundle.get_message(message_id)
        if message is None:
            return None

        # Format the message pattern
        # format_pattern() returns tuple (formatted_string, errors)
        if message.value:
            formatted, errors = bundle.format_pattern(message.value, variables)
            if errors:
                logger.warning(f"Formatting errors for {message_id}: {errors}")
            return formatted
        return None
    except Exception as e:
        logger.warning(f"Failed to format message {message_id}: {e}")
        return None
