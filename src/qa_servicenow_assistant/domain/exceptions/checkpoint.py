"""Checkpoint Engine exceptions (SAD Cap. 20)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class CheckpointError(QaServiceNowAssistantError):
    """Base exception for checkpoint persistence/recovery failures."""


class InvalidCheckpointStateError(CheckpointError):
    """Raised when CheckpointEngine.save_checkpoint() is asked to persist
    an inconsistent state (SAD 20.8 - "Checkpoints devem ser criados
    apenas em estados consistentes"): missing execution_id, workflow_id or
    last_completed_step. A caller-contract violation, not an operational
    failure - never caught internally, always propagates.
    """


class CheckpointPersistenceError(CheckpointError):
    """Raised by CheckpointRepositoryPort implementations when persisting
    or reading a checkpoint fails (I/O error, non-serializable data, or
    corrupted/unparseable stored data). Always chains the original error
    via `raise ... from error`. Caught by CheckpointEngine and turned into
    a structured CheckpointSaveResult/CheckpointRestoreResult (SAD 20.8 -
    "Falhas de recuperacao devem ser registradas"), consistent with the
    majority structured-result pattern used across this codebase (Navigation
    Engine, Page Recognition, Selector Resolver, Retry Engine).
    """
