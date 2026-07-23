"""Integration test for ReportingEngine using the real
FileReportRepository against a real filesystem directory (tmp_path),
demonstrating compatibility between the Reporting Engine application
service and its real infrastructure adapter (SAD Cap. 22), for both
supported formats (json, html).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.reporting.reporting_engine import (
    ReportingEngine,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ReportingConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.evidence_reference import (
    EvidenceReference,
)
from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)
from qa_servicenow_assistant.infrastructure.reporting.file_report_repository import (
    FileReportRepository,
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


def test_json_report_is_written_to_the_configured_directory(tmp_path: Path) -> None:
    configuration = ReportingConfiguration(format="json", directory=tmp_path / "reports")
    log_port = RecordingLogPort()
    engine = ReportingEngine(FileReportRepository(configuration), log_port, configuration)
    execution_result = ExecutionResult(
        execution_id="exec-real-1",
        workflow_id="incident_registration",
        status=ExecutionStatus.SUCCESS,
        duration_ms=4321.0,
        evidence=(EvidenceReference("final_state", "screenshots/exec-real-1/final.png"),),
        errors=(),
    )

    result = engine.generate_report(execution_result)

    assert result.success is True
    assert result.report_path == tmp_path / "reports" / "exec-real-1.json"
    data = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert data["execution_id"] == "exec-real-1"
    assert data["status"] == "success"
    assert "Report generated" in log_port.messages


def test_html_report_is_written_to_the_configured_directory(tmp_path: Path) -> None:
    configuration = ReportingConfiguration(format="html", directory=tmp_path / "reports")
    engine = ReportingEngine(
        FileReportRepository(configuration), RecordingLogPort(), configuration
    )
    execution_result = ExecutionResult(
        execution_id="exec-real-2",
        workflow_id="incident_registration",
        status=ExecutionStatus.FAILURE,
        duration_ms=999.0,
        errors=("Element not found",),
    )

    result = engine.generate_report(execution_result)

    assert result.success is True
    assert result.report_path == tmp_path / "reports" / "exec-real-2.html"
    content = result.report_path.read_text(encoding="utf-8")
    assert "exec-real-2" in content
    assert "Element not found" in content


def test_metrics_reflect_multiple_generated_reports(tmp_path: Path) -> None:
    configuration = ReportingConfiguration(format="json", directory=tmp_path / "reports")
    engine = ReportingEngine(
        FileReportRepository(configuration), RecordingLogPort(), configuration
    )

    engine.generate_report(
        ExecutionResult(
            execution_id="exec-a",
            workflow_id="w",
            status=ExecutionStatus.SUCCESS,
            duration_ms=100.0,
        )
    )
    engine.generate_report(
        ExecutionResult(
            execution_id="exec-b",
            workflow_id="w",
            status=ExecutionStatus.FAILURE,
            duration_ms=300.0,
        )
    )

    metrics = engine.calculate_metrics()

    assert metrics.total_executions == 2
    assert metrics.success_count == 1
    assert metrics.failure_count == 1
    assert metrics.average_duration_ms == 200.0
