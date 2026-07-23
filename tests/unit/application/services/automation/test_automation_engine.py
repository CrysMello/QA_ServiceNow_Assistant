"""Unit tests for AutomationEngine (SAD Cap. 13).

Uses a fake AutomationExecutorPort and a fake LogPort (same pattern used
throughout this codebase), since the real infrastructure adapter
(PlaywrightAutomationExecutor) is exercised separately by its own unit
tests and by the integration test.
"""

from __future__ import annotations

from typing import Any

import pytest

from qa_servicenow_assistant.application.ports.automation_executor_port import (
    AutomationExecutorPort,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.automation.automation_engine import (
    AutomationEngine,
)
from qa_servicenow_assistant.domain.exceptions.automation import (
    ElementNotActionableError,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    BrowserConfiguration,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []
        self.info_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        self.info_calls.append((message, context))

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


class FakeAutomationExecutor(AutomationExecutorPort):
    def __init__(self, error_to_raise: Exception | None = None) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self._error_to_raise = error_to_raise

    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))
        if self._error_to_raise is not None:
            raise self._error_to_raise

    def click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("click", page, selector, timeout_ms=timeout_ms)

    def double_click(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("double_click", page, selector, timeout_ms=timeout_ms)

    def fill(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        self._record("fill", page, selector, value, timeout_ms=timeout_ms)

    def clear(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("clear", page, selector, timeout_ms=timeout_ms)

    def select_option(self, page: Any, selector: Selector, value: str, *, timeout_ms: int) -> None:
        self._record("select_option", page, selector, value, timeout_ms=timeout_ms)

    def check(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("check", page, selector, timeout_ms=timeout_ms)

    def uncheck(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("uncheck", page, selector, timeout_ms=timeout_ms)

    def upload_file(self, page: Any, selector: Selector, file_path: str, *, timeout_ms: int) -> None:
        self._record("upload_file", page, selector, file_path, timeout_ms=timeout_ms)

    def press_key(self, page: Any, selector: Selector, key: str, *, timeout_ms: int) -> None:
        self._record("press_key", page, selector, key, timeout_ms=timeout_ms)

    def hover(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("hover", page, selector, timeout_ms=timeout_ms)

    def wait_for(self, page: Any, selector: Selector, *, timeout_ms: int) -> None:
        self._record("wait_for", page, selector, timeout_ms=timeout_ms)


def make_selector() -> Selector:
    return Selector(strategy="data_testid", value='[data-testid="submit"]', priority=2)


def test_click_delegates_with_default_timeout_and_logs() -> None:
    executor = FakeAutomationExecutor()
    log_port = FakeLogPort()
    engine = AutomationEngine(executor, log_port, BrowserConfiguration(timeout_ms=10_000))

    engine.click("page", make_selector())

    assert executor.calls == [("click", ("page", make_selector()), {"timeout_ms": 10_000})]
    assert len(log_port.debug_calls) == 1
    assert len(log_port.info_calls) == 1
    assert log_port.error_calls == []


def test_click_honors_explicit_timeout_override() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.click("page", make_selector(), timeout_ms=2_500)

    assert executor.calls == [("click", ("page", make_selector()), {"timeout_ms": 2_500})]


def test_fill_passes_value_through_to_executor() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.fill("page", make_selector(), "INC0010001")

    assert executor.calls == [
        ("fill", ("page", make_selector(), "INC0010001"), {"timeout_ms": 30_000})
    ]


def test_select_option_passes_value_through_to_executor() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.select_option("page", make_selector(), "high")

    assert executor.calls == [
        ("select_option", ("page", make_selector(), "high"), {"timeout_ms": 30_000})
    ]


def test_select_option_accepts_multiple_values() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.select_option("page", make_selector(), ["low", "high"])

    assert executor.calls == [
        ("select_option", ("page", make_selector(), ["low", "high"]), {"timeout_ms": 30_000})
    ]


def test_upload_file_passes_path_through_to_executor() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.upload_file("page", make_selector(), "/tmp/file.png")

    assert executor.calls == [
        ("upload_file", ("page", make_selector(), "/tmp/file.png"), {"timeout_ms": 30_000})
    ]


def test_upload_file_accepts_multiple_paths() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.upload_file("page", make_selector(), ["/tmp/a.png", "/tmp/b.png"])

    assert executor.calls == [
        (
            "upload_file",
            ("page", make_selector(), ["/tmp/a.png", "/tmp/b.png"]),
            {"timeout_ms": 30_000},
        )
    ]


def test_press_key_passes_key_through_to_executor() -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    engine.press_key("page", make_selector(), "Enter")

    assert executor.calls == [
        ("press_key", ("page", make_selector(), "Enter"), {"timeout_ms": 30_000})
    ]


@pytest.mark.parametrize(
    "method", ["double_click", "clear", "check", "uncheck", "hover", "wait_for"]
)
def test_simple_operations_delegate_to_executor(method: str) -> None:
    executor = FakeAutomationExecutor()
    engine = AutomationEngine(executor, FakeLogPort())

    getattr(engine, method)("page", make_selector())

    assert len(executor.calls) == 1
    assert executor.calls[0][0] == method


def test_failure_is_logged_and_reraised() -> None:
    error = ElementNotActionableError("timed out")
    executor = FakeAutomationExecutor(error_to_raise=error)
    log_port = FakeLogPort()
    engine = AutomationEngine(executor, log_port)

    with pytest.raises(ElementNotActionableError):
        engine.click("page", make_selector())

    assert len(log_port.error_calls) == 1
    assert log_port.info_calls == []  # never logs "completed" on failure
