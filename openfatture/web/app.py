"""OpenFatture Web UI - Main Application Entry Point.

This is the home/landing page for the Streamlit web interface.
Run with: streamlit run openfatture/web/app.py
"""

import streamlit as st

from openfatture.core.events import initialize_event_system
from openfatture.core.hooks import initialize_hook_system
from openfatture.utils.config import get_settings
from openfatture.utils.logging import configure_dynamic_logging
from openfatture.web.utils.lifespan import set_event_bus, set_hook_bridge
from openfatture.web.utils.state import init_state

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title="OpenFatture - Fatturazione Elettronica",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/gianlucamazza/openfatture",
        "Report a bug": "https://github.com/gianlucamazza/openfatture/issues",
        "About": """
        # OpenFatture 🧾

        Open-source electronic invoicing for Italian freelancers.

        **Version:** 1.1.0
        **License:** MIT
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
    with st.sidebar:
        st.image("https://via.placeholder.com/300x80/3366ff/ffffff?text=OpenFatture", width=250)

        st.markdown("---")

        # Quick stats in sidebar
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
            st.error(f"Errore caricamento stats: {e}")

        st.markdown("---")

        # Settings info
        st.subheader("⚙️ Configuration")
        settings = get_settings()
        st.text(f"Azienda: {settings.cedente_denominazione or 'N/A'}")
        st.text(f"P.IVA: {settings.cedente_partita_iva or 'N/A'}")
        st.text(f"Regime: {settings.cedente_regime_fiscale or 'N/A'}")

        if settings.ai_chat_enabled:
            st.success("🤖 AI Abilitato")
            st.text(f"Provider: {settings.ai_provider}")
        else:
            st.warning("AI Non Configurato")

        st.markdown("---")

        # Advanced operations
        st.subheader("🔧 Operazioni Avanzate")
        if st.button("📦 Batch Operations", use_container_width=True):
            st.switch_page("pages/8_📦_Batch.py")
        if st.button("📊 Reports", use_container_width=True):
            st.switch_page("pages/9_📊_Reports.py")
        if st.button("🪝 Hooks", use_container_width=True):
            st.switch_page("pages/10_🪝_Hooks.py")
        if st.button("📋 Events", use_container_width=True):
            st.switch_page("pages/11_📋_Events.py")


def render_home() -> None:
    """Render the home page content."""
    # Header
    st.title("🧾 OpenFatture - Fatturazione Elettronica")
    st.markdown(
        """
        ### Benvenuto nella Web UI di OpenFatture

        Sistema completo per la gestione delle fatture elettroniche italiane con:
        - ✨ **Fatturazione FatturaPA** - Genera XML conformi, valida e invia a SDI
        - 💰 **Riconciliazione Pagamenti** - Import bancari e matching intelligente
        - 🤖 **AI Assistant** - Descrizioni intelligenti, consulenza fiscale, chat
        - 📊 **Dashboard & Analytics** - Monitora il tuo business in tempo reale
        """
    )

    st.markdown("---")

    # Feature grid
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🧾 Fatture")
        st.markdown(
            """
            - Creazione guidata
            - Gestione clienti
            - Generazione XML
            - Invio SDI via PEC
            - Tracking notifiche
            """
        )
        if st.button("📝 Vai alle Fatture", use_container_width=True):
            st.switch_page("pages/2_🧾_Fatture.py")

    with col2:
        st.subheader("💰 Pagamenti")
        st.markdown(
            """
            - Import estratti conto
            - Matching automatico
            - Riconciliazione
            - Reminder scadenze
            - Audit trail
            """
        )
        if st.button("💳 Vai ai Pagamenti", use_container_width=True):
            st.switch_page("pages/4_💰_Pagamenti.py")

    with col3:
        st.subheader("🤖 AI Assistant")
        st.markdown(
            """
            - Chat interattivo
            - Descrizioni automatiche
            - Consulenza fiscale
            - Cash flow forecast
            - Compliance check
            """
        )
        if st.button("🚀 Prova l'AI", use_container_width=True):
            st.switch_page("pages/5_🤖_AI_Assistant.py")

    st.markdown("---")

    # Quick actions
    st.subheader("⚡ Azioni Rapide")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        if st.button("➕ Nuova Fattura", use_container_width=True):
            st.switch_page("pages/2_🧾_Fatture.py")

    with col_b:
        if st.button("👤 Nuovo Cliente", use_container_width=True):
            st.switch_page("pages/3_👥_Clienti.py")

    with col_c:
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/1_📊_Dashboard.py")

    with col_d:
        if st.button("📦 Batch Operations", use_container_width=True):
            st.switch_page("pages/8_📦_Batch.py")

    # Additional quick actions row
    st.markdown("---")
    st.subheader("🔧 Strumenti Avanzati")

    col_e, col_f, col_g = st.columns(3)

    with col_e:
        if st.button("📊 Reports", use_container_width=True):
            st.switch_page("pages/9_📊_Reports.py")

    with col_f:
        if st.button("🪝 Hooks", use_container_width=True):
            st.switch_page("pages/10_🪝_Hooks.py")

    with col_g:
        if st.button("📋 Events", use_container_width=True):
            st.switch_page("pages/11_📋_Events.py")

    st.markdown("---")

    # Getting started
    with st.expander("🚀 Getting Started", expanded=False):
        st.markdown(
            """
            ### Primi Passi

            1. **Configura l'ambiente**
               - Assicurati che `.env` sia configurato correttamente
               - Verifica i dati aziendali (P.IVA, regime fiscale)
               - Configura credenziali PEC per invio SDI

            2. **Crea i primi clienti**
               - Vai su "👥 Clienti" → "Aggiungi Cliente"
               - Inserisci i dati fiscali (P.IVA, codice fiscale)
               - Specifica SDI o PEC per ricezione fatture

            3. **Emetti la prima fattura**
               - "🧾 Fatture" → "Nuova Fattura"
               - Seleziona cliente e aggiungi righe
               - Genera XML e invia a SDI

            4. **Esplora l'AI Assistant**
               - Prova la chat per domande fiscali
               - Genera descrizioni intelligenti
               - Ottieni suggerimenti IVA automatici

            ### Documentazione

            - [README.md](https://github.com/gianlucamazza/openfatture)
            - [Guida Rapida](https://github.com/gianlucamazza/openfatture/blob/main/QUICKSTART.md)
            - [Configurazione](https://github.com/gianlucamazza/openfatture/blob/main/docs/CONFIGURATION.md)
            - [CLI Reference](https://github.com/gianlucamazza/openfatture/blob/main/docs/CLI_REFERENCE.md)
            """
        )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>OpenFatture v1.1.0 | MIT License | Made with ❤️ by freelancers, for freelancers</p>
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

        # Log the error
        log_error(e, "main_app", {"page": "home"})

        # Show user-friendly error message
        st.error("🚨 Si è verificato un errore imprevisto. Riprova più tardi.")

        # Show error details in development/debug mode
        from openfatture.utils.config import get_settings

        if get_settings().debug_config.enable_debug_logging:
            st.exception(e)

        # Provide recovery options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Ricarica Pagina"):
                st.rerun()
        with col2:
            if st.button("🏥 Vai alla Dashboard Salute"):
                st.switch_page("pages/12_🏥_Health.py")


if __name__ == "__main__":
    main()
