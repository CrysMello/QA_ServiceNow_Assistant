"""Integration tests for the Log Engine (LogPort + LoguruLogAdapter).

Exercises real file I/O, log rotation and end-to-end correlation +
masking, as required by Prompt 3 / ADR-0013 ("testes unitarios e de
integracao").
"""

from __future__ import annotations

from pathlib import Path

from qa_servicenow_assistant.domain.value_objects.configuration import (
    LoggingConfiguration,
)
from qa_servicenow_assistant.infrastructure.logging.loguru_log_adapter import (
    LoguruLogAdapter,
)


def test_end_to_end_correlation_console_and_file(tmp_path: Path) -> None:
    config = LoggingConfiguration(
        level="TRACE", directory=tmp_path, file_name="integration.log"
    )
    log_port = LoguruLogAdapter(config)

    execution_logger = log_port.bind(execution_id="exec-abc-123")
    module_logger = execution_logger.bind(module="ConfigurationManager")

    module_logger.info("Execution started")
    module_logger.info(
        "Step completed",
        workflow_step="load_configuration",
        instance_url="https://dev.service-now.com",
    )
    module_logger.error(
        "Step failed",
        workflow_step="load_configuration",
        password="should-never-appear",
    )

    log_file = tmp_path / "integration.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")

    assert "Execution started" in content
    assert "exec-abc-123" in content
    assert "ConfigurationManager" in content
    assert "load_configuration" in content
    assert "Step failed" in content
    assert "should-never-appear" not in content
    assert "***MASKED***" in content


def test_file_rotation_creates_additional_files(tmp_path: Path) -> None:
    config = LoggingConfiguration(
        level="TRACE",
        directory=tmp_path,
        file_name="rotating.log",
        rotation="1 KB",
        retention="1 day",
        console_enabled=False,
    )
    log_port = LoguruLogAdapter(config)

    long_message_payload = "x" * 200
    for index in range(50):
        log_port.info(f"Log line {index}: {long_message_payload}")

    log_files = list(tmp_path.glob("rotating*.log"))
    assert len(log_files) > 1, (
        "Expected rotation to produce more than one log file, found: "
        f"{[path.name for path in log_files]}"
    )


def test_retention_and_rotation_values_are_accepted_without_error(tmp_path: Path) -> None:
    config = LoggingConfiguration(
        directory=tmp_path,
        file_name="policy.log",
        rotation="00:00",
        retention="10 days",
    )
    log_port = LoguruLogAdapter(config)

    log_port.info("Policy accepted")

    assert (tmp_path / "policy.log").exists()
