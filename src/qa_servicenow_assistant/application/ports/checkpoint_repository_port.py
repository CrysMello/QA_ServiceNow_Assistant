"""Port for persisting and retrieving Checkpoint state (SAD 20.3 - "State
Repository: Persistir checkpoints. Dependencias: Infrastructure Layer").
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint


class CheckpointRepositoryPort(ABC):
    """Contract implemented by infrastructure adapters responsible for
    checkpoint persistence. Every method raises CheckpointPersistenceError
    on I/O failure or corrupted/unparseable stored data - never a bare
    exception (AI Coding Standards Sec.11)."""

    @abstractmethod
    def save(self, checkpoint: Checkpoint) -> None:
        """Append checkpoint to the persisted history for its execution_id."""
        raise NotImplementedError

    @abstractmethod
    def latest_for_execution(self, execution_id: str) -> Checkpoint | None:
        """Most recently saved checkpoint for execution_id, or None if
        none has been saved yet."""
        raise NotImplementedError

    @abstractmethod
    def history_for_execution(self, execution_id: str) -> tuple[Checkpoint, ...]:
        """All checkpoints saved for execution_id, oldest first. Empty
        tuple if none has been saved yet."""
        raise NotImplementedError
