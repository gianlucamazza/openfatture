"""Pydantic models for feedback system."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from openfatture.storage.database.models import FeedbackType, PredictionType


class FeedbackCreate(BaseModel):
    """Create user feedback."""

    session_id: str | None = None
    message_id: str | None = None
    feedback_type: FeedbackType
    rating: int | None = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    original_text: str | None = None
    corrected_text: str | None = None
    user_comment: str | None = None
    agent_type: str | None = None
    feature_name: str | None = None
    metadata: dict[str, Any] | None = None

    # Removed automatic validation - handled in application code

    # Removed automatic validation - handled in application code

    class Config:
        use_enum_values = False


class FeedbackResponse(BaseModel):
    """User feedback response."""

    id: int
    session_id: str | None
    message_id: str | None
    feedback_type: FeedbackType
    rating: int | None
    original_text: str | None
    corrected_text: str | None
    user_comment: str | None
    agent_type: str | None
    feature_name: str | None
    metadata: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = False


class ModelPredictionFeedbackCreate(BaseModel):
    """Create ML prediction feedback."""

    prediction_type: PredictionType
    entity_type: str = Field(..., description="Entity type (invoice, client, etc.)")
    entity_id: int = Field(..., description="Entity ID")
    prediction_data: dict[str, Any] = Field(..., description="Original prediction as JSON")
    confidence_score: Decimal | None = Field(None, ge=0, le=1)
    user_accepted: bool = False
    user_correction: dict[str, Any] | None = Field(None, description="User correction as JSON")
    user_comment: str | None = None
    model_version: str | None = None

    class Config:
        use_enum_values = False


class ModelPredictionFeedbackResponse(BaseModel):
    """ML prediction feedback response."""

    id: int
    prediction_type: PredictionType
    entity_type: str
    entity_id: int
    prediction_data: dict[str, Any]
    confidence_score: Decimal | None
    user_accepted: bool
    user_correction: dict[str, Any] | None
    user_comment: str | None
    model_version: str | None
    created_at: datetime
    processed: bool
    processed_at: datetime | None

    class Config:
        from_attributes = True
        use_enum_values = False


class FeedbackStats(BaseModel):
    """Feedback statistics."""

    total_feedback: int
    by_type: dict[str, int]
    by_agent: dict[str, int]
    average_rating: float | None
    acceptance_rate: float | None  # For predictions
    total_corrections: int
    recent_feedback_count: int  # Last 7 days


class PredictionFeedbackStats(BaseModel):
    """ML prediction feedback statistics."""

    total_predictions: int
    by_type: dict[str, int]
    acceptance_rate: float
    average_confidence: float | None
    total_corrections: int
    unprocessed_count: int
    by_model_version: dict[str, dict[str, Any]]
