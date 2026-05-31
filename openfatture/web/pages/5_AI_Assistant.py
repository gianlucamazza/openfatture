"""AI Assistant page with chat, description generator, and tax advisor.

Provides interactive AI tools for invoice management and tax compliance.

The heavy logic lives in the ``_ai_assistant`` sub-package; this module only
wires services and renders the four tabs.
"""

import streamlit as st

from openfatture.web.pages._ai_assistant import (
    render_chat_tab,
    render_description_tab,
    render_vat_tab,
    render_voice_tab,
)
from openfatture.web.services.ai_service import get_ai_service
from openfatture.web.services.custom_commands_service import get_custom_commands_service
from openfatture.web.services.feedback_service import get_feedback_service
from openfatture.web.services.session_service import get_session_service
from openfatture.web.services.voice_service import get_voice_service
from openfatture.web.utils.i18n import get_translator

# Initialize translator
t = get_translator()

st.set_page_config(page_title=t("page-ai-page-title"), page_icon="🤖", layout="wide")

# Title
st.title(t("page-ai-title"))
st.markdown(f"### {t('page-ai-subtitle')}")

# Initialize services
ai_service = get_ai_service()
custom_commands_service = get_custom_commands_service()
session_service = get_session_service()
feedback_service = get_feedback_service()
voice_service = get_voice_service()

# Check if AI is available
if not ai_service.is_available():
    st.error(t("page-ai-not-configured"))
    st.stop()

# Tab selection
tab1, tab2, tab3, tab4 = st.tabs(
    [
        f"💬 {t('page-ai-tab-chat')}",
        f"📝 {t('page-ai-tab-description')}",
        f"🧾 {t('page-ai-tab-vat')}",
        f"🎤 {t('page-ai-tab-voice')}",
    ]
)

# TAB 1: Chat Assistant
with tab1:
    render_chat_tab(
        ai_service=ai_service,
        custom_commands_service=custom_commands_service,
        session_service=session_service,
        feedback_service=feedback_service,
    )

# TAB 2: Invoice Description Generator
with tab2:
    render_description_tab(ai_service=ai_service)

# TAB 3: VAT Suggestion
with tab3:
    render_vat_tab(ai_service=ai_service)

# TAB 4: Voice Chat
with tab4:
    render_voice_tab(voice_service=voice_service)

# Info footer
st.markdown("---")
st.info(t("page-ai-footer-disclaimer"))
