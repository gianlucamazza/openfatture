"""Lightning Network payment management through web interface.

Create and manage Lightning invoices, monitor channels, and track payments.
"""

import streamlit as st

from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-lightning-page-title"), page_icon="", layout="wide")

st.title(t("page-lightning-title"))

# Check if Lightning is enabled
from openfatture.utils.config import get_settings

settings = get_settings()

if not settings.lightning_enabled:
    st.warning(t("page-lightning-not-enabled"))
    st.stop()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(t("page-lightning-invoices-title"))
    st.info(t("page-lightning-invoices-info"))

with col2:
    st.subheader(t("page-lightning-channels-title"))
    st.info(t("page-lightning-channels-info"))

# Recent Lightning invoices section
st.subheader(t("page-lightning-recent-title"))
st.info(t("page-lightning-recent-info"))

# Channel status section
st.subheader(t("page-lightning-status-title"))

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(t("page-lightning-metric-active"), "0", help=t("page-lightning-metric-active-help"))

with col2:
    st.metric(
        t("page-lightning-metric-capacity"), "0 SAT", help=t("page-lightning-metric-capacity-help")
    )

with col3:
    st.metric(
        t("page-lightning-metric-inbound"), "0%", help=t("page-lightning-metric-inbound-help")
    )

st.info(t("page-lightning-technical-notes"))

# Configuration section
with st.expander(t("page-lightning-config-title")):
    st.code(
        f"""
# Impostazioni correnti
lightning_enabled: {settings.lightning_enabled}
lightning_host: {settings.lightning_host}
lightning_timeout_seconds: {settings.lightning_timeout_seconds}
lightning_max_retries: {settings.lightning_max_retries}

# Provider BTC/EUR
lightning_coingecko_enabled: {settings.lightning_coingecko_enabled}
lightning_cmc_enabled: {settings.lightning_cmc_enabled}
lightning_fallback_rate: {settings.lightning_fallback_rate}

# Liquidità
lightning_liquidity_enabled: {settings.lightning_liquidity_enabled}
lightning_liquidity_min_ratio: {settings.lightning_liquidity_min_ratio}
lightning_liquidity_target_ratio: {settings.lightning_liquidity_target_ratio}
    """,
        language="yaml",
    )

    st.info(t("page-lightning-config-info"))
