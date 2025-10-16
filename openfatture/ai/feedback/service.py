"""Feedback service for managing user feedback and ML prediction tracking."""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from openfatture.ai.feedback.models import (
    FeedbackCreate,
    FeedbackResponse,
    ModelPredictionFeedbackCreate,
    ModelPredictionFeedbackResponse,
)
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import (
    ModelPredictionFeedback,
    PredictionType,
    UserFeedback,
)
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def _get_session() -> Session:
    """Get database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return SessionLocal()


class FeedbackService:
    """Service for managing user feedback and ML prediction feedback."""

    @staticmethod
    def create_user_feedback(feedback: FeedbackCreate) -> FeedbackResponse:
        """Create user feedback.

        Args:
            feedback: Feedback data

        Returns:
            Created feedback
        """
        db = _get_session()

        try:
            # Serialize metadata to JSON
            metadata_json = json.dumps(feedback.metadata) if feedback.metadata else None

            db_feedback = UserFeedback(
                session_id=feedback.session_id,
                message_id=feedback.message_id,
                feedback_type=feedback.feedback_type,
                rating=feedback.rating,
                original_text=feedback.original_text,
                corrected_text=feedback.corrected_text,
                user_comment=feedback.user_comment,
                agent_type=feedback.agent_type,
                feature_name=feedback.feature_name,
                metadata_json=metadata_json,
            )

            db.add(db_feedback)
            db.commit()
            db.refresh(db_feedback)

            logger.info(
                "user_feedback_created",
                feedback_id=db_feedback.id,
                type=feedback.feedback_type.value,
                session_id=feedback.session_id,
            )

            # Parse metadata back
            metadata = json.loads(db_feedback.metadata_json) if db_feedback.metadata_json else None

            return FeedbackResponse(
                id=db_feedback.id,
                session_id=db_feedback.session_id,
                message_id=db_feedback.message_id,
                feedback_type=db_feedback.feedback_type,
                rating=db_feedback.rating,
                original_text=db_feedback.original_text,
                corrected_text=db_feedback.corrected_text,
                user_comment=db_feedback.user_comment,
                agent_type=db_feedback.agent_type,
                feature_name=db_feedback.feature_name,
                metadata=metadata,
                created_at=db_feedback.created_at,
            )

        except Exception as e:
            db.rollback()
            logger.error("user_feedback_creation_failed", error=str(e))
            raise
        finally:
            db.close()

    @staticmethod
    def create_prediction_feedback(
        feedback: ModelPredictionFeedbackCreate,
    ) -> ModelPredictionFeedbackResponse:
        """Create ML prediction feedback.

        Args:
            feedback: Prediction feedback data

        Returns:
            Created prediction feedback
        """
        db = _get_session()

        try:
            # Serialize JSON fields
            prediction_json = json.dumps(feedback.prediction_data)
            correction_json = (
                json.dumps(feedback.user_correction) if feedback.user_correction else None
            )

            db_feedback = ModelPredictionFeedback(
                prediction_type=feedback.prediction_type,
                entity_type=feedback.entity_type,
                entity_id=feedback.entity_id,
                prediction_data=prediction_json,
                confidence_score=feedback.confidence_score,
                user_accepted=feedback.user_accepted,
                user_correction=correction_json,
                user_comment=feedback.user_comment,
                model_version=feedback.model_version,
            )

            db.add(db_feedback)
            db.commit()
            db.refresh(db_feedback)

            logger.info(
                "prediction_feedback_created",
                feedback_id=db_feedback.id,
                type=feedback.prediction_type.value,
                entity=f"{feedback.entity_type}:{feedback.entity_id}",
                accepted=feedback.user_accepted,
            )

            # Parse JSON back
            prediction_data = json.loads(db_feedback.prediction_data)
            correction_data = (
                json.loads(db_feedback.user_correction) if db_feedback.user_correction else None
            )

            return ModelPredictionFeedbackResponse(
                id=db_feedback.id,
                prediction_type=db_feedback.prediction_type,
                entity_type=db_feedback.entity_type,
                entity_id=db_feedback.entity_id,
                prediction_data=prediction_data,
                confidence_score=db_feedback.confidence_score,
                user_accepted=db_feedback.user_accepted,
                user_correction=correction_data,
                user_comment=db_feedback.user_comment,
                model_version=db_feedback.model_version,
                created_at=db_feedback.created_at,
                processed=db_feedback.processed,
                processed_at=db_feedback.processed_at,
            )

        except Exception as e:
            db.rollback()
            logger.error("prediction_feedback_creation_failed", error=str(e))
            raise
        finally:
            db.close()

    @staticmethod
    def get_user_feedback_by_session(session_id: str) -> list[FeedbackResponse]:
        """Get all feedback for a session.

        Args:
            session_id: Session ID

        Returns:
            List of feedback entries
        """
        db = _get_session()

        try:
            feedbacks = db.query(UserFeedback).filter(UserFeedback.session_id == session_id).all()

            return [
                FeedbackResponse(
                    id=f.id,
                    session_id=f.session_id,
                    message_id=f.message_id,
                    feedback_type=f.feedback_type,
                    rating=f.rating,
                    original_text=f.original_text,
                    corrected_text=f.corrected_text,
                    user_comment=f.user_comment,
                    agent_type=f.agent_type,
                    feature_name=f.feature_name,
                    metadata=json.loads(f.metadata_json) if f.metadata_json else None,
                    created_at=f.created_at,
                )
                for f in feedbacks
            ]

        finally:
            db.close()

    @staticmethod
    def get_prediction_feedback_by_entity(
        entity_type: str, entity_id: int
    ) -> list[ModelPredictionFeedbackResponse]:
        """Get all prediction feedback for an entity.

        Args:
            entity_type: Entity type (invoice, client, etc.)
            entity_id: Entity ID

        Returns:
            List of prediction feedback entries
        """
        db = _get_session()

        try:
            feedbacks = (
                db.query(ModelPredictionFeedback)
                .filter(
                    ModelPredictionFeedback.entity_type == entity_type,
                    ModelPredictionFeedback.entity_id == entity_id,
                )
                .all()
            )

            return [
                ModelPredictionFeedbackResponse(
                    id=f.id,
                    prediction_type=f.prediction_type,
                    entity_type=f.entity_type,
                    entity_id=f.entity_id,
                    prediction_data=json.loads(f.prediction_data),
                    confidence_score=f.confidence_score,
                    user_accepted=f.user_accepted,
                    user_correction=json.loads(f.user_correction) if f.user_correction else None,
                    user_comment=f.user_comment,
                    model_version=f.model_version,
                    created_at=f.created_at,
                    processed=f.processed,
                    processed_at=f.processed_at,
                )
                for f in feedbacks
            ]

        finally:
            db.close()

    @staticmethod
    def mark_prediction_processed(feedback_id: int) -> None:
        """Mark prediction feedback as processed (used in retraining).

        Args:
            feedback_id: Feedback ID
        """
        db = _get_session()

        try:
            feedback = (
                db.query(ModelPredictionFeedback)
                .filter(ModelPredictionFeedback.id == feedback_id)
                .first()
            )

            if feedback:
                feedback.processed = True
                feedback.processed_at = datetime.utcnow()
                db.commit()

                logger.info("prediction_feedback_marked_processed", feedback_id=feedback_id)

        except Exception as e:
            db.rollback()
            logger.error("mark_processed_failed", feedback_id=feedback_id, error=str(e))
            raise
        finally:
            db.close()

    @staticmethod
    def get_unprocessed_predictions(
        prediction_type: PredictionType | None = None, limit: int | None = None
    ) -> list[ModelPredictionFeedbackResponse]:
        """Get unprocessed prediction feedback for retraining.

        Args:
            prediction_type: Filter by prediction type
            limit: Maximum results

        Returns:
            List of unprocessed feedback
        """
        db = _get_session()

        try:
            query = db.query(ModelPredictionFeedback).filter(
                ModelPredictionFeedback.processed == False  # noqa: E712
            )

            if prediction_type:
                query = query.filter(ModelPredictionFeedback.prediction_type == prediction_type)

            if limit:
                query = query.limit(limit)

            feedbacks = query.all()

            return [
                ModelPredictionFeedbackResponse(
                    id=f.id,
                    prediction_type=f.prediction_type,
                    entity_type=f.entity_type,
                    entity_id=f.entity_id,
                    prediction_data=json.loads(f.prediction_data),
                    confidence_score=f.confidence_score,
                    user_accepted=f.user_accepted,
                    user_correction=json.loads(f.user_correction) if f.user_correction else None,
                    user_comment=f.user_comment,
                    model_version=f.model_version,
                    created_at=f.created_at,
                    processed=f.processed,
                    processed_at=f.processed_at,
                )
                for f in feedbacks
            ]

        finally:
            db.close()
