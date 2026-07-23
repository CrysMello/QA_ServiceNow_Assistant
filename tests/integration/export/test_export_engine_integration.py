"""Integration test for ExportEngine using the real ZipExportRepository
against a real filesystem directory (tmp_path), demonstrating
compatibility between the Export Engine application service and its real
infrastructure adapter (ADR-0014).

Simulates the intended real usage: a report already written by Reporting
Engine (as a plain file, not through ReportingEngine itself - Export
Engine has no dependency on it) plus a fake "screenshot" file are
packaged together into one archive.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.export.export_engine import (
    ExportEngine,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ExportConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem
from qa_servicenow_assistant.domain.value_objects.export_request import ExportRequest
from qa_servicenow_assistant.infrastructure.export.zip_export_repository import (
    ZipExportRepository,
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


def test_real_artifacts_are_packaged_into_a_single_archive(tmp_path: Path) -> None:
    report_path = tmp_path / "exec-real-1.json"
    report_path.write_text(json.dumps({"execution_id": "exec-real-1", "status": "success"}), encoding="utf-8")
    screenshot_path = tmp_path / "final.png"
    screenshot_path.write_bytes(b"fake-png-bytes")

    configuration = ExportConfiguration(directory=tmp_path / "exports")
    log_port = RecordingLogPort()
    engine = ExportEngine(ZipExportRepository(configuration), log_port)

    request = ExportRequest(
        execution_id="exec-real-1",
        items=(
            ExportItem(description="execution_report", source_path=report_path),
            ExportItem(description="final_screenshot", source_path=screenshot_path),
        ),
    )

    result = engine.export(request)

    assert result.success is True
    assert result.archive_path == tmp_path / "exports" / "exec-real-1.zip"
    assert result.manifest is not None
    assert len(result.manifest.entries) == 2
    assert "Export completed" in log_port.messages

    with zipfile.ZipFile(result.archive_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert any(name.endswith("exec-real-1.json") for name in names)
        assert any(name.endswith("final.png") for name in names)
