"""Unit tests for NavigationEngine (SAD Cap. 14).

Uses fakes for NavigationExecutorPort and NavigationValidationPort, since
their real counterparts (Automation Engine, Page Recognition) are later
modules not implemented yet - this is the whole point of depending on
abstract ports (Dependency Inversion).
"""

from __future__ import annotations

from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.ports.navigation_executor_port import (
    NavigationExecutorPort,
)
from qa_servicenow_assistant.application.ports.navigation_validation_port import (
    NavigationValidationPort,
)
from qa_servicenow_assistant.application.services.navigation.navigation_engine import (
    NavigationEngine,
)
from qa_servicenow_assistant.domain.exceptions.navigation import NavigationTimeoutError
from qa_servicenow_assistant.domain.value_objects.configuration import (
    NavigationConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.page_identifier import (
    PageIdentifier,
)


class FakeNavigationExecutor(NavigationExecutorPort):
    def __init__(self, error_to_raise: Exception | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._error_to_raise = error_to_raise

    def navigate(self, page: Any, url: str, timeout_ms: int) -> None:
        self.calls.append({"page": page, "url": url, "timeout_ms": timeout_ms})
        if self._error_to_raise is not None:
            raise self._error_to_raise


class FakeNavigationValidator(NavigationValidationPort):
    def __init__(self, result: bool = True) -> None:
        self.calls: list[tuple[Any, PageIdentifier]] = []
        self._result = result

    def validate(self, page: Any, target: PageIdentifier) -> bool:
        self.calls.append((page, target))
        return self._result


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


_TARGET = PageIdentifier(key="test_plan_list")
_URL = "https://dev.service-now.com/test_plan_list"
_FAKE_PAGE = object()


def test_successful_navigation_returns_success_result() -> None:
    executor = FakeNavigationExecutor()
    validator = FakeNavigationValidator(result=True)
    engine = NavigationEngine(executor, validator, FakeLogPort())

    result = engine.navigate(_FAKE_PAGE, _TARGET, _URL)

    assert result.success is True
    assert result.target == _TARGET
    assert result.url == _URL
    assert result.error_message is None
    assert result.duration_ms >= 0


def test_navigation_uses_configured_default_timeout() -> None:
    executor = FakeNavigationExecutor()
    engine = NavigationEngine(
        executor,
        FakeNavigationValidator(),
        FakeLogPort(),
        configuration=NavigationConfiguration(timeout_ms=12_345),
    )

    engine.navigate(_FAKE_PAGE, _TARGET, _URL)

    assert executor.calls[0]["timeout_ms"] == 12_345


def test_per_call_timeout_overrides_configured_default() -> None:
    executor = FakeNavigationExecutor()
    engine = NavigationEngine(
        executor,
        FakeNavigationValidator(),
        FakeLogPort(),
        configuration=NavigationConfiguration(timeout_ms=30_000),
    )

    engine.navigate(_FAKE_PAGE, _TARGET, _URL, timeout_ms=1_000)

    assert executor.calls[0]["timeout_ms"] == 1_000


def test_validation_failure_returns_failed_result_without_raising() -> None:
    engine = NavigationEngine(FakeNavigationExecutor(), FakeNavigationValidator(result=False), FakeLogPort())

    result = engine.navigate(_FAKE_PAGE, _TARGET, _URL)

    assert result.success is False
    assert "validation failed" in result.error_message.lower()


def test_execution_failure_is_reported_as_failed_result_not_raised() -> None:
    executor = FakeNavigationExecutor(error_to_raise=NavigationTimeoutError("Timed out"))
    engine = NavigationEngine(executor, FakeNavigationValidator(), FakeLogPort())

    result = engine.navigate(_FAKE_PAGE, _TARGET, _URL)  # must not raise

    assert result.success is False
    assert "Timed out" in result.error_message


def test_execution_failure_skips_validation() -> None:
    executor = FakeNavigationExecutor(error_to_raise=NavigationTimeoutError("Timed out"))
    validator = FakeNavigationValidator()
    engine = NavigationEngine(executor, validator, FakeLogPort())

    engine.navigate(_FAKE_PAGE, _TARGET, _URL)

    assert validator.calls == []


def test_history_accumulates_across_calls() -> None:
    engine = NavigationEngine(FakeNavigationExecutor(), FakeNavigationValidator(), FakeLogPort())

    engine.navigate(_FAKE_PAGE, _TARGET, _URL)
    engine.navigate(_FAKE_PAGE, PageIdentifier(key="other"), "https://dev.service-now.com/other")

    assert len(engine.history) == 2
    assert engine.history[0].target.key == "test_plan_list"
    assert engine.history[1].target.key == "other"


def test_successful_navigation_logs_info_events() -> None:
    log_port = FakeLogPort()
    engine = NavigationEngine(FakeNavigationExecutor(), FakeNavigationValidator(), log_port)

    engine.navigate(_FAKE_PAGE, _TARGET, _URL)

    messages = [message for message, _ in log_port.info_calls]
    assert "Navigation started" in messages
    assert "Navigation completed" in messages
    assert log_port.error_calls == []


def test_failed_navigation_logs_error_event() -> None:
    log_port = FakeLogPort()
    engine = NavigationEngine(FakeNavigationExecutor(), FakeNavigationValidator(result=False), log_port)

    engine.navigate(_FAKE_PAGE, _TARGET, _URL)

    assert len(log_port.error_calls) == 1
    message, context = log_port.error_calls[0]
    assert message == "Navigation failed"
    assert context["target"] == _TARGET.key
