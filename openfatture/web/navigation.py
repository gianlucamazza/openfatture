"""Modern Navigation System - Streamlit Best Practices 2025.

This module demonstrates the st.Page + st.navigation pattern recommended
for production Streamlit apps. It provides:
- Dynamic navigation with st.navigation()
- Grouped pages for better UX
- Shared layout (sidebar, footer) in the frame
- Programmatic page switching

Usage (to migrate from pages/ directory):
    1. Import this module in app.py
    2. Call setup_navigation() instead of render_sidebar()
    3. Navigation is handled automatically

Benefits:
- More flexible than pages/ directory
- Dynamic navigation (show/hide pages based on auth, features, etc.)
- Shared elements across all pages
- Better control over page order and grouping
"""

import streamlit as st


def create_page_registry() -> dict[str, st.Page]:
    """
    Create registry of all application pages using st.Page.

    Best Practice 2025: Define pages as st.Page objects for maximum flexibility.

    Returns:
        Dictionary mapping page IDs to st.Page objects
    """
    # Core pages
    home = st.Page("openfatture/web/pages/home.py", title="Home", icon="🏠", default=True)

    dashboard = st.Page(
        "openfatture/web/pages/1_📊_Dashboard.py",
        title="Dashboard",
        icon="📊",
    )

    # Invoice management
    invoices = st.Page(
        "openfatture/web/pages/2_🧾_Fatture.py",
        title="Fatture",
        icon="🧾",
    )

    clients = st.Page(
        "openfatture/web/pages/3_👥_Clienti.py",
        title="Clienti",
        icon="👥",
    )

    # Payments
    payments = st.Page(
        "openfatture/web/pages/4_💰_Pagamenti.py",
        title="Pagamenti",
        icon="💰",
    )

    # AI features
    ai_assistant = st.Page(
        "openfatture/web/pages/5_🤖_AI_Assistant.py",
        title="AI Assistant",
        icon="🤖",
    )

    # Settings
    settings = st.Page(
        "openfatture/web/pages/6_⚙️_Impostazioni.py",
        title="Impostazioni",
        icon="⚙️",
    )

    # Advanced features
    lightning = st.Page(
        "openfatture/web/pages/7_⚡_Lightning.py",
        title="Lightning",
        icon="⚡",
    )

    batch = st.Page(
        "openfatture/web/pages/8_📦_Batch.py",
        title="Batch Operations",
        icon="📦",
    )

    reports = st.Page(
        "openfatture/web/pages/9_📊_Reports.py",
        title="Reports",
        icon="📊",
    )

    return {
        "home": home,
        "dashboard": dashboard,
        "invoices": invoices,
        "clients": clients,
        "payments": payments,
        "ai_assistant": ai_assistant,
        "settings": settings,
        "lightning": lightning,
        "batch": batch,
        "reports": reports,
    }


def setup_navigation() -> st.Page:
    """
    Setup modern navigation with st.navigation and grouped pages.

    Best Practice 2025: Use st.navigation for dynamic, grouped navigation.
    This is the recommended approach over pages/ directory for production apps.

    Returns:
        Currently selected st.Page

    Example:
        >>> # In app.py
        >>> page = setup_navigation()
        >>> page.run()  # Render selected page
    """
    pages = create_page_registry()

    # Group pages logically for better UX
    navigation = st.navigation(
        {
            "🏠 Home": [pages["home"]],
            "📊 Business": [
                pages["dashboard"],
                pages["invoices"],
                pages["clients"],
            ],
            "💰 Finance": [
                pages["payments"],
                pages["lightning"],
            ],
            "🤖 AI & Tools": [
                pages["ai_assistant"],
                pages["batch"],
                pages["reports"],
            ],
            "⚙️ Settings": [
                pages["settings"],
            ],
        },
        position="sidebar",  # Navigation in sidebar
    )

    return navigation


def setup_navigation_with_conditions() -> st.Page:
    """
    Setup conditional navigation based on features/auth.

    Best Practice: Show/hide pages dynamically based on:
    - Feature flags
    - User permissions
    - App configuration

    Returns:
        Currently selected st.Page

    Example:
        >>> # Only show Lightning if enabled
        >>> page = setup_navigation_with_conditions()
        >>> page.run()
    """
    from openfatture.utils.config import get_settings

    settings = get_settings()
    pages = create_page_registry()

    # Build navigation dict conditionally
    nav_dict = {
        "🏠 Home": [pages["home"]],
        "📊 Business": [
            pages["dashboard"],
            pages["invoices"],
            pages["clients"],
        ],
        "💰 Finance": [pages["payments"]],
        "🤖 AI & Tools": [],
        "⚙️ Settings": [pages["settings"]],
    }

    # Add Lightning only if enabled
    if getattr(settings, "lightning_enabled", False):
        nav_dict["💰 Finance"].append(pages["lightning"])

    # Add AI features only if configured
    if settings.ai_chat_enabled:
        nav_dict["🤖 AI & Tools"].append(pages["ai_assistant"])

    # Always show batch and reports
    nav_dict["🤖 AI & Tools"].extend([pages["batch"], pages["reports"]])

    # Remove empty sections
    nav_dict = {k: v for k, v in nav_dict.items() if v}

    navigation = st.navigation(nav_dict, position="sidebar")

    return navigation


# Migration helper: programmatic page switching
def navigate_to(page_id: str) -> None:
    """
    Navigate to a specific page programmatically.

    Best Practice: Use st.session_state to trigger navigation.

    Args:
        page_id: ID of page to navigate to (from page_registry keys)

    Example:
        >>> navigate_to("invoices")  # Navigate to invoices page
    """
    st.session_state.navigate_to = page_id
    st.rerun()


# Example: Render shared sidebar elements
def render_shared_sidebar() -> None:
    """
    Render elements shared across all pages in sidebar.

    Best Practice: Put common UI in the "frame" (app.py) rather than
    repeating in each page.

    This appears above the navigation menu.
    """
    with st.sidebar:
        # Logo
        st.image("https://via.placeholder.com/300x80/3366ff/ffffff?text=OpenFatture", width=250)
        st.markdown("---")

        # Quick stats (common across all pages)
        st.subheader("📊 Quick Stats")

        try:
            from openfatture.cli.ui.dashboard import DashboardData

            data = DashboardData()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Fatture", data.get_total_invoices())
                st.metric("Clienti", data.get_total_clients())
            with col2:
                total_rev = data.get_total_revenue()
                st.metric("Fatturato", f"€{total_rev:,.0f}")
                pending = data.get_pending_amount()
                st.metric("In Sospeso", f"€{pending:,.0f}")

            data.close()

        except Exception as e:
            st.error(f"Errore stats: {e}")

        st.markdown("---")


def render_shared_footer() -> None:
    """
    Render footer shared across all pages.

    Best Practice: Common elements in the frame for consistency.
    """
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p>OpenFatture v1.1.0 | MIT License</p>
        <p>
            <a href='https://github.com/gianlucamazza/openfatture' target='_blank'>GitHub</a> •
            <a href='https://github.com/gianlucamazza/openfatture/issues' target='_blank'>Issues</a> •
            <a href='https://github.com/gianlucamazza/openfatture/blob/main/docs/README.md' target='_blank'>Docs</a>
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
