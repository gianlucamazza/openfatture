"""Invoice creation wizard page.

Multi-step guided wizard for creating invoices with AI assistance and validation.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import streamlit as st

from openfatture.web.services.ai_service import get_ai_service
from openfatture.web.services.client_service import StreamlitClientService
from openfatture.web.services.invoice_service import StreamlitInvoiceService
from openfatture.web.utils.async_helpers import run_async
from openfatture.web.utils.state import init_wizard_state, reset_wizard


def render_step_indicator(current_step: int, total_steps: int) -> None:
    """Render step indicator with progress bar."""
    st.markdown(f"### 📋 Creazione Fattura - Passo {current_step}/{total_steps}")

    # Progress bar
    progress = (current_step - 1) / (total_steps - 1)
    st.progress(progress)

    # Step labels
    steps = [
        "👥 Seleziona Cliente",
        "📝 Dettagli Fattura",
        "🛒 Aggiungi Prodotti",
        "🤖 AI Assistenza",
        "✅ Riepilogo & Crea",
    ]

    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps, strict=False)):
        with col:
            if i + 1 == current_step:
                st.markdown(f"**{step_name}**")
            elif i + 1 < current_step:
                st.markdown(f"✅ {step_name}")
            else:
                st.markdown(f"○ {step_name}")


def step_1_select_client(wizard_state: dict[str, Any]) -> bool:
    """Step 1: Select or create client."""
    st.header("👥 Seleziona Cliente")

    client_service = StreamlitClientService()

    # Search existing clients
    search_term = st.text_input(
        "Cerca cliente esistente",
        placeholder="Nome azienda, P.IVA...",
        help="Lascia vuoto per vedere tutti i clienti",
    )

    clients = client_service.get_clients(search=search_term, limit=20)

    if clients:
        st.subheader("Clienti esistenti")
        client_options = [""] + [
            f"{c['denominazione']} (P.IVA: {c['partita_iva']})" for c in clients
        ]
        selected_client_display = st.selectbox(
            "Seleziona cliente",
            options=client_options,
            help="Scegli un cliente esistente o creane uno nuovo",
        )

        if selected_client_display:
            # Find selected client
            for client in clients:
                if (
                    f"{client['denominazione']} (P.IVA: {client.get('partita_iva', 'N/A')})"
                    == selected_client_display
                ):
                    wizard_state["selected_client"] = client
                    break

    # Create new client option
    st.divider()
    st.subheader("➕ Oppure crea nuovo cliente")

    with st.expander("Crea nuovo cliente", expanded=not clients):
        with st.form("create_client_form"):
            col1, col2 = st.columns(2)

            with col1:
                denominazione = st.text_input(
                    "Denominazione *", placeholder="Nome azienda o persona"
                )
                partita_iva = st.text_input("Partita IVA", placeholder="12345678901")
                codice_fiscale = st.text_input(
                    "Codice Fiscale", placeholder="Codice fiscale (se persona fisica)"
                )

            with col2:
                indirizzo = st.text_input("Indirizzo", placeholder="Via Roma 123, 00100 Roma")
                email = st.text_input("Email", placeholder="cliente@email.com")
                telefono = st.text_input("Telefono", placeholder="+39 123 456 7890")

            regime_options = ["RF01 - Ordinario", "RF19 - Forfettario"]
            regime_fiscale = st.selectbox("Regime Fiscale", options=regime_options)

            if st.form_submit_button("Crea Cliente", use_container_width=True):
                if not denominazione:
                    st.error("Denominazione è obbligatoria")
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
                    st.success(f"Cliente '{denominazione}' creato con successo!")
                    st.cache_data.clear()  # Clear cache to show new client
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore nella creazione del cliente: {str(e)}")
                    return False

    # Check if client is selected
    return "selected_client" in wizard_state


def step_2_invoice_details(wizard_state: dict[str, Any]) -> bool:
    """Step 2: Invoice basic details."""
    st.header("📝 Dettagli Fattura")

    selected_client = wizard_state.get("selected_client", {})
    if selected_client:
        st.info(f"Cliente selezionato: **{selected_client['denominazione']}**")
        regime_display = selected_client.get("regime_fiscale", "RF01 - Ordinario")
        st.write(f"Regime fiscale: {regime_display}")

    col1, col2 = st.columns(2)

    with col1:
        # Auto-generate invoice number
        invoice_service = StreamlitInvoiceService()
        next_number = invoice_service.get_next_invoice_number(date.today().year)
        numero = st.text_input(
            "Numero Fattura", value=str(next_number), help="Numero progressivo della fattura"
        )

    with col2:
        anno = st.number_input(
            "Anno",
            value=date.today().year,
            min_value=2020,
            max_value=2030,
            help="Anno fiscale della fattura",
        )

        data_emissione = st.date_input(
            "Data Emissione", value=date.today(), help="Data di emissione della fattura"
        )

        # Calculate due date (default 30 days)
        default_due_date = data_emissione + timedelta(days=30)
        data_scadenza = st.date_input(
            "Data Scadenza", value=default_due_date, help="Data di scadenza del pagamento"
        )

    # Additional details
    st.subheader("📋 Dettagli aggiuntivi")
    oggetto = st.text_area(
        "Oggetto/Descrizione",
        placeholder="Descrizione generale della fattura...",
        help="Descrizione generale dei servizi/prodotti fatturati",
    )

    note = st.text_area(
        "Note",
        placeholder="Eventuali note aggiuntive...",
        help="Note interne o da mostrare in fattura",
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
    st.header("🛒 Prodotti e Servizi")

    # Initialize line items if not exists
    if "line_items" not in wizard_state:
        wizard_state["line_items"] = []

    line_items = wizard_state["line_items"]

    # Display existing items
    if line_items:
        st.subheader("Righe fattura")
        for i, item in enumerate(line_items):
            with st.expander(f"📦 {item['descrizione'][:50]}...", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    item["descrizione"] = st.text_area(
                        "Descrizione", value=item["descrizione"], key=f"desc_{i}", height=100
                    )
                with col2:
                    item["quantita"] = st.number_input(
                        "Quantità",
                        value=float(item["quantita"]),
                        min_value=0.01,
                        step=0.01,
                        key=f"qty_{i}",
                    )
                with col3:
                    item["prezzo_unitario"] = st.number_input(
                        "Prezzo Unitario (€)",
                        value=float(item["prezzo_unitario"]),
                        min_value=0.01,
                        step=0.01,
                        key=f"price_{i}",
                    )

                # Calculate total for this item
                total = Decimal(str(item["quantita"])) * Decimal(str(item["prezzo_unitario"]))
                st.write(f"**Totale riga: €{total:.2f}**")

                # Remove button
                if st.button("🗑️ Rimuovi", key=f"remove_{i}"):
                    line_items.pop(i)
                    st.rerun()

    # Add new item
    st.divider()
    st.subheader("➕ Aggiungi nuova riga")

    with st.form("add_item_form"):
        descrizione = st.text_area(
            "Descrizione *", placeholder="Descrizione del prodotto/servizio...", height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            quantita = st.number_input(
                "Quantità",
                value=1.0,
                min_value=0.01,
                step=0.01,
                help="Quantità del prodotto/servizio",
            )
        with col2:
            prezzo_unitario = st.number_input(
                "Prezzo Unitario (€)", min_value=0.01, step=0.01, help="Prezzo unitario IVA esclusa"
            )

        aliquota_iva = st.selectbox(
            "Aliquota IVA",
            options=[0, 4, 5, 10, 20, 21, 22],
            index=6,  # Default 22%
            help="Aliquota IVA applicabile",
        )

        if st.form_submit_button("Aggiungi Riga", use_container_width=True):
            if not descrizione:
                st.error("Descrizione è obbligatoria")
            else:
                new_item = {
                    "descrizione": descrizione,
                    "quantita": quantita,
                    "prezzo_unitario": prezzo_unitario,
                    "aliquota_iva": aliquota_iva,
                }
                line_items.append(new_item)
                st.success("Riga aggiunta!")
                st.rerun()

    # Calculate totals
    if line_items:
        st.divider()
        st.subheader("💰 Totali")

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
            st.metric("Imponibile", f"€{totale_imponibile:.2f}")
        with col2:
            st.metric("IVA", f"€{totale_iva:.2f}")
        with col3:
            st.metric("Totale", f"€{totale_fattura:.2f}")

    return len(line_items) > 0


def step_4_ai_assistance(wizard_state: dict[str, Any]) -> bool:
    """Step 4: AI assistance for descriptions and validation."""
    st.header("🤖 Assistenza AI")

    ai_service = get_ai_service()

    # AI Description Generator
    st.subheader("📝 Genera Descrizioni con AI")

    if st.button("🎯 Suggerisci descrizioni per le righe", use_container_width=True):
        line_items = wizard_state.get("line_items", [])

        if not line_items:
            st.warning("Aggiungi prima delle righe alla fattura")
        else:
            with st.spinner("Generando descrizioni..."):
                for i, item in enumerate(line_items):
                    if len(item["descrizione"]) < 20:  # Only enhance short descriptions
                        try:
                            # Generate professional description
                            prompt = f"""Crea una descrizione professionale e dettagliata per una fattura
                            basata su questa descrizione breve: "{item["descrizione"]}"

                            Il cliente è: {wizard_state["selected_client"]["denominazione"]}

                            Rendi la descrizione formale, completa e professionale per una fattura italiana.
                            Massimo 200 caratteri."""

                            enhanced_desc = run_async(
                                ai_service.generate_invoice_description(prompt)
                            )

                            if enhanced_desc:
                                item["descrizione"] = enhanced_desc
                                st.success(f"Descrizione riga {i + 1} migliorata!")

                        except Exception as e:
                            st.warning(f"Errore generazione descrizione riga {i + 1}: {str(e)}")

                st.rerun()

    # AI Tax Advisor
    st.subheader("💼 Consigli IVA")

    if st.button("🧾 Verifica aliquote IVA", use_container_width=True):
        line_items = wizard_state.get("line_items", [])

        if not line_items:
            st.warning("Aggiungi prima delle righe alla fattura")
        else:
            with st.spinner("Verificando aliquote IVA..."):
                for i, item in enumerate(line_items):
                    try:
                        prompt = f"""Verifica se l'aliquota IVA {item["aliquota_iva"]}% è corretta
                        per questo servizio/prodotto: "{item["descrizione"]}"

                        Cliente regime fiscale: {wizard_state["selected_client"]["regime_fiscale"]}
                        Fornitore regime fiscale: RF19 (forfettario)

                        Fornisci solo l'aliquota IVA corretta (numero) o "OK" se è corretta."""

                        suggestion = run_async(ai_service.suggest_vat(prompt))

                        if suggestion and suggestion.strip() != "OK":
                            try:
                                suggested_rate = float(suggestion.strip().replace("%", ""))
                                if suggested_rate != item["aliquota_iva"]:
                                    st.info(
                                        f"💡 Riga {i + 1}: Suggerita aliquota IVA {suggested_rate}% invece di {item['aliquota_iva']}%"
                                    )
                                    if st.button(
                                        f"Applica {suggested_rate}% alla riga {i + 1}",
                                        key=f"apply_tax_{i}",
                                    ):
                                        item["aliquota_iva"] = suggested_rate
                                        st.success("Aliquota IVA aggiornata!")
                                        st.rerun()
                            except ValueError:
                                st.info(f"Riga {i + 1}: {suggestion}")

                    except Exception as e:
                        st.warning(f"Errore verifica IVA riga {i + 1}: {str(e)}")

    # Compliance Check
    st.subheader("⚖️ Controllo Conformità")

    if st.button("🔍 Verifica conformità fattura", use_container_width=True):
        # Basic validation
        issues = []

        invoice_details = wizard_state.get("invoice_details", {})
        line_items = wizard_state.get("line_items", [])

        if not invoice_details.get("numero"):
            issues.append("Numero fattura mancante")

        if not line_items:
            issues.append("Nessuna riga fattura presente")

        for i, item in enumerate(line_items):
            if not item.get("descrizione"):
                issues.append(f"Riga {i + 1}: descrizione mancante")
            if item.get("quantita", 0) <= 0:
                issues.append(f"Riga {i + 1}: quantità deve essere > 0")
            if item.get("prezzo_unitario", 0) <= 0:
                issues.append(f"Riga {i + 1}: prezzo unitario deve essere > 0")

        if issues:
            st.error("**Problemi trovati:**")
            for issue in issues:
                st.write(f"• {issue}")
        else:
            st.success("✅ Fattura conforme ai requisiti di base!")

    return True


