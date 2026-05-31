"""Internal sub-package backing the AI Assistant Streamlit page.

Holds the helper functions and per-tab render functions extracted from
``5__AI_Assistant.py`` so the page itself stays thin.
"""

from openfatture.web.pages._ai_assistant.helpers import (
    handle_chat_error,
    handle_slash_command,
    retry_with_backoff,
)
from openfatture.web.pages._ai_assistant.tabs import (
    render_chat_tab,
    render_description_tab,
    render_vat_tab,
    render_voice_tab,
)

__all__ = [
    "handle_chat_error",
    "handle_slash_command",
    "retry_with_backoff",
    "render_chat_tab",
    "render_description_tab",
    "render_vat_tab",
    "render_voice_tab",
]
