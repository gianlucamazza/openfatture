"""Configuration management for OpenFatture."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DebugConfig(BaseSettings):
    """Dynamic debug configuration controls."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Global debug settings
    enable_debug_logging: bool = Field(
        default=False,
        description="Enable detailed debug logging across the application",
    )

    # Module-specific log levels (JSON string: {"module.name": "DEBUG"})
    log_level_per_module: str = Field(
        default="{}",
        description="JSON string with module-specific log levels",
    )

    # ReAct orchestration tracing
    enable_react_tracing: bool = Field(
        default=False,
        description="Enable detailed tracing of ReAct orchestration loops",
    )
    react_trace_max_iterations: int = Field(
        default=10,
        description="Maximum iterations to trace in ReAct loops",
    )

    # Tool execution metrics
    enable_tool_metrics: bool = Field(
        default=True,
        description="Enable collection of tool execution metrics",
    )
    tool_metrics_retention_days: int = Field(
        default=7,
        description="Days to retain tool execution metrics",
    )

    # Performance monitoring
    enable_performance_logging: bool = Field(
        default=True,
        description="Enable performance logging for operations",
    )
    performance_log_threshold_ms: int = Field(
        default=100,
        description="Log operations taking longer than this threshold (ms)",
    )

    # Chat debugging
    enable_chat_debug: bool = Field(
        default=False,
        description="Enable debug logging for chat interactions",
    )
    chat_debug_max_history: int = Field(
        default=50,
        description="Maximum chat messages to include in debug logs",
    )

    # Log output controls
    log_to_file: bool = Field(
        default=False,
        description="Enable logging to file in addition to console",
    )
    log_file_path: Path = Field(
        default=Path.home() / ".openfatture" / "logs" / "debug.log",
        description="Path to debug log file",
    )
    log_file_max_size_mb: int = Field(
        default=10,
        description="Maximum size of log file before rotation (MB)",
    )
    log_file_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
    )

    @field_validator("log_file_path")
    @classmethod
    def create_log_dir_if_not_exists(cls, v: Path) -> Path:
        """Create log directory if it doesn't exist."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    def get_module_log_level(self, module_name: str) -> str | None:
        """Get log level for specific module."""
        import json

        try:
            levels = json.loads(self.log_level_per_module)
            return levels.get(module_name)
        except (json.JSONDecodeError, TypeError):
            return None


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "OpenFatture"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = Field(
        default="sqlite:///./openfatture.db",
        description="Database connection URL",
    )

    # Paths
    data_dir: Path = Field(default=Path.home() / ".openfatture" / "data")
    archivio_dir: Path = Field(default=Path.home() / ".openfatture" / "archivio")
    certificates_dir: Path = Field(default=Path.home() / ".openfatture" / "certificates")

    # Cedente Prestatore (Your company data)
    cedente_denominazione: str = Field(default="", description="Your company name")
    cedente_partita_iva: str = Field(default="", description="Your VAT number")
    cedente_codice_fiscale: str = Field(default="", description="Your tax code")
    cedente_regime_fiscale: str = Field(default="RF19", description="Tax regime code")
    cedente_indirizzo: str = Field(default="", description="Your address")
    cedente_cap: str = Field(default="", description="Your postal code")
    cedente_comune: str = Field(default="", description="Your city")
    cedente_provincia: str = Field(default="", description="Your province code")
    cedente_nazione: str = Field(default="IT", description="Country code")
    cedente_telefono: str | None = Field(default=None, description="Your phone")
    cedente_email: str | None = Field(default=None, description="Your email")

    # PEC Configuration
    pec_smtp_server: str = Field(default="smtp.pec.it", description="PEC SMTP server")
    pec_smtp_port: int = Field(default=465, description="PEC SMTP port")
    pec_address: str = Field(default="", description="Your PEC address")
    pec_password: str = Field(default="", description="PEC password")
    sdi_pec_address: str = Field(
        default="sdi01@pec.fatturapa.it",
        description="SDI PEC address",
    )

    # Digital Signature
    signature_certificate_path: Path | None = Field(
        default=None,
        description="Path to digital signature certificate",
    )
    signature_certificate_password: str | None = Field(
        default=None,
        description="Certificate password",
    )

    # Email Templates & Branding
    email_logo_url: str | None = Field(
        default=None,
        description="URL to company logo for email headers",
    )
    email_primary_color: str = Field(
        default="#1976D2",
        description="Primary color for email templates (hex)",
    )
    email_secondary_color: str = Field(
        default="#424242",
        description="Secondary color for email templates (hex)",
    )
    email_footer_text: str | None = Field(
        default=None,
        description="Custom footer text for emails",
    )

    # Email Notifications
    notification_email: str | None = Field(
        default=None,
        description="Email address for internal notifications (SDI events, batch summaries)",
    )
    notification_enabled: bool = Field(
        default=True,
        description="Enable automatic email notifications",
    )

    # Localization
    locale: str = Field(
        default="it",
        description="Default locale for emails and UI (it, en)",
    )

    # AI Configuration
    ai_provider: str = Field(
        default="openai",
        description="AI provider (openai, anthropic, ollama)",
    )
    ai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="AI model name",
    )
    ai_api_key: str | None = Field(default=None, description="AI API key")
    ai_base_url: str | None = Field(
        default=None,
        description="AI API base URL (for local models)",
    )
    ai_temperature: float = Field(default=0.7, description="AI temperature")
    ai_max_tokens: int = Field(default=2000, description="AI max tokens")

    # AI Chat Assistant
    ai_chat_enabled: bool = Field(
        default=True,
        description="Enable AI chat assistant",
    )
    ai_chat_sessions_dir: Path = Field(
        default=Path.home() / ".openfatture" / "ai" / "sessions",
        description="Directory for chat session storage",
    )
    ai_chat_auto_save: bool = Field(
        default=True,
        description="Auto-save chat sessions after each message",
    )
    ai_chat_max_messages: int = Field(
        default=100,
        description="Maximum messages per chat session",
    )
    ai_chat_max_tokens: int = Field(
        default=8000,
        description="Maximum tokens per chat session",
    )

    # AI Tools & Function Calling
    ai_tools_enabled: bool = Field(
        default=True,
        description="Enable AI tool/function calling",
    )
    ai_enabled_tools: str = Field(
        default="search_invoices,get_invoice_details,get_invoice_stats,search_clients,get_client_details,get_client_stats",
        description="Comma-separated list of enabled tools",
    )
    ai_tools_require_confirmation: bool = Field(
        default=True,
        description="Require user confirmation before executing tools",
    )

    # Vector Store (for AI)
    vector_store_path: Path = Field(default=Path.home() / ".openfatture" / "vector_store")

    # Payment module
    payment_event_listeners: str | None = Field(
        default=None,
        description="Comma-separated dotted paths to custom payment event listeners",
    )

    # Global event system
    event_listeners: str | None = Field(
        default=None,
        description="Comma-separated dotted paths to custom global event listeners",
    )

    # Web scraper configuration
    web_scraper_enabled: bool = Field(
        default=True, description="Enable regulatory web scraping system"
    )

    # Debug configuration
    debug_config: DebugConfig = Field(default_factory=DebugConfig)

    @field_validator(
        "data_dir", "archivio_dir", "certificates_dir", "vector_store_path", "ai_chat_sessions_dir"
    )
    @classmethod
    def create_dir_if_not_exists(cls, v: Path) -> Path:
        """Create directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("web_scraper_enabled")
    @classmethod
    def validate_web_scraper_enabled(cls, v: bool) -> bool:
        """Validate web scraper configuration."""
        # Could add additional validation logic here
        return v


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment/file."""
    global _settings
    _settings = Settings()
    return _settings
