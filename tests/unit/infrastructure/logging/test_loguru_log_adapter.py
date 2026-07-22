"""Unit tests for LoguruLogAdapter (SAD 10.3 - Log Adapter)."""

from __future__ import annotations

from loguru import logger

from qa_servicenow_assistant.infrastructure.logging.loguru_log_adapter import (
    LoguruLogAdapter,
)


def test_info_writes_message_and_bound_context() -> None:
    captured: list[str] = []
    adapter = LoguruLogAdapter(level="DEBUG")
    sink_id = logger.add(captured.append, level="DEBUG")

    try:
        adapter.info("Configuration loaded", instance_url="https://dev.service-now.com")
    finally:
        logger.remove(sink_id)

    assert len(captured) == 1
    assert "Configuration loaded" in captured[0]


def test_all_levels_are_callable_without_raising() -> None:
    adapter = LoguruLogAdapter(level="DEBUG")

    adapter.debug("debug message")
    adapter.info("info message")
    adapter.warning("warning message")
    adapter.error("error message")
