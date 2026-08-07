"""Voice module data models and types."""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AudioFormat(str, Enum):
    """Supported audio formats for voice processing."""

    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    WEBM = "webm"


class TTSVoice(str, Enum):
    """Available TTS voices (OpenAI)."""

    ALLOY = "alloy"  # Neutral, balanced
    ECHO = "echo"  # Male, clear
    FABLE = "fable"  # British, expressive
    ONYX = "onyx"  # Male, deep
    NOVA = "nova"  # Female, warm
    SHIMMER = "shimmer"  # Female, soft


class TTSModel(str, Enum):
    """Available TTS models (OpenAI)."""

    TTS_1 = "tts-1"  # Fast, lower quality
    TTS_1_HD = "tts-1-hd"  # High quality, slower


class STTModel(str, Enum):
    """Available STT models (OpenAI Whisper)."""

    WHISPER_1 = "whisper-1"  # Multi-language, auto-detect


class VoiceConfig(BaseModel):
    """Configuration for voice providers."""

    # Provider settings
    provider: str = Field(default="openai", description="Voice provider (openai, etc.)")
    api_key: str | None = Field(default=None, description="API key for voice provider")

    # STT settings
    stt_model: STTModel = Field(default=STTModel.WHISPER_1, description="Speech-to-text model")
    stt_language: str | None = Field(
        default=None,
        description="Language code (auto-detect if None). ISO 639-1 format (it, en, fr, ...)",
    )
    stt_prompt: str | None = Field(
        default=None, description="Optional prompt to guide STT transcription style"
    )

    # TTS settings
    tts_model: TTSModel = Field(default=TTSModel.TTS_1_HD, description="Text-to-speech model")
    tts_voice: TTSVoice = Field(default=TTSVoice.NOVA, description="TTS voice to use")
    tts_speed: float = Field(default=1.0, ge=0.25, le=4.0, description="TTS speed (0.25-4.0)")
    tts_format: AudioFormat = Field(default=AudioFormat.MP3, description="Output audio format")

    # Multi-language voice mapping
    voice_map: dict[str, str] = Field(
        default_factory=lambda: {
            "it": "nova",  # Italian - warm female
            "en": "alloy",  # English - neutral
            "fr": "shimmer",  # French - soft female
            "de": "echo",  # German - clear male
            "es": "fable",  # Spanish - expressive
        },
        description="Language code to preferred voice mapping",
    )

    # Performance settings
    enable_streaming_tts: bool = Field(
        default=True, description="Enable TTS streaming for lower latency"
    )
    chunk_size_bytes: int = Field(default=4096, description="Audio chunk size for streaming")

    # Timeouts
    stt_timeout: int = Field(default=30, description="STT request timeout in seconds")
    tts_timeout: int = Field(default=60, description="TTS request timeout in seconds")

    def get_voice_for_language(self, language: str) -> str:
        """
        Get preferred TTS voice for a language.

        Args:
            language: Language code (ISO 639-1)

        Returns:
            Voice name (falls back to default if not mapped)
        """
        return self.voice_map.get(language.lower(), self.tts_voice.value)


class TranscriptionResult(BaseModel):
    """Result from speech-to-text transcription."""

    text: str = Field(..., description="Transcribed text")
    language: str | None = Field(default=None, description="Detected language (ISO 639-1)")
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Transcription confidence (0-1)"
    )
    duration_seconds: float | None = Field(default=None, description="Audio duration in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")


class SynthesisResult(BaseModel):
    """Result from text-to-speech synthesis."""

    audio_data: bytes = Field(..., description="Synthesized audio data")
    audio_format: AudioFormat = Field(..., description="Audio format")
    duration_seconds: float | None = Field(default=None, description="Audio duration in seconds")
    text_length: int = Field(..., description="Input text length (characters)")
    voice: str = Field(..., description="Voice used for synthesis")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")

    def save_to_file(self, path: Path | str) -> None:
        """
        Save audio data to file.

        Args:
            path: Output file path
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self.audio_data)


class VoiceResponse(BaseModel):
    """Complete voice interaction response (STT + LLM + TTS)."""

    # STT phase
    transcription: TranscriptionResult = Field(..., description="Speech-to-text result")

    # LLM phase
    llm_response: str = Field(..., description="LLM text response")
    llm_metadata: dict[str, Any] = Field(
        default_factory=dict, description="LLM response metadata (tokens, cost, etc.)"
    )

    # TTS phase
    synthesis: SynthesisResult | None = Field(
        default=None, description="Text-to-speech result (if enabled)"
    )

    # Overall metrics
    total_latency_ms: float = Field(..., description="Total processing time in milliseconds")
    stt_latency_ms: float = Field(..., description="STT processing time")
    llm_latency_ms: float = Field(..., description="LLM processing time")
    tts_latency_ms: float | None = Field(default=None, description="TTS processing time")

    def get_audio_file_path(self) -> Path | None:
        """Get path to saved audio file if synthesis was performed."""
        if self.synthesis:
            return Path(self.synthesis.metadata.get("file_path", ""))
        return None
