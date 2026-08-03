"""Tests for voice provider factory."""

import os
from unittest.mock import patch

import pytest

from openfatture.ai.voice.factory import (
    create_voice_provider,
    get_default_voice_config,
)
from openfatture.ai.voice.models import AudioFormat, STTModel, TTSModel, TTSVoice, VoiceConfig
from openfatture.ai.voice.openai_voice import OpenAIVoiceProvider


class TestVoiceProviderFactory:
    """Tests for create_voice_provider factory."""

    def test_create_openai_provider_with_config(self):
        """Test creating OpenAI provider with explicit config."""
        config = VoiceConfig(
            provider="openai",
            api_key="test-key",
            tts_voice=TTSVoice.ALLOY,
        )

        provider = create_voice_provider(config=config)

        assert isinstance(provider, OpenAIVoiceProvider)
        assert provider.config.api_key == "test-key"
        assert provider.config.tts_voice == TTSVoice.ALLOY
        assert provider.provider_name == "openai"

    def test_create_provider_without_api_key(self):
        """Test factory raises error without API key."""
        config = VoiceConfig(
            provider="openai",
            api_key=None,  # Missing API key
        )

        with pytest.raises(RuntimeError, match="API key required"):
            create_voice_provider(config=config)

    def test_unsupported_provider(self):
        """Test factory raises error for unsupported provider."""
        config = VoiceConfig(
            provider="unsupported-provider",
            api_key="test-key",
        )

        with pytest.raises(ValueError, match="Unsupported voice provider"):
            create_voice_provider(config=config)

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_VOICE_PROVIDER": "openai",
            "OPENAI_API_KEY": "env-test-key",
            "OPENFATTURE_VOICE_TTS_VOICE": "echo",
            "OPENFATTURE_VOICE_TTS_SPEED": "1.5",
            "OPENFATTURE_VOICE_STREAMING": "false",
        },
    )
    def test_create_provider_from_env(self):
        """Test creating provider from environment variables."""
        provider = create_voice_provider()

        assert isinstance(provider, OpenAIVoiceProvider)
        assert provider.config.api_key == "env-test-key"
        assert provider.config.tts_voice == TTSVoice.ECHO
        assert provider.config.tts_speed == 1.5
        assert provider.config.enable_streaming_tts is False

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_VOICE_STT_LANGUAGE": "it",
            "OPENFATTURE_VOICE_TTS_FORMAT": "opus",
        },
    )
    def test_create_provider_with_partial_env(self):
        """Test factory with partial env config and explicit params."""
        provider = create_voice_provider(
            api_key="explicit-key",
        )

        assert provider.config.api_key == "explicit-key"
        assert provider.config.stt_language == "it"  # From env
        assert provider.config.tts_format == AudioFormat.OPUS  # From env

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_VOICE_TTS_MODEL": "invalid-model",
            "OPENAI_API_KEY": "test-key",
        },
    )
    def test_invalid_env_values_fallback(self):
        """Test factory handles invalid env values with fallback."""
        # Should not raise, should fallback to defaults
        provider = create_voice_provider()

        # Invalid TTS model should fallback to default
        assert provider.config.tts_model == TTSModel.TTS_1_HD

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_VOICE_TTS_SPEED": "10.0",  # Out of range
            "OPENAI_API_KEY": "test-key",
        },
    )
    def test_out_of_range_speed_fallback(self):
        """Test factory handles out-of-range TTS speed."""
        provider = create_voice_provider()

        # Out of range speed should fallback to 1.0
        assert provider.config.tts_speed == 1.0


class TestDefaultVoiceConfig:
    """Tests for get_default_voice_config."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "default-test-key"})
    def test_default_config_structure(self):
        """Test default config structure."""
        config = get_default_voice_config()

        assert config.provider == "openai"
        assert config.api_key == "default-test-key"
        assert config.stt_model == STTModel.WHISPER_1
        assert config.stt_language is None  # Auto-detect
        assert config.tts_model == TTSModel.TTS_1_HD
        assert config.tts_voice == TTSVoice.NOVA
        assert config.tts_speed == 1.0
        assert config.tts_format == AudioFormat.MP3
        assert config.enable_streaming_tts is True

    def test_default_config_without_api_key(self):
        """Test default config without API key in env."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_default_voice_config()

            assert config.api_key is None
            # Other defaults should still be set
            assert config.provider == "openai"
            assert config.tts_voice == TTSVoice.NOVA


class TestVoiceConfigFromEnv:
    """Tests for _create_config_from_env (via factory)."""

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_VOICE_PROVIDER": "openai",
            "OPENAI_API_KEY": "env-key",
            "OPENFATTURE_VOICE_STT_MODEL": "whisper-1",
            "OPENFATTURE_VOICE_STT_LANGUAGE": "fr",
            "OPENFATTURE_VOICE_STT_PROMPT": "invoice terminology",
            "OPENFATTURE_VOICE_TTS_MODEL": "tts-1",
            "OPENFATTURE_VOICE_TTS_VOICE": "shimmer",
            "OPENFATTURE_VOICE_TTS_SPEED": "0.5",
            "OPENFATTURE_VOICE_TTS_FORMAT": "flac",
            "OPENFATTURE_VOICE_STREAMING": "no",
            "OPENFATTURE_VOICE_CHUNK_SIZE": "8192",
            "OPENFATTURE_VOICE_STT_TIMEOUT": "60",
            "OPENFATTURE_VOICE_TTS_TIMEOUT": "120",
        },
    )
    def test_comprehensive_env_config(self):
        """Test factory with comprehensive env configuration."""
        provider = create_voice_provider()

        assert provider.config.api_key == "env-key"
        assert provider.config.stt_model == STTModel.WHISPER_1
        assert provider.config.stt_language == "fr"
        assert provider.config.stt_prompt == "invoice terminology"
        assert provider.config.tts_model == TTSModel.TTS_1
        assert provider.config.tts_voice == TTSVoice.SHIMMER
        assert provider.config.tts_speed == 0.5
        assert provider.config.tts_format == AudioFormat.FLAC
        assert provider.config.enable_streaming_tts is False  # "no" is falsy
        assert provider.config.chunk_size_bytes == 8192
        assert provider.config.stt_timeout == 60
        assert provider.config.tts_timeout == 120

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "test-key",
            "OPENFATTURE_VOICE_STREAMING": "true",
        },
    )
    def test_streaming_enabled_values(self):
        """Test various truthy values for streaming enable."""
        provider = create_voice_provider()
        assert provider.config.enable_streaming_tts is True

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "test-key",
            "OPENFATTURE_VOICE_STREAMING": "1",
        },
    )
    def test_streaming_enabled_numeric(self):
        """Test numeric truthy value for streaming."""
        provider = create_voice_provider()
        assert provider.config.enable_streaming_tts is True

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "test-key",
            "OPENFATTURE_VOICE_STREAMING": "false",
        },
    )
    def test_streaming_disabled(self):
        """Test falsy value for streaming disable."""
        provider = create_voice_provider()
        assert provider.config.enable_streaming_tts is False
