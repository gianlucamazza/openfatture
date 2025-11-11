"""AI Assistant page with chat, description generator, and tax advisor.

Provides interactive AI tools for invoice management and tax compliance.
"""

import time
from collections.abc import Callable
from typing import Any

import streamlit as st

from openfatture.web.services.ai_service import get_ai_service
from openfatture.web.services.custom_commands_service import get_custom_commands_service
from openfatture.web.services.feedback_service import get_feedback_service
from openfatture.web.services.session_service import get_session_service
from openfatture.web.services.voice_service import get_voice_service
from openfatture.web.utils.async_helpers import run_async
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
            time.sleep(delay)

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


def handle_slash_command(
    user_input: str, custom_commands_service: Any
) -> tuple[str | None, str | None]:
    """
    Handle slash commands in chat input.

    Args:
        user_input: User input that may contain a slash command
        custom_commands_service: Custom commands service instance

    Returns:
        Tuple of (expanded_message, command_feedback)
        - expanded_message: The expanded command or None if not a command
        - command_feedback: User feedback message about command execution
    """
    if not user_input.startswith("/"):
        return None, None

    # Parse command
    parts = user_input.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # Handle built-in commands
    if command == "/help":
        feedback = """
**🤖 Comandi Disponibili:**

**Built-in:**
- `/help` - Mostra questo messaggio
- `/tools` - Lista strumenti AI disponibili
- `/stats` - Statistiche conversazione corrente
- `/custom` - Lista comandi personalizzati
- `/reload` - Ricarica comandi da disco
- `/clear` - Cancella cronologia chat

**Personalizzati:**
Crea comandi in `~/.openfatture/commands/*.yaml`

**Esempi:**
- "Come creo una fattura?"
- "Qual è l'aliquota IVA per il web design?"
- "Mostra le fatture di questo mese"
        """.strip()
        return None, feedback

    elif command == "/tools":
        # Show available AI tools
        tools_info = """
**🔧 Strumenti AI Disponibili:**

**Ricerca e Consultazione:**
- Ricerca fatture per cliente, data, importo
- Statistiche fatturato e pagamenti
- Consultazione normativa fiscale

**Azioni Disponibili:**
- Creazione descrizioni fatture professionali
- Suggerimento aliquote IVA corrette
- Analisi compliance fatturazione

**Integrazione Dati:**
- Accesso database clienti e prodotti
- Cronologia pagamenti e scadenze
- Report e analytics business
        """.strip()
        return None, tools_info

    elif command == "/stats":
        # Show conversation statistics
        total_messages = len(history)
        user_messages = len([msg for msg in history if msg["role"] == "user"])
        assistant_messages = len([msg for msg in history if msg["role"] == "assistant"])

        # Calculate approximate token usage (rough estimate)
        total_chars = sum(len(msg["content"]) for msg in history)
        estimated_tokens = total_chars // 4  # Rough approximation

        feedback = f"""
**📊 Statistiche Conversazione:**

- **Messaggi totali:** {total_messages}
- **Tuo messaggi:** {user_messages}
- **Risposte AI:** {assistant_messages}
- **Caratteri totali:** {total_chars:,}
- **Token stimati:** {estimated_tokens:,}

**💡 Suggerimenti:**
- Usa `/clear` per ricominciare da capo
- Salva conversazioni importanti con 💾 Salva
        """.strip()
        return None, feedback

    elif command == "/custom":
        commands = custom_commands_service.list_commands()
        if not commands:
            feedback = "📝 **Nessun comando personalizzato trovato**\n\nCrea comandi in `~/.openfatture/commands/*.yaml`"
        else:
            feedback = f"📝 **Comandi Personalizzati ({len(commands)}):**\n\n"
            for cmd in commands:
                aliases = f" ({', '.join(cmd['aliases'])})" if cmd["aliases"] else ""
                feedback += f"- `/{cmd['name']}`{aliases}: {cmd['description']}\n"
            feedback += "\n💡 Usa `/help` per vedere tutti i comandi"
        return None, feedback

    elif command == "/reload":
        try:
            result = custom_commands_service.reload_commands()
            feedback = f"🔄 **Comandi ricaricati:** {result['old_count']} → {result['new_count']} ({result['added']} aggiunti, {result['removed']} rimossi)"
        except Exception as e:
            feedback = f"❌ **Errore ricarica:** {str(e)}"
        return None, feedback

    elif command == "/clear":
        # This will be handled by the clear button, just show feedback
        return None, "🗑️ **Cronologia cancellata**\n\nLa conversazione è stata azzerata."

    # Handle custom commands
    elif custom_commands_service.has_command(command):
        try:
            expanded = custom_commands_service.execute_command(command, args)
            feedback = f"🔧 **Comando espanso:** `/{command}` → {len(expanded)} caratteri"
            return expanded, feedback
        except ValueError as e:
            return None, f"❌ **Errore comando:** {str(e)}"

    # Unknown command
    else:
        return (
            None,
            f"❓ **Comando sconosciuto:** `{command}`\n\nUsa `/help` per vedere i comandi disponibili",
        )


