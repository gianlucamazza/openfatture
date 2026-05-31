"""Tab render functions for the AI Assistant page.

Each ``render_*_tab`` function contains exactly the body of the corresponding
``with tabN:`` block from the original ``5_🤖_AI_Assistant.py`` page. The page
itself is now thin and simply calls these inside the relevant tab context.

Services and helpers are passed as parameters so the functions don't rely on
module-level globals defined by the page script.
"""

from typing import Any

import streamlit as st

from openfatture.web.pages._ai_assistant.helpers import (
    handle_chat_error,
    handle_slash_command,
    retry_with_backoff,
)
from openfatture.web.utils.async_helpers import run_async
from openfatture.web.utils.i18n import get_translator
from openfatture.web.utils.state import (
    clear_conversation_history,
    init_conversation_history,
)

# Initialize translator (same instance/interface used by the page)
t = get_translator()


def render_chat_tab(
    ai_service: Any,
    custom_commands_service: Any,
    session_service: Any,
    feedback_service: Any,
) -> None:
    """Render the Chat Assistant tab (original ``with tab1:`` body)."""
    st.markdown(f"### 💬 {t('page-ai-chat-title')}")
    st.markdown(t("page-ai-chat-description"))

    # Initialize conversation history
    history = init_conversation_history()

    # Action buttons
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col2:
        if st.button(
            f"💾 {t('page-ai-chat-save')}",
            use_container_width=True,
            help=t("page-ai-chat-save-help"),
        ):
            try:
                session_id = session_service.save_session(
                    {
                        "title": t("page-ai-chat-session-title", count=len(history) // 2),
                        "messages": history,
                    }
                )
                if session_id:
                    st.success(t("page-ai-chat-saved", session_id=session_id[:8]))
                    st.rerun()
                else:
                    st.error(t("page-ai-chat-save-error"))
            except Exception as e:
                st.error(t("page-ai-error-generic", error=str(e)))
    with col3:
        if st.button(
            f"🔄 {t('page-ai-chat-reload')}",
            use_container_width=True,
            help=t("page-ai-chat-reload-help"),
        ):
            try:
                result = custom_commands_service.reload_commands()
                st.success(t("page-ai-chat-reloaded", count=result["new_count"]))
                st.rerun()
            except Exception as e:
                st.error(t("page-ai-error-generic", error=str(e)))
    with col4:
        if st.button(f"🗑️ {t('page-ai-chat-clear')}", use_container_width=True):
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
    with st.expander(t("page-ai-chat-file-upload-title"), expanded=False):
        uploaded_file = st.file_uploader(
            t("page-ai-chat-file-upload-label"),
            type=["pdf", "txt", "md", "png", "jpg", "jpeg"],
            help=t("page-ai-chat-file-upload-help"),
            key="file_upload",
        )

        if uploaded_file:
            file_details = {
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "size": uploaded_file.size,
            }
            st.success(
                t(
                    "page-ai-chat-file-uploaded",
                    name=file_details["name"],
                    size=file_details["size"],
                )
            )

            # Store file in session state for processing
            if "uploaded_files" not in st.session_state:
                st.session_state.uploaded_files = []
            st.session_state.uploaded_files.append({"file": uploaded_file, "details": file_details})
            st.rerun()  # Refresh to show updated file list

    # Show currently uploaded files
    if "uploaded_files" in st.session_state and st.session_state.uploaded_files:
        st.markdown(f"### 📎 {t('page-ai-chat-files-attached')}")
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
            if st.button(f"🗑️ {t('page-ai-chat-files-clear-all')}", use_container_width=True):
                st.session_state.uploaded_files = []
                st.success(t("page-ai-chat-files-cleared"))
                st.rerun()

    # Custom commands info
    with st.expander(t("page-ai-chat-custom-commands-title"), expanded=False):
        commands = custom_commands_service.list_commands()
        if not commands:
            st.info(t("page-ai-chat-custom-commands-empty"))
        else:
            st.markdown(t("page-ai-chat-custom-commands-count", count=len(commands)))
            for cmd in commands:
                aliases = f" ({', '.join(cmd['aliases'])})" if cmd["aliases"] else ""
                with st.expander(f"🤖 /{cmd['name']}{aliases} - {cmd['category']}"):
                    st.markdown(
                        t("page-ai-chat-custom-commands-description", desc=cmd["description"])
                    )
                    if cmd["examples"]:
                        st.markdown(f"**{t('page-ai-chat-custom-commands-examples')}:**")
                        for example in cmd["examples"]:
                            st.code(example)
                    if cmd["author"]:
                        st.markdown(t("page-ai-chat-custom-commands-author", author=cmd["author"]))
                    if cmd["version"]:
                        st.markdown(
                            t("page-ai-chat-custom-commands-version", version=cmd["version"])
                        )

    # Session management
    with st.expander(t("page-ai-chat-sessions-title"), expanded=False):
        sessions = session_service.list_sessions()

        if not sessions:
            st.info(t("page-ai-chat-sessions-empty"))
        else:
            st.markdown(t("page-ai-chat-sessions-count", count=len(sessions)))

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
                        f"📂 {t('page-ai-chat-sessions-load')}",
                        key=f"load_{session['id']}",
                        use_container_width=True,
                    ):
                        try:
                            session_data = session_service.load_session(session["id"])
                            if session_data and session_data["messages"]:
                                # Clear current history and load new one
                                st.session_state.conversation_history = session_data["messages"]
                                st.success(
                                    t("page-ai-chat-sessions-loaded", title=session["title"])
                                )
                                st.rerun()
                            else:
                                st.error(t("page-ai-chat-sessions-load-error-empty"))
                        except Exception as e:
                            st.error(t("page-ai-chat-sessions-load-error", error=str(e)))

                with col3:
                    if st.button(
                        f"📝 {t('page-ai-chat-sessions-rename')}",
                        key=f"rename_{session['id']}",
                        use_container_width=True,
                    ):
                        # This would need a text input - simplified for now
                        st.info(t("page-ai-chat-sessions-rename-todo"))

                with col4:
                    if st.button(
                        f"🗑️ {t('page-ai-chat-sessions-delete')}",
                        key=f"delete_{session['id']}",
                        use_container_width=True,
                    ):
                        try:
                            if session_service.delete_session(session["id"]):
                                st.success(t("page-ai-chat-sessions-deleted"))
                                st.rerun()
                            else:
                                st.error(t("page-ai-chat-sessions-delete-error"))
                        except Exception as e:
                            st.error(t("page-ai-error-generic", error=str(e)))

    # Chat input
    user_input = st.chat_input(t("page-ai-chat-input-placeholder"), key="chat_input")

    if user_input:
        # Handle slash commands first
        expanded_message, command_feedback = handle_slash_command(
            user_input, custom_commands_service, history
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
            file_info_parts = [f"\n\n📎 {t('page-ai-chat-files-attached')}:"]

            for file_data in attached_files:
                file_name = file_data["details"]["name"]
                file_type = file_data["details"]["type"]
                file_size = file_data["details"]["size"]

                # Basic file type detection and content hints
                if file_type == "text/plain":
                    try:
                        content = str(file_data["file"].read(), "utf-8")
                        preview = content[:200] + "..." if len(content) > 200 else content
                        file_info_parts.append(
                            t(
                                "page-ai-chat-file-text-preview",
                                name=file_name,
                                preview=preview,
                            )
                        )
                    except Exception:
                        file_info_parts.append(
                            t("page-ai-chat-file-text", name=file_name, size=file_size)
                        )
                elif file_type == "application/pdf":
                    file_info_parts.append(
                        t("page-ai-chat-file-pdf", name=file_name, size=file_size)
                    )
                elif file_type.startswith("image/"):
                    file_info_parts.append(
                        t(
                            "page-ai-chat-file-image",
                            name=file_name,
                            format=file_type.split("/")[1],
                            size=file_size,
                        )
                    )
                else:
                    file_info_parts.append(
                        t("page-ai-chat-file-other", name=file_name, type=file_type, size=file_size)
                    )

            message_content += "\n".join(file_info_parts)
            message_content += f"\n\n💡 {t('page-ai-chat-file-analysis-hint')}"

        # Add user message to history
        history.append({"role": "user", "content": message_content})

        # Display user message
        with chat_container:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(message_content)

                # Show file attachments
                if attached_files:
                    st.markdown(f"**{t('page-ai-chat-attachments')}:**")
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
                with st.spinner(t("page-ai-chat-thinking")):
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
                                    f"👍 {t('page-ai-chat-feedback-good')}",
                                    key=f"good_{len(history)}",
                                    use_container_width=True,
                                ):
                                    success = feedback_service.submit_feedback(
                                        agent_type="chat_agent",
                                        rating=5,
                                        user_comment=t("page-ai-chat-feedback-good-comment"),
                                        original_text=full_response,
                                    )
                                    if success:
                                        st.success(t("page-ai-chat-feedback-thanks"))
                                    else:
                                        st.error(t("page-ai-chat-feedback-error"))

                            with feedback_col2:
                                if st.button(
                                    f"👎 {t('page-ai-chat-feedback-bad')}",
                                    key=f"bad_{len(history)}",
                                    use_container_width=True,
                                ):
                                    success = feedback_service.submit_feedback(
                                        agent_type="chat_agent",
                                        rating=2,
                                        user_comment=t("page-ai-chat-feedback-bad-comment"),
                                        original_text=full_response,
                                    )
                                    if success:
                                        st.success(t("page-ai-chat-feedback-thanks"))
                                    else:
                                        st.error(t("page-ai-chat-feedback-error"))

                            with feedback_col3:
                                with st.popover(f"💬 {t('page-ai-chat-feedback-comment')}"):
                                    user_comment = st.text_area(
                                        t("page-ai-chat-feedback-comment-label"),
                                        height=100,
                                        key=f"comment_{len(history)}",
                                    )
                                    if st.button(
                                        t("page-ai-chat-feedback-submit"),
                                        key=f"submit_comment_{len(history)}",
                                    ):
                                        if user_comment.strip():
                                            success = feedback_service.submit_feedback(
                                                agent_type="chat_agent",
                                                rating=3,  # Neutral rating for comments
                                                user_comment=user_comment.strip(),
                                                original_text=full_response,
                                            )
                                            if success:
                                                st.success(t("page-ai-chat-feedback-comment-sent"))
                                            else:
                                                st.error(t("page-ai-chat-feedback-error"))
                                        else:
                                            st.warning(t("page-ai-chat-feedback-comment-empty"))

                    except Exception as e:
                        error_message = handle_chat_error(e, "chat_streaming")
                        full_response = error_message
                        response_placeholder.error(error_message)

                        # Show additional help for common errors
                        if (
                            "connessione" in error_message.lower()
                            or "connection" in error_message.lower()
                        ):
                            st.info(t("page-ai-error-hint-connection"))
                        elif (
                            "autenticazione" in error_message.lower()
                            or "auth" in error_message.lower()
                        ):
                            st.info(t("page-ai-error-hint-auth"))

        # Add assistant response to history
        history.append({"role": "assistant", "content": full_response})

        st.rerun()


