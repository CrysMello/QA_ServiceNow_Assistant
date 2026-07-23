"""Outcome of CheckpointEngine.restore_latest() (SAD Cap. 20, 20.5 - Fluxo
de Recuperacao)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint


@dataclass(frozen=True)
class CheckpointRestoreResult:
    """Never raised for expected failures (no checkpoint found, corrupted
    data, inconsistent context) - consistent with the rest of this
    codebase's structured-result pattern."""

    success: bool
    checkpoint: Checkpoint | None
    error_message: str | None = None
