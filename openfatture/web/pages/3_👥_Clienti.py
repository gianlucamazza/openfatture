"""Client management page.

List, view, create, and manage clients through web interface.
"""

import pandas as pd
import streamlit as st

from openfatture.web.services.client_service import StreamlitClientService

st.set_page_config(page_title="Clienti - OpenFatture", page_icon="👥", layout="wide")

# Title
st.title("👥 Gestione Clienti")

# Initialize service
client_service = StreamlitClientService()

# Sidebar filters
st.sidebar.subheader("🔍 Filtri")

# Search
search_term = st.sidebar.text_input(
    "Cerca",
    placeholder="Denominazione, P.IVA, Codice Fiscale...",
    help="Cerca per denominazione, partita IVA o codice fiscale",
)

# Action buttons
col_add, col_refresh = st.sidebar.columns(2)

with col_add:
    if st.button("➕ Nuovo Cliente", use_container_width=True):
        st.session_state.show_add_client = True

with col_refresh:
    if st.button("🔄 Aggiorna", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Add client form (modal-like)
if st.session_state.get("show_add_client", False):
    with st.form("add_client_form"):
        st.subheader("➕ Nuovo Cliente")

        col1, col2 = st.columns(2)

        with col1:
            denominazione = st.text_input("Denominazione *", placeholder="Nome azienda o persona")
            partita_iva = st.text_input("Partita IVA", placeholder="12345678901")
            codice_fiscale = st.text_input("Codice Fiscale", placeholder="RSSMRA80A01H501U")

        with col2:
            codice_destinatario = st.text_input("Codice SDI", placeholder="ABC1234")
            pec = st.text_input("PEC", placeholder="cliente@pec.it")

        col3, col4 = st.columns(2)

        with col3:
            indirizzo = st.text_input("Indirizzo", placeholder="Via Roma 123")
            cap = st.text_input("CAP", placeholder="00100")
            telefono = st.text_input("Telefono", placeholder="+39 123 456 7890")

        with col4:
            comune = st.text_input("Comune", placeholder="Roma")
            provincia = st.text_input("Provincia", placeholder="RM", max_chars=2).upper()
            email = st.text_input("Email", placeholder="cliente@email.com")

        note = st.text_area("Note", placeholder="Note aggiuntive...", height=80)

        col_submit, col_cancel = st.columns([1, 1])

        with col_submit:
            submitted = st.form_submit_button(
                "💾 Salva Cliente", use_container_width=True, type="primary"
            )

        with col_cancel:
            if st.form_submit_button("❌ Annulla", use_container_width=True):
                st.session_state.show_add_client = False
                st.rerun()

        if submitted:
            if not denominazione.strip():
                st.error("La denominazione è obbligatoria")
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
                    st.success(f"✅ Cliente '{client.denominazione}' creato con successo!")
                    st.session_state.show_add_client = False
                    st.cache_data.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Errore nella creazione del cliente: {e}")

# Get clients data
try:
    clients_data = client_service.get_clients(search=search_term if search_term else None)

    if clients_data:
        # Convert to DataFrame for better display
        df = pd.DataFrame(clients_data)

        # Rename columns for display
        column_names = {
            "id": "ID",
            "denominazione": "Denominazione",
            "partita_iva": "P.IVA",
            "codice_fiscale": "Codice Fiscale",
            "codice_destinatario": "SDI",
            "pec": "PEC",
            "comune": "Comune",
            "provincia": "Prov.",
            "created_at": "Creato il",
        }
        df_display = df.rename(columns=column_names)

        # Format date
        if "Creato il" in df_display.columns:
            df_display["Creato il"] = pd.to_datetime(df_display["Creato il"]).dt.strftime(
                "%d/%m/%Y"
            )

        # Display stats
        st.subheader("📊 Statistiche")
        stats = client_service.get_client_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Totale Clienti", stats["total_clients"])
        with col2:
            st.metric("Con PEC", stats["clients_with_pec"])
        with col3:
            st.metric("Con SDI", stats["clients_with_sdi"])
        with col4:
            st.metric("Con P.IVA", stats["clients_with_piva"])

        st.markdown("---")

        # Clients table
        st.subheader("📋 Lista Clienti")

        # Add action column
        df_display["Azioni"] = ""

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
                st.write(f"**{row['ID']}**")

            with col_denom:
                st.write(row["Denominazione"])

            with col_piva:
                st.write(row["P.IVA"] or "-")

            with col_cf:
                st.write(row["Codice Fiscale"] or "-")

            with col_sdi:
                st.write(row["SDI"] or "-")

            with col_pec:
                if row["PEC"]:
                    st.write(f"📧 {row['PEC']}")
                else:
                    st.write("-")

            with col_comune:
                st.write(row["Comune"] or "-")

            with col_prov:
                st.write(row["Prov."] or "-")

            with col_created:
                st.write(row["Creato il"])

            with col_actions:
                client_id = int(row["ID"])
                if st.button("👁️", key=f"view_{client_id}", help="Visualizza dettagli"):
                    st.session_state.selected_client_id = client_id
                    st.session_state.show_client_detail = True

                if st.button("✏️", key=f"edit_{client_id}", help="Modifica"):
                    st.session_state.selected_client_id = client_id
                    st.session_state.show_edit_client = True

                if st.button("🗑️", key=f"delete_{client_id}", help="Elimina"):
                    st.session_state.selected_client_id = client_id
                    st.session_state.show_delete_confirm = True

            st.markdown("---")

    else:
        if search_term:
            st.info(f"🔍 Nessun cliente trovato per '{search_term}'")
        else:
            st.info("📝 Nessun cliente presente. Crea il primo cliente!")

            # Quick add form for empty state
            with st.expander("🚀 Crea il primo cliente", expanded=True):
                with st.form("quick_add_client"):
                    st.write("Compila i dati essenziali:")

                    quick_denom = st.text_input("Denominazione *", key="quick_denom")
                    quick_piva = st.text_input("Partita IVA", key="quick_piva")
                    quick_pec = st.text_input("PEC (opzionale)", key="quick_pec")

                    if st.form_submit_button("➕ Crea Cliente", type="primary"):
                        if not quick_denom.strip():
                            st.error("La denominazione è obbligatoria")
                        else:
                            try:
                                client_data = {
                                    "denominazione": quick_denom.strip(),
                                    "partita_iva": quick_piva.strip() if quick_piva else None,
                                    "pec": quick_pec.strip() if quick_pec else None,
                                }
                                client = client_service.create_client(client_data)
                                st.success(f"✅ Cliente '{client.denominazione}' creato!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Errore: {e}")

except Exception as e:
    st.error(f"❌ Errore nel caricamento dei clienti: {e}")
    st.info("💡 Verifica che il database sia inizializzato correttamente")

# Client detail modal
if st.session_state.get("show_client_detail", False):
    client_id = st.session_state.get("selected_client_id")
    if client_id:
        client = client_service.get_client_detail(client_id)
        if client:
            with st.expander(f"👁️ Dettagli Cliente: {client.denominazione}", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**ID:** {client.id}")
                    st.write(f"**Denominazione:** {client.denominazione}")
                    st.write(f"**P.IVA:** {client.partita_iva or 'N/A'}")
                    st.write(f"**Codice Fiscale:** {client.codice_fiscale or 'N/A'}")

                with col2:
                    st.write(f"**SDI:** {client.codice_destinatario or 'N/A'}")
                    st.write(f"**PEC:** {client.pec or 'N/A'}")
                    st.write(f"**Telefono:** {client.telefono or 'N/A'}")
                    st.write(f"**Email:** {client.email or 'N/A'}")

                if client.indirizzo:
                    st.write(f"**Indirizzo:** {client.indirizzo}")
                    if client.cap and client.comune:
                        st.write(
                            f"**Città:** {client.cap} {client.comune} ({client.provincia or ''})"
                        )

                if client.note:
                    st.write(f"**Note:** {client.note}")

                if st.button("❌ Chiudi", key="close_detail"):
                    st.session_state.show_client_detail = False
                    st.rerun()
        else:
            st.error("Cliente non trovato")
            st.session_state.show_client_detail = False

# Edit client modal
if st.session_state.get("show_edit_client", False):
    client_id = st.session_state.get("selected_client_id")
    if client_id:
        client = client_service.get_client_detail(client_id)
        if client:
            with st.expander(f"✏️ Modifica Cliente: {client.denominazione}", expanded=True):
                with st.form(f"edit_client_form_{client_id}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        denominazione = st.text_input("Denominazione *", value=client.denominazione)
                        partita_iva = st.text_input("Partita IVA", value=client.partita_iva or "")
                        codice_fiscale = st.text_input(
                            "Codice Fiscale", value=client.codice_fiscale or ""
                        )

                    with col2:
                        codice_destinatario = st.text_input(
                            "Codice SDI", value=client.codice_destinatario or ""
                        )
                        pec = st.text_input("PEC", value=client.pec or "")

                    col3, col4 = st.columns(2)

                    with col3:
                        indirizzo = st.text_input("Indirizzo", value=client.indirizzo or "")
                        cap = st.text_input("CAP", value=client.cap or "")
                        telefono = st.text_input("Telefono", value=client.telefono or "")

                    with col4:
                        comune = st.text_input("Comune", value=client.comune or "")
                        provincia = st.text_input(
                            "Provincia", value=client.provincia or "", max_chars=2
                        ).upper()
                        email = st.text_input("Email", value=client.email or "")

                    note = st.text_area("Note", value=client.note or "", height=80)

                    col_save, col_cancel = st.columns([1, 1])

                    with col_save:
                        saved = st.form_submit_button(
                            "💾 Salva Modifiche", use_container_width=True, type="primary"
                        )

                    with col_cancel:
                        if st.form_submit_button("❌ Annulla", use_container_width=True):
                            st.session_state.show_edit_client = False
                            st.rerun()

                    if saved:
                        if not denominazione.strip():
                            st.error("La denominazione è obbligatoria")
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
                                    client_id, client_data
                                )
                                if updated_client:
                                    st.success(
                                        f"✅ Cliente '{updated_client.denominazione}' aggiornato!"
                                    )
                                    st.session_state.show_edit_client = False
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Cliente non trovato")

                            except Exception as e:
                                st.error(f"❌ Errore nell'aggiornamento: {e}")
        else:
            st.error("Cliente non trovato")
            st.session_state.show_edit_client = False

# Delete confirmation modal
if st.session_state.get("show_delete_confirm", False):
    client_id = st.session_state.get("selected_client_id")
    if client_id:
        client = client_service.get_client_detail(client_id)
        if client:
            with st.expander(f"🗑️ Elimina Cliente: {client.denominazione}", expanded=True):
                st.warning(f"⚠️ Sei sicuro di voler eliminare il cliente '{client.denominazione}'?")
                st.write("Questa azione non può essere annullata.")

                col_yes, col_no = st.columns([1, 3])

                with col_yes:
                    if st.button("🗑️ Sì, Elimina", type="primary", use_container_width=True):
                        try:
                            deleted = client_service.delete_client(client_id)
                            if deleted:
                                st.success(f"✅ Cliente '{client.denominazione}' eliminato!")
                                st.session_state.show_delete_confirm = False
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Cliente non trovato")
                        except Exception as e:
                            st.error(f"❌ Errore nell'eliminazione: {e}")

                with col_no:
                    if st.button("❌ Annulla", use_container_width=True):
                        st.session_state.show_delete_confirm = False
                        st.rerun()
        else:
            st.error("Cliente non trovato")
            st.session_state.show_delete_confirm = False

# Quick preview using DashboardData
st.markdown("### 📊 Anteprima Rapida")

try:
    from openfatture.cli.ui.dashboard import DashboardData

    data = DashboardData()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("👥 Totale Clienti", data.get_total_clients())

    with col2:
        st.metric("📄 Totale Fatture", data.get_total_invoices())

    st.markdown("#### 👑 Top 5 Clienti")

    top_clients = data.get_top_clients(limit=5)

    if top_clients:
        import pandas as pd

        df = pd.DataFrame(top_clients, columns=["Cliente", "N. Fatture", "Fatturato Totale"])
        df["Fatturato Totale"] = df["Fatturato Totale"].apply(lambda x: f"€{float(x):,.2f}")

        st.dataframe(df, use_container_width=True, hide_index=True)

    data.close()

except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
