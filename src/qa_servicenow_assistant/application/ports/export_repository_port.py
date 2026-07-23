"""Port for packaging and persisting an export archive (ADR-0014)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem
from qa_servicenow_assistant.domain.value_objects.export_manifest import ExportManifest


class ExportRepositoryPort(ABC):
    """Contract implemented by infrastructure adapters responsible for
    building an export package. Raises ExportPersistenceError on I/O
    failure or a missing source file - never a bare exception (AI Coding
    Standards Sec.11)."""

    @abstractmethod
    def save(self, execution_id: str, items: Sequence[ExportItem]) -> tuple[Path, ExportManifest]:
        """Package items into a single archive and return its path plus
        the resulting manifest."""
        raise NotImplementedError
