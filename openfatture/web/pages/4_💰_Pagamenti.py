"""Payment tracking and reconciliation page (placeholder).

Manage payment reconciliation through web interface.
"""

import streamlit as st

st.set_page_config(page_title="Pagamenti - OpenFatture", page_icon="💰", layout="wide")

st.title("💰 Tracking & Riconciliazione Pagamenti")

st.info(
    """
    **🚧 Feature in sviluppo**

    La riconciliazione pagamenti via Web UI sarà disponibile a breve!

    Per ora, gestisci i pagamenti tramite CLI:

    ```bash
    # Import estratto conto
    uv run openfatture payment import statement.ofx --account 1

    # Match automatico
    uv run openfatture payment match --auto-apply

    # Riconciliazione batch
    uv run openfatture payment reconcile --account 1

    # Review queue interattiva
    uv run openfatture payment queue --interactive

    # Statistiche
    uv run openfatture payment stats
    ```

    Consulta `docs/PAYMENT_TRACKING.md` per la guida completa.
    """
)

# Quick stats
st.markdown("### 📊 Statistiche Pagamenti")

try:
    from openfatture.cli.ui.dashboard import DashboardData

    data = DashboardData()

    payment_stats = data.get_payment_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🔍 Non Abbinati", payment_stats["unmatched"])

    with col2:
        st.metric("✅ Abbinati", payment_stats["matched"])

    with col3:
        st.metric("⏭️ Ignorati", payment_stats["ignored"])

    with col4:
        total = sum(payment_stats.values())
        st.metric("📊 Totale", total)

    # Payment due
    st.markdown("---")
    st.markdown("### 💳 Scadenze Prossimi 30 Giorni")

    payment_due = data.get_payment_due_summary(window_days=30, max_upcoming=10)

    if payment_due.overdue or payment_due.due_soon or payment_due.upcoming:
        import pandas as pd

        all_entries = payment_due.overdue + payment_due.due_soon + payment_due.upcoming

        df = pd.DataFrame(
            [
                {
                    "Fattura": e.invoice_ref,
                    "Cliente": e.client_name[:30],
                    "Scadenza": e.due_date.strftime("%d/%m/%Y"),
                    "Residuo": f"€{float(e.residual):,.2f}",
                    "Stato": e.status.value.replace("_", " ").title(),
                }
                for e in all_entries
            ]
        )

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.metric("💸 Totale Residuo", f"€{float(payment_due.total_outstanding):,.2f}")
    else:
        st.success("✅ Nessun pagamento in scadenza")

    data.close()

except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
