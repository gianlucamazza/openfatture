"""Voice module for speech-to-text and text-to-speech capabilities."""

from openfatture.ai.voice.assistant import VoiceAssistant
from openfatture.ai.voice.base import (
    BaseVoiceProvider,
    VoiceProviderAuthError,
    VoiceProviderError,
    VoiceProviderRateLimitError,
    VoiceProviderTimeoutError,
    VoiceProviderUnavailableError,
    VoiceProviderValidationError,
)
from openfatture.ai.voice.factory import create_voice_provider, get_default_voice_config
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
from openfatture.ai.voice.openai_voice import OpenAIVoiceProvider

__all__ = [
    # Assistant
    "VoiceAssistant",
    # Base classes
    "BaseVoiceProvider",
    # Providers
    "OpenAIVoiceProvider",
    # Factory
    "create_voice_provider",
    "get_default_voice_config",
    # Models
    "VoiceConfig",
    "AudioFormat",
    "STTModel",
    "TTSModel",
    "TTSVoice",
    "TranscriptionResult",
    "SynthesisResult",
    "VoiceResponse",
    # Exceptions
    "VoiceProviderError",
    "VoiceProviderAuthError",
    "VoiceProviderRateLimitError",
    "VoiceProviderTimeoutError",
    "VoiceProviderUnavailableError",
    "VoiceProviderValidationError",
]
