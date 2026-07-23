"""Unit tests for ElementRecorder."""

from __future__ import annotations

from typing import Any

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.application.services.element_recording.element_recorder import (
    ElementRecorder,
)
from qa_servicenow_assistant.domain.value_objects.browser_snapshot import (
    CollectedElement,
)

_BUTTON = CollectedElement(tag_name="button", text="Submit", visible=True, attributes={"id": "submit-btn"})
_INPUT = CollectedElement(tag_name="input", text="", visible=True, attributes={"name": "username"})


class FakeLogPort(LogPort):
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, dict[str, Any]]] = []

    def bind(self, **context: Any) -> "FakeLogPort":
        return self

    def trace(self, message: str, **context: Any) -> None:
        pass

    def debug(self, message: str, **context: Any) -> None:
        self.debug_calls.append((message, context))

    def info(self, message: str, **context: Any) -> None:
        pass

    def warning(self, message: str, **context: Any) -> None:
        pass

    def error(self, message: str, **context: Any) -> None:
        pass

    def critical(self, message: str, **context: Any) -> None:
        pass


def test_records_are_empty_initially() -> None:
    recorder = ElementRecorder(FakeLogPort())

    assert recorder.records == ()


def test_record_appends_and_returns_the_record() -> None:
    recorder = ElementRecorder(FakeLogPort())

    recorded = recorder.record(_BUTTON, label="primary_action", page_url="https://dev.service-now.com/home")

    assert recorder.records == (recorded,)
    assert recorded.element == _BUTTON
    assert recorded.label == "primary_action"


def test_record_logs_debug_event() -> None:
    log_port = FakeLogPort()
    recorder = ElementRecorder(log_port)

    recorder.record(_BUTTON, label="primary_action", page_url="https://dev.service-now.com/home")

    assert len(log_port.debug_calls) == 1
    message, context = log_port.debug_calls[0]
    assert message == "Element recorded"
    assert context["label"] == "primary_action"
    assert context["tag_name"] == "button"


def test_record_many_records_all_elements_with_shared_label() -> None:
    recorder = ElementRecorder(FakeLogPort())

    recorded = recorder.record_many(
        [_BUTTON, _INPUT], label="form_fields", page_url="https://dev.service-now.com/form"
    )

    assert len(recorded) == 2
    assert all(record.label == "form_fields" for record in recorded)
    assert recorder.records == recorded


def test_records_accumulate_in_order_across_calls() -> None:
    recorder = ElementRecorder(FakeLogPort())

    recorder.record(_BUTTON, label="first", page_url="https://dev.service-now.com/a")
    recorder.record(_INPUT, label="second", page_url="https://dev.service-now.com/b")

    assert [record.label for record in recorder.records] == ["first", "second"]


def test_records_for_label_filters_correctly() -> None:
    recorder = ElementRecorder(FakeLogPort())
    recorder.record(_BUTTON, label="primary_action", page_url="https://dev.service-now.com/a")
    recorder.record(_INPUT, label="form_field", page_url="https://dev.service-now.com/a")
    recorder.record(_BUTTON, label="primary_action", page_url="https://dev.service-now.com/b")

    matches = recorder.records_for_label("primary_action")

    assert len(matches) == 2
    assert all(record.label == "primary_action" for record in matches)
