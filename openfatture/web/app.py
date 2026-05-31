"""OpenFatture Web UI - Main Application Entry Point.

This is the home/landing page for the Streamlit web interface.
Run with: streamlit run openfatture/web/app.py
"""

import streamlit as st

from openfatture.core.events import initialize_event_system
from openfatture.core.hooks import initialize_hook_system
from openfatture.utils.config import get_settings
from openfatture.utils.logging import configure_dynamic_logging
from openfatture.web.utils.i18n import get_translator, init_i18n, render_language_selector
from openfatture.web.utils.lifespan import set_event_bus, set_hook_bridge
from openfatture.web.utils.state import init_state

# Initialize i18n BEFORE any Streamlit commands
init_i18n()

# Get translator for page config (uses default language on first load)
t = get_translator()

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title=t("web-app-title"),
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/gianlucamazza/openfatture",
        "Report a bug": "https://github.com/gianlucamazza/openfatture/issues",
        "About": f"""
        # OpenFatture

        {t("web-app-tagline")}

        **{t("web-app-version", version="1.1.0")}**
        **{t("web-app-license")}**
        **Repository:** https://github.com/gianlucamazza/openfatture
        """,
    },
)

# Initialize dynamic logging configuration
settings = get_settings()
configure_dynamic_logging(settings.debug_config)

# Initialize event system and hook system (same as CLI)
event_bus = initialize_event_system(settings)
hook_bridge = initialize_hook_system(event_bus)

# Store in context for access from services
set_event_bus(event_bus)
set_hook_bridge(hook_bridge)


def render_sidebar() -> None:
    """Render the sidebar with navigation and info."""
    t = get_translator()

    with st.sidebar:
        st.image("https://via.placeholder.com/300x80/3366ff/ffffff?text=OpenFatture", width=250)

        st.markdown("---")

        # Language selector
        render_language_selector()

        st.markdown("---")

        # Quick stats in sidebar
        st.subheader(t("web-sidebar-quick-stats"))

        try:
            from openfatture.cli.ui.dashboard import DashboardData

            data = DashboardData()

            col1, col2 = st.columns(2)
            with col1:
                st.metric(t("web-sidebar-invoices"), data.get_total_invoices())
                st.metric(t("web-sidebar-clients"), data.get_total_clients())
            with col2:
                total_rev = data.get_total_revenue()
                st.metric(t("web-sidebar-revenue"), f"€{total_rev:,.0f}")
                pending = data.get_pending_amount()
                st.metric(t("web-sidebar-pending"), f"€{pending:,.0f}")

            data.close()

        except Exception as e:
            st.error(t("web-sidebar-error-loading-stats", error=str(e)))

        st.markdown("---")

        # Settings info
        st.subheader(t("web-sidebar-configuration"))
        settings = get_settings()
        st.text(f"{t('web-sidebar-company')}: {settings.cedente_denominazione or 'N/A'}")
        st.text(f"{t('web-sidebar-vat-number')}: {settings.cedente_partita_iva or 'N/A'}")
        st.text(f"{t('web-sidebar-tax-regime')}: {settings.cedente_regime_fiscale or 'N/A'}")

        if settings.ai_chat_enabled:
            st.success(t("web-sidebar-ai-enabled"))
            st.text(f"{t('web-sidebar-ai-provider')}: {settings.ai_provider}")
        else:
            st.warning(t("web-sidebar-ai-disabled"))

        st.markdown("---")

        # Advanced operations
        st.subheader(t("web-sidebar-advanced-ops"))
        if st.button(f"{t('web-nav-batch')}", use_container_width=True):
            st.switch_page("pages/8_Batch.py")
        if st.button(f"{t('web-nav-reports')}", use_container_width=True):
            st.switch_page("pages/9_Reports.py")
        if st.button(f"{t('web-nav-hooks')}", use_container_width=True):
            st.switch_page("pages/10_Hooks.py")
        if st.button(f"{t('web-nav-events')}", use_container_width=True):
            st.switch_page("pages/11_Events.py")


