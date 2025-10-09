"""Configuration management for OpenFatture."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Vector Store (for AI)
    vector_store_path: Path = Field(default=Path.home() / ".openfatture" / "vector_store")

    @field_validator("data_dir", "archivio_dir", "certificates_dir", "vector_store_path")
    @classmethod
    def create_dir_if_not_exists(cls, v: Path) -> Path:
        """Create directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
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
