"""Voice provider factory for creating provider instances."""

import os

from openfatture.ai.voice.base import BaseVoiceProvider
from openfatture.ai.voice.models import AudioFormat, STTModel, TTSModel, TTSVoice, VoiceConfig
from openfatture.ai.voice.openai_voice import OpenAIVoiceProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def create_voice_provider(
    provider: str | None = None,
    api_key: str | None = None,
    config: VoiceConfig | None = None,
) -> BaseVoiceProvider:
    """
    Create a voice provider instance.

    Factory method that creates the appropriate voice provider based on
    configuration or environment variables.

    Args:
        provider: Provider name ("openai", etc.). Uses env if None.
        api_key: API key for the provider. Uses env if None.
        config: Complete VoiceConfig. Creates from env if None.

    Returns:
        Initialized voice provider instance

    Raises:
        ValueError: If provider is unsupported or configuration is invalid
        RuntimeError: If API key is missing

    Environment variables (if config not provided):
        OPENFATTURE_VOICE_PROVIDER: Voice provider name (default: "openai")
        OPENAI_API_KEY: API key for OpenAI
        OPENFATTURE_VOICE_STT_MODEL: STT model (default: "whisper-1")
        OPENFATTURE_VOICE_STT_LANGUAGE: STT language code (auto-detect if not set)
        OPENFATTURE_VOICE_TTS_MODEL: TTS model (default: "tts-1-hd")
        OPENFATTURE_VOICE_TTS_VOICE: TTS voice (default: "nova")
        OPENFATTURE_VOICE_TTS_SPEED: TTS speed 0.25-4.0 (default: 1.0)
        OPENFATTURE_VOICE_TTS_FORMAT: Output format (default: "mp3")
        OPENFATTURE_VOICE_STREAMING: Enable TTS streaming (default: "true")

    Example:
        >>> # Create with defaults from environment
        >>> provider = create_voice_provider()
        >>>
        >>> # Create with explicit config
        >>> config = VoiceConfig(
        ...     provider="openai",
        ...     api_key="sk-...",
        ...     tts_voice=TTSVoice.NOVA,
        ... )
        >>> provider = create_voice_provider(config=config)
    """
    # Use provided config or create from environment
    if config is None:
        config = _create_config_from_env(provider, api_key)

    # Validate API key
    if not config.api_key:
        raise RuntimeError(
            f"API key required for voice provider '{config.provider}'. "
            "Set OPENAI_API_KEY environment variable or pass api_key parameter."
        )

    # Create provider based on type
    provider_name = config.provider.lower()

    if provider_name == "openai":
        logger.info(
            "creating_openai_voice_provider",
            stt_model=config.stt_model.value,
            tts_model=config.tts_model.value,
            tts_voice=config.tts_voice.value,
            streaming=config.enable_streaming_tts,
        )
        return OpenAIVoiceProvider(config=config)

    # Future providers can be added here:
    # elif provider_name == "google":
    #     return GoogleVoiceProvider(config=config)
    # elif provider_name == "azure":
    #     return AzureVoiceProvider(config=config)

    else:
        raise ValueError(
            f"Unsupported voice provider: {provider_name}. " f"Supported providers: openai"
        )


