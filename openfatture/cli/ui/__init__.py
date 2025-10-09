"""Interactive UI module for OpenFatture CLI."""

from .autocomplete import (
    autocomplete_cap,
    autocomplete_descrizione_servizio,
    autocomplete_modalita_pagamento,
    autocomplete_natura_iva,
    autocomplete_provincia,
    autocomplete_regime_fiscale,
    autocomplete_unita_misura,
)
from .dashboard import show_dashboard
from .helpers import (
    confirm_action,
    press_any_key,
    select_cliente,
    select_fattura,
    select_multiple,
    select_multiple_clienti,
    select_multiple_fatture,
    text_input,
)
from .menus import handle_main_menu, show_main_menu
from .progress import create_progress, process_with_progress, with_spinner
from .styles import minimal_style, openfatture_style

__all__ = [
    # Helpers
    "confirm_action",
    "press_any_key",
    "select_cliente",
    "select_fattura",
    "select_multiple",
    "select_multiple_clienti",
    "select_multiple_fatture",
    "text_input",
    # Menus
    "show_main_menu",
    "handle_main_menu",
    # Styles
    "openfatture_style",
    "minimal_style",
    # Progress
    "create_progress",
    "process_with_progress",
    "with_spinner",
    # Dashboard
    "show_dashboard",
    # Autocomplete
    "autocomplete_provincia",
    "autocomplete_cap",
    "autocomplete_regime_fiscale",
    "autocomplete_natura_iva",
    "autocomplete_descrizione_servizio",
    "autocomplete_unita_misura",
    "autocomplete_modalita_pagamento",
]
