"""Checkpoint: persisted execution state (SAD Cap. 20 - Checkpoint Engine).

Fields trace directly to SAD 20.4 (Informacoes Persistidas): Workflow,
Etapa atual, Pagina, Dados temporarios, Timestamp, Resultado parcial.
execution_id is not listed by SAD 20.4 itself, but every persisted record
in this codebase carries one (RNF-011 - "toda execucao deve possuir
identificador unico e trilha de auditoria"; same precedent as
RecordedElement) - it is also the key CheckpointRepositoryPort uses to
group and order checkpoint history per execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


@dataclass(frozen=True)
class Checkpoint:
    """Immutable snapshot of workflow execution state at a point in time.

    temporary_data is a plain dict (not immutable) for the same reason as
    CollectedElement.attributes: ergonomic access, with the caveat that
    instances are not truly immutable for that field. Values must be
    JSON-serializable - CheckpointSerializer persists them as-is and
    JsonFileCheckpointRepository raises CheckpointPersistenceError if they
    are not.
    """

    execution_id: str
    workflow_id: str
    last_completed_step: str
    page: PageIdentifier | None = None
    temporary_data: dict[str, Any] = field(default_factory=dict)
    partial_result: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
