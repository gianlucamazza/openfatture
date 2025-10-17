"""Hooks & Automation page.

Manage automation hooks and workflow triggers.
"""

import streamlit as st

from openfatture.web.services.hooks_service import StreamlitHooksService

st.set_page_config(page_title="Hooks & Automation - OpenFatture", page_icon="🪝", layout="wide")

# Title
st.title("🪝 Hooks & Automation")
st.markdown("### Gestione workflow automatizzati e trigger")

# Initialize service
hooks_service = StreamlitHooksService()

# Get hooks data
hooks = hooks_service.get_available_hooks()
summary = hooks_service.get_hooks_summary()

# Summary cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Hooks Totali", summary["total_hooks"])

with col2:
    st.metric("Hooks Attivi", summary["enabled_hooks"])

with col3:
    st.metric("Pre-hooks", summary["by_event_type"]["pre"])

with col4:
    st.metric("Post-hooks", summary["by_event_type"]["post"])

# Tabs for different views
tab_overview, tab_manage, tab_create, tab_test = st.tabs(
    ["📊 Panoramica", "⚙️ Gestione", "➕ Crea Hook", "🧪 Test"]
)

with tab_overview:
    st.subheader("📊 Panoramica Hooks")

    # Event type breakdown
    if hooks:
        # Group hooks by event type
        event_types: dict[str, list] = {}
        for hook in hooks:
            event_type = hook["event_type"]
            if event_type not in event_types:
                event_types[event_type] = []
            event_types[event_type].append(hook)

        for event_type, event_hooks in event_types.items():
            with st.expander(
                f"{'🎯' if event_type == 'pre' else '✅' if event_type == 'post' else '👀'} {event_type.upper()}-hooks ({len(event_hooks)})",
                expanded=True,
            ):
                for hook in event_hooks:
                    col_a, col_b, col_c, col_d = st.columns([3, 2, 1, 1])

                    with col_a:
                        status_icon = "✅" if hook["enabled"] else "⏸️"
                        st.write(f"{status_icon} **{hook['name']}**")
                        if hook["description"]:
                            st.caption(hook["description"])

                    with col_b:
                        st.caption(f"📁 {hook['path'].split('/')[-1]}")
                        if hook["author"]:
                            st.caption(f"👤 {hook['author']}")

                    with col_c:
                        st.caption(f"⏱️ {hook['timeout']}s")

                    with col_d:
                        if hook["enabled"]:
                            st.success("Attivo")
                        else:
                            st.warning("Disattivo")
    else:
        st.info("🎣 Nessun hook trovato. Crea il tuo primo hook nella tab 'Crea Hook'!")

with tab_manage:
    st.subheader("⚙️ Gestione Hooks")

    if hooks:
        st.markdown("### Toggle Stato Hooks")

        for hook in hooks:
            col1, col2, col3 = st.columns([3, 1, 2])

            with col1:
                st.write(f"**{hook['name']}**")
                if hook["description"]:
                    st.caption(hook["description"])

            with col2:
                # Toggle switch
                enabled = st.toggle(
                    f"Attiva {hook['name']}",
                    value=hook["enabled"],
                    key=f"toggle_{hook['name']}",
                    help=f"Abilita/disabilita l'hook {hook['name']}",
                )

                # Update status if changed
                if enabled != hook["enabled"]:
                    if hooks_service.toggle_hook_status(hook["name"], enabled):
                        if enabled:
                            st.success(f"✅ Hook '{hook['name']}' attivato")
                        else:
                            st.warning(f"⏸️ Hook '{hook['name']}' disattivato")
                        st.rerun()
                    else:
                        st.error("❌ Errore nell'aggiornamento dello stato del hook")

            with col3:
                if st.button(
                    "👁️ Dettagli", key=f"details_{hook['name']}", help="Mostra dettagli hook"
                ):
                    with st.expander(f"Dettagli {hook['name']}", expanded=True):
                        st.json(
                            {
                                "name": hook["name"],
                                "path": hook["path"],
                                "enabled": hook["enabled"],
                                "timeout": hook["timeout"],
                                "fail_on_error": hook["fail_on_error"],
                                "description": hook["description"],
                                "author": hook["author"],
                                "requires": hook["requires"],
                                "event_type": hook["event_type"],
                            }
                        )
    else:
        st.info("🎣 Nessun hook da gestire")

