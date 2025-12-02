"""Internationalization (i18n) module for OpenFatture.

This module provides a modern i18n infrastructure using Mozilla Fluent for
multi-language support across CLI, Web UI, AI prompts, and error messages.

Supported languages: IT (Italian - default), EN (English), ES (Spanish), FR (French), DE (German)

Usage:
    from openfatture.i18n import _, get_locale, set_locale

    # Basic translation
    message = _("cli-fattura-create-title")

    # With variables
    message = _("cli-fattura-created", numero="001")

    # Check/change locale
    current = get_locale()  # Returns "it", "en", etc.
    set_locale("en")        # Switch to English
"""

from openfatture.i18n.loader import get_locale, reload_translations, set_locale
from openfatture.i18n.translator import _

__all__ = [
    "_",
    "get_locale",
    "set_locale",
    "reload_translations",
]
