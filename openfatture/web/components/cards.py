"""Reusable Card Components - Best Practices 2025.

React-style components for consistent card displays.
All components support theming and responsive layout.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import streamlit as st


def metric_card(
    title: str,
    value: str | int | float,
    delta: str | int | float | None = None,
    delta_color: str = "normal",
    icon: str | None = None,
    help_text: str | None = None,
) -> None:
    """
    Display a metric card with optional delta and icon.

    Args:
        title: Card title/label
        value: Main metric value
        delta: Change indicator (optional)
        delta_color: Color for delta ("normal", "inverse", "off")
        icon: Emoji/icon to display before title
        help_text: Tooltip help text

    Example:
        >>> metric_card("Revenue", "€10,500", delta="+15%", icon="💰")
    """
    display_title = f"{icon} {title}" if icon else title
    st.metric(
        label=display_title,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )


def status_card(
    status: str,
    color: str = "blue",
    icon: str | None = None,
    description: str | None = None,
) -> None:
    """
    Display a status card with colored background.

    Args:
        status: Status text
        color: Background color ("blue", "green", "red", "yellow", "gray")
        icon: Optional icon/emoji
        description: Optional description text

    Example:
        >>> status_card("Active", color="green", icon="✅")
        >>> status_card("Pending", color="yellow", icon="⏳", description="Awaiting approval")
    """
    # Color mapping
    color_map = {
        "blue": "#E3F2FD",
        "green": "#E8F5E9",
        "red": "#FFEBEE",
        "yellow": "#FFF9C4",
        "gray": "#F5F5F5",
    }

    bg_color = color_map.get(color, color_map["blue"])
    display_status = f"{icon} {status}" if icon else status

    html = f"""
    <div style="
        background-color: {bg_color};
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid {color};
        margin: 0.5rem 0;
    ">
        <strong>{display_status}</strong>
        {f"<br><small>{description}</small>" if description else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def invoice_card(
    numero: str,
    data: date | datetime,
    cliente: str,
    totale: Decimal | float,
    stato: str,
    on_click: Any = None,
) -> None:
    """
    Display an invoice summary card.

    Args:
        numero: Invoice number
        data: Invoice date
        cliente: Client name
        totale: Total amount
        stato: Invoice status
        on_click: Optional callback for click action

    Example:
        >>> invoice_card(
        ...     numero="INV-001/2024",
        ...     data=date(2024, 1, 15),
        ...     cliente="Acme Corp",
        ...     totale=Decimal("1220.00"),
        ...     stato="INVIATA"
        ... )
    """
    # Format values
    data_str = data.strftime("%d/%m/%Y") if isinstance(data, (date, datetime)) else str(data)
    totale_str = f"€{float(totale):,.2f}"

    # Status color mapping
    status_colors = {
        "BOZZA": "gray",
        "DA_INVIARE": "yellow",
        "INVIATA": "blue",
        "CONSEGNATA": "green",
        "RIFIUTATA": "red",
    }
    status_color = status_colors.get(stato, "gray")

    with st.container():
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"**📄 {numero}**")
            st.caption(f"Cliente: {cliente}")

        with col2:
            st.markdown(f"**{totale_str}**")
            st.caption(data_str)

        with col3:
            status_badge(stato, color=status_color)

        if on_click:
            if st.button("Dettagli →", key=f"invoice_{numero}", use_container_width=True):
                on_click()

        st.markdown("---")


def client_card(
    denominazione: str,
    partita_iva: str | None = None,
    email: str | None = None,
    total_invoices: int | None = None,
    total_revenue: Decimal | float | None = None,
    on_click: Any = None,
) -> None:
    """
    Display a client summary card.

    Args:
        denominazione: Client name
        partita_iva: VAT number
        email: Email address
        total_invoices: Number of invoices
        total_revenue: Total revenue from client
        on_click: Optional callback

    Example:
        >>> client_card(
        ...     denominazione="Acme Corp SRL",
        ...     partita_iva="IT12345678901",
        ...     total_invoices=15,
        ...     total_revenue=Decimal("25000.00")
        ... )
    """
    with st.container():
        st.markdown(f"### 👤 {denominazione}")

        col1, col2 = st.columns(2)

        with col1:
            if partita_iva:
                st.caption(f"P.IVA: {partita_iva}")
            if email:
                st.caption(f"📧 {email}")

        with col2:
            if total_invoices is not None:
                st.caption(f"Fatture: {total_invoices}")
            if total_revenue is not None:
                revenue_str = f"€{float(total_revenue):,.2f}"
                st.caption(f"Fatturato: {revenue_str}")

        if on_click:
            if st.button("Vedi Dettagli", key=f"client_{denominazione}", use_container_width=True):
                on_click()

        st.markdown("---")


def status_badge(
    status: str,
    color: str = "blue",
    size: str = "medium",
) -> None:
    """
    Display an inline status badge.

    Args:
        status: Status text
        color: Badge color
        size: Badge size ("small", "medium", "large")

    Example:
        >>> status_badge("Active", color="green")
    """
    # Size mapping
    size_map = {
        "small": "0.7rem",
        "medium": "0.9rem",
        "large": "1.1rem",
    }
    font_size = size_map.get(size, size_map["medium"])

    # Color mapping (darker for text, lighter for background)
    color_schemes = {
        "green": ("white", "#4CAF50"),
        "blue": ("white", "#2196F3"),
        "red": ("white", "#f44336"),
        "yellow": ("#333", "#FFC107"),
        "gray": ("white", "#9E9E9E"),
    }

    text_color, bg_color = color_schemes.get(color, color_schemes["blue"])

    html = f"""
    <span style="
        background-color: {bg_color};
        color: {text_color};
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: {font_size};
        font-weight: 500;
        display: inline-block;
    ">
        {status}
    </span>
    """
    st.markdown(html, unsafe_allow_html=True)


def info_card(
    title: str,
    content: str | list[str],
    icon: str = "ℹ️",
    color: str = "blue",
    expandable: bool = False,
) -> None:
    """
    Display an informational card.

    Args:
        title: Card title
        content: Content (string or list of bullet points)
        icon: Icon/emoji
        color: Card color theme
        expandable: Whether content is in an expander

    Example:
        >>> info_card(
        ...     title="Getting Started",
        ...     content=["Step 1: Configure", "Step 2: Create invoice"],
        ...     icon="🚀"
        ... )
    """
    if expandable:
        with st.expander(f"{icon} {title}"):
            _render_card_content(content)
    else:
        st.markdown(f"### {icon} {title}")
        _render_card_content(content)


def _render_card_content(content: str | list[str]) -> None:
    """Helper to render card content."""
    if isinstance(content, list):
        for item in content:
            st.markdown(f"- {item}")
    else:
        st.markdown(content)


# Composite card for dashboard KPI section
def kpi_dashboard(
    metrics: list[dict[str, Any]],
    columns: int = 4,
) -> None:
    """
    Display a row of KPI metric cards.

    Args:
        metrics: List of metric dicts with keys: title, value, delta, icon
        columns: Number of columns

    Example:
        >>> kpi_dashboard([
        ...     {"title": "Revenue", "value": "€10K", "delta": "+15%", "icon": "💰"},
        ...     {"title": "Invoices", "value": 42, "delta": "+3", "icon": "📄"},
        ... ], columns=2)
    """
    cols = st.columns(columns)

    for idx, metric in enumerate(metrics):
        with cols[idx % columns]:
            metric_card(
                title=metric.get("title", ""),
                value=metric.get("value", 0),
                delta=metric.get("delta"),
                icon=metric.get("icon"),
                help_text=metric.get("help"),
            )
