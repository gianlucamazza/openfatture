"""Client management page.

List, view, create, and manage clients through web interface.
"""

import pandas as pd
import streamlit as st

from openfatture.storage.database.models import Cliente
from openfatture.web.services.client_service import StreamlitClientService
from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-clients-title"), page_icon="", layout="wide")

# Title
st.title(t("page-clients-title"))

# Initialize service
client_service = StreamlitClientService()

# Sidebar filters
st.sidebar.subheader(t("page-clients-filter-title"))

# Search
search_term = st.sidebar.text_input(
    t("page-clients-filter-search"),
    placeholder=t("page-clients-filter-search-placeholder"),
    help=t("page-clients-filter-search-help"),
)

# Action buttons
col_add, col_refresh = st.sidebar.columns(2)

with col_add:
    if st.button(t("page-clients-action-new"), use_container_width=True):
        st.session_state.show_add_client = True

with col_refresh:
    if st.button(t("page-clients-action-refresh"), use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Add client form (modal-like)
if st.session_state.get("show_add_client", False):
    with st.form("add_client_form"):
        st.subheader(t("page-clients-form-add-title"))

        col1, col2 = st.columns(2)

        with col1:
            denominazione = st.text_input(
                t("page-clients-form-denominazione"),
                placeholder=t("page-clients-form-denominazione-placeholder"),
            )
            partita_iva = st.text_input(
                t("page-clients-form-piva"), placeholder=t("page-clients-form-piva-placeholder")
            )
            codice_fiscale = st.text_input(
                t("page-clients-form-cf"), placeholder=t("page-clients-form-cf-placeholder")
            )

        with col2:
            codice_destinatario = st.text_input(
                t("page-clients-form-sdi"), placeholder=t("page-clients-form-sdi-placeholder")
            )
            pec = st.text_input(
                t("page-clients-form-pec"), placeholder=t("page-clients-form-pec-placeholder")
            )

        col3, col4 = st.columns(2)

        with col3:
            indirizzo = st.text_input(
                t("page-clients-form-address"),
                placeholder=t("page-clients-form-address-placeholder"),
            )
            cap = st.text_input(
                t("page-clients-form-zip"), placeholder=t("page-clients-form-zip-placeholder")
            )
            telefono = st.text_input(
                t("page-clients-form-phone"), placeholder=t("page-clients-form-phone-placeholder")
            )

        with col4:
            comune = st.text_input(
                t("page-clients-form-city"), placeholder=t("page-clients-form-city-placeholder")
            )
            provincia = st.text_input(
                t("page-clients-form-province"),
                placeholder=t("page-clients-form-province-placeholder"),
                max_chars=2,
            ).upper()
            email = st.text_input(
                t("page-clients-form-email"), placeholder=t("page-clients-form-email-placeholder")
            )

        note = st.text_area(
            t("page-clients-form-notes"),
            placeholder=t("page-clients-form-notes-placeholder"),
            height=80,
        )

        col_submit, col_cancel = st.columns([1, 1])

        with col_submit:
            submitted = st.form_submit_button(
                t("page-clients-form-save"), use_container_width=True, type="primary"
            )

        with col_cancel:
            if st.form_submit_button(t("page-clients-form-cancel"), use_container_width=True):
                st.session_state.show_add_client = False
                st.rerun()

        if submitted:
            if not denominazione.strip():
                st.error(t("page-clients-error-denominazione-required"))
            else:
                try:
                    client_data = {
                        "denominazione": denominazione.strip(),
                        "partita_iva": partita_iva.strip() if partita_iva else None,
                        "codice_fiscale": codice_fiscale.strip() if codice_fiscale else None,
                        "codice_destinatario": (
                            codice_destinatario.strip() if codice_destinatario else None
                        ),
                        "pec": pec.strip() if pec else None,
                        "indirizzo": indirizzo.strip() if indirizzo else None,
                        "cap": cap.strip() if cap else None,
                        "comune": comune.strip() if comune else None,
                        "provincia": provincia.strip() if provincia else None,
                        "telefono": telefono.strip() if telefono else None,
                        "email": email.strip() if email else None,
                        "note": note.strip() if note else None,
                    }

                    client = client_service.create_client(client_data)
                    st.success(t("page-clients-success-created", name=client.denominazione))
                    st.session_state.show_add_client = False
                    st.cache_data.clear()
                    st.rerun()

                except Exception as e:
                    st.error(t("page-clients-error-create", error=str(e)))

# Get clients data
try:
    clients_data = client_service.get_clients(search=search_term if search_term else None)

    if clients_data:
        # Convert to DataFrame for better display
        df = pd.DataFrame(clients_data)

        # Rename columns for display
        column_names = {
            "id": t("page-clients-table-col-id"),
            "denominazione": t("page-clients-table-col-denominazione"),
            "partita_iva": t("page-clients-table-col-piva"),
            "codice_fiscale": t("page-clients-table-col-cf"),
            "codice_destinatario": t("page-clients-table-col-sdi"),
            "pec": t("page-clients-table-col-pec"),
            "comune": t("page-clients-table-col-comune"),
            "provincia": t("page-clients-table-col-provincia"),
            "created_at": t("page-clients-table-col-created"),
        }
        df_display = df.rename(columns=column_names)

        # Format date
        created_col = t("page-clients-table-col-created")
        if created_col in df_display.columns:
            df_display[created_col] = pd.to_datetime(df_display[created_col]).dt.strftime(
                "%d/%m/%Y"
            )

        # Display stats
        st.subheader(t("page-clients-stats-title"))
        stats = client_service.get_client_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(t("page-clients-stats-total"), stats["total_clients"])
        with col2:
            st.metric(t("page-clients-stats-with-pec"), stats["clients_with_pec"])
        with col3:
            st.metric(t("page-clients-stats-with-sdi"), stats["clients_with_sdi"])
        with col4:
            st.metric(t("page-clients-stats-with-piva"), stats["clients_with_piva"])

        st.markdown("---")

        # Clients table
        st.subheader(t("page-clients-list-title"))

        # Add action column
        df_display[t("page-clients-table-col-actions")] = ""

        # Display table with actions
        for idx, row in df_display.iterrows():
            (
                col_id,
                col_denom,
                col_piva,
                col_cf,
                col_sdi,
                col_pec,
                col_comune,
                col_prov,
                col_created,
                col_actions,
            ) = st.columns([0.5, 2, 1, 1.2, 0.8, 1.5, 1, 0.5, 1, 1])

            with col_id:
                st.write(f"**{row[t('page-clients-table-col-id')]}**")

            with col_denom:
                st.write(row[t("page-clients-table-col-denominazione")])

            with col_piva:
                st.write(row[t("page-clients-table-col-piva")] or "-")

            with col_cf:
                st.write(row[t("page-clients-table-col-cf")] or "-")

            with col_sdi:
                st.write(row[t("page-clients-table-col-sdi")] or "-")

            with col_pec:
                if row[t("page-clients-table-col-pec")]:
                    st.write(f"{row[t('page-clients-table-col-pec')]}")
                else:
                    st.write("-")

            with col_comune:
                st.write(row[t("page-clients-table-col-comune")] or "-")

            with col_prov:
                st.write(row[t("page-clients-table-col-provincia")] or "-")

            with col_created:
                st.write(row[t("page-clients-table-col-created")])

            with col_actions:
                client_id = int(row[t("page-clients-table-col-id")])
                if st.button("", key=f"view_{client_id}", help=t("page-clients-action-view")):
                    st.session_state.selected_client_id = client_id
                    st.session_state.show_client_detail = True

                if st.button("", key=f"edit_{client_id}", help=t("page-clients-action-edit")):
                    st.session_state.selected_client_id = client_id
                    st.session_state.show_edit_client = True

                if st.button("", key=f"delete_{client_id}", help=t("page-clients-action-delete")):
                    st.session_state.selected_client_id = client_id
                    st.session_state.show_delete_confirm = True

            st.markdown("---")

    else:
        if search_term:
            st.info(t("page-clients-no-results", term=search_term))
        else:
            st.info(t("page-clients-empty-state"))

            # Quick add form for empty state
            with st.expander(t("page-clients-quick-add-title"), expanded=True):
                with st.form("quick_add_client"):
                    st.write(t("page-clients-quick-add-description"))

                    quick_denom = st.text_input(
                        t("page-clients-form-denominazione"), key="quick_denom"
                    )
                    quick_piva = st.text_input(t("page-clients-form-piva"), key="quick_piva")
                    quick_pec = st.text_input(
                        t("page-clients-quick-add-pec-optional"), key="quick_pec"
                    )

                    if st.form_submit_button(t("page-clients-quick-add-button"), type="primary"):
                        if not quick_denom.strip():
                            st.error(t("page-clients-error-denominazione-required"))
                        else:
                            try:
                                client_data = {
                                    "denominazione": quick_denom.strip(),
                                    "partita_iva": quick_piva.strip() if quick_piva else None,
                                    "pec": quick_pec.strip() if quick_pec else None,
                                }
                                client = client_service.create_client(client_data)
                                st.success(
                                    t(
                                        "page-clients-success-quick-created",
                                        name=client.denominazione,
                                    )
                                )
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(t("page-clients-error-quick-create", error=str(e)))

except Exception as e:
    st.error(t("page-clients-error-loading", error=str(e)))
    st.info(t("page-clients-error-loading-hint"))

# Client detail modal
if st.session_state.get("show_client_detail", False):
    client_id_raw = st.session_state.get("selected_client_id")
    if client_id_raw and isinstance(client_id_raw, int):
        client_detail: Cliente | None = client_service.get_client_detail(client_id_raw)
        if client_detail:
            with st.expander(
                t("page-clients-detail-title", name=client_detail.denominazione), expanded=True
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**{t('page-clients-detail-id')}:** {client_detail.id}")
                    st.write(
                        f"**{t('page-clients-detail-denominazione')}:** {client_detail.denominazione}"
                    )
                    st.write(
                        f"**{t('page-clients-detail-piva')}:** {client_detail.partita_iva or t('page-clients-detail-na')}"
                    )
                    st.write(
                        f"**{t('page-clients-detail-cf')}:** {client_detail.codice_fiscale or t('page-clients-detail-na')}"
                    )

                with col2:
                    st.write(
                        f"**{t('page-clients-detail-sdi')}:** {client_detail.codice_destinatario or t('page-clients-detail-na')}"
                    )
                    st.write(
                        f"**{t('page-clients-detail-pec')}:** {client_detail.pec or t('page-clients-detail-na')}"
                    )
                    st.write(
                        f"**{t('page-clients-detail-phone')}:** {client_detail.telefono or t('page-clients-detail-na')}"
                    )
                    st.write(
                        f"**{t('page-clients-detail-email')}:** {client_detail.email or t('page-clients-detail-na')}"
                    )

                if client_detail.indirizzo:
                    st.write(f"**{t('page-clients-detail-address')}:** {client_detail.indirizzo}")
                    if client_detail.cap and client_detail.comune:
                        st.write(
                            f"**{t('page-clients-detail-city')}:** {client_detail.cap} {client_detail.comune} ({client_detail.provincia or ''})"
                        )

                if client_detail.note:
                    st.write(f"**{t('page-clients-detail-notes')}:** {client_detail.note}")

                if st.button(t("page-clients-detail-close"), key="close_detail"):
                    st.session_state.show_client_detail = False
                    st.rerun()
        else:
            st.error(t("page-clients-error-not-found"))
            st.session_state.show_client_detail = False

# Edit client modal
if st.session_state.get("show_edit_client", False):
    client_id_raw = st.session_state.get("selected_client_id")
    if client_id_raw and isinstance(client_id_raw, int):
        client_edit: Cliente | None = client_service.get_client_detail(client_id_raw)
        if client_edit:
            with st.expander(
                t("page-clients-edit-title", name=client_edit.denominazione), expanded=True
            ):
                with st.form(f"edit_client_form_{client_id_raw}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        denominazione = st.text_input(
                            t("page-clients-form-denominazione"), value=client_edit.denominazione
                        )
                        partita_iva = st.text_input(
                            t("page-clients-form-piva"), value=client_edit.partita_iva or ""
                        )
                        codice_fiscale = st.text_input(
                            t("page-clients-form-cf"), value=client_edit.codice_fiscale or ""
                        )

                    with col2:
                        codice_destinatario = st.text_input(
                            t("page-clients-form-sdi"), value=client_edit.codice_destinatario or ""
                        )
                        pec = st.text_input(t("page-clients-form-pec"), value=client_edit.pec or "")

                    col3, col4 = st.columns(2)

                    with col3:
                        indirizzo = st.text_input(
                            t("page-clients-form-address"), value=client_edit.indirizzo or ""
                        )
                        cap = st.text_input(t("page-clients-form-zip"), value=client_edit.cap or "")
                        telefono = st.text_input(
                            t("page-clients-form-phone"), value=client_edit.telefono or ""
                        )

                    with col4:
                        comune = st.text_input(
                            t("page-clients-form-city"), value=client_edit.comune or ""
                        )
                        provincia = st.text_input(
                            t("page-clients-form-province"),
                            value=client_edit.provincia or "",
                            max_chars=2,
                        ).upper()
                        email = st.text_input(
                            t("page-clients-form-email"), value=client_edit.email or ""
                        )

                    note = st.text_area(
                        t("page-clients-form-notes"), value=client_edit.note or "", height=80
                    )

                    col_save, col_cancel = st.columns([1, 1])

                    with col_save:
                        saved = st.form_submit_button(
                            t("page-clients-edit-save"), use_container_width=True, type="primary"
                        )

                    with col_cancel:
                        if st.form_submit_button(
                            t("page-clients-form-cancel"), use_container_width=True
                        ):
                            st.session_state.show_edit_client = False
                            st.rerun()

                    if saved:
                        if not denominazione.strip():
                            st.error(t("page-clients-error-denominazione-required"))
                        else:
                            try:
                                client_data = {
                                    "denominazione": denominazione.strip(),
                                    "partita_iva": partita_iva.strip() if partita_iva else None,
                                    "codice_fiscale": (
                                        codice_fiscale.strip() if codice_fiscale else None
                                    ),
                                    "codice_destinatario": (
                                        codice_destinatario.strip() if codice_destinatario else None
                                    ),
                                    "pec": pec.strip() if pec and pec.strip() else None,
                                    "indirizzo": indirizzo.strip() if indirizzo else None,
                                    "cap": cap.strip() if cap else None,
                                    "comune": comune.strip() if comune else None,
                                    "provincia": provincia.strip() if provincia else None,
                                    "telefono": telefono.strip() if telefono else None,
                                    "email": email.strip() if email else None,
                                    "note": note.strip() if note else None,
                                }

                                updated_client = client_service.update_client(
                                    client_id_raw, client_data
                                )
                                if updated_client:
                                    st.success(
                                        t(
                                            "page-clients-success-updated",
                                            name=updated_client.denominazione,
                                        )
                                    )
                                    st.session_state.show_edit_client = False
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(t("page-clients-error-not-found"))

                            except Exception as e:
                                st.error(t("page-clients-error-update", error=str(e)))
        else:
            st.error(t("page-clients-error-not-found"))
            st.session_state.show_edit_client = False

# Delete confirmation modal
if st.session_state.get("show_delete_confirm", False):
    client_id_raw = st.session_state.get("selected_client_id")
    if client_id_raw and isinstance(client_id_raw, int):
        client_delete: Cliente | None = client_service.get_client_detail(client_id_raw)
        if client_delete:
            with st.expander(
                t("page-clients-delete-title", name=client_delete.denominazione), expanded=True
            ):
                st.warning(t("page-clients-delete-confirm", name=client_delete.denominazione))
                st.write(t("page-clients-delete-warning"))

                col_yes, col_no = st.columns([1, 3])

                with col_yes:
                    if st.button(
                        t("page-clients-delete-yes"), type="primary", use_container_width=True
                    ):
                        try:
                            deleted = client_service.delete_client(client_id_raw)
                            if deleted:
                                st.success(
                                    t(
                                        "page-clients-success-deleted",
                                        name=client_delete.denominazione,
                                    )
                                )
                                st.session_state.show_delete_confirm = False
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(t("page-clients-error-not-found"))
                        except Exception as e:
                            st.error(t("page-clients-error-delete", error=str(e)))

                with col_no:
                    if st.button(t("page-clients-delete-no"), use_container_width=True):
                        st.session_state.show_delete_confirm = False
                        st.rerun()
        else:
            st.error(t("page-clients-error-not-found"))
            st.session_state.show_delete_confirm = False

# Quick preview using DashboardData
st.markdown(f"### {t('page-clients-preview-title')}")

try:
    from openfatture.cli.ui.dashboard import DashboardData

    data = DashboardData()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(t("page-clients-preview-total"), data.get_total_clients())

    with col2:
        st.metric(t("page-clients-preview-invoices"), data.get_total_invoices())

    st.markdown(f"#### {t('page-clients-preview-top5')}")

    top_clients = data.get_top_clients(limit=5)

    if top_clients:
        import pandas as pd

        df = pd.DataFrame(
            top_clients,
            columns=[
                t("page-clients-preview-col-client"),
                t("page-clients-preview-col-invoices"),
                t("page-clients-preview-col-revenue"),
            ],
        )
        df[t("page-clients-preview-col-revenue")] = df[t("page-clients-preview-col-revenue")].apply(
            lambda x: f"€{float(x):,.2f}"
        )

        st.dataframe(df, use_container_width=True, hide_index=True)

    data.close()

except Exception as e:
    st.error(t("page-clients-preview-error", error=str(e)))
