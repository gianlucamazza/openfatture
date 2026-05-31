"""Internationalization utilities for Streamlit web UI.

This module provides i18n integration between the existing openfatture.i18n
module and Streamlit's session state for language selection.
"""

from pathlib import Path
from typing import Any

import streamlit as st
from fluent.runtime import FluentLocalization, FluentResourceLoader

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)

# Available languages
AVAILABLE_LANGUAGES = {
    "it": "Italiano",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
}

DEFAULT_LANGUAGE = "it"


def get_locales_dir() -> Path:
    """Get the locales directory path."""
    return Path(__file__).parent.parent.parent / "i18n" / "locales"


def get_current_language() -> str:
    """Get the current language from Streamlit session state.

    Returns:
        Language code (it, en, es, fr, de). Defaults to 'it' if not set.
    """
    if "language" not in st.session_state:
        st.session_state.language = DEFAULT_LANGUAGE
    return st.session_state.language


def set_language(language: str) -> None:
    """Set the current language in Streamlit session state.

    Args:
        language: Language code (it, en, es, fr, de)
    """
    if language in AVAILABLE_LANGUAGES:
        st.session_state.language = language
        logger.info(f"Language changed to: {language}")
    else:
        logger.warning(f"Invalid language code: {language}. Using default: {DEFAULT_LANGUAGE}")
        st.session_state.language = DEFAULT_LANGUAGE


def get_translator() -> "WebTranslator":
    """Get a translator instance for the current language.

    Returns:
        WebTranslator instance configured for current language
    """
    language = get_current_language()
    return WebTranslator(language)


class WebTranslator:
    """Translator for Streamlit web UI.

    This class provides translation functionality using Fluent (.ftl files)
    and integrates with Streamlit's session state for language management.
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        """Initialize translator for a specific language.

        Args:
            language: Language code (it, en, es, fr, de)
        """
        self.language = language
        self._localization = self._load_localization()

    def _load_localization(self) -> FluentLocalization:
        """Load Fluent localization for the current language."""
        locales_dir = get_locales_dir()
        loader = FluentResourceLoader(str(locales_dir / "{locale}"))

        # Load web UI resources (web.ftl, web_pages.ftl, cli.ftl for shared strings)
        resources = ["web.ftl", "web_pages.ftl", "cli.ftl"]

        try:
            localization = FluentLocalization([self.language], resources, loader)
            logger.debug(f"Loaded localization for language: {self.language}")
            return localization
        except Exception as e:
            logger.error(f"Failed to load localization for {self.language}: {e}")
            # Fallback to Italian
            return FluentLocalization([DEFAULT_LANGUAGE], resources, loader)

    def t(self, key: str, **variables: Any) -> str:
        """Translate a key with optional variables.

        Args:
            key: Translation key (e.g., "web-app-title")
            **variables: Variables to substitute in the translation

        Returns:
            Translated string or the key itself if translation not found
        """
        try:
            result = self._localization.format_value(key, variables)
            return result if result else key
        except Exception as e:
            logger.warning(f"Translation error for key '{key}': {e}")
            return key

    def __call__(self, key: str, **variables: Any) -> str:
        """Allow translator to be called like a function.

        Args:
            key: Translation key
            **variables: Variables to substitute

        Returns:
            Translated string
        """
        return self.t(key, **variables)


def init_i18n() -> None:
    """Initialize i18n for the web UI.

    This should be called once at app startup to set up the language
    in session state if not already present.
    """
    if "language" not in st.session_state:
        st.session_state.language = DEFAULT_LANGUAGE
        logger.info(f"Initialized i18n with default language: {DEFAULT_LANGUAGE}")


def render_language_selector(key: str = "language_selector") -> None:
    """Render a language selector widget in the sidebar.

    Args:
        key: Unique key for the Streamlit widget
    """
    current_lang = get_current_language()
    t = get_translator()

    # Language selector in sidebar
    selected_lang = st.selectbox(
        label=t("web-lang-selector-title"),
        options=list(AVAILABLE_LANGUAGES.keys()),
        format_func=lambda x: AVAILABLE_LANGUAGES[x],
        index=list(AVAILABLE_LANGUAGES.keys()).index(current_lang),
        key=key,
    )

    # Update language if changed
    if selected_lang != current_lang:
        set_language(selected_lang)
        st.success(t("web-lang-selector-changed", language=AVAILABLE_LANGUAGES[selected_lang]))
        st.rerun()


# Convenience function for quick translations
def _(key: str, **variables: Any) -> str:
    """Quick translation function (underscore alias).

    Args:
        key: Translation key
        **variables: Variables to substitute

    Returns:
        Translated string
    """
    return get_translator().t(key, **variables)
