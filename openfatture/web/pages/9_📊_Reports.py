"""Reports and analytics page.

Generate various business reports and analytics.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from openfatture.web.services.report_service import StreamlitReportService

st.set_page_config(page_title="Reports - OpenFatture", page_icon="📊", layout="wide")

# Title
st.title("📊 Reports & Analytics")
st.markdown("### Report aziendali e analisi avanzate")

# Initialize service
report_service = StreamlitReportService()

# Get available years
available_years = report_service.get_available_years()
if not available_years:
    st.warning("⚠️ Nessun dato disponibile per i report")
    st.info("Crea alcune fatture per vedere i report")
    st.stop()

# Sidebar controls
st.sidebar.subheader("🔍 Parametri Report")

selected_year = st.sidebar.selectbox(
    "Anno", options=available_years, index=0 if available_years else None
)

report_quarter = st.sidebar.selectbox(
    "Trimestre (opzionale)", options=["Tutti"] + ["Q1", "Q2", "Q3", "Q4"], index=0
)

quarter = None if report_quarter == "Tutti" else report_quarter

# Report tabs
tab_revenue, tab_vat, tab_clients = st.tabs(["💰 Fatturato", "📋 IVA", "👥 Clienti"])

with tab_revenue:
    st.subheader("💰 Report Fatturato")

    # Generate revenue report
    revenue_data = report_service.get_revenue_report(selected_year, quarter)

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Fatturato Totale",
            f"€{revenue_data['total_revenue']:,.2f}",
            help=f"Periodo: {revenue_data['period']}",
        )

    with col2:
        st.metric("IVA Totale", f"€{revenue_data['total_vat']:,.2f}")

    with col3:
        st.metric("Fatture Emesse", revenue_data["total_invoices"])

    with col4:
        st.metric("Valore Medio Fattura", f"€{revenue_data['avg_invoice_value']:,.2f}")

    # Monthly chart
    if revenue_data["monthly_breakdown"]:
        st.subheader("📈 Andamento Mensile")

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
                title="Fatturato Mensile",
                labels={"x": "Mese", "y": "Fatturato (€)"},
                color=revenues,
                color_continuous_scale="Blues",
            )
            fig_revenue.update_layout(height=400)
            st.plotly_chart(fig_revenue, use_container_width=True)

            # Invoice count chart
            fig_count = px.line(
                x=months,
                y=invoice_counts,
                title="Numero Fatture Mensili",
                labels={"x": "Mese", "y": "Numero Fatture"},
                markers=True,
            )
            fig_count.update_layout(height=300)
            st.plotly_chart(fig_count, use_container_width=True)

with tab_vat:
    st.subheader("📋 Report IVA")

    # Generate VAT report
    vat_data = report_service.get_vat_report(selected_year, quarter)

    # Summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Imponibile Totale", f"€{vat_data['total_imponibile']:,.2f}")

    with col2:
        st.metric("IVA Totale", f"€{vat_data['total_iva']:,.2f}")

    with col3:
        st.metric("Fatturato Totale", f"€{vat_data['total_fatturato']:,.2f}")

    # VAT breakdown
    if vat_data["vat_breakdown"]:
        st.subheader("📊 Ripartizione per Aliquota IVA")

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
            title="Riparto Imponibile per Aliquota IVA",
            hole=0.4,
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

        # Detailed table
        st.subheader("📋 Dettaglio per Aliquota")

        vat_table_data = []
        for rate, data in vat_data["vat_breakdown"].items():
            vat_table_data.append(
                {
                    "Aliquota IVA": f"{rate}%",
                    "Imponibile": f"€{data['imponibile']:,.2f}",
                    "IVA": f"€{data['iva']:,.2f}",
                    "Totale": f"€{data['imponibile'] + data['iva']:,.2f}",
                }
            )

        if vat_table_data:
            df_vat = pd.DataFrame(vat_table_data)
            st.dataframe(df_vat, use_container_width=True, hide_index=True)

with tab_clients:
    st.subheader("👥 Report Clienti")

    # Generate client report
    client_data = report_service.get_client_report(selected_year)

    # Summary
    st.metric(
        "Clienti Attivi",
        client_data["total_clients"],
        help=f"Clienti con fatture emesse nel {selected_year}",
    )

    # Top clients
    if client_data["top_clients"]:
        st.subheader("🏆 Top Clienti per Fatturato")

        # Prepare data
        clients_list = []
        for name, data in client_data["top_clients"].items():
            clients_list.append(
                {
                    "Cliente": name,
                    "Fatture": data["invoices"],
                    "Totale": data["total"],
                    "Ultima Fattura": (
                        data["last_invoice"].strftime("%d/%m/%Y") if data["last_invoice"] else "N/A"
                    ),
                }
            )

        # Display as table
        df_clients = pd.DataFrame(clients_list)
        df_clients["Totale"] = df_clients["Totale"].apply(lambda x: f"€{x:,.2f}")

        st.dataframe(df_clients, use_container_width=True, hide_index=True)

        # Bar chart
        fig_clients = px.bar(
            df_clients.head(10),
            x="Cliente",
            y="Totale",
            title="Top 10 Clienti per Fatturato",
            labels={"Totale": "Fatturato (€)", "Cliente": "Cliente"},
            color="Totale",
            color_continuous_scale="Greens",
        )
        fig_clients.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_clients, use_container_width=True)

# Export options
st.markdown("---")
st.subheader("📤 Export Report")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Fatturato (CSV)", use_container_width=True):
        # Prepare CSV data
        csv_data = "Mese,Fatturato,Numero Fatture\n"
        for month, data in revenue_data["monthly_breakdown"].items():
            month_name = f"{month:02d}/{selected_year}"
            csv_data += f"{month_name},{data['revenue']:.2f},{data['invoices']}\n"

        st.download_button(
            label="Scarica CSV",
            data=csv_data,
            file_name=f"report_fatturato_{selected_year}.csv",
            mime="text/csv",
        )

with col2:
    if st.button("📋 Export IVA (CSV)", use_container_width=True):
        # Prepare CSV data
        csv_data = "Aliquota IVA,Imponibile,IVA,Totale\n"
        for rate, data in vat_data["vat_breakdown"].items():
            total = data["imponibile"] + data["iva"]
            csv_data += f"{rate}%,{data['imponibile']:.2f},{data['iva']:.2f},{total:.2f}\n"

        st.download_button(
            label="Scarica CSV",
            data=csv_data,
            file_name=f"report_iva_{selected_year}.csv",
            mime="text/csv",
        )

with col3:
    if st.button("👥 Export Clienti (CSV)", use_container_width=True):
        # Prepare CSV data
        csv_data = "Cliente,Fatture,Totale,Ultima Fattura\n"
        for name, data in client_data["top_clients"].items():
            total_str = f"{data['total']:.2f}"
            last_invoice_str = (
                data["last_invoice"].strftime("%d/%m/%Y") if data["last_invoice"] else "N/A"
            )
            csv_data += f'"{name}",{data["invoices"]},{total_str},{last_invoice_str}\n'

        st.download_button(
            label="Scarica CSV",
            data=csv_data,
            file_name=f"report_clienti_{selected_year}.csv",
            mime="text/csv",
        )

# Footer info
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    📊 <strong>Report aggiornati automaticamente</strong> • Dati basati su fatture consegnate o accettate
    </div>
    """,
    unsafe_allow_html=True,
)
