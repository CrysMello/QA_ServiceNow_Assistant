"""Integration test for CheckpointEngine using the real
JsonFileCheckpointRepository against a real filesystem directory
(tmp_path), demonstrating compatibility between the Checkpoint Engine
application service and its real infrastructure adapter (SAD Cap. 20).

Simulates the interruption/recovery scenario from SAD 20.6 ("Recuperacao
apos reinicio da aplicacao"): a checkpoint is saved by one CheckpointEngine
instance, then a brand new instance - backed by a fresh
JsonFileCheckpointRepository pointed at the same directory, mirroring a
process restart - restores it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.checkpoint.checkpoint_engine import (
    CheckpointEngine,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    CheckpointConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)
from qa_servicenow_assistant.infrastructure.checkpoints.json_file_checkpoint_repository import (
    JsonFileCheckpointRepository,
)


class RecordingLogPort(LogPort):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def bind(self, **context: Any) -> "RecordingLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def warning(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def error(self, message: str, **context: Any) -> None:
        self.messages.append(message)

    def critical(self, message: str, **context: Any) -> None:
        pass


def test_checkpoint_saved_by_one_process_is_restored_after_a_simulated_restart(
    tmp_path: Path,
) -> None:
    configuration = CheckpointConfiguration(directory=tmp_path / "checkpoints")
    log_port = RecordingLogPort()

    writer_engine = CheckpointEngine(JsonFileCheckpointRepository(configuration), log_port)
    save_result = writer_engine.save_checkpoint(
        execution_id="exec-real-1",
        workflow_id="incident_registration",
        last_completed_step="fill_short_description",
        page=PageIdentifier(key="incident_form"),
        temporary_data={"incident_number": "INC0010045"},
        partial_result="in_progress",
    )
    assert save_result.success is True

    # A fresh repository instance over the same directory, as would happen
    # after the application process restarts.
    reader_engine = CheckpointEngine(JsonFileCheckpointRepository(configuration), log_port)
    restore_result = reader_engine.restore_latest("exec-real-1")

    assert restore_result.success is True
    restored = restore_result.checkpoint
    assert restored is not None
    assert restored.workflow_id == "incident_registration"
    assert restored.last_completed_step == "fill_short_description"
    assert restored.page == PageIdentifier(key="incident_form")
    assert restored.temporary_data == {"incident_number": "INC0010045"}
    assert "Checkpoint saved" in log_port.messages
    assert "Checkpoint restored" in log_port.messages


def test_history_accumulates_across_multiple_checkpoints_on_disk(tmp_path: Path) -> None:
    configuration = CheckpointConfiguration(directory=tmp_path / "checkpoints")
    engine = CheckpointEngine(JsonFileCheckpointRepository(configuration), RecordingLogPort())

    engine.save_checkpoint(execution_id="exec-real-2", workflow_id="w", last_completed_step="step_1")
    engine.save_checkpoint(execution_id="exec-real-2", workflow_id="w", last_completed_step="step_2")
    engine.save_checkpoint(execution_id="exec-real-2", workflow_id="w", last_completed_step="step_3")

    history = engine.history("exec-real-2")

    assert [checkpoint.last_completed_step for checkpoint in history] == [
        "step_1",
        "step_2",
        "step_3",
    ]