def step_5_summary_and_create(wizard_state: dict[str, Any]) -> bool:
    """Step 5: Summary and create invoice."""
    st.header("✅ Riepilogo e Creazione")

    # Display summary
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Cliente")
        client = wizard_state["selected_client"]
        st.write(f"**{client['denominazione']}**")
        if client.get("partita_iva"):
            st.write(f"P.IVA: {client['partita_iva']}")
        st.write(f"Regime: {client['regime_fiscale']}")

    with col2:
        st.subheader("📄 Fattura")
        details = wizard_state["invoice_details"]
        st.write(f"**{details['numero']}/{details['anno']}**")
        st.write(f"Emissione: {details['data_emissione'].strftime('%d/%m/%Y')}")
        st.write(f"Scadenza: {details['data_scadenza'].strftime('%d/%m/%Y')}")

    # Line items summary
    st.subheader("🛒 Righe Fattura")
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
                "Descrizione": (
                    item["descrizione"][:50] + "..."
                    if len(item["descrizione"]) > 50
                    else item["descrizione"]
                ),
                "Q.tà": item["quantita"],
                "Prezzo": f"€{item['prezzo_unitario']:.2f}",
                "IVA": f"{item['aliquota_iva']}%",
                "Totale": f"€{(imponibile + iva):.2f}",
            }
        )

    st.dataframe(summary_data, use_container_width=True)

    # Totals
    st.subheader("💰 Totali")
    totale_fattura = totale_imponibile + totale_iva

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Imponibile", f"€{totale_imponibile:.2f}")
    with col2:
        st.metric("IVA", f"€{totale_iva:.2f}")
    with col3:
        st.metric("Totale Fattura", f"€{totale_fattura:.2f}")

    # Create invoice
    st.divider()

    if st.button("🚀 Crea Fattura", type="primary", use_container_width=True):
        with st.spinner("Creando fattura..."):
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

                st.success(f"✅ Fattura {fattura.numero}/{fattura.anno} creata con successo!")

                # Clear wizard state
                reset_wizard()

                # Show next steps
                st.info(
                    f"""
                **Prossimi passi:**
                1. **Valida** la fattura: `openfatture fattura valida {fattura.numero}`
                2. **Invia** alla SDI: `openfatture pec invia {fattura.numero}`
                3. **Monitora** lo stato nella pagina Fatture
                """
                )

                return True

            except Exception as e:
                st.error(f"Errore nella creazione della fattura: {str(e)}")
                return False

    return False


def main() -> None:
    """Main page function."""
    st.set_page_config(page_title="Crea Fattura - OpenFatture", page_icon="✏️", layout="wide")

    st.title("✏️ Creazione Fattura Guidata")

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
            if st.button("⬅️ Indietro", use_container_width=True):
                wizard_state["current_step"] = current_step - 1
                st.rerun()

    with col3:
        if current_step < total_steps:
            step_function = steps[current_step - 1]
            if step_function(wizard_state):
                if st.button("Avanti ➡️", use_container_width=True):
                    wizard_state["current_step"] = current_step + 1
                    st.rerun()
        else:
            # Final step
            step_function = steps[current_step - 1]
            step_completed = step_function(wizard_state)
            if step_completed:
                st.success("🎉 Fattura creata con successo!")
                if st.button("🔄 Crea un'altra fattura", use_container_width=True):
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
