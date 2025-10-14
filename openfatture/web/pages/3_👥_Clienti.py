"""Client management page (placeholder).

List and manage clients through web interface.
"""

import streamlit as st

st.set_page_config(page_title="Clienti - OpenFatture", page_icon="👥", layout="wide")

st.title("👥 Gestione Clienti")

st.info(
    """
    **🚧 Feature in sviluppo**

    La gestione clienti via Web UI sarà disponibile a breve!

    Per ora, gestisci i clienti tramite CLI:

    ```bash
    # Lista clienti
    uv run openfatture cliente list

    # Aggiungi cliente (interattivo)
    uv run openfatture cliente add "Nome Cliente" --interactive

    # Dettaglio cliente
    uv run openfatture cliente show <id>
    ```

    Consulta `docs/CLI_REFERENCE.md` per tutti i comandi disponibili.
    """
)

# Quick preview using DashboardData
st.markdown("### 📊 Anteprima Rapida")

try:
    from openfatture.cli.ui.dashboard import DashboardData

    data = DashboardData()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("👥 Totale Clienti", data.get_total_clients())

    with col2:
        st.metric("📄 Totale Fatture", data.get_total_invoices())

    st.markdown("#### 👑 Top 5 Clienti")

    top_clients = data.get_top_clients(limit=5)

    if top_clients:
        import pandas as pd

        df = pd.DataFrame(top_clients, columns=["Cliente", "N. Fatture", "Fatturato Totale"])
        df["Fatturato Totale"] = df["Fatturato Totale"].apply(lambda x: f"€{float(x):,.2f}")

        st.dataframe(df, use_container_width=True, hide_index=True)

    data.close()

except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