def render_description_tab(ai_service: Any) -> None:
    """Render the Invoice Description Generator tab (original ``with tab2:`` body)."""
    st.markdown(f"### 📝 {t('page-ai-desc-title')}")
    st.markdown(t("page-ai-desc-description"))

    with st.form("description_form"):
        servizio = st.text_area(
            t("page-ai-desc-service-label"),
            placeholder=t("page-ai-desc-service-placeholder"),
            help=t("page-ai-desc-service-help"),
        )

        col1, col2 = st.columns(2)

        with col1:
            ore = st.number_input(
                t("page-ai-desc-hours-label"),
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=0.5,
                help=t("page-ai-desc-hours-help"),
            )

            progetto = st.text_input(
                t("page-ai-desc-project-label"),
                placeholder=t("page-ai-desc-project-placeholder"),
                help=t("page-ai-desc-project-help"),
            )

        with col2:
            tariffa = st.number_input(
                t("page-ai-desc-rate-label"),
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=5.0,
                help=t("page-ai-desc-rate-help"),
            )

            tecnologie = st.text_input(
                t("page-ai-desc-tech-label"),
                placeholder=t("page-ai-desc-tech-placeholder"),
                help=t("page-ai-desc-tech-help"),
            )

        submitted = st.form_submit_button(
            f"✨ {t('page-ai-desc-generate')}", use_container_width=True
        )

    if submitted:
        if not servizio:
            st.error(t("page-ai-desc-error-empty"))
        else:
            with st.spinner(t("page-ai-desc-generating")):
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
                        st.success(t("page-ai-desc-success"))

                        # Display result
                        if response.metadata.get("is_structured"):
                            data = response.metadata["parsed_model"]

                            st.markdown(f"#### 📄 {t('page-ai-desc-result-title')}")
                            st.info(data["descrizione_completa"])

                            if data.get("deliverables"):
                                st.markdown(f"#### 📦 {t('page-ai-desc-deliverables')}")
                                for item in data["deliverables"]:
                                    st.markdown(f"- {item}")

                            if data.get("competenze"):
                                st.markdown(f"#### 🔧 {t('page-ai-desc-skills')}")
                                for skill in data["competenze"]:
                                    st.markdown(f"- {skill}")

                            if data.get("durata_ore"):
                                st.markdown(t("page-ai-desc-duration", hours=data["durata_ore"]))

                            if data.get("note"):
                                st.markdown(t("page-ai-desc-notes", notes=data["note"]))

                        else:
                            st.markdown(f"#### 📄 {t('page-ai-desc-result-generated')}")
                            st.info(response.content)

                        # Metrics
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric(t("page-ai-metric-provider"), response.provider)
                        with col_m2:
                            st.metric(t("page-ai-metric-tokens"), response.usage.total_tokens)
                        with col_m3:
                            st.metric(
                                t("page-ai-metric-cost"),
                                f"${response.usage.estimated_cost_usd:.4f}",
                            )

                    else:
                        error_message = handle_chat_error(
                            Exception(response.error), "description_generation"
                        )
                        st.error(error_message)

                except Exception as e:
                    error_message = handle_chat_error(e, "description_generation")
                    st.error(error_message)

                    # Show additional help for common errors
                    if (
                        "connessione" in error_message.lower()
                        or "connection" in error_message.lower()
                    ):
                        st.info(t("page-ai-error-hint-connection"))
                    elif (
                        "autenticazione" in error_message.lower() or "auth" in error_message.lower()
                    ):
                        st.info(t("page-ai-error-hint-auth"))


