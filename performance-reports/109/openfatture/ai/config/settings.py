"""AI module configuration settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        env_file=".env",
        env_file_encoding="utf-8",
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

    # Vector Store (ChromaDB)
    chromadb_host: str = Field(
        default="localhost",
        description="ChromaDB host",
    )

    chromadb_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="ChromaDB port",
    )

    chromadb_persist_directory: Path = Field(
        default=Path(".chromadb"),
        description="ChromaDB persistence directory",
    )

    chromadb_collection_name: str = Field(
        default="openfatture_invoices",
        description="ChromaDB collection name",
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

    # Prompts
    prompts_directory: Path = Field(
        default=Path("openfatture/ai/prompts"),
        description="Directory containing prompt templates",
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

    # Agent-Specific Settings
    invoice_assistant_enabled: bool = Field(
        default=True,
        description="Enable Invoice Assistant agent",
    )

    tax_advisor_enabled: bool = Field(
        default=True,
        description="Enable Tax Advisor agent",
    )

    cash_flow_predictor_enabled: bool = Field(
        default=True,
        description="Enable Cash Flow Predictor agent",
    )

    compliance_checker_enabled: bool = Field(
        default=True,
        description="Enable Compliance Checker agent",
    )

    # Orchestration
    multi_agent_enabled: bool = Field(
        default=False,  # Experimental
        description="Enable multi-agent orchestration (experimental)",
    )

    max_workflow_steps: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum steps in multi-agent workflow",
    )

    @field_validator("chromadb_persist_directory", "prompts_directory")
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        """Ensure path exists or can be created."""
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

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

    def is_provider_configured(self) -> bool:
        """Check if current provider is properly configured."""
        if self.provider == "ollama":
            return True  # Ollama only needs base URL

        api_key = self.get_api_key_for_provider()
        return api_key is not None and len(api_key) > 0

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


def get_ai_settings() -> AISettings:
    """
    Get global AI settings instance (singleton pattern).

    Returns:
        AISettings instance
    """
    global _settings

    if _settings is None:
        _settings = AISettings()

    return _settings


def reset_ai_settings() -> None:
    """Reset global settings (useful for testing)."""
    global _settings
    _settings = None
