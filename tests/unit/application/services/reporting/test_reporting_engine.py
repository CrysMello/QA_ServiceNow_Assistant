"""Unit tests for ReportingEngine (SAD Cap. 22).

Uses a fake ReportRepositoryPort and a fake LogPort (same pattern used
throughout this codebase), since the real infrastructure adapter
(FileReportRepository) is exercised separately by its own unit tests and
by the integration test.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.report_repository_port import (
    ReportRepositoryPort,
)
from qa_servicenow_assistant.application.services.reporting.reporting_engine import (
    ReportingEngine,
)
from qa_servicenow_assistant.domain.exceptions.reporting import (
    ReportPersistenceError,
    UnsupportedReportFormatError,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ReportingConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.execution_result import (
    ExecutionResult,
)
from qa_servicenow_assistant.domain.value_objects.execution_status import (
    ExecutionStatus,
)


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


class FakeReportRepository(ReportRepositoryPort):
    def __init__(self) -> None:
        self.saved: list[tuple[str, str]] = []
        self.save_error: Exception | None = None

    def save(self, content: str, file_name: str) -> Path:
        if self.save_error is not None:
            raise self.save_error
        self.saved.append((content, file_name))
        return Path("/fake") / file_name


def make_result(**overrides: object) -> ExecutionResult:
    defaults: dict[str, object] = dict(
        execution_id="exec-1",
        workflow_id="workflow-1",
        status=ExecutionStatus.SUCCESS,
        duration_ms=1000.0,
    )
    defaults.update(overrides)
    return ExecutionResult(**defaults)  # type: ignore[arg-type]


def test_generate_report_defaults_to_configured_format() -> None:
    repository = FakeReportRepository()
    log_port = FakeLogPort()
    engine = ReportingEngine(repository, log_port, ReportingConfiguration(format="json"))

    result = engine.generate_report(make_result())

    assert result.success is True
    assert result.report_path == Path("/fake/exec-1.json")
    assert repository.saved[0][1] == "exec-1.json"
    assert len(log_port.info_calls) == 1


def test_generate_report_honors_explicit_format_override() -> None:
    repository = FakeReportRepository()
    engine = ReportingEngine(repository, FakeLogPort(), ReportingConfiguration(format="json"))

    result = engine.generate_report(make_result(), format="html")

    assert result.success is True
    assert result.report_path == Path("/fake/exec-1.html")


def test_generate_report_raises_on_unsupported_format() -> None:
    engine = ReportingEngine(FakeReportRepository(), FakeLogPort())

    with pytest.raises(UnsupportedReportFormatError):
        engine.generate_report(make_result(), format="pdf")


def test_generate_report_returns_failed_result_on_persistence_error() -> None:
    repository = FakeReportRepository()
    repository.save_error = ReportPersistenceError("disk full")
    log_port = FakeLogPort()
    engine = ReportingEngine(repository, log_port)

    result = engine.generate_report(make_result())

    assert result.success is False
    assert result.report_path is None
    assert result.error_message == "disk full"
    assert len(log_port.error_calls) == 1


def test_generate_report_records_result_into_history_even_when_persistence_fails() -> None:
    repository = FakeReportRepository()
    repository.save_error = ReportPersistenceError("disk full")
    engine = ReportingEngine(repository, FakeLogPort())
    execution_result = make_result()

    engine.generate_report(execution_result)

    assert engine.history == (execution_result,)


def test_history_accumulates_across_multiple_calls() -> None:
    engine = ReportingEngine(FakeReportRepository(), FakeLogPort())
    first = make_result(execution_id="e1")
    second = make_result(execution_id="e2")

    engine.generate_report(first)
    engine.generate_report(second)

    assert engine.history == (first, second)


def test_calculate_metrics_reflects_recorded_history() -> None:
    engine = ReportingEngine(FakeReportRepository(), FakeLogPort())
    engine.generate_report(make_result(execution_id="e1", status=ExecutionStatus.SUCCESS))
    engine.generate_report(make_result(execution_id="e2", status=ExecutionStatus.FAILURE))

    metrics = engine.calculate_metrics()

    assert metrics.total_executions == 2
    assert metrics.success_count == 1
    assert metrics.failure_count == 1


def test_calculate_metrics_with_no_history_is_zeroed() -> None:
    engine = ReportingEngine(FakeReportRepository(), FakeLogPort())

    metrics = engine.calculate_metrics()

    assert metrics.total_executions == 0
