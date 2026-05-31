"""Batch operations page.

Import/export operations for bulk data management.
"""

import streamlit as st

from openfatture.i18n import t
from openfatture.web.services.batch_service import StreamlitBatchService

st.set_page_config(page_title=t("page-batch-page-title"), page_icon="", layout="wide")

# Title
st.title(t("page-batch-title"))
st.markdown(f"### {t('page-batch-subtitle')}")

# Initialize service
batch_service = StreamlitBatchService()

# Tabs for different operations
tab_import, tab_export, tab_history = st.tabs(
    [t("page-batch-tab-import"), t("page-batch-tab-export"), t("page-batch-tab-history")]
)

with tab_import:
    st.subheader(t("page-batch-import-title"))

    # Import type selection
    import_type = st.radio(
        t("page-batch-import-type-label"),
        [t("page-batch-import-type-clients"), t("page-batch-import-type-invoices")],
        horizontal=True,
        help=t("page-batch-import-type-help"),
    )

    # File upload
    uploaded_file = st.file_uploader(
        t("page-batch-import-upload-label", type=import_type.lower()),
        type=["csv"],
        help=t("page-batch-import-upload-help", type=import_type.lower()),
    )

    if uploaded_file is not None:
        # Read file content
        csv_content = uploaded_file.getvalue().decode("utf-8")

        # Validate CSV format
        validation = batch_service.validate_csv_format(csv_content, import_type.lower())

        if validation["valid"]:
            st.success(t("page-batch-import-valid-file", count=validation["row_count"]))

            # Show preview
            with st.expander(t("page-batch-import-preview"), expanded=True):
                lines = csv_content.split("\n")[:6]  # First 5 lines + header
                st.code("\n".join(lines), language="csv")

            # Import options
            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    t("page-batch-import-validate-only"), type="secondary", use_container_width=True
                ):
                    if import_type == t("page-batch-import-type-clients"):
                        result = batch_service.import_clients_from_csv(csv_content)
                        result["processed"] = 0  # Dry run
                        result["created"] = 0
                        result["updated"] = 0
                    else:
                        result = batch_service.import_invoices_from_csv(csv_content)

                    if result["success"]:
                        st.success(t("page-batch-import-validate-complete"))
                    else:
                        st.error(t("page-batch-import-validate-errors"))
                        for error in result["errors"][:5]:  # Show first 5 errors
                            st.write(f"• {error}")

            with col2:
                confirm_import = st.button(
                    t("page-batch-import-button", type=import_type),
                    type="primary",
                    use_container_width=True,
                )

            if confirm_import:
                with st.spinner(t("page-batch-import-importing", type=import_type.lower())):
                    if import_type == t("page-batch-import-type-clients"):
                        result = batch_service.import_clients_from_csv(csv_content)
                    else:
                        result = batch_service.import_invoices_from_csv(csv_content)

                # Show results
                if result["success"]:
                    st.success(t("page-batch-import-success"))

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric(t("page-batch-import-metric-processed"), result["processed"])
                    with col_b:
                        st.metric(t("page-batch-import-metric-created"), result["created"])
                    with col_c:
                        st.metric(t("page-batch-import-metric-updated"), result["updated"])

                    if result["errors"]:
                        with st.expander(t("page-batch-import-minor-errors"), expanded=False):
                            for error in result["errors"]:
                                st.write(f"• {error}")

                else:
                    st.error(t("page-batch-import-failed"))
                    for error in result["errors"]:
                        st.error(error)

        else:
            st.error(t("page-batch-import-invalid-file"))
            for error in validation["errors"]:
                st.error(f"• {error}")

    # Template download
    st.markdown("---")
    st.subheader(t("page-batch-import-template-title"))

    col1, col2 = st.columns(2)

    with col1:
        if st.button(t("page-batch-import-template-clients"), use_container_width=True):
            template = """denominazione,partita_iva,codice_fiscale,codice_destinatario,pec,indirizzo,cap,comune,provincia,telefono,email,note
"Azienda SRL","12345678901","RSSMRA80A01H501U","ABC1234","cliente@pec.it","Via Roma 123","00100","Roma","RM","+39 123 456 789","cliente@email.com","Note cliente"
"""
            st.download_button(
                label=t("page-batch-import-download-csv"),
                data=template,
                file_name="template_clienti.csv",
                mime="text/csv",
            )

    with col2:
        if st.button(t("page-batch-import-template-invoices"), use_container_width=True):
            template = """numero,anno,data_emissione,cliente,descrizione,quantita,prezzo_unitario,aliquota_iva
"001","2024","2024-01-15","Azienda SRL","Consulenza web","1","500.00","22.00"
"""
            st.download_button(
                label=t("page-batch-import-download-csv"),
                data=template,
                file_name="template_fatture.csv",
                mime="text/csv",
            )

