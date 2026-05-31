"""Invoice creation wizard page.

Multi-step guided wizard for creating invoices with AI assistance and validation.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import streamlit as st

from openfatture.i18n import get_translator
from openfatture.web.services.ai_service import get_ai_service
from openfatture.web.services.client_service import StreamlitClientService
from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.web.utils.state import init_wizard_state, reset_wizard

# Initialize translator
t = get_translator()


def render_step_indicator(current_step: int, total_steps: int) -> None:
    """Render step indicator with progress bar."""
    st.markdown(
        f"### {t('page-invoice-create-wizard-title', step=current_step, total=total_steps)}"
    )

    # Progress bar
    progress = (current_step - 1) / (total_steps - 1)
    st.progress(progress)

    # Step labels
    steps = [
        t("page-invoice-create-step-1-label"),
        t("page-invoice-create-step-2-label"),
        t("page-invoice-create-step-3-label"),
        t("page-invoice-create-step-4-label"),
        t("page-invoice-create-step-5-label"),
    ]

    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps, strict=False)):
        with col:
            if i + 1 == current_step:
                st.markdown(f"**{step_name}**")
            elif i + 1 < current_step:
                st.markdown(f"{step_name}")
            else:
                st.markdown(f"○ {step_name}")


def step_1_select_client(wizard_state: dict[str, Any]) -> bool:
    """Step 1: Select or create client."""
    st.header(t("page-invoice-create-step-1-header"))

    client_service = StreamlitClientService()

    # Search existing clients
    search_term = st.text_input(
        t("page-invoice-create-client-search-label"),
        placeholder=t("page-invoice-create-client-search-placeholder"),
        help=t("page-invoice-create-client-search-help"),
    )

    clients = client_service.get_clients(search=search_term, limit=20)

    if clients:
        st.subheader(t("page-invoice-create-client-existing-title"))
        client_options = [""] + [
            f"{c['denominazione']} ({t('page-invoice-create-client-vat-label')}: {c['partita_iva']})"
            for c in clients
        ]
        selected_client_display = st.selectbox(
            t("page-invoice-create-client-select-label"),
            options=client_options,
            help=t("page-invoice-create-client-select-help"),
        )

        if selected_client_display:
            # Find selected client
            for client in clients:
                if (
                    f"{client['denominazione']} ({t('page-invoice-create-client-vat-label')}: {client.get('partita_iva', 'N/A')})"
                    == selected_client_display
                ):
                    wizard_state["selected_client"] = client
                    break

    # Create new client option
    st.divider()
    st.subheader(t("page-invoice-create-client-create-title"))

    with st.expander(t("page-invoice-create-client-create-expander"), expanded=not clients):
        with st.form("create_client_form"):
            col1, col2 = st.columns(2)

            with col1:
                denominazione = st.text_input(
                    t("page-invoice-create-client-name-label"),
                    placeholder=t("page-invoice-create-client-name-placeholder"),
                )
                partita_iva = st.text_input(
                    t("page-invoice-create-client-vat-input-label"),
                    placeholder=t("page-invoice-create-client-vat-placeholder"),
                )
                codice_fiscale = st.text_input(
                    t("page-invoice-create-client-fiscal-code-label"),
                    placeholder=t("page-invoice-create-client-fiscal-code-placeholder"),
                )

            with col2:
                indirizzo = st.text_input(
                    t("page-invoice-create-client-address-label"),
                    placeholder=t("page-invoice-create-client-address-placeholder"),
                )
                email = st.text_input(
                    t("page-invoice-create-client-email-label"),
                    placeholder=t("page-invoice-create-client-email-placeholder"),
                )
                telefono = st.text_input(
                    t("page-invoice-create-client-phone-label"),
                    placeholder=t("page-invoice-create-client-phone-placeholder"),
                )

            regime_options = [
                t("page-invoice-create-client-regime-ordinary"),
                t("page-invoice-create-client-regime-flat"),
            ]
            regime_fiscale = st.selectbox(
                t("page-invoice-create-client-regime-label"), options=regime_options
            )

            if st.form_submit_button(
                t("page-invoice-create-client-create-button"), use_container_width=True
            ):
                if not denominazione:
                    st.error(t("page-invoice-create-client-name-required"))
                    return False

                # Extract regime code
                regime_code = regime_fiscale.split(" - ")[0]

                client_data = {
                    "denominazione": denominazione,
                    "partita_iva": partita_iva or None,
                    "codice_fiscale": codice_fiscale or None,
                    "indirizzo": indirizzo or None,
                    "email": email or None,
                    "telefono": telefono or None,
                    "regime_fiscale": regime_code,
                }

                try:
                    new_client = client_service.create_client(client_data)
                    wizard_state["selected_client"] = {
                        "id": new_client.id,
                        "denominazione": new_client.denominazione,
                        "partita_iva": new_client.partita_iva,
                        "regime_fiscale": new_client.regime_fiscale,
                    }
                    st.success(t("page-invoice-create-client-create-success", name=denominazione))
                    st.cache_data.clear()  # Clear cache to show new client
                    st.rerun()
                except Exception as e:
                    st.error(t("page-invoice-create-client-create-error", error=str(e)))
                    return False

    # Check if client is selected
    return "selected_client" in wizard_state


def step_2_invoice_details(wizard_state: dict[str, Any]) -> bool:
    """Step 2: Invoice basic details."""
    st.header(t("page-invoice-create-step-2-header"))

    selected_client = wizard_state.get("selected_client", {})
    if selected_client:
        st.info(
            t(
                "page-invoice-create-details-client-selected",
                name=selected_client["denominazione"],
            )
        )
        regime_display = selected_client.get("regime_fiscale", "RF01 - Ordinario")
        st.write(t("page-invoice-create-details-regime", regime=regime_display))

    col1, col2 = st.columns(2)

    with col1:
        # Auto-generate invoice number
        invoice_service = StreamlitInvoiceService()
        next_number = invoice_service.get_next_invoice_number(date.today().year)
        numero = st.text_input(
            t("page-invoice-create-details-number-label"),
            value=str(next_number),
            help=t("page-invoice-create-details-number-help"),
        )

    with col2:
        anno = st.number_input(
            t("page-invoice-create-details-year-label"),
            value=date.today().year,
            min_value=2020,
            max_value=2030,
            help=t("page-invoice-create-details-year-help"),
        )

        data_emissione = st.date_input(
            t("page-invoice-create-details-date-label"),
            value=date.today(),
            help=t("page-invoice-create-details-date-help"),
        )

        # Calculate due date (default 30 days)
        default_due_date = data_emissione + timedelta(days=30)
        data_scadenza = st.date_input(
            t("page-invoice-create-details-due-date-label"),
            value=default_due_date,
            help=t("page-invoice-create-details-due-date-help"),
        )

    # Additional details
    st.subheader(t("page-invoice-create-details-additional-title"))
    oggetto = st.text_area(
        t("page-invoice-create-details-subject-label"),
        placeholder=t("page-invoice-create-details-subject-placeholder"),
        help=t("page-invoice-create-details-subject-help"),
    )

    note = st.text_area(
        t("page-invoice-create-details-notes-label"),
        placeholder=t("page-invoice-create-details-notes-placeholder"),
        help=t("page-invoice-create-details-notes-help"),
    )

    # Store data
    wizard_state["invoice_details"] = {
        "numero": numero,
        "anno": anno,
        "data_emissione": data_emissione,
        "data_scadenza": data_scadenza,
        "oggetto": oggetto,
        "note": note,
    }

    return True


def step_3_add_products(wizard_state: dict[str, Any]) -> bool:
    """Step 3: Add products/services line items."""
    st.header(t("page-invoice-create-step-3-header"))

    # Initialize line items if not exists
    if "line_items" not in wizard_state:
        wizard_state["line_items"] = []

    line_items = wizard_state["line_items"]

    # Display existing items
    if line_items:
        st.subheader(t("page-invoice-create-lines-title"))
        for i, item in enumerate(line_items):
            with st.expander(f"{item['descrizione'][:50]}...", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    item["descrizione"] = st.text_area(
                        t("page-invoice-create-lines-description-label"),
                        value=item["descrizione"],
                        key=f"desc_{i}",
                        height=100,
                    )
                with col2:
                    item["quantita"] = st.number_input(
                        t("page-invoice-create-lines-quantity-label"),
                        value=float(item["quantita"]),
                        min_value=0.01,
                        step=0.01,
                        key=f"qty_{i}",
                    )
                with col3:
                    item["prezzo_unitario"] = st.number_input(
                        t("page-invoice-create-lines-price-label"),
                        value=float(item["prezzo_unitario"]),
                        min_value=0.01,
                        step=0.01,
                        key=f"price_{i}",
                    )

                # Calculate total for this item
                total = Decimal(str(item["quantita"])) * Decimal(str(item["prezzo_unitario"]))
                st.write(f"**{t('page-invoice-create-lines-row-total', total=f'€{total:.2f}')}**")

                # Remove button
                if st.button(t("page-invoice-create-lines-remove-button"), key=f"remove_{i}"):
                    line_items.pop(i)
                    st.rerun()

    # Add new item
    st.divider()
    st.subheader(t("page-invoice-create-lines-add-title"))

    with st.form("add_item_form"):
        descrizione = st.text_area(
            t("page-invoice-create-lines-description-input-label"),
            placeholder=t("page-invoice-create-lines-description-placeholder"),
            height=100,
        )

        col1, col2 = st.columns(2)
        with col1:
            quantita = st.number_input(
                t("page-invoice-create-lines-quantity-input-label"),
                value=1.0,
                min_value=0.01,
                step=0.01,
                help=t("page-invoice-create-lines-quantity-help"),
            )
        with col2:
            prezzo_unitario = st.number_input(
                t("page-invoice-create-lines-price-input-label"),
                min_value=0.01,
                step=0.01,
                help=t("page-invoice-create-lines-price-help"),
            )

        aliquota_iva = st.selectbox(
            t("page-invoice-create-lines-vat-label"),
            options=[0, 4, 5, 10, 20, 21, 22],
            index=6,  # Default 22%
            help=t("page-invoice-create-lines-vat-help"),
        )

        if st.form_submit_button(
            t("page-invoice-create-lines-add-button"), use_container_width=True
        ):
            if not descrizione:
                st.error(t("page-invoice-create-lines-description-required"))
            else:
                new_item = {
                    "descrizione": descrizione,
                    "quantita": quantita,
                    "prezzo_unitario": prezzo_unitario,
                    "aliquota_iva": aliquota_iva,
                }
                line_items.append(new_item)
                st.success(t("page-invoice-create-lines-add-success"))
                st.rerun()

    # Calculate totals
    if line_items:
        st.divider()
        st.subheader(t("page-invoice-create-lines-totals-title"))

        totale_imponibile = Decimal("0")
        totale_iva = Decimal("0")

        for item in line_items:
            imponibile = Decimal(str(item["quantita"])) * Decimal(str(item["prezzo_unitario"]))
            iva = imponibile * Decimal(str(item["aliquota_iva"])) / Decimal("100")
            totale_imponibile += imponibile
            totale_iva += iva

        totale_fattura = totale_imponibile + totale_iva

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t("page-invoice-create-lines-subtotal-label"), f"€{totale_imponibile:.2f}")
        with col2:
            st.metric(t("page-invoice-create-lines-vat-amount-label"), f"€{totale_iva:.2f}")
        with col3:
            st.metric(t("page-invoice-create-lines-total-label"), f"€{totale_fattura:.2f}")

    return len(line_items) > 0


def step_4_ai_assistance(wizard_state: dict[str, Any]) -> bool:
    """Step 4: AI assistance for descriptions and validation."""
    st.header(t("page-invoice-create-step-4-header"))

    ai_service = get_ai_service()

    # AI Description Generator
    st.subheader(t("page-invoice-create-ai-description-title"))

    if st.button(t("page-invoice-create-ai-description-button"), use_container_width=True):
        line_items = wizard_state.get("line_items", [])

        if not line_items:
            st.warning(t("page-invoice-create-ai-description-no-lines"))
        else:
            with st.spinner(t("page-invoice-create-ai-description-generating")):
                for i, item in enumerate(line_items):
                    if len(item["descrizione"]) < 20:  # Only enhance short descriptions
                        try:
                            # Generate professional description
                            prompt = f"""Crea una descrizione professionale e dettagliata per una fattura
                            basata su questa descrizione breve: "{item["descrizione"]}"

                            Il cliente è: {wizard_state["selected_client"]["denominazione"]}

                            Rendi la descrizione formale, completa e professionale per una fattura italiana.
                            Massimo 200 caratteri."""

                            response = ai_service.generate_invoice_description(prompt)

                            if response and response.content:
                                item["descrizione"] = response.content
                                st.success(
                                    t(
                                        "page-invoice-create-ai-description-improved",
                                        row=i + 1,
                                    )
                                )

                        except Exception as e:
                            st.warning(
                                t(
                                    "page-invoice-create-ai-description-error",
                                    row=i + 1,
                                    error=str(e),
                                )
                            )

                st.rerun()

    # AI Tax Advisor
    st.subheader(t("page-invoice-create-ai-vat-title"))

    if st.button(t("page-invoice-create-ai-vat-button"), use_container_width=True):
        line_items = wizard_state.get("line_items", [])

        if not line_items:
            st.warning(t("page-invoice-create-ai-vat-no-lines"))
        else:
            with st.spinner(t("page-invoice-create-ai-vat-checking")):
                for i, item in enumerate(line_items):
                    try:
                        prompt = f"""Verifica se l'aliquota IVA {item["aliquota_iva"]}% è corretta
                        per questo servizio/prodotto: "{item["descrizione"]}"

                        Cliente regime fiscale: {wizard_state["selected_client"]["regime_fiscale"]}
                        Fornitore regime fiscale: RF19 (forfettario)

                        Fornisci solo l'aliquota IVA corretta (numero) o "OK" se è corretta."""

                        response = ai_service.suggest_vat(prompt)

                        if response and response.content:
                            suggestion = response.content
                        else:
                            suggestion = ""

                        if suggestion and suggestion.strip() != "OK":
                            try:
                                suggested_rate = float(suggestion.strip().replace("%", ""))
                                if suggested_rate != item["aliquota_iva"]:
                                    st.info(
                                        t(
                                            "page-invoice-create-ai-vat-suggestion",
                                            row=i + 1,
                                            suggested=suggested_rate,
                                            current=item["aliquota_iva"],
                                        )
                                    )
                                    if st.button(
                                        t(
                                            "page-invoice-create-ai-vat-apply",
                                            rate=suggested_rate,
                                            row=i + 1,
                                        ),
                                        key=f"apply_tax_{i}",
                                    ):
                                        item["aliquota_iva"] = suggested_rate
                                        st.success(t("page-invoice-create-ai-vat-updated"))
                                        st.rerun()
                            except ValueError:
                                st.info(
                                    t("page-invoice-create-ai-vat-info", row=i + 1, info=suggestion)
                                )

                    except Exception as e:
                        st.warning(t("page-invoice-create-ai-vat-error", row=i + 1, error=str(e)))

    # Compliance Check
    st.subheader(t("page-invoice-create-ai-compliance-title"))

    if st.button(t("page-invoice-create-ai-compliance-button"), use_container_width=True):
        # Basic validation
        issues = []

        invoice_details = wizard_state.get("invoice_details", {})
        line_items = wizard_state.get("line_items", [])

        if not invoice_details.get("numero"):
            issues.append(t("page-invoice-create-ai-compliance-no-number"))

        if not line_items:
            issues.append(t("page-invoice-create-ai-compliance-no-lines"))

        for i, item in enumerate(line_items):
            if not item.get("descrizione"):
                issues.append(t("page-invoice-create-ai-compliance-line-no-desc", row=i + 1))
            if item.get("quantita", 0) <= 0:
                issues.append(t("page-invoice-create-ai-compliance-line-qty-invalid", row=i + 1))
            if item.get("prezzo_unitario", 0) <= 0:
                issues.append(t("page-invoice-create-ai-compliance-line-price-invalid", row=i + 1))

        if issues:
            st.error(f"**{t('page-invoice-create-ai-compliance-issues-found')}:**")
            for issue in issues:
                st.write(f"• {issue}")
        else:
            st.success(t("page-invoice-create-ai-compliance-success"))

    return True


