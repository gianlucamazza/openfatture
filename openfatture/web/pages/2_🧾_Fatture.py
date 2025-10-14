"""Invoice management page.

List, view, and manage invoices through web interface.
"""

import streamlit as st
import pandas as pd
from datetime import date

from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.storage.database.models import StatoFattura

st.set_page_config(page_title="Fatture - OpenFatture", page_icon="🧾", layout="wide")

# Title
st.title("🧾 Gestione Fatture")

# Initialize service
invoice_service = StreamlitInvoiceService()

# Sidebar filters
st.sidebar.subheader("🔍 Filtri")

# Year filter
available_years = invoice_service.get_available_years()
if available_years:
    selected_year = st.sidebar.selectbox(
        "Anno",
        options=["Tutti"] + available_years,
        index=0,
    )
else:
    selected_year = "Tutti"
    st.sidebar.info("Nessuna fattura presente")

# Status filter
status_options = ["Tutti"] + [s.value for s in StatoFattura]
selected_status = st.sidebar.selectbox(
    "Stato",
    options=status_options,
    index=0,
)

# Build filters
filters = {}
if selected_year != "Tutti":
    filters["anno"] = selected_year
if selected_status != "Tutti":
    filters["stato"] = selected_status

# Limit
limit = st.sidebar.number_input("Risultati massimi", min_value=10, max_value=1000, value=50, step=10)

st.sidebar.markdown("---")

# Quick actions
st.sidebar.subheader("⚡ Azioni Rapide")

if st.sidebar.button("➕ Nuova Fattura", use_container_width=True):
    st.info(
        """
        **Feature in sviluppo**

        Per ora, crea fatture tramite CLI:
        ```bash
        uv run openfatture fattura crea
        ```

        La creazione guidata Web UI sarà disponibile a breve!
        """
    )

