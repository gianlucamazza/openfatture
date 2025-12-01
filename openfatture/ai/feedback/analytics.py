"""Analytics and statistics for feedback system."""

from datetime import datetime, timedelta

from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from openfatture.ai.feedback.models import FeedbackStats, PredictionFeedbackStats
from openfatture.storage.session import db_session
from openfatture.storage.database.models import (
    FeedbackType,
    ModelPredictionFeedback,
    UserFeedback,
)
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class FeedbackAnalytics:
    """Analytics service for feedback metrics."""

    @staticmethod
    def get_user_feedback_stats(days: int = 30) -> FeedbackStats:
        """Get user feedback statistics.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Feedback statistics
        """
        with db_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Total feedback
            total = db.query(func.count(UserFeedback.id)).scalar() or 0

            # By type
            by_type_raw = (
                db.query(UserFeedback.feedback_type, func.count(UserFeedback.id))
                .group_by(UserFeedback.feedback_type)
                .all()
            )
            by_type = {feedback_type.value: count for feedback_type, count in by_type_raw}

            # By agent
            by_agent_raw = (
                db.query(UserFeedback.agent_type, func.count(UserFeedback.id))
                .filter(UserFeedback.agent_type.isnot(None))
                .group_by(UserFeedback.agent_type)
                .all()
            )
            by_agent = {agent: count for agent, count in by_agent_raw if agent}

            # Average rating
            avg_rating = (
                db.query(func.avg(UserFeedback.rating))
                .filter(UserFeedback.feedback_type == FeedbackType.RATING)
                .scalar()
            )

            # Total corrections
            total_corrections = (
                db.query(func.count(UserFeedback.id))
                .filter(UserFeedback.feedback_type == FeedbackType.CORRECTION)
                .scalar()
                or 0
            )

            # Recent feedback (last 7 days)
            recent_count = (
                db.query(func.count(UserFeedback.id))
                .filter(UserFeedback.created_at >= cutoff_date)
                .scalar()
                or 0
            )

            logger.info(
                "user_feedback_stats_calculated",
                total=total,
                days=days,
                avg_rating=avg_rating,
            )

            return FeedbackStats(
                total_feedback=total,
                by_type=by_type,
                by_agent=by_agent,
                average_rating=float(avg_rating) if avg_rating else None,
                acceptance_rate=None,  # Not applicable for user feedback
                total_corrections=total_corrections,
                recent_feedback_count=recent_count,
            )

    @staticmethod
    def get_prediction_feedback_stats(days: int = 30) -> PredictionFeedbackStats:
        """Get ML prediction feedback statistics.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Prediction feedback statistics
        """
        with db_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Total predictions with feedback
            total = (
                db.query(func.count(ModelPredictionFeedback.id))
                .filter(ModelPredictionFeedback.created_at >= cutoff_date)
                .scalar()
                or 0
            )

            # By prediction type
            by_type_raw = (
                db.query(
                    ModelPredictionFeedback.prediction_type,
                    func.count(ModelPredictionFeedback.id),
                )
                .filter(ModelPredictionFeedback.created_at >= cutoff_date)
                .group_by(ModelPredictionFeedback.prediction_type)
                .all()
            )
            by_type = {pred_type.value: count for pred_type, count in by_type_raw}

            # Acceptance rate
            accepted_count = (
                db.query(func.count(ModelPredictionFeedback.id))
                .filter(
                    ModelPredictionFeedback.created_at >= cutoff_date,
                    ModelPredictionFeedback.user_accepted == True,  # noqa: E712
                )
                .scalar()
                or 0
            )
            acceptance_rate = (accepted_count / total * 100) if total > 0 else 0.0

            # Average confidence
            avg_confidence = (
                db.query(func.avg(ModelPredictionFeedback.confidence_score))
                .filter(
                    ModelPredictionFeedback.created_at >= cutoff_date,
                    ModelPredictionFeedback.confidence_score.isnot(None),
                )
                .scalar()
            )

            # Total corrections
            total_corrections = (
                db.query(func.count(ModelPredictionFeedback.id))
                .filter(
                    ModelPredictionFeedback.created_at >= cutoff_date,
                    ModelPredictionFeedback.user_correction.isnot(None),
                )
                .scalar()
                or 0
            )

            # Unprocessed count (for retraining queue)
            unprocessed_count = (
                db.query(func.count(ModelPredictionFeedback.id))
                .filter(ModelPredictionFeedback.processed == False)  # noqa: E712
                .scalar()
                or 0
            )

            # By model version
            by_version_raw = (
                db.query(
                    ModelPredictionFeedback.model_version,
                    func.count(ModelPredictionFeedback.id),
                    func.avg(ModelPredictionFeedback.confidence_score),
                    func.sum(
                        func.cast(ModelPredictionFeedback.user_accepted, type_=Integer)
                    ),  # Count accepted
                )
                .filter(
                    ModelPredictionFeedback.created_at >= cutoff_date,
                    ModelPredictionFeedback.model_version.isnot(None),
                )
                .group_by(ModelPredictionFeedback.model_version)
                .all()
            )

            by_model_version = {}
            for version, count, avg_conf, accepted in by_version_raw:
                if version:
                    by_model_version[version] = {
                        "total": count,
                        "avg_confidence": float(avg_conf) if avg_conf else None,
                        "acceptance_rate": (float(accepted) / count * 100) if count > 0 else 0.0,
                    }

            logger.info(
                "prediction_feedback_stats_calculated",
                total=total,
                days=days,
                acceptance_rate=acceptance_rate,
                avg_confidence=avg_confidence,
            )

            return PredictionFeedbackStats(
                total_predictions=total,
                by_type=by_type,
                acceptance_rate=acceptance_rate,
                average_confidence=float(avg_confidence) if avg_confidence else None,
                total_corrections=total_corrections,
                unprocessed_count=unprocessed_count,
                by_model_version=by_model_version,
            )

    @staticmethod
    def get_correction_patterns(limit: int = 20) -> list[dict]:
        """Analyze common correction patterns.

        Args:
            limit: Maximum patterns to return

        Returns:
            List of correction patterns with frequency
        """
        with db_session() as db:
            # Get recent corrections
            corrections = (
                db.query(
                    UserFeedback.agent_type,
                    UserFeedback.feature_name,
                    UserFeedback.original_text,
                    UserFeedback.corrected_text,
                    UserFeedback.created_at,
                )
                .filter(UserFeedback.feedback_type == FeedbackType.CORRECTION)
                .order_by(UserFeedback.created_at.desc())
                .limit(limit)
                .all()
            )

            patterns = []
            for agent, feature, original, corrected, created_at in corrections:
                patterns.append(
                    {
                        "agent_type": agent,
                        "feature_name": feature,
                        "original": original[:100] if original else None,  # Truncate
                        "corrected": corrected[:100] if corrected else None,
                        "created_at": created_at.isoformat() if created_at else None,
                    }
                )

            logger.info("correction_patterns_analyzed", count=len(patterns))

            return patterns

    @staticmethod
    def get_low_confidence_predictions(threshold: float = 0.6, limit: int = 20) -> list[dict]:
        """Get low-confidence predictions for human review.

        Args:
            threshold: Confidence threshold (default: 0.6)
            limit: Maximum results

        Returns:
            List of low-confidence predictions
        """
        with db_session() as db:
            predictions = (
                db.query(
                    ModelPredictionFeedback.id,
                    ModelPredictionFeedback.prediction_type,
                    ModelPredictionFeedback.entity_type,
                    ModelPredictionFeedback.entity_id,
                    ModelPredictionFeedback.confidence_score,
                    ModelPredictionFeedback.user_accepted,
                    ModelPredictionFeedback.created_at,
                )
                .filter(
                    ModelPredictionFeedback.confidence_score < threshold,
                    ModelPredictionFeedback.processed == False,  # noqa: E712
                )
                .order_by(ModelPredictionFeedback.confidence_score.asc())
                .limit(limit)
                .all()
            )

            results = []
            for (
                pred_id,
                pred_type,
                entity_type,
                entity_id,
                confidence,
                accepted,
                created,
            ) in predictions:
                results.append(
                    {
                        "id": pred_id,
                        "prediction_type": pred_type.value,
                        "entity": f"{entity_type}:{entity_id}",
                        "confidence": float(confidence) if confidence else None,
                        "user_accepted": accepted,
                        "created_at": created.isoformat() if created else None,
                    }
                )

            logger.info(
                "low_confidence_predictions_retrieved",
                threshold=threshold,
                count=len(results),
            )

            return results
