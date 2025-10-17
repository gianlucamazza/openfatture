"""Payment tracking and reconciliation page.

Manage bank accounts, import statements, and reconcile payments through web interface.
"""

import pandas as pd
import streamlit as st

from openfatture.web.services.payment_service import StreamlitPaymentService

st.set_page_config(page_title="Pagamenti - OpenFatture", page_icon="💰", layout="wide")

# Title
st.title("💰 Tracking & Riconciliazione Pagamenti")

# Initialize service
payment_service = StreamlitPaymentService()

# Sidebar filters and actions
st.sidebar.subheader("🔍 Filtri")

# Account filter
accounts = payment_service.get_bank_accounts()
if accounts:
    account_options = ["Tutti"] + [f"{acc['name']} ({acc['iban'][-4:]})" for acc in accounts]
    selected_account_display = st.sidebar.selectbox(
        "Conto Bancario",
        options=account_options,
        index=0,
    )

    # Extract account ID from selection
    selected_account_id = None
    if selected_account_display != "Tutti":
        for acc in accounts:
            if f"{acc['name']} ({acc['iban'][-4:]})" == selected_account_display:
                selected_account_id = acc["id"]
                break
else:
    selected_account_id = None
    st.sidebar.info("Nessun conto bancario configurato")

# Status filter
status_options = ["all", "unmatched", "matched", "ignored"]
status_labels = {
    "all": "Tutti",
    "unmatched": "Da Riconciliare",
    "matched": "Riconciliati",
    "ignored": "Ignorati",
}
selected_status = st.sidebar.selectbox(
    "Stato",
    options=list(status_labels.keys()),
    format_func=lambda x: status_labels[x],
    index=0,
)

# Action buttons
col_import, col_refresh = st.sidebar.columns(2)

with col_import:
    if st.button("📥 Import", use_container_width=True, help="Importa estratto conto"):
        st.session_state.show_import_form = True

