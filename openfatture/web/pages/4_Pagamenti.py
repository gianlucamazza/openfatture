"""Payment tracking and reconciliation page.

Manage bank accounts, import statements, and reconcile payments through web interface.
"""

import pandas as pd
import streamlit as st

from openfatture.i18n import get_translator
from openfatture.web.services.payment_service import StreamlitPaymentService

# Initialize translator
t = get_translator()

st.set_page_config(
    page_title=t("page-payments-page-title"),
    page_icon="",
    layout="wide",
)

# Title
st.title(t("page-payments-title"))

# Initialize service
payment_service = StreamlitPaymentService()

# Sidebar filters and actions
st.sidebar.subheader(t("page-payments-filter-title"))

# Account filter
accounts = payment_service.get_bank_accounts()
if accounts:
    account_options = [t("page-payments-filter-all-accounts")] + [
        f"{acc['name']} ({acc['iban'][-4:]})" for acc in accounts
    ]
    selected_account_display = st.sidebar.selectbox(
        t("page-payments-filter-bank-account"),
        options=account_options,
        index=0,
    )

    # Extract account ID from selection
    selected_account_id = None
    if selected_account_display != t("page-payments-filter-all-accounts"):
        for acc in accounts:
            if f"{acc['name']} ({acc['iban'][-4:]})" == selected_account_display:
                selected_account_id = acc["id"]
                break
else:
    selected_account_id = None
    st.sidebar.info(t("page-payments-no-accounts-configured"))

# Status filter
status_options = ["all", "unmatched", "matched", "ignored"]
status_labels = {
    "all": t("page-payments-status-all"),
    "unmatched": t("page-payments-status-unmatched"),
    "matched": t("page-payments-status-matched"),
    "ignored": t("page-payments-status-ignored"),
}
selected_status = st.sidebar.selectbox(
    t("page-payments-filter-status"),
    options=list(status_labels.keys()),
    format_func=lambda x: status_labels[x],
    index=0,
)

# Action buttons
col_import, col_refresh = st.sidebar.columns(2)

with col_import:
    if st.button(
        t("page-payments-action-import"),
        use_container_width=True,
        help=t("page-payments-action-import-help"),
    ):
        st.session_state.show_import_form = True

with col_refresh:
    if st.button(t("page-payments-action-refresh"), use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Import form
if st.session_state.get("show_import_form", False):
    with st.expander(t("page-payments-import-title"), expanded=True):
        # Account selection
        if accounts:
            account_options = [""] + [f"{acc['name']} ({acc['iban'][-4:]})" for acc in accounts]
            selected_account_display = st.selectbox(
                t("page-payments-import-select-account"),
                options=account_options,
                help=t("page-payments-import-select-account-help"),
            )

            selected_account_id = None
            if selected_account_display:
                for acc in accounts:
                    if f"{acc['name']} ({acc['iban'][-4:]})" == selected_account_display:
                        selected_account_id = acc["id"]
                        break
        else:
            st.error(t("page-payments-import-no-account-error"))
            selected_account_id = None

        # File upload
        uploaded_file = st.file_uploader(
            t("page-payments-import-file-label"),
            type=["ofx", "qfx", "csv", "qif"],
            help=t("page-payments-import-file-help"),
        )

        # Bank preset for CSV files
        bank_preset = None
        if uploaded_file and uploaded_file.name.lower().endswith(".csv"):
            bank_options = ["", "intesa", "unicredit", "revolut", "n26", "fineco", "bancoposta"]
            bank_preset = st.selectbox(
                t("page-payments-import-bank-preset"),
                options=bank_options,
                help=t("page-payments-import-bank-preset-help"),
            )

        # Import options
        col1, col2 = st.columns(2)
        with col1:
            auto_match = st.checkbox(
                t("page-payments-import-auto-match"),
                value=True,
                help=t("page-payments-import-auto-match-help"),
            )
        with col2:
            confidence_threshold = st.slider(
                t("page-payments-import-confidence"),
                0.5,
                1.0,
                0.85,
                help=t("page-payments-import-confidence-help"),
            )

        # Import button
        import_disabled = not (selected_account_id and uploaded_file)
        if st.button(
            t("page-payments-import-button"),
            disabled=import_disabled,
            use_container_width=True,
        ):
            if not selected_account_id:
                st.error(t("page-payments-import-error-no-account"))
            elif not uploaded_file:
                st.error(t("page-payments-import-error-no-file"))
            else:
                with st.spinner(t("page-payments-import-importing")):
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
                        st.success(f"{result['message']}")

                        # Show details
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                t("page-payments-import-metric-imported"),
                                result["transactions_imported"],
                            )
                        with col2:
                            st.metric(
                                t("page-payments-import-metric-errors"),
                                len(result.get("errors", [])),
                            )
                        with col3:
                            st.metric(
                                t("page-payments-import-metric-duplicates"),
                                result.get("duplicates", 0),
                            )

                        if result.get("format_detected"):
                            st.info(
                                t(
                                    "page-payments-import-format-detected",
                                    {"format": result["format_detected"]},
                                )
                            )

                        # Show errors if any
                        if result.get("errors"):
                            with st.expander(
                                t("page-payments-import-errors-title"), expanded=False
                            ):
                                for error in result["errors"]:
                                    st.write(f"• {error}")

                        # Clear cache and refresh
                        st.cache_data.clear()
                        st.success(t("page-payments-import-success-refresh"))

                    else:
                        st.error(f"{result['message']}")
                        if result.get("errors"):
                            for error in result["errors"]:
                                st.write(f"• {error}")

        if st.button(t("page-payments-import-close")):
            st.session_state.show_import_form = False
            st.rerun()

