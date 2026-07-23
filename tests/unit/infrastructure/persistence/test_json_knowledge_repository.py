"""Unit tests for JsonKnowledgeRepository (SAD 10.3, SAD Cap. 11)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.exceptions.knowledge_base import (
    IncompatibleKnowledgeBaseVersionError,
    KnowledgeBaseFormatError,
    KnowledgeBaseNotFoundError,
)
from qa_servicenow_assistant.infrastructure.persistence.json_knowledge_repository import (
    JsonKnowledgeRepository,
)


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.warning_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        self.warning_calls.append((message, context))

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def write_full_knowledge_base(directory: Path, *, version: str = "1.0") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "manifest.json", {"version": version, "generated_at": "2026-01-01"})
    write_json(
        directory / "pages.json",
        [
            {
                "key": "incident_form",
                "url_pattern": "/incident.do",
                "title": "Incident",
                "required_element_keys": ["submit_button"],
            }
        ],
    )
    write_json(
        directory / "elements.json",
        [{"key": "submit_button", "page_key": "incident_form", "description": "Submit button"}],
    )
    write_json(
        directory / "selectors.json",
        [{"element_key": "submit_button", "strategy": "id", "value": "#submit", "priority": 3}],
    )
    write_json(
        directory / "workflows.json",
        [{"key": "create_incident", "description": "Create an incident", "step_keys": ["incident_form"]}],
    )
    write_json(directory / "fingerprints.json", {"incident_form": "fp-123"})


def test_loads_a_complete_knowledge_base(tmp_path: Path) -> None:
    write_full_knowledge_base(tmp_path)
    log_port = FakeLogPort()

    repository = JsonKnowledgeRepository(tmp_path, log_port)

    pages = repository.get_known_pages()
    assert [page.key for page in pages] == ["incident_form"]
    assert pages[0].fingerprint == "fp-123"  # merged from fingerprints.json

    assert repository.get_page("incident_form") is not None
    assert repository.get_page("unknown") is None

    element = repository.get_element("submit_button")
    assert element is not None
    assert element.page_key == "incident_form"

    selector = repository.get_selector("submit_button")
    assert selector is not None
    assert selector.strategy == "id"
    assert selector.value == "#submit"

    workflow = repository.get_workflow("create_incident")
    assert workflow is not None
    assert workflow.step_keys == ("incident_form",)

    assert repository.get_fingerprint("incident_form") == "fp-123"
    assert repository.validate_version() is True
    assert any(message == "Knowledge Base loaded" for message, _ in log_port.info_calls)


def test_missing_directory_raises_not_found(tmp_path: Path) -> None:
    missing_dir = tmp_path / "does_not_exist"

    with pytest.raises(KnowledgeBaseNotFoundError):
        JsonKnowledgeRepository(missing_dir, FakeLogPort())


def test_missing_manifest_raises_not_found(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)

    with pytest.raises(KnowledgeBaseNotFoundError):
        JsonKnowledgeRepository(tmp_path, FakeLogPort())


def test_invalid_manifest_json_raises_format_error(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(KnowledgeBaseFormatError):
        JsonKnowledgeRepository(tmp_path, FakeLogPort())


def test_manifest_missing_version_key_raises_format_error(tmp_path: Path) -> None:
    write_json(tmp_path / "manifest.json", {"generated_at": "2026-01-01"})

    with pytest.raises(KnowledgeBaseFormatError):
        JsonKnowledgeRepository(tmp_path, FakeLogPort())


def test_incompatible_version_raises(tmp_path: Path) -> None:
    write_full_knowledge_base(tmp_path, version="9.9")

    with pytest.raises(IncompatibleKnowledgeBaseVersionError):
        JsonKnowledgeRepository(tmp_path, FakeLogPort())


def test_expected_version_is_configurable(tmp_path: Path) -> None:
    write_full_knowledge_base(tmp_path, version="2.5")

    repository = JsonKnowledgeRepository(tmp_path, FakeLogPort(), expected_version="2.5")

    assert repository.validate_version() is True


def test_missing_optional_files_are_treated_as_empty_and_logged(tmp_path: Path) -> None:
    write_json(tmp_path / "manifest.json", {"version": "1.0"})
    log_port = FakeLogPort()

    repository = JsonKnowledgeRepository(tmp_path, log_port)

    assert repository.get_known_pages() == ()
    assert repository.get_element("x") is None
    assert repository.get_selector("x") is None
    assert repository.get_workflow("x") is None
    assert len(log_port.warning_calls) == 5  # pages/elements/selectors/workflows/fingerprints


def test_malformed_page_entry_raises_format_error(tmp_path: Path) -> None:
    write_json(tmp_path / "manifest.json", {"version": "1.0"})
    write_json(tmp_path / "pages.json", [{"key": "incident_form"}])  # missing url_pattern

    with pytest.raises(KnowledgeBaseFormatError):
        JsonKnowledgeRepository(tmp_path, FakeLogPort())


def test_malformed_selector_entry_raises_format_error(tmp_path: Path) -> None:
    write_json(tmp_path / "manifest.json", {"version": "1.0"})
    write_json(tmp_path / "selectors.json", [{"element_key": "submit_button", "strategy": "id"}])

    with pytest.raises(KnowledgeBaseFormatError):
        JsonKnowledgeRepository(tmp_path, FakeLogPort())
