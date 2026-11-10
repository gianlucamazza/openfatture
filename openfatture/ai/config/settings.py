"""AI module configuration settings."""

from typing import TYPE_CHECKING, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from openfatture.platform.config import Settings


class AISettings(BaseSettings):
    """
    Configuration for AI features.

    All settings can be configured via environment variables with
    the prefix OPENFATTURE_AI_.

    Example:
        export OPENFATTURE_AI_PROVIDER=anthropic
        export OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENFATTURE_AI_",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider Selection
    provider: Literal["openai", "anthropic", "ollama"] = Field(
        default="openai",
        description="LLM provider to use (openai, anthropic, ollama)",
    )

    # API Credentials
    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API key",
    )

    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API key",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )

    # Model Selection (per provider) - Updated October 2025
    openai_model: str = Field(
        default="gpt-5",
        description="OpenAI model to use (gpt-5, gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo)",
    )

    anthropic_model: str = Field(
        default="claude-4.5-sonnet",
        description="Anthropic model to use (claude-4.5-opus, claude-4.5-sonnet, claude-4.5-haiku)",
    )

    ollama_model: str = Field(
        default="qwen3:8b",
        description="Ollama model to use (qwen3:8b recommended for tool calling, mistral-small3.1, llama3.2)",
    )

    # Generation Parameters
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for generation (0.0-2.0)",
    )

    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=100000,
        description="Maximum tokens to generate",
    )

    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Top-p (nucleus) sampling parameter",
    )

    # Features
    streaming_enabled: bool = Field(
        default=True,
        description="Enable streaming responses",
    )

    caching_enabled: bool = Field(
        default=True,
        description="Enable response caching",
    )

    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection",
    )

    tools_enabled: bool = Field(
        default=True,
        description="Enable tool/function calling",
    )

    rag_enabled: bool = Field(
        default=True,
        description="Enable RAG (Retrieval Augmented Generation)",
    )

    # Cost Controls
    max_cost_per_request_usd: float = Field(
        default=0.50,
        ge=0.0,
        description="Maximum cost per request in USD",
    )

    daily_budget_usd: float = Field(
        default=10.0,
        ge=0.0,
        description="Daily budget limit in USD",
    )

    warn_cost_threshold_usd: float = Field(
        default=0.25,
        ge=0.0,
        description="Warning threshold for cost per request in USD",
    )

    # Embeddings
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for vector search",
    )

    embedding_dimensions: int = Field(
        default=1536,
        ge=1,
        description="Embedding vector dimensions",
    )

    # Timeouts
    request_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for LLM requests in seconds",
    )

    stream_timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Timeout for streaming responses in seconds",
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries for failed requests",
    )

    retry_delay_seconds: float = Field(
        default=1.0,
        ge=0.1,
        description="Base delay between retries in seconds",
    )

    # Cache Configuration
    cache_ttl_seconds: int = Field(
        default=86400,  # 24 hours
        ge=0,
        description="Cache TTL in seconds (0 to disable)",
    )

    cache_max_size_mb: int = Field(
        default=100,
        ge=1,
        description="Maximum cache size in MB",
    )

    def get_model_for_provider(self) -> str:
        """Get the model name for the current provider."""
        return {
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
            "ollama": self.ollama_model,
        }[self.provider]

    def get_api_key_for_provider(self) -> str | None:
        """Get the API key for the current provider."""
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "ollama": None,  # Ollama doesn't need API key
        }

        key = key_map.get(self.provider)
        return key.get_secret_value() if key else None

    def to_dict(self, include_secrets: bool = False) -> dict:
        """
        Convert to dictionary for logging.

        Args:
            include_secrets: Whether to include API keys (default: False)

        Returns:
            Dictionary with settings
        """
        data = self.model_dump()

        # Redact secrets if requested
        if not include_secrets:
            for key in ["openai_api_key", "anthropic_api_key"]:
                if key in data and data[key]:
                    data[key] = "***REDACTED***"

        return data


# Global settings instance
_settings: AISettings | None = None


def _env_has(name: str) -> bool:
    """True if an environment variable is set (case-insensitive key match)."""
    import os

    if not name:
        return False
    target = name.upper()
    return any(key.upper() == target for key in os.environ)


def hydrate_ai_settings_from_platform(ai: AISettings) -> AISettings:
    """Apply product SSOT credentials from platform ``Settings`` (AI_* / init / docs).

    Precedence for mapped fields:
    1. Explicit ``OPENFATTURE_AI_*`` env (AISettings load) — wins when set
    2. Platform ``Settings`` (``AI_PROVIDER``, ``AI_API_KEY``, ``AI_MODEL``, …)
    3. AISettings field defaults

    Advanced multi-key knobs (per-provider models, budgets, chroma) stay on
    ``AISettings`` / ``OPENFATTURE_AI_*`` only.
    """
    from openfatture.platform.config import get_settings

    plat = get_settings()
    updates: dict[str, object] = {}
    platform_provider = _platform_provider(plat.ai_provider)
    if platform_provider is not None:
        updates["provider"] = platform_provider
    provider = str(updates.get("provider") or ai.provider)
    updates.update(_platform_credentials(plat, provider))
    for field, attribute in _PLATFORM_TUNING:
        if not _env_has(f"OPENFATTURE_AI_{field.upper()}"):
            updates[field] = getattr(plat, attribute)

    if not updates:
        return ai
    return ai.model_copy(update=updates)


_HYDRATED_PROVIDERS = ("openai", "anthropic", "ollama")
_API_KEY_PROVIDERS = ("openai", "anthropic")
_PLATFORM_TUNING = (
    ("temperature", "ai_temperature"),
    ("max_tokens", "ai_max_tokens"),
    ("tools_enabled", "ai_tools_enabled"),
)


def _platform_provider(value: str | None) -> str | None:
    """The platform ``AI_PROVIDER`` when supported and not overridden by env."""
    if _env_has("OPENFATTURE_AI_PROVIDER") or not value:
        return None
    candidate = value.strip().lower()
    return candidate if candidate in _HYDRATED_PROVIDERS else None


def _platform_credentials(plat: "Settings", provider: str) -> dict[str, object]:
    """Model, API key and base URL of ``provider`` from platform settings."""
    updates: dict[str, object] = {}
    if provider not in _HYDRATED_PROVIDERS:
        return updates
    prefix = f"OPENFATTURE_AI_{provider.upper()}"
    if plat.ai_model and not _env_has(f"{prefix}_MODEL"):
        updates[f"{provider}_model"] = plat.ai_model
    if plat.ai_api_key and provider in _API_KEY_PROVIDERS and not _env_has(f"{prefix}_API_KEY"):
        updates[f"{provider}_api_key"] = SecretStr(plat.ai_api_key)
    if plat.ai_base_url and provider == "ollama" and not _env_has(f"{prefix}_BASE_URL"):
        updates["ollama_base_url"] = plat.ai_base_url
    return updates


def get_ai_settings() -> AISettings:
    """
    Get global AI settings instance (singleton pattern).

    Product credentials are hydrated from platform ``Settings`` (see
    :func:`hydrate_ai_settings_from_platform`) so ``init`` / ``AI_*`` env vars
    and the provider factory share one source of truth.
    """
    global _settings

    if _settings is None:
        _settings = hydrate_ai_settings_from_platform(AISettings())

    return _settings


def reset_ai_settings() -> None:
    """Reset global settings (useful for testing)."""
    global _settings
    _settings = None
