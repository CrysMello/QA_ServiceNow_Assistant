"""Unit tests for ZipExportRepository (ADR-0014)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from qa_servicenow_assistant.domain.exceptions.export import ExportPersistenceError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ExportConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.export_item import ExportItem
from qa_servicenow_assistant.infrastructure.export.zip_export_repository import (
    ZipExportRepository,
)


def make_repository(tmp_path: Path) -> ZipExportRepository:
    return ZipExportRepository(ExportConfiguration(directory=tmp_path / "exports"))


def make_source_file(tmp_path: Path, name: str, content: str = "content") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_creates_configured_directory_on_construction(tmp_path: Path) -> None:
    directory = tmp_path / "exports"
    assert not directory.exists()

    ZipExportRepository(ExportConfiguration(directory=directory))

    assert directory.is_dir()


def test_save_writes_archive_containing_all_items(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    report = make_source_file(tmp_path, "report.json", "{}")
    screenshot = make_source_file(tmp_path, "final.png", "fake-png-bytes")
    items = (
        ExportItem(description="execution_report", source_path=report),
        ExportItem(description="final_screenshot", source_path=screenshot),
    )

    archive_path, manifest = repository.save("exec-1", items)

    assert archive_path == tmp_path / "exports" / "exec-1.zip"
    assert manifest.execution_id == "exec-1"
    assert len(manifest.entries) == 2
    assert manifest.entries[0].description == "execution_report"
    assert manifest.entries[1].description == "final_screenshot"

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert "00_report.json" in names
        assert "01_final.png" in names
        assert "manifest.json" in names
        manifest_data = json.loads(archive.read("manifest.json"))
        assert manifest_data["execution_id"] == "exec-1"
        assert len(manifest_data["entries"]) == 2


def test_save_raises_when_a_source_file_is_missing(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    missing = tmp_path / "does_not_exist.png"
    items = (ExportItem(description="missing", source_path=missing),)

    with pytest.raises(ExportPersistenceError):
        repository.save("exec-1", items)

    assert not (tmp_path / "exports" / "exec-1.zip").exists()


def test_save_sanitizes_unsafe_execution_id(tmp_path: Path) -> None:
    directory = tmp_path / "exports"
    repository = ZipExportRepository(ExportConfiguration(directory=directory))
    report = make_source_file(tmp_path, "report.json")
    items = (ExportItem(description="report", source_path=report),)

    archive_path, _manifest = repository.save("../../etc/passwd", items)

    assert archive_path.parent == directory


def test_save_rejects_empty_execution_id_after_sanitization(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    report = make_source_file(tmp_path, "report.json")
    items = (ExportItem(description="report", source_path=report),)

    with pytest.raises(ExportPersistenceError):
        repository.save("", items)


def test_duplicate_file_names_do_not_collide_in_the_archive(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    first_dir = tmp_path / "a"
    second_dir = tmp_path / "b"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "screenshot.png"
    second = second_dir / "screenshot.png"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    items = (
        ExportItem(description="before", source_path=first),
        ExportItem(description="after", source_path=second),
    )

    archive_path, manifest = repository.save("exec-1", items)

    assert manifest.entries[0].archive_name != manifest.entries[1].archive_name
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.read(manifest.entries[0].archive_name) == b"first"
        assert archive.read(manifest.entries[1].archive_name) == b"second"
