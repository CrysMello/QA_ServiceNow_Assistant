"""Unit tests for JsonFileCheckpointRepository (SAD 20.3 - State Repository)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_servicenow_assistant.domain.exceptions.checkpoint import (
    CheckpointPersistenceError,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.configuration import (
    CheckpointConfiguration,
)
from qa_servicenow_assistant.infrastructure.checkpoints.json_file_checkpoint_repository import (
    JsonFileCheckpointRepository,
)


def make_repository(tmp_path: Path) -> JsonFileCheckpointRepository:
    return JsonFileCheckpointRepository(CheckpointConfiguration(directory=tmp_path / "checkpoints"))


def test_creates_configured_directory_on_construction(tmp_path: Path) -> None:
    directory = tmp_path / "checkpoints"
    assert not directory.exists()

    JsonFileCheckpointRepository(CheckpointConfiguration(directory=directory))

    assert directory.is_dir()


def test_latest_for_execution_returns_none_when_nothing_saved(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)

    assert repository.latest_for_execution("exec-1") is None


def test_history_for_execution_returns_empty_tuple_when_nothing_saved(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)

    assert repository.history_for_execution("exec-1") == ()


def test_save_then_latest_for_execution_returns_the_saved_checkpoint(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    checkpoint = Checkpoint(
        execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_1"
    )

    repository.save(checkpoint)
    latest = repository.latest_for_execution("exec-1")

    assert latest == checkpoint


def test_multiple_saves_are_kept_as_ordered_history(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    first = Checkpoint(execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_1")
    second = Checkpoint(execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_2")
    third = Checkpoint(execution_id="exec-1", workflow_id="workflow-1", last_completed_step="step_3")

    repository.save(first)
    repository.save(second)
    repository.save(third)

    history = repository.history_for_execution("exec-1")

    assert history == (first, second, third)
    assert repository.latest_for_execution("exec-1") == third


def test_different_execution_ids_are_isolated(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    checkpoint_a = Checkpoint(execution_id="exec-a", workflow_id="w", last_completed_step="step_1")
    checkpoint_b = Checkpoint(execution_id="exec-b", workflow_id="w", last_completed_step="step_1")

    repository.save(checkpoint_a)
    repository.save(checkpoint_b)

    assert repository.history_for_execution("exec-a") == (checkpoint_a,)
    assert repository.history_for_execution("exec-b") == (checkpoint_b,)


def test_execution_id_with_unsafe_characters_stays_inside_configured_directory(tmp_path: Path) -> None:
    directory = tmp_path / "checkpoints"
    repository = JsonFileCheckpointRepository(CheckpointConfiguration(directory=directory))
    checkpoint = Checkpoint(
        execution_id="../../etc/passwd", workflow_id="w", last_completed_step="step_1"
    )

    repository.save(checkpoint)

    written_files = list(directory.iterdir())
    assert len(written_files) == 1
    assert written_files[0].parent == directory
    assert repository.latest_for_execution("../../etc/passwd") == checkpoint


def test_corrupted_json_file_raises_on_read(tmp_path: Path) -> None:
    directory = tmp_path / "checkpoints"
    repository = JsonFileCheckpointRepository(CheckpointConfiguration(directory=directory))
    (directory / "exec-1.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(CheckpointPersistenceError):
        repository.latest_for_execution("exec-1")


def test_malformed_entry_raises_on_read(tmp_path: Path) -> None:
    directory = tmp_path / "checkpoints"
    repository = JsonFileCheckpointRepository(CheckpointConfiguration(directory=directory))
    (directory / "exec-1.json").write_text('[{"workflow_id": "w"}]', encoding="utf-8")

    with pytest.raises(CheckpointPersistenceError):
        repository.history_for_execution("exec-1")


def test_non_json_serializable_temporary_data_raises_on_save(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    checkpoint = Checkpoint(
        execution_id="exec-1",
        workflow_id="workflow-1",
        last_completed_step="step_1",
        temporary_data={"unsupported": {1, 2, 3}},
    )

    with pytest.raises(CheckpointPersistenceError):
        repository.save(checkpoint)

    assert repository.latest_for_execution("exec-1") is None
