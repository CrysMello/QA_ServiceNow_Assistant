"""Unit tests for CheckpointEngine (SAD Cap. 20).

Uses a fake CheckpointRepositoryPort and a fake LogPort (same pattern as
NavigationEngine's/RetryEngine's tests), since the real infrastructure
adapter (JsonFileCheckpointRepository) is exercised separately by its own
unit tests and by the integration test.
"""

from __future__ import annotations

from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.checkpoint_repository_port import (
    CheckpointRepositoryPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.checkpoint.checkpoint_engine import (
    CheckpointEngine,
)
from qa_servicenow_assistant.domain.exceptions.checkpoint import (
    CheckpointPersistenceError,
    InvalidCheckpointStateError,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.warning_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        self.warning_calls.append((message, context))

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


class FakeCheckpointRepository(CheckpointRepositoryPort):
    def __init__(self) -> None:
        self._history: dict[str, list[Checkpoint]] = {}
        self.save_error: Exception | None = None
        self.latest_error: Exception | None = None
        self.history_error: Exception | None = None

    def save(self, checkpoint: Checkpoint) -> None:
        if self.save_error is not None:
            raise self.save_error
        self._history.setdefault(checkpoint.execution_id, []).append(checkpoint)

    def latest_for_execution(self, execution_id: str) -> Checkpoint | None:
        if self.latest_error is not None:
            raise self.latest_error
        history = self._history.get(execution_id, [])
        return history[-1] if history else None

    def history_for_execution(self, execution_id: str) -> tuple[Checkpoint, ...]:
        if self.history_error is not None:
            raise self.history_error
        return tuple(self._history.get(execution_id, []))

    def seed(self, checkpoint: Checkpoint) -> None:
        self._history.setdefault(checkpoint.execution_id, []).append(checkpoint)


def test_save_checkpoint_persists_and_returns_success() -> None:
    repository = FakeCheckpointRepository()
    log_port = FakeLogPort()
    engine = CheckpointEngine(repository, log_port)

    result = engine.save_checkpoint(
        execution_id="exec-1",
        workflow_id="workflow-1",
        last_completed_step="step_1",
        page=PageIdentifier(key="incident_form"),
        temporary_data={"incident_number": "INC001"},
        partial_result="in_progress",
    )

    assert result.success is True
    assert result.checkpoint is not None
    assert result.checkpoint.execution_id == "exec-1"
    assert repository.history_for_execution("exec-1") == (result.checkpoint,)
    assert len(log_port.info_calls) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"execution_id": "", "workflow_id": "w", "last_completed_step": "s"},
        {"execution_id": "e", "workflow_id": "", "last_completed_step": "s"},
        {"execution_id": "e", "workflow_id": "w", "last_completed_step": ""},
    ],
)
def test_save_checkpoint_raises_on_inconsistent_state(kwargs: dict[str, str]) -> None:
    engine = CheckpointEngine(FakeCheckpointRepository(), FakeLogPort())

    with pytest.raises(InvalidCheckpointStateError):
        engine.save_checkpoint(**kwargs)


def test_save_checkpoint_returns_failed_result_on_persistence_error() -> None:
    repository = FakeCheckpointRepository()
    repository.save_error = CheckpointPersistenceError("disk full")
    log_port = FakeLogPort()
    engine = CheckpointEngine(repository, log_port)

    result = engine.save_checkpoint(
        execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_1"
    )

    assert result.success is False
    assert result.checkpoint is None
    assert result.error_message == "disk full"
    assert len(log_port.error_calls) == 1


def test_restore_latest_returns_failure_when_nothing_found() -> None:
    engine = CheckpointEngine(FakeCheckpointRepository(), FakeLogPort())

    result = engine.restore_latest("exec-1")

    assert result.success is False
    assert result.checkpoint is None
    assert "No checkpoint found" in result.error_message


def test_restore_latest_returns_the_last_saved_checkpoint() -> None:
    repository = FakeCheckpointRepository()
    log_port = FakeLogPort()
    engine = CheckpointEngine(repository, log_port)
    engine.save_checkpoint(execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_1")
    engine.save_checkpoint(execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_2")

    result = engine.restore_latest("exec-1")

    assert result.success is True
    assert result.checkpoint.last_completed_step == "step_2"
    assert any(message == "Checkpoint restored" for message, _ in log_port.info_calls)


def test_restore_latest_returns_failed_result_on_persistence_error() -> None:
    repository = FakeCheckpointRepository()
    repository.latest_error = CheckpointPersistenceError("corrupted file")
    engine = CheckpointEngine(repository, FakeLogPort())

    result = engine.restore_latest("exec-1")

    assert result.success is False
    assert result.error_message == "corrupted file"


def test_restore_latest_rejects_inconsistent_checkpoint() -> None:
    repository = FakeCheckpointRepository()
    inconsistent = Checkpoint(execution_id="exec-1", workflow_id="", last_completed_step="")
    repository.seed(inconsistent)
    log_port = FakeLogPort()
    engine = CheckpointEngine(repository, log_port)

    result = engine.restore_latest("exec-1")

    assert result.success is False
    assert "inconsistent" in result.error_message
    assert len(log_port.error_calls) == 1


def test_history_returns_all_saved_checkpoints_oldest_first() -> None:
    repository = FakeCheckpointRepository()
    engine = CheckpointEngine(repository, FakeLogPort())
    engine.save_checkpoint(execution_id="exec-1", workflow_id="w", last_completed_step="step_1")
    engine.save_checkpoint(execution_id="exec-1", workflow_id="w", last_completed_step="step_2")

    history = engine.history("exec-1")

    assert [checkpoint.last_completed_step for checkpoint in history] == ["step_1", "step_2"]


def test_history_returns_empty_tuple_on_persistence_error() -> None:
    repository = FakeCheckpointRepository()
    repository.history_error = CheckpointPersistenceError("boom")
    log_port = FakeLogPort()
    engine = CheckpointEngine(repository, log_port)

    result = engine.history("exec-1")

    assert result == ()
    assert len(log_port.error_calls) == 1
