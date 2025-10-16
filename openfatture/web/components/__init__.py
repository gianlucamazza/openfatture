"""Reusable UI Components for OpenFatture Web Interface - Best Practices 2025.

This module provides React-style reusable components for consistent UI/UX.

Component Categories:
- Cards: metric_card, invoice_card, client_card, status_card
- Tables: data_table, invoice_table
- Alerts: success_alert, error_alert, warning_alert, info_alert
- Legacy helpers: format_currency, format_date

Usage:
    >>> from openfatture.web.components import metric_card, success_alert
    >>> metric_card("Revenue", "€10,000", delta="+15%", icon="💰")
    >>> success_alert("Invoice created successfully!")
"""

from typing import Any

import streamlit as st

# Import all components from submodules
from openfatture.web.components.alerts import (
    confirmation_dialog,
    error_alert,
    info_alert,
    progress_indicator,
    success_alert,
    toast_notification,
    warning_alert,
)
from openfatture.web.components.cards import (
    client_card,
    info_card,
    invoice_card,
    kpi_dashboard,
    metric_card,
    status_badge,
    status_card,
)
from openfatture.web.components.tables import data_table, invoice_table

# Re-export all components
__all__ = [
    # Cards
    "metric_card",
    "status_card",
    "invoice_card",
    "client_card",
    "status_badge",
    "info_card",
    "kpi_dashboard",
    # Tables
    "data_table",
    "invoice_table",
    # Alerts
    "success_alert",
    "error_alert",
    "warning_alert",
    "info_alert",
    "confirmation_dialog",
    "toast_notification",
    "progress_indicator",
    # Legacy helpers (backwards compatibility)
    "format_currency",
    "format_date",
    "create_metric_card",
    "create_action_button",
    "create_status_badge",
    "create_expander_with_actions",
    "display_data_table",
]


# ============================================================================
# LEGACY HELPERS (Backwards Compatibility)
# ============================================================================
# These are kept for backwards compatibility with existing pages.
# New code should use the modern components above.


def format_currency(amount: float, currency: str = "€") -> str:
    """Format amount as currency string (legacy helper)."""
    return f"{currency}{amount:,.2f}"


def format_date(date_obj: Any, format_str: str = "%d/%m/%Y") -> str:
    """Format date object to string (legacy helper)."""
    if hasattr(date_obj, "strftime"):
        return date_obj.strftime(format_str)
    return str(date_obj)


def create_metric_card(
    title: str, value: str, delta: str | None = None, help_text: str | None = None
) -> None:
    """Create a consistent metric card (legacy - use metric_card instead)."""
    metric_card(title, value, delta, help_text=help_text)


def create_action_button(label: str, key: str, help_text: str | None = None, **kwargs) -> bool:
    """Create a consistent action button (legacy helper)."""
    return st.button(label, key=key, help=help_text, **kwargs)


def create_status_badge(status: str, status_map: dict[str, str] | None = None) -> str:
    """Create a colored status badge (legacy - use status_badge instead)."""
    if status_map is None:
        status_map = {
            "success": "green",
            "error": "red",
            "warning": "orange",
            "info": "blue",
            "default": "gray",
        }

    color = status_map.get(status.lower(), status_map["default"])
    return f'<span style="color: {color}">●</span> {status}'


def create_expander_with_actions(
    title: str, actions: list[dict[str, Any]] | None = None, **kwargs
) -> Any:
    """Create an expander with optional action buttons (legacy helper)."""
    expander = st.expander(title, **kwargs)

    if actions:
        with expander:
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(action["label"], key=action["key"], help=action.get("help")):
                        return action.get("callback", lambda: None)()

    return expander


def display_data_table(
    data: list[dict[str, Any]],
    columns: list[str],
    actions: list[dict[str, Any]] | None = None,
    key_prefix: str = "table",
) -> None:
    """Display data in a consistent table format (legacy - use data_table instead)."""
    if not data:
        st.info("Nessun dato da visualizzare")
        return

    for i, row in enumerate(data):
        cols = st.columns(len(columns) + (1 if actions else 0))

        # Display data columns
        for j, col in enumerate(columns):
            with cols[j]:
                value = row.get(col, "")
                if isinstance(value, float) and col.lower() in ["amount", "importo", "totale"]:
                    st.write(format_currency(value))
                elif col.lower() in ["date", "data"]:
                    st.write(format_date(value))
                else:
                    st.write(str(value) if value else "-")

        # Display action buttons
        if actions:
            with cols[-1]:
                for action in actions:
                    if st.button(
                        action["icon"],
                        key=f"{key_prefix}_{i}_{action['key']}",
                        help=action.get("help", ""),
                    ):
                        action.get("callback", lambda: None)(row)

        st.markdown("---")