def _create_config_from_env(
    provider: str | None = None,
    api_key: str | None = None,
) -> VoiceConfig:
    """
    Create VoiceConfig from environment variables.

    Args:
        provider: Provider name override
        api_key: API key override

    Returns:
        VoiceConfig populated from environment
    """
    # Provider selection (always has a default)
    provider_name = provider or os.getenv("OPENFATTURE_VOICE_PROVIDER", "openai")
    assert provider_name is not None, "Provider name must be specified"

    # API key
    if api_key is None:
        if provider_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        # Add more providers here as needed

    # STT settings
    stt_model_str = os.getenv("OPENFATTURE_VOICE_STT_MODEL", "whisper-1")
    try:
        stt_model = STTModel(stt_model_str)
    except ValueError:
        logger.warning(
            "invalid_stt_model_env",
            value=stt_model_str,
            fallback=STTModel.WHISPER_1.value,
        )
        stt_model = STTModel.WHISPER_1

    stt_language = os.getenv("OPENFATTURE_VOICE_STT_LANGUAGE")  # None = auto-detect
    stt_prompt = os.getenv("OPENFATTURE_VOICE_STT_PROMPT")

    # TTS settings
    tts_model_str = os.getenv("OPENFATTURE_VOICE_TTS_MODEL", "tts-1-hd")
    try:
        tts_model = TTSModel(tts_model_str)
    except ValueError:
        logger.warning(
            "invalid_tts_model_env",
            value=tts_model_str,
            fallback=TTSModel.TTS_1_HD.value,
        )
        tts_model = TTSModel.TTS_1_HD

    tts_voice_str = os.getenv("OPENFATTURE_VOICE_TTS_VOICE", "nova")
    try:
        tts_voice = TTSVoice(tts_voice_str)
    except ValueError:
        logger.warning(
            "invalid_tts_voice_env",
            value=tts_voice_str,
            fallback=TTSVoice.NOVA.value,
        )
        tts_voice = TTSVoice.NOVA

    tts_speed = float(os.getenv("OPENFATTURE_VOICE_TTS_SPEED", "1.0"))
    if not 0.25 <= tts_speed <= 4.0:
        logger.warning(
            "invalid_tts_speed_env",
            value=tts_speed,
            fallback=1.0,
        )
        tts_speed = 1.0

    tts_format_str = os.getenv("OPENFATTURE_VOICE_TTS_FORMAT", "mp3")
    try:
        tts_format = AudioFormat(tts_format_str)
    except ValueError:
        logger.warning(
            "invalid_tts_format_env",
            value=tts_format_str,
            fallback=AudioFormat.MP3.value,
        )
        tts_format = AudioFormat.MP3

    # Performance settings
    streaming_str = os.getenv("OPENFATTURE_VOICE_STREAMING", "true").lower()
    enable_streaming = streaming_str in ("true", "1", "yes", "on")

    chunk_size = int(os.getenv("OPENFATTURE_VOICE_CHUNK_SIZE", "4096"))

    # Timeouts
    stt_timeout = int(os.getenv("OPENFATTURE_VOICE_STT_TIMEOUT", "30"))
    tts_timeout = int(os.getenv("OPENFATTURE_VOICE_TTS_TIMEOUT", "60"))

    # Create config
    config = VoiceConfig(
        provider=provider_name,
        api_key=api_key,
        stt_model=stt_model,
        stt_language=stt_language,
        stt_prompt=stt_prompt,
        tts_model=tts_model,
        tts_voice=tts_voice,
        tts_speed=tts_speed,
        tts_format=tts_format,
        enable_streaming_tts=enable_streaming,
        chunk_size_bytes=chunk_size,
        stt_timeout=stt_timeout,
        tts_timeout=tts_timeout,
    )

    logger.debug(
        "voice_config_created_from_env",
        provider=config.provider,
        stt_model=config.stt_model.value,
        tts_model=config.tts_model.value,
        tts_voice=config.tts_voice.value,
        streaming=config.enable_streaming_tts,
    )

    return config


def get_default_voice_config() -> VoiceConfig:
    """
    Get default voice configuration.

    Returns:
        VoiceConfig with sensible defaults for OpenAI

    Example:
        >>> config = get_default_voice_config()
        >>> config.api_key = "sk-..."
        >>> provider = create_voice_provider(config=config)
    """
    return VoiceConfig(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        stt_model=STTModel.WHISPER_1,
        stt_language=None,  # Auto-detect
        tts_model=TTSModel.TTS_1_HD,
        tts_voice=TTSVoice.NOVA,
        tts_speed=1.0,
        tts_format=AudioFormat.MP3,
        enable_streaming_tts=True,
    )
