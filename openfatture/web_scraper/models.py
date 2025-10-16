"""Models for regulatory web scraping system."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..storage.database.base import Base, IntPKMixin


class UpdateStatus(str, Enum):
    """Status of regulatory update operations."""

    PENDING = "pending"
    SCRAPING = "scraping"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class ContentType(str, Enum):
    """Types of content that can be scraped."""

    HTML = "html"
    PDF = "pdf"
    XML = "xml"
    JSON = "json"
    TEXT = "text"


class RegulatorySource(BaseModel):
    """Configuration for a regulatory source to scrape."""

    id: str = Field(..., description="Unique identifier for the source")
    name: str = Field(..., description="Human-readable name")
    url: str = Field(..., description="Base URL to scrape")
    description: str | None = Field(None, description="Description of the source")

    # Scraping configuration
    content_type: ContentType = Field(ContentType.HTML, description="Primary content type")
    selectors: dict[str, str] = Field(
        default_factory=dict, description="CSS selectors for content extraction"
    )
    follow_links: bool = Field(False, description="Whether to follow links from this page")
    link_selectors: list[str] = Field(
        default_factory=list, description="Selectors for links to follow"
    )

    # Update detection
    change_detection: str = Field("content_hash", description="Method for detecting changes")
    last_updated: datetime | None = Field(None, description="Last time this source was updated")

    # Metadata
    jurisdiction: str = Field("IT", description="Jurisdiction (IT, EU, etc.)")
    category: str = Field(..., description="Category (tax, vat, invoice, etc.)")
    priority: int = Field(1, ge=1, le=10, description="Priority for updates (1=highest)")

    # Compliance
    official_source: bool = Field(True, description="Whether this is an official government source")
    requires_auth: bool = Field(False, description="Whether authentication is required")

    # Processing
    enabled: bool = Field(True, description="Whether this source is enabled")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        from urllib.parse import urlparse

        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {v}")
        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
        return v


class RegulatoryDocument(Base, IntPKMixin):
    """Database model for scraped regulatory documents."""

    __tablename__ = "regulatory_documents"

    # Source information
    source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Metadata
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(10), default="IT")
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Processing status
    status: Mapped[UpdateStatus] = mapped_column(
        SQLEnum(UpdateStatus), nullable=False, default=UpdateStatus.PENDING
    )

    # Timestamps
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Change detection
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    change_confidence: Mapped[float] = mapped_column(default=0.0)

    # AI processing results
    extracted_entities: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)
    impact_assessment: Mapped[str | None] = mapped_column(Text)

    # Validation
    requires_review: Mapped[bool] = mapped_column(default=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100))
    review_notes: Mapped[str | None] = mapped_column(Text)

    # File storage
    raw_content_path: Mapped[str | None] = mapped_column(String(500))
    processed_content_path: Mapped[str | None] = mapped_column(String(500))

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"<RegulatoryDocument(id={self.id}, source='{self.source_id}', title='{self.title[:50]}...', status='{self.status.value}')>"


class ScrapingSession(Base, IntPKMixin):
    """Database model for scraping sessions."""

    __tablename__ = "scraping_sessions"

    # Session info
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")

    # Configuration
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Statistics
    sources_processed: Mapped[int] = mapped_column(default=0)
    documents_scraped: Mapped[int] = mapped_column(default=0)
    documents_changed: Mapped[int] = mapped_column(default=0)
    errors_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Results
    results: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<ScrapingSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"


class RegulatoryUpdate(Base, IntPKMixin):
    """Database model for regulatory updates applied to knowledge base."""

    __tablename__ = "regulatory_updates"

    # Update info
    document_id: Mapped[int] = mapped_column(ForeignKey("regulatory_documents.id"), nullable=False)
    document: Mapped[RegulatoryDocument] = relationship(backref="updates")

    # Knowledge base integration
    kb_collection: Mapped[str] = mapped_column(String(100), nullable=False)
    kb_document_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # Update details
    update_type: Mapped[str] = mapped_column(String(50), nullable=False)  # add, update, delete
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Validation
    applied_by: Mapped[str] = mapped_column(String(100), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Rollback support
    rollback_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<RegulatoryUpdate(id={self.id}, document_id={self.document_id}, type='{self.update_type}')>"