if st.sidebar.button("🔄 Aggiorna Lista", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Main content
st.markdown("### 📋 Lista Fatture")

try:
    # Get invoices
    invoices = invoice_service.get_invoices(filters=filters, limit=limit)

    if not invoices:
        st.info("📭 Nessuna fattura trovata con i filtri selezionati")
    else:
        # Display stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Fatture Trovate", len(invoices))

        with col2:
            total_amount = sum(inv["totale"] for inv in invoices)
            st.metric("💰 Totale", f"€{total_amount:,.2f}")

        with col3:
            # Count by status
            status_counts = {}
            for inv in invoices:
                status = inv["stato"]
                status_counts[status] = status_counts.get(status, 0) + 1

            st.metric("📋 Stati Diversi", len(status_counts))

        with col4:
            avg_amount = total_amount / len(invoices) if invoices else 0
            st.metric("📈 Importo Medio", f"€{avg_amount:,.2f}")

        st.markdown("---")

        # Convert to DataFrame for display
        df = pd.DataFrame(invoices)

        # Format columns
        df["data_emissione"] = pd.to_datetime(df["data_emissione"]).dt.strftime("%d/%m/%Y")
        df["numero_completo"] = df["numero"] + "/" + df["anno"].astype(str)

        # Status emoji mapping
        status_emoji = {
            "bozza": "📝",
            "da_inviare": "📤",
            "inviata": "✉️",
            "accettata": "✅",
            "consegnata": "✅",
            "rifiutata": "❌",
            "scartata": "❌",
            "errore": "⚠️",
        }

        df["stato_display"] = df["stato"].apply(
            lambda x: f"{status_emoji.get(x, '📄')} {x.replace('_', ' ').title()}"
        )

        # Reorder and rename columns for display
        display_df = df[
            [
                "id",
                "numero_completo",
                "data_emissione",
                "cliente_denominazione",
                "totale",
                "stato_display",
                "num_righe",
            ]
        ].copy()

        display_df.columns = ["ID", "Numero", "Data", "Cliente", "Totale €", "Stato", "Righe"]

        # Format totale
        display_df["Totale €"] = display_df["Totale €"].apply(lambda x: f"{x:,.2f}")

        # Display table with selection
        st.markdown("#### 📋 Tabella Fatture")

        # Use dataframe with column configuration
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Numero": st.column_config.TextColumn("Numero", width="small"),
                "Data": st.column_config.TextColumn("Data", width="small"),
                "Cliente": st.column_config.TextColumn("Cliente", width="large"),
                "Totale €": st.column_config.TextColumn("Totale €", width="medium"),
                "Stato": st.column_config.TextColumn("Stato", width="medium"),
                "Righe": st.column_config.NumberColumn("Righe", width="small"),
            },
        )

        # Invoice detail expander
        st.markdown("---")
        st.markdown("### 🔍 Dettaglio Fattura")

        selected_id = st.number_input(
            "Inserisci ID fattura da visualizzare",
            min_value=1,
            value=invoices[0]["id"] if invoices else 1,
            step=1,
        )

        if st.button("📄 Mostra Dettaglio", type="primary"):
            fattura = invoice_service.get_invoice_detail(selected_id)

            if not fattura:
                st.error(f"❌ Fattura con ID {selected_id} non trovata")
            else:
                st.success(f"✅ Fattura {fattura.numero}/{fattura.anno}")

                # Header info
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.metric("Numero", f"{fattura.numero}/{fattura.anno}")
                    st.metric("Data Emissione", fattura.data_emissione.strftime("%d/%m/%Y"))

                with col_b:
                    st.metric(
                        "Cliente",
                        fattura.cliente.denominazione if fattura.cliente else "N/A",
                    )
                    st.metric("Tipo", fattura.tipo_documento.value)

                with col_c:
                    st.metric("Stato", fattura.stato.value.replace("_", " ").title())
                    if fattura.numero_sdi:
                        st.metric("Numero SDI", fattura.numero_sdi)

                # Line items
                st.markdown("#### 📦 Righe Fattura")

                if fattura.righe:
                    righe_df = pd.DataFrame(
                        [
                            {
                                "#": riga.numero_riga,
                                "Descrizione": riga.descrizione,
                                "Quantità": float(riga.quantita),
                                "Prezzo €": float(riga.prezzo_unitario),
                                "IVA %": float(riga.aliquota_iva),
                                "Totale €": float(riga.totale),
                            }
                            for riga in fattura.righe
                        ]
                    )

                    st.dataframe(righe_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nessuna riga presente")

                # Totals
                st.markdown("#### 💰 Totali")

                totals_col1, totals_col2, totals_col3, totals_col4 = st.columns(4)

                with totals_col1:
                    st.metric("Imponibile", f"€{float(fattura.imponibile):,.2f}")

                with totals_col2:
                    st.metric("IVA", f"€{float(fattura.iva):,.2f}")

                with totals_col3:
                    if fattura.ritenuta_acconto:
                        st.metric(
                            "Ritenuta",
                            f"-€{float(fattura.ritenuta_acconto):,.2f}",
                        )
                    if fattura.importo_bollo:
                        st.metric("Bollo", f"€{float(fattura.importo_bollo):,.2f}")

                with totals_col4:
                    st.metric(
                        "**TOTALE**",
                        f"**€{float(fattura.totale):,.2f}**",
                    )

                # Files
                st.markdown("#### 📁 File")

                file_col1, file_col2 = st.columns(2)

                with file_col1:
                    if fattura.xml_path:
                        st.success(f"✅ XML: `{fattura.xml_path}`")
                    else:
                        st.info("📄 XML non ancora generato")

                with file_col2:
                    if fattura.pdf_path:
                        st.success(f"✅ PDF: `{fattura.pdf_path}`")
                    else:
                        st.info("📄 PDF non ancora generato")

                # Actions
                st.markdown("#### ⚡ Azioni")

                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if st.button("📝 Genera XML", use_container_width=True):
                        with st.spinner("Generando XML..."):
                            xml_content, error = invoice_service.generate_xml(fattura, validate=True)

                            if error:
                                st.error(f"❌ Errore: {error}")
                            else:
                                st.success("✅ XML generato con successo!")
                                st.code(xml_content[:500] + "...", language="xml")

                with action_col2:
                    st.button("📤 Invia SDI", disabled=True, use_container_width=True)
                    st.caption("Feature CLI")

                with action_col3:
                    st.button("📄 Genera PDF", disabled=True, use_container_width=True)
                    st.caption("Feature CLI")

except Exception as e:
    st.error(f"❌ Errore caricamento fatture: {e}")
    st.exception(e)
