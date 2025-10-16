"""Health check utilities for Streamlit web app - Best Practices 2025.

Provides health monitoring for:
- Database connectivity
- AI provider availability
- System resources
- Application state
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import streamlit as st
from sqlalchemy import text

from openfatture.storage.database.base import get_session
from openfatture.utils.config import get_settings


@dataclass
class HealthStatus:
    """Health check status result."""

    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    response_time_ms: float | None = None
    details: dict[str, Any] | None = None


class HealthChecker:
    """Comprehensive health checker for web application."""

    def __init__(self):
        """Initialize health checker."""
        self.settings = get_settings()

    def check_database(self) -> HealthStatus:
        """
        Check database connectivity.

        Returns:
            HealthStatus with database health
        """
        start_time = time.time()

        try:
            session = get_session()
            # Simple query to test connection
            session.execute(text("SELECT 1"))
            session.close()

            response_time = (time.time() - start_time) * 1000

            return HealthStatus(
                component="database",
                status="healthy",
                message="Database connection successful",
                response_time_ms=response_time,
                details={
                    "db_url": (
                        self.settings.database_url.split("@")[-1]
                        if "@" in self.settings.database_url
                        else "sqlite"
                    ),
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                component="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    def check_ai_provider(self) -> HealthStatus:
        """
        Check AI provider availability.

        Returns:
            HealthStatus with AI provider health
        """
        start_time = time.time()

        try:
            from openfatture.web.services.ai_service import get_ai_service

            ai_service = get_ai_service()

            if not ai_service.is_available():
                return HealthStatus(
                    component="ai_provider",
                    status="degraded",
                    message="AI provider not configured",
                    response_time_ms=(time.time() - start_time) * 1000,
                    details={"provider": "none", "configured": False},
                )

            # For now, just check if it's configured
            # TODO: Add actual health check API call
            response_time = (time.time() - start_time) * 1000

            return HealthStatus(
                component="ai_provider",
                status="healthy",
                message="AI provider configured and available",
                response_time_ms=response_time,
                details={
                    "provider": self.settings.ai_provider,
                    "model": self.settings.ai_model,
                    "configured": True,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthStatus(
                component="ai_provider",
                status="unhealthy",
                message=f"AI provider check failed: {str(e)[:100]}",
                response_time_ms=response_time,
            )

    def check_session_state(self) -> HealthStatus:
        """
        Check Streamlit session state health.

        Returns:
            HealthStatus with session state health
        """
        try:
            # Count session state keys
            state_keys = len(st.session_state.keys())

            # Check if session state is working
            test_key = "_health_check_test"
            st.session_state[test_key] = datetime.now()
            del st.session_state[test_key]

            status = "healthy" if state_keys < 100 else "degraded"
            message = (
                "Session state healthy"
                if state_keys < 100
                else f"Session state has {state_keys} keys (consider cleanup)"
            )

            return HealthStatus(
                component="session_state",
                status=status,
                message=message,
                details={"keys_count": state_keys},
            )

        except Exception as e:
            return HealthStatus(
                component="session_state",
                status="unhealthy",
                message=f"Session state check failed: {str(e)[:100]}",
            )

    def check_all(self) -> list[HealthStatus]:
        """
        Run all health checks.

        Returns:
            List of HealthStatus for all components
        """
        return [
            self.check_database(),
            self.check_ai_provider(),
            self.check_session_state(),
        ]

    def get_overall_status(self, checks: list[HealthStatus]) -> str:
        """
        Get overall application health status.

        Args:
            checks: List of individual health checks

        Returns:
            Overall status: "healthy", "degraded", or "unhealthy"
        """
        if any(check.status == "unhealthy" for check in checks):
            return "unhealthy"
        elif any(check.status == "degraded" for check in checks):
            return "degraded"
        else:
            return "healthy"


def render_health_dashboard() -> None:
    """
    Render health check dashboard in Streamlit.

    Usage:
        >>> from openfatture.web.utils.health import render_health_dashboard
        >>> render_health_dashboard()
    """
    st.markdown("## 🏥 System Health")
    st.markdown("Real-time health monitoring of application components")

    # Run health checks
    checker = HealthChecker()

    with st.spinner("Checking system health..."):
        checks = checker.check_all()

    overall_status = checker.get_overall_status(checks)

    # Overall status indicator
    status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}

    st.markdown("---")

    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        st.metric("Overall Status", overall_status.upper())

    with col2:
        st.metric(
            "Components Checked",
            len(checks),
        )

    with col3:
        healthy_count = sum(1 for check in checks if check.status == "healthy")
        st.metric("Healthy", f"{healthy_count}/{len(checks)}")

    st.markdown("---")

    # Individual component status
    st.markdown("### Component Status")

    for check in checks:
        status_icon = status_emoji.get(check.status, "❓")

        with st.expander(f"{status_icon} {check.component.upper()} - {check.status.upper()}"):
            st.markdown(f"**Message:** {check.message}")

            if check.response_time_ms:
                st.metric("Response Time", f"{check.response_time_ms:.2f} ms")

            if check.details:
                st.markdown("**Details:**")
                for key, value in check.details.items():
                    st.text(f"  {key}: {value}")

    # Refresh button
    if st.button("🔄 Refresh Health Checks", use_container_width=True):
        st.rerun()


def quick_health_check() -> dict[str, Any]:
    """
    Quick health check for API/monitoring.

    Returns:
        Dictionary with health status and checks

    Usage:
        >>> health = quick_health_check()
        >>> if health['status'] != 'healthy':
        ...     alert_ops_team(health)
    """
    checker = HealthChecker()
    checks = checker.check_all()
    overall_status = checker.get_overall_status(checks)

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "checks": [
            {
                "component": check.component,
                "status": check.status,
                "message": check.message,
                "response_time_ms": check.response_time_ms,
            }
            for check in checks
        ],
    }
