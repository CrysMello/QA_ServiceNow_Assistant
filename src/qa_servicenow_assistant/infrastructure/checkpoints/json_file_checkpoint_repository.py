"""JSON-file-based implementation of CheckpointRepositoryPort (SAD 20.3 -
State Repository).

One JSON file per execution_id under CheckpointConfiguration.directory,
holding a JSON array of serialized checkpoints in save() order (oldest
first) - this file IS the checkpoint history for that execution
(SAD 20.2 - "Registrar historico de checkpoints").

Single-process CLI tool (SAD 29.2 - "Execucao via CLI"): no file locking
or concurrent-writer protection is implemented, matching the scope of the
rest of this codebase.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.checkpoint_repository_port import (
    CheckpointRepositoryPort,
)
from qa_servicenow_assistant.domain.exceptions.checkpoint import (
    CheckpointPersistenceError,
)
from qa_servicenow_assistant.domain.services.checkpoint_serializer import (
    CheckpointSerializer,
)
from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.configuration import (
    CheckpointConfiguration,
)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")


class JsonFileCheckpointRepository(CheckpointRepositoryPort):
    """Persists checkpoints as one JSON array file per execution_id.

    execution_id is caller-supplied and used to build a file path; it is
    sanitized (non alnum/dash/underscore characters replaced with "_")
    so it can never be used to escape configuration.directory.
    """

    def __init__(
        self,
        configuration: CheckpointConfiguration | None = None,
        serializer: CheckpointSerializer | None = None,
    ) -> None:
        self._directory = Path((configuration or CheckpointConfiguration()).directory)
        self._serializer = serializer or CheckpointSerializer()
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: Checkpoint) -> None:
        history = self._read(checkpoint.execution_id)
        history.append(self._serializer.to_dict(checkpoint))
        self._write(checkpoint.execution_id, history)

    def latest_for_execution(self, execution_id: str) -> Checkpoint | None:
        history = self.history_for_execution(execution_id)
        return history[-1] if history else None

    def history_for_execution(self, execution_id: str) -> tuple[Checkpoint, ...]:
        raw_history = self._read(execution_id)
        try:
            return tuple(self._serializer.from_dict(entry) for entry in raw_history)
        except (KeyError, TypeError, ValueError) as error:
            raise CheckpointPersistenceError(
                f"Corrupted checkpoint data for execution_id={execution_id}"
            ) from error

    def _path_for(self, execution_id: str) -> Path:
        safe_name = _UNSAFE_FILENAME_CHARS.sub("_", execution_id)
        return self._directory / f"{safe_name}.json"

    def _read(self, execution_id: str) -> list[dict[str, Any]]:
        path = self._path_for(execution_id)
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as error:
            raise CheckpointPersistenceError(
                f"Failed to read checkpoint file for execution_id={execution_id}: {path}"
            ) from error

    def _write(self, execution_id: str, history: list[dict[str, Any]]) -> None:
        path = self._path_for(execution_id)
        try:
            serialized = json.dumps(history, indent=2)
        except TypeError as error:
            raise CheckpointPersistenceError(
                f"Checkpoint data for execution_id={execution_id} is not JSON-serializable"
            ) from error

        try:
            path.write_text(serialized, encoding="utf-8")
        except OSError as error:
            raise CheckpointPersistenceError(
                f"Failed to write checkpoint file for execution_id={execution_id}: {path}"
            ) from error
