"""Model Version Management for ML Models.

Handles versioning, rollback, and lifecycle management of trained ML models.
Each version is stored with complete metadata for audit and comparison.

Example:
    >>> from openfatture.ai.ml.retraining import ModelVersionManager
    >>> manager = ModelVersionManager()
    >>>
    >>> # Save current model as new version
    >>> version_id = manager.save_version(
    ...     model_name="cash_flow",
    ...     metrics={"mae": 2.5, "rmse": 3.1},
    ...     notes="Retrained with 100 new feedback samples"
    ... )
    >>>
    >>> # List all versions
    >>> versions = manager.list_versions("cash_flow")
    >>>
    >>> # Rollback to previous version
    >>> manager.rollback_to_version("cash_flow", version_id)
"""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openfatture.ai.ml.config import get_ml_config
from openfatture.ai.ml.retraining.config import get_retraining_config
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ModelVersion:
    """Metadata for a specific model version.

    Attributes:
        version_id: Unique version identifier (timestamp-based)
        model_name: Name of the model (e.g., "cash_flow")
        created_at: Creation timestamp
        metrics: Performance metrics dict
        notes: Optional version notes
        config_snapshot: ML config snapshot at training time
    """

    def __init__(
        self,
        version_id: str,
        model_name: str,
        created_at: datetime,
        metrics: dict[str, Any],
        notes: str | None = None,
        config_snapshot: dict[str, Any] | None = None,
    ):
        """Initialize model version metadata."""
        self.version_id = version_id
        self.model_name = model_name
        self.created_at = created_at
        self.metrics = metrics
        self.notes = notes
        self.config_snapshot = config_snapshot or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version_id": self.version_id,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics,
            "notes": self.notes,
            "config_snapshot": self.config_snapshot,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelVersion":
        """Create from dictionary."""
        return cls(
            version_id=data["version_id"],
            model_name=data["model_name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metrics=data.get("metrics", {}),
            notes=data.get("notes"),
            config_snapshot=data.get("config_snapshot", {}),
        )


class ModelVersionManager:
    """Manages ML model versioning and rollback.

    Handles:
    - Saving new model versions with metadata
    - Loading specific versions
    - Listing all versions
    - Rolling back to previous versions
    - Cleaning up old versions (based on retention policy)

    Example:
        >>> manager = ModelVersionManager()
        >>> version_id = manager.save_version("cash_flow", metrics={"mae": 2.5})
        >>> versions = manager.list_versions("cash_flow")
        >>> manager.rollback_to_version("cash_flow", version_id)
    """

    def __init__(self):
        """Initialize version manager."""
        self.ml_config = get_ml_config()
        self.retrain_config = get_retraining_config()
        self.versions_path = self.retrain_config.versions_path
        self.versions_path.mkdir(parents=True, exist_ok=True)

        logger.info("model_version_manager_initialized", path=str(self.versions_path))

    def save_version(
        self,
        model_name: str = "cash_flow",
        metrics: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> str:
        """Save current model as a new version.

        Creates a timestamped version directory and copies all model files.

        Args:
            model_name: Name of the model to version
            metrics: Performance metrics for this version
            notes: Optional version notes

        Returns:
            Version ID (timestamp-based)

        Raises:
            FileNotFoundError: If current model files don't exist
        """
        # Generate version ID
        version_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        # Get current model path
        current_model_prefix = self.ml_config.get_model_filepath(model_name)

        # Check if model files exist
        if not self._model_files_exist(current_model_prefix):
            raise FileNotFoundError(
                f"Model files not found at {current_model_prefix}. "
                "Train the model before creating a version."
            )

        # Create version directory
        version_dir = self.versions_path / model_name / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy all model files
        self._copy_model_files(current_model_prefix, version_dir / model_name)

        # Load metrics from current model if not provided
        if metrics is None:
            metrics_path = Path(f"{current_model_prefix}_metrics.json")
            if metrics_path.exists():
                with metrics_path.open("r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
                    metrics = metrics_data.get("metrics", {})
            else:
                metrics = {}

        # Create version metadata
        config_snapshot = self.ml_config.model_dump()
        config_snapshot = {
            k: (str(v) if isinstance(v, Path) else v) for k, v in config_snapshot.items()
        }

        version = ModelVersion(
            version_id=version_id,
            model_name=model_name,
            created_at=datetime.now(UTC),
            metrics=metrics,
            notes=notes,
            config_snapshot=config_snapshot,
        )

        # Save version metadata
        metadata_path = version_dir / "version_metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(version.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(
            "model_version_saved",
            model_name=model_name,
            version_id=version_id,
            path=str(version_dir),
            metrics=metrics,
        )

        # Cleanup old versions
        self._cleanup_old_versions(model_name)

        return version_id

    def load_version(
        self,
        model_name: str,
        version_id: str,
        restore_to_current: bool = False,
    ) -> ModelVersion:
        """Load a specific model version.

        Args:
            model_name: Name of the model
            version_id: Version ID to load
            restore_to_current: If True, restore to current model location

        Returns:
            ModelVersion metadata

        Raises:
            FileNotFoundError: If version doesn't exist
        """
        version_dir = self.versions_path / model_name / version_id

        if not version_dir.exists():
            raise FileNotFoundError(f"Version {version_id} not found for model {model_name}")

        # Load version metadata
        metadata_path = version_dir / "version_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Version metadata not found at {metadata_path}")

        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

        version = ModelVersion.from_dict(metadata)

        # Restore to current location if requested
        if restore_to_current:
            current_model_prefix = self.ml_config.get_model_filepath(model_name)
            self._copy_model_files(version_dir / model_name, current_model_prefix)

            logger.info(
                "model_version_restored",
                model_name=model_name,
                version_id=version_id,
                path=current_model_prefix,
            )

        return version

    def rollback_to_version(self, model_name: str, version_id: str) -> None:
        """Rollback to a previous model version.

        Restores the specified version to the current model location.

        Args:
            model_name: Name of the model
            version_id: Version ID to rollback to

        Raises:
            FileNotFoundError: If version doesn't exist
        """
        logger.info("rolling_back_model", model_name=model_name, version_id=version_id)

        # Load and restore version
        self.load_version(model_name, version_id, restore_to_current=True)

        logger.info("model_rollback_completed", model_name=model_name, version_id=version_id)

    def list_versions(self, model_name: str) -> list[ModelVersion]:
        """List all versions for a model.

        Args:
            model_name: Name of the model

        Returns:
            List of ModelVersion objects, sorted by creation time (newest first)
        """
        model_versions_dir = self.versions_path / model_name

        if not model_versions_dir.exists():
            return []

        versions = []

        for version_dir in model_versions_dir.iterdir():
            if not version_dir.is_dir():
                continue

            metadata_path = version_dir / "version_metadata.json"
            if not metadata_path.exists():
                logger.warning(
                    "version_metadata_missing",
                    model_name=model_name,
                    version_id=version_dir.name,
                )
                continue

            try:
                with metadata_path.open("r", encoding="utf-8") as f:
                    metadata = json.load(f)

                version = ModelVersion.from_dict(metadata)
                versions.append(version)

            except Exception as e:
                logger.error(
                    "version_load_failed",
                    model_name=model_name,
                    version_id=version_dir.name,
                    error=str(e),
                )

        # Sort by creation time (newest first)
        versions.sort(key=lambda v: v.created_at, reverse=True)

        return versions

    def get_latest_version(self, model_name: str) -> ModelVersion | None:
        """Get the most recent version for a model.

        Args:
            model_name: Name of the model

        Returns:
            Latest ModelVersion or None if no versions exist
        """
        versions = self.list_versions(model_name)
        return versions[0] if versions else None

    def delete_version(self, model_name: str, version_id: str) -> None:
        """Delete a specific model version.

        Args:
            model_name: Name of the model
            version_id: Version ID to delete

        Raises:
            FileNotFoundError: If version doesn't exist
        """
        version_dir = self.versions_path / model_name / version_id

        if not version_dir.exists():
            raise FileNotFoundError(f"Version {version_id} not found for model {model_name}")

        # Delete version directory
        shutil.rmtree(version_dir)

        logger.info("model_version_deleted", model_name=model_name, version_id=version_id)

    def _cleanup_old_versions(self, model_name: str) -> None:
        """Remove old versions exceeding max_versions limit.

        Args:
            model_name: Name of the model
        """
        versions = self.list_versions(model_name)

        # Keep only max_versions
        if len(versions) > self.retrain_config.max_versions:
            versions_to_delete = versions[self.retrain_config.max_versions :]

            for version in versions_to_delete:
                try:
                    self.delete_version(model_name, version.version_id)
                    logger.info(
                        "old_version_cleaned_up",
                        model_name=model_name,
                        version_id=version.version_id,
                    )
                except Exception as e:
                    logger.error(
                        "version_cleanup_failed",
                        model_name=model_name,
                        version_id=version.version_id,
                        error=str(e),
                    )

    def _model_files_exist(self, filepath_prefix: str) -> bool:
        """Check if model files exist at the given prefix.

        Args:
            filepath_prefix: Model file prefix path

        Returns:
            True if all required files exist
        """
        prophet_path = Path(f"{filepath_prefix}_prophet.json")
        xgboost_path = Path(f"{filepath_prefix}_xgboost.json")
        pipeline_path = Path(f"{filepath_prefix}_pipeline.pkl")

        return prophet_path.exists() and xgboost_path.exists() and pipeline_path.exists()

    def _copy_model_files(self, source_prefix: str | Path, dest_prefix: str | Path) -> None:
        """Copy all model files from source to destination.

        Args:
            source_prefix: Source file prefix (can be string or Path)
            dest_prefix: Destination file prefix (can be string or Path)
        """
        # Convert to strings for suffix concatenation
        source_str = str(source_prefix)
        dest_str = str(dest_prefix)

        # Ensure destination directory exists
        dest_dir = Path(dest_str).parent
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy all model artifacts
        for suffix in ["_prophet.json", "_xgboost.json", "_pipeline.pkl", "_metrics.json"]:
            source_file = Path(f"{source_str}{suffix}")
            dest_file = Path(f"{dest_str}{suffix}")

            if source_file.exists():
                shutil.copy2(source_file, dest_file)
            elif suffix != "_metrics.json":  # metrics is optional
                raise FileNotFoundError(f"Required model file not found: {source_file}")