def render_home() -> None:
    """Render the home page content."""
    t = get_translator()

    # Header
    st.title(t("page-home-title"))
    st.markdown(
        f"""
        ### {t("page-home-welcome")}

        {t("page-home-description")}
        - **{t("page-home-feature-invoicing")}**
        - **{t("page-home-feature-payments")}**
        - **{t("page-home-feature-ai")}**
        - **{t("page-home-feature-batch")}**
        """
    )

    st.markdown("---")

    # Feature grid
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader(t("page-home-feature-grid-invoices-title"))
        st.markdown(
            f"""
            - {t("page-home-feature-grid-invoices-item-1")}
            - {t("page-home-feature-grid-invoices-item-2")}
            - {t("page-home-feature-grid-invoices-item-3")}
            - {t("page-home-feature-grid-invoices-item-4")}
            - {t("page-home-feature-grid-invoices-item-5")}
            """
        )
        if st.button(t("page-home-feature-grid-invoices-button"), use_container_width=True):
            st.switch_page("pages/2_Fatture.py")

    with col2:
        st.subheader(t("page-home-feature-grid-payments-title"))
        st.markdown(
            f"""
            - {t("page-home-feature-grid-payments-item-1")}
            - {t("page-home-feature-grid-payments-item-2")}
            - {t("page-home-feature-grid-payments-item-3")}
            - {t("page-home-feature-grid-payments-item-4")}
            - {t("page-home-feature-grid-payments-item-5")}
            """
        )
        if st.button(t("page-home-feature-grid-payments-button"), use_container_width=True):
            st.switch_page("pages/4_Pagamenti.py")

    with col3:
        st.subheader(t("page-home-feature-grid-ai-title"))
        st.markdown(
            f"""
            - {t("page-home-feature-grid-ai-item-1")}
            - {t("page-home-feature-grid-ai-item-2")}
            - {t("page-home-feature-grid-ai-item-3")}
            - {t("page-home-feature-grid-ai-item-4")}
            - {t("page-home-feature-grid-ai-item-5")}
            """
        )
        if st.button(t("page-home-feature-grid-ai-button"), use_container_width=True):
            st.switch_page("pages/5_AI_Assistant.py")

    st.markdown("---")

    # Quick actions
    st.subheader(t("page-home-quick-actions"))

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        if st.button(t("page-home-action-new-invoice"), use_container_width=True):
            st.switch_page("pages/2_Fatture.py")

    with col_b:
        if st.button(t("page-home-action-new-client"), use_container_width=True):
            st.switch_page("pages/3_Clienti.py")

    with col_c:
        if st.button(t("page-home-action-dashboard"), use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")

    with col_d:
        if st.button(t("page-home-action-batch"), use_container_width=True):
            st.switch_page("pages/8_Batch.py")

    # Additional quick actions row
    st.markdown("---")
    st.subheader(t("page-home-advanced-tools"))

    col_e, col_f, col_g = st.columns(3)

    with col_e:
        if st.button(t("page-home-advanced-reports"), use_container_width=True):
            st.switch_page("pages/9_Reports.py")

    with col_f:
        if st.button(t("page-home-advanced-hooks"), use_container_width=True):
            st.switch_page("pages/10_Hooks.py")

    with col_g:
        if st.button(t("page-home-advanced-events"), use_container_width=True):
            st.switch_page("pages/11_Events.py")

    st.markdown("---")

    # Getting started
    with st.expander(t("page-home-getting-started"), expanded=False):
        st.markdown(
            f"""
            ### {t("page-home-getting-started-title")}

            **{t("page-home-step-1-title")}**
               - {t("page-home-step-1-item-1")}
               - {t("page-home-step-1-item-2")}
               - {t("page-home-step-1-item-3")}

            **{t("page-home-step-2-title")}**
               - {t("page-home-step-2-item-1")}
               - {t("page-home-step-2-item-2")}
               - {t("page-home-step-2-item-3")}

            **{t("page-home-step-3-title")}**
               - {t("page-home-step-3-item-1")}
               - {t("page-home-step-3-item-2")}
               - {t("page-home-step-3-item-3")}

            **{t("page-home-step-4-title")}**
               - {t("page-home-step-4-item-1")}
               - {t("page-home-step-4-item-2")}
               - {t("page-home-step-4-item-3")}

            ### {t("page-home-docs-title")}

            - [README.md](https://github.com/gianlucamazza/openfatture)
            - [Guida Rapida](https://github.com/gianlucamazza/openfatture/blob/main/QUICKSTART.md)
            - [Configurazione](https://github.com/gianlucamazza/openfatture/blob/main/docs/CONFIGURATION.md)
            - [CLI Reference](https://github.com/gianlucamazza/openfatture/blob/main/docs/CLI_REFERENCE.md)
            """
        )

    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #666;'>
        <p>{t("page-home-footer-version", version="1.1.0")} | {t("page-home-footer-license")} | {t("page-home-footer-tagline")}</p>
        <p>
            <a href='https://github.com/gianlucamazza/openfatture' target='_blank'>GitHub</a> •
            <a href='https://github.com/gianlucamazza/openfatture/issues' target='_blank'>Issues</a> •<br>
            <a href='https://github.com/gianlucamazza/openfatture/blob/main/docs/README.md' target='_blank'>Documentation</a>
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main application entry point."""
    try:
        # Initialize app state
        init_state("initialized", True)

        # Render components
        render_sidebar()
        render_home()

    except Exception as e:
        # Global error handling - Best Practices 2025
        from openfatture.web.utils.logging_config import log_error

        # Get translator for error messages
        t = get_translator()

        # Log the error
        log_error(e, "main_app", {"page": "home"})

        # Show user-friendly error message
        st.error(t("web-error-unexpected"))

        # Show error details in development/debug mode
        from openfatture.utils.config import get_settings

        if get_settings().debug_config.enable_debug_logging:
            st.exception(e)

        # Provide recovery options
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("web-error-reload-page")):
                st.rerun()
        with col2:
            if st.button(t("web-error-goto-health")):
                st.switch_page("pages/12_Health.py")


if __name__ == "__main__":
    main()
