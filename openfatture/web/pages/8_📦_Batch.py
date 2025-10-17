"""Batch operations page.

Import/export operations for bulk data management.
"""

import streamlit as st

from openfatture.web.services.batch_service import StreamlitBatchService

st.set_page_config(page_title="Batch Operations - OpenFatture", page_icon="📦", layout="wide")

# Title
st.title("📦 Operazioni Batch")
st.markdown("### Import/Export massivi di dati")

# Initialize service
batch_service = StreamlitBatchService()

# Tabs for different operations
tab_import, tab_export, tab_history = st.tabs(["📥 Import", "📤 Export", "📋 Cronologia"])

with tab_import:
    st.subheader("📥 Import Dati")

    # Import type selection
    import_type = st.radio(
        "Tipo di dati da importare:",
        ["Clienti", "Fatture"],
        horizontal=True,
        help="Seleziona il tipo di dati da importare",
    )

    # File upload
    uploaded_file = st.file_uploader(
        f"Carica file CSV per {import_type.lower()}",
        type=["csv"],
        help=f"Il file CSV deve contenere i dati dei {import_type.lower()}",
    )

    if uploaded_file is not None:
        # Read file content
        csv_content = uploaded_file.getvalue().decode("utf-8")

        # Validate CSV format
        validation = batch_service.validate_csv_format(csv_content, import_type.lower())

        if validation["valid"]:
            st.success(f"✅ File valido! {validation['row_count']} righe rilevate")

            # Show preview
            with st.expander("👁️ Anteprima dati", expanded=True):
                lines = csv_content.split("\n")[:6]  # First 5 lines + header
                st.code("\n".join(lines), language="csv")

            # Import options
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔍 Convalida Solo", type="secondary", use_container_width=True):
                    if import_type == "Clienti":
                        result = batch_service.import_clients_from_csv(csv_content)
                        result["processed"] = 0  # Dry run
                        result["created"] = 0
                        result["updated"] = 0
                    else:
                        result = batch_service.import_invoices_from_csv(csv_content)

                    if result["success"]:
                        st.success("✅ Convalida completata senza errori")
                    else:
                        st.error("❌ Errori di convalida:")
                        for error in result["errors"][:5]:  # Show first 5 errors
                            st.write(f"• {error}")

            with col2:
                confirm_import = st.button(
                    f"📥 Importa {import_type}", type="primary", use_container_width=True
                )

            if confirm_import:
                with st.spinner(f"Importando {import_type.lower()}..."):
                    if import_type == "Clienti":
                        result = batch_service.import_clients_from_csv(csv_content)
                    else:
                        result = batch_service.import_invoices_from_csv(csv_content)

                # Show results
                if result["success"]:
                    st.success("✅ Import completato con successo!")

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Processati", result["processed"])
                    with col_b:
                        st.metric("Creati", result["created"])
                    with col_c:
                        st.metric("Aggiornati", result["updated"])

                    if result["errors"]:
                        with st.expander("⚠️ Errori minori", expanded=False):
                            for error in result["errors"]:
                                st.write(f"• {error}")

                else:
                    st.error("❌ Import fallito")
                    for error in result["errors"]:
                        st.error(error)

        else:
            st.error("❌ File CSV non valido:")
            for error in validation["errors"]:
                st.error(f"• {error}")

    # Template download
    st.markdown("---")
    st.subheader("📋 Template CSV")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Scarica Template Clienti", use_container_width=True):
            template = """denominazione,partita_iva,codice_fiscale,codice_destinatario,pec,indirizzo,cap,comune,provincia,telefono,email,note
"Azienda SRL","12345678901","RSSMRA80A01H501U","ABC1234","cliente@pec.it","Via Roma 123","00100","Roma","RM","+39 123 456 789","cliente@email.com","Note cliente"
"""
            st.download_button(
                label="Scarica CSV",
                data=template,
                file_name="template_clienti.csv",
                mime="text/csv",
            )

    with col2:
        if st.button("📥 Scarica Template Fatture", use_container_width=True):
            template = """numero,anno,data_emissione,cliente,descrizione,quantita,prezzo_unitario,aliquota_iva
"001","2024","2024-01-15","Azienda SRL","Consulenza web","1","500.00","22.00"
"""
            st.download_button(
                label="Scarica CSV",
                data=template,
                file_name="template_fatture.csv",
                mime="text/csv",
            )

