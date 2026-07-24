"""Automatic Model Retraining Scheduler.

APScheduler-based scheduler that periodically checks retraining triggers
and executes model retraining workflow when conditions are met.

Example:
    >>> from openfatture.ai.ml.retraining import RetrainingScheduler
    >>>
    >>> # Start scheduler
    >>> scheduler = RetrainingScheduler()
    >>> scheduler.start()
    >>>
    >>> # Check status
    >>> status = scheduler.get_status()
    >>> print(status)
    >>>
    >>> # Trigger manual retraining
    >>> await scheduler.trigger_manual_retraining("cash_flow")
    >>>
    >>> # Stop scheduler
    >>> scheduler.stop()
"""

import asyncio
from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]

from openfatture.ai.ml.retraining.config import get_retraining_config
from openfatture.ai.ml.retraining.triggers import RetrainingTrigger
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class RetrainingScheduler:
    """Automatic model retraining scheduler.

    Manages periodic checks for retraining triggers and executes
    the retraining workflow when conditions are met.

    Uses APScheduler BackgroundScheduler for non-blocking execution.

    Example:
        >>> scheduler = RetrainingScheduler()
        >>> scheduler.start()
        >>>
        >>> # Scheduler runs in background
        >>> # Check status
        >>> status = scheduler.get_status()
        >>>
        >>> # Stop when done
        >>> scheduler.stop()
    """

    def __init__(self):
        """Initialize retraining scheduler."""
        self.config = get_retraining_config()
        self.trigger_checker = RetrainingTrigger()

        # APScheduler instance
        self.scheduler = BackgroundScheduler()

        # State tracking
        self.running = False
        self.last_check_time: datetime | None = None
        self.last_retrain_time: datetime | None = None
        self.retraining_in_progress = False

        logger.info("retraining_scheduler_initialized", enabled=self.config.enabled)

    def start(self) -> None:
        """Start the retraining scheduler.

        Schedules periodic trigger checks based on config.check_interval_hours.
        """
        if not self.config.enabled:
            logger.warning(
                "retraining_scheduler_disabled",
                message="Set OPENFATTURE_RETRAIN_ENABLED=true to enable",
            )
            return

        if self.running:
            logger.warning("scheduler_already_running")
            return

        # Schedule periodic checks
        interval_hours = self.config.check_interval_hours

        self.scheduler.add_job(
            func=self._check_and_retrain,
            trigger=IntervalTrigger(hours=interval_hours),
            id="retraining_check",
            name="Check Retraining Triggers",
            replace_existing=True,
        )

        # Start scheduler
        self.scheduler.start()
        self.running = True

        logger.info(
            "retraining_scheduler_started",
            interval_hours=interval_hours,
            dry_run=self.config.dry_run,
        )

    def stop(self) -> None:
        """Stop the retraining scheduler."""
        if not self.running:
            logger.warning("scheduler_not_running")
            return

        self.scheduler.shutdown(wait=True)
        self.running = False

        logger.info("retraining_scheduler_stopped")

    def _check_and_retrain(self) -> None:
        """Check triggers and execute retraining if needed.

        This is the main scheduled job that:
        1. Checks retraining triggers
        2. Executes retraining if triggered
        3. Handles errors and logging
        """
        self.last_check_time = datetime.now()

        logger.info("retraining_check_started")

        try:
            # Check if retraining should be triggered
            should_trigger, reasons = self.trigger_checker.should_trigger_retraining("cash_flow")

            if not should_trigger:
                logger.info("retraining_not_needed")
                return

            # Log trigger reasons
            logger.info(
                "retraining_triggered",
                reason_count=len(reasons),
                reasons=[r.to_dict() for r in reasons],
            )

            # Execute retraining (async operation in sync context)
            if self.config.dry_run:
                logger.info("retraining_skipped_dry_run", message="Dry run mode enabled")
            else:
                # Run async retraining in new event loop
                # Note: APScheduler runs in background thread, so we need explicit event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.trigger_manual_retraining("cash_flow"))
                finally:
                    loop.close()

        except Exception as e:
            logger.error("retraining_check_failed", error=str(e), exc_info=True)

    async def trigger_manual_retraining(
        self, model_name: str = "cash_flow", force: bool = False
    ) -> dict[str, Any]:
        """Manually trigger model retraining.

        Args:
            model_name: Name of the model to retrain
            force: Force retraining even if triggers not met

        Returns:
            Dictionary with retraining results

        Raises:
            RuntimeError: If retraining already in progress
        """
        if self.retraining_in_progress:
            raise RuntimeError("Retraining already in progress")

        self.retraining_in_progress = True

        try:
            logger.info("manual_retraining_triggered", model_name=model_name, force=force)

            # Check triggers (unless forced)
            if not force:
                should_trigger, reasons = self.trigger_checker.should_trigger_retraining(model_name)

                if not should_trigger:
                    logger.info("retraining_not_needed_manual")
                    return {
                        "success": False,
                        "message": "Retraining triggers not met",
                        "model_name": model_name,
                    }

                logger.info("retraining_reasons", reasons=[r.to_dict() for r in reasons])

            # Import here to avoid circular dependency
            from openfatture.ai.agents.cash_flow_predictor import CashFlowPredictorAgent

            # Execute retraining via CashFlowPredictor
            agent = CashFlowPredictorAgent()

            if self.config.dry_run:
                logger.info("retraining_dry_run", model_name=model_name)
                result = {
                    "success": True,
                    "dry_run": True,
                    "message": "Dry run mode - retraining not executed",
                    "model_name": model_name,
                }
            else:
                # This will call retrain_from_feedback (to be implemented next)
                await agent.initialize(force_retrain=True)

                self.last_retrain_time = datetime.now()

                result = {
                    "success": True,
                    "dry_run": False,
                    "message": "Retraining completed successfully",
                    "model_name": model_name,
                    "retrained_at": self.last_retrain_time.isoformat(),
                }

            logger.info("retraining_completed", result=result)

            return result

        except Exception as e:
            logger.error("retraining_failed", model_name=model_name, error=str(e), exc_info=True)
            return {
                "success": False,
                "message": f"Retraining failed: {str(e)}",
                "model_name": model_name,
            }

        finally:
            self.retraining_in_progress = False

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status.

        Returns:
            Dictionary with scheduler status and statistics
        """
        # Get trigger summary
        trigger_summary = self.trigger_checker.get_trigger_summary("cash_flow")

        # Get next scheduled run
        next_run_time = None
        if self.running:
            job = self.scheduler.get_job("retraining_check")
            if job:
                next_run_time = job.next_run_time.isoformat() if job.next_run_time else None

        status = {
            "enabled": self.config.enabled,
            "running": self.running,
            "dry_run": self.config.dry_run,
            "retraining_in_progress": self.retraining_in_progress,
            "interval_hours": self.config.check_interval_hours,
            "last_check_time": (self.last_check_time.isoformat() if self.last_check_time else None),
            "last_retrain_time": (
                self.last_retrain_time.isoformat() if self.last_retrain_time else None
            ),
            "next_run_time": next_run_time,
            "trigger_status": trigger_summary,
        }

        return status


# Global scheduler instance (singleton pattern)
_scheduler: RetrainingScheduler | None = None


def get_scheduler() -> RetrainingScheduler:
    """Get or create global scheduler instance.

    Returns:
        RetrainingScheduler singleton
    """
    global _scheduler

    if _scheduler is None:
        _scheduler = RetrainingScheduler()

    return _scheduler