with tab_export:
    st.subheader(t("page-batch-export-title"))

    # Export type selection
    export_type = st.radio(
        t("page-batch-export-type-label"),
        [t("page-batch-import-type-clients"), t("page-batch-import-type-invoices")],
        horizontal=True,
    )

    # Export options
    filters = {}
    include_lines = False
    export_year: str | int = t("page-batch-export-year-all")

    if export_type == t("page-batch-import-type-invoices"):
        col1, col2 = st.columns(2)

        with col1:
            export_year = st.selectbox(
                t("page-batch-export-year-label"),
                [t("page-batch-export-year-all")] + list(range(2020, 2026)),
                index=0,
            )

        with col2:
            include_lines = st.checkbox(
                t("page-batch-export-include-lines"), help=t("page-batch-export-include-lines-help")
            )

        if export_year != t("page-batch-export-year-all"):
            filters["anno"] = export_year

    # Export button
    if st.button(
        t("page-batch-export-button", type=export_type), type="primary", use_container_width=True
    ):
        with st.spinner(t("page-batch-export-exporting", type=export_type.lower())):
            if export_type == t("page-batch-import-type-clients"):
                success, csv_data, error = batch_service.export_clients_to_csv()
            else:
                success, csv_data, error = batch_service.export_invoices_to_csv(
                    filters=(
                        filters if export_type == t("page-batch-import-type-invoices") else None
                    ),
                    include_lines=(
                        include_lines
                        if export_type == t("page-batch-import-type-invoices")
                        else False
                    ),
                )

        if success:
            st.success(t("page-batch-export-success"))

            # Show preview
            lines = csv_data.split("\n")[:6]
            with st.expander(t("page-batch-export-preview"), expanded=True):
                st.code("\n".join(lines), language="csv")

            # Download button
            year_suffix = (
                export_year
                if export_type == t("page-batch-import-type-invoices")
                and export_year != t("page-batch-export-year-all")
                else "tutti"
            )
            st.download_button(
                label=t("page-batch-export-download", type=export_type),
                data=csv_data,
                file_name=f"{export_type.lower()}_{year_suffix}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        else:
            st.error(t("page-batch-export-failed", error=error))

with tab_history:
    st.subheader(t("page-batch-history-title"))

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
                    st.write(
                        t("page-batch-history-records", count=item.get("records_processed", 0))
                    )

                with col3:
                    status = item.get("status", "unknown")
                    if status == "success":
                        st.write(t("page-batch-history-status-success"))
                    elif status == "partial":
                        st.write(t("page-batch-history-status-partial"))
                    else:
                        st.write(t("page-batch-history-status-failed"))

                with col4:
                    if st.button(
                        t("page-batch-history-details"),
                        key=f"history_{item.get('id', 'unknown')}",
                        help=t("page-batch-history-details-title"),
                    ):
                        st.write(t("page-batch-history-details-title"))
                        st.json(item)
    else:
        st.info(t("page-batch-history-empty"))

        # Info about CLI batch operations
        with st.expander(t("page-batch-history-cli-title"), expanded=False):
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
    <strong>Suggerimento:</strong> Per operazioni batch molto grandi, usa la CLI per prestazioni ottimali
    </div>
    """,
    unsafe_allow_html=True,
)
