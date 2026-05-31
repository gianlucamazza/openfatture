"""Dashboard page with KPIs and analytics.

Displays key business metrics, charts, and recent activity.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from openfatture.cli.ui.dashboard import DashboardData
from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-dashboard-title"), page_icon="", layout="wide")

# Title
st.title(t("page-dashboard-title"))
st.markdown(f"### {t('page-dashboard-subtitle')}")

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
    st.markdown(f"### {t('page-dashboard-kpi-section')}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_invoices = data.get_total_invoices()
        st.metric(
            label=t("page-dashboard-kpi-total-invoices"),
            value=total_invoices,
            delta=None,
        )

    with col2:
        total_clients = data.get_total_clients()
        st.metric(
            label=t("page-dashboard-kpi-total-clients"),
            value=total_clients,
            delta=None,
        )

    with col3:
        total_revenue = data.get_total_revenue()
        st.metric(
            label=t("page-dashboard-kpi-total-revenue"),
            value=f"€{total_revenue:,.2f}",
            delta=None,
        )

    with col4:
        revenue_month = data.get_revenue_this_month()
        st.metric(
            label=t("page-dashboard-kpi-revenue-month"),
            value=f"€{revenue_month:,.2f}",
            delta=None,
        )

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"#### {t('page-dashboard-chart-invoices-by-status')}")

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
            st.info(t("page-dashboard-no-invoices"))

    with col_right:
        st.markdown(f"#### {t('page-dashboard-chart-revenue-6-months')}")

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
                yaxis_title=t("page-dashboard-chart-yaxis-revenue"),
                xaxis_title=t("page-dashboard-chart-xaxis-month"),
                height=350,
                margin={"l": 20, "r": 20, "t": 40, "b": 20},
                showlegend=False,
            )

            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info(t("page-dashboard-no-data"))

    st.markdown("---")

    # Bottom row - Tables
    col_bottom_left, col_bottom_right = st.columns(2)

    with col_bottom_left:
        st.markdown(f"#### {t('page-dashboard-top-clients')}")

        top_clients = data.get_top_clients(limit=5)

        if top_clients:
            import pandas as pd

            df_clients = pd.DataFrame(
                top_clients,
                columns=[
                    t("page-dashboard-col-client"),
                    t("page-dashboard-col-num-invoices"),
                    t("page-dashboard-col-revenue"),
                ],
            )
            df_clients[t("page-dashboard-col-revenue")] = df_clients[
                t("page-dashboard-col-revenue")
            ].apply(lambda x: f"€{float(x):,.2f}")

            st.dataframe(
                df_clients,
                use_container_width=True,
                hide_index=True,
                column_config={
                    t("page-dashboard-col-client"): st.column_config.TextColumn(
                        t("page-dashboard-col-client"), width="large"
                    ),
                    t("page-dashboard-col-num-invoices"): st.column_config.NumberColumn(
                        t("page-dashboard-col-num-invoices-short")
                    ),
                    t("page-dashboard-col-revenue"): st.column_config.TextColumn(
                        t("page-dashboard-col-revenue"), width="medium"
                    ),
                },
            )
        else:
            st.info(t("page-dashboard-no-clients"))

    with col_bottom_right:
        st.markdown(f"#### {t('page-dashboard-recent-invoices')}")

        recent = data.get_recent_invoices(limit=5)

        if recent:
            import pandas as pd

            df_recent = pd.DataFrame(
                [
                    {
                        t("page-dashboard-col-number"): f"{f.numero}/{f.anno}",
                        t("page-dashboard-col-date"): f.data_emissione.strftime("%d/%m/%Y"),
                        t("page-dashboard-col-client"): (
                            (f.cliente.denominazione[:30] + "...")
                            if len(f.cliente.denominazione) > 30
                            else f.cliente.denominazione
                        ),
                        t("page-dashboard-col-total"): f"€{float(f.totale):,.2f}",
                        t("page-dashboard-col-status"): f.stato.value,
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
            st.info(t("page-dashboard-no-invoices"))

    st.markdown("---")

    # Payment stats panel
    st.markdown(f"#### {t('page-dashboard-payment-tracking')}")

    payment_stats = data.get_payment_stats()

    pcol1, pcol2, pcol3, pcol4 = st.columns(4)

    with pcol1:
        st.metric(t("page-dashboard-payment-unmatched"), payment_stats["unmatched"])

    with pcol2:
        st.metric(t("page-dashboard-payment-matched"), payment_stats["matched"])

    with pcol3:
        st.metric(t("page-dashboard-payment-ignored"), payment_stats["ignored"])

    with pcol4:
        total_transactions = sum(payment_stats.values())
        st.metric(t("page-dashboard-payment-total"), total_transactions)

    # Payment due summary
    st.markdown("---")
    st.markdown(f"#### {t('page-dashboard-payment-due-30')}")

    payment_due = data.get_payment_due_summary(window_days=30, max_upcoming=10)

    if payment_due.overdue or payment_due.due_soon or payment_due.upcoming:
        import pandas as pd

        # Combine all entries
        all_entries = payment_due.overdue + payment_due.due_soon + payment_due.upcoming

        df_due = pd.DataFrame(
            [
                {
                    t("page-dashboard-col-invoice"): entry.invoice_ref,
                    t("page-dashboard-col-client"): (
                        entry.client_name[:30] + "..."
                        if len(entry.client_name) > 30
                        else entry.client_name
                    ),
                    t("page-dashboard-col-due-date"): entry.due_date.strftime("%d/%m/%Y"),
                    t("page-dashboard-col-days"): entry.days_delta,
                    t("page-dashboard-col-residual"): f"€{float(entry.residual):,.2f}",
                    t("page-dashboard-col-status"): entry.status.value.replace("_", " ").title(),
                    t("page-dashboard-col-category"): (
                        t("page-dashboard-category-overdue")
                        if entry in payment_due.overdue
                        else (
                            t("page-dashboard-category-due-soon")
                            if entry in payment_due.due_soon
                            else t("page-dashboard-category-upcoming")
                        )
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
                t("page-dashboard-col-days"): st.column_config.NumberColumn(
                    t("page-dashboard-col-days-delta"), help=t("page-dashboard-col-days-help")
                ),
                t("page-dashboard-col-residual"): st.column_config.TextColumn(
                    t("page-dashboard-col-residual-amount")
                ),
            },
        )

        st.metric(
            t("page-dashboard-total-outstanding"),
            f"€{float(payment_due.total_outstanding):,.2f}",
        )
    else:
        st.success(t("page-dashboard-no-payments-due"))

    # Close data connection
    data.close()

except Exception as e:
    st.error(t("page-dashboard-error-loading", error=str(e)))
    st.exception(e)

# Refresh button
st.markdown("---")
if st.button(t("page-dashboard-refresh-button"), type="secondary"):
    st.cache_data.clear()
    st.rerun()
