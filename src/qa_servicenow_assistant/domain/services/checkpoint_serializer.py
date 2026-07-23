"""CheckpointSerializer: pure domain service converting Checkpoint to/from
a JSON-safe plain dict (SAD 20.3 - "State Serializer: Serializar o estado
da execucao. Dependencias: Domain Model").

No I/O here (SAD 8.7 - "A Domain Layer nao acessa arquivos nem banco de
dados"); CheckpointRepositoryPort implementations are responsible for
actually writing/reading the dicts this class produces/consumes, and for
translating any failure (I/O error or malformed dict) into
CheckpointPersistenceError.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from qa_servicenow_assistant.domain.value_objects.checkpoint import Checkpoint
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class CheckpointSerializer:
    """Converts Checkpoint <-> plain dict (str/number/bool/None/dict/list
    only), suitable for json.dumps()/json.loads()."""

    def to_dict(self, checkpoint: Checkpoint) -> dict[str, Any]:
        return {
            "execution_id": checkpoint.execution_id,
            "workflow_id": checkpoint.workflow_id,
            "last_completed_step": checkpoint.last_completed_step,
            "page_key": checkpoint.page.key if checkpoint.page is not None else None,
            "temporary_data": dict(checkpoint.temporary_data),
            "partial_result": checkpoint.partial_result,
            "created_at": checkpoint.created_at.isoformat(),
        }

    def from_dict(self, data: dict[str, Any]) -> Checkpoint:
        """Raises KeyError/TypeError/ValueError on malformed input - the
        caller (JsonFileCheckpointRepository) is responsible for catching
        these and translating them into CheckpointPersistenceError."""
        page_key = data.get("page_key")
        return Checkpoint(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            last_completed_step=data["last_completed_step"],
            page=PageIdentifier(key=page_key) if page_key is not None else None,
            temporary_data=dict(data.get("temporary_data") or {}),
            partial_result=data.get("partial_result", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
        )
