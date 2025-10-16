"""Reusable Alert Components - Best Practices 2025.

Consistent alert/notification components for user feedback.
"""

from collections.abc import Callable

import streamlit as st


def success_alert(message: str, icon: str = "✅", dismissible: bool = False) -> None:
    """
    Display a success alert.

    Args:
        message: Success message
        icon: Icon/emoji
        dismissible: Whether user can dismiss

    Example:
        >>> success_alert("Invoice created successfully!")
    """
    if dismissible:
        with st.container():
            col1, col2 = st.columns([10, 1])
            with col1:
                st.success(f"{icon} {message}")
            with col2:
                if st.button("✖", key=f"dismiss_{hash(message)}"):
                    st.rerun()
    else:
        st.success(f"{icon} {message}")


def error_alert(
    message: str,
    details: str | None = None,
    icon: str = "❌",
    show_exception: bool = False,
) -> None:
    """
    Display an error alert.

    Args:
        message: Error message
        details: Additional error details
        icon: Icon/emoji
        show_exception: Show full exception trace

    Example:
        >>> error_alert("Failed to save invoice", details="Database connection error")
    """
    st.error(f"{icon} {message}")

    if details:
        with st.expander("ℹ️ Dettagli Errore"):
            st.code(details)

    if show_exception:
        import traceback

        st.exception(traceback.format_exc())


def warning_alert(
    message: str,
    action: str | None = None,
    on_action: Callable | None = None,
    icon: str = "⚠️",
) -> None:
    """
    Display a warning alert with optional action.

    Args:
        message: Warning message
        action: Action button label
        on_action: Callback when action clicked
        icon: Icon/emoji

    Example:
        >>> warning_alert(
        ...     "This invoice is overdue",
        ...     action="Send Reminder",
        ...     on_action=lambda: send_reminder()
        ... )
    """
    st.warning(f"{icon} {message}")

    if action and on_action:
        if st.button(action, key=f"warning_action_{hash(message)}"):
            on_action()


def info_alert(
    message: str,
    learn_more_url: str | None = None,
    icon: str = "ℹ️",
) -> None:
    """
    Display an informational alert.

    Args:
        message: Info message
        learn_more_url: Optional documentation URL
        icon: Icon/emoji

    Example:
        >>> info_alert(
        ...     "New feature available",
        ...     learn_more_url="https://docs.example.com"
        ... )
    """
    st.info(f"{icon} {message}")

    if learn_more_url:
        st.markdown(f"[📚 Learn more]({learn_more_url})")


def confirmation_dialog(
    title: str,
    message: str,
    on_confirm: Callable,
    on_cancel: Callable | None = None,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    danger: bool = False,
) -> None:
    """
    Display a confirmation dialog (using expander pattern).

    Args:
        title: Dialog title
        message: Confirmation message
        on_confirm: Callback when confirmed
        on_cancel: Optional callback when cancelled
        confirm_text: Confirm button label
        cancel_text: Cancel button label
        danger: Style as dangerous action (red button)

    Example:
        >>> confirmation_dialog(
        ...     title="Delete Invoice",
        ...     message="Are you sure? This cannot be undone.",
        ...     on_confirm=lambda: delete_invoice(),
        ...     danger=True
        ... )
    """
    with st.expander(f"⚠️ {title}", expanded=True):
        st.markdown(message)

        col1, col2 = st.columns(2)

        with col1:
            button_type = "primary" if not danger else "secondary"
            if st.button(
                cancel_text,
                key=f"cancel_{hash(title)}",
                use_container_width=True,
                type="secondary",
            ):
                if on_cancel:
                    on_cancel()

        with col2:
            if st.button(
                confirm_text,
                key=f"confirm_{hash(title)}",
                use_container_width=True,
                type=button_type,
            ):
                on_confirm()


def toast_notification(
    message: str,
    type: str = "success",
    duration: int = 3,
) -> None:
    """
    Display a toast notification (Streamlit 1.27+).

    Args:
        message: Notification message
        type: Type ("success", "error", "warning", "info")
        duration: Duration in seconds

    Example:
        >>> toast_notification("Settings saved!", type="success")
    """
    # Note: st.toast requires Streamlit >= 1.27
    try:
        if type == "success":
            st.toast(f"✅ {message}", icon="✅")
        elif type == "error":
            st.toast(f"❌ {message}", icon="❌")
        elif type == "warning":
            st.toast(f"⚠️ {message}", icon="⚠️")
        else:
            st.toast(f"ℹ️ {message}", icon="ℹ️")
    except AttributeError:
        # Fallback for older Streamlit versions
        if type == "success":
            st.success(message)
        elif type == "error":
            st.error(message)
        elif type == "warning":
            st.warning(message)
        else:
            st.info(message)


def progress_indicator(
    current: int,
    total: int,
    label: str = "Progress",
    show_percentage: bool = True,
) -> None:
    """
    Display a progress indicator.

    Args:
        current: Current step
        total: Total steps
        label: Progress label
        show_percentage: Show percentage text

    Example:
        >>> progress_indicator(current=3, total=5, label="Processing invoices")
    """
    percentage = int((current / total) * 100) if total > 0 else 0

    if show_percentage:
        st.caption(f"{label}: {current}/{total} ({percentage}%)")

    st.progress(percentage / 100)
