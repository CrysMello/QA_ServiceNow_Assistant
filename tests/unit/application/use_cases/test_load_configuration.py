"""Unit tests for LoadConfigurationUseCase (SAD 9.3, SAD Cap. 21)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.configuration_repository import (
    ConfigurationRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.use_cases.load_configuration import (
    LoadConfigurationRequest,
    LoadConfigurationUseCase,
)
from qa_servicenow_assistant.domain.exceptions.configuration import (
    InvalidConfigurationValueError,
)


class FakeConfigurationRepository(ConfigurationRepository):
    """Test double for ConfigurationRepository (RNF-007 - testabilidade)."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {}
        self.requested_paths: list[Path] = []

    def load(self, config_path: Path) -> dict[str, Any]:
        self.requested_paths.append(config_path)
        return self._data


class FakeLogPort(LogPort):
    """Test double for LogPort recording every call for assertions."""

    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, Any]]] = []

    def debug(self, message: str, **context: Any) -> None:
        pass

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass


@pytest.fixture
def valid_request(tmp_path: Path) -> LoadConfigurationRequest:
    spreadsheet = tmp_path / "input.xlsx"
    spreadsheet.write_bytes(b"fake-xlsx-content")
    knowledge_base_dir = tmp_path / "knowledge_base"
    knowledge_base_dir.mkdir()

    return LoadConfigurationRequest(
        spreadsheet_path=spreadsheet,
        knowledge_base_path=knowledge_base_dir,
        instance_url="https://dev12345.service-now.com",
    )


def test_execute_without_config_file_uses_defaults(valid_request: LoadConfigurationRequest) -> None:
    repository = FakeConfigurationRepository()
    log_port = FakeLogPort()
    use_case = LoadConfigurationUseCase(repository, log_port)

    configuration = use_case.execute(valid_request)

    assert configuration.instance_url == valid_request.instance_url
    assert configuration.browser.headless is True
    assert configuration.retry.max_attempts == 3
    assert repository.requested_paths == []  # no config file was requested


def test_execute_merges_config_file_values(
    valid_request: LoadConfigurationRequest, tmp_path: Path
) -> None:
    repository = FakeConfigurationRepository(
        data={"browser": {"headless": False, "timeout_ms": 45_000}, "retry": {"max_attempts": 5}}
    )
    log_port = FakeLogPort()
    config_file = tmp_path / "config.json"
    request = LoadConfigurationRequest(
        spreadsheet_path=valid_request.spreadsheet_path,
        knowledge_base_path=valid_request.knowledge_base_path,
        instance_url=valid_request.instance_url,
        config_file_path=config_file,
    )
    use_case = LoadConfigurationUseCase(repository, log_port)

    configuration = use_case.execute(request)

    assert configuration.browser.headless is False
    assert configuration.browser.timeout_ms == 45_000
    assert configuration.retry.max_attempts == 5
    assert repository.requested_paths == [config_file]


def test_environment_override_takes_precedence_over_config_file(
    valid_request: LoadConfigurationRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = FakeConfigurationRepository(data={"browser": {"headless": False}})
    log_port = FakeLogPort()
    monkeypatch.setenv("QA_SNA_BROWSER_HEADLESS", "true")
    request = LoadConfigurationRequest(
        spreadsheet_path=valid_request.spreadsheet_path,
        knowledge_base_path=valid_request.knowledge_base_path,
        instance_url=valid_request.instance_url,
        config_file_path=Path("unused.json"),
    )
    use_case = LoadConfigurationUseCase(repository, log_port)

    configuration = use_case.execute(request)

    assert configuration.browser.headless is True


def test_invalid_configuration_propagates_validation_error(
    valid_request: LoadConfigurationRequest,
) -> None:
    repository = FakeConfigurationRepository()
    log_port = FakeLogPort()
    request = LoadConfigurationRequest(
        spreadsheet_path=valid_request.spreadsheet_path,
        knowledge_base_path=valid_request.knowledge_base_path,
        instance_url="not-a-valid-url",
    )
    use_case = LoadConfigurationUseCase(repository, log_port)

    with pytest.raises(InvalidConfigurationValueError):
        use_case.execute(request)

    assert log_port.info_calls == []  # summary must not be logged when validation fails


def test_execute_logs_summary(valid_request: LoadConfigurationRequest) -> None:
    repository = FakeConfigurationRepository()
    log_port = FakeLogPort()
    use_case = LoadConfigurationUseCase(repository, log_port)

    use_case.execute(valid_request)

    assert len(log_port.info_calls) == 1
    message, context = log_port.info_calls[0]
    assert message == "Configuration loaded"
    assert context["instance_url"] == valid_request.instance_url
