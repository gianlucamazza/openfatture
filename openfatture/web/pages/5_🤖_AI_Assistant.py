"""AI Assistant page with chat, description generator, and tax advisor.

Provides interactive AI tools for invoice management and tax compliance.
"""

import streamlit as st
from openfatture.web.services.ai_service import get_ai_service
from openfatture.web.utils.state import (
    init_conversation_history,
    clear_conversation_history,
    init_state,
)

st.set_page_config(page_title="AI Assistant - OpenFatture", page_icon="🤖", layout="wide")

# Title
st.title("🤖 AI Assistant")
st.markdown("### Assistente Intelligente per Fatturazione e Fisco")

# Initialize AI service
ai_service = get_ai_service()

# Check if AI is available
if not ai_service.is_available():
    st.error(
        """
        ⚠️ **AI non configurato**

        Per abilitare l'AI Assistant:
        1. Configura le credenziali nel file `.env`
        2. Imposta `AI_PROVIDER` (openai/anthropic/ollama)
        3. Imposta `AI_API_KEY` (se necessario)
        4. Riavvia l'applicazione

        Consulta `docs/CONFIGURATION.md` per i dettagli.
        """
    )
    st.stop()

# Tab selection
tab1, tab2, tab3 = st.tabs(["💬 Chat Assistente", "📝 Genera Descrizione", "🧾 Suggerimento IVA"])

# =============================================================================
# TAB 1: Chat Assistant
# =============================================================================
with tab1:
    st.markdown("### 💬 Chat Interattivo")
    st.markdown(
        """
        Chatta con l'assistente AI per:
        - Domande su fatturazione e normativa
        - Consigli fiscali e IVA
        - Gestione pagamenti e scadenze
        - Consulenza generale business
        """
    )

    # Initialize conversation history
    history = init_conversation_history()

    # Clear chat button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Cancella", use_container_width=True):
            clear_conversation_history()
            st.rerun()

    # Display chat history
    st.markdown("---")

    chat_container = st.container()

    with chat_container:
        for msg in history:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)

    # Chat input
    user_input = st.chat_input("Scrivi il tuo messaggio...", key="chat_input")

    if user_input:
        # Add user message to history
        history.append({"role": "user", "content": user_input})

        # Display user message
        with chat_container:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)

        # Get AI response with streaming
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                response_placeholder = st.empty()
                full_response = ""

                # Stream response
                with st.spinner("Pensando..."):
                    try:
                        import asyncio

                        async def stream_chat():
                            chunks = []
                            async for chunk in ai_service.chat_stream(user_input, history[:-1]):
                                chunks.append(chunk)
                                response_placeholder.markdown("".join(chunks) + "▌")
                            return "".join(chunks)

                        full_response = asyncio.run(stream_chat())
                        response_placeholder.markdown(full_response)

                    except Exception as e:
                        full_response = f"❌ Errore: {e}"
                        response_placeholder.error(full_response)

        # Add assistant response to history
        history.append({"role": "assistant", "content": full_response})

        st.rerun()

# =============================================================================
# TAB 2: Invoice Description Generator
# =============================================================================
with tab2:
    st.markdown("### 📝 Genera Descrizione Fattura")
    st.markdown(
        """
        Genera descrizioni professionali per le tue fatture usando l'AI.
        Fornisci informazioni sul servizio e ottieni una descrizione dettagliata.
        """
    )

    with st.form("description_form"):
        servizio = st.text_area(
            "Servizio Fornito *",
            placeholder="es. Consulenza sviluppo web app e-commerce",
            help="Descrivi brevemente il servizio/prodotto",
        )

        col1, col2 = st.columns(2)

        with col1:
            ore = st.number_input(
                "Ore Lavorate",
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=0.5,
                help="Numero ore (opzionale)",
            )

            progetto = st.text_input(
                "Nome Progetto",
                placeholder="es. Progetto E-Commerce XYZ",
                help="Nome del progetto (opzionale)",
            )

        with col2:
            tariffa = st.number_input(
                "Tariffa Oraria (€)",
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=5.0,
                help="Tariffa oraria in euro (opzionale)",
            )

            tecnologie = st.text_input(
                "Tecnologie",
                placeholder="Python, FastAPI, PostgreSQL",
                help="Tecnologie usate, separate da virgola (opzionale)",
            )

        submitted = st.form_submit_button("✨ Genera Descrizione", use_container_width=True)

    if submitted:
        if not servizio:
            st.error("⚠️ Inserisci una descrizione del servizio")
        else:
            with st.spinner("🤖 Generando descrizione professionale..."):
                try:
                    tech_list = (
                        [t.strip() for t in tecnologie.split(",") if t.strip()]
                        if tecnologie
                        else None
                    )

                    response = ai_service.generate_invoice_description(
                        servizio=servizio,
                        ore=ore if ore > 0 else None,
                        tariffa=tariffa if tariffa > 0 else None,
                        progetto=progetto if progetto else None,
                        tecnologie=tech_list,
                    )

                    if response.status.value == "success":
                        st.success("✅ Descrizione generata con successo!")

                        # Display result
                        if response.metadata.get("is_structured"):
                            data = response.metadata["parsed_model"]

                            st.markdown("#### 📄 Descrizione Professionale")
                            st.info(data["descrizione_completa"])

                            if data.get("deliverables"):
                                st.markdown("#### 📦 Deliverables")
                                for item in data["deliverables"]:
                                    st.markdown(f"- {item}")

                            if data.get("competenze"):
                                st.markdown("#### 🔧 Competenze Tecniche")
                                for skill in data["competenze"]:
                                    st.markdown(f"- {skill}")

                            if data.get("durata_ore"):
                                st.markdown(f"**⏱️ Durata:** {data['durata_ore']} ore")

                            if data.get("note"):
                                st.markdown(f"**📌 Note:** {data['note']}")

                        else:
                            st.markdown("#### 📄 Descrizione Generata")
                            st.info(response.content)

                        # Metrics
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("Provider", response.provider)
                        with col_m2:
                            st.metric("Tokens", response.usage.total_tokens)
                        with col_m3:
                            st.metric("Costo", f"${response.usage.estimated_cost_usd:.4f}")

                    else:
                        st.error(f"❌ Errore: {response.error}")

                except Exception as e:
                    st.error(f"❌ Errore durante generazione: {e}")

