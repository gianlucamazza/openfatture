"""Invoice management page.

List, view, and manage invoices through web interface.
"""

import pandas as pd
import streamlit as st

from openfatture.storage.database.models import StatoFattura
from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-invoices-title"), page_icon="🧾", layout="wide")

# Title
st.title(t("page-invoices-title"))

# Initialize service
invoice_service = StreamlitInvoiceService()

# Sidebar filters
st.sidebar.subheader(t("page-invoices-filter-title"))

# Year filter
available_years = invoice_service.get_available_years()
if available_years:
    selected_year = st.sidebar.selectbox(
        t("page-invoices-filter-year"),
        options=[t("page-invoices-filter-all")] + available_years,
        index=0,
    )
else:
    selected_year = t("page-invoices-filter-all")
    st.sidebar.info(t("page-invoices-no-invoices-in-db"))

# Status filter
status_options = [t("page-invoices-filter-all")] + [s.value for s in StatoFattura]
selected_status = st.sidebar.selectbox(
    t("page-invoices-filter-status"),
    options=status_options,
    index=0,
)

# Build filters
filters = {}
if selected_year != t("page-invoices-filter-all"):
    filters["anno"] = selected_year
if selected_status != t("page-invoices-filter-all"):
    filters["stato"] = selected_status

# Limit
limit = st.sidebar.number_input(
    t("page-invoices-filter-max-results"), min_value=10, max_value=1000, value=50, step=10
)

st.sidebar.markdown("---")

# Quick actions
st.sidebar.subheader(t("page-invoices-action-quick-title"))

if st.sidebar.button(t("page-invoices-action-new-invoice"), use_container_width=True):
    st.info(t("page-invoices-action-new-invoice-info"))