st.set_page_config(page_title="AI Assistant - OpenFatture", page_icon="🤖", layout="wide")

# Title
st.title("🤖 AI Assistant")
st.markdown("### Assistente Intelligente per Fatturazione e Fisco")

# Initialize services
ai_service = get_ai_service()
custom_commands_service = get_custom_commands_service()
session_service = get_session_service()
feedback_service = get_feedback_service()
voice_service = get_voice_service()

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
tab1, tab2, tab3, tab4 = st.tabs(
    ["💬 Chat Assistente", "📝 Genera Descrizione", "🧾 Suggerimento IVA", "🎤 Voice Chat"]
)

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

    # Action buttons
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col2:
        if st.button("💾 Salva", use_container_width=True, help="Salva conversazione"):
            try:
                session_id = session_service.save_session(
                    {"title": f"Chat {len(history) // 2} messaggi", "messages": history}
                )
                if session_id:
                    st.success(f"✅ Salvata: {session_id[:8]}...")
                    st.rerun()
                else:
                    st.error("❌ Errore salvataggio")
            except Exception as e:
                st.error(f"❌ Errore: {str(e)}")
    with col3:
        if st.button("🔄 Reload", use_container_width=True, help="Ricarica comandi personalizzati"):
            try:
                result = custom_commands_service.reload_commands()
                st.success(f"✅ Ricaricati: {result['new_count']} comandi")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Errore: {str(e)}")
    with col4:
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

    # Custom commands info
    with st.expander("📝 Comandi Personalizzati", expanded=False):
        commands = custom_commands_service.list_commands()
        if not commands:
            st.info(
                "Nessun comando personalizzato trovato. Crea comandi in `~/.openfatture/commands/*.yaml`"
            )
        else:
            st.markdown(f"**{len(commands)} comandi disponibili:**")
            for cmd in commands:
                aliases = f" ({', '.join(cmd['aliases'])})" if cmd["aliases"] else ""
                with st.expander(f"🤖 /{cmd['name']}{aliases} - {cmd['category']}"):
                    st.markdown(f"**Descrizione:** {cmd['description']}")
                    if cmd["examples"]:
                        st.markdown("**Esempi:**")
                        for example in cmd["examples"]:
                            st.code(example)
                    if cmd["author"]:
                        st.markdown(f"**Autore:** {cmd['author']}")
                    if cmd["version"]:
                        st.markdown(f"**Versione:** {cmd['version']}")

    # Session management
    with st.expander("💾 Sessioni Salvate", expanded=False):
        sessions = session_service.list_sessions()

        if not sessions:
            st.info(
                "Nessuna sessione salvata. Usa il pulsante 💾 Salva per salvare la conversazione corrente."
            )
        else:
            st.markdown(f"**{len(sessions)} sessioni disponibili:**")

            # Session list with load/delete buttons
            for session in sorted(sessions, key=lambda x: x["updated_at"], reverse=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"**{session['title']}**")
                    st.caption(
                        f"ID: {session['id'][:8]}... • {session['message_count']} msg • {session['updated_at'].strftime('%d/%m/%Y %H:%M')}"
                    )

                with col2:
                    if st.button(
                        "📂 Carica", key=f"load_{session['id']}", use_container_width=True
                    ):
                        try:
                            session_data = session_service.load_session(session["id"])
                            if session_data and session_data["messages"]:
                                # Clear current history and load new one
                                st.session_state.conversation_history = session_data["messages"]
                                st.success(f"✅ Caricata sessione: {session['title']}")
                                st.rerun()
                            else:
                                st.error("❌ Sessione vuota o corrotta")
                        except Exception as e:
                            st.error(f"❌ Errore caricamento: {str(e)}")

                with col3:
                    if st.button(
                        "📝 Rinomina", key=f"rename_{session['id']}", use_container_width=True
                    ):
                        # This would need a text input - simplified for now
                        st.info("Funzionalità rinomina da implementare")

                with col4:
                    if st.button(
                        "🗑️ Elimina", key=f"delete_{session['id']}", use_container_width=True
                    ):
                        try:
                            if session_service.delete_session(session["id"]):
                                st.success("✅ Sessione eliminata")
                                st.rerun()
                            else:
                                st.error("❌ Errore eliminazione")
                        except Exception as e:
                            st.error(f"❌ Errore: {str(e)}")

    # Chat input
    user_input = st.chat_input("Scrivi il tuo messaggio o usa /comando...", key="chat_input")

    if user_input:
        # Handle slash commands first
        expanded_message, command_feedback = handle_slash_command(
            user_input, custom_commands_service
        )

        if command_feedback:
            # This is a command - show feedback and don't send to AI
            with chat_container:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(command_feedback)
            # Add to history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": command_feedback})
            st.rerun()
            st.stop()

        # Use expanded message if command was processed, otherwise use original input
        final_input = expanded_message if expanded_message else user_input

        # Process uploaded files if any
        attached_files = []
        if "uploaded_files" in st.session_state and st.session_state.uploaded_files:
            attached_files = st.session_state.uploaded_files.copy()
            # Clear uploaded files after processing
            st.session_state.uploaded_files = []

        # Prepare message content with file information
        message_content = final_input
        if attached_files:
            file_info_parts = ["\n\n📎 File allegati:"]

            for file_data in attached_files:
                file_name = file_data["details"]["name"]
                file_type = file_data["details"]["type"]
                file_size = file_data["details"]["size"]

                # Basic file type detection and content hints
                if file_type == "text/plain":
                    try:
                        content = str(file_data["file"].read(), "utf-8")
                        preview = content[:200] + "..." if len(content) > 200 else content
                        file_info_parts.append(f"- **{file_name}** (testo): {preview}")
                    except Exception:
                        file_info_parts.append(f"- **{file_name}** (testo, {file_size} bytes)")
                elif file_type == "application/pdf":
                    file_info_parts.append(
                        f"- **{file_name}** (PDF, {file_size} bytes) - Contenuto da analizzare"
                    )
                elif file_type.startswith("image/"):
                    file_info_parts.append(
                        f"- **{file_name}** (immagine {file_type.split('/')[1]}, {file_size} bytes) - Testo da estrarre via OCR"
                    )
                else:
                    file_info_parts.append(f"- **{file_name}** ({file_type}, {file_size} bytes)")

            message_content += "\n".join(file_info_parts)
            message_content += (
                "\n\n💡 L'AI analizzerà questi file per fornire una risposta più precisa."
            )

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
                            tool_events = []

                            # Process streaming with tool calling visualization
                            async for chunk_type, chunk_data in ai_service.chat_stream(
                                message_content, history[:-1]
                            ):
                                if chunk_type == "text":
                                    # Regular text chunk
                                    chunks.append(chunk_data)
                                    current_text = "".join(chunks)

                                    # Add tool events to display
                                    tool_display = ""
                                    if tool_events:
                                        tool_display = "\n\n" + "\n".join(
                                            [
                                                f"🔧 **{event.data.get('tool_name', 'Tool')}:** {event.data.get('result', event.data.get('error', ''))}"
                                                for event in tool_events[-3:]  # Show last 3 events
                                            ]
                                        )

                                    response_placeholder.markdown(current_text + tool_display + "▌")

                                elif chunk_type == "tool_event":
                                    # Tool calling event
                                    tool_events.append(chunk_data)

                                    # Update display with tool event
                                    current_text = "".join(chunks)
                                    tool_display = "\n\n" + "\n".join(
                                        [
                                            f"🔧 **{event.data.get('tool_name', 'Tool')}:** {event.data.get('result', event.data.get('error', ''))}"
                                            for event in tool_events[-3:]  # Show last 3 events
                                        ]
                                    )

                                    response_placeholder.markdown(current_text + tool_display + "▌")

                            return "".join(chunks)

                        # Execute with retry logic (Best Practice 2025: use run_async)
                        full_response = run_async(
                            retry_with_backoff(
                                stream_chat,
                                max_retries=2,  # Allow 2 retries for chat
                                base_delay=1.0,
                                max_delay=5.0,
                            )
                        )
                        response_placeholder.markdown(full_response)

                        # Add feedback buttons after successful response
                        if full_response and not full_response.startswith("❌"):
                            st.markdown("---")
                            feedback_col1, feedback_col2, feedback_col3 = st.columns([1, 1, 2])

                            with feedback_col1:
                                if st.button(
                                    "👍 Buono", key=f"good_{len(history)}", use_container_width=True
                                ):
                                    success = feedback_service.submit_feedback(
                                        agent_type="chat_agent",
                                        rating=5,
                                        user_comment="Buona risposta",
                                        original_text=full_response,
                                    )
                                    if success:
                                        st.success("✅ Grazie per il feedback!")
                                    else:
                                        st.error("❌ Errore nell'invio del feedback")

                            with feedback_col2:
                                if st.button(
                                    "👎 Scarso", key=f"bad_{len(history)}", use_container_width=True
                                ):
                                    success = feedback_service.submit_feedback(
                                        agent_type="chat_agent",
                                        rating=2,
                                        user_comment="Risposta insoddisfacente",
                                        original_text=full_response,
                                    )
                                    if success:
                                        st.success("✅ Grazie per il feedback!")
                                    else:
                                        st.error("❌ Errore nell'invio del feedback")

                            with feedback_col3:
                                with st.popover("💬 Commento"):
                                    user_comment = st.text_area(
                                        "Lascia un commento sulla risposta:",
                                        height=100,
                                        key=f"comment_{len(history)}",
                                    )
                                    if st.button(
                                        "Invia Commento", key=f"submit_comment_{len(history)}"
                                    ):
                                        if user_comment.strip():
                                            success = feedback_service.submit_feedback(
                                                agent_type="chat_agent",
                                                rating=3,  # Neutral rating for comments
                                                user_comment=user_comment.strip(),
                                                original_text=full_response,
                                            )
                                            if success:
                                                st.success("✅ Commento inviato!")
                                            else:
                                                st.error("❌ Errore nell'invio del commento")
                                        else:
                                            st.warning("Inserisci un commento")

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

                    # Execute with retry logic (Best Practice 2025: use run_async)
                    response = run_async(
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

# =============================================================================
# TAB 4: Voice Chat
# =============================================================================
with tab4:
    st.markdown("### 🎤 Chat Vocale con AI")

    # Check if voice is available
    if not voice_service.is_available():
        st.warning(
            """
            ⚠️ **Voice Chat non configurato**

            Per abilitare il Voice Chat:
            1. Configura `OPENAI_API_KEY` nel file `.env`
            2. Imposta `OPENFATTURE_VOICE_ENABLED=true`
            3. Riavvia l'applicazione

            Consulta la documentazione per i dettagli.
            """
        )
        st.stop()

    st.markdown(
        """
        Parla con l'assistente AI usando la tua voce:
        - 🎤 Registra la tua domanda
        - 🤖 L'AI la trascrive e risponde
        - 🔊 Ascolta la risposta vocale
        - 💬 Supporta conversazioni con contesto
        """
    )

    # Voice configuration info
    with st.expander("⚙️ Configurazione Voice", expanded=False):
        voice_config = voice_service.get_config()

        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            st.metric("Provider", voice_config.get("provider", "N/A"))
        with col_v2:
            st.metric("STT Model", voice_config.get("stt_model", "N/A"))
        with col_v3:
            st.metric("TTS Voice", voice_config.get("tts_voice", "N/A"))

        st.markdown(f"**TTS Model:** {voice_config.get('tts_model', 'N/A')}")
        st.markdown(f"**TTS Speed:** {voice_config.get('tts_speed', 1.0)}x")
        st.markdown(f"**TTS Format:** {voice_config.get('tts_format', 'mp3')}")
        st.markdown(f"**Streaming:** {'✓' if voice_config.get('streaming_enabled') else '✗'}")

    # Initialize voice conversation history
    if "voice_conversation_history" not in st.session_state:
        st.session_state.voice_conversation_history = []

    voice_history = st.session_state.voice_conversation_history

    # Action buttons
    voice_col1, voice_col2 = st.columns([4, 1])
    with voice_col2:
        if st.button("🗑️ Cancella Voice", use_container_width=True):
            st.session_state.voice_conversation_history = []
            st.rerun()

    # Display voice conversation history
    if voice_history:
        st.markdown("### 📜 Cronologia Conversazione")
        with st.container():
            for i, interaction in enumerate(voice_history):
                # User message
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"**Tu:** {interaction['transcription']}")
                    if interaction.get("language"):
                        st.caption(f"Lingua rilevata: {interaction['language']}")

                # Assistant response
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(f"**Assistente:** {interaction['response']}")

                    # Show audio if available
                    if interaction.get("audio_data"):
                        st.audio(interaction["audio_data"], format="audio/mp3")

                    # Metrics
                    if interaction.get("metrics"):
                        metrics = interaction["metrics"]
                        metric_cols = st.columns(4)
                        with metric_cols[0]:
                            st.caption(f"STT: {metrics.get('stt_ms', 0):.0f}ms")
                        with metric_cols[1]:
                            st.caption(f"LLM: {metrics.get('llm_ms', 0):.0f}ms")
                        with metric_cols[2]:
                            st.caption(f"TTS: {metrics.get('tts_ms', 0):.0f}ms")
                        with metric_cols[3]:
                            st.caption(f"Totale: {metrics.get('total_ms', 0):.0f}ms")
    else:
        st.info("👋 Nessuna conversazione vocale ancora. Registra la tua prima domanda!")

    st.markdown("---")

    # Audio input
    st.markdown("### 🎙️ Registra la tua voce")

    # Streamlit audio input (available from Streamlit 1.28+)
    audio_input = st.audio_input(
        "Premi il pulsante per registrare",
        key="voice_chat_audio_input",
        help="Parla chiaramente nel microfono. La registrazione si ferma automaticamente dopo il silenzio.",
    )

    if audio_input is not None:
        st.success(f"✅ Audio registrato: {audio_input.size} bytes")

        # Show audio preview
        st.audio(audio_input, format="audio/wav")

        # Process audio button
        if st.button("🚀 Invia e Processa", type="primary", use_container_width=True):
            with st.spinner("🤖 Processando il tuo messaggio vocale..."):
                try:
                    # Read audio bytes
                    audio_bytes = audio_input.read()
                    audio_input.seek(0)  # Reset for reuse

                    # Build conversation history for context
                    history_for_context = []
                    for interaction in voice_history:
                        history_for_context.append(
                            {"role": "user", "content": interaction["transcription"]}
                        )
                        history_for_context.append(
                            {"role": "assistant", "content": interaction["response"]}
                        )

                    # Process voice input
                    response = voice_service.process_voice_input(
                        audio_bytes=audio_bytes,
                        conversation_history=history_for_context if history_for_context else None,
                    )

                    # Store interaction in history
                    interaction = {
                        "transcription": response.transcription.text,
                        "language": response.transcription.language,
                        "response": response.llm_response,
                        "audio_data": response.synthesis.audio_data if response.synthesis else None,
                        "metrics": {
                            "stt_ms": response.stt_latency_ms,
                            "llm_ms": response.llm_latency_ms,
                            "tts_ms": response.tts_latency_ms,
                            "total_ms": response.total_latency_ms,
                        },
                    }
                    voice_history.append(interaction)

                    # Show success and results
                    st.success("✅ Messaggio vocale processato con successo!")

                    # Display results
                    result_col1, result_col2 = st.columns(2)

                    with result_col1:
                        st.markdown("#### 📝 Trascrizione")
                        st.info(f"**Tu:** {response.transcription.text}")
                        st.caption(f"Lingua: {response.transcription.language}")

                    with result_col2:
                        st.markdown("#### 🤖 Risposta AI")
                        st.success(f"**Assistente:** {response.llm_response}")

                    # Audio response
                    if response.synthesis:
                        st.markdown("#### 🔊 Risposta Vocale")
                        st.audio(response.synthesis.audio_data, format="audio/mp3")

                    # Metrics
                    st.markdown("#### 📊 Metriche")
                    metrics_cols = st.columns(4)
                    with metrics_cols[0]:
                        st.metric("STT", f"{response.stt_latency_ms:.0f}ms")
                    with metrics_cols[1]:
                        st.metric("LLM", f"{response.llm_latency_ms:.0f}ms")
                    with metrics_cols[2]:
                        st.metric("TTS", f"{response.tts_latency_ms or 0:.0f}ms")
                    with metrics_cols[3]:
                        st.metric("Totale", f"{response.total_latency_ms:.0f}ms")

                    # Additional info
                    if response.llm_metadata:
                        with st.expander("ℹ️ Dettagli Tecnici"):
                            st.json(
                                {
                                    "provider": response.llm_metadata.get("provider"),
                                    "model": response.llm_metadata.get("model"),
                                    "tokens": response.llm_metadata.get("tokens"),
                                    "cost_usd": response.llm_metadata.get("cost_usd"),
                                }
                            )

                    # Rerun to refresh history display
                    st.rerun()

                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Errore durante il processamento: {error_msg}")

                    # Show additional help
                    if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                        st.info("💡 Suggerimento: Verifica la tua connessione internet")
                    elif "auth" in error_msg.lower() or "key" in error_msg.lower():
                        st.info(
                            "💡 Suggerimento: Verifica le impostazioni API nelle configurazioni"
                        )
                    elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                        st.info(
                            "💡 Suggerimento: Limite di richieste raggiunto. Riprova tra qualche minuto"
                        )

                    st.exception(e)

    # Help section
    with st.expander("❓ Come funziona", expanded=False):
        st.markdown(
            """
        **Workflow Voice Chat:**

        1. **🎤 Registrazione**: Premi il pulsante e parla nel microfono
        2. **📝 Trascrizione (STT)**: OpenAI Whisper converte la voce in testo
        3. **🤖 Elaborazione (LLM)**: L'AI comprende e genera una risposta
        4. **🔊 Sintesi (TTS)**: OpenAI TTS converte la risposta in audio
        5. **▶️ Riproduzione**: Ascolta la risposta vocale

        **Supporto Lingue:**
        - Rilevamento automatico tra 100+ lingue
        - Italiano, Inglese, Francese, Tedesco, Spagnolo e molte altre

        **Costi Stimati:**
        - STT (Whisper): ~$0.006 per minuto di audio
        - TTS: ~$0.015 per 1.000 caratteri (tts-1) o ~$0.030 (tts-1-hd)
        - LLM: Prezzo standard del modello configurato

        **Requisiti:**
        - Microfono funzionante
        - Browser moderno (Chrome, Firefox, Safari, Edge)
        - Connessione internet stabile
        """
        )

# Info footer
st.markdown("---")
st.info(
    """
    **💡 Suggerimento:** L'AI Assistant è uno strumento di supporto. Le informazioni fornite
    dovrebbero essere sempre verificate con un commercialista o consulente fiscale per garantire
    la conformità alle normative vigenti.
    """
)