def render_vat_tab(ai_service: Any) -> None:
    """Render the VAT Suggestion tab (original ``with tab3:`` body)."""
    st.markdown(f"### 🧾 {t('page-ai-vat-title')}")
    st.markdown(t("page-ai-vat-description"))

    with st.form("vat_form"):
        descrizione = st.text_area(
            t("page-ai-vat-service-label"),
            placeholder=t("page-ai-vat-service-placeholder"),
            help=t("page-ai-vat-service-help"),
        )

        col1, col2 = st.columns(2)

        with col1:
            cliente_pa = st.checkbox(
                t("page-ai-vat-client-pa-label"),
                help=t("page-ai-vat-client-pa-help"),
            )

            importo = st.number_input(
                t("page-ai-vat-amount-label"),
                min_value=0.0,
                value=0.0,
                step=10.0,
                help=t("page-ai-vat-amount-help"),
            )

        with col2:
            cliente_estero = st.checkbox(
                t("page-ai-vat-client-foreign-label"),
                help=t("page-ai-vat-client-foreign-help"),
            )

            if cliente_estero:
                paese = st.text_input(
                    t("page-ai-vat-country-label"),
                    value="",
                    max_chars=2,
                    placeholder=t("page-ai-vat-country-placeholder"),
                    help=t("page-ai-vat-country-help"),
                )
            else:
                paese = "IT"

        categoria = st.selectbox(
            t("page-ai-vat-category-label"),
            options=[
                "",
                t("page-ai-vat-category-consulting"),
                t("page-ai-vat-category-software"),
                t("page-ai-vat-category-training"),
                t("page-ai-vat-category-design"),
                t("page-ai-vat-category-marketing"),
                t("page-ai-vat-category-maintenance"),
                t("page-ai-vat-category-other"),
            ],
            help=t("page-ai-vat-category-help"),
        )

        submitted_vat = st.form_submit_button(
            f"🧾 {t('page-ai-vat-suggest')}", use_container_width=True
        )

    if submitted_vat:
        if not descrizione:
            st.error(t("page-ai-vat-error-empty"))
        else:
            with st.spinner(t("page-ai-vat-analyzing")):
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
                        st.success(t("page-ai-vat-success"))

                        # Display result
                        if response.metadata.get("is_structured"):
                            data = response.metadata["parsed_model"]

                            # Main tax info
                            st.markdown(f"#### 📊 {t('page-ai-vat-treatment-title')}")

                            info_cols = st.columns(3)

                            with info_cols[0]:
                                st.metric(
                                    t("page-ai-vat-rate-metric"),
                                    f"{data['aliquota_iva']}%",
                                )

                            with info_cols[1]:
                                st.metric(
                                    t("page-ai-vat-reverse-charge-metric"),
                                    t("page-ai-yes") if data["reverse_charge"] else t("page-ai-no"),
                                )

                            with info_cols[2]:
                                confidence_pct = int(data["confidence"] * 100)
                                st.metric(t("page-ai-vat-confidence-metric"), f"{confidence_pct}%")

                            if data.get("codice_natura"):
                                st.info(t("page-ai-vat-nature-code", code=data["codice_natura"]))

                            if data.get("split_payment"):
                                st.warning(t("page-ai-vat-split-payment"))

                            if data.get("regime_speciale"):
                                st.info(
                                    t("page-ai-vat-special-regime", regime=data["regime_speciale"])
                                )

                            # Explanation
                            st.markdown(f"#### 📋 {t('page-ai-vat-explanation-title')}")
                            st.markdown(data["spiegazione"])

                            # Legal reference
                            st.markdown(f"#### 📜 {t('page-ai-vat-legal-reference-title')}")
                            st.markdown(data["riferimento_normativo"])

                            # Invoice notes
                            if data.get("note_fattura"):
                                st.markdown(f"#### 📝 {t('page-ai-vat-invoice-note-title')}")
                                st.code(data["note_fattura"])

                            # Recommendations
                            if data.get("raccomandazioni") and len(data["raccomandazioni"]) > 0:
                                st.markdown(f"#### 💡 {t('page-ai-vat-recommendations-title')}")
                                for racc in data["raccomandazioni"]:
                                    st.markdown(f"- {racc}")

                        else:
                            st.markdown(f"#### 📊 {t('page-ai-vat-suggestion-title')}")
                            st.info(response.content)

                        # Metrics
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric(t("page-ai-metric-provider"), response.provider)
                        with col_m2:
                            st.metric(t("page-ai-metric-tokens"), response.usage.total_tokens)
                        with col_m3:
                            st.metric(
                                t("page-ai-metric-cost"),
                                f"${response.usage.estimated_cost_usd:.4f}",
                            )

                    else:
                        st.error(t("page-ai-vat-error", error=response.error))

                except Exception as e:
                    st.error(t("page-ai-vat-error-generic", error=str(e)))
                    st.exception(e)