# Main content
try:
    # Bank accounts overview
    if accounts:
        st.subheader(t("page-payments-accounts-title"))

        # Display accounts in a grid
        cols = st.columns(min(len(accounts), 3))
        for i, account in enumerate(accounts):
            with cols[i % len(cols)]:
                with st.container(border=True):
                    st.subheader(f"{account['name']}")
                    st.metric(
                        t("page-payments-accounts-current-balance"),
                        f"€{account['current_balance']:,.2f}",
                        delta=f"€{account['current_balance'] - account['opening_balance']:,.2f}",
                    )
                    st.caption(t("page-payments-accounts-iban", {"last4": account["iban"][-4:]}))
                    st.caption(t("page-payments-accounts-bank", {"name": account["bank_name"]}))

        st.markdown("---")

    # Payment statistics
    st.subheader(t("page-payments-stats-title"))
    stats = payment_service.get_payment_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(t("page-payments-stats-accounts"), stats["total_accounts"])

    with col2:
        st.metric(t("page-payments-stats-transactions"), stats["total_transactions"])

    with col3:
        st.metric(t("page-payments-stats-balance"), f"€{stats['total_balance']:,.2f}")

    with col4:
        matched_pct = (
            (stats["matched_transactions"] / stats["total_transactions"] * 100)
            if stats["total_transactions"] > 0
            else 0
        )
        st.metric(t("page-payments-stats-reconciled"), f"{matched_pct:.1f}%")

    # Status distribution
    if stats["status_distribution"]:
        st.subheader(t("page-payments-stats-distribution-title"))

        status_data = []
        for status, count in stats["status_distribution"].items():
            if count > 0:
                status_data.append(
                    {
                        t("page-payments-stats-distribution-status"): status_labels.get(
                            status, status
                        ),
                        t("page-payments-stats-distribution-transactions"): count,
                    }
                )

        if status_data:
            status_df = pd.DataFrame(status_data)
            st.bar_chart(
                status_df.set_index(t("page-payments-stats-distribution-status")), height=200
            )

    st.markdown("---")

    # Transactions list
    st.subheader(t("page-payments-transactions-title"))

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
            "id": t("page-payments-table-col-id"),
            "date": t("page-payments-table-col-date"),
            "amount": t("page-payments-table-col-amount"),
            "description": t("page-payments-table-col-description"),
            "reference": t("page-payments-table-col-reference"),
            "status": t("page-payments-table-col-status"),
            "matched_payment_id": t("page-payments-table-col-invoice"),
        }
        df_display = df.rename(columns=column_names)

        # Format columns
        date_col = t("page-payments-table-col-date")
        amount_col = t("page-payments-table-col-amount")
        status_col = t("page-payments-table-col-status")
        actions_col = t("page-payments-table-col-actions")

        df_display[date_col] = pd.to_datetime(df_display[date_col]).dt.strftime("%d/%m/%Y")
        df_display[amount_col] = df_display[amount_col].apply(lambda x: f"€{x:,.2f}")
        df_display[status_col] = df_display[status_col].apply(lambda x: status_labels.get(x, x))

        # Add action column
        df_display[actions_col] = ""

        # Display transactions
        id_col = t("page-payments-table-col-id")
        desc_col = t("page-payments-table-col-description")
        ref_col = t("page-payments-table-col-reference")
        invoice_col = t("page-payments-table-col-invoice")

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
                st.write(f"**{row[id_col][:8]}...**")  # Show first 8 chars of UUID

            with col_date:
                st.write(row[date_col])

            with col_amount:
                amount_color = (
                    "green"
                    if row[amount_col].startswith("€")
                    and float(row[amount_col].replace("€", "").replace(",", "")) > 0
                    else "red"
                )
                st.markdown(
                    f'<span style="color: {amount_color}">{row[amount_col]}</span>',
                    unsafe_allow_html=True,
                )

            with col_desc:
                # Truncate long descriptions
                desc = row[desc_col]
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                st.write(desc)

            with col_ref:
                st.write(row[ref_col] or "-")

            with col_status:
                status_color = {
                    t("page-payments-status-unmatched"): "orange",
                    t("page-payments-status-matched"): "green",
                    t("page-payments-status-ignored"): "gray",
                }.get(row[status_col], "blue")
                st.markdown(
                    f'<span style="color: {status_color}">●</span> {row[status_col]}',
                    unsafe_allow_html=True,
                )

            with col_invoice:
                if pd.notna(row[invoice_col]) and row[invoice_col]:
                    st.write(f"{row[invoice_col]}")
                else:
                    st.write("-")

            with col_actions:
                tx_id = row[id_col]
                if st.button("", key=f"view_{tx_id}", help=t("page-payments-action-view-details")):
                    st.session_state.selected_transaction_id = tx_id
                    st.session_state.show_transaction_detail = True

                if row[status_col] == t("page-payments-status-unmatched"):
                    if st.button("", key=f"match_{tx_id}", help=t("page-payments-action-match")):
                        st.session_state.selected_transaction_id = tx_id
                        st.session_state.show_match_form = True
                elif row[status_col] in [
                    t("page-payments-status-matched"),
                    t("page-payments-status-paired"),
                ]:
                    st.write("")  # Already matched

            st.markdown("---")

        # Summary
        total_amount = df["amount"].sum()
        st.info(
            t(
                "page-payments-transactions-summary",
                {"total": f"€{total_amount:,.2f}", "count": len(transactions)},
            )
        )

    else:
        if selected_account_id or selected_status != "all":
            st.info(t("page-payments-no-transactions-filtered"))
        else:
            st.info(t("page-payments-no-transactions"))

            # Quick setup guide
            with st.expander(t("page-payments-quickstart-title"), expanded=True):
                st.markdown(t("page-payments-quickstart-content"))