with col_refresh:
    if st.button("🔄 Aggiorna", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Import form
if st.session_state.get("show_import_form", False):
    with st.expander("📥 Importa Estratto Conto", expanded=True):
        # Account selection
        if accounts:
            account_options = [""] + [f"{acc['name']} ({acc['iban'][-4:]})" for acc in accounts]
            selected_account_display = st.selectbox(
                "Seleziona conto bancario *",
                options=account_options,
                help="Scegli il conto dove importare le transazioni",
            )

            selected_account_id = None
            if selected_account_display:
                for acc in accounts:
                    if f"{acc['name']} ({acc['iban'][-4:]})" == selected_account_display:
                        selected_account_id = acc["id"]
                        break
        else:
            st.error("Nessun conto bancario configurato. Creane uno prima di importare.")
            selected_account_id = None

        # File upload
        uploaded_file = st.file_uploader(
            "Seleziona file estratto conto",
            type=["ofx", "qfx", "csv", "qif"],
            help="Supporta formati: OFX, QFX, CSV, QIF",
        )

        # Bank preset for CSV files
        bank_preset = None
        if uploaded_file and uploaded_file.name.lower().endswith(".csv"):
            bank_options = ["", "intesa", "unicredit", "revolut", "n26", "fineco", "bancoposta"]
            bank_preset = st.selectbox(
                "Banca (per CSV)",
                options=bank_options,
                help="Seleziona la banca per il parsing corretto del CSV",
            )

        # Import options
        col1, col2 = st.columns(2)
        with col1:
            auto_match = st.checkbox(
                "Auto-match pagamenti",
                value=True,
                help="Tenta automaticamente di abbinare le transazioni alle fatture",
            )
        with col2:
            confidence_threshold = st.slider(
                "Soglia confidenza", 0.5, 1.0, 0.85, help="Minima confidenza per auto-matching"
            )

        # Import button
        import_disabled = not (selected_account_id and uploaded_file)
        if st.button("🚀 Importa Transazioni", disabled=import_disabled, use_container_width=True):
            if not selected_account_id:
                st.error("Seleziona un conto bancario")
            elif not uploaded_file:
                st.error("Seleziona un file da importare")
            else:
                with st.spinner("Importando transazioni..."):
                    # Read file content
                    file_content = uploaded_file.read()

                    # Import via service
                    result = payment_service.import_bank_statement(
                        account_id=selected_account_id,
                        file_content=file_content,
                        filename=uploaded_file.name,
                        bank_preset=bank_preset,
                    )

                    if result["success"]:
                        st.success(f"✅ {result['message']}")

                        # Show details
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Transazioni Importate", result["transactions_imported"])
                        with col2:
                            st.metric("Errori", len(result.get("errors", [])))
                        with col3:
                            st.metric("Duplicati", result.get("duplicates", 0))

                        if result.get("format_detected"):
                            st.info(f"📄 Formato rilevato: {result['format_detected']}")

                        # Show errors if any
                        if result.get("errors"):
                            with st.expander("⚠️ Errori durante l'import", expanded=False):
                                for error in result["errors"]:
                                    st.write(f"• {error}")

                        # Clear cache and refresh
                        st.cache_data.clear()
                        st.success("🔄 Dati aggiornati!")

                    else:
                        st.error(f"❌ {result['message']}")
                        if result.get("errors"):
                            for error in result["errors"]:
                                st.write(f"• {error}")

        if st.button("❌ Chiudi"):
            st.session_state.show_import_form = False
            st.rerun()

# Main content
try:
    # Bank accounts overview
    if accounts:
        st.subheader("🏦 Conti Bancari")

        # Display accounts in a grid
        cols = st.columns(min(len(accounts), 3))
        for i, account in enumerate(accounts):
            with cols[i % len(cols)]:
                with st.container(border=True):
                    st.subheader(f"🏦 {account['name']}")
                    st.metric(
                        "Saldo Attuale",
                        f"€{account['current_balance']:,.2f}",
                        delta=f"€{account['current_balance'] - account['opening_balance']:,.2f}",
                    )
                    st.caption(f"IBAN: ...{account['iban'][-4:]}")
                    st.caption(f"Banca: {account['bank_name']}")

        st.markdown("---")

    # Payment statistics
    st.subheader("📊 Statistiche Pagamenti")
    stats = payment_service.get_payment_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Conti Bancari", stats["total_accounts"])

    with col2:
        st.metric("Transazioni Totali", stats["total_transactions"])

    with col3:
        st.metric("Saldo Totale", f"€{stats['total_balance']:,.2f}")

    with col4:
        matched_pct = (
            (stats["matched_transactions"] / stats["total_transactions"] * 100)
            if stats["total_transactions"] > 0
            else 0
        )
        st.metric("Riconciliati", f"{matched_pct:.1f}%")

    # Status distribution
    if stats["status_distribution"]:
        st.subheader("📈 Distribuzione per Stato")

        status_data = []
        for status, count in stats["status_distribution"].items():
            if count > 0:
                status_data.append(
                    {"Stato": status_labels.get(status, status), "Transazioni": count}
                )

        if status_data:
            status_df = pd.DataFrame(status_data)
            st.bar_chart(status_df.set_index("Stato"), height=200)

    st.markdown("---")

    # Transactions list
    st.subheader("📋 Transazioni")

    # Get transactions
    transactions = payment_service.get_transactions(
        account_id=selected_account_id,
        status_filter=selected_status if selected_status != "all" else None,
        limit=100,  # Limit for performance
    )

    if transactions:
        # Convert to DataFrame for display
        df = pd.DataFrame(transactions)

        # Rename columns for display
        column_names = {
            "id": "ID",
            "date": "Data",
            "amount": "Importo",
            "description": "Descrizione",
            "reference": "Riferimento",
            "status": "Stato",
            "matched_payment_id": "Fattura",
        }
        df_display = df.rename(columns=column_names)

        # Format columns
        df_display["Data"] = pd.to_datetime(df_display["Data"]).dt.strftime("%d/%m/%Y")
        df_display["Importo"] = df_display["Importo"].apply(lambda x: f"€{x:,.2f}")
        df_display["Stato"] = df_display["Stato"].apply(lambda x: status_labels.get(x, x))

        # Add action column
        df_display["Azioni"] = ""

        # Display transactions
        for idx, row in df_display.iterrows():
            (
                col_id,
                col_date,
                col_amount,
                col_desc,
                col_ref,
                col_status,
                col_invoice,
                col_actions,
            ) = st.columns([0.5, 1, 1, 2, 1, 1, 1, 1])

            with col_id:
                st.write(f"**{row['ID'][:8]}...**")  # Show first 8 chars of UUID

            with col_date:
                st.write(row["Data"])

            with col_amount:
                amount_color = (
                    "green"
                    if row["Importo"].startswith("€")
                    and float(row["Importo"].replace("€", "").replace(",", "")) > 0
                    else "red"
                )
                st.markdown(
                    f'<span style="color: {amount_color}">{row["Importo"]}</span>',
                    unsafe_allow_html=True,
                )

            with col_desc:
                # Truncate long descriptions
                desc = row["Descrizione"]
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                st.write(desc)

            with col_ref:
                st.write(row["Riferimento"] or "-")

            with col_status:
                status_color = {
                    "Da Riconciliare": "orange",
                    "Riconciliati": "green",
                    "Ignorati": "gray",
                }.get(row["Stato"], "blue")
                st.markdown(
                    f'<span style="color: {status_color}">●</span> {row["Stato"]}',
                    unsafe_allow_html=True,
                )

            with col_invoice:
                if pd.notna(row["Fattura"]) and row["Fattura"]:
                    st.write(f"✅ {row['Fattura']}")
                else:
                    st.write("-")

            with col_actions:
                tx_id = row["ID"]
                if st.button("👁️", key=f"view_{tx_id}", help="Visualizza dettagli"):
                    st.session_state.selected_transaction_id = tx_id
                    st.session_state.show_transaction_detail = True

                if row["Stato"] == "Da Riconciliare":
                    if st.button("🔗", key=f"match_{tx_id}", help="Riconcilia"):
                        st.session_state.selected_transaction_id = tx_id
                        st.session_state.show_match_form = True
                elif row["Stato"] in ["Riconciliati", "Abbinati"]:
                    st.write("✅")  # Already matched

            st.markdown("---")

        # Summary
        total_amount = df["amount"].sum()
        st.info(
            f"📊 **Totale visualizzato:** €{total_amount:,.2f} su {len(transactions)} transazioni"
        )

    else:
        if selected_account_id or selected_status != "all":
            st.info("🔍 Nessuna transazione trovata con i filtri selezionati")
        else:
            st.info("📭 Nessuna transazione presente")

            # Quick setup guide
            with st.expander("🚀 Come iniziare con i pagamenti", expanded=True):
                st.markdown(
                    """
                    ### Primi Passi

                    1. **Aggiungi un conto bancario**
                       ```bash
                       uv run openfatture payment account add "Conto Business" --iban IT123...
                       ```

                    2. **Importa un estratto conto**
                       ```bash
                       uv run openfatture payment import estratto.ofx --account 1
                       ```

                    3. **Riconcilia automaticamente**
                       ```bash
                       uv run openfatture payment match --auto-apply
                       ```

                    4. **Verifica riconciliazioni**
                       ```bash
                       uv run openfatture payment status
                       ```
                    """
                )

except Exception as e:
    st.error(f"❌ Errore nel caricamento dei pagamenti: {e}")
    st.info("💡 Verifica che il database sia inizializzato correttamente")

# Transaction detail modal
if st.session_state.get("show_transaction_detail", False):
    tx_id = st.session_state.get("selected_transaction_id")
    if tx_id:
        transaction = payment_service.get_transaction_detail(tx_id)
        if transaction:
            with st.expander(f"👁️ Dettagli Transazione {str(transaction.id)[:8]}...", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**ID:** {transaction.id}")
                    st.write(f"**Data:** {transaction.date.strftime('%d/%m/%Y')}")
                    st.write(f"**Importo:** €{transaction.amount:,.2f}")
                    st.write(f"**Descrizione:** {transaction.description}")

                with col2:
                    st.write(f"**Riferimento:** {transaction.reference or 'N/A'}")
                    st.write(f"**Controparte:** {transaction.counterparty or 'N/A'}")
                    st.write(f"**Stato:** {transaction.status.value}")
                    if transaction.match_confidence:
                        st.write(f"**Confidenza Match:** {transaction.match_confidence:.1%}")

                if transaction.matched_payment_id:
                    st.write(f"**Fattura Collegata:** {transaction.matched_payment_id}")

                if st.button("❌ Chiudi", key="close_detail"):
                    st.session_state.show_transaction_detail = False
                    st.rerun()
        else:
            st.error("Transazione non trovata")
            st.session_state.show_transaction_detail = False

# Match transaction modal
if st.session_state.get("show_match_form", False):
    tx_id = st.session_state.get("selected_transaction_id")
    if tx_id:
        transaction = payment_service.get_transaction_detail(tx_id)
        if transaction:
            with st.expander(
                f"🔗 Riconcilia Transazione €{transaction.amount:,.2f}", expanded=True
            ):
                # Transaction details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Data:** {transaction.date.strftime('%d/%m/%Y')}")
                    st.write(f"**Importo:** €{transaction.amount:,.2f}")
                    st.write(f"**Descrizione:** {transaction.description}")

                with col2:
                    st.write(f"**Riferimento:** {transaction.reference or 'N/A'}")
                    st.write(f"**Controparte:** {transaction.counterparty or 'N/A'}")
                    st.write(f"**Stato:** {transaction.status.value}")

                # Get potential matches
                potential_matches = payment_service.get_potential_matches(tx_id, limit=10)

                if potential_matches:
                    st.subheader("🎯 Abbinamenti Suggeriti")

                    # Display matches
                    for match in potential_matches:
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                            with col1:
                                st.write(f"**{match['numero']}/{match['anno']}**")
                                st.write(f"Cliente: {match['cliente']}")
                                st.write(f"€{match['totale']:,.2f}")

                            with col2:
                                confidence = match.get("confidence", 0)
                                st.metric("Confidenza", f"{confidence:.1%}")

                            with col3:
                                days_diff = match.get("days_difference", 0)
                                st.write(f"±{abs(days_diff)} giorni")

                            with col4:
                                amount_diff = match.get("amount_difference", 0)
                                color = "green" if abs(amount_diff) < 0.01 else "orange"
                                st.markdown(
                                    f"<span style='color:{color}'>€{amount_diff:+,.2f}</span>",
                                    unsafe_allow_html=True,
                                )

                            # Match button
                            match_key = f"match_{tx_id}_{match['id']}"
                            if st.button("✅ Abbina", key=match_key, use_container_width=True):
                                with st.spinner("Abbinando transazione..."):
                                    result = payment_service.match_transaction(tx_id, match["id"])
                                    if result["success"]:
                                        st.success(
                                            f"✅ Transazione abbinata a fattura {match['numero']}"
                                        )
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Errore: {result['message']}")

                else:
                    st.info("🔍 Nessun abbinamento automatico trovato")

                # Manual match option
                st.divider()
                st.subheader("🔍 Ricerca Manuale")

                search_term = st.text_input(
                    "Cerca fattura",
                    placeholder="Numero fattura, cliente...",
                    help="Inserisci numero fattura o nome cliente",
                )

                if search_term:
                    manual_matches = payment_service.search_invoices_for_matching(
                        search_term, transaction.amount, limit=5
                    )

                    if manual_matches:
                        st.write("Risultati ricerca:")
                        for match in manual_matches:
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(
                                    f"**{match['numero']}/{match['anno']}** - {match['cliente']}"
                                )
                            with col2:
                                st.write(f"€{match['totale']:,.2f}")
                            with col3:
                                match_key = f"manual_match_{tx_id}_{match['id']}"
                                if st.button("Abbina", key=match_key):
                                    with st.spinner("Abbinando..."):
                                        result = payment_service.match_transaction(
                                            tx_id, match["id"]
                                        )
                                        if result["success"]:
                                            st.success("✅ Abbinata!")
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {result['message']}")
                    else:
                        st.write("Nessuna fattura trovata")

                if st.button("❌ Chiudi", key="close_match"):
                    st.session_state.show_match_form = False
                    st.rerun()
        else:
            st.error("Transazione non trovata")
            st.session_state.show_match_form = False

# Quick stats
st.markdown("### 📊 Statistiche Pagamenti")

try:
    from openfatture.cli.ui.dashboard import DashboardData

    data = DashboardData()

    payment_stats = data.get_payment_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🔍 Non Abbinati", payment_stats["unmatched"])

    with col2:
        st.metric("✅ Abbinati", payment_stats["matched"])

    with col3:
        st.metric("⏭️ Ignorati", payment_stats["ignored"])

    with col4:
        total = sum(payment_stats.values())
        st.metric("📊 Totale", total)

    # Payment due
    st.markdown("---")
    st.markdown("### 💳 Scadenze Prossimi 30 Giorni")

    payment_due = data.get_payment_due_summary(window_days=30, max_upcoming=10)

    if payment_due.overdue or payment_due.due_soon or payment_due.upcoming:
        import pandas as pd

        all_entries = payment_due.overdue + payment_due.due_soon + payment_due.upcoming

        df = pd.DataFrame(
            [
                {
                    "Fattura": e.invoice_ref,
                    "Cliente": e.client_name[:30],
                    "Scadenza": e.due_date.strftime("%d/%m/%Y"),
                    "Residuo": f"€{float(e.residual):,.2f}",
                    "Stato": e.status.value.replace("_", " ").title(),
                }
                for e in all_entries
            ]
        )

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.metric("💸 Totale Residuo", f"€{float(payment_due.total_outstanding):,.2f}")
    else:
        st.success("✅ Nessun pagamento in scadenza")

    data.close()

except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
