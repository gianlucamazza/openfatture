"""Feedback system for AI responses and ML predictions.

This module enables tracking of user feedback to improve AI models through:
- User ratings and corrections on AI responses
- ML prediction acceptance/rejection tracking
- Continuous learning feedback loops
"""

from openfatture.ai.feedback.analytics import FeedbackAnalytics
from openfatture.ai.feedback.models import (
    FeedbackCreate,
    FeedbackResponse,
    ModelPredictionFeedbackCreate,
    ModelPredictionFeedbackResponse,
)
from openfatture.ai.feedback.service import FeedbackService

__all__ = [
    "FeedbackService",
    "FeedbackAnalytics",
    "FeedbackCreate",
    "FeedbackResponse",
    "ModelPredictionFeedbackCreate",
    "ModelPredictionFeedbackResponse",
]