except Exception as e:
    st.error(t("page-payments-error-loading", {"error": str(e)}))
    st.info(t("page-payments-error-loading-hint"))

# Transaction detail modal
if st.session_state.get("show_transaction_detail", False):
    tx_id = st.session_state.get("selected_transaction_id")
    if tx_id:
        transaction = payment_service.get_transaction_detail(tx_id)
        if transaction:
            with st.expander(
                t("page-payments-detail-title", {"id": str(transaction.id)[:8]}), expanded=True
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**{t('page-payments-detail-id')}:** {transaction.id}")
                    st.write(
                        f"**{t('page-payments-detail-date')}:** {transaction.date.strftime('%d/%m/%Y')}"
                    )
                    st.write(f"**{t('page-payments-detail-amount')}:** €{transaction.amount:,.2f}")
                    st.write(
                        f"**{t('page-payments-detail-description')}:** {transaction.description}"
                    )

                with col2:
                    st.write(
                        f"**{t('page-payments-detail-reference')}:** {transaction.reference or 'N/A'}"
                    )
                    st.write(
                        f"**{t('page-payments-detail-counterparty')}:** {transaction.counterparty or 'N/A'}"
                    )
                    st.write(f"**{t('page-payments-detail-status')}:** {transaction.status.value}")
                    if transaction.match_confidence:
                        st.write(
                            f"**{t('page-payments-detail-confidence')}:** {transaction.match_confidence:.1%}"
                        )

                if transaction.matched_payment_id:
                    st.write(
                        f"**{t('page-payments-detail-linked-invoice')}:** {transaction.matched_payment_id}"
                    )

                if st.button(t("page-payments-detail-close"), key="close_detail"):
                    st.session_state.show_transaction_detail = False
                    st.rerun()
        else:
            st.error(t("page-payments-detail-not-found"))
            st.session_state.show_transaction_detail = False

# Match transaction modal
if st.session_state.get("show_match_form", False):
    tx_id = st.session_state.get("selected_transaction_id")
    if tx_id:
        transaction = payment_service.get_transaction_detail(tx_id)
        if transaction:
            with st.expander(
                t("page-payments-match-title", {"amount": f"€{transaction.amount:,.2f}"}),
                expanded=True,
            ):
                # Transaction details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(
                        f"**{t('page-payments-match-date')}:** {transaction.date.strftime('%d/%m/%Y')}"
                    )
                    st.write(f"**{t('page-payments-match-amount')}:** €{transaction.amount:,.2f}")
                    st.write(
                        f"**{t('page-payments-match-description')}:** {transaction.description}"
                    )

                with col2:
                    st.write(
                        f"**{t('page-payments-match-reference')}:** {transaction.reference or 'N/A'}"
                    )
                    st.write(
                        f"**{t('page-payments-match-counterparty')}:** {transaction.counterparty or 'N/A'}"
                    )
                    st.write(f"**{t('page-payments-match-status')}:** {transaction.status.value}")

                # Get potential matches
                potential_matches = payment_service.get_potential_matches(tx_id, limit=10)

                if potential_matches:
                    st.subheader(t("page-payments-match-suggestions-title"))

                    # Display matches
                    for match in potential_matches:
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                            with col1:
                                st.write(f"**{match['numero']}/{match['anno']}**")
                                st.write(
                                    t("page-payments-match-client", {"client": match["cliente"]})
                                )
                                st.write(f"€{match['totale']:,.2f}")

                            with col2:
                                confidence = match.get("confidence", 0)
                                st.metric(t("page-payments-match-confidence"), f"{confidence:.1%}")

                            with col3:
                                days_diff = match.get("days_difference", 0)
                                st.write(
                                    t("page-payments-match-days-diff", {"days": abs(days_diff)})
                                )

                            with col4:
                                amount_diff = match.get("amount_difference", 0)
                                color = "green" if abs(amount_diff) < 0.01 else "orange"
                                st.markdown(
                                    f"<span style='color:{color}'>€{amount_diff:+,.2f}</span>",
                                    unsafe_allow_html=True,
                                )

                            # Match button
                            match_key = f"match_{tx_id}_{match['id']}"
                            if st.button(
                                t("page-payments-match-button"),
                                key=match_key,
                                use_container_width=True,
                            ):
                                with st.spinner(t("page-payments-match-matching")):
                                    result = payment_service.match_transaction(tx_id, match["id"])
                                    if result["success"]:
                                        st.success(
                                            t(
                                                "page-payments-match-success",
                                                {"number": match["numero"]},
                                            )
                                        )
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(
                                            t(
                                                "page-payments-match-error",
                                                {"error": result["message"]},
                                            )
                                        )

                else:
                    st.info(t("page-payments-match-no-suggestions"))

                # Manual match option
                st.divider()
                st.subheader(t("page-payments-match-manual-title"))

                search_term = st.text_input(
                    t("page-payments-match-manual-search"),
                    placeholder=t("page-payments-match-manual-placeholder"),
                    help=t("page-payments-match-manual-help"),
                )

                if search_term:
                    manual_matches = payment_service.search_invoices_for_matching(
                        search_term, transaction.amount, limit=5
                    )

                    if manual_matches:
                        st.write(t("page-payments-match-manual-results"))
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
                                if st.button(t("page-payments-match-manual-button"), key=match_key):
                                    with st.spinner(t("page-payments-match-matching")):
                                        result = payment_service.match_transaction(
                                            tx_id, match["id"]
                                        )
                                        if result["success"]:
                                            st.success(t("page-payments-match-manual-success"))
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error(
                                                t(
                                                    "page-payments-match-error",
                                                    {"error": result["message"]},
                                                )
                                            )
                    else:
                        st.write(t("page-payments-match-manual-no-results"))

                if st.button(t("page-payments-match-close"), key="close_match"):
                    st.session_state.show_match_form = False
                    st.rerun()
        else:
            st.error(t("page-payments-detail-not-found"))
            st.session_state.show_match_form = False