if st.sidebar.button(t("page-invoices-action-refresh"), use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Main content
st.markdown(t("page-invoices-list-title"))

try:
    # Get invoices
    invoices = invoice_service.get_invoices(filters=filters, limit=limit)

    if not invoices:
        st.info(t("page-invoices-no-invoices-found"))
    else:
        # Display stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(t("page-invoices-stats-count"), len(invoices))

        with col2:
            total_amount = sum(inv["totale"] for inv in invoices)
            st.metric(t("page-invoices-stats-total"), f"€{total_amount:,.2f}")

        with col3:
            # Count by status
            status_counts: dict[str, int] = {}
            for inv in invoices:
                status = inv["stato"]
                status_counts[status] = status_counts.get(status, 0) + 1

            st.metric(t("page-invoices-stats-statuses"), len(status_counts))

        with col4:
            avg_amount = total_amount / len(invoices) if invoices else 0
            st.metric(t("page-invoices-stats-average"), f"€{avg_amount:,.2f}")

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

        display_df.columns = [
            t("page-invoices-col-id"),
            t("page-invoices-col-number"),
            t("page-invoices-col-date"),
            t("page-invoices-col-client"),
            t("page-invoices-col-total-eur"),
            t("page-invoices-col-status"),
            t("page-invoices-col-lines"),
        ]

        # Format totale
        display_df[t("page-invoices-col-total-eur")] = display_df[
            t("page-invoices-col-total-eur")
        ].apply(lambda x: f"{x:,.2f}")

        # Display table with selection
        st.markdown(t("page-invoices-table-title"))

        # Use dataframe with column configuration
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                t("page-invoices-col-id"): st.column_config.NumberColumn(
                    t("page-invoices-col-id"), width="small"
                ),
                t("page-invoices-col-number"): st.column_config.TextColumn(
                    t("page-invoices-col-number"), width="small"
                ),
                t("page-invoices-col-date"): st.column_config.TextColumn(
                    t("page-invoices-col-date"), width="small"
                ),
                t("page-invoices-col-client"): st.column_config.TextColumn(
                    t("page-invoices-col-client"), width="large"
                ),
                t("page-invoices-col-total-eur"): st.column_config.TextColumn(
                    t("page-invoices-col-total-eur"), width="medium"
                ),
                t("page-invoices-col-status"): st.column_config.TextColumn(
                    t("page-invoices-col-status"), width="medium"
                ),
                t("page-invoices-col-lines"): st.column_config.NumberColumn(
                    t("page-invoices-col-lines"), width="small"
                ),
            },
        )

        # Invoice detail expander
        st.markdown("---")
        st.markdown(t("page-invoices-detail-title"))

        selected_id = st.number_input(
            t("page-invoices-detail-input-id"),
            min_value=1,
            value=invoices[0]["id"] if invoices else 1,
            step=1,
        )

        if st.button(t("page-invoices-detail-show-button"), type="primary"):
            fattura = invoice_service.get_invoice_detail(selected_id)

            if not fattura:
                st.error(t("page-invoices-detail-error-not-found", id=selected_id))
            else:
                st.success(
                    t("page-invoices-detail-success", number=fattura.numero, year=fattura.anno)
                )

                # Header info
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.metric(t("page-invoices-detail-number"), f"{fattura.numero}/{fattura.anno}")
                    st.metric(
                        t("page-invoices-detail-date"),
                        fattura.data_emissione.strftime("%d/%m/%Y"),
                    )

                with col_b:
                    st.metric(
                        t("page-invoices-detail-client"),
                        fattura.cliente.denominazione if fattura.cliente else "N/A",
                    )
                    st.metric(t("page-invoices-detail-type"), fattura.tipo_documento.value)

                with col_c:
                    st.metric(
                        t("page-invoices-detail-status"),
                        fattura.stato.value.replace("_", " ").title(),
                    )
                    if fattura.numero_sdi:
                        st.metric(t("page-invoices-detail-sdi-number"), fattura.numero_sdi)

                # Line items
                st.markdown(t("page-invoices-detail-lines-title"))

                if fattura.righe:
                    righe_df = pd.DataFrame(
                        [
                            {
                                t("page-invoices-detail-lines-col-num"): riga.numero_riga,
                                t("page-invoices-detail-lines-col-desc"): riga.descrizione,
                                t("page-invoices-detail-lines-col-qty"): float(riga.quantita),
                                t("page-invoices-detail-lines-col-price"): float(
                                    riga.prezzo_unitario
                                ),
                                t("page-invoices-detail-lines-col-vat"): float(riga.aliquota_iva),
                                t("page-invoices-detail-lines-col-total"): float(riga.totale),
                            }
                            for riga in fattura.righe
                        ]
                    )

                    st.dataframe(righe_df, use_container_width=True, hide_index=True)
                else:
                    st.warning(t("page-invoices-detail-lines-empty"))

                # Totals
                st.markdown(t("page-invoices-detail-totals-title"))

                totals_col1, totals_col2, totals_col3, totals_col4 = st.columns(4)

                with totals_col1:
                    st.metric(
                        t("page-invoices-detail-totals-taxable"),
                        f"€{float(fattura.imponibile):,.2f}",
                    )

                with totals_col2:
                    st.metric(t("page-invoices-detail-totals-vat"), f"€{float(fattura.iva):,.2f}")

                with totals_col3:
                    if fattura.ritenuta_acconto:
                        st.metric(
                            t("page-invoices-detail-totals-withholding"),
                            f"-€{float(fattura.ritenuta_acconto):,.2f}",
                        )
                    if fattura.importo_bollo:
                        st.metric(
                            t("page-invoices-detail-totals-stamp"),
                            f"€{float(fattura.importo_bollo):,.2f}",
                        )

                with totals_col4:
                    st.metric(
                        t("page-invoices-detail-totals-total"),
                        f"**€{float(fattura.totale):,.2f}**",
                    )

                # Files
                st.markdown(t("page-invoices-detail-files-title"))

                file_col1, file_col2 = st.columns(2)

                with file_col1:
                    if fattura.xml_path:
                        st.success(
                            t("page-invoices-detail-files-xml-exists", path=fattura.xml_path)
                        )
                    else:
                        st.info(t("page-invoices-detail-files-xml-missing"))

                with file_col2:
                    if fattura.pdf_path:
                        st.success(
                            t("page-invoices-detail-files-pdf-exists", path=fattura.pdf_path)
                        )
                    else:
                        st.info(t("page-invoices-detail-files-pdf-missing"))

                # Actions
                st.markdown(t("page-invoices-detail-actions-title"))

                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if st.button(
                        t("page-invoices-detail-actions-generate-xml"), use_container_width=True
                    ):
                        with st.spinner(t("page-invoices-detail-actions-generating-xml")):
                            xml_content, error = invoice_service.generate_xml(
                                fattura, validate=True
                            )

                            if error:
                                st.error(t("page-invoices-detail-actions-error", error=error))
                            else:
                                st.success(t("page-invoices-detail-actions-xml-success"))
                                st.code(xml_content[:500] + "...", language="xml")

                with action_col2:
                    st.button(
                        t("page-invoices-detail-actions-send-sdi"),
                        disabled=True,
                        use_container_width=True,
                    )
                    st.caption(t("page-invoices-detail-actions-cli-feature"))

                with action_col3:
                    st.button(
                        t("page-invoices-detail-actions-generate-pdf"),
                        disabled=True,
                        use_container_width=True,
                    )
                    st.caption(t("page-invoices-detail-actions-cli-feature"))

except Exception as e:
    st.error(t("page-invoices-error-loading", error=str(e)))
    st.exception(e)
