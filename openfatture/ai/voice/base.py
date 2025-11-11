"""Base voice provider abstraction."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import BinaryIO

from openfatture.ai.voice.models import (
    AudioFormat,
    SynthesisResult,
    TranscriptionResult,
    VoiceConfig,
)


class BaseVoiceProvider(ABC):
    """
    Abstract base class for voice providers.

    Provides a unified interface for different voice services
    (OpenAI Whisper/TTS, Google Cloud, Azure, etc.).

    All providers must implement:
    - Speech-to-Text (STT) transcription
    - Text-to-Speech (TTS) synthesis
    - Streaming TTS support
    - Health checks
    """

    def __init__(
        self,
        config: VoiceConfig,
    ) -> None:
        """
        Initialize voice provider.

        Args:
            config: Voice configuration
        """
        self.config = config

    @abstractmethod
    async def transcribe(
        self,
        audio: bytes | Path | BinaryIO,
        language: str | None = None,
        prompt: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe speech to text (STT).

        Args:
            audio: Audio data (bytes, file path, or file-like object)
            language: Language code (ISO 639-1). Auto-detect if None.
            prompt: Optional prompt to guide transcription (e.g., technical terms)

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            VoiceProviderError: If transcription fails
        """
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
        output_format: AudioFormat | None = None,
    ) -> SynthesisResult:
        """
        Synthesize text to speech (TTS).

        Args:
            text: Text to synthesize
            voice: Voice name (uses config default if None)
            language: Language code (uses config or auto-detect if None)
            output_format: Audio format (uses config default if None)

        Returns:
            SynthesisResult with audio data and metadata

        Raises:
            VoiceProviderError: If synthesis fails
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None,
        output_format: AudioFormat | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text to speech with streaming (TTS).

        Yields audio chunks as they become available for lower latency.

        Args:
            text: Text to synthesize
            voice: Voice name (uses config default if None)
            language: Language code (uses config or auto-detect if None)
            output_format: Audio format (uses config default if None)

        Yields:
            Audio data chunks (bytes)

        Raises:
            VoiceProviderError: If synthesis fails
        """
        pass
        yield b""  # pragma: no cover

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if voice provider is available and working.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'openai', 'google', 'azure')."""
        pass

    @property
    @abstractmethod
    def supports_streaming_tts(self) -> bool:
        """Check if this provider supports TTS streaming."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Get list of supported language codes (ISO 639-1)."""
        pass

    @property
    @abstractmethod
    def supported_voices(self) -> list[str]:
        """Get list of supported voice names."""
        pass

    def _load_audio_file(self, audio_path: Path | str) -> bytes:
        """
        Load audio file to bytes.

        Args:
            audio_path: Path to audio file

        Returns:
            Audio data as bytes

        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        return path.read_bytes()

    def _validate_language(self, language: str | None) -> bool:
        """
        Validate if language is supported.

        Args:
            language: Language code (ISO 639-1)

        Returns:
            True if supported or None, False otherwise
        """
        if language is None:
            return True
        return language.lower() in [lang.lower() for lang in self.supported_languages]


class VoiceProviderError(Exception):
    """Base exception for voice provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize voice provider error.

        Args:
            message: Error message
            provider: Provider name
            original_error: Original exception if wrapped
        """
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class VoiceProviderAuthError(VoiceProviderError):
    """Authentication error (invalid API key, etc.)."""

    pass


class VoiceProviderRateLimitError(VoiceProviderError):
    """Rate limit exceeded."""

    pass


class VoiceProviderTimeoutError(VoiceProviderError):
    """Request timeout."""

    pass


class VoiceProviderUnavailableError(VoiceProviderError):
    """Provider service unavailable."""

    pass


class VoiceProviderValidationError(VoiceProviderError):
    """Invalid input (unsupported format, language, etc.)."""

    pass
