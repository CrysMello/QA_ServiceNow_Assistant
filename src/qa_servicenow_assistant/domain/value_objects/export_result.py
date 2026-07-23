"""Outcome of ExportEngine.export() (ADR-0014)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qa_servicenow_assistant.domain.value_objects.export_manifest import ExportManifest


@dataclass(frozen=True)
class ExportResult:
    """Never raised for expected failures (persistence/I-O errors) -
    consistent with Checkpoint Engine and Reporting Engine.
    InvalidExportRequestError is the exception, reserved for
    caller-contract violations (empty execution_id or no items)."""

    success: bool
    archive_path: Path | None
    manifest: ExportManifest | None
    error_message: str | None = None
