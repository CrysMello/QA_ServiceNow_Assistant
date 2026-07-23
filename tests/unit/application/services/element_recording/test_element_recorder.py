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
_EXEC_A = "exec-aaa"
_EXEC_B = "exec-bbb"


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

    recorded = recorder.record(
        _BUTTON, execution_id=_EXEC_A, label="primary_action", page_url="https://dev.service-now.com/home"
    )

    assert recorder.records == (recorded,)
    assert recorded.element == _BUTTON
    assert recorded.execution_id == _EXEC_A
    assert recorded.label == "primary_action"


def test_record_logs_debug_event_with_execution_id_and_element_id() -> None:
    log_port = FakeLogPort()
    recorder = ElementRecorder(log_port)

    recorder.record(
        _BUTTON, execution_id=_EXEC_A, label="primary_action", page_url="https://dev.service-now.com/home"
    )

    assert len(log_port.debug_calls) == 1
    message, context = log_port.debug_calls[0]
    assert message == "Element recorded"
    assert context["execution_id"] == _EXEC_A
    assert context["label"] == "primary_action"
    assert context["tag_name"] == "button"
    assert context["element_id"] == "submit-btn"


def test_record_many_records_all_elements_with_shared_context() -> None:
    recorder = ElementRecorder(FakeLogPort())

    recorded = recorder.record_many(
        [_BUTTON, _INPUT],
        execution_id=_EXEC_A,
        label="form_fields",
        page_url="https://dev.service-now.com/form",
        page_id="form_page",
    )

    assert len(recorded) == 2
    assert all(record.label == "form_fields" for record in recorded)
    assert all(record.execution_id == _EXEC_A for record in recorded)
    assert all(record.page_id == "form_page" for record in recorded)
    assert recorder.records == recorded


def test_records_accumulate_in_order_across_calls() -> None:
    recorder = ElementRecorder(FakeLogPort())

    recorder.record(_BUTTON, execution_id=_EXEC_A, label="first", page_url="https://dev.service-now.com/a")
    recorder.record(_INPUT, execution_id=_EXEC_A, label="second", page_url="https://dev.service-now.com/b")

    assert [record.label for record in recorder.records] == ["first", "second"]


def test_records_for_label_filters_correctly() -> None:
    recorder = ElementRecorder(FakeLogPort())
    recorder.record(_BUTTON, execution_id=_EXEC_A, label="primary_action", page_url="https://dev.service-now.com/a")
    recorder.record(_INPUT, execution_id=_EXEC_A, label="form_field", page_url="https://dev.service-now.com/a")
    recorder.record(_BUTTON, execution_id=_EXEC_A, label="primary_action", page_url="https://dev.service-now.com/b")

    matches = recorder.records_for_label("primary_action")

    assert len(matches) == 2
    assert all(record.label == "primary_action" for record in matches)


def test_records_for_execution_isolates_between_executions() -> None:
    recorder = ElementRecorder(FakeLogPort())
    recorder.record(_BUTTON, execution_id=_EXEC_A, label="a1", page_url="https://x")
    recorder.record(_INPUT, execution_id=_EXEC_A, label="a2", page_url="https://x")
    recorder.record(_BUTTON, execution_id=_EXEC_B, label="b1", page_url="https://x")

    exec_a_records = recorder.records_for_execution(_EXEC_A)
    exec_b_records = recorder.records_for_execution(_EXEC_B)

    assert len(exec_a_records) == 2
    assert all(record.execution_id == _EXEC_A for record in exec_a_records)
    assert len(exec_b_records) == 1
    assert exec_b_records[0].execution_id == _EXEC_B


def test_records_for_execution_returns_empty_for_unknown_execution() -> None:
    recorder = ElementRecorder(FakeLogPort())
    recorder.record(_BUTTON, execution_id=_EXEC_A, label="a1", page_url="https://x")

    assert recorder.records_for_execution("never-recorded") == ()


def test_records_property_returns_a_new_tuple_each_time_not_the_internal_list() -> None:
    recorder = ElementRecorder(FakeLogPort())
    recorder.record(_BUTTON, execution_id=_EXEC_A, label="a1", page_url="https://x")

    first_access = recorder.records
    second_access = recorder.records

    assert first_access == second_access
    assert first_access is not second_access  # distinct tuple objects, no shared mutable state


def test_mutating_returned_records_does_not_affect_internal_state() -> None:
    recorder = ElementRecorder(FakeLogPort())
    recorder.record(_BUTTON, execution_id=_EXEC_A, label="a1", page_url="https://x")

    exposed = recorder.records
    mutated_copy = list(exposed)
    mutated_copy.append("not a real record")  # only mutates the local copy

    assert len(recorder.records) == 1  # internal state untouched
