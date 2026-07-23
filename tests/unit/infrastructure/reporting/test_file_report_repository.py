"""Unit tests for FileReportRepository (SAD 22.6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_servicenow_assistant.domain.exceptions.reporting import ReportPersistenceError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ReportingConfiguration,
)
from qa_servicenow_assistant.infrastructure.reporting.file_report_repository import (
    FileReportRepository,
)


def make_repository(tmp_path: Path) -> FileReportRepository:
    return FileReportRepository(ReportingConfiguration(directory=tmp_path / "reports"))


def test_creates_configured_directory_on_construction(tmp_path: Path) -> None:
    directory = tmp_path / "reports"
    assert not directory.exists()

    FileReportRepository(ReportingConfiguration(directory=directory))

    assert directory.is_dir()


def test_save_writes_content_and_returns_path(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)

    path = repository.save("hello world", "exec-1.json")

    assert path == tmp_path / "reports" / "exec-1.json"
    assert path.read_text(encoding="utf-8") == "hello world"


def test_save_sanitizes_unsafe_file_names(tmp_path: Path) -> None:
    directory = tmp_path / "reports"
    repository = FileReportRepository(ReportingConfiguration(directory=directory))

    path = repository.save("content", "../../etc/passwd.json")

    assert path.parent == directory
    assert path.read_text(encoding="utf-8") == "content"


@pytest.mark.parametrize("file_name", [".", ".."])
def test_save_rejects_names_that_are_traversal_segments(tmp_path: Path, file_name: str) -> None:
    repository = make_repository(tmp_path)

    with pytest.raises(ReportPersistenceError):
        repository.save("content", file_name)


def test_save_replaces_path_separators_with_a_harmless_placeholder(tmp_path: Path) -> None:
    directory = tmp_path / "reports"
    repository = FileReportRepository(ReportingConfiguration(directory=directory))

    path = repository.save("content", "/")

    assert path.parent == directory
    assert path.name == "_"
