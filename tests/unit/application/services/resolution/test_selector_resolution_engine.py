"""Unit tests for SelectorResolutionEngine."""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.resolution.selector_resolution_engine import (
    SelectorResolutionEngine,
)
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    BrowserSnapshot,
    CollectedElement,
)


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []
        self.warning_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        pass

    def warning(self, message: str, **context: Any) -> None:
        self.warning_calls.append((message, context))

    def error(self, message: str, **context: Any) -> None:
        self.error_calls.append((message, context))

    def critical(self, message: str, **context: Any) -> None:
        pass


def _snapshot(elements: tuple[CollectedElement, ...]) -> BrowserSnapshot:
    return BrowserSnapshot(url="https://dev.service-now.com", title="X", html="<html></html>", elements=elements)


def test_unique_resolution_logs_debug() -> None:
    target = CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn"})
    snapshot = _snapshot((target,))
    log_port = FakeLogPort()
    engine = SelectorResolutionEngine(log_port)

    result = engine.resolve(target, snapshot)

    assert result.is_unique is True
    assert len(log_port.debug_calls) == 1
    assert log_port.warning_calls == []
    assert log_port.error_calls == []


def test_non_unique_resolution_logs_warning() -> None:
    target = CollectedElement(tag_name="div", text="Item", visible=True)
    duplicate = CollectedElement(tag_name="div", text="Item", visible=True)
    snapshot = _snapshot((target, duplicate))
    log_port = FakeLogPort()
    engine = SelectorResolutionEngine(log_port)

    result = engine.resolve(target, snapshot)

    assert result.is_resolved is True
    assert result.is_unique is False
    assert len(log_port.warning_calls) == 1
    assert log_port.debug_calls == []


def test_unresolvable_logs_error() -> None:
    target = CollectedElement(tag_name="div", text="", visible=True)
    snapshot = _snapshot((target,))
    log_port = FakeLogPort()
    engine = SelectorResolutionEngine(log_port)

    result = engine.resolve(target, snapshot)

    assert result.is_resolved is False
    assert len(log_port.error_calls) == 1
