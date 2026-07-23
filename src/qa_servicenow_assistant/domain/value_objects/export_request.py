"""ExportRequest: what to package for a single execution (ADR-0014)."""

from __future__ import annotations

from dataclasses import dataclass

from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem


@dataclass(frozen=True)
class ExportRequest:
    execution_id: str
    items: tuple[ExportItem, ...]
