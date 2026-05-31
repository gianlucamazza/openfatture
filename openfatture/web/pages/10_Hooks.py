"""Hooks & Automation page.

Manage automation hooks and workflow triggers.
"""

import streamlit as st

from openfatture.web.services.hooks_service import StreamlitHooksService
from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-hooks-page-title"), page_icon="🪝", layout="wide")

# Title
st.title(t("page-hooks-title"))
st.markdown(f"### {t('page-hooks-subtitle')}")

# Initialize service
hooks_service = StreamlitHooksService()

# Get hooks data
hooks = hooks_service.get_available_hooks()
summary = hooks_service.get_hooks_summary()

# Summary cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(t("page-hooks-total-hooks"), summary["total_hooks"])

with col2:
    st.metric(t("page-hooks-enabled-hooks"), summary["enabled_hooks"])

with col3:
    st.metric(t("page-hooks-pre-hooks"), summary["by_event_type"]["pre"])

with col4:
    st.metric(t("page-hooks-post-hooks"), summary["by_event_type"]["post"])

# Tabs for different views
tab_overview, tab_manage, tab_create, tab_test = st.tabs(
    [
        t("page-hooks-tab-overview"),
        t("page-hooks-tab-manage"),
        t("page-hooks-tab-create"),
        t("page-hooks-tab-test"),
    ]
)

with tab_overview:
    st.subheader(t("page-hooks-overview-title"))

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
                            st.success(t("page-hooks-active"))
                        else:
                            st.warning(t("page-hooks-inactive"))
    else:
        st.info(t("page-hooks-no-hooks-info"))

with tab_manage:
    st.subheader(t("page-hooks-manage-title"))

    if hooks:
        st.markdown(f"### {t('page-hooks-toggle-state-title')}")

        for hook in hooks:
            col1, col2, col3 = st.columns([3, 1, 2])

            with col1:
                st.write(f"**{hook['name']}**")
                if hook["description"]:
                    st.caption(hook["description"])

            with col2:
                # Toggle switch
                enabled = st.toggle(
                    t("page-hooks-activate-label", name=hook["name"]),
                    value=hook["enabled"],
                    key=f"toggle_{hook['name']}",
                    help=t("page-hooks-toggle-help", name=hook["name"]),
                )

                # Update status if changed
                if enabled != hook["enabled"]:
                    if hooks_service.toggle_hook_status(hook["name"], enabled):
                        if enabled:
                            st.success(t("page-hooks-activated-success", name=hook["name"]))
                        else:
                            st.warning(t("page-hooks-deactivated-success", name=hook["name"]))
                        st.rerun()
                    else:
                        st.error(t("page-hooks-update-error"))

            with col3:
                if st.button(
                    t("page-hooks-details-btn"),
                    key=f"details_{hook['name']}",
                    help=t("page-hooks-show-details-help"),
                ):
                    with st.expander(
                        t("page-hooks-details-title", name=hook["name"]), expanded=True
                    ):
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
        st.info(t("page-hooks-no-hooks-manage"))

with tab_create:
    st.subheader(t("page-hooks-create-title"))

    with st.form("create_hook_form"):
        col1, col2 = st.columns(2)

        with col1:
            hook_name = st.text_input(
                t("page-hooks-hook-name-label"),
                placeholder=t("page-hooks-hook-name-placeholder"),
                help=t("page-hooks-hook-name-help"),
            )

            hook_type = st.selectbox(
                t("page-hooks-script-type-label"),
                ["bash", "python"],
                help=t("page-hooks-script-type-help"),
            )

        with col2:
            description = st.text_input(
                t("page-hooks-description-label"),
                placeholder=t("page-hooks-description-placeholder"),
                help=t("page-hooks-description-help"),
            )

            event_type = st.selectbox(
                t("page-hooks-event-type-label"),
                ["pre", "post", "on"],
                help=t("page-hooks-event-type-help"),
            )

        # Preview template
        if hook_name and hook_type:
            st.markdown(f"### {t('page-hooks-template-preview')}")
            template = hooks_service.get_hook_template(hook_type)

            # Customize template
            if description:
                template = template.replace("Hook description here", description)

            with st.expander(t("page-hooks-template-code"), expanded=False):
                st.code(template, language=hook_type)

        # Submit button
        submitted = st.form_submit_button(t("page-hooks-create-hook-btn"), type="primary")

        if submitted:
            if not hook_name:
                st.error(t("page-hooks-name-required-error"))
            elif not hook_name.startswith(f"{event_type}-"):
                st.warning(t("page-hooks-name-prefix-warning", prefix=event_type))

            else:
                success, message = hooks_service.create_hook_from_template(
                    hook_name, hook_type, description
                )

                if success:
                    st.success(f"✅ {message}")
                    st.info(t("page-hooks-reload-page-info"))
                else:
                    st.error(f"❌ {message}")

with tab_test:
    st.subheader(t("page-hooks-test-title"))

    if hooks:
        # Hook selection
        hook_names = [hook["name"] for hook in hooks]
        selected_hook = st.selectbox(
            t("page-hooks-select-hook-label"), hook_names, help=t("page-hooks-select-hook-help")
        )

        if selected_hook:
            hook_info = next(h for h in hooks if h["name"] == selected_hook)

            st.markdown(f"### {t('page-hooks-hook-info-title')}")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(t("page-hooks-event-type-metric"), hook_info["event_type"].upper())

            with col2:
                st.metric(
                    t("page-hooks-status-metric"),
                    t("page-hooks-active") if hook_info["enabled"] else t("page-hooks-inactive"),
                )

            with col3:
                st.metric(t("page-hooks-timeout-metric"), f"{hook_info['timeout']}s")

            # Test button
            if st.button(
                t("page-hooks-validate-hook-btn"), type="primary", use_container_width=True
            ):
                with st.spinner(t("page-hooks-validating-spinner")):
                    result = hooks_service.test_hook_execution(selected_hook)

                if result["success"]:
                    st.success(t("page-hooks-validation-success"))

                    if result["result"]:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric(
                                t("page-hooks-code-lines-metric"), result["result"]["line_count"]
                            )
                        with col_b:
                            st.metric(
                                t("page-hooks-size-metric"),
                                f"{result['result']['file_size']} bytes",
                            )
                        with col_c:
                            executable = (
                                t("page-hooks-yes")
                                if result["result"]["is_executable"]
                                else t("page-hooks-no")
                            )
                            st.metric(t("page-hooks-executable-metric"), executable)

                        st.info(f"💡 {result['result']['message']}")
                else:
                    st.error(t("page-hooks-validation-error", error=result["error"]))

            # Show hook content
            if st.button(t("page-hooks-show-code-btn"), use_container_width=True):
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
                        st.error(t("page-hooks-file-not-found-error"))
                except Exception as e:
                    st.error(t("page-hooks-file-read-error", error=str(e)))
    else:
        st.info(t("page-hooks-no-hooks-test"))

# Footer info
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    {t("page-hooks-footer-info")}
    </div>
    """,
    unsafe_allow_html=True,
)
