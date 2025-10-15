"""AI Assistant page with chat, description generator, and tax advisor.

Provides interactive AI tools for invoice management and tax compliance.
"""

import asyncio
from collections.abc import Callable
from typing import Any

import streamlit as st

from openfatture.web.services.ai_service import get_ai_service
from openfatture.web.utils.state import (
    clear_conversation_history,
    init_conversation_history,
)


async def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        backoff_factor: Factor to multiply delay by on each retry

    Returns:
        Result of the function call

    Raises:
        Exception: Last exception if all retries fail
    """
    last_exception = None
    delay = base_delay

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                # Last attempt failed
                raise e

            # Calculate delay with exponential backoff
            delay = min(delay * backoff_factor, max_delay)

            # Show retry message to user
            retry_msg = (
                f"🔄 Tentativo {attempt + 1}/{max_retries + 1} fallito. Riprovo tra {delay:.1f}s..."
            )
            st.warning(retry_msg)

            # Wait before retry
            await asyncio.sleep(delay)

    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("Retry logic failed with unknown error")


def handle_chat_error(error: Exception, context: str = "chat") -> str:
    """
    Handle chat-related errors with user-friendly messages.

    Args:
        error: The exception that occurred
        context: Context where the error occurred

    Returns:
        User-friendly error message
    """
    error_str = str(error).lower()

    # Network/API errors
    if any(keyword in error_str for keyword in ["connection", "timeout", "network", "api"]):
        return "🌐 Errore di connessione. Verifica la tua connessione internet e riprova."

    # Authentication errors
    elif any(keyword in error_str for keyword in ["auth", "token", "key", "unauthorized"]):
        return "🔐 Errore di autenticazione. Verifica le tue credenziali AI."

    # Rate limiting
    elif any(keyword in error_str for keyword in ["rate", "limit", "quota"]):
        return "⏱️ Limite di richieste raggiunto. Riprova tra qualche minuto."

    # Model/service unavailable
    elif any(keyword in error_str for keyword in ["model", "service", "unavailable"]):
        return "🚫 Servizio temporaneamente non disponibile. Riprova più tardi."

    # Generic error
    else:
        return f"❌ Errore imprevisto: {str(error)[:100]}..."


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

    # File upload section
    with st.expander("📎 Allega File (Opzionale)", expanded=False):
        uploaded_file = st.file_uploader(
            "Carica un documento per discuterne con l'AI",
            type=["pdf", "txt", "md", "png", "jpg", "jpeg"],
            help="Supporta PDF, testo, immagini e altri documenti",
            key="file_upload",
        )

        if uploaded_file:
            file_details = {
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "size": uploaded_file.size,
            }
            st.success(f"📄 File caricato: {file_details['name']} ({file_details['size']} bytes)")

            # Store file in session state for processing
            if "uploaded_files" not in st.session_state:
                st.session_state.uploaded_files = []
            st.session_state.uploaded_files.append({"file": uploaded_file, "details": file_details})
            st.rerun()  # Refresh to show updated file list

    # Show currently uploaded files
    if "uploaded_files" in st.session_state and st.session_state.uploaded_files:
        st.markdown("### 📎 File Allegati")
        cols = st.columns([3, 1])

        with cols[0]:
            for i, file_data in enumerate(st.session_state.uploaded_files):
                file_type = file_data["details"]["type"]
                if file_type.startswith("image/"):
                    st.image(file_data["file"], caption=file_data["details"]["name"], width=150)
                else:
                    st.info(
                        f"📄 {file_data['details']['name']} ({file_data['details']['size']} bytes)"
                    )

        with cols[1]:
            if st.button("🗑️ Cancella Tutti", use_container_width=True):
                st.session_state.uploaded_files = []
                st.success("File cancellati!")
                st.rerun()

    # Chat input
    user_input = st.chat_input("Scrivi il tuo messaggio...", key="chat_input")

    if user_input:
        # Process uploaded files if any
        attached_files = []
        if "uploaded_files" in st.session_state and st.session_state.uploaded_files:
            attached_files = st.session_state.uploaded_files.copy()
            # Clear uploaded files after processing
            st.session_state.uploaded_files = []

        # Prepare message content with file information
        message_content = user_input
        if attached_files:
            file_info = "\n\n📎 File allegati:\n" + "\n".join(
                [f"- {f['details']['name']} ({f['details']['type']})" for f in attached_files]
            )
            message_content += file_info

        # Add user message to history
        history.append({"role": "user", "content": message_content})

        # Display user message
        with chat_container:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(message_content)

                # Show file attachments
                if attached_files:
                    st.markdown("**Allegati:**")
                    for file_data in attached_files:
                        file_type = file_data["details"]["type"]
                        if file_type.startswith("image/"):
                            st.image(
                                file_data["file"], caption=file_data["details"]["name"], width=200
                            )
                        else:
                            st.info(
                                f"📄 {file_data['details']['name']} ({file_data['details']['size']} bytes)"
                            )

        # Get AI response with streaming
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                response_placeholder = st.empty()
                full_response = ""

                # Stream response with retry logic
                with st.spinner("Pensando..."):
                    try:

                        async def stream_chat():
                            chunks = []
                            # For now, pass the message with file info as text
                            # Future enhancement: implement proper file processing
                            async for chunk in ai_service.chat_stream(
                                message_content, history[:-1]
                            ):
                                chunks.append(chunk)
                                response_placeholder.markdown("".join(chunks) + "▌")
                            return "".join(chunks)

                        # Execute with retry logic
                        full_response = asyncio.run(
                            retry_with_backoff(
                                stream_chat,
                                max_retries=2,  # Allow 2 retries for chat
                                base_delay=1.0,
                                max_delay=5.0,
                            )
                        )
                        response_placeholder.markdown(full_response)

                    except Exception as e:
                        error_message = handle_chat_error(e, "chat_streaming")
                        full_response = error_message
                        response_placeholder.error(error_message)

                        # Show additional help for common errors
                        if "connessione" in error_message.lower():
                            st.info("💡 Suggerimento: Controlla la tua connessione internet")
                        elif "autenticazione" in error_message.lower():
                            st.info("💡 Suggerimento: Verifica le impostazioni AI nelle preferenze")

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

                    async def generate_description():
                        tech_list = (
                            [t.strip() for t in tecnologie.split(",") if t.strip()]
                            if tecnologie
                            else None
                        )

                        return ai_service.generate_invoice_description(
                            servizio=servizio,
                            ore=ore if ore > 0 else None,
                            tariffa=tariffa if tariffa > 0 else None,
                            progetto=progetto if progetto else None,
                            tecnologie=tech_list,
                        )

                    # Execute with retry logic
                    response = asyncio.run(
                        retry_with_backoff(
                            generate_description,
                            max_retries=2,  # Allow 2 retries for description generation
                            base_delay=1.0,
                            max_delay=3.0,
                        )
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
                        error_message = handle_chat_error(
                            Exception(response.error), "description_generation"
                        )
                        st.error(error_message)

                except Exception as e:
                    error_message = handle_chat_error(e, "description_generation")
                    st.error(error_message)

                    # Show additional help for common errors
                    if "connessione" in error_message.lower():
                        st.info("💡 Suggerimento: Controlla la tua connessione internet")
                    elif "autenticazione" in error_message.lower():
                        st.info("💡 Suggerimento: Verifica le impostazioni AI nelle preferenze")

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
