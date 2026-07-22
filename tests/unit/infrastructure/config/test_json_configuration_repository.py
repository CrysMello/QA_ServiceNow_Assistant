"""Unit tests for JsonConfigurationRepository (SAD 10.3, 10.6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_servicenow_assistant.domain.exceptions.configuration import (
    ConfigurationFileNotFoundError,
    ConfigurationFormatError,
)
from qa_servicenow_assistant.infrastructure.config.json_configuration_repository import (
    JsonConfigurationRepository,
)


@pytest.fixture
def repository() -> JsonConfigurationRepository:
    return JsonConfigurationRepository()


def test_loads_valid_json_object(repository: JsonConfigurationRepository, tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"browser": {"headless": False}}), encoding="utf-8")

    data = repository.load(config_file)

    assert data == {"browser": {"headless": False}}


def test_missing_file_raises(repository: JsonConfigurationRepository, tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(ConfigurationFileNotFoundError):
        repository.load(missing_file)


def test_invalid_json_raises(repository: JsonConfigurationRepository, tmp_path: Path) -> None:
    broken_file = tmp_path / "broken.json"
    broken_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ConfigurationFormatError):
        repository.load(broken_file)


def test_non_object_json_raises(repository: JsonConfigurationRepository, tmp_path: Path) -> None:
    array_file = tmp_path / "array.json"
    array_file.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ConfigurationFormatError, match="JSON object"):
        repository.load(array_file)
