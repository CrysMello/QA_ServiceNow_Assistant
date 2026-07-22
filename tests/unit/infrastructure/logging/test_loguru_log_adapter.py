"""Unit tests for LoguruLogAdapter (SAD 10.3; SAD Cap. 24; ADR-0013)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_servicenow_assistant.domain.value_objects.configuration import (
    LoggingConfiguration,
)
from qa_servicenow_assistant.infrastructure.logging.loguru_log_adapter import (
    LoguruLogAdapter,
)


def _make_config(tmp_path: Path, **overrides: object) -> LoggingConfiguration:
    defaults: dict[str, object] = {
        "level": "TRACE",
        "directory": tmp_path,
        "file_name": "test.log",
    }
    defaults.update(overrides)
    return LoggingConfiguration(**defaults)  # type: ignore[arg-type]


def test_writes_message_to_file(tmp_path: Path) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path))

    adapter.info("Configuration loaded", instance_url="https://dev.service-now.com")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "Configuration loaded" in content
    assert "https://dev.service-now.com" in content


@pytest.mark.parametrize(
    "level_method", ["trace", "debug", "info", "warning", "error", "critical"]
)
def test_all_required_levels_are_supported(tmp_path: Path, level_method: str) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path))

    getattr(adapter, level_method)(f"{level_method} message")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert f"{level_method} message" in content
    assert level_method.upper() in content


def test_sensitive_data_is_masked_by_default(tmp_path: Path) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path))

    adapter.warning("Login attempt", password="hunter2")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "hunter2" not in content
    assert "***MASKED***" in content


def test_masking_can_be_disabled_via_configuration(tmp_path: Path) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path, mask_sensitive_data=False))

    adapter.warning("Login attempt", password="hunter2")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "hunter2" in content


def test_bind_reuses_sinks_and_carries_context(tmp_path: Path) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path))

    execution_logger = adapter.bind(execution_id="exec-123", module="ConfigurationManager")
    execution_logger.info("Step completed", workflow_step="load_configuration")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "exec-123" in content
    assert "ConfigurationManager" in content
    assert "load_configuration" in content


def test_bind_does_not_mutate_original_instance(tmp_path: Path) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path))

    adapter.bind(execution_id="exec-123")
    adapter.info("No bound context expected here")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "No bound context expected here" in content
    assert "exec-123" not in content


def test_console_sink_can_be_disabled(tmp_path: Path) -> None:
    adapter = LoguruLogAdapter(_make_config(tmp_path, console_enabled=False))

    adapter.info("File only message")

    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "File only message" in content


def test_file_sink_creates_missing_directory(tmp_path: Path) -> None:
    nested_dir = tmp_path / "nested" / "logs"
    adapter = LoguruLogAdapter(_make_config(nested_dir))

    adapter.info("Directory created on demand")

    assert (nested_dir / "test.log").exists()
