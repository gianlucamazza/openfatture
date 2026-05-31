"""Reports and analytics page.

Generate various business reports and analytics.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from openfatture.web.services.report_service import StreamlitReportService
from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-reports-page-title"), page_icon="📊", layout="wide")

# Title
st.title(t("page-reports-title"))
st.markdown(f"### {t('page-reports-subtitle')}")

# Initialize service
report_service = StreamlitReportService()

# Get available years
available_years = report_service.get_available_years()
if not available_years:
    st.warning(t("page-reports-no-data-warning"))
    st.info(t("page-reports-no-data-info"))
    st.stop()

# Sidebar controls
st.sidebar.subheader(t("page-reports-sidebar-title"))

selected_year = st.sidebar.selectbox(
    t("page-reports-year-label"), options=available_years, index=0 if available_years else None
)

report_quarter = st.sidebar.selectbox(
    t("page-reports-quarter-label"),
    options=[t("page-reports-all-label")] + ["Q1", "Q2", "Q3", "Q4"],
    index=0,
)

quarter = None if report_quarter == t("page-reports-all-label") else report_quarter

# Report tabs
tab_revenue, tab_vat, tab_clients = st.tabs(
    [t("page-reports-tab-revenue"), t("page-reports-tab-vat"), t("page-reports-tab-clients")]
)

with tab_revenue:
    st.subheader(t("page-reports-revenue-title"))

    # Generate revenue report
    revenue_data = report_service.get_revenue_report(selected_year, quarter)

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            t("page-reports-total-revenue"),
            f"€{revenue_data['total_revenue']:,.2f}",
            help=f"{t('page-reports-period-label')}: {revenue_data['period']}",
        )

    with col2:
        st.metric(t("page-reports-total-vat"), f"€{revenue_data['total_vat']:,.2f}")

    with col3:
        st.metric(t("page-reports-invoices-issued"), revenue_data["total_invoices"])

    with col4:
        st.metric(t("page-reports-avg-invoice-value"), f"€{revenue_data['avg_invoice_value']:,.2f}")

    # Monthly chart
    if revenue_data["monthly_breakdown"]:
        st.subheader(t("page-reports-monthly-trend"))

        # Prepare data for chart
        months = []
        revenues = []
        invoice_counts = []

        for month in range(1, 13):
            if month in revenue_data["monthly_breakdown"]:
                month_name = f"{month:02d}/{selected_year}"
                months.append(month_name)
                revenues.append(revenue_data["monthly_breakdown"][month]["revenue"])
                invoice_counts.append(revenue_data["monthly_breakdown"][month]["invoices"])

        if months:
            # Revenue chart
            fig_revenue = px.bar(
                x=months,
                y=revenues,
                title=t("page-reports-monthly-revenue-chart"),
                labels={"x": t("page-reports-month-label"), "y": t("page-reports-revenue-label")},
                color=revenues,
                color_continuous_scale="Blues",
            )
            fig_revenue.update_layout(height=400)
            st.plotly_chart(fig_revenue, use_container_width=True)

            # Invoice count chart
            fig_count = px.line(
                x=months,
                y=invoice_counts,
                title=t("page-reports-monthly-invoices-chart"),
                labels={
                    "x": t("page-reports-month-label"),
                    "y": t("page-reports-invoice-count-label"),
                },
                markers=True,
            )
            fig_count.update_layout(height=300)
            st.plotly_chart(fig_count, use_container_width=True)

with tab_vat:
    st.subheader(t("page-reports-vat-title"))

    # Generate VAT report
    vat_data = report_service.get_vat_report(selected_year, quarter)

    # Summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(t("page-reports-total-taxable"), f"€{vat_data['total_imponibile']:,.2f}")

    with col2:
        st.metric(t("page-reports-total-vat"), f"€{vat_data['total_iva']:,.2f}")

    with col3:
        st.metric(t("page-reports-total-revenue"), f"€{vat_data['total_fatturato']:,.2f}")

    # VAT breakdown
    if vat_data["vat_breakdown"]:
        st.subheader(t("page-reports-vat-breakdown-title"))

        # Prepare data for pie chart
        labels = []
        imponibile_values = []
        iva_values = []

        for rate, data in vat_data["vat_breakdown"].items():
            labels.append(f"{rate}%")
            imponibile_values.append(data["imponibile"])
            iva_values.append(data["iva"])

        # Pie chart for imponibile
        fig_pie = px.pie(
            values=imponibile_values,
            names=labels,
            title=t("page-reports-vat-distribution-chart"),
            hole=0.4,
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

        # Detailed table
        st.subheader(t("page-reports-vat-detail-title"))

        vat_table_data = []
        for rate, data in vat_data["vat_breakdown"].items():
            vat_table_data.append(
                {
                    t("page-reports-vat-rate-label"): f"{rate}%",
                    t("page-reports-taxable-label"): f"€{data['imponibile']:,.2f}",
                    t("page-reports-vat-label"): f"€{data['iva']:,.2f}",
                    t("page-reports-total-label"): f"€{data['imponibile'] + data['iva']:,.2f}",
                }
            )

        if vat_table_data:
            df_vat = pd.DataFrame(vat_table_data)
            st.dataframe(df_vat, use_container_width=True, hide_index=True)

with tab_clients:
    st.subheader(t("page-reports-clients-title"))

    # Generate client report
    client_data = report_service.get_client_report(selected_year)

    # Summary
    st.metric(
        t("page-reports-active-clients"),
        client_data["total_clients"],
        help=f"{t('page-reports-clients-with-invoices')} {selected_year}",
    )

    # Top clients
    if client_data["top_clients"]:
        st.subheader(t("page-reports-top-clients-title"))

        # Prepare data
        clients_list = []
        for name, data in client_data["top_clients"].items():
            clients_list.append(
                {
                    t("page-reports-client-label"): name,
                    t("page-reports-invoices-label"): data["invoices"],
                    t("page-reports-total-label"): data["total"],
                    t("page-reports-last-invoice-label"): (
                        data["last_invoice"].strftime("%d/%m/%Y") if data["last_invoice"] else "N/A"
                    ),
                }
            )

        # Display as table
        df_clients = pd.DataFrame(clients_list)
        df_clients[t("page-reports-total-label")] = df_clients[t("page-reports-total-label")].apply(
            lambda x: f"€{x:,.2f}"
        )

        st.dataframe(df_clients, use_container_width=True, hide_index=True)

        # Bar chart
        fig_clients = px.bar(
            df_clients.head(10),
            x=t("page-reports-client-label"),
            y=t("page-reports-total-label"),
            title=t("page-reports-top-10-clients-chart"),
            labels={
                t("page-reports-total-label"): t("page-reports-revenue-label"),
                t("page-reports-client-label"): t("page-reports-client-label"),
            },
            color=t("page-reports-total-label"),
            color_continuous_scale="Greens",
        )
        fig_clients.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_clients, use_container_width=True)

# Export options
st.markdown("---")
st.subheader(t("page-reports-export-title"))

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(t("page-reports-export-revenue-btn"), use_container_width=True):
        # Prepare CSV data
        csv_data = f"{t('page-reports-month-label')},{t('page-reports-revenue-label')},{t('page-reports-invoice-count-label')}\n"
        for month, data in revenue_data["monthly_breakdown"].items():
            month_name = f"{month:02d}/{selected_year}"
            csv_data += f"{month_name},{data['revenue']:.2f},{data['invoices']}\n"

        st.download_button(
            label=t("page-reports-download-csv"),
            data=csv_data,
            file_name=f"report_fatturato_{selected_year}.csv",
            mime="text/csv",
        )

with col2:
    if st.button(t("page-reports-export-vat-btn"), use_container_width=True):
        # Prepare CSV data
        csv_data = f"{t('page-reports-vat-rate-label')},{t('page-reports-taxable-label')},{t('page-reports-vat-label')},{t('page-reports-total-label')}\n"
        for rate, data in vat_data["vat_breakdown"].items():
            total = data["imponibile"] + data["iva"]
            csv_data += f"{rate}%,{data['imponibile']:.2f},{data['iva']:.2f},{total:.2f}\n"

        st.download_button(
            label=t("page-reports-download-csv"),
            data=csv_data,
            file_name=f"report_iva_{selected_year}.csv",
            mime="text/csv",
        )

with col3:
    if st.button(t("page-reports-export-clients-btn"), use_container_width=True):
        # Prepare CSV data
        csv_data = f"{t('page-reports-client-label')},{t('page-reports-invoices-label')},{t('page-reports-total-label')},{t('page-reports-last-invoice-label')}\n"
        for name, data in client_data["top_clients"].items():
            total_str = f"{data['total']:.2f}"
            last_invoice_str = (
                data["last_invoice"].strftime("%d/%m/%Y") if data["last_invoice"] else "N/A"
            )
            csv_data += f'"{name}",{data["invoices"]},{total_str},{last_invoice_str}\n'

        st.download_button(
            label=t("page-reports-download-csv"),
            data=csv_data,
            file_name=f"report_clienti_{selected_year}.csv",
            mime="text/csv",
        )

# Footer info
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    {t("page-reports-footer-info")}
    </div>
    """,
    unsafe_allow_html=True,
)