# =============================================================================
# TAB 3: VAT Suggestion
# =============================================================================
with tab3:
    st.markdown("### 🧾 Suggerimento Aliquota IVA")
    st.markdown(
        """
        Ottieni suggerimenti AI sull'aliquota IVA corretta e il trattamento fiscale
        in base al tipo di servizio/prodotto e al cliente.
        """
    )

    with st.form("vat_form"):
        descrizione = st.text_area(
            "Descrizione Servizio/Prodotto *",
            placeholder="es. Consulenza informatica per sviluppo software gestionale",
            help="Descrivi il servizio o prodotto da fatturare",
        )

        col1, col2 = st.columns(2)

        with col1:
            cliente_pa = st.checkbox(
                "Cliente è Pubblica Amministrazione",
                help="Spunta se il cliente è PA",
            )

            importo = st.number_input(
                "Importo (€)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                help="Importo in euro (opzionale)",
            )

        with col2:
            cliente_estero = st.checkbox(
                "Cliente Estero",
                help="Spunta se il cliente non è residente in Italia",
            )

            if cliente_estero:
                paese = st.text_input(
                    "Paese Cliente",
                    value="",
                    max_chars=2,
                    placeholder="IT, FR, US...",
                    help="Codice ISO paese a 2 lettere",
                )
            else:
                paese = "IT"

        categoria = st.selectbox(
            "Categoria Servizio",
            options=[
                "",
                "Consulenza",
                "Sviluppo Software",
                "Formazione",
                "Design/Grafica",
                "Marketing",
                "Manutenzione",
                "Altro",
            ],
            help="Categoria del servizio (opzionale)",
        )

        submitted_vat = st.form_submit_button(
            "🧾 Ottieni Suggerimento IVA", use_container_width=True
        )

    if submitted_vat:
        if not descrizione:
            st.error("⚠️ Inserisci una descrizione del servizio/prodotto")
        else:
            with st.spinner("🤖 Analizzando trattamento fiscale..."):
                try:
                    response = ai_service.suggest_vat(
                        description=descrizione,
                        cliente_pa=cliente_pa,
                        cliente_estero=cliente_estero,
                        paese_cliente=paese if cliente_estero else "IT",
                        importo=importo if importo > 0 else 0.0,
                        categoria=categoria if categoria else None,
                    )

                    if response.status.value == "success":
                        st.success("✅ Analisi completata!")

                        # Display result
                        if response.metadata.get("is_structured"):
                            data = response.metadata["parsed_model"]

                            # Main tax info
                            st.markdown("#### 📊 Trattamento Fiscale")

                            info_cols = st.columns(3)

                            with info_cols[0]:
                                st.metric("Aliquota IVA", f"{data['aliquota_iva']}%")

                            with info_cols[1]:
                                st.metric(
                                    "Reverse Charge",
                                    "✓ SI" if data["reverse_charge"] else "✗ NO",
                                )

                            with info_cols[2]:
                                confidence_pct = int(data["confidence"] * 100)
                                st.metric("Confidence", f"{confidence_pct}%")

                            if data.get("codice_natura"):
                                st.info(f"**Codice Natura IVA:** {data['codice_natura']}")

                            if data.get("split_payment"):
                                st.warning("⚠️ **Split Payment** applicabile")

                            if data.get("regime_speciale"):
                                st.info(f"**Regime Speciale:** {data['regime_speciale']}")

                            # Explanation
                            st.markdown("#### 📋 Spiegazione")
                            st.markdown(data["spiegazione"])

                            # Legal reference
                            st.markdown("#### 📜 Riferimento Normativo")
                            st.markdown(data["riferimento_normativo"])

                            # Invoice notes
                            if data.get("note_fattura"):
                                st.markdown("#### 📝 Nota per Fattura")
                                st.code(data["note_fattura"])

                            # Recommendations
                            if data.get("raccomandazioni") and len(data["raccomandazioni"]) > 0:
                                st.markdown("#### 💡 Raccomandazioni")
                                for racc in data["raccomandazioni"]:
                                    st.markdown(f"- {racc}")

                        else:
                            st.markdown("#### 📊 Suggerimento")
                            st.info(response.content)

                        # Metrics
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("Provider", response.provider)
                        with col_m2:
                            st.metric("Tokens", response.usage.total_tokens)
                        with col_m3:
                            st.metric("Costo", f"${response.usage.estimated_cost_usd:.4f}")

                    else:
                        st.error(f"❌ Errore: {response.error}")

                except Exception as e:
                    st.error(f"❌ Errore durante analisi: {e}")
                    st.exception(e)

# Info footer
st.markdown("---")
st.info(
    """
    **💡 Suggerimento:** L'AI Assistant è uno strumento di supporto. Le informazioni fornite
    dovrebbero essere sempre verificate con un commercialista o consulente fiscale per garantire
    la conformità alle normative vigenti.
    """
)
