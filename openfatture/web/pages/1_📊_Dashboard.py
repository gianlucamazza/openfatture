"""Dashboard page with KPIs and analytics.

Displays key business metrics, charts, and recent activity.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from openfatture.cli.ui.dashboard import DashboardData
from openfatture.web.services.invoice_service import StreamlitInvoiceService

st.set_page_config(page_title="Dashboard - OpenFatture", page_icon="📊", layout="wide")

# Title
st.title("📊 Dashboard")
st.markdown("### Panoramica Business Real-Time")

# Initialize services
invoice_service = StreamlitInvoiceService()


@st.cache_data(ttl=30, show_spinner=False)
def get_dashboard_data() -> DashboardData:
    """Get cached dashboard data."""
    return DashboardData()


# Get data
try:
    data = get_dashboard_data()

    # KPI Row
    st.markdown("### 📈 Metriche Principali")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_invoices = data.get_total_invoices()
        st.metric(
            label="📄 Totale Fatture",
            value=total_invoices,
            delta=None,
        )

    with col2:
        total_clients = data.get_total_clients()
        st.metric(
            label="👥 Clienti Attivi",
            value=total_clients,
            delta=None,
        )

    with col3:
        total_revenue = data.get_total_revenue()
        st.metric(
            label="💰 Fatturato Totale",
            value=f"€{total_revenue:,.2f}",
            delta=None,
        )

    with col4:
        revenue_month = data.get_revenue_this_month()
        st.metric(
            label="📅 Fatturato Mese",
            value=f"€{revenue_month:,.2f}",
            delta=None,
        )

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📊 Fatture per Stato")

        # Invoice status distribution
        status_data = data.get_invoices_by_status()

        if status_data:
            status_labels = [s.replace("_", " ").title() for s, _ in status_data]
            status_counts = [c for _, c in status_data]

            fig_status = px.pie(
                names=status_labels,
                values=status_counts,
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            fig_status.update_traces(textposition="inside", textinfo="percent+label")
            fig_status.update_layout(
                showlegend=True,
                height=350,
                margin={"l": 20, "r": 20, "t": 40, "b": 20},
            )

            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Nessuna fattura presente")

    with col_right:
        st.markdown("#### 📈 Fatturato Ultimi 6 Mesi")

        # Monthly revenue chart
        monthly_data = data.get_monthly_revenue(months=6)

        if monthly_data:
            months = [m for m, _ in monthly_data]
            revenues = [float(r) for _, r in monthly_data]

            fig_revenue = go.Figure()

            fig_revenue.add_trace(
                go.Bar(
                    x=months,
                    y=revenues,
                    marker_color="lightseagreen",
                    text=[f"€{r:,.0f}" for r in revenues],
                    textposition="outside",
                )
            )

            fig_revenue.update_layout(
                yaxis_title="Fatturato (€)",
                xaxis_title="Mese",
                height=350,
                margin={"l": 20, "r": 20, "t": 40, "b": 20},
                showlegend=False,
            )

            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("Nessun dato disponibile")

    st.markdown("---")

    # Bottom row - Tables
    col_bottom_left, col_bottom_right = st.columns(2)

    with col_bottom_left:
        st.markdown("#### 👑 Top 5 Clienti")

        top_clients = data.get_top_clients(limit=5)

        if top_clients:
            import pandas as pd

            df_clients = pd.DataFrame(
                top_clients,
                columns=["Cliente", "N. Fatture", "Fatturato"],
            )
            df_clients["Fatturato"] = df_clients["Fatturato"].apply(lambda x: f"€{float(x):,.2f}")

            st.dataframe(
                df_clients,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cliente": st.column_config.TextColumn("Cliente", width="large"),
                    "N. Fatture": st.column_config.NumberColumn("Fatture"),
                    "Fatturato": st.column_config.TextColumn("Fatturato", width="medium"),
                },
            )
        else:
            st.info("Nessun cliente presente")

    with col_bottom_right:
        st.markdown("#### 🕐 Ultime 5 Fatture")

        recent = data.get_recent_invoices(limit=5)

        if recent:
            import pandas as pd

            df_recent = pd.DataFrame(
                [
                    {
                        "Numero": f"{f.numero}/{f.anno}",
                        "Data": f.data_emissione.strftime("%d/%m/%Y"),
                        "Cliente": (
                            (f.cliente.denominazione[:30] + "...")
                            if len(f.cliente.denominazione) > 30
                            else f.cliente.denominazione
                        ),
                        "Totale": f"€{float(f.totale):,.2f}",
                        "Stato": f.stato.value,
                    }
                    for f in recent
                    if f.cliente is not None
                ]
            )

            st.dataframe(
                df_recent,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Nessuna fattura presente")

    st.markdown("---")

    # Payment stats panel
    st.markdown("#### 💳 Tracking Pagamenti")

    payment_stats = data.get_payment_stats()

    pcol1, pcol2, pcol3, pcol4 = st.columns(4)

    with pcol1:
        st.metric("🔍 Non Abbinati", payment_stats["unmatched"])

    with pcol2:
        st.metric("✅ Abbinati", payment_stats["matched"])

    with pcol3:
        st.metric("⏭️ Ignorati", payment_stats["ignored"])

    with pcol4:
        total_transactions = sum(payment_stats.values())
        st.metric("📊 Totale Transazioni", total_transactions)

    # Payment due summary
    st.markdown("---")
    st.markdown("#### 💰 Scadenze Pagamenti (Prossimi 30 gg)")

    payment_due = data.get_payment_due_summary(window_days=30, max_upcoming=10)

    if payment_due.overdue or payment_due.due_soon or payment_due.upcoming:
        import pandas as pd

        # Combine all entries
        all_entries = payment_due.overdue + payment_due.due_soon + payment_due.upcoming

        df_due = pd.DataFrame(
            [
                {
                    "Fattura": entry.invoice_ref,
                    "Cliente": (
                        entry.client_name[:30] + "..."
                        if len(entry.client_name) > 30
                        else entry.client_name
                    ),
                    "Scadenza": entry.due_date.strftime("%d/%m/%Y"),
                    "Giorni": entry.days_delta,
                    "Residuo": f"€{float(entry.residual):,.2f}",
                    "Stato": entry.status.value.replace("_", " ").title(),
                    "Categoria": (
                        "🔴 Scaduto"
                        if entry in payment_due.overdue
                        else "🟡 In scadenza" if entry in payment_due.due_soon else "🟢 Prossimo"
                    ),
                }
                for entry in all_entries
            ]
        )

        st.dataframe(
            df_due,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Giorni": st.column_config.NumberColumn("Δ Giorni", help="Giorni alla scadenza"),
                "Residuo": st.column_config.TextColumn("Importo Residuo"),
            },
        )

        st.metric(
            "💸 Totale Residuo da Incassare",
            f"€{float(payment_due.total_outstanding):,.2f}",
        )
    else:
        st.success("✅ Nessun pagamento in scadenza")

    # Close data connection
    data.close()

except Exception as e:
    st.error(f"❌ Errore caricamento dashboard: {e}")
    st.exception(e)

# Refresh button
st.markdown("---")
if st.button("🔄 Aggiorna Dati", type="secondary"):
    st.cache_data.clear()
    st.rerun()
