"""Voice assistant orchestration layer."""

import io
import time
from pathlib import Path
from typing import Any, BinaryIO

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.voice.base import BaseVoiceProvider
from openfatture.ai.voice.models import AudioFormat, VoiceResponse
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceAssistant:
    """
    Voice-enabled AI assistant.

    Orchestrates the complete voice interaction flow:
    1. Speech-to-Text (STT): Transcribe user audio
    2. LLM Processing: Generate response via ChatAgent
    3. Text-to-Speech (TTS): Synthesize audio response

    This class bridges the voice provider and chat agent,
    managing the end-to-end conversation flow with voice I/O.

    Example:
        >>> from openfatture.ai.voice import create_voice_provider
        >>> from openfatture.ai.agents.chat_agent import ChatAgent
        >>> from openfatture.ai.providers import create_provider
        >>>
        >>> # Create components
        >>> voice_provider = create_voice_provider()
        >>> llm_provider = create_provider()
        >>> chat_agent = ChatAgent(provider=llm_provider)
        >>>
        >>> # Create voice assistant
        >>> assistant = VoiceAssistant(
        ...     voice_provider=voice_provider,
        ...     chat_agent=chat_agent,
        ... )
        >>>
        >>> # Process voice input
        >>> audio_bytes = Path("recording.mp3").read_bytes()
        >>> response = await assistant.process_voice_input(audio_bytes)
        >>>
        >>> # Play response audio
        >>> response.synthesis.save_to_file("response.mp3")
    """

    def __init__(
        self,
        voice_provider: BaseVoiceProvider,
        chat_agent: ChatAgent,
        enable_tts: bool = True,
        auto_detect_language: bool = True,
    ) -> None:
        """
        Initialize voice assistant.

        Args:
            voice_provider: Voice provider for STT/TTS
            chat_agent: Chat agent for LLM processing
            enable_tts: Enable text-to-speech for responses
            auto_detect_language: Auto-detect language in STT
        """
        self.voice_provider = voice_provider
        self.chat_agent = chat_agent
        self.enable_tts = enable_tts
        self.auto_detect_language = auto_detect_language

        logger.info(
            "voice_assistant_initialized",
            provider=voice_provider.provider_name,
            tts_enabled=enable_tts,
            auto_detect=auto_detect_language,
        )

    async def process_voice_input(
        self,
        audio: bytes | Path | BinaryIO,
        context: ChatContext | None = None,
        stt_language: str | None = None,
        tts_voice: str | None = None,
        save_audio: Path | None = None,
    ) -> VoiceResponse:
        """
        Process voice input through complete STT → LLM → TTS pipeline.

        Args:
            audio: Audio input (bytes, file path, or file-like object)
            context: Optional chat context (conversation history, etc.)
            stt_language: Language code for STT (auto-detect if None)
            tts_voice: Voice for TTS (uses config default if None)
            save_audio: Optional path to save synthesized audio

        Returns:
            VoiceResponse with transcription, LLM response, and synthesis

        Raises:
            VoiceProviderError: If STT/TTS fails
            Exception: If LLM processing fails
        """
        overall_start = time.time()

        # Phase 1: Speech-to-Text
        logger.info("voice_assistant_stt_started")
        stt_start = time.time()

        transcription = await self.voice_provider.transcribe(
            audio=audio,
            language=stt_language if not self.auto_detect_language else None,
        )

        stt_latency = (time.time() - stt_start) * 1000
        logger.info(
            "voice_assistant_stt_completed",
            text_length=len(transcription.text),
            language=transcription.language,
            latency_ms=stt_latency,
        )

        # Phase 2: LLM Processing
        logger.info("voice_assistant_llm_started", text=transcription.text[:100])
        llm_start = time.time()

        # Create or update context
        if context is None:
            context = ChatContext(user_input=transcription.text)
        else:
            # Update with transcribed text
            context.user_input = transcription.text

        # Execute chat agent
        chat_response = await self.chat_agent.execute(context)

        llm_latency = (time.time() - llm_start) * 1000
        logger.info(
            "voice_assistant_llm_completed",
            response_length=len(chat_response.content),
            latency_ms=llm_latency,
        )

        # Phase 3: Text-to-Speech (if enabled)
        synthesis = None
        tts_latency = None

        if self.enable_tts:
            logger.info("voice_assistant_tts_started", text_length=len(chat_response.content))
            tts_start = time.time()

            # Determine voice based on detected language
            selected_voice = tts_voice
            if selected_voice is None and transcription.language:
                selected_voice = self.voice_provider.config.get_voice_for_language(
                    transcription.language
                )

            synthesis = await self.voice_provider.synthesize(
                text=chat_response.content,
                voice=selected_voice,
                language=transcription.language,
            )

            tts_latency = (time.time() - tts_start) * 1000
            logger.info(
                "voice_assistant_tts_completed",
                audio_size_kb=len(synthesis.audio_data) / 1024,
                latency_ms=tts_latency,
            )

            # Save audio if requested
            if save_audio:
                synthesis.save_to_file(save_audio)
                logger.debug("voice_assistant_audio_saved", path=str(save_audio))

        # Build complete response
        total_latency = (time.time() - overall_start) * 1000

        response = VoiceResponse(
            transcription=transcription,
            llm_response=chat_response.content,
            llm_metadata={
                "provider": chat_response.provider,
                "model": chat_response.model,
                "tokens": chat_response.usage.total_tokens,
                "cost_usd": chat_response.usage.estimated_cost_usd,
            },
            synthesis=synthesis,
            total_latency_ms=total_latency,
            stt_latency_ms=stt_latency,
            llm_latency_ms=llm_latency,
            tts_latency_ms=tts_latency,
        )

        logger.info(
            "voice_assistant_completed",
            total_latency_ms=total_latency,
            stt_ms=stt_latency,
            llm_ms=llm_latency,
            tts_ms=tts_latency,
            tokens=chat_response.usage.total_tokens,
        )

        return response

    async def process_voice_input_streaming(
        self,
        audio: bytes | Path | BinaryIO,
        context: ChatContext | None = None,
        stt_language: str | None = None,
        tts_voice: str | None = None,
    ) -> tuple[VoiceResponse, BinaryIO]:
        """
        Process voice input with streaming TTS for lower latency.

        This method transcribes audio, processes with LLM, and streams
        TTS audio as it's generated for faster perceived response time.

        Args:
            audio: Audio input (bytes, file path, or file-like object)
            context: Optional chat context
            stt_language: Language code for STT
            tts_voice: Voice for TTS

        Returns:
            Tuple of (VoiceResponse, audio_stream) where audio_stream
            yields audio chunks as they're generated

        Raises:
            VoiceProviderError: If STT/TTS fails
        """
        overall_start = time.time()

        # Phase 1: Speech-to-Text
        stt_start = time.time()
        transcription = await self.voice_provider.transcribe(
            audio=audio,
            language=stt_language if not self.auto_detect_language else None,
        )
        stt_latency = (time.time() - stt_start) * 1000

        # Phase 2: LLM Processing
        llm_start = time.time()

        if context is None:
            context = ChatContext(user_input=transcription.text)
        else:
            context.user_input = transcription.text

        chat_response = await self.chat_agent.execute(context)
        llm_latency = (time.time() - llm_start) * 1000

        # Phase 3: Streaming TTS
        tts_start = time.time()

        selected_voice = tts_voice
        if selected_voice is None and transcription.language:
            selected_voice = self.voice_provider.config.get_voice_for_language(
                transcription.language
            )

        # Start streaming synthesis
        audio_chunks = []
        async for chunk in self.voice_provider.synthesize_stream(
            text=chat_response.content,
            voice=selected_voice,
            language=transcription.language,
        ):
            audio_chunks.append(chunk)

        tts_latency = (time.time() - tts_start) * 1000

        # Combine all audio chunks
        complete_audio = b"".join(audio_chunks)

        # Create synthesis result
        from openfatture.ai.voice.models import SynthesisResult

        synthesis = SynthesisResult(
            audio_data=complete_audio,
            audio_format=self.voice_provider.config.tts_format,
            text_length=len(chat_response.content),
            voice=selected_voice or self.voice_provider.config.tts_voice.value,
        )

        # Build response
        total_latency = (time.time() - overall_start) * 1000

        response = VoiceResponse(
            transcription=transcription,
            llm_response=chat_response.content,
            llm_metadata={
                "provider": chat_response.provider,
                "model": chat_response.model,
                "tokens": chat_response.usage.total_tokens,
            },
            synthesis=synthesis,
            total_latency_ms=total_latency,
            stt_latency_ms=stt_latency,
            llm_latency_ms=llm_latency,
            tts_latency_ms=tts_latency,
        )

        logger.info(
            "voice_assistant_streaming_completed",
            total_latency_ms=total_latency,
            chunks=len(audio_chunks),
        )

        # Create audio stream from complete audio data
        audio_stream = io.BytesIO(complete_audio)
        return response, audio_stream

    async def transcribe_only(
        self,
        audio: bytes | Path | BinaryIO,
        language: str | None = None,
    ) -> str:
        """
        Transcribe audio without LLM processing (STT only).

        Useful for testing or when you only need transcription.

        Args:
            audio: Audio input
            language: Language code (auto-detect if None)

        Returns:
            Transcribed text

        Raises:
            VoiceProviderError: If transcription fails
        """
        transcription = await self.voice_provider.transcribe(
            audio=audio,
            language=language if not self.auto_detect_language else None,
        )

        logger.info(
            "voice_assistant_transcribe_only",
            text_length=len(transcription.text),
            language=transcription.language,
        )

        return transcription.text

    async def synthesize_only(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
        output_format: AudioFormat | None = None,
        save_to: Path | None = None,
    ) -> bytes:
        """
        Synthesize text to speech without LLM processing (TTS only).

        Useful for testing or when you have pre-generated text.

        Args:
            text: Text to synthesize
            voice: Voice to use
            language: Language code
            output_format: Audio format
            save_to: Optional path to save audio

        Returns:
            Audio data (bytes)

        Raises:
            VoiceProviderError: If synthesis fails
        """
        synthesis = await self.voice_provider.synthesize(
            text=text,
            voice=voice,
            language=language,
            output_format=output_format,
        )

        if save_to:
            synthesis.save_to_file(save_to)
            logger.debug("voice_assistant_audio_saved", path=str(save_to))

        logger.info(
            "voice_assistant_synthesize_only",
            text_length=len(text),
            audio_size_kb=len(synthesis.audio_data) / 1024,
        )

        return synthesis.audio_data

    def get_stats(self) -> dict[str, Any]:
        """
        Get assistant statistics and configuration.

        Returns:
            Dictionary with assistant info
        """
        return {
            "voice_provider": self.voice_provider.provider_name,
            "llm_provider": self.chat_agent.provider.provider_name,
            "llm_model": self.chat_agent.provider.model,
            "tts_enabled": self.enable_tts,
            "auto_detect_language": self.auto_detect_language,
            "supported_languages": self.voice_provider.supported_languages[:10],  # First 10
            "supported_voices": self.voice_provider.supported_voices,
            "streaming_tts": self.voice_provider.supports_streaming_tts,
        }