def render_voice_tab(voice_service: Any) -> None:
    """Render the Voice Chat tab (original ``with tab4:`` body)."""
    st.markdown(f"### 🎤 {t('page-ai-voice-title')}")

    # Check if voice is available
    if not voice_service.is_available():
        st.warning(t("page-ai-voice-not-configured"))
        st.stop()

    st.markdown(t("page-ai-voice-description"))

    # Voice configuration info
    with st.expander(t("page-ai-voice-config-title"), expanded=False):
        voice_config = voice_service.get_config()

        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            st.metric(t("page-ai-voice-config-provider"), voice_config.get("provider", "N/A"))
        with col_v2:
            st.metric(t("page-ai-voice-config-stt"), voice_config.get("stt_model", "N/A"))
        with col_v3:
            st.metric(t("page-ai-voice-config-tts-voice"), voice_config.get("tts_voice", "N/A"))

        st.markdown(t("page-ai-voice-config-tts-model", model=voice_config.get("tts_model", "N/A")))
        st.markdown(t("page-ai-voice-config-tts-speed", speed=voice_config.get("tts_speed", 1.0)))
        st.markdown(
            t("page-ai-voice-config-tts-format", format=voice_config.get("tts_format", "mp3"))
        )
        st.markdown(
            t(
                "page-ai-voice-config-streaming",
                enabled=(
                    t("page-ai-yes") if voice_config.get("streaming_enabled") else t("page-ai-no")
                ),
            )
        )

    # Initialize voice conversation history
    if "voice_conversation_history" not in st.session_state:
        st.session_state.voice_conversation_history = []

    voice_history = st.session_state.voice_conversation_history

    # Action buttons
    voice_col1, voice_col2 = st.columns([4, 1])
    with voice_col2:
        if st.button(f"🗑️ {t('page-ai-voice-clear')}", use_container_width=True):
            st.session_state.voice_conversation_history = []
            st.rerun()

    # Display voice conversation history
    if voice_history:
        st.markdown(f"### 📜 {t('page-ai-voice-history-title')}")
        with st.container():
            for i, interaction in enumerate(voice_history):
                # User message
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(t("page-ai-voice-user-message", text=interaction["transcription"]))
                    if interaction.get("language"):
                        st.caption(
                            t("page-ai-voice-language-detected", lang=interaction["language"])
                        )

                # Assistant response
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(t("page-ai-voice-assistant-message", text=interaction["response"]))

                    # Show audio if available
                    if interaction.get("audio_data"):
                        st.audio(interaction["audio_data"], format="audio/mp3")

                    # Metrics
                    if interaction.get("metrics"):
                        metrics = interaction["metrics"]
                        metric_cols = st.columns(4)
                        with metric_cols[0]:
                            st.caption(
                                t("page-ai-voice-metric-stt", ms=f"{metrics.get('stt_ms', 0):.0f}")
                            )
                        with metric_cols[1]:
                            st.caption(
                                t("page-ai-voice-metric-llm", ms=f"{metrics.get('llm_ms', 0):.0f}")
                            )
                        with metric_cols[2]:
                            st.caption(
                                t("page-ai-voice-metric-tts", ms=f"{metrics.get('tts_ms', 0):.0f}")
                            )
                        with metric_cols[3]:
                            st.caption(
                                t(
                                    "page-ai-voice-metric-total",
                                    ms=f"{metrics.get('total_ms', 0):.0f}",
                                )
                            )
    else:
        st.info(t("page-ai-voice-history-empty"))

    st.markdown("---")

    # Audio input
    st.markdown(f"### 🎙️ {t('page-ai-voice-record-title')}")

    # Streamlit audio input (available from Streamlit 1.28+)
    audio_input = st.audio_input(
        t("page-ai-voice-record-label"),
        key="voice_chat_audio_input",
        help=t("page-ai-voice-record-help"),
    )

    if audio_input is not None:
        st.success(t("page-ai-voice-recorded", size=audio_input.size))

        # Show audio preview
        st.audio(audio_input, format="audio/wav")

        # Process audio button
        if st.button(f"🚀 {t('page-ai-voice-process')}", type="primary", use_container_width=True):
            with st.spinner(t("page-ai-voice-processing")):
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
                    st.success(t("page-ai-voice-success"))

                    # Display results
                    result_col1, result_col2 = st.columns(2)

                    with result_col1:
                        st.markdown(f"#### 📝 {t('page-ai-voice-transcription-title')}")
                        st.info(t("page-ai-voice-user-message", text=response.transcription.text))
                        st.caption(
                            t("page-ai-voice-language", lang=response.transcription.language)
                        )

                    with result_col2:
                        st.markdown(f"#### 🤖 {t('page-ai-voice-response-title')}")
                        st.success(t("page-ai-voice-assistant-message", text=response.llm_response))

                    # Audio response
                    if response.synthesis:
                        st.markdown(f"#### 🔊 {t('page-ai-voice-audio-response-title')}")
                        st.audio(response.synthesis.audio_data, format="audio/mp3")

                    # Metrics
                    st.markdown(f"#### 📊 {t('page-ai-voice-metrics-title')}")
                    metrics_cols = st.columns(4)
                    with metrics_cols[0]:
                        st.metric("STT", f"{response.stt_latency_ms:.0f}ms")
                    with metrics_cols[1]:
                        st.metric("LLM", f"{response.llm_latency_ms:.0f}ms")
                    with metrics_cols[2]:
                        st.metric("TTS", f"{response.tts_latency_ms or 0:.0f}ms")
                    with metrics_cols[3]:
                        st.metric(
                            t("page-ai-voice-metric-total-label"),
                            f"{response.total_latency_ms:.0f}ms",
                        )

                    # Additional info
                    if response.llm_metadata:
                        with st.expander(t("page-ai-voice-tech-details")):
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
                    st.error(t("page-ai-voice-error", error=error_msg))

                    # Show additional help
                    if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                        st.info(t("page-ai-voice-error-hint-connection"))
                    elif "auth" in error_msg.lower() or "key" in error_msg.lower():
                        st.info(t("page-ai-voice-error-hint-auth"))
                    elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                        st.info(t("page-ai-voice-error-hint-rate"))

                    st.exception(e)

    # Help section
    with st.expander(t("page-ai-voice-help-title"), expanded=False):
        st.markdown(t("page-ai-voice-help-content"))
