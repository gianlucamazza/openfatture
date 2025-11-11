"""OpenAI voice provider implementation (Whisper + TTS)."""

import time
from collections.abc import AsyncIterator
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from openai import AsyncOpenAI, OpenAIError

from openfatture.ai.voice.base import (
    BaseVoiceProvider,
    VoiceProviderAuthError,
    VoiceProviderError,
    VoiceProviderRateLimitError,
    VoiceProviderTimeoutError,
    VoiceProviderUnavailableError,
    VoiceProviderValidationError,
)
from openfatture.ai.voice.models import (
    AudioFormat,
    SynthesisResult,
    TranscriptionResult,
    TTSVoice,
    VoiceConfig,
)
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIVoiceProvider(BaseVoiceProvider):
    """
    OpenAI voice provider using Whisper (STT) and TTS API.

    Features:
    - Whisper: Multi-language STT with 100+ languages
    - TTS: High-quality speech synthesis with 6 voices
    - Streaming TTS for reduced latency
    - Auto-language detection

    Supported formats:
    - STT input: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
    - TTS output: mp3, opus, aac, flac
    """

    # Whisper supported languages (ISO 639-1 codes)
    # Full list: https://github.com/openai/whisper#available-models-and-languages
    WHISPER_LANGUAGES = [
        "af",
        "ar",
        "hy",
        "az",
        "be",
        "bs",
        "bg",
        "ca",
        "zh",
        "hr",
        "cs",
        "da",
        "nl",
        "en",
        "et",
        "fi",
        "fr",
        "gl",
        "de",
        "el",
        "he",
        "hi",
        "hu",
        "is",
        "id",
        "it",
        "ja",
        "kn",
        "kk",
        "ko",
        "lv",
        "lt",
        "mk",
        "ms",
        "mr",
        "mi",
        "ne",
        "no",
        "fa",
        "pl",
        "pt",
        "ro",
        "ru",
        "sr",
        "sk",
        "sl",
        "es",
        "sw",
        "sv",
        "tl",
        "ta",
        "th",
        "tr",
        "uk",
        "ur",
        "vi",
        "cy",
    ]

    # TTS supported voices
    TTS_VOICES = [voice.value for voice in TTSVoice]

    def __init__(self, config: VoiceConfig) -> None:
        """
        Initialize OpenAI voice provider.

        Args:
            config: Voice configuration with API key
        """
        super().__init__(config)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=config.api_key)

        logger.info(
            "openai_voice_provider_initialized",
            stt_model=config.stt_model.value,
            tts_model=config.tts_model.value,
            tts_voice=config.tts_voice.value,
            streaming_enabled=config.enable_streaming_tts,
        )

    async def transcribe(
        self,
        audio: bytes | Path | BinaryIO,
        language: str | None = None,
        prompt: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe speech to text using Whisper API.

        Args:
            audio: Audio data (bytes, file path, or file-like object)
            language: Language code (ISO 639-1). Auto-detect if None.
            prompt: Optional prompt to guide transcription

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            VoiceProviderError: If transcription fails
        """
        start_time = time.time()

        try:
            # Prepare audio input
            audio_file = self._prepare_audio_input(audio)

            # Prepare API parameters
            params = {
                "model": self.config.stt_model.value,
                "file": audio_file,
                "response_format": "verbose_json",  # Get metadata
            }

            # Add optional parameters
            if language:
                if not self._validate_language(language):
                    raise VoiceProviderValidationError(
                        f"Unsupported language: {language}",
                        provider=self.provider_name,
                    )
                params["language"] = language
            elif self.config.stt_language:
                params["language"] = self.config.stt_language

            stt_prompt = prompt or self.config.stt_prompt
            if stt_prompt:
                params["prompt"] = stt_prompt

            # Call Whisper API
            logger.debug(
                "whisper_transcription_started",
                language=params.get("language", "auto"),
                has_prompt=bool(params.get("prompt")),
            )

            response = await self.client.audio.transcriptions.create(**params)

            # Extract transcription result
            transcription = TranscriptionResult(
                text=response.text,
                language=response.language if hasattr(response, "language") else language,
                confidence=None,  # Whisper doesn't provide confidence scores
                duration_seconds=response.duration if hasattr(response, "duration") else None,
                metadata={
                    "model": self.config.stt_model.value,
                    "prompt": params.get("prompt"),
                },
            )

            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                "whisper_transcription_completed",
                text_length=len(transcription.text),
                language=transcription.language,
                latency_ms=latency_ms,
            )

            return transcription

        except OpenAIError as e:
            raise self._handle_openai_error(e, "STT transcription")

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
        output_format: AudioFormat | None = None,
    ) -> SynthesisResult:
        """
        Synthesize text to speech using OpenAI TTS API.

        Args:
            text: Text to synthesize (max 4096 characters)
            voice: Voice name (uses config default if None)
            language: Language code (ignored for OpenAI TTS - voice determines accent)
            output_format: Audio format (uses config default if None)

        Returns:
            SynthesisResult with audio data and metadata

        Raises:
            VoiceProviderError: If synthesis fails
        """
        start_time = time.time()

        try:
            # Validate text length (OpenAI limit: 4096 chars)
            if len(text) > 4096:
                raise VoiceProviderValidationError(
                    f"Text too long: {len(text)} chars (max 4096)",
                    provider=self.provider_name,
                )

            # Determine voice (language-based if provided)
            selected_voice = self._select_voice(voice, language)

            # Determine output format
            selected_format = output_format or self.config.tts_format

            # Prepare API parameters
            params = {
                "model": self.config.tts_model.value,
                "voice": selected_voice,
                "input": text,
                "response_format": selected_format.value,
                "speed": self.config.tts_speed,
            }

            logger.debug(
                "tts_synthesis_started",
                text_length=len(text),
                voice=selected_voice,
                format=selected_format.value,
                speed=self.config.tts_speed,
            )

            # Call TTS API (non-streaming)
            response = await self.client.audio.speech.create(**params)

            # Read audio data
            audio_data = response.read()

            # Create synthesis result
            synthesis = SynthesisResult(
                audio_data=audio_data,
                audio_format=selected_format,
                duration_seconds=None,  # Not provided by API
                text_length=len(text),
                voice=selected_voice,
                metadata={
                    "model": self.config.tts_model.value,
                    "speed": self.config.tts_speed,
                    "format": selected_format.value,
                },
            )

            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                "tts_synthesis_completed",
                text_length=len(text),
                audio_size_kb=len(audio_data) / 1024,
                latency_ms=latency_ms,
            )

            return synthesis

        except OpenAIError as e:
            raise self._handle_openai_error(e, "TTS synthesis")

    async def synthesize_stream(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
        output_format: AudioFormat | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text to speech with streaming for lower latency.

        Args:
            text: Text to synthesize (max 4096 characters)
            voice: Voice name (uses config default if None)
            language: Language code (ignored for OpenAI TTS)
            output_format: Audio format (uses config default if None)

        Yields:
            Audio data chunks (bytes)

        Raises:
            VoiceProviderError: If synthesis fails
        """
        start_time = time.time()
        total_bytes = 0

        try:
            # Validate text length
            if len(text) > 4096:
                raise VoiceProviderValidationError(
                    f"Text too long: {len(text)} chars (max 4096)",
                    provider=self.provider_name,
                )

            # Determine voice and format
            selected_voice = self._select_voice(voice, language)
            selected_format = output_format or self.config.tts_format

            # Prepare API parameters
            params = {
                "model": self.config.tts_model.value,
                "voice": selected_voice,
                "input": text,
                "response_format": selected_format.value,
                "speed": self.config.tts_speed,
            }

            logger.debug(
                "tts_streaming_started",
                text_length=len(text),
                voice=selected_voice,
                format=selected_format.value,
            )

            # Call TTS API with streaming
            async with self.client.audio.speech.with_streaming_response.create(
                **params
            ) as response:
                # Stream audio chunks
                async for chunk in response.iter_bytes(chunk_size=self.config.chunk_size_bytes):
                    if chunk:  # Filter out empty chunks
                        total_bytes += len(chunk)
                        yield chunk

            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                "tts_streaming_completed",
                text_length=len(text),
                audio_size_kb=total_bytes / 1024,
                chunks_streamed=total_bytes // self.config.chunk_size_bytes,
                latency_ms=latency_ms,
            )

        except OpenAIError as e:
            raise self._handle_openai_error(e, "TTS streaming synthesis")

    async def health_check(self) -> bool:
        """
        Check if OpenAI voice API is available.

        Performs a minimal test request to verify connectivity.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Test with minimal TTS request
            test_text = "test"
            await self.client.audio.speech.create(
                model="tts-1",  # Use fast model for health check
                voice="alloy",
                input=test_text,
                response_format="mp3",
            )
            logger.debug("openai_voice_health_check_passed")
            return True

        except Exception as e:
            logger.warning(
                "openai_voice_health_check_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "openai"

    @property
    def supports_streaming_tts(self) -> bool:
        """OpenAI TTS supports streaming."""
        return True

    @property
    def supported_languages(self) -> list[str]:
        """Get Whisper supported languages."""
        return self.WHISPER_LANGUAGES

    @property
    def supported_voices(self) -> list[str]:
        """Get TTS supported voices."""
        return self.TTS_VOICES

    def _prepare_audio_input(self, audio: bytes | Path | BinaryIO) -> BinaryIO:
        """
        Prepare audio input for API.

        Args:
            audio: Audio data in various formats

        Returns:
            File-like object ready for API

        Raises:
            FileNotFoundError: If path doesn't exist
        """
        if isinstance(audio, bytes):
            return BytesIO(audio)
        elif isinstance(audio, Path):
            audio_data = self._load_audio_file(audio)
            return BytesIO(audio_data)
        else:
            # Already a file-like object
            return audio

    def _select_voice(self, voice: str | None, language: str | None) -> str:
        """
        Select appropriate TTS voice based on language and preferences.

        Args:
            voice: Explicit voice name (takes priority)
            language: Language code for voice mapping

        Returns:
            Selected voice name
        """
        # Explicit voice takes priority
        if voice:
            if voice not in self.TTS_VOICES:
                logger.warning(
                    "invalid_voice_fallback",
                    requested_voice=voice,
                    fallback=self.config.tts_voice.value,
                )
                return self.config.tts_voice.value
            return voice

        # Use language mapping
        if language:
            mapped_voice = self.config.get_voice_for_language(language)
            logger.debug(
                "voice_selected_by_language",
                language=language,
                voice=mapped_voice,
            )
            return mapped_voice

        # Fallback to config default
        return self.config.tts_voice.value

    def _handle_openai_error(self, error: OpenAIError, operation: str) -> VoiceProviderError:
        """
        Convert OpenAI errors to VoiceProviderError subclasses.

        Args:
            error: Original OpenAI error
            operation: Operation description (for logging)

        Returns:
            Appropriate VoiceProviderError subclass
        """
        error_message = f"{operation} failed: {str(error)}"

        # Authentication errors
        if "authentication" in str(error).lower() or "api_key" in str(error).lower():
            logger.error(
                "openai_voice_auth_error",
                operation=operation,
                error=str(error),
            )
            return VoiceProviderAuthError(
                error_message,
                provider=self.provider_name,
                original_error=error,
            )

        # Rate limit errors
        if "rate_limit" in str(error).lower() or "quota" in str(error).lower():
            logger.warning(
                "openai_voice_rate_limit",
                operation=operation,
                error=str(error),
            )
            return VoiceProviderRateLimitError(
                error_message,
                provider=self.provider_name,
                original_error=error,
            )

        # Timeout errors
        if "timeout" in str(error).lower():
            logger.warning(
                "openai_voice_timeout",
                operation=operation,
                error=str(error),
            )
            return VoiceProviderTimeoutError(
                error_message,
                provider=self.provider_name,
                original_error=error,
            )

        # Service unavailable
        if "503" in str(error) or "unavailable" in str(error).lower():
            logger.warning(
                "openai_voice_unavailable",
                operation=operation,
                error=str(error),
            )
            return VoiceProviderUnavailableError(
                error_message,
                provider=self.provider_name,
                original_error=error,
            )

        # Validation errors (bad input)
        if "400" in str(error) or "invalid" in str(error).lower():
            logger.warning(
                "openai_voice_validation_error",
                operation=operation,
                error=str(error),
            )
            return VoiceProviderValidationError(
                error_message,
                provider=self.provider_name,
                original_error=error,
            )

        # Generic error
        logger.error(
            "openai_voice_error",
            operation=operation,
            error=str(error),
            error_type=type(error).__name__,
        )
        return VoiceProviderError(
            error_message,
            provider=self.provider_name,
            original_error=error,
        )