# Quick stats
st.markdown(t("page-payments-quick-stats-title"))

try:
    from openfatture.cli.ui.dashboard import DashboardData

    data = DashboardData()

    payment_stats = data.get_payment_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(t("page-payments-quick-stats-unmatched"), payment_stats["unmatched"])

    with col2:
        st.metric(t("page-payments-quick-stats-matched"), payment_stats["matched"])

    with col3:
        st.metric(t("page-payments-quick-stats-ignored"), payment_stats["ignored"])

    with col4:
        total = sum(payment_stats.values())
        st.metric(t("page-payments-quick-stats-total"), total)

    # Payment due
    st.markdown("---")
    st.markdown(t("page-payments-due-title"))

    payment_due = data.get_payment_due_summary(window_days=30, max_upcoming=10)

    if payment_due.overdue or payment_due.due_soon or payment_due.upcoming:
        import pandas as pd

        all_entries = payment_due.overdue + payment_due.due_soon + payment_due.upcoming

        df = pd.DataFrame(
            [
                {
                    t("page-payments-due-col-invoice"): e.invoice_ref,
                    t("page-payments-due-col-client"): e.client_name[:30],
                    t("page-payments-due-col-due-date"): e.due_date.strftime("%d/%m/%Y"),
                    t("page-payments-due-col-residual"): f"€{float(e.residual):,.2f}",
                    t("page-payments-due-col-status"): e.status.value.replace("_", " ").title(),
                }
                for e in all_entries
            ]
        )

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.metric(
            t("page-payments-due-total-residual"),
            f"€{float(payment_due.total_outstanding):,.2f}",
        )
    else:
        st.success(t("page-payments-due-no-payments"))

    data.close()

except Exception as e:
    st.error(t("page-payments-quick-stats-error", {"error": str(e)}))
