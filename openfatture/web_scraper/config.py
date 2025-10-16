"""Web scraper configuration for regulatory updates."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class WebScraperConfig(BaseModel):
    """Configuration for regulatory web scraping system.

    This configuration controls all aspects of the regulatory update system,
    including scraping behavior, AI processing, and compliance settings.
    """

    # General settings
    enabled: bool = Field(default=True, description="Enable regulatory web scraping system")

    # Source configuration
    sources_config_path: Path = Field(
        default=Path("openfatture/web_scraper/sources.json"),
        description="Path to regulatory sources configuration",
    )

    # Scraping settings
    browser_type: Literal["chromium", "firefox", "webkit"] = Field(
        default="chromium", description="Browser type for Playwright"
    )

    headless: bool = Field(default=True, description="Run browser in headless mode")

    user_agent: str = Field(
        default="OpenFatture/1.1.0 (Regulatory Update Bot; +https://github.com/gianlucamazza/openfatture)",
        description="User agent string for requests",
    )

    # Rate limiting
    requests_per_minute: int = Field(
        default=10, description="Maximum requests per minute per domain"
    )

    delay_between_requests: float = Field(
        default=2.0, ge=0.1, le=60.0, description="Delay between requests in seconds"
    )

    # Content processing
    max_content_length: int = Field(
        default=5_000_000,  # 5MB
        description="Maximum content length to process (bytes)",
    )

    supported_content_types: list[str] = Field(
        default=["text/html", "application/pdf", "text/plain"],
        description="Supported content types for processing",
    )

    # AI processing
    ai_provider: str = Field(default="openai", description="AI provider for content extraction")

    ai_model: str = Field(
        default="gpt-4-turbo-preview", description="AI model for content processing"
    )

    ai_temperature: float = Field(
        default=0.1, ge=0.0, le=1.0, description="AI temperature for deterministic processing"
    )

    # Change detection
    similarity_threshold: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Similarity threshold for change detection"
    )

    # Storage
    cache_dir: Path = Field(
        default=Path.home() / ".openfatture" / "web_scraper" / "cache",
        description="Cache directory for scraped content",
    )

    temp_dir: Path = Field(
        default=Path.home() / ".openfatture" / "web_scraper" / "temp",
        description="Temporary directory for processing",
    )

    # Compliance & Security
    respect_robots_txt: bool = Field(default=True, description="Respect robots.txt files")

    require_https: bool = Field(default=True, description="Only scrape HTTPS URLs")

    allowed_domains: list[str] = Field(
        default=[
            "agenziaentrate.gov.it",
            "fatturapa.gov.it",
            "ministeroeconomia.gov.it",
            "europa.eu",
            "eur-lex.europa.eu",
        ],
        description="Allowed domains for scraping",
    )

    # Monitoring & Logging
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")

    log_level: str = Field(default="INFO", description="Logging level")

    # Update scheduling
    check_interval_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # 1 week
        description="Hours between update checks",
    )

    # Validation
    require_human_review: bool = Field(
        default=True, description="Require human review for regulatory updates"
    )

    auto_update_threshold: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Confidence threshold for automatic updates"
    )

    @field_validator("cache_dir")
    @classmethod
    def create_cache_dir(cls, v: Path) -> Path:
        """Create cache directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("temp_dir")
    @classmethod
    def create_temp_dir(cls, v: Path) -> Path:
        """Create temp directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        """Validate domain format."""
        import re

        domain_pattern = re.compile(
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        )

        for domain in v:
            if not domain_pattern.match(domain):
                raise ValueError(f"Invalid domain format: {domain}")

        return v


# Default configuration
DEFAULT_WEB_SCRAPER_CONFIG = WebScraperConfig()


def get_web_scraper_config() -> WebScraperConfig:
    """Get web scraper configuration from environment variables.

    Environment variables:
    - OPENFATTURE_WEB_SCRAPER_ENABLED: Enable/disable web scraper
    - OPENFATTURE_WEB_SCRAPER_SOURCES_CONFIG: Sources config path
    - OPENFATTURE_WEB_SCRAPER_BROWSER_TYPE: Browser type
    - OPENFATTURE_WEB_SCRAPER_HEADLESS: Headless mode
    - OPENFATTURE_WEB_SCRAPER_REQUESTS_PER_MINUTE: Rate limiting
    - OPENFATTURE_WEB_SCRAPER_AI_PROVIDER: AI provider
    - OPENFATTURE_WEB_SCRAPER_AI_MODEL: AI model
    - OPENFATTURE_WEB_SCRAPER_SIMILARITY_THRESHOLD: Change detection threshold
    - OPENFATTURE_WEB_SCRAPER_CHECK_INTERVAL_HOURS: Update check interval
    - OPENFATTURE_WEB_SCRAPER_REQUIRE_HUMAN_REVIEW: Require human review

    Returns:
        WebScraperConfig instance with environment settings
    """
    import os
    from typing import cast

    browser_type_raw = os.getenv("OPENFATTURE_WEB_SCRAPER_BROWSER_TYPE", "chromium")
    if browser_type_raw not in ["chromium", "firefox", "webkit"]:
        browser_type_raw = "chromium"
    browser_type = cast(Literal["chromium", "firefox", "webkit"], browser_type_raw)

    return WebScraperConfig(
        enabled=os.getenv("OPENFATTURE_WEB_SCRAPER_ENABLED", "true").lower() == "true",
        sources_config_path=Path(
            os.getenv(
                "OPENFATTURE_WEB_SCRAPER_SOURCES_CONFIG", "openfatture/web_scraper/sources.json"
            )
        ),
        browser_type=browser_type,
        headless=os.getenv("OPENFATTURE_WEB_SCRAPER_HEADLESS", "true").lower() == "true",
        requests_per_minute=int(os.getenv("OPENFATTURE_WEB_SCRAPER_REQUESTS_PER_MINUTE", "10")),
        ai_provider=os.getenv("OPENFATTURE_WEB_SCRAPER_AI_PROVIDER", "openai"),
        ai_model=os.getenv("OPENFATTURE_WEB_SCRAPER_AI_MODEL", "gpt-4-turbo-preview"),
        similarity_threshold=float(
            os.getenv("OPENFATTURE_WEB_SCRAPER_SIMILARITY_THRESHOLD", "0.85")
        ),
        check_interval_hours=int(os.getenv("OPENFATTURE_WEB_SCRAPER_CHECK_INTERVAL_HOURS", "24")),
        require_human_review=os.getenv(
            "OPENFATTURE_WEB_SCRAPER_REQUIRE_HUMAN_REVIEW", "true"
        ).lower()
        == "true",
    )