def step_5_summary_and_create(wizard_state: dict[str, Any]) -> bool:
    """Step 5: Summary and create invoice."""
    st.header(t("page-invoice-create-step-5-header"))

    # Display summary
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("page-invoice-create-summary-client-title"))
        client = wizard_state["selected_client"]
        st.write(f"**{client['denominazione']}**")
        if client.get("partita_iva"):
            st.write(t("page-invoice-create-summary-client-vat", vat=client["partita_iva"]))
        st.write(t("page-invoice-create-summary-client-regime", regime=client["regime_fiscale"]))

    with col2:
        st.subheader(t("page-invoice-create-summary-invoice-title"))
        details = wizard_state["invoice_details"]
        st.write(f"**{details['numero']}/{details['anno']}**")
        st.write(
            t(
                "page-invoice-create-summary-invoice-date",
                date=details["data_emissione"].strftime("%d/%m/%Y"),
            )
        )
        st.write(
            t(
                "page-invoice-create-summary-invoice-due",
                date=details["data_scadenza"].strftime("%d/%m/%Y"),
            )
        )

    # Line items summary
    st.subheader(t("page-invoice-create-summary-lines-title"))
    line_items = wizard_state["line_items"]

    summary_data = []
    totale_imponibile = Decimal("0")
    totale_iva = Decimal("0")

    for item in line_items:
        imponibile = Decimal(str(item["quantita"])) * Decimal(str(item["prezzo_unitario"]))
        iva = imponibile * Decimal(str(item["aliquota_iva"])) / Decimal("100")
        totale_imponibile += imponibile
        totale_iva += iva

        summary_data.append(
            {
                t("page-invoice-create-summary-table-description"): (
                    item["descrizione"][:50] + "..."
                    if len(item["descrizione"]) > 50
                    else item["descrizione"]
                ),
                t("page-invoice-create-summary-table-quantity"): item["quantita"],
                t("page-invoice-create-summary-table-price"): f"€{item['prezzo_unitario']:.2f}",
                t("page-invoice-create-summary-table-vat"): f"{item['aliquota_iva']}%",
                t("page-invoice-create-summary-table-total"): f"€{(imponibile + iva):.2f}",
            }
        )

    st.dataframe(summary_data, use_container_width=True)

    # Totals
    st.subheader(t("page-invoice-create-summary-totals-title"))
    totale_fattura = totale_imponibile + totale_iva

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t("page-invoice-create-summary-totals-subtotal"), f"€{totale_imponibile:.2f}")
    with col2:
        st.metric(t("page-invoice-create-summary-totals-vat"), f"€{totale_iva:.2f}")
    with col3:
        st.metric(t("page-invoice-create-summary-totals-total"), f"€{totale_fattura:.2f}")

    # Create invoice
    st.divider()

    if st.button(
        t("page-invoice-create-summary-create-button"), type="primary", use_container_width=True
    ):
        with st.spinner(t("page-invoice-create-summary-creating")):
            try:
                invoice_service = StreamlitInvoiceService()

                # Prepare line items data
                righe_data = []
                for item in line_items:
                    righe_data.append(
                        {
                            "descrizione": item["descrizione"],
                            "quantita": item["quantita"],
                            "prezzo_unitario": item["prezzo_unitario"],
                            "aliquota_iva": item["aliquota_iva"],
                        }
                    )

                # Create invoice
                fattura = invoice_service.create_invoice(
                    cliente_id=wizard_state["selected_client"]["id"],
                    numero=details["numero"],
                    anno=details["anno"],
                    data_emissione=details["data_emissione"],
                    righe_data=righe_data,
                )

                if not fattura:
                    raise ValueError(t("page-invoice-create-summary-error-create-failed"))

                st.success(
                    t(
                        "page-invoice-create-summary-success",
                        number=fattura.numero,
                        year=fattura.anno,
                    )
                )

                # Clear wizard state
                reset_wizard()

                # Show next steps (fattura is guaranteed non-None here due to check above)
                st.info(
                    t(
                        "page-invoice-create-summary-next-steps",
                        number=fattura.numero,
                    )
                )

                return True

            except Exception as e:
                st.error(t("page-invoice-create-summary-error", error=str(e)))
                return False

    return False


