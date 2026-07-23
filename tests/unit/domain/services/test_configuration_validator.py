"""Unit tests for ConfigurationValidator (SAD Cap. 21, RF-002)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_servicenow_assistant.domain.exceptions.configuration import (
    InvalidConfigurationValueError,
    MissingRequiredParameterError,
)
from qa_servicenow_assistant.domain.services.configuration_validator import (
    ConfigurationValidator,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ApplicationConfiguration,
    BrowserConfiguration,
    ExportConfiguration,
    LoggingConfiguration,
    ReportingConfiguration,
    RetryConfiguration,
)


@pytest.fixture
def validator() -> ConfigurationValidator:
    return ConfigurationValidator()


@pytest.fixture
def valid_configuration(tmp_path: Path) -> ApplicationConfiguration:
    spreadsheet = tmp_path / "input.xlsx"
    spreadsheet.write_bytes(b"fake-xlsx-content")
    knowledge_base_dir = tmp_path / "knowledge_base"
    knowledge_base_dir.mkdir()

    return ApplicationConfiguration(
        spreadsheet_path=spreadsheet,
        knowledge_base_path=knowledge_base_dir,
        instance_url="https://dev12345.service-now.com",
    )


def test_valid_configuration_passes(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    validator.validate(valid_configuration)  # must not raise


def test_missing_spreadsheet_extension_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration, tmp_path: Path
) -> None:
    bad_file = tmp_path / "input.csv"
    bad_file.write_bytes(b"data")
    configuration = _replace_spreadsheet(valid_configuration, bad_file)

    with pytest.raises(InvalidConfigurationValueError, match=".xlsx"):
        validator.validate(configuration)


def test_nonexistent_spreadsheet_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration, tmp_path: Path
) -> None:
    missing_file = tmp_path / "does_not_exist.xlsx"
    configuration = _replace_spreadsheet(valid_configuration, missing_file)

    with pytest.raises(InvalidConfigurationValueError, match="does not exist"):
        validator.validate(configuration)


def test_nonexistent_knowledge_base_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration, tmp_path: Path
) -> None:
    missing_dir = tmp_path / "no_kb"
    configuration = _replace_knowledge_base(valid_configuration, missing_dir)

    with pytest.raises(InvalidConfigurationValueError, match="does not exist"):
        validator.validate(configuration)


def test_knowledge_base_not_a_directory_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration, tmp_path: Path
) -> None:
    kb_file = tmp_path / "kb.json"
    kb_file.write_text("{}", encoding="utf-8")
    configuration = _replace_knowledge_base(valid_configuration, kb_file)

    with pytest.raises(InvalidConfigurationValueError, match="must be a directory"):
        validator.validate(configuration)


def test_empty_instance_url_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, instance_url="")

    with pytest.raises(MissingRequiredParameterError):
        validator.validate(configuration)


@pytest.mark.parametrize("bad_url", ["not-a-url", "ftp://example.com", "example.com"])
def test_invalid_instance_url_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration, bad_url: str
) -> None:
    configuration = _replace(valid_configuration, instance_url=bad_url)

    with pytest.raises(InvalidConfigurationValueError, match="valid HTTP"):
        validator.validate(configuration)


def test_non_positive_browser_timeout_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, browser=BrowserConfiguration(timeout_ms=0))

    with pytest.raises(InvalidConfigurationValueError, match="browser.timeout_ms"):
        validator.validate(configuration)


def test_msedge_browser_type_is_valid(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, browser=BrowserConfiguration(browser_type="msedge"))

    validator.validate(configuration)  # must not raise


def test_unsupported_browser_type_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, browser=BrowserConfiguration(browser_type="firefox"))

    with pytest.raises(InvalidConfigurationValueError, match="browser_type"):
        validator.validate(configuration)


def test_retry_max_attempts_below_minimum_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, retry=RetryConfiguration(max_attempts=0))

    with pytest.raises(InvalidConfigurationValueError, match="max_attempts"):
        validator.validate(configuration)


def test_unknown_backoff_strategy_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(
        valid_configuration, retry=RetryConfiguration(backoff_strategy="unknown")
    )

    with pytest.raises(InvalidConfigurationValueError, match="backoff_strategy"):
        validator.validate(configuration)


def test_unknown_log_level_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, logging=LoggingConfiguration(level="NOISY"))

    with pytest.raises(InvalidConfigurationValueError, match="logging.level"):
        validator.validate(configuration)


def test_empty_log_file_name_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, logging=LoggingConfiguration(file_name="  "))

    with pytest.raises(InvalidConfigurationValueError, match="file_name"):
        validator.validate(configuration)


def test_empty_log_rotation_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, logging=LoggingConfiguration(rotation=""))

    with pytest.raises(InvalidConfigurationValueError, match="rotation"):
        validator.validate(configuration)


def test_empty_log_retention_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, logging=LoggingConfiguration(retention=""))

    with pytest.raises(InvalidConfigurationValueError, match="retention"):
        validator.validate(configuration)


def test_all_log_sinks_disabled_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(
        valid_configuration,
        logging=LoggingConfiguration(console_enabled=False, file_enabled=False),
    )

    with pytest.raises(InvalidConfigurationValueError, match="at least one sink"):
        validator.validate(configuration)


def test_unsupported_report_format_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, reporting=ReportingConfiguration(format="pdf"))

    with pytest.raises(InvalidConfigurationValueError, match="reporting.format"):
        validator.validate(configuration)


def test_unsupported_export_format_raises(
    validator: ConfigurationValidator, valid_configuration: ApplicationConfiguration
) -> None:
    configuration = _replace(valid_configuration, export=ExportConfiguration(archive_format="tar"))

    with pytest.raises(InvalidConfigurationValueError, match="export.archive_format"):
        validator.validate(configuration)


def _replace(configuration: ApplicationConfiguration, **changes: object) -> ApplicationConfiguration:
    from dataclasses import replace

    return replace(configuration, **changes)


def _replace_spreadsheet(configuration: ApplicationConfiguration, path: Path) -> ApplicationConfiguration:
    return _replace(configuration, spreadsheet_path=path)


def _replace_knowledge_base(configuration: ApplicationConfiguration, path: Path) -> ApplicationConfiguration:
    return _replace(configuration, knowledge_base_path=path)
