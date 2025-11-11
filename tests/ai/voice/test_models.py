"""Tests for voice models."""

import pytest
from pydantic import ValidationError

from openfatture.ai.voice.models import (
    AudioFormat,
    STTModel,
    SynthesisResult,
    TranscriptionResult,
    TTSModel,
    TTSVoice,
    VoiceConfig,
    VoiceResponse,
)


class TestVoiceConfig:
    """Tests for VoiceConfig model."""

    def test_default_config(self):
        """Test default configuration."""
        config = VoiceConfig()

        assert config.provider == "openai"
        assert config.stt_model == STTModel.WHISPER_1
        assert config.tts_model == TTSModel.TTS_1_HD
        assert config.tts_voice == TTSVoice.NOVA
        assert config.tts_speed == 1.0
        assert config.tts_format == AudioFormat.MP3
        assert config.enable_streaming_tts is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = VoiceConfig(
            provider="custom",
            api_key="test-key",
            stt_model=STTModel.WHISPER_1,
            stt_language="it",
            tts_model=TTSModel.TTS_1,
            tts_voice=TTSVoice.ALLOY,
            tts_speed=1.5,
            tts_format=AudioFormat.OPUS,
            enable_streaming_tts=False,
        )

        assert config.provider == "custom"
        assert config.api_key == "test-key"
        assert config.stt_language == "it"
        assert config.tts_voice == TTSVoice.ALLOY
        assert config.tts_speed == 1.5
        assert config.tts_format == AudioFormat.OPUS
        assert config.enable_streaming_tts is False

    def test_tts_speed_validation(self):
        """Test TTS speed validation."""
        # Valid speeds
        VoiceConfig(tts_speed=0.25)
        VoiceConfig(tts_speed=1.0)
        VoiceConfig(tts_speed=4.0)

        # Invalid speeds (should not raise due to ge/le validators)
        with pytest.raises(ValidationError):
            VoiceConfig(tts_speed=0.2)  # Too slow

        with pytest.raises(ValidationError):
            VoiceConfig(tts_speed=5.0)  # Too fast

    def test_voice_mapping(self):
        """Test get_voice_for_language method."""
        config = VoiceConfig()

        # Test predefined mappings
        assert config.get_voice_for_language("it") == "nova"
        assert config.get_voice_for_language("en") == "alloy"
        assert config.get_voice_for_language("fr") == "shimmer"

        # Test fallback to default
        assert config.get_voice_for_language("unknown") == config.tts_voice.value

        # Test case insensitivity
        assert config.get_voice_for_language("IT") == "nova"

    def test_custom_voice_mapping(self):
        """Test custom voice mapping."""
        custom_map = {
            "it": "onyx",
            "en": "fable",
        }
        config = VoiceConfig(voice_map=custom_map)

        assert config.get_voice_for_language("it") == "onyx"
        assert config.get_voice_for_language("en") == "fable"
        # Fallback for unmapped language
        assert config.get_voice_for_language("fr") == config.tts_voice.value


class TestTranscriptionResult:
    """Tests for TranscriptionResult model."""

    def test_basic_transcription(self):
        """Test basic transcription result."""
        result = TranscriptionResult(
            text="Hello, this is a test.",
            language="en",
        )

        assert result.text == "Hello, this is a test."
        assert result.language == "en"
        assert result.confidence is None
        assert result.duration_seconds is None

    def test_full_transcription(self):
        """Test transcription with all fields."""
        result = TranscriptionResult(
            text="Ciao, questo è un test.",
            language="it",
            confidence=0.95,
            duration_seconds=3.5,
            metadata={"model": "whisper-1", "prompt": "invoice terminology"},
        )

        assert result.text == "Ciao, questo è un test."
        assert result.language == "it"
        assert result.confidence == 0.95
        assert result.duration_seconds == 3.5
        assert result.metadata["model"] == "whisper-1"


class TestSynthesisResult:
    """Tests for SynthesisResult model."""

    def test_synthesis_result(self):
        """Test synthesis result."""
        audio_data = b"fake audio data"
        result = SynthesisResult(
            audio_data=audio_data,
            audio_format=AudioFormat.MP3,
            text_length=100,
            voice="nova",
        )

        assert result.audio_data == audio_data
        assert result.audio_format == AudioFormat.MP3
        assert result.text_length == 100
        assert result.voice == "nova"
        assert result.duration_seconds is None

    def test_synthesis_with_metadata(self):
        """Test synthesis with metadata."""
        result = SynthesisResult(
            audio_data=b"test",
            audio_format=AudioFormat.OPUS,
            text_length=50,
            voice="alloy",
            duration_seconds=2.5,
            metadata={"model": "tts-1-hd", "speed": 1.2},
        )

        assert result.duration_seconds == 2.5
        assert result.metadata["model"] == "tts-1-hd"
        assert result.metadata["speed"] == 1.2


class TestVoiceResponse:
    """Tests for VoiceResponse model."""

    def test_voice_response(self):
        """Test complete voice interaction response."""
        transcription = TranscriptionResult(
            text="What is the total revenue?",
            language="en",
        )

        synthesis = SynthesisResult(
            audio_data=b"fake audio",
            audio_format=AudioFormat.MP3,
            text_length=50,
            voice="nova",
        )

        response = VoiceResponse(
            transcription=transcription,
            llm_response="The total revenue is €45,000.",
            synthesis=synthesis,
            total_latency_ms=3500,
            stt_latency_ms=1200,
            llm_latency_ms=1500,
            tts_latency_ms=800,
        )

        assert response.transcription.text == "What is the total revenue?"
        assert response.llm_response == "The total revenue is €45,000."
        assert response.synthesis is not None
        assert response.total_latency_ms == 3500
        assert response.stt_latency_ms == 1200
        assert response.llm_latency_ms == 1500
        assert response.tts_latency_ms == 800

    def test_voice_response_without_tts(self):
        """Test voice response without TTS (STT only)."""
        transcription = TranscriptionResult(
            text="Test transcription",
            language="en",
        )

        response = VoiceResponse(
            transcription=transcription,
            llm_response="LLM text response",
            synthesis=None,  # No TTS
            total_latency_ms=2000,
            stt_latency_ms=1000,
            llm_latency_ms=1000,
            tts_latency_ms=None,
        )

        assert response.synthesis is None
        assert response.tts_latency_ms is None
        assert response.get_audio_file_path() is None


class TestEnums:
    """Tests for voice enums."""

    def test_audio_formats(self):
        """Test AudioFormat enum."""
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.OPUS.value == "opus"
        assert AudioFormat.AAC.value == "aac"
        assert AudioFormat.FLAC.value == "flac"
        assert AudioFormat.WAV.value == "wav"

    def test_tts_voices(self):
        """Test TTSVoice enum."""
        assert TTSVoice.ALLOY.value == "alloy"
        assert TTSVoice.NOVA.value == "nova"
        assert TTSVoice.SHIMMER.value == "shimmer"

        # Verify all 6 voices exist
        assert len(list(TTSVoice)) == 6

    def test_tts_models(self):
        """Test TTSModel enum."""
        assert TTSModel.TTS_1.value == "tts-1"
        assert TTSModel.TTS_1_HD.value == "tts-1-hd"

    def test_stt_models(self):
        """Test STTModel enum."""
        assert STTModel.WHISPER_1.value == "whisper-1"
