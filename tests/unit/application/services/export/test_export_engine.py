"""Unit tests for ExportEngine (ADR-0014).

Uses a fake ExportRepositoryPort and a fake LogPort (same pattern used
throughout this codebase), since the real infrastructure adapter
(ZipExportRepository) is exercised separately by its own unit tests and
by the integration test.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pytest

from qa_servicenow_assistant.application.ports.export_repository_port import (
    ExportRepositoryPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.export.export_engine import (
    ExportEngine,
)
from qa_servicenow_assistant.domain.exceptions.export import (
    ExportPersistenceError,
    InvalidExportRequestError,
)
from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem
from qa_servicenow_assistant.domain.value_objects.export_manifest import (
    ExportManifest,
    ExportManifestEntry,
)
from qa_servicenow_assistant.domain.value_objects.export_request import ExportRequest


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


class FakeExportRepository(ExportRepositoryPort):
    def __init__(self) -> None:
        self.save_error: Exception | None = None
        self.saved: list[tuple[str, Sequence[ExportItem]]] = []

    def save(self, execution_id: str, items: Sequence[ExportItem]) -> tuple[Path, ExportManifest]:
        if self.save_error is not None:
            raise self.save_error
        self.saved.append((execution_id, items))
        entries = tuple(
            ExportManifestEntry(description=item.description, archive_name=f"{i:02d}", size_bytes=1)
            for i, item in enumerate(items)
        )
        manifest = ExportManifest(execution_id=execution_id, entries=entries)
        return Path("/fake") / f"{execution_id}.zip", manifest


def make_request(**overrides: object) -> ExportRequest:
    defaults: dict[str, object] = dict(
        execution_id="exec-1",
        items=(ExportItem(description="report", source_path=Path("report.json")),),
    )
    defaults.update(overrides)
    return ExportRequest(**defaults)  # type: ignore[arg-type]


def test_export_persists_and_returns_success() -> None:
    repository = FakeExportRepository()
    log_port = FakeLogPort()
    engine = ExportEngine(repository, log_port)

    result = engine.export(make_request())

    assert result.success is True
    assert result.archive_path == Path("/fake/exec-1.zip")
    assert result.manifest is not None
    assert len(repository.saved) == 1
    assert len(log_port.info_calls) == 1


def test_export_raises_on_empty_execution_id() -> None:
    engine = ExportEngine(FakeExportRepository(), FakeLogPort())

    with pytest.raises(InvalidExportRequestError):
        engine.export(make_request(execution_id=""))


def test_export_raises_on_no_items() -> None:
    engine = ExportEngine(FakeExportRepository(), FakeLogPort())

    with pytest.raises(InvalidExportRequestError):
        engine.export(make_request(items=()))


def test_export_returns_failed_result_on_persistence_error() -> None:
    repository = FakeExportRepository()
    repository.save_error = ExportPersistenceError("disk full")
    log_port = FakeLogPort()
    engine = ExportEngine(repository, log_port)

    result = engine.export(make_request())

    assert result.success is False
    assert result.archive_path is None
    assert result.manifest is None
    assert result.error_message == "disk full"
    assert len(log_port.error_calls) == 1