with tab_create:
    st.subheader("➕ Crea Nuovo Hook")

    with st.form("create_hook_form"):
        col1, col2 = st.columns(2)

        with col1:
            hook_name = st.text_input(
                "Nome Hook",
                placeholder="es: post-invoice-send",
                help="Nome del hook (usa prefissi pre-, post-, on-)",
            )

            hook_type = st.selectbox(
                "Tipo Script", ["bash", "python"], help="Tipo di script per l'hook"
            )

        with col2:
            description = st.text_input(
                "Descrizione",
                placeholder="Cosa fa questo hook...",
                help="Breve descrizione del hook",
            )

            event_type = st.selectbox(
                "Tipo Evento", ["pre", "post", "on"], help="Quando viene eseguito l'hook"
            )

        # Preview template
        if hook_name and hook_type:
            st.markdown("### 📋 Anteprima Template")
            template = hooks_service.get_hook_template(hook_type)

            # Customize template
            if description:
                template = template.replace("Hook description here", description)

            with st.expander("👁️ Codice Template", expanded=False):
                st.code(template, language=hook_type)

        # Submit button
        submitted = st.form_submit_button("🚀 Crea Hook", type="primary")

        if submitted:
            if not hook_name:
                st.error("❌ Inserisci un nome per l'hook")
            elif not hook_name.startswith(f"{event_type}-"):
                st.warning(f"💡 Suggerimento: il nome dovrebbe iniziare con '{event_type}-'")

            else:
                success, message = hooks_service.create_hook_from_template(
                    hook_name, hook_type, description
                )

                if success:
                    st.success(f"✅ {message}")
                    st.info("🔄 Ricarica la pagina per vedere il nuovo hook")
                else:
                    st.error(f"❌ {message}")

with tab_test:
    st.subheader("🧪 Test Hooks")

    if hooks:
        # Hook selection
        hook_names = [hook["name"] for hook in hooks]
        selected_hook = st.selectbox(
            "Seleziona Hook da Testare", hook_names, help="Scegli l'hook da validare"
        )

        if selected_hook:
            hook_info = next(h for h in hooks if h["name"] == selected_hook)

            st.markdown("### 📋 Informazioni Hook")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Tipo Evento", hook_info["event_type"].upper())

            with col2:
                st.metric("Stato", "Attivo" if hook_info["enabled"] else "Disattivo")

            with col3:
                st.metric("Timeout", f"{hook_info['timeout']}s")

            # Test button
            if st.button("🧪 Valida Hook", type="primary", use_container_width=True):
                with st.spinner("Validando hook..."):
                    result = hooks_service.test_hook_execution(selected_hook)

                if result["success"]:
                    st.success("✅ Hook validato con successo!")

                    if result["result"]:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Righe Codice", result["result"]["line_count"])
                        with col_b:
                            st.metric("Dimensione", f"{result['result']['file_size']} bytes")
                        with col_c:
                            executable = "Sì" if result["result"]["is_executable"] else "No"
                            st.metric("Eseguibile", executable)

                        st.info(f"💡 {result['result']['message']}")
                else:
                    st.error(f"❌ Errore validazione: {result['error']}")

            # Show hook content
            if st.button("📄 Mostra Codice", use_container_width=True):
                try:
                    hook_config = hooks_service.registry.get_hook(selected_hook)
                    if hook_config and hook_config.script_path.exists():
                        content = hook_config.script_path.read_text(encoding="utf-8")
                        st.code(
                            content,
                            language=(
                                "bash" if hook_config.script_path.suffix == ".sh" else "python"
                            ),
                        )
                    else:
                        st.error("❌ File hook non trovato")
                except Exception as e:
                    st.error(f"❌ Errore lettura file: {e}")
    else:
        st.info("🎣 Nessun hook disponibile per il test")

# Footer info
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    🪝 <strong>Hooks System:</strong> Automazione workflow basata su eventi •
    📍 <strong>Directory:</strong> ~/.openfatture/hooks/ •
    📚 <strong>Documentazione:</strong> Vedi CLI per esempi avanzati
    </div>
    """,
    unsafe_allow_html=True,
)
