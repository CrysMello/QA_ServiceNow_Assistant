"""Outcome of CheckpointEngine.save_checkpoint() (SAD Cap. 20)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint


@dataclass(frozen=True)
class CheckpointSaveResult:
    """Never raised for expected failures (persistence I/O errors) -
    consistent with Navigation Engine, Page Recognition, Selector
    Resolver and Retry Engine. InvalidCheckpointStateError is the
    exception, reserved for caller-contract violations (SAD 20.8).
    """

    success: bool
    checkpoint: Checkpoint | None
    error_message: str | None = None
