"""Voice service for Web UI.

Provides voice interaction capabilities through the Streamlit interface.
"""

import asyncio
from typing import Any

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.voice import VoiceAssistant, create_voice_provider
from openfatture.ai.voice.models import VoiceResponse
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceService:
    """
    Voice service for Web UI.

    Manages voice assistant interactions through Streamlit interface.
    """

    def __init__(self) -> None:
        """Initialize voice service."""
        self.settings = get_settings()
        self._voice_assistant: VoiceAssistant | None = None

    def is_available(self) -> bool:
        """
        Check if voice features are available.

        Returns:
            True if voice is enabled and configured
        """
        return (
            self.settings.voice_enabled
            and self.settings.openai_api_key is not None
            and len(self.settings.openai_api_key) > 0
        )

    def get_voice_assistant(self) -> VoiceAssistant:
        """
        Get or create voice assistant instance.

        Returns:
            VoiceAssistant instance

        Raises:
            RuntimeError: If voice is not available
        """
        if not self.is_available():
            raise RuntimeError("Voice features not available. Check configuration.")

        if self._voice_assistant is None:
            # Create voice provider
            voice_provider = create_voice_provider(api_key=self.settings.openai_api_key)

            # Create chat agent
            chat_provider = create_provider()
            chat_agent = ChatAgent(provider=chat_provider, enable_streaming=False)

            # Create voice assistant
            self._voice_assistant = VoiceAssistant(
                voice_provider=voice_provider,
                chat_agent=chat_agent,
                enable_tts=True,
            )

            logger.info("voice_assistant_initialized", provider="openai")

        return self._voice_assistant

    async def process_voice_input_async(
        self,
        audio_bytes: bytes,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> VoiceResponse:
        """
        Process voice input asynchronously.

        Args:
            audio_bytes: Audio data (WAV, MP3, etc.)
            conversation_history: Optional conversation history

        Returns:
            VoiceResponse with transcription, LLM response, and synthesis

        Raises:
            RuntimeError: If voice is not available
            Exception: If processing fails
        """
        assistant = self.get_voice_assistant()

        # Create context with history if provided
        context = None
        if conversation_history:
            from openfatture.ai.domain.message import ConversationHistory, Message, Role

            conv_history = ConversationHistory()
            for msg in conversation_history:
                role = Role(msg["role"])
                content = msg["content"]
                conv_history.add_message(Message(role=role, content=content))

            context = ChatContext(
                user_input="",  # Will be filled by transcription
                conversation_history=conv_history,
            )

        # Process voice input
        logger.info("voice_input_processing", audio_size=len(audio_bytes))
        response = await assistant.process_voice_input(
            audio=audio_bytes,
            context=context,
        )

        logger.info(
            "voice_input_processed",
            language=response.transcription.language,
            text_length=len(response.transcription.text),
            response_length=len(response.llm_response),
            total_latency_ms=response.total_latency_ms,
        )

        return response

    def process_voice_input(
        self,
        audio_bytes: bytes,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> VoiceResponse:
        """
        Process voice input synchronously (wrapper for async method).

        Args:
            audio_bytes: Audio data (WAV, MP3, etc.)
            conversation_history: Optional conversation history

        Returns:
            VoiceResponse with transcription, LLM response, and synthesis
        """
        # Create new event loop for sync execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.process_voice_input_async(audio_bytes, conversation_history)
            )
        finally:
            loop.close()

    def get_config(self) -> dict[str, Any]:
        """
        Get voice configuration.

        Returns:
            Dictionary with voice settings
        """
        if not self.is_available():
            return {"enabled": False, "message": "Voice not configured"}

        return {
            "enabled": True,
            "provider": self.settings.voice_provider,
            "stt_model": self.settings.voice_stt_model,
            "tts_model": self.settings.voice_tts_model,
            "tts_voice": self.settings.voice_tts_voice,
            "tts_speed": self.settings.voice_tts_speed,
            "tts_format": self.settings.voice_tts_format,
            "streaming_enabled": self.settings.voice_streaming_enabled,
        }


# Singleton instance
_voice_service: VoiceService | None = None


def get_voice_service() -> VoiceService:
    """
    Get singleton voice service instance.

    Returns:
        VoiceService instance
    """
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
