"""Settings and configuration page.

Display current configuration and provide links to documentation.
"""

import streamlit as st

from openfatture.i18n.translator import Translator
from openfatture.utils.config import get_settings

# Initialize translator
t = Translator()

st.set_page_config(page_title=t("page-settings-page-title"), page_icon="", layout="wide")

st.title(t("page-settings-title"))

# Get settings
settings = get_settings()

# Company info section
st.markdown(f"### {t('page-settings-company-title')}")

col1, col2 = st.columns(2)

not_configured = t("page-settings-not-configured")

with col1:
    st.text_input(
        t("page-settings-company-name"),
        value=settings.cedente_denominazione or not_configured,
        disabled=True,
    )
    st.text_input(
        t("page-settings-company-vat"),
        value=settings.cedente_partita_iva or not_configured,
        disabled=True,
    )
    st.text_input(
        t("page-settings-company-fiscal-code"),
        value=settings.cedente_codice_fiscale or not_configured,
        disabled=True,
    )

with col2:
    st.text_input(
        t("page-settings-company-regime"),
        value=settings.cedente_regime_fiscale or not_configured,
        disabled=True,
    )
    st.text_input(
        t("page-settings-company-address"),
        value=settings.cedente_indirizzo or not_configured,
        disabled=True,
    )
    st.text_input(
        t("page-settings-company-zip-city"),
        value=f"{settings.cedente_cap or ''} {settings.cedente_comune or ''}",
        disabled=True,
    )

# PEC section
st.markdown("---")
st.markdown(f"### {t('page-settings-pec-title')}")

pec_col1, pec_col2 = st.columns(2)

with pec_col1:
    st.text_input(
        t("page-settings-pec-address"),
        value=settings.pec_address or not_configured,
        disabled=True,
        type="password",
    )
    st.text_input(
        t("page-settings-pec-smtp-server"),
        value=settings.pec_smtp_server or not_configured,
        disabled=True,
    )

with pec_col2:
    st.text_input(
        t("page-settings-pec-from"), value=settings.pec_address or not_configured, disabled=True
    )
    st.text_input(
        t("page-settings-pec-smtp-port"), value=str(settings.pec_smtp_port), disabled=True
    )

# AI section
st.markdown("---")
st.markdown(f"### {t('page-settings-ai-title')}")

ai_col1, ai_col2, ai_col3 = st.columns(3)

with ai_col1:
    if settings.ai_chat_enabled:
        st.success(t("page-settings-ai-enabled"))
    else:
        st.warning(t("page-settings-ai-not-configured"))

with ai_col2:
    st.text_input(
        t("page-settings-ai-provider"), value=settings.ai_provider or not_configured, disabled=True
    )

with ai_col3:
    st.text_input(
        t("page-settings-ai-model"), value=settings.ai_model or not_configured, disabled=True
    )

# Database section
st.markdown("---")
st.markdown(f"### {t('page-settings-database-title')}")

st.text_input(t("page-settings-database-url"), value=str(settings.database_url), disabled=True)

# Paths section
st.markdown("---")
st.markdown(f"### {t('page-settings-paths-title')}")

path_col1, path_col2 = st.columns(2)

with path_col1:
    st.text_input(t("page-settings-paths-data-dir"), value=str(settings.data_dir), disabled=True)
    st.text_input(
        t("page-settings-paths-archivio-dir"), value=str(settings.archivio_dir), disabled=True
    )

with path_col2:
    st.text_input(t("page-settings-paths-data-dir"), value=str(settings.data_dir), disabled=True)

# Configuration help
st.markdown("---")
st.markdown(f"### {t('page-settings-guide-title')}")

st.info(t("page-settings-guide-content"))

# Quick links
st.markdown(f"### {t('page-settings-links-title')}")

link_col1, link_col2, link_col3 = st.columns(3)

with link_col1:
    st.markdown(
        f"[{t('page-settings-link-docs')}](https://github.com/gianlucamazza/openfatture/tree/main/docs)"
    )

with link_col2:
    st.markdown(
        f"[{t('page-settings-link-bug')}](https://github.com/gianlucamazza/openfatture/issues)"
    )

with link_col3:
    st.markdown(
        f"[{t('page-settings-link-discussions')}](https://github.com/gianlucamazza/openfatture/discussions)"
    )

# Environment info
st.markdown("---")
st.markdown(f"### {t('page-settings-system-title')}")

import platform
import sys

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.metric(
        t("page-settings-system-python"),
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )

with info_col2:
    st.metric(t("page-settings-system-platform"), platform.system())

with info_col3:
    st.metric(t("page-settings-system-version"), "1.1.0")
