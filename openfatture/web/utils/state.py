"""Session state management utilities for Streamlit.

Provides helpers for managing Streamlit session_state with type safety.
"""

from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def init_state(key: str, default: T) -> T:
    """
    Initialize a session state value if it doesn't exist.

    Args:
        key: Session state key
        default: Default value to set if key doesn't exist

    Returns:
        Current or newly set value

    Example:
        >>> page = init_state("current_page", "dashboard")
    """
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def get_state(key: str, default: T | None = None) -> T | None:
    """
    Get a value from session state with optional default.

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Session state value or default

    Example:
        >>> invoice_id = get_state("selected_invoice_id", None)
    """
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """
    Set a value in session state.

    Args:
        key: Session state key
        value: Value to set

    Example:
        >>> set_state("filter_year", 2024)
    """
    st.session_state[key] = value


def clear_state(key: str) -> None:
    """
    Remove a key from session state if it exists.

    Args:
        key: Session state key to remove

    Example:
        >>> clear_state("temp_data")
    """
    if key in st.session_state:
        del st.session_state[key]


def clear_all_state() -> None:
    """Clear all session state (use with caution!)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def init_conversation_history() -> list[dict[str, str]]:
    """
    Initialize and return AI conversation history from session state.

    Returns:
        List of conversation messages in format: [{"role": "user|assistant", "content": "..."}]

    Example:
        >>> history = init_conversation_history()
        >>> history.append({"role": "user", "content": "Hello"})
    """
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    return st.session_state.conversation_history


def clear_conversation_history() -> None:
    """Clear AI conversation history from session state."""
    if "conversation_history" in st.session_state:
        st.session_state.conversation_history = []


def init_wizard_state() -> dict[str, Any]:
    """
    Initialize multi-step wizard state.

    Returns:
        Dictionary for tracking wizard progress and data

    Example:
        >>> wizard = init_wizard_state()
        >>> wizard["current_step"] = 2
        >>> wizard["invoice_data"] = {...}
    """
    if "wizard_state" not in st.session_state:
        st.session_state.wizard_state = {"current_step": 1, "data": {}}
    return st.session_state.wizard_state


def reset_wizard() -> None:
    """Reset wizard state to initial values."""
    if "wizard_state" in st.session_state:
        st.session_state.wizard_state = {"current_step": 1, "data": {}}
