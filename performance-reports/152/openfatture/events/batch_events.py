"""Batch operation events.

Events emitted during batch imports and exports.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseEvent


@dataclass(frozen=True)
class BatchImportStartedEvent(BaseEvent):
    """Event emitted when a batch import operation begins.

    Triggered before processing CSV file.

    Hook point: pre-batch-import
    """

    file_path: str
    operation_type: str  # import, export
    dry_run: bool = False


@dataclass(frozen=True)
class BatchImportCompletedEvent(BaseEvent):
    """Event emitted when a batch import operation completes.

    Triggered after all records processed.

    Hook point: post-batch-import
    """

    file_path: str
    operation_type: str
    success: bool
    records_processed: int
    records_succeeded: int
    records_failed: int
    errors: list[str] | None = None
