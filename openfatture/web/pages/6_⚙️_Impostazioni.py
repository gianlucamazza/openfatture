"""Settings and configuration page.

Display current configuration and provide links to documentation.
"""

import streamlit as st
from openfatture.utils.config import get_settings

st.set_page_config(page_title="Impostazioni - OpenFatture", page_icon="⚙️", layout="wide")

st.title("⚙️ Impostazioni & Configurazione")

# Get settings
settings = get_settings()

# Company info section
st.markdown("### 🏢 Dati Azienda")

col1, col2 = st.columns(2)

with col1:
    st.text_input("Denominazione", value=settings.cedente_denominazione or "Non configurato", disabled=True)
    st.text_input("Partita IVA", value=settings.cedente_partita_iva or "Non configurato", disabled=True)
    st.text_input("Codice Fiscale", value=settings.cedente_codice_fiscale or "Non configurato", disabled=True)

with col2:
    st.text_input("Regime Fiscale", value=settings.cedente_regime_fiscale or "Non configurato", disabled=True)
    st.text_input("Indirizzo", value=settings.cedente_indirizzo or "Non configurato", disabled=True)
    st.text_input("CAP - Comune", value=f"{settings.cedente_cap or ''} {settings.cedente_comune or ''}", disabled=True)

# PEC section
st.markdown("---")
st.markdown("### 📧 Configurazione PEC (SDI)")

pec_col1, pec_col2 = st.columns(2)

with pec_col1:
    st.text_input("PEC Username", value=settings.pec_username or "Non configurato", disabled=True, type="password")
    st.text_input("SMTP Server", value=settings.pec_smtp_server or "Non configurato", disabled=True)

with pec_col2:
    st.text_input("PEC From", value=settings.pec_from_email or "Non configurato", disabled=True)
    st.text_input("SMTP Port", value=str(settings.pec_smtp_port), disabled=True)

# AI section
st.markdown("---")
st.markdown("### 🤖 Configurazione AI")

ai_col1, ai_col2, ai_col3 = st.columns(3)

with ai_col1:
    if settings.ai_enabled:
        st.success("✅ AI Abilitato")
    else:
        st.warning("⚠️ AI Non Configurato")

with ai_col2:
    st.text_input("Provider", value=settings.ai_provider or "Non configurato", disabled=True)

with ai_col3:
    st.text_input("Model", value=settings.ai_model or "Non configurato", disabled=True)

# Database section
st.markdown("---")
st.markdown("### 💾 Database")

st.text_input("Database URL", value=str(settings.database_url), disabled=True)

# Paths section
st.markdown("---")
st.markdown("### 📁 Percorsi")

path_col1, path_col2 = st.columns(2)

with path_col1:
    st.text_input("Data Directory", value=str(settings.data_dir), disabled=True)
    st.text_input("Archivio Directory", value=str(settings.archivio_dir), disabled=True)

with path_col2:
    st.text_input("Temp Directory", value=str(settings.temp_dir), disabled=True)

# Configuration help
st.markdown("---")
st.markdown("### 📖 Guida Configurazione")

st.info(
    """
    **Modificare la configurazione:**

    1. Edita il file `.env` nella root del progetto
    2. Usa `.env.example` come template
    3. Riavvia l'applicazione per applicare le modifiche

    **Documentazione completa:**
    - `docs/CONFIGURATION.md` - Reference completo variabili
    - `docs/QUICKSTART.md` - Setup iniziale
    - `.env.example` - Template configurazione
    """
)

# Quick links
st.markdown("### 🔗 Link Utili")

link_col1, link_col2, link_col3 = st.columns(3)

with link_col1:
    st.markdown("[📚 Documentazione](https://github.com/gianlucamazza/openfatture/tree/main/docs)")

with link_col2:
    st.markdown("[🐛 Report Bug](https://github.com/gianlucamazza/openfatture/issues)")

with link_col3:
    st.markdown("[💬 Discussions](https://github.com/gianlucamazza/openfatture/discussions)")

# Environment info
st.markdown("---")
st.markdown("### ℹ️ Informazioni Sistema")

import sys
import platform

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

with info_col2:
    st.metric("Platform", platform.system())

with info_col3:
    st.metric("App Version", "1.1.0")
