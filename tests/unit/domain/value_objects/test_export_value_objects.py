"""Unit tests for the Export Engine value objects (ADR-0014)."""

from __future__ import annotations

from datetime import datetime

import pytest

from qa_servicenow_assistant.domain.value_objects.export_manifest import (
    ExportManifest,
    ExportManifestEntry,
)
from qa_servicenow_assistant.domain.value_objects.export_result import ExportResult


def test_export_manifest_defaults_timestamp() -> None:
    manifest = ExportManifest(execution_id="exec-1", entries=())

    assert isinstance(manifest.exported_at, datetime)
    assert manifest.exported_at.tzinfo is not None


def test_export_manifest_is_frozen() -> None:
    manifest = ExportManifest(execution_id="exec-1", entries=())

    with pytest.raises(AttributeError):
        manifest.execution_id = "other"  # type: ignore[misc]


def test_export_manifest_entry_holds_fields() -> None:
    entry = ExportManifestEntry(description="report", archive_name="00_report.json", size_bytes=42)

    assert entry.description == "report"
    assert entry.archive_name == "00_report.json"
    assert entry.size_bytes == 42


def test_export_result_is_frozen() -> None:
    result = ExportResult(success=True, archive_path=None, manifest=None)

    with pytest.raises(AttributeError):
        result.success = False  # type: ignore[misc]
