"""Web service adapter for AI feedback collection.

Provides async/sync bridge for feedback operations in Streamlit web interface.
"""

from typing import Any

import streamlit as st

from openfatture.ai.feedback import FeedbackCreate, FeedbackService
from openfatture.storage.database.models import FeedbackType


class StreamlitFeedbackService:
    """Adapter service for feedback collection in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with feedback service."""
        self._feedback_service: FeedbackService | None = None

    @property
    def feedback_service(self) -> FeedbackService:
        """Get or create feedback service (cached)."""
        if self._feedback_service is None:
            self._feedback_service = FeedbackService()
        return self._feedback_service

    def submit_feedback(
        self,
        agent_type: str,
        rating: int,
        feedback_type: str = "rating",
        user_comment: str | None = None,
        original_text: str | None = None,
        corrected_text: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Submit feedback for an AI interaction.

        Args:
            agent_type: Type of agent (chat_agent, invoice_assistant, etc.)
            rating: Rating from 1-5
            feedback_type: Type of feedback (rating, correction, etc.)
            user_comment: Optional user comments
            original_text: Original AI response text
            corrected_text: Corrected/suggested text (for corrections)
            metadata: Additional metadata

        Returns:
            True if feedback was submitted successfully
        """
        try:
            # Map string feedback_type to enum
            if feedback_type == "rating":
                fb_type = FeedbackType.RATING
            elif feedback_type == "correction":
                fb_type = FeedbackType.CORRECTION
            else:
                fb_type = FeedbackType.RATING

            feedback = FeedbackCreate(
                agent_type=agent_type,
                rating=rating,
                feedback_type=fb_type,
                user_comment=user_comment,
                original_text=original_text,
                corrected_text=corrected_text,
                metadata=metadata or {},
            )

            result = self.feedback_service.create_user_feedback(feedback)
            return result is not None
        except Exception:
            return False

    def get_feedback_count(self) -> int:
        """
        Get total number of feedback entries.

        Returns:
            Number of feedback entries
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you'd add a count method to FeedbackService
            return 0  # Placeholder
        except Exception:
            return 0


@st.cache_resource
def get_feedback_service() -> StreamlitFeedbackService:
    """
    Get cached feedback service instance.

    Returns:
        Singleton feedback service
    """
    return StreamlitFeedbackService()
