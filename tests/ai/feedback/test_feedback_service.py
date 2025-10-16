"""Tests for feedback service."""

from decimal import Decimal

import pytest

from openfatture.ai.feedback import (
    FeedbackCreate,
    FeedbackService,
    ModelPredictionFeedbackCreate,
)
from openfatture.storage.database.models import FeedbackType, PredictionType


@pytest.fixture
def feedback_service():
    """Create feedback service instance."""
    return FeedbackService()


def test_create_user_feedback_rating(feedback_service):
    """Test creating user feedback with rating."""
    feedback = FeedbackCreate(
        session_id="test-session-123",
        feedback_type=FeedbackType.RATING,
        rating=5,
        original_text="AI generated response",
        agent_type="chat_agent",
    )

    result = feedback_service.create_user_feedback(feedback)

    assert result.id > 0
    assert result.session_id == "test-session-123"
    assert result.feedback_type == FeedbackType.RATING
    assert result.rating == 5
    assert result.agent_type == "chat_agent"


def test_create_user_feedback_correction(feedback_service):
    """Test creating user feedback with correction."""
    feedback = FeedbackCreate(
        session_id="test-session-456",
        feedback_type=FeedbackType.CORRECTION,
        original_text="Wrong output",
        corrected_text="Correct output",
        user_comment="Fixed the error",
        agent_type="invoice_assistant",
    )

    result = feedback_service.create_user_feedback(feedback)

    assert result.id > 0
    assert result.feedback_type == FeedbackType.CORRECTION
    assert result.original_text == "Wrong output"
    assert result.corrected_text == "Correct output"
    assert result.user_comment == "Fixed the error"


def test_create_prediction_feedback(feedback_service):
    """Test creating ML prediction feedback."""
    feedback = ModelPredictionFeedbackCreate(
        prediction_type=PredictionType.INVOICE_DELAY,
        entity_type="invoice",
        entity_id=123,
        prediction_data={"expected_days": 15, "confidence": 0.85},
        confidence_score=Decimal("0.85"),
        user_accepted=True,
        model_version="v1.0.0",
    )

    result = feedback_service.create_prediction_feedback(feedback)

    assert result.id > 0
    assert result.prediction_type == PredictionType.INVOICE_DELAY
    assert result.entity_type == "invoice"
    assert result.entity_id == 123
    assert result.user_accepted is True
    assert result.model_version == "v1.0.0"
    assert result.processed is False


def test_get_user_feedback_by_session(feedback_service):
    """Test retrieving user feedback by session."""
    # Create feedback
    feedback1 = FeedbackCreate(
        session_id="test-session-789",
        feedback_type=FeedbackType.THUMBS_UP,
        original_text="Good response",
    )
    feedback2 = FeedbackCreate(
        session_id="test-session-789",
        feedback_type=FeedbackType.COMMENT,
        user_comment="Very helpful!",
    )

    feedback_service.create_user_feedback(feedback1)
    feedback_service.create_user_feedback(feedback2)

    # Retrieve
    results = feedback_service.get_user_feedback_by_session("test-session-789")

    assert len(results) >= 2
    session_ids = [f.session_id for f in results]
    assert all(sid == "test-session-789" for sid in session_ids)


def test_mark_prediction_processed(feedback_service):
    """Test marking prediction feedback as processed."""
    # Create feedback
    feedback = ModelPredictionFeedbackCreate(
        prediction_type=PredictionType.TAX_SUGGESTION,
        entity_type="service",
        entity_id=1,
        prediction_data={"aliquota_iva": 22},
        user_accepted=False,
        user_correction={"aliquota_iva": 10},
    )

    result = feedback_service.create_prediction_feedback(feedback)
    assert result.processed is False

    # Mark as processed
    feedback_service.mark_prediction_processed(result.id)

    # Verify
    feedbacks = feedback_service.get_prediction_feedback_by_entity("service", 1)
    assert len(feedbacks) > 0
    assert feedbacks[0].processed is True
    assert feedbacks[0].processed_at is not None


def test_get_unprocessed_predictions(feedback_service):
    """Test retrieving unprocessed predictions."""
    # Create processed and unprocessed feedback
    feedback1 = ModelPredictionFeedbackCreate(
        prediction_type=PredictionType.DESCRIPTION_GENERATION,
        entity_type="invoice",
        entity_id=1,
        prediction_data={"text": "description"},
        user_accepted=True,
    )

    feedback2 = ModelPredictionFeedbackCreate(
        prediction_type=PredictionType.DESCRIPTION_GENERATION,
        entity_type="invoice",
        entity_id=2,
        prediction_data={"text": "another description"},
        user_accepted=False,
    )

    result1 = feedback_service.create_prediction_feedback(feedback1)
    result2 = feedback_service.create_prediction_feedback(feedback2)

    # Mark one as processed
    feedback_service.mark_prediction_processed(result1.id)

    # Get unprocessed
    unprocessed = feedback_service.get_unprocessed_predictions(
        prediction_type=PredictionType.DESCRIPTION_GENERATION
    )

    # Should contain result2 but not result1
    unprocessed_ids = [f.id for f in unprocessed]
    assert result2.id in unprocessed_ids
    assert result1.id not in unprocessed_ids
