"""Lightning Network payment management through web interface.

Create and manage Lightning invoices, monitor channels, and track payments.
"""

import streamlit as st

st.set_page_config(page_title="Lightning - OpenFatture", page_icon="⚡", layout="wide")

st.title("⚡ Lightning Network Pagamenti")

# Check if Lightning is enabled
from openfatture.utils.config import get_settings

settings = get_settings()

if not settings.lightning_enabled:
    st.warning(
        """
    ⚠️ **Lightning Network non abilitato**

    Per utilizzare i pagamenti Lightning:

    1. Abilita Lightning nelle impostazioni:
       ```bash
       uv run openfatture config set lightning_enabled true
       ```

    2. Configura la connessione LND:
       ```bash
       uv run openfatture config set lightning_host "localhost:10009"
       uv run openfatture config set lightning_cert_path "/path/to/tls.cert"
       uv run openfatture config set lightning_macaroon_path "/path/to/admin.macaroon"
       ```

    3. Riavvia l'applicazione
    """
    )
    st.stop()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Gestione Fatture Lightning")

    st.info(
        """
    **🚧 Feature in sviluppo**

    La gestione fatture Lightning via Web UI sarà disponibile a breve!

    Per ora, crea fatture Lightning tramite CLI:

    ```bash
    # Crea fattura da fattura esistente
    uv run openfatture lightning invoice create --fattura-id 123

    # Crea fattura zero-amount
    uv run openfatture lightning invoice create --amount 0 --description "Donazione"

    # Lista fatture Lightning
    uv run openfatture lightning invoice list
    ```
    """
    )

with col2:
    st.subheader("📊 Stato Canali")

    st.info(
        """
    **Monitoraggio Canali**

    ```bash
    # Stato canali
    uv run openfatture lightning channels status

    # Report liquidità
    uv run openfatture lightning liquidity report

    # Monitoraggio automatico
    uv run openfatture lightning liquidity monitor --start
    ```
    """
    )

# Recent Lightning invoices section
st.subheader("🕒 Fatture Lightning Recenti")

st.info(
    "Le fatture Lightning recenti verranno mostrate qui una volta implementata l'integrazione completa."
)

# Channel status section
st.subheader("🔗 Stato Canali Lightning")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Canali Attivi", "0", help="Canali Lightning attivi")

with col2:
    st.metric("Capacità Totale", "0 SAT", help="Capacità totale canali")

with col3:
    st.metric("Liquidità Inbound", "0%", help="Percentuale liquidità inbound")

st.info(
    """
**Note tecniche:**

- **LND**: Lightning Network Daemon connection required
- **Rate Provider**: BTC/EUR conversion via CoinGecko/CoinMarketCap
- **Sicurezza**: TLS + Macaroon authentication
- **Webhook**: Real-time payment notifications support
"""
)

# Configuration section
with st.expander("⚙️ Configurazione Lightning"):
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

    st.info(
        """
    **Modifica configurazione:**

    ```bash
    uv run openfatture config set lightning_host "your-lnd-host:10009"
    uv run openfatture config set lightning_cert_path "/path/to/tls.cert"
    uv run openfatture config set lightning_macaroon_path "/path/to/admin.macaroon"
    ```
    """
    )