with tab_export:
    st.subheader("📤 Export Dati")

    # Export type selection
    export_type = st.radio("Tipo di dati da esportare:", ["Clienti", "Fatture"], horizontal=True)

    # Export options
    filters = {}
    include_lines = False
    export_year = "Tutti"

    if export_type == "Fatture":
        col1, col2 = st.columns(2)

        with col1:
            export_year = st.selectbox(
                "Anno (opzionale)", ["Tutti"] + list(range(2020, 2026)), index=0
            )

        with col2:
            include_lines = st.checkbox(
                "Includi righe fattura", help="Esporta ogni riga fattura separatamente"
            )

        if export_year != "Tutti":
            filters["anno"] = export_year

    # Export button
    if st.button(f"📤 Esporta {export_type}", type="primary", use_container_width=True):
        with st.spinner(f"Esportando {export_type.lower()}..."):
            if export_type == "Clienti":
                success, csv_data, error = batch_service.export_clients_to_csv()
            else:
                success, csv_data, error = batch_service.export_invoices_to_csv(
                    filters=filters if export_type == "Fatture" else None,
                    include_lines=include_lines if export_type == "Fatture" else False,
                )

        if success:
            st.success("✅ Export completato!")

            # Show preview
            lines = csv_data.split("\n")[:6]
            with st.expander("👁️ Anteprima", expanded=True):
                st.code("\n".join(lines), language="csv")

            # Download button
            st.download_button(
                label=f"📥 Scarica {export_type}.csv",
                data=csv_data,
                file_name=f"{export_type.lower()}_{export_year if export_type == 'Fatture' and export_year != 'Tutti' else 'tutti'}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        else:
            st.error(f"❌ Export fallito: {error}")

with tab_history:
    st.subheader("📋 Cronologia Operazioni Batch")

    # Get batch history
    history = batch_service.get_batch_history()

    if history:
        # Display history table
        for item in history:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                with col1:
                    st.write(f"**{item['operation']}**")
                    st.caption(item.get("timestamp", "N/A"))

                with col2:
                    st.write(f"📊 {item.get('records_processed', 0)} record")

                with col3:
                    status = item.get("status", "unknown")
                    if status == "success":
                        st.write("✅ Successo")
                    elif status == "partial":
                        st.write("⚠️ Parziale")
                    else:
                        st.write("❌ Fallito")

                with col4:
                    if st.button("👁️", key=f"history_{item.get('id', 'unknown')}", help="Dettagli"):
                        st.write("Dettagli operazione:")
                        st.json(item)
    else:
        st.info("📭 Nessuna operazione batch registrata")

        # Info about CLI batch operations
        with st.expander("💡 Operazioni Batch Avanzate", expanded=False):
            st.markdown(
                """
                Per operazioni batch avanzate, utilizza la CLI:

                **Import:**
                ```bash
                # Import clienti
                uv run openfatture batch import-clients clienti.csv

                # Import fatture
                uv run openfatture batch import-invoices fatture.csv
                ```

                **Export:**
                ```bash
                # Export fatture per anno
                uv run openfatture batch export-invoices --year 2024

                # Export clienti
                uv run openfatture batch export-clients
                ```

                **Validazione:**
                ```bash
                # Valida fatture senza salvare
                uv run openfatture batch validate-invoices fatture.csv
                ```
                """
            )

# Footer info
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    💡 <strong>Suggerimento:</strong> Per operazioni batch molto grandi, usa la CLI per prestazioni ottimali
    </div>
    """,
    unsafe_allow_html=True,
)