def main() -> None:
    """Main page function."""
    st.set_page_config(page_title=t("page-invoice-create-page-title"), page_icon="", layout="wide")

    st.title(t("page-invoice-create-title"))

    # Initialize wizard state
    wizard_state = init_wizard_state()

    # Define steps
    steps = [
        step_1_select_client,
        step_2_invoice_details,
        step_3_add_products,
        step_4_ai_assistance,
        step_5_summary_and_create,
    ]

    current_step = wizard_state.get("current_step", 1)
    total_steps = len(steps)

    # Render step indicator
    render_step_indicator(current_step, total_steps)

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_step > 1:
            if st.button(t("page-invoice-create-nav-back"), use_container_width=True):
                wizard_state["current_step"] = current_step - 1
                st.rerun()

    with col3:
        if current_step < total_steps:
            step_function = steps[current_step - 1]
            if step_function(wizard_state):
                if st.button(t("page-invoice-create-nav-next"), use_container_width=True):
                    wizard_state["current_step"] = current_step + 1
                    st.rerun()
        else:
            # Final step
            step_function = steps[current_step - 1]
            step_completed = step_function(wizard_state)
            if step_completed:
                st.success(t("page-invoice-create-nav-success"))
                if st.button(t("page-invoice-create-nav-create-another"), use_container_width=True):
                    reset_wizard()
                    st.rerun()

    # Render current step
    with st.container():
        step_function = steps[current_step - 1]
        step_valid = step_function(wizard_state)

        # Auto-advance if step is valid and not final step
        if (
            step_valid
            and current_step < total_steps
            and not st.session_state.get("manual_step", False)
        ):
            # Small delay for UX
            pass


if __name__ == "__main__":
    main()
